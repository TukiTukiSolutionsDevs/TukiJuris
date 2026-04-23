/**
 * AuditLogTab tests.
 *
 * Spec IDs: FE-AUDITLOG-TAB, FE-AUDITLOG-PAGINATION, FE-ADMIN-TESTS
 * Tests: loading/empty states, row expansion (JSON), filters, pagination boundaries.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";

// ---------------------------------------------------------------------------
// Hoisted mocks
// ---------------------------------------------------------------------------

const { mockAuthFetch, mockReplace, mockGet } = vi.hoisted(() => ({
  mockAuthFetch: vi.fn(),
  mockReplace:   vi.fn(),
  mockGet:       vi.fn().mockReturnValue(null),
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

import { AuditLogTab } from "../_components/AuditLogTab";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const ENTRY = {
  id:            "entry-1",
  user_id:       "actor-uuid-1234",
  action:        "role.assign",
  resource_type: "user_role",
  resource_id:   "some-resource",
  before_state:  { role: "support" },
  after_state:   { role: "super_admin" },
  ip_address:    "127.0.0.1",
  created_at:    "2026-04-22T10:00:00Z",
};

function makePage(items = [ENTRY], total = 1): Response {
  return {
    ok: true,
    json: async () => ({ items, total, page: 1, page_size: 20 }),
  } as unknown as Response;
}

function makeEmptyPage(): Response {
  return {
    ok: true,
    json: async () => ({ items: [], total: 0, page: 1, page_size: 20 }),
  } as unknown as Response;
}

beforeEach(() => {
  vi.clearAllMocks();
  mockGet.mockReturnValue(null);
  mockAuthFetch.mockResolvedValue(makePage());
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("AuditLogTab — loading and empty states", () => {
  it("shows loading state while fetching", () => {
    mockAuthFetch.mockReturnValue(new Promise(() => {}));
    render(<AuditLogTab />);
    expect(screen.getByTestId("audit-loading")).toBeInTheDocument();
  });

  it("shows empty state when no entries returned", async () => {
    mockAuthFetch.mockResolvedValue(makeEmptyPage());
    render(<AuditLogTab />);
    await waitFor(() =>
      expect(screen.getByTestId("audit-empty")).toBeInTheDocument()
    );
  });

  it("renders the audit table when entries exist", async () => {
    render(<AuditLogTab />);
    await waitFor(() =>
      expect(screen.getByTestId("audit-table")).toBeInTheDocument()
    );
    expect(screen.getByText("role.assign")).toBeInTheDocument();
  });
});

describe("AuditLogTab — row expansion with JSON", () => {
  it("expands a row and shows before_state as formatted JSON", async () => {
    const user = userEvent.setup();
    render(<AuditLogTab />);

    await waitFor(() => screen.getByTestId("audit-row-entry-1"));
    await user.click(screen.getByTestId("audit-row-entry-1"));

    await waitFor(() =>
      expect(screen.getByTestId("audit-row-entry-1-expanded")).toBeInTheDocument()
    );

    // Verify expanded row contains the before_state JSON content
    const expanded = screen.getByTestId("audit-row-entry-1-expanded");
    expect(expanded.textContent).toContain('"role"');
    expect(expanded.textContent).toContain('"support"');
  });

  it("expands a row and shows after_state as formatted JSON", async () => {
    const user = userEvent.setup();
    render(<AuditLogTab />);

    await waitFor(() => screen.getByTestId("audit-row-entry-1"));
    await user.click(screen.getByTestId("audit-row-entry-1"));

    await waitFor(() => screen.getByTestId("audit-row-entry-1-expanded"));
    const expanded = screen.getByTestId("audit-row-entry-1-expanded");
    expect(expanded.textContent).toContain('"super_admin"');
  });

  it("collapses an expanded row when clicked again", async () => {
    const user = userEvent.setup();
    render(<AuditLogTab />);

    await waitFor(() => screen.getByTestId("audit-row-entry-1"));
    await user.click(screen.getByTestId("audit-row-entry-1"));
    await waitFor(() => screen.getByTestId("audit-row-entry-1-expanded"));

    await user.click(screen.getByTestId("audit-row-entry-1"));
    await waitFor(() =>
      expect(screen.queryByTestId("audit-row-entry-1-expanded")).toBeNull()
    );
  });

  it("shows null-state message when both before and after state are null", async () => {
    mockAuthFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [{ ...ENTRY, before_state: null, after_state: null }],
        total: 1,
        page: 1,
        page_size: 20,
      }),
    } as unknown as Response);

    const user = userEvent.setup();
    render(<AuditLogTab />);

    await waitFor(() => screen.getByTestId("audit-row-entry-1"));
    await user.click(screen.getByTestId("audit-row-entry-1"));

    await waitFor(() =>
      expect(screen.getByText(/Sin estado antes\/después registrado/)).toBeInTheDocument()
    );
  });
});

describe("AuditLogTab — filters", () => {
  it("renders the filter bar", async () => {
    render(<AuditLogTab />);
    await waitFor(() =>
      expect(screen.getByTestId("audit-filter-bar")).toBeInTheDocument()
    );
    expect(screen.getByTestId("filter-actor")).toBeInTheDocument();
    expect(screen.getByTestId("filter-action")).toBeInTheDocument();
    expect(screen.getByTestId("filter-resource")).toBeInTheDocument();
    expect(screen.getByTestId("filter-date-from")).toBeInTheDocument();
    expect(screen.getByTestId("filter-date-to")).toBeInTheDocument();
  });

  it("calls router.replace with filter params when Apply is clicked", async () => {
    const user = userEvent.setup();
    render(<AuditLogTab />);

    await waitFor(() => screen.getByTestId("filter-action"));

    await user.type(screen.getByTestId("filter-action"), "role.assign");
    await user.click(screen.getByTestId("apply-filters-btn"));

    expect(mockReplace).toHaveBeenCalledWith(
      expect.stringContaining("audit_action=role.assign")
    );
  });

  it("clears all filter params when Clear is clicked", async () => {
    const user = userEvent.setup();
    // Simulate pre-existing filter params
    mockGet.mockImplementation((key: string) =>
      key === "audit_action" ? "role.assign" : null
    );

    render(<AuditLogTab />);
    await waitFor(() => screen.getByTestId("clear-filters-btn"));
    await user.click(screen.getByTestId("clear-filters-btn"));

    expect(mockReplace).toHaveBeenCalledWith("/admin?");
  });

  it("resets to page 1 when filters are applied", async () => {
    const user = userEvent.setup();
    render(<AuditLogTab />);

    await waitFor(() => screen.getByTestId("apply-filters-btn"));
    await user.click(screen.getByTestId("apply-filters-btn"));

    // audit_page should NOT be in the replace call (deleted = reset to 1)
    const callArg: string = mockReplace.mock.calls[0][0];
    expect(callArg).not.toContain("audit_page");
  });
});

describe("AuditLogTab — pagination", () => {
  it("does NOT render pagination when total ≤ PAGE_SIZE", async () => {
    // 1 item, total=1 < 20
    render(<AuditLogTab />);
    await waitFor(() => screen.getByTestId("audit-table"));
    expect(screen.queryByTestId("audit-pagination")).toBeNull();
  });

  it("renders pagination when total > PAGE_SIZE", async () => {
    mockAuthFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        items: Array.from({ length: 20 }, (_, i) => ({
          ...ENTRY,
          id: `entry-${i}`,
        })),
        total: 45,
        page: 1,
        page_size: 20,
      }),
    } as unknown as Response);

    render(<AuditLogTab />);
    await waitFor(() =>
      expect(screen.getByTestId("audit-pagination")).toBeInTheDocument()
    );
  });

  it("disables Previous button on first page", async () => {
    mockAuthFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        items: Array.from({ length: 20 }, (_, i) => ({ ...ENTRY, id: `e${i}` })),
        total: 45,
        page: 1,
        page_size: 20,
      }),
    } as unknown as Response);

    render(<AuditLogTab />);
    await waitFor(() => screen.getByTestId("prev-page-btn"));
    expect(screen.getByTestId("prev-page-btn")).toBeDisabled();
    expect(screen.getByTestId("next-page-btn")).not.toBeDisabled();
  });

  it("disables Next button on last page", async () => {
    // Simulate page 3 of 3
    mockGet.mockImplementation((key: string) =>
      key === "audit_page" ? "3" : null
    );
    mockAuthFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        items: Array.from({ length: 5 }, (_, i) => ({ ...ENTRY, id: `e${i}` })),
        total: 45,   // 45 / 20 = 3 pages
        page: 3,
        page_size: 20,
      }),
    } as unknown as Response);

    render(<AuditLogTab />);
    await waitFor(() => screen.getByTestId("next-page-btn"));
    expect(screen.getByTestId("next-page-btn")).toBeDisabled();
    expect(screen.getByTestId("prev-page-btn")).not.toBeDisabled();
  });

  it("calls router.replace with incremented audit_page when Next is clicked", async () => {
    mockAuthFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        items: Array.from({ length: 20 }, (_, i) => ({ ...ENTRY, id: `e${i}` })),
        total: 45,
        page: 1,
        page_size: 20,
      }),
    } as unknown as Response);

    const user = userEvent.setup();
    render(<AuditLogTab />);

    await waitFor(() => screen.getByTestId("next-page-btn"));
    await user.click(screen.getByTestId("next-page-btn"));

    expect(mockReplace).toHaveBeenCalledWith(
      expect.stringContaining("audit_page=2")
    );
  });
});

// ---------------------------------------------------------------------------
// R8 — exact copy + 5-column contract assertions
// ---------------------------------------------------------------------------

describe("AuditLogTab — exact spec copy", () => {
  it("empty-state text matches spec exactly", async () => {
    mockAuthFetch.mockResolvedValue(makeEmptyPage());
    render(<AuditLogTab />);
    await waitFor(() =>
      expect(screen.getByTestId("audit-empty").textContent?.trim()).toBe(
        "No hay entradas que coincidan con los filtros."
      )
    );
  });
});

describe("AuditLogTab — column contract", () => {
  it("renders all 5 required columns as distinct headers", async () => {
    render(<AuditLogTab />);
    await waitFor(() => screen.getByTestId("audit-table"));
    const headers = screen.getAllByRole("columnheader");
    // 6 total: empty expand-icon column + 5 spec-required columns
    expect(headers.length).toBeGreaterThanOrEqual(6);
    const texts = headers.map((h) => h.textContent?.trim() ?? "");
    expect(texts).toContain("Timestamp");
    expect(texts).toContain("Actor");
    expect(texts).toContain("Acción");
    expect(texts).toContain("Tipo recurso");
    expect(texts).toContain("ID recurso");
  });

  it("renders resource_type and resource_id in separate cells", async () => {
    render(<AuditLogTab />);
    await waitFor(() => screen.getByTestId("audit-row-entry-1"));
    // Both values from ENTRY fixture should appear independently
    expect(screen.getByText("user_role")).toBeInTheDocument();
    expect(screen.getByText("some-resource")).toBeInTheDocument();
  });
});
