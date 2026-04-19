import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";
import { middleware } from "../middleware";
import { SESSION_MARKER_COOKIE } from "../lib/constants";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function req(
  path: string,
  opts: { cookie?: boolean; search?: string } = {},
): NextRequest {
  const url = `http://localhost${path}${opts.search ?? ""}`;
  const r = new NextRequest(url);
  if (opts.cookie) {
    r.cookies.set(SESSION_MARKER_COOKIE, "1");
  }
  return r;
}

function location(response: Response): string | null {
  return response.headers.get("location");
}

// ---------------------------------------------------------------------------
// Static assets and API routes — always pass through
// ---------------------------------------------------------------------------

describe("middleware — static / API pass-through", () => {
  it("passes through /_next/static/... unconditionally", () => {
    const res = middleware(req("/_next/static/chunk.js"));
    expect(res.status).not.toBe(302);
    expect(res.status).not.toBe(307);
  });

  it("passes through /api/auth/refresh unconditionally", () => {
    const res = middleware(req("/api/auth/refresh"));
    expect(res.status).not.toBe(302);
    expect(res.status).not.toBe(307);
  });

  it("passes through /favicon.ico unconditionally", () => {
    const res = middleware(req("/favicon.ico"));
    expect(res.status).not.toBe(302);
    expect(res.status).not.toBe(307);
  });

  it("passes through paths with a file extension (e.g. .png)", () => {
    const res = middleware(req("/brand/logo.png"));
    expect(res.status).not.toBe(302);
    expect(res.status).not.toBe(307);
  });
});

// ---------------------------------------------------------------------------
// Public routes — always allowed
// ---------------------------------------------------------------------------

describe("middleware — public routes", () => {
  it("allows /landing without a session", () => {
    const res = middleware(req("/landing"));
    expect(res.status).not.toBe(302);
  });

  it("allows /auth/login without a session", () => {
    const res = middleware(req("/auth/login"));
    expect(res.status).not.toBe(302);
  });

  it("allows /auth/register without a session", () => {
    const res = middleware(req("/auth/register"));
    expect(res.status).not.toBe(302);
  });

  // /onboarding is a PROTECTED route — requires an active session.
  // (Unauthenticated users cannot reach /onboarding; they are sent to login first.)
  it("does NOT include /onboarding in public paths", () => {
    const res = middleware(req("/onboarding"));
    // Must redirect unauthenticated requests to /auth/login
    expect(res.status).toBeGreaterThanOrEqual(300);
    expect(location(res)).toContain("/auth/login");
  });
});

// ---------------------------------------------------------------------------
// Auth-page bounce — authenticated user visiting /auth/login or /auth/register
// ---------------------------------------------------------------------------

describe("middleware — auth-page bounce when session cookie present", () => {
  it("redirects /auth/login to / when session cookie is set (no returnTo)", () => {
    const res = middleware(req("/auth/login", { cookie: true }));
    expect(res.status).toBeGreaterThanOrEqual(300);
    expect(res.status).toBeLessThan(400);
    expect(location(res)).toContain("/");
  });

  it("redirects /auth/register to / when session cookie is set (no returnTo)", () => {
    const res = middleware(req("/auth/register", { cookie: true }));
    expect(res.status).toBeGreaterThanOrEqual(300);
    expect(location(res)).toContain("/");
  });

  it("honours a valid returnTo when bouncing from /auth/login", () => {
    const res = middleware(
      req("/auth/login", { cookie: true, search: "?returnTo=%2Fhistorial" }),
    );
    expect(res.status).toBeGreaterThanOrEqual(300);
    expect(location(res)).toContain("/historial");
  });

  it("falls back to / when returnTo is an external URL", () => {
    const res = middleware(
      req("/auth/login", {
        cookie: true,
        search: "?returnTo=https%3A%2F%2Fevil.com",
      }),
    );
    expect(location(res)).not.toContain("evil.com");
  });

  it("falls back to / when returnTo is protocol-relative", () => {
    const res = middleware(
      req("/auth/login", {
        cookie: true,
        search: "?returnTo=%2F%2Fevil.com",
      }),
    );
    expect(location(res)).not.toContain("evil.com");
  });

  it("does NOT bounce /auth/login when session cookie is absent", () => {
    const res = middleware(req("/auth/login"));
    // Should be a NextResponse.next() — status 200 (or no redirect)
    expect(res.status).not.toBeGreaterThanOrEqual(300);
  });
});

// ---------------------------------------------------------------------------
// Protected routes — session required
// ---------------------------------------------------------------------------

describe("middleware — protected routes", () => {
  it("allows /onboarding when session cookie is present", () => {
    const res = middleware(req("/onboarding", { cookie: true }));
    expect(res.status).not.toBeGreaterThanOrEqual(300);
  });

  it("redirects /chat to /auth/login with returnTo when no session", () => {
    const res = middleware(req("/chat"));
    expect(res.status).toBeGreaterThanOrEqual(300);
    const loc = location(res) ?? "";
    expect(loc).toContain("/auth/login");
    expect(loc).toContain("returnTo");
    expect(loc).toContain("%2Fchat");
  });

  it("redirects /admin to /auth/login with returnTo when no session", () => {
    const res = middleware(req("/admin"));
    expect(res.status).toBeGreaterThanOrEqual(300);
    const loc = location(res) ?? "";
    expect(loc).toContain("/auth/login");
    expect(loc).toContain("%2Fadmin");
  });

  it("redirects /historial to /auth/login when no session", () => {
    const res = middleware(req("/historial"));
    expect(res.status).toBeGreaterThanOrEqual(300);
    expect(location(res)).toContain("/auth/login");
  });

  it("allows /chat when session cookie is present", () => {
    const res = middleware(req("/chat", { cookie: true }));
    expect(res.status).not.toBeGreaterThanOrEqual(300);
  });

  it("allows /admin when session cookie is present (role check is client-side)", () => {
    const res = middleware(req("/admin", { cookie: true }));
    expect(res.status).not.toBeGreaterThanOrEqual(300);
  });

  it("allows /admin/users when session cookie is present", () => {
    const res = middleware(req("/admin/users", { cookie: true }));
    expect(res.status).not.toBeGreaterThanOrEqual(300);
  });

  it("preserves search params in returnTo for protected routes", () => {
    const res = middleware(req("/buscar", { search: "?q=contrato" }));
    const loc = location(res) ?? "";
    expect(loc).toContain("returnTo");
    expect(loc).toContain("buscar");
  });
});
