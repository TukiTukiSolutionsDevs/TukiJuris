/**
 * LLM providers display tests — configuracion page (Preferencias / API Keys tabs)
 *
 * Covers FE-LLM-PROVIDERS:
 *   LP-1  Known providers render with correct displayName from PROVIDER_LABELS
 *   LP-2  GET /api/keys/llm-providers success → no crash, backend providers stored
 *   LP-3  GET /api/keys/llm-providers failure → graceful degradation, hardcoded renders
 *   LP-4  labelForProvider with unknown ID returns generic fallback, never throws
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Mock sonner (used by the page now)
// ---------------------------------------------------------------------------
vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
  Toaster: () => null,
}));

// ---------------------------------------------------------------------------
// Stable mocks
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
  useHasFeature: () => true,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/configuracion",
  useSearchParams: () => ({ get: () => null }),
}));

// ---------------------------------------------------------------------------
// Import page and lib
// ---------------------------------------------------------------------------
import ConfiguracionPage from "../page";
import { labelForProvider, PROVIDER_LABELS } from "@/lib/llm/providerLabels";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function makeOk(data: unknown) {
  return { ok: true, json: () => Promise.resolve(data) };
}

function setupAuthFetch(
  providersResponse: { ok: boolean; data?: unknown } = { ok: true, data: [] },
  freeModelsResponse: { ok: boolean; data?: unknown } = { ok: true, data: { models: [], enabled: false, daily_limit: 5 } },
) {
  mockAuthFetch.mockImplementation(async (url: string) => {
    if (url.includes("/api/auth/me")) return makeOk({ id: "user-1", email: "t@t.com", name: "T" });
    if (url.includes("/api/organizations/")) return { ok: false, json: () => Promise.resolve([]) };
    if (url.includes("/api/keys/llm-providers")) {
      return providersResponse.ok
        ? makeOk(providersResponse.data ?? [])
        : { ok: false, status: 500, json: () => Promise.resolve({}) };
    }
    if (url.includes("/api/keys/free-models")) {
      return freeModelsResponse.ok
        ? makeOk(freeModelsResponse.data ?? { models: [], enabled: false, daily_limit: 5 })
        : { ok: false, status: 500, json: () => Promise.resolve({}) };
    }
    if (url.includes("/api/keys/llm-keys")) return makeOk([]);
    return { ok: false, json: () => Promise.resolve({}) };
  });
}

async function goToPreferenciasTab(user: ReturnType<typeof userEvent.setup>) {
  // Two sets of tab buttons exist (mobile + desktop); click the first match
  const btns = await screen.findAllByRole("button", { name: /preferencias/i });
  await user.click(btns[0]);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.clearAllMocks();
  setupAuthFetch();
});

// LP-4: pure unit test for labelForProvider — no component needed
describe("labelForProvider (pure)", () => {
  it("LP-4a: returns correct displayName for known provider", () => {
    expect(labelForProvider("google").displayName).toBe("Google (Gemini)");
    expect(labelForProvider("anthropic").displayName).toBe("Anthropic");
  });

  it("LP-4b: returns generic fallback for unknown provider, never throws", () => {
    expect(() => labelForProvider("unknown-xyz")).not.toThrow();
    const label = labelForProvider("unknown-xyz");
    expect(label.displayName).toBe("unknown-xyz");
  });

  it("LP-4c: backendName is used as displayName when provider is unknown", () => {
    const label = labelForProvider("some-new-provider", "SomeNewAI");
    expect(label.displayName).toBe("SomeNewAI");
  });

  it("LP-4d: all PROVIDER_LABELS entries have required displayName", () => {
    for (const [id, label] of Object.entries(PROVIDER_LABELS)) {
      expect(label.displayName, `Provider ${id} missing displayName`).toBeTruthy();
    }
  });
});

describe("configuracion — LLM providers (Preferencias tab)", () => {
  it("LP-1: known provider display names render on Preferencias tab", async () => {
    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToPreferenciasTab(user);

    // Wait for providers to render — Google is always first in PROVIDER_ORDER
    // The name appears multiple times (tab + config summary) so use getAllByText
    await waitFor(() => {
      expect(screen.getAllByText("Google (Gemini)").length).toBeGreaterThan(0);
    });
    // At least one more known provider visible
    expect(screen.getAllByText("Groq").length).toBeGreaterThan(0);
  });

  it("LP-2: GET /api/keys/llm-providers + /api/keys/free-models called; backend provider renders", async () => {
    setupAuthFetch({
      ok: true,
      data: [
        { id: "google", name: "Google" },
        { id: "openai", name: "OpenAI" },
        { id: "new-provider", name: "NewAI" },
      ],
    });
    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToPreferenciasTab(user);

    // Both endpoints must be fetched
    await waitFor(() => {
      const urls = mockAuthFetch.mock.calls.map((call) => call[0] as string);
      expect(urls.some((u) => u.includes("/api/keys/llm-providers"))).toBe(true);
      expect(urls.some((u) => u.includes("/api/keys/free-models"))).toBe(true);
    });

    // Known provider still renders with overlay label
    await waitFor(() => {
      expect(screen.getAllByText("Google (Gemini)").length).toBeGreaterThan(0);
    });

    // Unknown provider from backend renders using its backend name
    await waitFor(() => {
      expect(screen.getAllByText("NewAI").length).toBeGreaterThan(0);
    });
  });

  it("LP-3: both fetches fail → graceful fallback, hardcoded providers still render", async () => {
    setupAuthFetch({ ok: false }, { ok: false });
    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToPreferenciasTab(user);

    // Hardcoded providers must still render even when both backend calls fail
    await waitFor(() => {
      expect(screen.getAllByText("Google (Gemini)").length).toBeGreaterThan(0);
    });
  });
});
