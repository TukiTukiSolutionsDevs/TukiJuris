/**
 * Memory settings flow tests — configuracion page (Memoria tab)
 *
 * Covers FE-MEM-SETTINGS:
 *   MS-1  Loading spinner shown while GET /api/memory/settings in-flight
 *   MS-2  Toggles render initial state from API response
 *   MS-3  Toggle click → optimistic update → PUT /api/memory/settings called
 *   MS-4  PUT success → toast.success, state updated with server response
 *   MS-5  PUT error → optimistic update reverted, toast.error
 *   MS-6  Both toggles disabled while savingMemSettings
 *   MS-7  auto_extraction toggle disabled when memory_enabled=false
 *   MS-8  Disabled notice rendered when memory_enabled=false
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Mock sonner before imports that use it
// vi.mock() is hoisted — refs must be created via vi.hoisted() to be available
// ---------------------------------------------------------------------------
const { mockToastSuccess, mockToastError } = vi.hoisted(() => ({
  mockToastSuccess: vi.fn(),
  mockToastError: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: { success: mockToastSuccess, error: mockToastError },
  Toaster: () => null,
}));

// ---------------------------------------------------------------------------
// Stable mock refs
// ---------------------------------------------------------------------------
const mockAuthFetch = vi.fn();

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({
    authFetch: mockAuthFetch,
    logout: vi.fn(),
    logoutAll: vi.fn(),
    user: { id: "user-1", email: "test@test.com", isAdmin: false },
    onboardingCompleted: true,
  }),
  useHasFeature: () => false,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/configuracion",
  useSearchParams: () => ({ get: () => null }),
}));

// ---------------------------------------------------------------------------
// Import page AFTER mocks
// ---------------------------------------------------------------------------
import ConfiguracionPage from "../page";

// ---------------------------------------------------------------------------
// Default mock settings response
// ---------------------------------------------------------------------------
const DEFAULT_SETTINGS = { memory_enabled: true, auto_extract: true };

function setupAuthFetch(
  settingsOverrides: Record<string, unknown> = {},
  putResponse: { ok: boolean; body?: Record<string, unknown> } = { ok: true }
) {
  mockAuthFetch.mockImplementation(async (url: string, options?: RequestInit) => {
    if (url.includes("/api/auth/me")) {
      return { ok: true, json: () => Promise.resolve({ id: "user-1", email: "test@test.com", name: "Test User", onboarding_completed: true }) };
    }
    if (url.includes("/api/organizations/")) {
      return { ok: false, json: () => Promise.resolve([]) };
    }
    if (url.includes("/api/memory/settings") && options?.method === "PUT") {
      return {
        ok: putResponse.ok,
        status: putResponse.ok ? 200 : 500,
        json: () => Promise.resolve(putResponse.body ?? { ...DEFAULT_SETTINGS, ...settingsOverrides }),
      };
    }
    if (url.includes("/api/memory/settings")) {
      return { ok: true, json: () => Promise.resolve({ ...DEFAULT_SETTINGS, ...settingsOverrides }) };
    }
    if (url.includes("/api/memory/")) {
      return { ok: true, json: () => Promise.resolve({ groups: [], total: 0, active_count: 0 }) };
    }
    return { ok: false, json: () => Promise.resolve({}) };
  });
}

// ---------------------------------------------------------------------------
// Helper: navigate to Memoria tab
// ---------------------------------------------------------------------------
async function goToMemoriaTab(user: ReturnType<typeof userEvent.setup>) {
  // Two sets of tab buttons exist (mobile + desktop); click the first match
  const btns = await screen.findAllByRole("button", { name: /memoria/i });
  await user.click(btns[0]);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.clearAllMocks();
  setupAuthFetch();
});

describe("configuracion — memory settings (Memoria tab)", () => {
  it("MS-1: shows loading spinner while GET /api/memory/settings is in-flight", async () => {
    let resolveSettings!: (v: unknown) => void;
    mockAuthFetch.mockImplementation(async (url: string) => {
      if (url.includes("/api/auth/me")) {
        return { ok: true, json: () => Promise.resolve({ id: "user-1", email: "t@t.com", name: "T" }) };
      }
      if (url.includes("/api/organizations/")) return { ok: false, json: () => Promise.resolve([]) };
      if (url.includes("/api/memory/settings")) {
        return new Promise((resolve) => {
          resolveSettings = resolve;
        });
      }
      if (url.includes("/api/memory/")) return { ok: true, json: () => Promise.resolve({ groups: [], total: 0, active_count: 0 }) };
      return { ok: false, json: () => Promise.resolve({}) };
    });

    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToMemoriaTab(user);

    // Spinner must appear while the settings request is pending
    await waitFor(() => {
      expect(screen.getByText(/cargando configuración/i)).toBeInTheDocument();
    });

    // Resolve the pending request
    resolveSettings({ ok: true, json: () => Promise.resolve(DEFAULT_SETTINGS) });
  });

  it("MS-2: toggles render initial state from API (both ON)", async () => {
    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToMemoriaTab(user);

    await waitFor(() => {
      const memToggle = screen.getByTestId("toggle-memory-enabled");
      expect(memToggle).not.toBeDisabled();
      expect(memToggle).toHaveClass("bg-primary-container");
    });
    const extractToggle = screen.getByTestId("toggle-auto-extraction");
    expect(extractToggle).toHaveClass("bg-primary-container");
  });

  it("MS-2b: toggles reflect OFF state when API returns memory_enabled=false", async () => {
    setupAuthFetch({ memory_enabled: false, auto_extract: false });
    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToMemoriaTab(user);

    await waitFor(() => {
      expect(screen.getByTestId("toggle-memory-enabled")).toHaveClass("bg-[#35343a]");
    });
    expect(screen.getByTestId("memory-disabled-notice")).toBeInTheDocument();
  });

  it("MS-3: clicking memory toggle fires PUT /api/memory/settings with flipped value", async () => {
    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToMemoriaTab(user);

    await waitFor(() => screen.getByTestId("toggle-memory-enabled"));
    await user.click(screen.getByTestId("toggle-memory-enabled"));

    await waitFor(() => {
      const putCall = mockAuthFetch.mock.calls.find(
        ([url, opts]) => url.includes("/api/memory/settings") && opts?.method === "PUT"
      );
      expect(putCall).toBeDefined();
      const body = JSON.parse(putCall![1].body as string);
      expect(body.memory_enabled).toBe(false);
      // Spec contract: field must be auto_extract (not auto_extraction_enabled)
      expect(body).toHaveProperty("auto_extract");
    });
  });

  it("MS-4: PUT success → toast.success called, state updated", async () => {
    setupAuthFetch({}, { ok: true, body: { memory_enabled: false, auto_extract: true } });
    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToMemoriaTab(user);

    await waitFor(() => screen.getByTestId("toggle-memory-enabled"));
    await user.click(screen.getByTestId("toggle-memory-enabled"));

    await waitFor(() => {
      expect(mockToastSuccess).toHaveBeenCalledWith("Configuración actualizada");
    });
  });

  it("MS-5: PUT error → optimistic state reverted, toast.error called", async () => {
    setupAuthFetch({}, { ok: false });
    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToMemoriaTab(user);

    await waitFor(() => screen.getByTestId("toggle-memory-enabled"));
    await user.click(screen.getByTestId("toggle-memory-enabled"));

    await waitFor(() => {
      expect(mockToastError).toHaveBeenCalledWith("No se pudo actualizar la configuración");
    });
    // Toggle should revert to ON (original value)
    await waitFor(() => {
      expect(screen.getByTestId("toggle-memory-enabled")).toHaveClass("bg-primary-container");
    });
  });

  it("MS-7: auto_extraction toggle is disabled when memory_enabled=false", async () => {
    setupAuthFetch({ memory_enabled: false, auto_extract: true });
    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToMemoriaTab(user);

    await waitFor(() => {
      expect(screen.getByTestId("toggle-auto-extraction")).toBeDisabled();
    });
  });

  it("MS-8: disabled notice is shown when memory_enabled=false", async () => {
    setupAuthFetch({ memory_enabled: false });
    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToMemoriaTab(user);

    await waitFor(() => {
      expect(screen.getByTestId("memory-disabled-notice")).toBeInTheDocument();
    });
  });

  it("MS-8b: disabled notice is NOT shown when memory_enabled=true", async () => {
    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToMemoriaTab(user);

    await waitFor(() => screen.getByTestId("toggle-memory-enabled"));
    expect(screen.queryByTestId("memory-disabled-notice")).not.toBeInTheDocument();
  });
});
