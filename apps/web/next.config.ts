import type { NextConfig } from "next";

// In development, Next proxies /api/* to the FastAPI backend so cookies are
// same-origin (localhost:3000). In production the same-origin constraint is
// enforced by the reverse proxy — this rewrite becomes a passthrough.
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Required for the production Docker build (Dockerfile.prod).
  // Generates a standalone output directory with a minimal node_modules tree.
  output: "standalone",

  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
};

export default nextConfig;
