/**
 * Unit tests for OnboardingPage.
 *
 * Covers:
 *  - finish() awaits completeOnboarding() then redirects to /chat
 *  - skipAll() awaits completeOnboarding() then redirects to /chat
 *  - completeOnboarding() is NOT called until finish/skip is triggered
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Mock step sub-components — keep tests focused on page-level orchestration
// ---------------------------------------------------------------------------

vi.mock("../_components/StepBienvenida", () => ({
  StepBienvenida: ({ onNext }: { onNext: () => void }) => (
    <button onClick={onNext}>step-bienvenida-next</button>
  ),
}));

vi.mock("../_components/StepPerfil", () => ({
  StepPerfil: ({ onNext }: { onNext: () => void }) => (
    <button onClick={onNext}>step-perfil-next</button>
  ),
}));

vi.mock("../_components/StepOrganizacion", () => ({
  StepOrganizacion: ({ onNext }: { onNext: () => void }) => (
    <button onClick={onNext}>step-organizacion-next</button>
  ),
}));

vi.mock("../_components/StepApiKey", () => ({
  StepApiKey: ({ onNext }: { onNext: () => void }) => (
    <button onClick={onNext}>step-apikey-next</button>
  ),
}));

vi.mock("../_components/StepListo", () => ({
  StepListo: ({ onFinish }: { onFinish: () => void }) => (
    <button onClick={onFinish}>step-listo-finish</button>
  ),
}));

vi.mock("../_components/ProgressBar", () => ({
  ProgressBar: () => <div data-testid="progress-bar" />,
}));

// ---------------------------------------------------------------------------
// Mock next/navigation
// ---------------------------------------------------------------------------

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

// ---------------------------------------------------------------------------
// Mock AuthContext
// ---------------------------------------------------------------------------

const mockCompleteOnboarding = vi.fn();
const mockAuthFetch = vi.fn();

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({
    authFetch: mockAuthFetch,
    completeOnboarding: mockCompleteOnboarding,
  }),
}));

// ---------------------------------------------------------------------------
// Provide a proper localStorage mock (jsdom Storage may lack prototype methods
// in some vitest workers when other tests stub the global)
// ---------------------------------------------------------------------------

const _store: Record<string, string> = {};
const localStorageMock = {
  getItem: (k: string) => _store[k] ?? null,
  setItem: (k: string, v: string) => {
    _store[k] = v;
  },
  removeItem: (k: string) => {
    delete _store[k];
  },
  clear: () => {
    Object.keys(_store).forEach((k) => delete _store[k]);
  },
};
vi.stubGlobal("localStorage", localStorageMock);

// ---------------------------------------------------------------------------
// Import page after mocks are in place
// ---------------------------------------------------------------------------

import OnboardingPage from "../page";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function clickThrough(n: number) {
  const user = userEvent.setup();
  const labels = [
    "step-bienvenida-next",
    "step-perfil-next",
    "step-organizacion-next",
    "step-apikey-next",
  ];
  for (let i = 0; i < n; i++) {
    const btn = screen.getByText(labels[i]);
    await user.click(btn);
    // Wait for animation timeout (250 ms debounce in page)
    await waitFor(() =>
      expect(screen.queryByText(labels[i])).not.toBeInTheDocument(),
    );
  }
}

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  mockPush.mockReset();
  mockCompleteOnboarding.mockReset().mockResolvedValue(undefined);
  mockAuthFetch.mockReset().mockResolvedValue({});
  localStorageMock.clear();
});

// ---------------------------------------------------------------------------
// skipAll
// ---------------------------------------------------------------------------

describe("OnboardingPage — skipAll()", () => {
  it("calls completeOnboarding() then redirects to /chat", async () => {
    const user = userEvent.setup();
    render(<OnboardingPage />);

    const skipBtn = screen.getByText(/Omitir configuracion/i);
    await user.click(skipBtn);

    await waitFor(() => {
      expect(mockCompleteOnboarding).toHaveBeenCalledTimes(1);
    });
    expect(mockPush).toHaveBeenCalledWith("/chat");
    expect(mockPush).not.toHaveBeenCalledWith("/");
  });

  it("does NOT redirect when completeOnboarding rejects (no silent swallow)", async () => {
    mockCompleteOnboarding.mockRejectedValue(new Error("network"));
    const user = userEvent.setup();
    render(<OnboardingPage />);

    const skipBtn = screen.getByText(/Omitir configuracion/i);
    // React async onClick handlers don't propagate rejections to the click caller.
    // The rejection becomes an unhandled promise rejection; router.push is never called.
    await user.click(skipBtn);
    // Let micro-tasks settle
    await new Promise((r) => setTimeout(r, 50));
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("does NOT call completeOnboarding before skip is clicked", () => {
    render(<OnboardingPage />);
    expect(mockCompleteOnboarding).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// finish
// ---------------------------------------------------------------------------

describe("OnboardingPage — finish()", () => {
  it("calls completeOnboarding() then redirects to /chat after completing all steps", async () => {
    const user = userEvent.setup();
    render(<OnboardingPage />);

    // Navigate through steps 1-4
    await clickThrough(4);

    // Now at step 5 — click finish
    const finishBtn = screen.getByText("step-listo-finish");
    await user.click(finishBtn);

    await waitFor(() => {
      expect(mockCompleteOnboarding).toHaveBeenCalledTimes(1);
    });
    expect(mockPush).toHaveBeenCalledWith("/chat");
    expect(mockPush).not.toHaveBeenCalledWith("/");
  });

  it("persists onboarding prefs to localStorage before calling completeOnboarding", async () => {
    const user = userEvent.setup();
    render(<OnboardingPage />);

    await clickThrough(4);

    const finishBtn = screen.getByText("step-listo-finish");
    await user.click(finishBtn);

    await waitFor(() => {
      expect(mockCompleteOnboarding).toHaveBeenCalledTimes(1);
    });

    expect(localStorageMock.getItem("tukijuris_onboarding_done")).toBe("true");
  });
});
