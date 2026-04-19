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

describe("resolvePostLoginDestination", () => {
  describe("returnTo precedence over role default", () => {
    it("uses a valid returnTo for a regular user", () => {
      expect(resolvePostLoginDestination("/historial", false)).toBe("/historial");
    });

    it("uses a valid returnTo for an admin user", () => {
      expect(resolvePostLoginDestination("/historial", true)).toBe("/historial");
    });

    it("uses /admin returnTo for an admin when explicitly provided", () => {
      expect(resolvePostLoginDestination("/admin/users", true)).toBe("/admin/users");
    });
  });

  describe("role-based default when returnTo is absent or invalid", () => {
    it("returns /admin for admin with null returnTo", () => {
      expect(resolvePostLoginDestination(null, true)).toBe("/admin");
    });

    it("returns /chat for regular user with null returnTo", () => {
      expect(resolvePostLoginDestination(null, false)).toBe("/chat");
    });

    it("returns /admin for admin with undefined returnTo", () => {
      expect(resolvePostLoginDestination(undefined, true)).toBe("/admin");
    });

    it("returns /chat for regular user with undefined returnTo", () => {
      expect(resolvePostLoginDestination(undefined, false)).toBe("/chat");
    });

    it("ignores external returnTo and falls back to role default (admin)", () => {
      expect(resolvePostLoginDestination("https://evil.com", true)).toBe("/admin");
    });

    it("ignores external returnTo and falls back to role default (user)", () => {
      expect(resolvePostLoginDestination("https://evil.com", false)).toBe("/chat");
    });

    it("ignores protocol-relative returnTo and falls back to role default", () => {
      expect(resolvePostLoginDestination("//evil.com/steal", false)).toBe("/chat");
    });

    it("ignores /auth/login returnTo (loop) and falls back to role default", () => {
      expect(resolvePostLoginDestination("/auth/login", false)).toBe("/chat");
    });
  });
});
