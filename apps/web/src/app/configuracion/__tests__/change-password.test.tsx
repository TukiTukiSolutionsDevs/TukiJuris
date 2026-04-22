/**
 * Change-password flow tests — configuracion page
 *
 * Covers FCT-1..FCT-8 per the spec test matrix.
 *
 * Strategy:
 *  - mockAuthFetch forwards POST /api/auth/change-password to native fetch,
 *    which MSW intercepts. Per-test server.use() overrides take full effect.
 *  - FCT-1 + FCT-8 (timer-based) spy on setTimeout, extract the 1500 ms
 *    callback, and call it directly — no fake-timer / waitFor conflicts.
 */

import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/msw/server";
import { authHandlers } from "@/test/msw/handlers";

// ---------------------------------------------------------------------------
// Stable mock refs
// ---------------------------------------------------------------------------

const mockLogout = vi.fn();
const mockLogoutAll = vi.fn();
const mockAuthFetch = vi.fn();
const mockPush = vi.fn();

// ---------------------------------------------------------------------------
// Mock AuthContext
// ---------------------------------------------------------------------------

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
  useRouter: () => ({ push: mockPush, replace: vi.fn() }),
  usePathname: () => "/configuracion",
  useSearchParams: () => ({ get: () => null }),
}));

// ---------------------------------------------------------------------------
// Import page AFTER mocks
// ---------------------------------------------------------------------------

import ConfiguracionPage from "../page";

// ---------------------------------------------------------------------------
// Helper: configure mockAuthFetch
// profileOverrides are merged into the /api/auth/me response so FCT-7 can
// inject auth_provider: "microsoft".
// ---------------------------------------------------------------------------

function setupAuthFetch(profileOverrides: Record<string, unknown> = {}) {
  mockAuthFetch.mockImplementation(async (url: string, options?: RequestInit) => {
    if (url.includes("/api/auth/me")) {
      return {
        ok: true,
        json: () =>
          Promise.resolve({
            id: "user-1",
            email: "test@test.com",
            name: "Test User",
            onboarding_completed: true,
            ...profileOverrides,
          }),
      };
    }
    if (url.includes("/api/organizations/")) {
      return { ok: false, json: () => Promise.resolve([]) };
    }
    if (url.includes("/api/auth/change-password")) {
      // Forward to MSW so per-test server.use() overrides take effect
      return fetch(url, {
        method: options?.method ?? "POST",
        body: options?.body as BodyInit | undefined,
        headers: { "Content-Type": "application/json" },
      });
    }
    return { ok: false, json: () => Promise.resolve({}) };
  });
}

// ---------------------------------------------------------------------------
// Helpers: open panel + fill and submit the form
// ---------------------------------------------------------------------------

async function openPasswordPanel(user: ReturnType<typeof userEvent.setup>) {
  // DisclosureCard toggle button — accessible name includes "Cambiar contraseña"
  const btn = await screen.findByRole("button", { name: /cambiar contraseña/i });
  await user.click(btn);
}

async function fillAndSubmit(
  user: ReturnType<typeof userEvent.setup>,
  {
    current = "currentpass",
    newPw = "newpassword123",
    confirm = "newpassword123",
  }: { current?: string; newPw?: string; confirm?: string } = {},
) {
  await user.type(screen.getByPlaceholderText("••••••••"), current);
  await user.type(screen.getByPlaceholderText(/minimo 8/i), newPw);
  await user.type(screen.getByPlaceholderText(/repite/i), confirm);
  // "Actualizar contrasena" — no ñ in source, won't match DisclosureCard description
  await user.click(screen.getByRole("button", { name: /actualizar contrasena/i }));
}

// ---------------------------------------------------------------------------
// Global beforeEach / afterEach
// ---------------------------------------------------------------------------

