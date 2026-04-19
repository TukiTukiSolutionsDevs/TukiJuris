/**
 * Tests for returnto threading in the Register page SSO buttons.
 *
 * Covers:
 *  - On /auth/* page → no returnto appended to authorize URL
 *  - On / (root) → no returnto appended
 *  - On a non-auth, non-root page → returnto=<pathname> appended
 *  - Both Google and Microsoft providers
 */

import { render, waitFor, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/msw/server";
import RegisterPage from "../page";

// ---------------------------------------------------------------------------
// Module mocks
// ---------------------------------------------------------------------------

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  useSearchParams: () => ({ get: vi.fn().mockReturnValue(null) }),
}));

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({
    user: null,
    isLoading: false,
    register: vi.fn(),
  }),
}));

vi.mock("@/components/ThemeProvider", () => ({
  useTheme: () => ({ theme: "light" }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const API_BASE = "http://localhost:8000/api/auth/oauth";
const OAUTH_REDIRECT = "https://login.microsoftonline.com/oauth2/auth?state=xyz";

function stubLocation(pathname: string) {
  vi.stubGlobal("location", {
    href: `http://localhost${pathname}`,
    origin: "http://localhost",
    protocol: "http:",
    host: "localhost",
    hostname: "localhost",
    port: "",
    pathname,
    search: "",
    hash: "",
    replace: vi.fn(),
    assign: vi.fn(),
    reload: vi.fn(),
  });
}

function interceptAuthorize(provider: "google" | "microsoft") {
  const spy = vi.fn((url: string) => url);
  server.use(
    http.get(`${API_BASE}/${provider}/authorize`, ({ request }) => {
      spy(request.url);
      return HttpResponse.json({ url: OAUTH_REDIRECT });
    }),
  );
  return spy;
}

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  // Default: currently on the register page itself
  stubLocation("/auth/register");
});

afterEach(() => {
  vi.unstubAllGlobals();
});

// ---------------------------------------------------------------------------
// Google SSO
// ---------------------------------------------------------------------------

describe("RegisterPage — Google SSO returnto", () => {
  it("omits returnto when already on /auth/register", async () => {
    const spy = interceptAuthorize("google");
    render(<RegisterPage />);
    fireEvent.click(screen.getByRole("button", { name: /google/i }));
    await waitFor(() => expect(spy).toHaveBeenCalled());
    const called = new URL(spy.mock.calls[0][0]);
    expect(called.searchParams.has("returnto")).toBe(false);
  });

  it("omits returnto when on /auth/login", async () => {
    stubLocation("/auth/login");
    const spy = interceptAuthorize("google");
    render(<RegisterPage />);
    fireEvent.click(screen.getByRole("button", { name: /google/i }));
    await waitFor(() => expect(spy).toHaveBeenCalled());
    const called = new URL(spy.mock.calls[0][0]);
    expect(called.searchParams.has("returnto")).toBe(false);
  });

  it("omits returnto when on root /", async () => {
    stubLocation("/");
    const spy = interceptAuthorize("google");
    render(<RegisterPage />);
    fireEvent.click(screen.getByRole("button", { name: /google/i }));
    await waitFor(() => expect(spy).toHaveBeenCalled());
    const called = new URL(spy.mock.calls[0][0]);
    expect(called.searchParams.has("returnto")).toBe(false);
  });

  it("appends returnto when on a regular page", async () => {
    stubLocation("/historial");
    const spy = interceptAuthorize("google");
    render(<RegisterPage />);
    fireEvent.click(screen.getByRole("button", { name: /google/i }));
    await waitFor(() => expect(spy).toHaveBeenCalled());
    const called = new URL(spy.mock.calls[0][0]);
    expect(called.searchParams.get("returnto")).toBe("/historial");
  });

  it("appends encoded returnto for nested paths", async () => {
    stubLocation("/casos/abc-123/detalle");
    const spy = interceptAuthorize("google");
    render(<RegisterPage />);
    fireEvent.click(screen.getByRole("button", { name: /google/i }));
    await waitFor(() => expect(spy).toHaveBeenCalled());
    const called = new URL(spy.mock.calls[0][0]);
    expect(called.searchParams.get("returnto")).toBe("/casos/abc-123/detalle");
  });
});

// ---------------------------------------------------------------------------
// Microsoft SSO
// ---------------------------------------------------------------------------

describe("RegisterPage — Microsoft SSO returnto", () => {
  it("omits returnto when already on /auth/register", async () => {
    const spy = interceptAuthorize("microsoft");
    render(<RegisterPage />);
    fireEvent.click(screen.getByRole("button", { name: /microsoft/i }));
    await waitFor(() => expect(spy).toHaveBeenCalled());
    const called = new URL(spy.mock.calls[0][0]);
    expect(called.searchParams.has("returnto")).toBe(false);
  });

  it("appends returnto when on a regular page", async () => {
    stubLocation("/consultas");
    const spy = interceptAuthorize("microsoft");
    render(<RegisterPage />);
    fireEvent.click(screen.getByRole("button", { name: /microsoft/i }));
    await waitFor(() => expect(spy).toHaveBeenCalled());
    const called = new URL(spy.mock.calls[0][0]);
    expect(called.searchParams.get("returnto")).toBe("/consultas");
  });
});
