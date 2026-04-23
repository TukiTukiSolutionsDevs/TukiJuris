/**
 * Admin page tab navigation tests.
 *
 * Spec IDs: FE-ADMIN-TABS, FE-ADMIN-TESTS
 * Tests tab rendering, URL-driven switching, and legacy Resumen content.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";

// ---------------------------------------------------------------------------
// Hoisted mocks
// ---------------------------------------------------------------------------

const { mockReplace, mockGet } = vi.hoisted(() => ({
  mockReplace: vi.fn(),
  mockGet: vi.fn().mockReturnValue(null), // default: no ?tab= param → "resumen"
}));

vi.mock("next/navigation", () => ({
  useRouter:      () => ({ replace: mockReplace }),
  usePathname:    () => "/admin",
  useSearchParams: () => ({
    get: mockGet,
    toString: () => "",
  }),
}));

const { mockAuthFetch, mockHasPermission } = vi.hoisted(() => ({
  mockAuthFetch:      vi.fn(),
  mockHasPermission:  vi.fn().mockReturnValue(false),
}));

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({
    authFetch:     mockAuthFetch,
    hasPermission: mockHasPermission,
    user:          { id: "admin-1", email: "admin@test.com", isAdmin: true },
  }),
}));

// Stub heavy sub-components to avoid cascading fetches
vi.mock("../_components/RevenueCards",    () => ({ RevenueCards:    () => <div data-testid="revenue-cards" /> }));
vi.mock("../_components/BYOKBadge",       () => ({ BYOKBadge:       () => <span data-testid="byok-badge" /> }));
vi.mock("../_components/BYOKTable",       () => ({ BYOKTable:       () => <div data-testid="byok-table" /> }));
vi.mock("../_components/InvoicesTable",   () => ({ InvoicesTable:   () => <div data-testid="invoices-table" /> }));
vi.mock("../_components/UsersPagination", () => ({ UsersPagination: () => <div data-testid="users-pagination" /> }));
vi.mock("../_components/UserRolesPanel",  () => ({ UserRolesPanel:  () => <div data-testid="user-roles-panel" /> }));
vi.mock("../_components/AuditLogTab",        () => ({ AuditLogTab:        () => <div data-testid="audit-log-tab" /> }));
vi.mock("../_components/AdminInvoicesTab",   () => ({ AdminInvoicesTab:   () => <div data-testid="admin-invoices-tab" /> }));

vi.mock("@/components/AdminLayout", () => ({
  AdminLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));
vi.mock("@/components/shell/InternalPageHeader", () => ({
  InternalPageHeader: () => <div data-testid="page-header" />,
}));
vi.mock("@/components/shell/ShellUtilityActions", () => ({
  ShellUtilityActions: () => null,
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeOkJsonResponse(data: unknown): Response {
  return {
    ok: true,
    json: async () => data,
    status: 200,
  } as unknown as Response;
}

function setupDefaultFetches() {
  mockAuthFetch.mockImplementation((url: string) => {
    if (url.includes("/api/health/ready"))    return Promise.resolve(makeOkJsonResponse({ status: "ok", checks: { database: "ok", pgvector: "ok" } }));
    if (url.includes("/api/health/knowledge")) return Promise.resolve(makeOkJsonResponse({ status: "ok", total_documents: 0, total_chunks: 0, embedded_chunks: 0, embedding_coverage: 100, chunks_by_area: {} }));
    if (url.includes("/api/health"))          return Promise.resolve(makeOkJsonResponse({ status: "ok" }));
    if (url.includes("/api/admin/users"))     return Promise.resolve(makeOkJsonResponse({ users: [], total: 0, page: 1, per_page: 20 }));
    if (url.includes("/api/admin/stats"))     return Promise.resolve(makeOkJsonResponse({ total_users: 0, total_organizations: 0, queries_today: 0, total_conversations: 0 }));
    if (url.includes("/api/admin/activity"))  return Promise.resolve(makeOkJsonResponse([]));
    return Promise.resolve({ ok: false, status: 403, json: async () => ({}) } as unknown as Response);
  });
}

import AdminPage from "../page";

beforeEach(() => {
  vi.clearAllMocks();
  mockGet.mockReturnValue(null); // default: no tab param
  mockHasPermission.mockReturnValue(false);
  setupDefaultFetches();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("AdminPage tab navigation", () => {
  it("renders the Resumen and Auditoría tab buttons", async () => {
    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Resumen" })).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: "Auditoría" })).toBeInTheDocument();
    });
  });

  it("defaults to Resumen tab when no ?tab= param", async () => {
    mockGet.mockReturnValue(null);
    render(<AdminPage />);

    await waitFor(() => {
      const resumenTab = screen.getByRole("tab", { name: "Resumen" });
      expect(resumenTab).toHaveAttribute("aria-selected", "true");
    });

    expect(screen.queryByTestId("audit-log-tab")).toBeNull();
  });

  it("shows Auditoría tab selected when ?tab=auditoria", async () => {
    mockGet.mockImplementation((key: string) =>
      key === "tab" ? "auditoria" : null
    );

    render(<AdminPage />);

    await waitFor(() => {
      const auditoriaTab = screen.getByRole("tab", { name: "Auditoría" });
      expect(auditoriaTab).toHaveAttribute("aria-selected", "true");
    });

    expect(screen.getByTestId("audit-log-tab")).toBeInTheDocument();
  });

  it("calls router.replace with ?tab=auditoria when Auditoría tab is clicked", async () => {
    const user = userEvent.setup();
    render(<AdminPage />);

    await waitFor(() => screen.getByRole("tab", { name: "Auditoría" }));
    await user.click(screen.getByRole("tab", { name: "Auditoría" }));

    expect(mockReplace).toHaveBeenCalledWith(
      expect.stringContaining("tab=auditoria")
    );
  });

  it("calls router.replace with ?tab=resumen when Resumen tab is clicked", async () => {
    mockGet.mockImplementation((key: string) =>
      key === "tab" ? "auditoria" : null
    );
    const user = userEvent.setup();
    render(<AdminPage />);

    await waitFor(() => screen.getByRole("tab", { name: "Resumen" }));
    await user.click(screen.getByRole("tab", { name: "Resumen" }));

    expect(mockReplace).toHaveBeenCalledWith(
      expect.stringContaining("tab=resumen")
    );
  });

  it("Resumen tab renders the users section when users are returned", async () => {
    mockAuthFetch.mockImplementation((url: string) => {
      if (url.includes("/api/admin/users"))
        return Promise.resolve(
          makeOkJsonResponse({
            users: [
              {
                id: "u1",
                email: "alice@test.com",
                full_name: "Alice",
                plan: "pro",
                queries_this_month: 5,
                created_at: "2026-01-01T00:00:00Z",
                last_active: null,
                byok_count: 0,
              },
            ],
            total: 1,
            page: 1,
            per_page: 20,
          })
        );
      if (url.includes("/api/admin/stats"))      return Promise.resolve(makeOkJsonResponse({ total_users: 1, total_organizations: 0, queries_today: 0, total_conversations: 0 }));
      if (url.includes("/api/health/knowledge")) return Promise.resolve(makeOkJsonResponse({ status: "ok", total_documents: 0, total_chunks: 0, embedded_chunks: 0, embedding_coverage: 100, chunks_by_area: {} }));
      if (url.includes("/api/health/ready"))     return Promise.resolve(makeOkJsonResponse({ status: "ok", checks: { database: "ok", pgvector: "ok" } }));
      if (url.includes("/api/health"))           return Promise.resolve(makeOkJsonResponse({ status: "ok" }));
      if (url.includes("/api/admin/activity"))   return Promise.resolve(makeOkJsonResponse([]));
      return Promise.resolve({ ok: false, status: 403, json: async () => ({}) } as unknown as Response);
    });

    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText("Alice")).toBeInTheDocument();
    });
  });

  it("does NOT render AuditLogTab stub in Resumen tab", async () => {
    mockGet.mockReturnValue(null);
    render(<AdminPage />);
    await waitFor(() => screen.getByRole("tab", { name: "Resumen" }));
    expect(screen.queryByTestId("audit-log-tab")).toBeNull();
  });

  it("tablist has correct aria-label", async () => {
    render(<AdminPage />);
    await waitFor(() =>
      expect(
        screen.getByRole("tablist", { name: "Secciones del panel de administración" })
      ).toBeInTheDocument()
    );
  });
});

// ---------------------------------------------------------------------------
// Facturas tab — security gating (Sprint 8b)
// ---------------------------------------------------------------------------

describe("AdminPage — Facturas tab (billing:update gate)", () => {
  it("renders Facturas tab button", async () => {
    render(<AdminPage />);
    await waitFor(() =>
      expect(screen.getByTestId("facturas-tab-btn")).toBeInTheDocument()
    );
    expect(screen.getByTestId("facturas-tab-btn").textContent).toBe("Facturas");
  });

  it("Facturas tab button is DISABLED when hasPermission('billing:update') returns false", async () => {
    mockHasPermission.mockReturnValue(false);
    render(<AdminPage />);
    await waitFor(() => screen.getByTestId("facturas-tab-btn"));
    expect(screen.getByTestId("facturas-tab-btn")).toBeDisabled();
  });

  it("tooltip is present in DOM when permission is missing", async () => {
    mockHasPermission.mockReturnValue(false);
    render(<AdminPage />);
    await waitFor(() => screen.getByTestId("facturas-tab-tooltip"));
    expect(screen.getByTestId("facturas-tab-tooltip").textContent).toContain(
      "Requiere permiso billing:update"
    );
  });

  it("Facturas tab button is ENABLED when hasPermission('billing:update') returns true", async () => {
    mockHasPermission.mockImplementation((perm: string) => perm === "billing:update");
    render(<AdminPage />);
    await waitFor(() => screen.getByTestId("facturas-tab-btn"));
    expect(screen.getByTestId("facturas-tab-btn")).not.toBeDisabled();
  });

  it("tooltip is NOT rendered when permission is granted", async () => {
    mockHasPermission.mockImplementation((perm: string) => perm === "billing:update");
    render(<AdminPage />);
    await waitFor(() => screen.getByTestId("facturas-tab-btn"));
    expect(screen.queryByTestId("facturas-tab-tooltip")).toBeNull();
  });

  it("navigates to ?tab=facturas when Facturas tab is clicked with permission", async () => {
    mockHasPermission.mockImplementation((perm: string) => perm === "billing:update");
    const user = userEvent.setup();
    render(<AdminPage />);

    await waitFor(() => screen.getByTestId("facturas-tab-btn"));
    await user.click(screen.getByTestId("facturas-tab-btn"));

    expect(mockReplace).toHaveBeenCalledWith(
      expect.stringContaining("tab=facturas")
    );
  });

  it("does NOT navigate when Facturas tab is clicked WITHOUT permission", async () => {
    mockHasPermission.mockReturnValue(false);
    const user = userEvent.setup();
    render(<AdminPage />);

    await waitFor(() => screen.getByTestId("facturas-tab-btn"));
    await user.click(screen.getByTestId("facturas-tab-btn"));

    expect(mockReplace).not.toHaveBeenCalledWith(
      expect.stringContaining("tab=facturas")
    );
  });

  it("renders AdminInvoicesTab when ?tab=facturas AND permission granted", async () => {
    mockHasPermission.mockImplementation((perm: string) => perm === "billing:update");
    mockGet.mockImplementation((key: string) => key === "tab" ? "facturas" : null);
    render(<AdminPage />);

    await waitFor(() =>
      expect(screen.getByTestId("admin-invoices-tab")).toBeInTheDocument()
    );
  });

  it("does NOT render AdminInvoicesTab when ?tab=facturas but NO permission", async () => {
    mockHasPermission.mockReturnValue(false);
    mockGet.mockImplementation((key: string) => key === "tab" ? "facturas" : null);
    render(<AdminPage />);

    await waitFor(() => screen.getByTestId("facturas-tab-btn"));
    expect(screen.queryByTestId("admin-invoices-tab")).toBeNull();
  });
});
