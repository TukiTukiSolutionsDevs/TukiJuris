/**
 * Analytics page — OrgSwitcher integration tests.
 * Spec: analytics/spec.md — Organization-Scoped Analytics
 *
 * Tests: hydration, invalid-stored-org fallback, single-org hidden,
 *        persistence on change, refetch after switch.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach, afterEach, beforeAll } from "vitest";
import React from "react";

// ---------------------------------------------------------------------------
// localStorage stub (jsdom may not expose full Storage API in all envs)
// ---------------------------------------------------------------------------

const lsStore: Record<string, string> = {};
const localStorageMock: Storage = {
  getItem: (key: string) => lsStore[key] ?? null,
  setItem: (key: string, value: string) => { lsStore[key] = value; },
  removeItem: (key: string) => { delete lsStore[key]; },
  clear: () => { Object.keys(lsStore).forEach((k) => delete lsStore[k]); },
  key: (index: number) => Object.keys(lsStore)[index] ?? null,
  get length() { return Object.keys(lsStore).length; },
};

beforeAll(() => {
  vi.stubGlobal("localStorage", localStorageMock);
});

// ---------------------------------------------------------------------------
// Hoisted mocks
// ---------------------------------------------------------------------------

const { mockAuthFetch } = vi.hoisted(() => ({
  mockAuthFetch: vi.fn(),
}));

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({
    authFetch: mockAuthFetch,
    user: { id: "u1", email: "admin@test.com", isAdmin: true },
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
  usePathname: () => "/analytics",
  useSearchParams: () => ({ get: vi.fn().mockReturnValue(null), toString: () => "" }),
}));

vi.mock("@/components/AppLayout", () => ({
  AppLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));
vi.mock("@/components/shell/InternalPageHeader", () => ({
  InternalPageHeader: ({ actions }: { actions?: React.ReactNode }) => (
    <div data-testid="page-header">{actions}</div>
  ),
}));
vi.mock("@/components/shell/ShellUtilityActions", () => ({
  ShellUtilityActions: () => null,
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const MULTI_ORGS = [
  { id: "org-1", name: "Alpha Legal" },
  { id: "org-2", name: "Beta Corp" },
];

const SINGLE_ORG = [{ id: "org-1", name: "Alpha Legal" }];

function makeOkResponse(data: unknown) {
  return { ok: true, json: async () => data } as unknown as Response;
}

function makeAnalyticsResponse() {
  return makeOkResponse({
    queries_today: 0,
    queries_today_vs_yesterday_pct: 0,
    queries_week: 0,
    queries_month: 0,
    queries_trend: [],
    top_areas: [],
    top_models: [],
    avg_latency_ms: 0,
    satisfaction_rate: 0,
    active_users: 0,
  });
}

function setupFetches(orgs: typeof MULTI_ORGS) {
  mockAuthFetch.mockImplementation((url: string) => {
    if (url.includes("/api/organizations")) return Promise.resolve(makeOkResponse(orgs));
    if (url.includes("/overview")) return Promise.resolve(makeAnalyticsResponse());
    if (url.includes("/areas")) return Promise.resolve(makeOkResponse({ areas: [] }));
    if (url.includes("/models")) return Promise.resolve(makeOkResponse({ models: [] }));
    if (url.includes("/queries")) return Promise.resolve(makeOkResponse({ queries: [] }));
    if (url.includes("/costs")) return Promise.resolve(makeOkResponse({ models: [], total_cost_usd: 0, window_days: 30 }));
    if (url.includes("/top-queries")) return Promise.resolve(makeOkResponse({ queries: [], window_days: 30 }));
    return Promise.resolve({ ok: false, status: 404, json: async () => ({}) } as unknown as Response);
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

import AnalyticsPage from "../page";

beforeEach(() => {
  vi.clearAllMocks();
  localStorageMock.clear();
});

afterEach(() => {
  localStorageMock.clear();
});

describe("Analytics — OrgSwitcher hydration", () => {
  it("selects orgs[0] when localStorage has no stored id", async () => {
    setupFetches(MULTI_ORGS);
    render(<AnalyticsPage />);

    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: "Cambiar organización" })).toBeInTheDocument()
    );

    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select.value).toBe("org-1");
  });

  it("selects the stored org when localStorage has a valid id", async () => {
    localStorage.setItem("tk_selected_org_id", "org-2");
    setupFetches(MULTI_ORGS);
    render(<AnalyticsPage />);

    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: "Cambiar organización" })).toBeInTheDocument()
    );

    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select.value).toBe("org-2");
  });

  it("falls back to orgs[0] when stored id is not in the org list", async () => {
    localStorage.setItem("tk_selected_org_id", "org-invalid");
    setupFetches(MULTI_ORGS);
    render(<AnalyticsPage />);

    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: "Cambiar organización" })).toBeInTheDocument()
    );

    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select.value).toBe("org-1");
  });
});

describe("Analytics — single org hides OrgSwitcher", () => {
  it("does NOT render OrgSwitcher when user has only 1 org", async () => {
    setupFetches(SINGLE_ORG);
    render(<AnalyticsPage />);

    // Wait for the org fetch to complete
    await waitFor(() =>
      expect(mockAuthFetch).toHaveBeenCalledWith(expect.stringContaining("/api/organizations"))
    );

    // Give it extra time to settle
    await new Promise((r) => setTimeout(r, 50));

    expect(screen.queryByRole("combobox", { name: "Cambiar organización" })).toBeNull();
  });
});

describe("Analytics — org switch persistence and refetch", () => {
  it("persists new org to localStorage when user switches org", async () => {
    setupFetches(MULTI_ORGS);
    const user = userEvent.setup();
    render(<AnalyticsPage />);

    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: "Cambiar organización" })).toBeInTheDocument()
    );

    await user.selectOptions(screen.getByRole("combobox"), "org-2");
    expect(localStorage.getItem("tk_selected_org_id")).toBe("org-2");
  });

  it("refetches analytics data after org switch", async () => {
    setupFetches(MULTI_ORGS);
    const user = userEvent.setup();
    render(<AnalyticsPage />);

    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: "Cambiar organización" })).toBeInTheDocument()
    );

    await user.selectOptions(screen.getByRole("combobox"), "org-2");

    await waitFor(() => {
      const org2OverviewCalls = mockAuthFetch.mock.calls.filter((c) =>
        (c[0] as string).includes("org-2") && (c[0] as string).includes("/overview")
      ).length;
      expect(org2OverviewCalls).toBeGreaterThan(0);
    });
  });
});
