/**
 * Tests for SessionsList component
 *
 * Covers AC4.1–AC4.5, AC5.1–AC5.2, AC6.3:
 *  - Populated list, empty state, loading state, error state
 *  - Read-only (no per-session revoke button)
 *  - Current session highlight when jti is present in access token
 *  - No badge when token has no jti claim
 */

import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/msw/server";

// ---------------------------------------------------------------------------
// Mocks — order matters: must precede component import
// ---------------------------------------------------------------------------

const mockAuthFetch = vi.fn();

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({ authFetch: mockAuthFetch }),
}));

vi.mock("@/lib/auth/authClient", () => ({
  getAccessToken: vi.fn().mockReturnValue(null),
}));

// ---------------------------------------------------------------------------
// Import after mocks
// ---------------------------------------------------------------------------

import { SessionsList } from "@/components/configuracion/SessionsList";
import { getAccessToken } from "@/lib/auth/authClient";

// ---------------------------------------------------------------------------
// Test data
// ---------------------------------------------------------------------------

const SESSION_A = {
  jti: "session-jti-aaaaaa",
  user_id: "user-1",
  created_at: "2026-04-01T10:00:00Z",
  expires_at: "2026-05-01T10:00:00Z",
  user_agent: "Chrome/123",
};

const SESSION_B = {
  jti: "session-jti-bbbbbb",
  user_id: "user-1",
  created_at: "2026-04-10T08:00:00Z",
  expires_at: "2026-05-10T08:00:00Z",
  user_agent: "Firefox/120",
};

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

beforeEach(() => {
  mockAuthFetch
    .mockReset()
    .mockImplementation((url: string, init?: RequestInit) => fetch(url, init));
  vi.mocked(getAccessToken).mockReturnValue(null);
  server.use(http.get("/api/auth/sessions", () => HttpResponse.json([])));
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("SessionsList", () => {
  it("renders populated sessions list", async () => {
    server.use(
      http.get("/api/auth/sessions", () =>
        HttpResponse.json([SESSION_A, SESSION_B]),
      ),
    );

    render(<SessionsList />);

    await waitFor(() => {
      expect(screen.getByTestId("sessions-list")).toBeInTheDocument();
    });
    expect(
      screen.getByTestId(`session-row-${SESSION_A.jti}`),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId(`session-row-${SESSION_B.jti}`),
    ).toBeInTheDocument();
  });

  it("renders empty state when no sessions exist", async () => {
    render(<SessionsList />);

    await waitFor(() => {
      expect(screen.getByTestId("sessions-empty")).toBeInTheDocument();
    });
  });

  it("renders error state when fetch fails", async () => {
    server.use(
      http.get("/api/auth/sessions", () =>
        new HttpResponse(null, { status: 500 }),
      ),
    );

    render(<SessionsList />);

    await waitFor(() => {
      expect(screen.getByTestId("sessions-error")).toBeInTheDocument();
    });
  });

  it("shows loading spinner before data arrives", () => {
    server.use(
      http.get("/api/auth/sessions", async () => {
        await new Promise((r) => setTimeout(r, 300));
        return HttpResponse.json([]);
      }),
    );

    render(<SessionsList />);
    expect(screen.getByTestId("sessions-loading")).toBeInTheDocument();
  });

  it("does NOT render per-session revoke buttons (read-only)", async () => {
    server.use(
      http.get("/api/auth/sessions", () => HttpResponse.json([SESSION_A])),
    );

    render(<SessionsList />);

    await waitFor(() => {
      expect(screen.getByTestId("sessions-list")).toBeInTheDocument();
    });
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("highlights the current session when jti matches the access token", async () => {
    // Build a fake token whose payload includes jti matching SESSION_A
    const payload = btoa(
      JSON.stringify({
        sub: "user-1",
        jti: SESSION_A.jti,
        type: "access",
        exp: 9999999999,
        iat: 0,
      }),
    ).replace(/=/g, "");
    vi.mocked(getAccessToken).mockReturnValue(`header.${payload}.sig`);

    server.use(
      http.get("/api/auth/sessions", () =>
        HttpResponse.json([SESSION_A, SESSION_B]),
      ),
    );

    render(<SessionsList />);

    await waitFor(() => {
      expect(screen.getByTestId("current-session-badge")).toBeInTheDocument();
    });
  });

  it("truncates jti to first 8 chars + '...'", async () => {
    server.use(
      http.get("/api/auth/sessions", () => HttpResponse.json([SESSION_A])),
    );

    render(<SessionsList />);

    await waitFor(() => {
      expect(screen.getByTestId("sessions-list")).toBeInTheDocument();
    });
    // SESSION_A.jti = "session-jti-aaaaaa" → slice(0,8) = "session-" → "session-..."
    expect(screen.getByText("session-...")).toBeInTheDocument();
  });

  it("shows 'Sesión actual' as badge text for the current session", async () => {
    const payload = btoa(
      JSON.stringify({
        sub: "user-1",
        jti: SESSION_A.jti,
        type: "access",
        exp: 9999999999,
        iat: 0,
      }),
    ).replace(/=/g, "");
    vi.mocked(getAccessToken).mockReturnValue(`header.${payload}.sig`);

    server.use(
      http.get("/api/auth/sessions", () => HttpResponse.json([SESSION_A])),
    );

    render(<SessionsList />);

    await waitFor(() => {
      expect(screen.getByTestId("current-session-badge")).toBeInTheDocument();
    });
    expect(screen.getByTestId("current-session-badge")).toHaveTextContent(
      "Sesión actual",
    );
  });

  it("does NOT show current-session badge when token has no jti claim", async () => {
    const payload = btoa(
      JSON.stringify({ sub: "user-1", type: "access", exp: 9999999999, iat: 0 }),
    ).replace(/=/g, "");
    vi.mocked(getAccessToken).mockReturnValue(`header.${payload}.sig`);

    server.use(
      http.get("/api/auth/sessions", () => HttpResponse.json([SESSION_A])),
    );

    render(<SessionsList />);

    await waitFor(() => {
      expect(screen.getByTestId("sessions-list")).toBeInTheDocument();
    });
    expect(
      screen.queryByTestId("current-session-badge"),
    ).not.toBeInTheDocument();
  });
});
