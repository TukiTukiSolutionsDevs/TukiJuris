/**
 * Focused tests for the "Cerrar todas las sesiones" (logout-all) button
 * in the configuracion page.
 *
 * Covers:
 *  - Button renders in the perfil tab (default active tab)
 *  - Clicking it calls logoutAll() from AuthContext
 *  - logoutAll() is NOT called on mount (no accidental invocation)
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/msw/server";

// ---------------------------------------------------------------------------
// Mock AuthContext
// ---------------------------------------------------------------------------

const mockLogoutAll = vi.fn();
const mockLogout = vi.fn();
const mockAuthFetch = vi.fn();

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({
    authFetch: mockAuthFetch,
    logout: mockLogout,
    logoutAll: mockLogoutAll,
    user: { id: "user-1", email: "test@test.com", isAdmin: false },
    onboardingCompleted: true,
  }),
}));

// ---------------------------------------------------------------------------
// Mock next/navigation
// ---------------------------------------------------------------------------

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/configuracion",
  useSearchParams: () => ({ get: () => null }),
}));

// ---------------------------------------------------------------------------
// Import page after mocks
// ---------------------------------------------------------------------------

import ConfiguracionPage from "../page";

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

beforeEach(() => {
  mockLogoutAll.mockReset().mockResolvedValue(undefined);
  mockLogout.mockReset().mockResolvedValue(undefined);
  // authFetch is used inside loadData — return sensible defaults
  mockAuthFetch.mockReset().mockImplementation((url: string) => {
    if (url.includes("/api/auth/me")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            id: "user-1",
            email: "test@test.com",
            name: "Test User",
            full_name: "Test User",
            onboarding_completed: true,
          }),
      });
    }
    if (url.includes("/api/organizations/")) {
      return Promise.resolve({ ok: false, json: () => Promise.resolve([]) });
    }
    return Promise.resolve({ ok: false, json: () => Promise.resolve({}) });
  });

  // Also cover MSW path — in case authFetch falls through to fetch
  server.use(
    http.get("/api/organizations/", () => HttpResponse.json([])),
    http.get("/api/auth/me/permissions", () => HttpResponse.json({})),
  );
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("configuracion — logout-all button", () => {
  it("renders the 'Cerrar todas las sesiones' button in the perfil tab", async () => {
    render(<ConfiguracionPage />);
    await waitFor(() => {
      expect(
        screen.getByTestId("logout-all-btn"),
      ).toBeInTheDocument();
    });
  });

  it("calls logoutAll() when the button is clicked", async () => {
    const user = userEvent.setup();
    render(<ConfiguracionPage />);

    const btn = await screen.findByTestId("logout-all-btn");
    await user.click(btn);

    await waitFor(() => {
      expect(mockLogoutAll).toHaveBeenCalledTimes(1);
    });
  });

  it("does NOT call logoutAll() on mount", async () => {
    render(<ConfiguracionPage />);
    // Let the page fully initialize
    await screen.findByTestId("logout-all-btn");
    expect(mockLogoutAll).not.toHaveBeenCalled();
  });
});
