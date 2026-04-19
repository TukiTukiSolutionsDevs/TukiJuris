/**
 * Unit tests for the Google OAuth callback page.
 *
 * Covers:
 *  - Missing `code` param → shows error UI
 *  - Backend failure → shows error UI
 *  - Successful exchange, non-admin → redirects to /chat
 *  - Successful exchange, admin → redirects to /admin
 *  - `returnto` from response body respected (backend-authoritative)
 *  - Defense-in-depth: absolute URL in `returnto` → falls back to role default
 *  - Onboarding precedence: onboarding_completed false → redirects to /onboarding
 */

import { render, waitFor, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/msw/server";
import { ACCESS_TOKEN, ADMIN_ACCESS_TOKEN } from "@/test/msw/handlers";
import GoogleCallbackPage from "../page";

// ---------------------------------------------------------------------------
// Mock next/navigation — useSearchParams must not suspend in tests
// ---------------------------------------------------------------------------

const mockGet = vi.fn();
const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useSearchParams: () => ({ get: mockGet }),
  useRouter: () => ({ push: pushMock }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const GOOGLE_CALLBACK_URL = "/api/auth/oauth/google/callback";

function setupParams(params: Record<string, string | null>) {
  mockGet.mockImplementation((key: string) => params[key] ?? null);
}

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  // Preserve all existing location properties so that fetch can still resolve
  // relative URLs via location.origin.
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
    replace: vi.fn(),
    assign: vi.fn(),
    reload: vi.fn(),
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  mockGet.mockReset();
  pushMock.mockReset();
});

// ---------------------------------------------------------------------------
// No code param
// ---------------------------------------------------------------------------

describe("GoogleCallbackPage — missing code", () => {
  it("shows an error when the code query param is absent", async () => {
    setupParams({ code: null, state: null });
    render(<GoogleCallbackPage />);
    await waitFor(() => {
      expect(
        screen.getByText(/No se recibio el codigo de autorizacion de Google/i),
      ).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// Backend failure
// ---------------------------------------------------------------------------

describe("GoogleCallbackPage — backend failure", () => {
  it("shows the error detail returned by the backend", async () => {
    setupParams({ code: "auth-code", state: "state" });
    server.use(
      http.post(GOOGLE_CALLBACK_URL, () =>
        HttpResponse.json({ detail: "Token exchange failed" }, { status: 400 }),
      ),
    );
    render(<GoogleCallbackPage />);
    await waitFor(() => {
      expect(screen.getByText(/Token exchange failed/i)).toBeInTheDocument();
    });
  });

  it("shows a fallback error when backend returns no detail", async () => {
    setupParams({ code: "auth-code", state: "state" });
    server.use(
      http.post(GOOGLE_CALLBACK_URL, () =>
        HttpResponse.json({}, { status: 500 }),
      ),
    );
    render(<GoogleCallbackPage />);
    await waitFor(() => {
      expect(
        screen.getByText(/Error al autenticar con Google/i),
      ).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// Successful callback — role-based redirect
// ---------------------------------------------------------------------------

describe("GoogleCallbackPage — successful callback", () => {
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

  it("redirects non-admin to /chat when no returnto in response", async () => {
    setupParams({ code: "auth-code", state: "state" });
    server.use(
      http.post(GOOGLE_CALLBACK_URL, () =>
        HttpResponse.json({ access_token: ACCESS_TOKEN, returnto: null }),
      ),
    );
    render(<GoogleCallbackPage />);
    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/chat");
    });
  });

  it("redirects admin to /admin when no returnto in response", async () => {
    setupParams({ code: "auth-code", state: "state" });
    server.use(
      http.post(GOOGLE_CALLBACK_URL, () =>
        HttpResponse.json({ access_token: ADMIN_ACCESS_TOKEN, returnto: null }),
      ),
    );
    render(<GoogleCallbackPage />);
    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/admin");
    });
  });

  it("honours a valid returnto from the response body", async () => {
    setupParams({ code: "auth-code", state: "state" });
    server.use(
      http.post(GOOGLE_CALLBACK_URL, () =>
        HttpResponse.json({ access_token: ACCESS_TOKEN, returnto: "/historial" }),
      ),
    );
    render(<GoogleCallbackPage />);
    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/historial");
    });
  });

  it("falls back to role default when returnto is an absolute URL (defense-in-depth)", async () => {
    setupParams({ code: "auth-code", state: "state" });
    server.use(
      http.post(GOOGLE_CALLBACK_URL, () =>
        HttpResponse.json({ access_token: ACCESS_TOKEN, returnto: "https://evil.com" }),
      ),
    );
    render(<GoogleCallbackPage />);
    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/chat");
      expect(pushMock).not.toHaveBeenCalledWith(
        expect.stringContaining("evil.com"),
      );
    });
  });
});

// ---------------------------------------------------------------------------
// Onboarding precedence
// ---------------------------------------------------------------------------

describe("GoogleCallbackPage — onboarding precedence", () => {
  it("redirects to /onboarding when onboarding_completed is false", async () => {
    setupParams({ code: "auth-code", state: "state" });
    server.use(
      http.post(GOOGLE_CALLBACK_URL, () =>
        HttpResponse.json({ access_token: ACCESS_TOKEN, returnto: null }),
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
    render(<GoogleCallbackPage />);
    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/onboarding");
    });
  });

  it("falls through to role-based redirect when /me fetch fails", async () => {
    setupParams({ code: "auth-code", state: "state" });
    server.use(
      http.post(GOOGLE_CALLBACK_URL, () =>
        HttpResponse.json({ access_token: ACCESS_TOKEN, returnto: null }),
      ),
      http.get("/api/auth/me", () => HttpResponse.error()),
    );
    render(<GoogleCallbackPage />);
    // /me fails → non-blocking → falls through to role redirect
    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/chat");
    });
  });
});
