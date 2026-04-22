/**
 * Middleware admin gate tests — FAT-1..5
 *
 * Covers the tk_admin cookie check added for ADMIN_PATH_PREFIXES
 * (/admin/**, /analytics/**) per frontend-admin-route-hardening spec.
 *
 * Strategy: import the middleware function directly, construct NextRequest
 * instances with explicit cookie headers, assert the response status and
 * Location header. No React, no MSW — pure function tests.
 */

import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";
import { middleware, config } from "../middleware";
import {
  ADMIN_MARKER_COOKIE,
  ADMIN_MARKER_VALUE,
  SESSION_MARKER_COOKIE,
} from "../lib/constants";

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

function makeRequest(
  pathname: string,
  cookies: { session?: boolean; admin?: boolean } = {},
): NextRequest {
  const url = new URL(pathname, "http://localhost");
  const r = new NextRequest(url);
  if (cookies.session) {
    r.cookies.set(SESSION_MARKER_COOKIE, "1");
  }
  if (cookies.admin) {
    r.cookies.set(ADMIN_MARKER_COOKIE, ADMIN_MARKER_VALUE);
  }
  return r;
}

function location(res: Response): string | null {
  return res.headers.get("location");
}

// ---------------------------------------------------------------------------
// FAT-1: Anonymous → /admin/users → redirect to /login
// ---------------------------------------------------------------------------

describe("FAT-1: anonymous user → /admin/users → redirect to /login", () => {
  it("redirects to /auth/login and includes returnTo", () => {
    const res = middleware(makeRequest("/admin/users"));
    expect(res.status).toBeGreaterThanOrEqual(300);
    expect(res.status).toBeLessThan(400);
    const loc = location(res) ?? "";
    expect(loc).toContain("/auth/login");
    expect(loc).toContain("returnTo");
  });
});

// ---------------------------------------------------------------------------
// FAT-2: Auth non-admin → /admin/users → redirect to /
// ---------------------------------------------------------------------------

describe("FAT-2: authenticated non-admin → /admin/users → redirect to /", () => {
  it("redirects to / when tk_session present but tk_admin absent", () => {
    const res = middleware(makeRequest("/admin/users", { session: true }));
    expect(res.status).toBeGreaterThanOrEqual(300);
    expect(res.status).toBeLessThan(400);
    expect(location(res)).toBe("http://localhost/");
  });
});

// ---------------------------------------------------------------------------
// FAT-3: Auth admin → /admin/users → pass-through
// ---------------------------------------------------------------------------

describe("FAT-3: authenticated admin → /admin/users → pass-through", () => {
  it("allows the request when both tk_session and tk_admin are present", () => {
    const res = middleware(
      makeRequest("/admin/users", { session: true, admin: true }),
    );
    expect(res.status).not.toBeGreaterThanOrEqual(300);
  });
});

// ---------------------------------------------------------------------------
// FAT-4: Auth non-admin → /analytics → redirect to /
// ---------------------------------------------------------------------------

describe("FAT-4: authenticated non-admin → /analytics → redirect to /", () => {
  it("redirects to / when tk_session present but tk_admin absent on /analytics", () => {
    const res = middleware(makeRequest("/analytics", { session: true }));
    expect(res.status).toBeGreaterThanOrEqual(300);
    expect(res.status).toBeLessThan(400);
    expect(location(res)).toBe("http://localhost/");
  });
});

// ---------------------------------------------------------------------------
// FAT-5: Auth admin → /analytics → pass-through
// ---------------------------------------------------------------------------

describe("FAT-5: authenticated admin → /analytics → pass-through", () => {
  it("allows /analytics when both tk_session and tk_admin are present", () => {
    const res = middleware(
      makeRequest("/analytics", { session: true, admin: true }),
    );
    expect(res.status).not.toBeGreaterThanOrEqual(300);
  });
});

// ---------------------------------------------------------------------------
// FAH-5: middleware matcher covers /admin/* and /analytics/*
// ---------------------------------------------------------------------------

describe("FAH-5: middleware matcher covers admin and analytics paths", () => {
  it("matcher pattern includes /((?!_next/static|_next/image|favicon.ico).*)", () => {
    const expectedPattern = "/((?!_next/static|_next/image|favicon.ico).*)";
    expect(config.matcher).toContain(expectedPattern);
  });
});
