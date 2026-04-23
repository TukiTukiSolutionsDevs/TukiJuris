/**
 * InvoiceHistorySection unit tests.
 * Spec: billing/spec.md — Invoice History and Details
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";

// ---------------------------------------------------------------------------
// Hoisted mocks
// ---------------------------------------------------------------------------

const { mockAuthFetch } = vi.hoisted(() => ({
  mockAuthFetch: vi.fn(),
}));

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({ authFetch: mockAuthFetch }),
}));

import { InvoiceHistorySection } from "../_components/InvoiceHistorySection";

const ORG_ID = "org-1";

const INVOICE = {
  id:         "inv-001",
  status:     "paid",
  total:      3900,
  currency:   "PEN",
  created_at: "2026-04-01T00:00:00Z",
};

function makeOk(data: unknown) {
  return { ok: true, status: 200, json: async () => data } as unknown as Response;
}

beforeEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("InvoiceHistorySection — loading state", () => {
  it("shows 3 skeleton rows while fetching", () => {
    mockAuthFetch.mockReturnValue(new Promise(() => {}));
    render(<InvoiceHistorySection orgId={ORG_ID} />);
    expect(screen.getByTestId("invoice-loading")).toBeInTheDocument();
  });
});

describe("InvoiceHistorySection — empty state", () => {
  it("shows empty message when no invoices returned", async () => {
    mockAuthFetch.mockResolvedValue(makeOk([]));
    render(<InvoiceHistorySection orgId={ORG_ID} />);
    await waitFor(() =>
      expect(screen.getByTestId("invoice-empty")).toBeInTheDocument()
    );
    expect(screen.getByTestId("invoice-empty").textContent).toContain(
      "Todavía no tenés facturas."
    );
  });
});

describe("InvoiceHistorySection — error state", () => {
  it("shows error message when fetch fails", async () => {
    mockAuthFetch.mockResolvedValue({ ok: false, status: 500, json: async () => ({}) });
    render(<InvoiceHistorySection orgId={ORG_ID} />);
    await waitFor(() =>
      expect(screen.getByTestId("invoice-error")).toBeInTheDocument()
    );
    expect(screen.getByText("No se pudieron cargar las facturas.")).toBeInTheDocument();
  });

  it("shows a retry button in error state", async () => {
    mockAuthFetch.mockResolvedValue({ ok: false, status: 500, json: async () => ({}) });
    render(<InvoiceHistorySection orgId={ORG_ID} />);
    await waitFor(() =>
      expect(screen.getByTestId("invoice-retry-btn")).toBeInTheDocument()
    );
  });

  it("retries the fetch when retry button is clicked", async () => {
    mockAuthFetch
      .mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({}) })
      .mockResolvedValue(makeOk([INVOICE]));

    const user = userEvent.setup();
    render(<InvoiceHistorySection orgId={ORG_ID} />);

    await waitFor(() => screen.getByTestId("invoice-retry-btn"));
    await user.click(screen.getByTestId("invoice-retry-btn"));

    await waitFor(() =>
      expect(screen.getByTestId("invoice-table")).toBeInTheDocument()
    );
  });
});

describe("InvoiceHistorySection — table rendering", () => {
  it("renders invoice table with fecha, estado, total columns", async () => {
    mockAuthFetch.mockResolvedValue(makeOk([INVOICE]));
    render(<InvoiceHistorySection orgId={ORG_ID} />);

    await waitFor(() =>
      expect(screen.getByTestId("invoice-table")).toBeInTheDocument()
    );

    const headers = screen.getAllByRole("columnheader");
    const texts = headers.map((h) => h.textContent?.trim() ?? "");
    expect(texts).toContain("Fecha");
    expect(texts).toContain("Estado");
    expect(texts).toContain("Total");
  });

  it("renders an invoice row for each invoice", async () => {
    mockAuthFetch.mockResolvedValue(makeOk([INVOICE]));
    render(<InvoiceHistorySection orgId={ORG_ID} />);

    await waitFor(() =>
      expect(screen.getByTestId("invoice-row-inv-001")).toBeInTheDocument()
    );
  });

  it("fetches invoice detail on row click", async () => {
    const DETAIL = { ...INVOICE, subtotal: 3300, tax: 600, items: [] };
    mockAuthFetch
      .mockResolvedValueOnce(makeOk([INVOICE]))    // list
      .mockResolvedValue(makeOk(DETAIL));            // detail

    const user = userEvent.setup();
    render(<InvoiceHistorySection orgId={ORG_ID} />);

    await waitFor(() => screen.getByTestId("invoice-row-inv-001"));
    await user.click(screen.getByTestId("invoice-row-inv-001"));

    await waitFor(() =>
      expect(screen.getByTestId("invoice-detail-modal")).toBeInTheDocument()
    );

    expect(mockAuthFetch).toHaveBeenCalledWith(
      `/api/billing/${ORG_ID}/invoices/inv-001`
    );
  });

  it("detail modal shows detail content after fetch", async () => {
    const DETAIL = { ...INVOICE, subtotal: 3300, tax: 600, items: [] };
    mockAuthFetch
      .mockResolvedValueOnce(makeOk([INVOICE]))
      .mockResolvedValue(makeOk(DETAIL));

    const user = userEvent.setup();
    render(<InvoiceHistorySection orgId={ORG_ID} />);

    await waitFor(() => screen.getByTestId("invoice-row-inv-001"));
    await user.click(screen.getByTestId("invoice-row-inv-001"));

    await waitFor(() =>
      expect(screen.getByTestId("invoice-detail-content")).toBeInTheDocument()
    );
  });

  it("calls GET /api/billing/{org_id}/invoices on mount", async () => {
    mockAuthFetch.mockResolvedValue(makeOk([]));
    render(<InvoiceHistorySection orgId={ORG_ID} />);

    await waitFor(() =>
      expect(mockAuthFetch).toHaveBeenCalledWith(`/api/billing/${ORG_ID}/invoices`)
    );
  });
});
