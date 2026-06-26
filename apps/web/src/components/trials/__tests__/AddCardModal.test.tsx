import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";
import { AddCardModal } from "../AddCardModal";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockAuthFetch = vi.fn();
type MockUser = {
  id: string;
  email: string;
  isAdmin: boolean;
  plan: null;
  entitlements: string[];
};
const DEFAULT_USER: MockUser = {
  id: "user-1",
  email: "test@tukijuris.pe",
  isAdmin: false,
  plan: null,
  entitlements: [],
};
let mockUser: MockUser | null = DEFAULT_USER;

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({ authFetch: mockAuthFetch, user: mockUser }),
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
  mockUser = DEFAULT_USER;
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

  it("submit button is disabled when required fields are empty", () => {
    render(<AddCardModal trialId="trial-1" onClose={vi.fn()} />);
    expect(screen.getByTestId("submit-card-btn")).toBeDisabled();
  });

  it("submit button enables only after token + first/last name are filled", async () => {
    const user = userEvent.setup();
    render(<AddCardModal trialId="trial-1" onClose={vi.fn()} />);

    await user.type(screen.getByTestId("card-token-input"), "tkn_test123");
    expect(screen.getByTestId("submit-card-btn")).toBeDisabled();

    await user.type(screen.getByTestId("first-name-input"), "Juan");
    expect(screen.getByTestId("submit-card-btn")).toBeDisabled();

    await user.type(screen.getByTestId("last-name-input"), "Pérez");
    expect(screen.getByTestId("submit-card-btn")).not.toBeDisabled();
  });

  it("calls addCardToTrial with backend-shaped body on submit", async () => {
    mockAddCard.mockResolvedValue(TRIAL_RESULT);
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<AddCardModal trialId="trial-1" onClose={onClose} />);

    await user.type(screen.getByTestId("card-token-input"), "tkn_test123");
    await user.type(screen.getByTestId("first-name-input"), "Juan");
    await user.type(screen.getByTestId("last-name-input"), "Pérez");
    await user.click(screen.getByTestId("submit-card-btn"));

    await waitFor(() => {
      expect(mockAddCard).toHaveBeenCalledWith(mockAuthFetch, {
        provider: "culqi",
        token_id: "tkn_test123",
        customer_info: {
          email: DEFAULT_USER.email,
          first_name: "Juan",
          last_name: "Pérez",
        },
      });
    });
  });

  it("calls onClose(true) on successful submit", async () => {
    mockAddCard.mockResolvedValue(TRIAL_RESULT);
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<AddCardModal trialId="trial-1" onClose={onClose} />);

    await user.type(screen.getByTestId("card-token-input"), "tkn_test123");
    await user.type(screen.getByTestId("first-name-input"), "Juan");
    await user.type(screen.getByTestId("last-name-input"), "Pérez");
    await user.click(screen.getByTestId("submit-card-btn"));

    await waitFor(() => {
      expect(onClose).toHaveBeenCalledWith(true);
    });
  });

  it("shows error message when addCardToTrial fails", async () => {
    mockAddCard.mockRejectedValue(new Error("Payment error"));
    const user = userEvent.setup();
    render(<AddCardModal trialId="trial-1" onClose={vi.fn()} />);

    await user.type(screen.getByTestId("card-token-input"), "tkn_bad1");
    await user.type(screen.getByTestId("first-name-input"), "Juan");
    await user.type(screen.getByTestId("last-name-input"), "Pérez");
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

  it("lets the user type an email when the session has none", async () => {
    mockUser = { ...DEFAULT_USER, email: "" };
    mockAddCard.mockResolvedValue(TRIAL_RESULT);
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<AddCardModal trialId="trial-1" onClose={onClose} />);

    const emailInput = screen.getByTestId("card-email-input") as HTMLInputElement;
    expect(emailInput.value).toBe("");

    await user.type(screen.getByTestId("card-token-input"), "tkn_test123");
    await user.type(screen.getByTestId("first-name-input"), "Juan");
    await user.type(screen.getByTestId("last-name-input"), "Pérez");

    // Still blocked because email is missing.
    expect(screen.getByTestId("submit-card-btn")).toBeDisabled();

    await user.type(emailInput, "fallback@correo.pe");
    expect(screen.getByTestId("submit-card-btn")).not.toBeDisabled();

    await user.click(screen.getByTestId("submit-card-btn"));

    await waitFor(() => {
      expect(mockAddCard).toHaveBeenCalledWith(mockAuthFetch, {
        provider: "culqi",
        token_id: "tkn_test123",
        customer_info: {
          email: "fallback@correo.pe",
          first_name: "Juan",
          last_name: "Pérez",
        },
      });
    });
  });
});
