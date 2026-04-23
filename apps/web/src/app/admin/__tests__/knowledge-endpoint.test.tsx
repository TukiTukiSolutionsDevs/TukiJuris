/**
 * Admin knowledge endpoint swap tests — /admin page
 *
 * Covers FE-ADMIN-KB-SWAP:
 *   KE-1  /api/admin/knowledge ok → kbHealth data rendered from primary endpoint
 *   KE-2  /api/admin/knowledge non-ok → fallback to /api/health/knowledge, data rendered
 *   KE-3  /api/admin/knowledge 403 → fallback to /api/health/knowledge, data rendered
 *   KE-4  Both endpoints fail → kbHealth section not rendered (graceful)
 *   KE-5  No toast shown on fallback
 */

import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import React from "react";

// ---------------------------------------------------------------------------
// Hoisted mocks
// ---------------------------------------------------------------------------
const { mockReplace, mockGet } = vi.hoisted(() => ({
  mockReplace: vi.fn(),
  mockGet: vi.fn().mockReturnValue(null),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace }),
  usePathname: () => "/admin",
  useSearchParams: () => ({
    get: mockGet,
    toString: () => "",
  }),
}));

const { mockAuthFetch, mockHasPermission } = vi.hoisted(() => ({
  mockAuthFetch: vi.fn(),
  mockHasPermission: vi.fn().mockReturnValue(false),
}));

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({
    authFetch: mockAuthFetch,
    hasPermission: mockHasPermission,
    user: { id: "admin-1", email: "admin@test.com", isAdmin: true },
  }),
}));

// Stub heavy sub-components
vi.mock("../_components/RevenueCards", () => ({ RevenueCards: () => <div data-testid="revenue-cards" /> }));
vi.mock("../_components/BYOKBadge", () => ({ BYOKBadge: () => <span data-testid="byok-badge" /> }));
vi.mock("../_components/BYOKTable", () => ({ BYOKTable: () => <div data-testid="byok-table" /> }));
vi.mock("../_components/InvoicesTable", () => ({ InvoicesTable: () => <div data-testid="invoices-table" /> }));
vi.mock("../_components/UsersPagination", () => ({ UsersPagination: () => <div data-testid="users-pagination" /> }));
vi.mock("../_components/UserRolesPanel", () => ({ UserRolesPanel: () => <div data-testid="user-roles-panel" /> }));
vi.mock("../_components/AuditLogTab", () => ({ AuditLogTab: () => <div data-testid="audit-log-tab" /> }));
vi.mock("@/components/AdminLayout", () => ({ AdminLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }));
vi.mock("@/components/shell/InternalPageHeader", () => ({ InternalPageHeader: () => <div data-testid="page-header" /> }));
vi.mock("@/components/shell/ShellUtilityActions", () => ({ ShellUtilityActions: () => null }));

// ---------------------------------------------------------------------------
// Import AFTER mocks
// ---------------------------------------------------------------------------
import AdminPage from "../page";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const KB_HEALTH_DATA = {
  status: "ok",
  total_documents: 10,
  total_chunks: 500,
  embedded_chunks: 490,
  embedding_coverage: 98,
  chunks_by_area: { civil: 200, penal: 300 },
};

function makeOk(data: unknown) {
  return { ok: true, status: 200, json: async () => data } as unknown as Response;
}

function makeError(status = 500) {
  return { ok: false, status, json: async () => ({}) } as unknown as Response;
}

