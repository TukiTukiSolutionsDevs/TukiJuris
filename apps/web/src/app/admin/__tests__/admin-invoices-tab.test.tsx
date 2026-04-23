/**
 * AdminInvoicesTab tests.
 * Spec: admin/spec.md — Admin Invoices Tab + Admin Invoice Mutations
 *
 * Tests: permission gating (via parent), filter/pagination, modal opening,
 *        disabled submit without reason, success close+refetch, error preservation.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";

// ---------------------------------------------------------------------------
// Hoisted mocks
// ---------------------------------------------------------------------------

const { mockAuthFetch, mockReplace, mockGet, mockToastSuccess, mockToastError } =
  vi.hoisted(() => ({
    mockAuthFetch:    vi.fn(),
    mockReplace:      vi.fn(),
    mockGet:          vi.fn().mockReturnValue(null),
    mockToastSuccess: vi.fn(),
    mockToastError:   vi.fn(),
  }));

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({ authFetch: mockAuthFetch }),
}));

vi.mock("next/navigation", () => ({
  useRouter:       () => ({ replace: mockReplace }),
  usePathname:     () => "/admin",
  useSearchParams: () => ({
    get:      mockGet,
    toString: () => "",
  }),
}));

vi.mock("sonner", () => ({
  toast: {
    success: mockToastSuccess,
    error:   mockToastError,
  },
}));

import { AdminInvoicesTab } from "../_components/AdminInvoicesTab";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const INVOICE = {
  id:         "inv-abc-0001",
  org_id:     "org-xyz-0001",
  status:     "paid",
  total:      3900,
  currency:   "PEN",
  created_at: "2026-04-01T00:00:00Z",
};

function makePage(items = [INVOICE], total = 1) {
  return {
    ok: true,
    json: async () => ({ items, total, page: 1, page_size: 20 }),
  } as unknown as Response;
}

function makeEmptyPage() {
  return {
    ok: true,
    json: async () => ({ items: [], total: 0, page: 1, page_size: 20 }),
  } as unknown as Response;
}

function makePatchOk() {
  return { ok: true, status: 200, json: async () => ({}) } as unknown as Response;
}

function makePatchFail() {
  return { ok: false, status: 500, json: async () => ({}) } as unknown as Response;
}

beforeEach(() => {
  vi.clearAllMocks();
  mockGet.mockReturnValue(null);
  mockAuthFetch.mockResolvedValue(makePage());
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("AdminInvoicesTab — loading & empty states", () => {
  it("shows loading state while fetching", () => {
    mockAuthFetch.mockReturnValue(new Promise(() => {}));
    render(<AdminInvoicesTab />);
    expect(screen.getByTestId("inv-loading")).toBeInTheDocument();
  });

  it("shows empty state when no invoices returned", async () => {
    mockAuthFetch.mockResolvedValue(makeEmptyPage());
    render(<AdminInvoicesTab />);
    await waitFor(() =>
      expect(screen.getByTestId("inv-empty")).toBeInTheDocument()
    );
  });

  it("renders the invoice table when invoices exist", async () => {
    render(<AdminInvoicesTab />);
    await waitFor(() =>
      expect(screen.getByTestId("inv-table")).toBeInTheDocument()
    );
  });
});

describe("AdminInvoicesTab — filter bar", () => {
  it("renders status select and org id input", async () => {
    render(<AdminInvoicesTab />);
    await waitFor(() => screen.getByTestId("inv-filter-bar"));
    expect(screen.getByTestId("filter-status")).toBeInTheDocument();
    expect(screen.getByTestId("filter-org-id")).toBeInTheDocument();
  });

  it("calls router.replace with filter params on Apply", async () => {
    const user = userEvent.setup();
    render(<AdminInvoicesTab />);
    await waitFor(() => screen.getByTestId("filter-org-id"));

    await user.type(screen.getByTestId("filter-org-id"), "org-xyz");
    await user.click(screen.getByTestId("apply-filters-btn"));

    expect(mockReplace).toHaveBeenCalledWith(
      expect.stringContaining("inv_org_id=org-xyz")
    );
  });

  it("clears all filter params on Clear", async () => {
    const user = userEvent.setup();
    mockGet.mockImplementation((key: string) =>
      key === "inv_status" ? "paid" : null
    );
    render(<AdminInvoicesTab />);
    await waitFor(() => screen.getByTestId("clear-filters-btn"));
    await user.click(screen.getByTestId("clear-filters-btn"));

    expect(mockReplace).toHaveBeenCalledWith("/admin?");
  });

  it("resets to page 1 when filters applied", async () => {
    const user = userEvent.setup();
    render(<AdminInvoicesTab />);
    await waitFor(() => screen.getByTestId("apply-filters-btn"));
    await user.click(screen.getByTestId("apply-filters-btn"));

    const callArg: string = mockReplace.mock.calls[0][0];
    expect(callArg).not.toContain("inv_page");
  });
});

describe("AdminInvoicesTab — pagination", () => {
  it("does NOT render pagination when total ≤ PAGE_SIZE", async () => {
    render(<AdminInvoicesTab />);
    await waitFor(() => screen.getByTestId("inv-table"));
    expect(screen.queryByTestId("inv-pagination")).toBeNull();
  });

  it("renders pagination when total > PAGE_SIZE", async () => {
    mockAuthFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        items: Array.from({ length: 20 }, (_, i) => ({ ...INVOICE, id: `inv-${i}` })),
        total: 45,
        page: 1,
        page_size: 20,
      }),
    } as unknown as Response);

    render(<AdminInvoicesTab />);
    await waitFor(() =>
      expect(screen.getByTestId("inv-pagination")).toBeInTheDocument()
    );
  });

  it("Anterior disabled on first page, Siguiente enabled", async () => {
    mockAuthFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        items: Array.from({ length: 20 }, (_, i) => ({ ...INVOICE, id: `inv-${i}` })),
        total: 45, page: 1, page_size: 20,
      }),
    } as unknown as Response);

    render(<AdminInvoicesTab />);
    await waitFor(() => screen.getByTestId("prev-page-btn"));
    expect(screen.getByTestId("prev-page-btn")).toBeDisabled();
    expect(screen.getByTestId("next-page-btn")).not.toBeDisabled();
  });
});

describe("AdminInvoicesTab — mutation modal", () => {
  it("opens modal when Reembolsar is clicked from action menu", async () => {
    const user = userEvent.setup();
    render(<AdminInvoicesTab />);

    await waitFor(() => screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await waitFor(() => screen.getByTestId(`refund-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`refund-btn-${INVOICE.id}`));

    await waitFor(() =>
      expect(screen.getByTestId("mutation-modal")).toBeInTheDocument()
    );
  });

  it("opens modal when Anular is clicked from action menu", async () => {
    const user = userEvent.setup();
    render(<AdminInvoicesTab />);

    await waitFor(() => screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await waitFor(() => screen.getByTestId(`void-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`void-btn-${INVOICE.id}`));

    await waitFor(() =>
      expect(screen.getByTestId("mutation-modal")).toBeInTheDocument()
    );
  });

  it("submit button is DISABLED when reason is empty", async () => {
    const user = userEvent.setup();
    render(<AdminInvoicesTab />);

    await waitFor(() => screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await waitFor(() => screen.getByTestId(`refund-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`refund-btn-${INVOICE.id}`));

    await waitFor(() => screen.getByTestId("modal-submit-btn"));
    expect(screen.getByTestId("modal-submit-btn")).toBeDisabled();
  });

  it("submit button is DISABLED when reason is only whitespace", async () => {
    const user = userEvent.setup();
    render(<AdminInvoicesTab />);

    await waitFor(() => screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await waitFor(() => screen.getByTestId(`refund-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`refund-btn-${INVOICE.id}`));

    await waitFor(() => screen.getByTestId("reason-textarea"));
    await user.type(screen.getByTestId("reason-textarea"), "   ");

    expect(screen.getByTestId("modal-submit-btn")).toBeDisabled();
  });

  it("submit button is ENABLED when reason has content", async () => {
    const user = userEvent.setup();
    render(<AdminInvoicesTab />);

    await waitFor(() => screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await waitFor(() => screen.getByTestId(`refund-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`refund-btn-${INVOICE.id}`));

    await waitFor(() => screen.getByTestId("reason-textarea"));
    await user.type(screen.getByTestId("reason-textarea"), "Duplicado");

    expect(screen.getByTestId("modal-submit-btn")).not.toBeDisabled();
  });

  it("on success: shows toast, closes modal, refetches list", async () => {
    mockAuthFetch
      .mockResolvedValueOnce(makePage())    // initial load
      .mockResolvedValueOnce(makePatchOk()) // PATCH
      .mockResolvedValue(makePage());        // refetch

    const user = userEvent.setup();
    render(<AdminInvoicesTab />);

    await waitFor(() => screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await waitFor(() => screen.getByTestId(`refund-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`refund-btn-${INVOICE.id}`));

    await waitFor(() => screen.getByTestId("reason-textarea"));
    await user.type(screen.getByTestId("reason-textarea"), "Solicitud del cliente");
    await user.click(screen.getByTestId("modal-submit-btn"));

    await waitFor(() => {
      expect(mockToastSuccess).toHaveBeenCalledWith("Factura reembolsada");
      expect(screen.queryByTestId("mutation-modal")).toBeNull();
    });

    // Refetch should have happened (3 calls total: initial + patch + refetch)
    expect(mockAuthFetch.mock.calls.length).toBeGreaterThanOrEqual(3);
  });

  it("on error: shows error toast, modal stays open, reason preserved", async () => {
    mockAuthFetch
      .mockResolvedValueOnce(makePage())    // initial load
      .mockResolvedValueOnce(makePatchFail()); // PATCH fails

    const user = userEvent.setup();
    render(<AdminInvoicesTab />);

    await waitFor(() => screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await waitFor(() => screen.getByTestId(`refund-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`refund-btn-${INVOICE.id}`));

    await waitFor(() => screen.getByTestId("reason-textarea"));
    await user.type(screen.getByTestId("reason-textarea"), "Motivo de prueba");
    await user.click(screen.getByTestId("modal-submit-btn"));

    await waitFor(() => expect(mockToastError).toHaveBeenCalledWith("No se pudo reembolsar la factura"));

    // Modal stays open
    expect(screen.getByTestId("mutation-modal")).toBeInTheDocument();

    // Reason preserved
    const textarea = screen.getByTestId("reason-textarea") as HTMLTextAreaElement;
    expect(textarea.value).toBe("Motivo de prueba");
  });

  it("issues PATCH /api/admin/invoices/{id} with action and reason", async () => {
    mockAuthFetch
      .mockResolvedValueOnce(makePage())
      .mockResolvedValueOnce(makePatchOk())
      .mockResolvedValue(makePage());

    const user = userEvent.setup();
    render(<AdminInvoicesTab />);

    await waitFor(() => screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await waitFor(() => screen.getByTestId(`void-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`void-btn-${INVOICE.id}`));

    await waitFor(() => screen.getByTestId("reason-textarea"));
    await user.type(screen.getByTestId("reason-textarea"), "Fraudulento");
    await user.click(screen.getByTestId("modal-submit-btn"));

    await waitFor(() => expect(mockToastSuccess).toHaveBeenCalledWith("Factura anulada"));

    expect(mockAuthFetch).toHaveBeenCalledWith(
      `/api/admin/invoices/${INVOICE.id}`,
      expect.objectContaining({
        method: "PATCH",
        body:   JSON.stringify({ action: "void", reason: "Fraudulento" }),
      })
    );
  });

  it("on void error: shows 'No se pudo anular la factura' toast, modal stays open", async () => {
    mockAuthFetch
      .mockResolvedValueOnce(makePage())    // initial load
      .mockResolvedValueOnce(makePatchFail()); // PATCH fails

    const user = userEvent.setup();
    render(<AdminInvoicesTab />);

    await waitFor(() => screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`action-menu-btn-${INVOICE.id}`));
    await waitFor(() => screen.getByTestId(`void-btn-${INVOICE.id}`));
    await user.click(screen.getByTestId(`void-btn-${INVOICE.id}`));

    await waitFor(() => screen.getByTestId("reason-textarea"));
    await user.type(screen.getByTestId("reason-textarea"), "Motivo anulación");
    await user.click(screen.getByTestId("modal-submit-btn"));

    await waitFor(() =>
      expect(mockToastError).toHaveBeenCalledWith("No se pudo anular la factura")
    );

    // Modal stays open
    expect(screen.getByTestId("mutation-modal")).toBeInTheDocument();
  });
});
