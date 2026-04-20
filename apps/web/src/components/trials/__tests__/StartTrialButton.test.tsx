import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";
import { StartTrialButton } from "../StartTrialButton";

// ---------------------------------------------------------------------------
// Mocks — vi.hoisted() ensures refs are available before vi.mock() hoisting
// ---------------------------------------------------------------------------

const { mockAuthFetch } = vi.hoisted(() => ({
  mockAuthFetch: vi.fn(),
}));

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({ authFetch: mockAuthFetch }),
}));

vi.mock("@/lib/api/trial", () => ({
  fetchCurrentTrial: vi.fn(),
  startTrial: vi.fn(),
}));

import { fetchCurrentTrial, startTrial } from "@/lib/api/trial";

const mockFetchCurrent = fetchCurrentTrial as ReturnType<typeof vi.fn>;
const mockStartTrial = startTrial as ReturnType<typeof vi.fn>;

const ACTIVE_TRIAL = {
  id: "trial-1",
  user_id: "user-1",
  plan_code: "pro",
  status: "active" as const,
  started_at: new Date().toISOString(),
  ends_at: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 days from now
  days_remaining: 5,
  card_added_at: null,
  provider: null,
  charged_at: null,
  charge_failed_at: null,
  charge_failure_reason: null,
  retry_count: 0,
  canceled_at: null,
  canceled_by_user: false,
  downgraded_at: null,
  subscription_id: null,
};

beforeEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("StartTrialButton", () => {
  it("shows loading state initially", () => {
    mockFetchCurrent.mockReturnValue(new Promise(() => {}));
    render(<StartTrialButton />);
    expect(screen.getByTestId("trial-loading")).toBeInTheDocument();
  });

  it("shows start button when no trial exists", async () => {
    mockFetchCurrent.mockResolvedValue(null);
    render(<StartTrialButton />);

    await waitFor(() => {
      expect(screen.getByTestId("start-trial-btn")).toBeInTheDocument();
      expect(screen.getByText("Iniciar prueba gratuita")).toBeInTheDocument();
    });
  });

  it("shows trial status when trial is active", async () => {
    mockFetchCurrent.mockResolvedValue(ACTIVE_TRIAL);
    render(<StartTrialButton />);

    await waitFor(() => {
      expect(screen.getByTestId("trial-status")).toBeInTheDocument();
      expect(screen.getByTestId("trial-status-badge")).toBeInTheDocument();
    });
  });

  it("shows days remaining for active trial", async () => {
    mockFetchCurrent.mockResolvedValue(ACTIVE_TRIAL);
    render(<StartTrialButton />);

    await waitFor(() => {
      expect(screen.getByText(/restante/)).toBeInTheDocument();
    });
  });

  it("calls startTrial on button click and transitions to status view", async () => {
    mockFetchCurrent.mockResolvedValue(null);
    mockStartTrial.mockResolvedValue(ACTIVE_TRIAL);
    const user = userEvent.setup();
    render(<StartTrialButton />);

    await waitFor(() => screen.getByTestId("start-trial-btn"));
    await user.click(screen.getByTestId("start-trial-btn"));

    await waitFor(() => {
      expect(mockStartTrial).toHaveBeenCalledWith(mockAuthFetch);
      expect(screen.getByTestId("trial-status")).toBeInTheDocument();
    });
  });

  it("shows error message when startTrial fails", async () => {
    mockFetchCurrent.mockResolvedValue(null);
    mockStartTrial.mockRejectedValue(new Error("Server error"));
    const user = userEvent.setup();
    render(<StartTrialButton />);

    await waitFor(() => screen.getByTestId("start-trial-btn"));
    await user.click(screen.getByTestId("start-trial-btn"));

    await waitFor(() => {
      expect(screen.getByTestId("trial-error")).toBeInTheDocument();
      expect(screen.getByText(/No se pudo iniciar/)).toBeInTheDocument();
    });
  });

  it("shows no status text for non-active trial", async () => {
    mockFetchCurrent.mockResolvedValue({ ...ACTIVE_TRIAL, status: "downgraded" });
    render(<StartTrialButton />);

    await waitFor(() => {
      expect(screen.getByTestId("trial-status")).toBeInTheDocument();
      expect(screen.queryByText(/restante/)).not.toBeInTheDocument();
    });
  });
});