function setupBaseAuthFetch(overrides: (url: string) => Response | null = () => null) {
  mockAuthFetch.mockImplementation(async (url: string) => {
    const override = overrides(url);
    if (override !== null) return override;
    if (url.includes("/api/health/ready")) return makeOk({ status: "ok", checks: { database: "ok", pgvector: "ok" } });
    if (url.includes("/api/health")) return makeOk({ status: "ok" });
    if (url.includes("/api/admin/users")) return makeOk({ users: [], total: 0, page: 1, per_page: 20 });
    if (url.includes("/api/admin/stats")) return makeOk({ total_users: 0, total_organizations: 0, queries_today: 0, total_conversations: 0 });
    if (url.includes("/api/admin/activity")) return makeOk([]);
    return makeError(403);
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  mockGet.mockReturnValue(null);
  mockHasPermission.mockReturnValue(false);
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("AdminPage — knowledge endpoint swap (B4)", () => {
  it("KE-1: /api/admin/knowledge ok → kbHealth section rendered", async () => {
    setupBaseAuthFetch((url) => {
      if (url.includes("/api/admin/knowledge")) return makeOk(KB_HEALTH_DATA);
      return null;
    });

    render(<AdminPage />);

    // The kbHealth section renders "Respaldo & Base de conocimiento" heading
    await waitFor(() => {
      expect(screen.getByText(/Respaldo & Base de conocimiento/i)).toBeInTheDocument();
    });
    // Embedding coverage
    expect(screen.getByText(/98% cobertura/)).toBeInTheDocument();
  });

  it("KE-2: /api/admin/knowledge non-ok → falls back to /api/health/knowledge, data rendered", async () => {
    let adminKnowledgeCalled = false;
    let fallbackCalled = false;

    setupBaseAuthFetch((url) => {
      if (url === "/api/admin/knowledge") {
        adminKnowledgeCalled = true;
        return makeError(500);
      }
      if (url === "/api/health/knowledge") {
        fallbackCalled = true;
        return makeOk(KB_HEALTH_DATA);
      }
      return null;
    });

    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText(/Respaldo & Base de conocimiento/i)).toBeInTheDocument();
    });

    expect(adminKnowledgeCalled).toBe(true);
    expect(fallbackCalled).toBe(true);
  });

  it("KE-3: /api/admin/knowledge 403 → falls back to /api/health/knowledge", async () => {
    let fallbackCalled = false;

    setupBaseAuthFetch((url) => {
      if (url === "/api/admin/knowledge") return makeError(403);
      if (url === "/api/health/knowledge") {
        fallbackCalled = true;
        return makeOk(KB_HEALTH_DATA);
      }
      return null;
    });

    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText(/Respaldo & Base de conocimiento/i)).toBeInTheDocument();
    });

    expect(fallbackCalled).toBe(true);
  });

  it("KE-4: both endpoints fail → kbHealth section not rendered, no crash", async () => {
    setupBaseAuthFetch((url) => {
      if (url === "/api/admin/knowledge") return makeError(500);
      if (url === "/api/health/knowledge") return makeError(500);
      return null;
    });

    render(<AdminPage />);

    // Page must not crash — wait for load to complete
    await waitFor(() => {
      expect(screen.queryByText(/Cargando panel/i)).not.toBeInTheDocument();
    });

    // kbHealth section must not appear
    expect(screen.queryByText(/Respaldo/i)).not.toBeInTheDocument();
  });

  it("KE-5: no toast shown when falling back to /api/health/knowledge", async () => {
    // sonner is NOT mocked here — if toast was called it would throw or appear
    setupBaseAuthFetch((url) => {
      if (url === "/api/admin/knowledge") return makeError(403);
      if (url === "/api/health/knowledge") return makeOk(KB_HEALTH_DATA);
      return null;
    });

    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText(/Respaldo & Base de conocimiento/i)).toBeInTheDocument();
    });

    // No error text should be visible in the page
    expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
  });

  it("KE-6: defensive mapping — partial KB response (missing fields) does not crash", async () => {
    setupBaseAuthFetch((url) => {
      if (url === "/api/admin/knowledge") {
        // Only partial data — missing several optional fields
        return makeOk({ status: "ok", chunks_by_area: {} });
      }
      return null;
    });

    render(<AdminPage />);

    // Should not throw, kbHealth section renders
    await waitFor(() => {
      expect(screen.getByText(/Respaldo & Base de conocimiento/i)).toBeInTheDocument();
    });
    // Defaults to 0% coverage
    expect(screen.getByText(/0% cobertura/)).toBeInTheDocument();
  });
});
