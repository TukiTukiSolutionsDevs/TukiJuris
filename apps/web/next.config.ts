import type { NextConfig } from "next";

// In development, Next proxies /api/* to the FastAPI backend so cookies are
// same-origin (localhost:3000). In production the same-origin constraint is
// enforced by the reverse proxy — this rewrite becomes a passthrough.
//
// INTERNAL_API_URL is the in-cluster / inside-container hostname (e.g.
// http://api:8000 in docker-compose). NEXT_PUBLIC_API_URL is the browser-facing
// URL (http://localhost:8000 in dev). The rewrite runs on the Next.js server
// (inside the container), so it MUST use the internal address — otherwise
// `localhost` resolves to the container itself and the proxy gets ECONNREFUSED.
const API_URL =
  process.env.INTERNAL_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Required for the production Docker build (Dockerfile.prod).
  // Generates a standalone output directory with a minimal node_modules tree.
  output: "standalone",

  // Pin Turbopack's workspace root to THIS app. Without this, Next 16 can
  // infer the wrong root when a stray package-lock.json exists above the
  // project (e.g. in $HOME), which breaks module resolution — including
  // `tailwindcss` — with "Can't resolve" errors.
  turbopack: {
    root: __dirname,
  },

  // Do NOT auto-strip trailing slashes on /api/*.
  //
  // FastAPI routes are defined with trailing slashes (e.g. `/api/bookmarks/`).
  // By default Next issues a 308 for `/api/bookmarks/` → `/api/bookmarks`,
  // which then hits FastAPI's own 307 slash-redirect back to
  // `http://127.0.0.1:8000/api/bookmarks/` (internal host!). The browser
  // follows that cross-origin, drops the refresh cookie, and the request
  // lands at the backend with no credentials → 401.
  //
  // Turning off Next's redirect makes the proxy forward the path EXACTLY as
  // the client requested, which matches the backend route → no 307 → same
  // origin preserved → cookies and Authorization header survive.
  skipTrailingSlashRedirect: true,

  // Two-rule rewrite: preserve trailing slash when present.
  //
  // Next's single `/api/:path*` pattern collapses the trailing slash when it
  // reconstructs the destination URL, so `/api/bookmarks/` arrives at FastAPI
  // as `/api/bookmarks`. FastAPI's routes are explicitly defined with the
  // slash (`@router.get("/")`) and its default `redirect_slashes=True` then
  // emits a 307 whose Location header uses the BACKEND's internal host —
  // uvicorn's `--proxy-headers` does NOT honour `X-Forwarded-Host`. The
  // browser follows that 307 cross-origin, drops the httpOnly refresh
  // cookie, and the retry lands at a bare 401.
  //
  // Matching the slash-suffixed variant FIRST means requests that include
  // the trailing slash are forwarded verbatim (with slash), so FastAPI's
  // auto-redirect never fires. Calls that legitimately omit the slash
  // still hit the second rule.
  async rewrites() {
    return [
      { source: "/api/:path*/", destination: `${API_URL}/api/:path*/` },
      { source: "/api/:path*", destination: `${API_URL}/api/:path*` },
    ];
  },
};

export default nextConfig;
