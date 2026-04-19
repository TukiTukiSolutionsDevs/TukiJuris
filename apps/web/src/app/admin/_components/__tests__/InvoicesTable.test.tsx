import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";
import { InvoicesTable } from "../InvoicesTable";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockAuthFetch = vi.fn();

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({ authFetch: mockAuthFetch }),
}));

vi.mock("@/lib/api/admin", () => ({
  fetchAdminInvoices: vi.fn(),
}));

import { fetchAdminInvoices } from "@/lib/api/admin";

const mockFetch = fetchAdminInvoices as ReturnType<typeof vi.fn>;

const INVOICE = {
  id: "inv-1",
  org_id: "org-1",
  provider: "culqi",
  provider_charge_id: "chr_abc123",
  status: "paid",
  currency: "PEN",
  base_amount: "70.00",
  seats_count: 0,
  seat_amount: "0.00",
  subtotal_amount: "70.00",
  tax_amount: "12.60",
  total_amount: "82.60",
  plan: "pro",
  paid_at: "2026-01-15T10:00:00Z",
  failed_at: null,
  refunded_at: null,
  voided_at: null,
  refund_reason: null,
  void_reason: null,
  created_at: "2026-01-15T10:00:00Z",
  updated_at: "2026-01-15T10:00:00Z",
};

const PAGE_ONE = {
  items: [INVOICE],
  total: 1,
  page: 1,
  per_page: 20,
};

beforeEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("InvoicesTable", () => {
  it("shows loading state initially", () => {
    mockFetch.mockReturnValue(new Promise(() => {}));
    render(<InvoicesTable />);
    expect(screen.getByText(/Cargando facturas/)).toBeInTheDocument();
  });

  it("renders invoice rows after successful fetch", async () => {
    mockFetch.mockResolvedValue(PAGE_ONE);
    render(<InvoicesTable />);

    await waitFor(() => {
      expect(screen.getByText("Culqi")).toBeInTheDocument();
      expect(screen.getByText("chr_abc123")).toBeInTheDocument();
      expect(screen.getByText("pro")).toBeInTheDocument();
      expect(screen.getByText("S/ 82.60")).toBeInTheDocument();
    });
  });

  it("shows paid status badge", async () => {
    mockFetch.mockResolvedValue(PAGE_ONE);
    render(<InvoicesTable />);

    await waitFor(() => {
      expect(screen.getByText(/paid/i)).toBeInTheDocument();
    });
  });

  it("shows failed status badge for failed invoices", async () => {
    mockFetch.mockResolvedValue({
      ...PAGE_ONE,
      items: [{ ...INVOICE, status: "failed", paid_at: null, failed_at: "2026-01-15T10:00:00Z" }],
    });
    render(<InvoicesTable />);

    await waitFor(() => {
      expect(screen.getByText(/failed/i)).toBeInTheDocument();
    });
  });

  it("shows empty state when no invoices", async () => {
    mockFetch.mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 });
    render(<InvoicesTable />);

    await waitFor(() => {
      expect(screen.getByText(/No hay facturas/)).toBeInTheDocument();
    });
  });

  it("shows error message on fetch failure", async () => {
    const err = new Error("Server error");
    mockFetch.mockRejectedValue(err);
    render(<InvoicesTable />);

    await waitFor(() => {
      expect(
        screen.getByText(/No se pudieron cargar las facturas/),
      ).toBeInTheDocument();
    });
  });

  it("silently unmounts on 403 (non-admin)", async () => {
    const err = Object.assign(new Error("Forbidden"), { status: 403 });
    mockFetch.mockRejectedValue(err);
    const { container } = render(<InvoicesTable />);

    await waitFor(() => {
      expect(container.firstChild).toBeNull();
    });
  });

  it("shows total count in header", async () => {
    mockFetch.mockResolvedValue({ ...PAGE_ONE, total: 42 });
    render(<InvoicesTable />);

    await waitFor(() => {
      expect(screen.getByText("42 total")).toBeInTheDocument();
    });
  });

  it("calls fetchAdminInvoices with correct page on mount", async () => {
    mockFetch.mockResolvedValue(PAGE_ONE);
    render(<InvoicesTable />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        mockAuthFetch,
        1,
        20,
      );
    });
  });

  it("displays MercadoPago label for mercadopago provider", async () => {
    mockFetch.mockResolvedValue({
      ...PAGE_ONE,
      items: [{ ...INVOICE, provider: "mercadopago" }],
    });
    render(<InvoicesTable />);

    await waitFor(() => {
      expect(screen.getByText("MercadoPago")).toBeInTheDocument();
    });
  });
});
