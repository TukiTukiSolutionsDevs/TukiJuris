import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";
import { RevenueCards } from "../RevenueCards";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockAuthFetch = vi.fn();

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({ authFetch: mockAuthFetch }),
}));

vi.mock("@/lib/api/admin", () => ({
  fetchRevenue: vi.fn(),
}));

import { fetchRevenue } from "@/lib/api/admin";

const mockFetchRevenue = fetchRevenue as ReturnType<typeof vi.fn>;

const REVENUE_FIXTURE = {
  mrr_cents: 150000,
  arr_cents: 1800000,
  source: "plan_service",
  breakdown: [
    { plan: "pro", display_name: "Profesional", org_count: 3, revenue_cents: 90000 },
    { plan: "studio", display_name: "Estudio", org_count: 2, revenue_cents: 60000 },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("RevenueCards", () => {
  it("shows loading state initially", () => {
    // Never resolves during this test
    mockFetchRevenue.mockReturnValue(new Promise(() => {}));
    render(<RevenueCards />);
    expect(screen.getByText(/Cargando ingresos/)).toBeInTheDocument();
  });

  it("renders MRR and ARR cards after successful fetch", async () => {
    mockFetchRevenue.mockResolvedValue(REVENUE_FIXTURE);
    render(<RevenueCards />);

    await waitFor(() => {
      // MRR: S/ 1,500.00
      expect(screen.getByText(/MRR mensual/i)).toBeInTheDocument();
      expect(screen.getByText(/ARR anual/i)).toBeInTheDocument();
    });
  });

  it("renders per-plan breakdown table", async () => {
    mockFetchRevenue.mockResolvedValue(REVENUE_FIXTURE);
    render(<RevenueCards />);

    await waitFor(() => {
      expect(screen.getByText("Profesional")).toBeInTheDocument();
      expect(screen.getByText("Estudio")).toBeInTheDocument();
    });
  });

  it("shows source label", async () => {
    mockFetchRevenue.mockResolvedValue(REVENUE_FIXTURE);
    render(<RevenueCards />);

    await waitFor(() => {
      expect(screen.getByText(/plan_service/)).toBeInTheDocument();
    });
  });

  it("silently unmounts (returns null) when API returns 403", async () => {
    const err = Object.assign(new Error("Forbidden"), { status: 403 });
    mockFetchRevenue.mockRejectedValue(err);

    const { container } = render(<RevenueCards />);

    await waitFor(() => {
      expect(container.firstChild).toBeNull();
    });
  });

  it("shows error message on non-403 failure", async () => {
    const err = Object.assign(new Error("Server Error"), { status: 500 });
    mockFetchRevenue.mockRejectedValue(err);

    render(<RevenueCards />);

    await waitFor(() => {
      expect(screen.getByText(/No se pudo cargar los datos de ingresos/)).toBeInTheDocument();
    });
  });

  it("renders nothing (no table) when breakdown is empty", async () => {
    mockFetchRevenue.mockResolvedValue({ ...REVENUE_FIXTURE, breakdown: [] });
    render(<RevenueCards />);

    await waitFor(() => {
      expect(screen.queryByText("Profesional")).toBeNull();
    });
  });
});
