import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";
import { StartTrialButton } from "../StartTrialButton";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockAuthFetch = vi.fn();

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
  org_id: "org-1",
  status: "active" as const,
  trial_ends_at: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 days from now
  charge_amount: "50.00",
  currency: "PEN",
  provider: null,
  created_at: new Date().toISOString(),
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
    mockFetchCurrent.mockResolvedValue({ ...ACTIVE_TRIAL, status: "expired" });
    render(<StartTrialButton />);

    await waitFor(() => {
      expect(screen.getByTestId("trial-status")).toBeInTheDocument();
      expect(screen.queryByText(/restante/)).not.toBeInTheDocument();
    });
  });
});
