/**
 * Unit tests for the Microsoft OAuth callback page.
 *
 * Covers:
 *  - Missing `code` param → shows error UI
 *  - Backend failure → shows error UI
 *  - Successful exchange, non-admin → redirects to /chat
 *  - Successful exchange, admin → redirects to /admin
 *  - Valid same-origin `returnTo` → respected
 *  - External `returnTo` → falls back to role default
 *  - Onboarding precedence: no full_name → redirects to /onboarding
 */

import { render, waitFor, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/msw/server";
import { ACCESS_TOKEN, ADMIN_ACCESS_TOKEN } from "@/test/msw/handlers";
import MicrosoftCallbackPage from "../page";

// ---------------------------------------------------------------------------
// Mock next/navigation — useSearchParams must not suspend in tests
// ---------------------------------------------------------------------------

const mockGet = vi.fn();

vi.mock("next/navigation", () => ({
  useSearchParams: () => ({ get: mockGet }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const MICROSOFT_CALLBACK_URL = "/api/auth/oauth/microsoft/callback";

function setupParams(params: Record<string, string | null>) {
  mockGet.mockImplementation((key: string) => params[key] ?? null);
}

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------

let replaceMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  replaceMock = vi.fn();
  // Preserve all existing location properties so that fetch can still resolve
  // relative URLs via location.origin. Only replace() is mocked.
  vi.stubGlobal("location", {
    href: "http://localhost/",
    origin: "http://localhost",
    protocol: "http:",
    host: "localhost",
    hostname: "localhost",
    port: "",
    pathname: "/",
    search: "",
    hash: "",
    replace: replaceMock,
    assign: vi.fn(),
    reload: vi.fn(),
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  mockGet.mockReset();
});

// ---------------------------------------------------------------------------
// No code param
// ---------------------------------------------------------------------------

describe("MicrosoftCallbackPage — missing code", () => {
  it("shows an error when the code query param is absent", async () => {
    setupParams({ code: null, state: null, returnTo: null });
    render(<MicrosoftCallbackPage />);
    await waitFor(() => {
      expect(
        screen.getByText(/No se recibio el codigo de autorizacion de Microsoft/i),
      ).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// Backend failure
// ---------------------------------------------------------------------------

describe("MicrosoftCallbackPage — backend failure", () => {
  it("shows the error detail returned by the backend", async () => {
    setupParams({ code: "auth-code", state: "state", returnTo: null });
    server.use(
      http.post(MICROSOFT_CALLBACK_URL, () =>
        HttpResponse.json({ detail: "Token exchange failed" }, { status: 400 }),
      ),
    );
    render(<MicrosoftCallbackPage />);
    await waitFor(() => {
      expect(screen.getByText(/Token exchange failed/i)).toBeInTheDocument();
    });
  });

  it("shows a fallback error when backend returns no detail", async () => {
    setupParams({ code: "auth-code", state: "state", returnTo: null });
    server.use(
      http.post(MICROSOFT_CALLBACK_URL, () =>
        HttpResponse.json({}, { status: 500 }),
      ),
    );
    render(<MicrosoftCallbackPage />);
    await waitFor(() => {
      expect(
        screen.getByText(/Error al autenticar con Microsoft/i),
      ).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// Successful callback — role-based redirect
// ---------------------------------------------------------------------------

describe("MicrosoftCallbackPage — successful callback", () => {
  beforeEach(() => {
    // User has onboarding_completed → skip onboarding gate
    server.use(
      http.get("/api/auth/me", () =>
        HttpResponse.json({
          id: "user-1",
          email: "user@test.com",
          full_name: "Test User",
          onboarding_completed: true,
        }),
      ),
    );
  });

  it("redirects non-admin to /chat when no returnTo is present", async () => {
    setupParams({ code: "auth-code", state: "state", returnTo: null });
    server.use(
      http.post(MICROSOFT_CALLBACK_URL, () =>
        HttpResponse.json({ access_token: ACCESS_TOKEN }),
      ),
    );
    render(<MicrosoftCallbackPage />);
    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/chat");
    });
  });

  it("redirects admin to /admin when no returnTo is present", async () => {
    setupParams({ code: "auth-code", state: "state", returnTo: null });
    server.use(
      http.post(MICROSOFT_CALLBACK_URL, () =>
        HttpResponse.json({ access_token: ADMIN_ACCESS_TOKEN }),
      ),
    );
    render(<MicrosoftCallbackPage />);
    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/admin");
    });
  });

  it("honours a valid same-origin returnTo over the role default", async () => {
    setupParams({ code: "auth-code", state: "state", returnTo: "/historial" });
    server.use(
      http.post(MICROSOFT_CALLBACK_URL, () =>
        HttpResponse.json({ access_token: ACCESS_TOKEN }),
      ),
    );
    render(<MicrosoftCallbackPage />);
    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/historial");
    });
  });

  it("ignores an external returnTo and falls back to /chat for non-admin", async () => {
    setupParams({
      code: "auth-code",
      state: "state",
      returnTo: "https://evil.com",
    });
    server.use(
      http.post(MICROSOFT_CALLBACK_URL, () =>
        HttpResponse.json({ access_token: ACCESS_TOKEN }),
      ),
    );
    render(<MicrosoftCallbackPage />);
    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/chat");
      expect(replaceMock).not.toHaveBeenCalledWith(
        expect.stringContaining("evil.com"),
      );
    });
  });
});

// ---------------------------------------------------------------------------
// Onboarding precedence
// ---------------------------------------------------------------------------

describe("MicrosoftCallbackPage — onboarding precedence", () => {
  it("redirects to /onboarding when onboarding_completed is false", async () => {
    setupParams({ code: "auth-code", state: "state", returnTo: null });
    server.use(
      http.post(MICROSOFT_CALLBACK_URL, () =>
        HttpResponse.json({ access_token: ACCESS_TOKEN }),
      ),
      http.get("/api/auth/me", () =>
        HttpResponse.json({
          id: "user-1",
          email: "user@test.com",
          full_name: "Test User",
          onboarding_completed: false,
        }),
      ),
    );
    render(<MicrosoftCallbackPage />);
    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/onboarding");
    });
  });

  it("falls through to role-based redirect when /me fetch fails", async () => {
    setupParams({ code: "auth-code", state: "state", returnTo: null });
    server.use(
      http.post(MICROSOFT_CALLBACK_URL, () =>
        HttpResponse.json({ access_token: ACCESS_TOKEN }),
      ),
      http.get("/api/auth/me", () => HttpResponse.error()),
    );
    render(<MicrosoftCallbackPage />);
    // /me fails → non-blocking → falls through to role redirect
    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/chat");
    });
  });
});
