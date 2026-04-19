import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";
import { AddCardModal } from "../AddCardModal";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockAuthFetch = vi.fn();

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({ authFetch: mockAuthFetch }),
}));

vi.mock("@/lib/api/trial", () => ({
  addCardToTrial: vi.fn(),
}));

import { addCardToTrial } from "@/lib/api/trial";

const mockAddCard = addCardToTrial as ReturnType<typeof vi.fn>;

const TRIAL_RESULT = {
  id: "trial-1",
  org_id: "org-1",
  status: "active" as const,
  trial_ends_at: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
  charge_amount: "50.00",
  currency: "PEN",
  provider: "culqi",
  created_at: new Date().toISOString(),
};

beforeEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("AddCardModal", () => {
  it("renders modal with card token input", () => {
    render(<AddCardModal trialId="trial-1" onClose={vi.fn()} />);
    expect(screen.getByTestId("add-card-modal")).toBeInTheDocument();
    expect(screen.getByTestId("card-token-input")).toBeInTheDocument();
    expect(screen.getByText("Agregar tarjeta")).toBeInTheDocument();
  });

  it("submit button is disabled when input is empty", () => {
    render(<AddCardModal trialId="trial-1" onClose={vi.fn()} />);
    expect(screen.getByTestId("submit-card-btn")).toBeDisabled();
  });

  it("submit button enables after typing token", async () => {
    const user = userEvent.setup();
    render(<AddCardModal trialId="trial-1" onClose={vi.fn()} />);

    await user.type(screen.getByTestId("card-token-input"), "tkn_test123");
    expect(screen.getByTestId("submit-card-btn")).not.toBeDisabled();
  });

  it("calls addCardToTrial with correct args on submit", async () => {
    mockAddCard.mockResolvedValue(TRIAL_RESULT);
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<AddCardModal trialId="trial-1" onClose={onClose} />);

    await user.type(screen.getByTestId("card-token-input"), "tkn_test123");
    await user.click(screen.getByTestId("submit-card-btn"));

    await waitFor(() => {
      expect(mockAddCard).toHaveBeenCalledWith(mockAuthFetch, "trial-1", "tkn_test123");
    });
  });

  it("calls onClose(true) on successful submit", async () => {
    mockAddCard.mockResolvedValue(TRIAL_RESULT);
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<AddCardModal trialId="trial-1" onClose={onClose} />);

    await user.type(screen.getByTestId("card-token-input"), "tkn_test123");
    await user.click(screen.getByTestId("submit-card-btn"));

    await waitFor(() => {
      expect(onClose).toHaveBeenCalledWith(true);
    });
  });

  it("shows error message when addCardToTrial fails", async () => {
    mockAddCard.mockRejectedValue(new Error("Payment error"));
    const user = userEvent.setup();
    render(<AddCardModal trialId="trial-1" onClose={vi.fn()} />);

    await user.type(screen.getByTestId("card-token-input"), "tkn_bad");
    await user.click(screen.getByTestId("submit-card-btn"));

    await waitFor(() => {
      expect(screen.getByTestId("card-error")).toBeInTheDocument();
      expect(screen.getByText(/No se pudo registrar la tarjeta/)).toBeInTheDocument();
    });
  });

  it("calls onClose() when close button is clicked", async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<AddCardModal trialId="trial-1" onClose={onClose} />);

    await user.click(screen.getByTestId("modal-close"));
    expect(onClose).toHaveBeenCalledWith();
  });

  it("calls onClose() when Cancelar button is clicked", async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<AddCardModal trialId="trial-1" onClose={onClose} />);

    await user.click(screen.getByText("Cancelar"));
    expect(onClose).toHaveBeenCalledWith();
  });
});
