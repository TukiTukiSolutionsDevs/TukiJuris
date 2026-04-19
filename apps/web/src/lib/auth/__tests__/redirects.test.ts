import { describe, expect, it } from "vitest";
import {
  validateReturnTo,
  resolvePostLoginDestination,
} from "../redirects";

// ---------------------------------------------------------------------------
// validateReturnTo
// ---------------------------------------------------------------------------

describe("validateReturnTo", () => {
  it("returns null for null", () => {
    expect(validateReturnTo(null)).toBeNull();
  });

  it("returns null for undefined", () => {
    expect(validateReturnTo(undefined)).toBeNull();
  });

  it("returns null for empty string", () => {
    expect(validateReturnTo("")).toBeNull();
  });

  it("returns null for http:// URLs (external)", () => {
    expect(validateReturnTo("http://evil.com/steal")).toBeNull();
  });

  it("returns null for https:// URLs (external)", () => {
    expect(validateReturnTo("https://evil.com")).toBeNull();
  });

  it("returns null for protocol-relative URLs (//evil.com)", () => {
    expect(validateReturnTo("//evil.com/steal")).toBeNull();
  });

  it("returns null for /auth/login (redirect loop)", () => {
    expect(validateReturnTo("/auth/login")).toBeNull();
  });

  it("returns null for /auth/login?reason=expired (redirect loop)", () => {
    expect(validateReturnTo("/auth/login?reason=expired")).toBeNull();
  });

  it("returns null for /auth/register (redirect loop)", () => {
    expect(validateReturnTo("/auth/register")).toBeNull();
  });

  it("accepts /historial (valid same-origin path)", () => {
    expect(validateReturnTo("/historial")).toBe("/historial");
  });

  it("accepts /admin/users (valid same-origin admin path)", () => {
    expect(validateReturnTo("/admin/users")).toBe("/admin/users");
  });

  it("accepts / (root path)", () => {
    expect(validateReturnTo("/")).toBe("/");
  });

  it("accepts paths with query strings", () => {
    expect(validateReturnTo("/buscar?q=contrato")).toBe("/buscar?q=contrato");
  });

  it("accepts /onboarding", () => {
    expect(validateReturnTo("/onboarding")).toBe("/onboarding");
  });
});

// ---------------------------------------------------------------------------
// resolvePostLoginDestination
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// resolvePostLoginDestination — 8 combinations + idempotency (AC1-5, AC15)
// ---------------------------------------------------------------------------

describe("resolvePostLoginDestination — onboarding flag combinations", () => {
  // Combo 1: returnTo valid, user not onboarded
  it("C1: valid returnTo, non-admin, not onboarded → returnTo wins", () => {
    expect(resolvePostLoginDestination("/historial", false, false)).toBe("/historial");
  });

  // Combo 2: returnTo valid, user onboarded
  it("C2: valid returnTo, non-admin, onboarded → returnTo wins", () => {
    expect(resolvePostLoginDestination("/historial", false, true)).toBe("/historial");
  });

  // Combo 3: returnTo valid, admin, not onboarded
  it("C3: valid returnTo, admin, not onboarded → returnTo wins", () => {
    expect(resolvePostLoginDestination("/historial", true, false)).toBe("/historial");
  });

  // Combo 4: returnTo valid, admin, onboarded
  it("C4: valid returnTo, admin, onboarded → returnTo wins", () => {
    expect(resolvePostLoginDestination("/historial", true, true)).toBe("/historial");
  });

  // Combo 5: no returnTo, user not onboarded
  it("C5: no returnTo, non-admin, not onboarded → /onboarding", () => {
    expect(resolvePostLoginDestination(null, false, false)).toBe("/onboarding");
  });

  // Combo 6: no returnTo, user onboarded
  it("C6: no returnTo, non-admin, onboarded → ROUTE_AFTER_LOGIN_USER", () => {
    expect(resolvePostLoginDestination(null, false, true)).toBe("/chat");
  });

  // Combo 7: no returnTo, admin not onboarded
  it("C7: no returnTo, admin, not onboarded → /onboarding (onboarding takes precedence over admin route)", () => {
    expect(resolvePostLoginDestination(null, true, false)).toBe("/onboarding");
  });

  // Combo 8: no returnTo, admin onboarded
  it("C8: no returnTo, admin, onboarded → ROUTE_AFTER_LOGIN_ADMIN", () => {
    expect(resolvePostLoginDestination(null, true, true)).toBe("/admin");
  });

  // Idempotency edge (AC15): returnTo="/onboarding" but user already onboarded → skip loop
  it("idempotency: returnTo=/onboarding, onboarded=true, non-admin → falls through to /chat", () => {
    expect(resolvePostLoginDestination("/onboarding", false, true)).toBe("/chat");
  });

  it("idempotency: returnTo=/onboarding, onboarded=true, admin → falls through to /admin", () => {
    expect(resolvePostLoginDestination("/onboarding", true, true)).toBe("/admin");
  });

  // returnTo="/onboarding" while NOT onboarded should use returnTo (valid path)
  it("returnTo=/onboarding + not onboarded → /onboarding is a valid returnTo (no idempotency guard)", () => {
    expect(resolvePostLoginDestination("/onboarding", false, false)).toBe("/onboarding");
  });
});

// All pre-existing tests assume user is already onboarded (onboardingCompleted=true)
// so they pass `true` as the third argument.
describe("resolvePostLoginDestination", () => {
  describe("returnTo precedence over role default", () => {
    it("uses a valid returnTo for a regular user", () => {
      expect(resolvePostLoginDestination("/historial", false, true)).toBe("/historial");
    });

    it("uses a valid returnTo for an admin user", () => {
      expect(resolvePostLoginDestination("/historial", true, true)).toBe("/historial");
    });

    it("uses /admin returnTo for an admin when explicitly provided", () => {
      expect(resolvePostLoginDestination("/admin/users", true, true)).toBe("/admin/users");
    });
  });

  describe("role-based default when returnTo is absent or invalid", () => {
    it("returns /admin for admin with null returnTo", () => {
      expect(resolvePostLoginDestination(null, true, true)).toBe("/admin");
    });

    it("returns /chat for regular user with null returnTo", () => {
      expect(resolvePostLoginDestination(null, false, true)).toBe("/chat");
    });

    it("returns /admin for admin with undefined returnTo", () => {
      expect(resolvePostLoginDestination(undefined, true, true)).toBe("/admin");
    });

    it("returns /chat for regular user with undefined returnTo", () => {
      expect(resolvePostLoginDestination(undefined, false, true)).toBe("/chat");
    });

    it("ignores external returnTo and falls back to role default (admin)", () => {
      expect(resolvePostLoginDestination("https://evil.com", true, true)).toBe("/admin");
    });

    it("ignores external returnTo and falls back to role default (user)", () => {
      expect(resolvePostLoginDestination("https://evil.com", false, true)).toBe("/chat");
    });

    it("ignores protocol-relative returnTo and falls back to role default", () => {
      expect(resolvePostLoginDestination("//evil.com/steal", false, true)).toBe("/chat");
    });

    it("ignores /auth/login returnTo (loop) and falls back to role default", () => {
      expect(resolvePostLoginDestination("/auth/login", false, true)).toBe("/chat");
    });
  });
});
