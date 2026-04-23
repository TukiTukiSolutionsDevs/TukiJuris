/**
 * TrialRetryBanner unit tests.
 * Spec: billing/spec.md — Trial Retry Banner
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";

// ---------------------------------------------------------------------------
// Hoisted mocks
// ---------------------------------------------------------------------------

const { mockAuthFetch, mockToastSuccess, mockToastError } = vi.hoisted(() => ({
  mockAuthFetch:    vi.fn(),
  mockToastSuccess: vi.fn(),
  mockToastError:   vi.fn(),
}));

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({ authFetch: mockAuthFetch }),
}));

vi.mock("sonner", () => ({
  toast: {
    success: mockToastSuccess,
    error:   mockToastError,
  },
}));

import { TrialRetryBanner } from "../_components/TrialRetryBanner";

beforeEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("TrialRetryBanner — rendering", () => {
  it("renders the retry button", () => {
    render(<TrialRetryBanner trialId="trial-1" onSuccess={vi.fn()} />);
    expect(screen.getByTestId("retry-charge-btn")).toBeInTheDocument();
    expect(screen.getByText("Reintentar cobro")).toBeInTheDocument();
  });

  it("has role=alert for accessibility", () => {
    render(<TrialRetryBanner trialId="trial-1" onSuccess={vi.fn()} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});

describe("TrialRetryBanner — retry success", () => {
  it("calls POST /api/trials/{id}/retry-charge on click", async () => {
    mockAuthFetch.mockResolvedValue({ ok: true, status: 200, json: async () => ({}) });
    const user = userEvent.setup();
    render(<TrialRetryBanner trialId="trial-123" onSuccess={vi.fn()} />);

    await user.click(screen.getByTestId("retry-charge-btn"));

    expect(mockAuthFetch).toHaveBeenCalledWith(
      "/api/trials/trial-123/retry-charge",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("shows success toast and calls onSuccess on 200", async () => {
    const onSuccess = vi.fn();
    mockAuthFetch.mockResolvedValue({ ok: true, status: 200, json: async () => ({}) });
    const user = userEvent.setup();
    render(<TrialRetryBanner trialId="trial-1" onSuccess={onSuccess} />);

    await user.click(screen.getByTestId("retry-charge-btn"));

    await waitFor(() => {
      expect(mockToastSuccess).toHaveBeenCalledWith(
        "Cobro reintentado. Actualizando estado..."
      );
      expect(onSuccess).toHaveBeenCalledTimes(1);
    });
  });

  it("disables the button and sets aria-busy while pending", async () => {
    let resolve: (v: unknown) => void;
    mockAuthFetch.mockReturnValue(new Promise((res) => { resolve = res; }));
    const user = userEvent.setup();
    render(<TrialRetryBanner trialId="trial-1" onSuccess={vi.fn()} />);

    await user.click(screen.getByTestId("retry-charge-btn"));

    const btn = screen.getByTestId("retry-charge-btn");
    expect(btn).toBeDisabled();
    expect(btn).toHaveAttribute("aria-busy", "true");

    // Resolve to avoid hanging
    resolve!({ ok: true, status: 200, json: async () => ({}) });
  });
});

describe("TrialRetryBanner — retry errors", () => {
  it("shows 503 toast when server returns 503", async () => {
    mockAuthFetch.mockResolvedValue({ ok: false, status: 503, json: async () => ({}) });
    const user = userEvent.setup();
    render(<TrialRetryBanner trialId="trial-1" onSuccess={vi.fn()} />);

    await user.click(screen.getByTestId("retry-charge-btn"));

    await waitFor(() => {
      expect(mockToastError).toHaveBeenCalledWith(
        "El sistema de prueba no está disponible en este momento."
      );
    });
  });

  it("shows generic toast for non-503 error", async () => {
    mockAuthFetch.mockResolvedValue({ ok: false, status: 500, json: async () => ({}) });
    const user = userEvent.setup();
    render(<TrialRetryBanner trialId="trial-1" onSuccess={vi.fn()} />);

    await user.click(screen.getByTestId("retry-charge-btn"));

    await waitFor(() => {
      expect(mockToastError).toHaveBeenCalledWith(
        "No se pudo reintentar el cobro. Intentá nuevamente."
      );
    });
  });

  it("shows generic toast when request throws (network error)", async () => {
    mockAuthFetch.mockRejectedValue(new Error("Network error"));
    const user = userEvent.setup();
    render(<TrialRetryBanner trialId="trial-1" onSuccess={vi.fn()} />);

    await user.click(screen.getByTestId("retry-charge-btn"));

    await waitFor(() => {
      expect(mockToastError).toHaveBeenCalledWith(
        "No se pudo reintentar el cobro. Intentá nuevamente."
      );
    });
  });

  it("does NOT call onSuccess on error", async () => {
    const onSuccess = vi.fn();
    mockAuthFetch.mockResolvedValue({ ok: false, status: 500, json: async () => ({}) });
    const user = userEvent.setup();
    render(<TrialRetryBanner trialId="trial-1" onSuccess={onSuccess} />);

    await user.click(screen.getByTestId("retry-charge-btn"));

    await waitFor(() => expect(mockToastError).toHaveBeenCalled());
    expect(onSuccess).not.toHaveBeenCalled();
  });
});