beforeEach(() => {
  mockLogout.mockReset().mockResolvedValue(undefined);
  mockLogoutAll.mockReset().mockResolvedValue(undefined);
  mockAuthFetch.mockReset();
  mockPush.mockReset();
  setupAuthFetch();
  server.use(
    http.get("/api/organizations/", () => HttpResponse.json([])),
    http.get("/api/auth/me/permissions", () => HttpResponse.json({})),
  );
});

afterEach(() => {
  server.resetHandlers();
});

// ===========================================================================
// FCT-2..FCT-7 — error paths + OAuth UI (real timers)
// ===========================================================================

describe("configuracion — change-password error paths", () => {
  it("FCT-2: wrong current password (401 invalid_credentials) shows specific error, no reset, no logout", async () => {
    server.use(authHandlers.changePasswordError("invalid_credentials", 401));
    const user = userEvent.setup();
    render(<ConfiguracionPage />);

    await openPasswordPanel(user);
    await fillAndSubmit(user);

    await waitFor(() => {
      expect(
        screen.getByText("La contraseña actual es incorrecta."),
      ).toBeInTheDocument();
    });

    // FCB-1: form fields must NOT be reset on error
    expect(screen.getByPlaceholderText("••••••••")).toHaveValue("currentpass");
    // FCB-1: logout must NOT be triggered
    expect(mockLogout).not.toHaveBeenCalled();
  });

  it("FCT-3: OAuth user (400 oauth_password_unsupported) interpolates provider name", async () => {
    server.use(
      authHandlers.changePasswordError(
        { code: "oauth_password_unsupported", auth_provider: "microsoft" },
        400,
      ),
    );
    const user = userEvent.setup();
    render(<ConfiguracionPage />);

    await openPasswordPanel(user);
    await fillAndSubmit(user);

    await waitFor(() => {
      expect(screen.getByText(/(microsoft)/)).toBeInTheDocument();
    });
  });

  it("FCT-4: new == current (400 new_password_same_as_current) shows correct message", async () => {
    server.use(authHandlers.changePasswordError("new_password_same_as_current", 400));
    const user = userEvent.setup();
    render(<ConfiguracionPage />);

    await openPasswordPanel(user);
    await fillAndSubmit(user);

    await waitFor(() => {
      expect(
        screen.getByText("La nueva contraseña debe ser distinta a la actual."),
      ).toBeInTheDocument();
    });
  });

  it("FCT-5: weak password (422) shows verbatim validator message", async () => {
    server.use(authHandlers.changePasswordError("Mínimo 8 caracteres", 422));
    const user = userEvent.setup();
    render(<ConfiguracionPage />);

    await openPasswordPanel(user);
    await fillAndSubmit(user);

    await waitFor(() => {
      expect(screen.getByText("Mínimo 8 caracteres")).toBeInTheDocument();
    });
  });

  it("FCT-6: rate limit (429) shows rate-limit copy", async () => {
    server.use(authHandlers.changePasswordError(null, 429));
    const user = userEvent.setup();
    render(<ConfiguracionPage />);

    await openPasswordPanel(user);
    await fillAndSubmit(user);

    await waitFor(() => {
      expect(
        screen.getByText("Demasiados intentos. Esperá un momento e intentá de nuevo."),
      ).toBeInTheDocument();
    });
  });

  it("FCT-7: OAuth profile hides password section and renders info card", async () => {
    setupAuthFetch({ auth_provider: "microsoft" });
    render(<ConfiguracionPage />);

    // Info card must be visible with the provider name
    await waitFor(() => {
      expect(screen.getByText(/gestionada en microsoft/i)).toBeInTheDocument();
    });

    // Password form inputs must NOT be rendered (FCB-10)
    expect(screen.queryByPlaceholderText("••••••••")).not.toBeInTheDocument();
  });
});

// ===========================================================================
// FCT-1 + FCT-8 — success path with 1500 ms logout timer
// We spy on setTimeout, extract the callback, and invoke it directly.
// This avoids fake-timer / waitFor polling conflicts entirely.
// ===========================================================================

describe("configuracion — change-password success path", () => {
  it("FCT-1: 204 → success toast visible + logout called + redirect to /login after 1500 ms", async () => {
    const setTimeoutSpy = vi.spyOn(globalThis, "setTimeout");
    const user = userEvent.setup();
    render(<ConfiguracionPage />);

    await openPasswordPanel(user);
    await fillAndSubmit(user);

    // Toast must appear (FCB-7)
    await waitFor(() => {
      expect(
        screen.getByText(/contraseña actualizada\. por seguridad/i),
      ).toBeInTheDocument();
    });

    // FCB-9: form fields must be cleared immediately after toast (before logout timer fires)
    expect(screen.getByPlaceholderText("••••••••")).toHaveValue("");
    expect(screen.getByPlaceholderText(/minimo 8/i)).toHaveValue("");
    expect(screen.getByPlaceholderText(/repite/i)).toHaveValue("");

    // Extract and invoke the 1500 ms callback (FCB-8)
    const logoutCall = setTimeoutSpy.mock.calls.find(([, ms]) => ms === 1500);
    expect(logoutCall).toBeDefined();
    const callback = logoutCall![0] as () => Promise<void>;
    await act(async () => { await callback(); });

    expect(mockLogout).toHaveBeenCalledTimes(1);
    expect(mockPush).toHaveBeenCalledWith("/login");

    setTimeoutSpy.mockRestore();
  });

  it("FCT-8: logout rejection still calls router.push('/login')", async () => {
    mockLogout.mockRejectedValue(new Error("Network error"));
    const setTimeoutSpy = vi.spyOn(globalThis, "setTimeout");
    const user = userEvent.setup();
    render(<ConfiguracionPage />);

    await openPasswordPanel(user);
    await fillAndSubmit(user);

    await waitFor(() => {
      expect(
        screen.getByText(/contraseña actualizada\. por seguridad/i),
      ).toBeInTheDocument();
    });

    const logoutCall = setTimeoutSpy.mock.calls.find(([, ms]) => ms === 1500);
    expect(logoutCall).toBeDefined();
    const callback = logoutCall![0] as () => Promise<void>;
    // logout() rejects → the async callback propagates the rejection even though
    // finally already called router.push. Absorb the expected rejection.
    await act(async () => {
      try { await callback(); } catch { /* expected: logout threw */ }
    });

    // Despite logout() throwing, router.push must still be called (try/finally)
    expect(mockLogout).toHaveBeenCalledTimes(1);
    expect(mockPush).toHaveBeenCalledWith("/login");

    setTimeoutSpy.mockRestore();
  });

  it("FCT-9: session-expiry 401 (no invalid_credentials detail) shows error + logout + redirect after 1500 ms", async () => {
    // FCB-6: 401 with no/empty detail → session expired, not wrong password
    server.use(authHandlers.changePasswordError(null, 401));
    const setTimeoutSpy = vi.spyOn(globalThis, "setTimeout");
    const user = userEvent.setup();
    render(<ConfiguracionPage />);

    await openPasswordPanel(user);
    await fillAndSubmit(user);

    // Session-expiry message must appear
    await waitFor(() => {
      expect(
        screen.getByText("Tu sesión expiró. Iniciá sesión de nuevo."),
      ).toBeInTheDocument();
    });

    // Extract and invoke the 1500 ms callback (FCB-6 forced logout)
    const logoutCall = setTimeoutSpy.mock.calls.find(([, ms]) => ms === 1500);
    expect(logoutCall).toBeDefined();
    const callback = logoutCall![0] as () => Promise<void>;
    await act(async () => { await callback(); });

    expect(mockLogout).toHaveBeenCalledTimes(1);
    expect(mockPush).toHaveBeenCalledWith("/login");

    setTimeoutSpy.mockRestore();
  });
});
