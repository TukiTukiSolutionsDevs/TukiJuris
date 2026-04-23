/**
 * Billing page — OrgSwitcher integration tests.
 * Spec: billing/spec.md — Organization-Scoped Billing
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
  useAuth: () => ({ authFetch: mockAuthFetch }),
}));

vi.mock("@/components/AppLayout", () => ({
  AppLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Stub sub-components that make their own fetches
vi.mock("../_components/TrialRetryBanner", () => ({
  TrialRetryBanner: () => <div data-testid="trial-retry-banner-stub" />,
}));
vi.mock("../_components/InvoiceHistorySection", () => ({
  InvoiceHistorySection: ({ orgId }: { orgId: string }) => (
    <div data-testid={`invoice-history-${orgId}`} />
  ),
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const MULTI_ORGS = [
  { id: "org-1", name: "Alpha Legal" },
  { id: "org-2", name: "Beta Corp" },
];

const SINGLE_ORG = [{ id: "org-1", name: "Alpha Legal" }];

function makeOk(data: unknown) {
  return { ok: true, status: 200, json: async () => data } as unknown as Response;
}

function setupFetches(orgs: { id: string; name: string }[]) {
  mockAuthFetch.mockImplementation((url: string) => {
    if (url.includes("/api/organizations"))      return Promise.resolve(makeOk(orgs));
    if (url.includes("/api/billing/config"))     return Promise.resolve(makeOk({ payments_enabled: false, providers: [] }));
    if (url.includes("/usage"))                  return Promise.resolve(makeOk({ queries_used: 0, queries_limit: 10, period: "week" }));
    if (url.includes("/subscription"))           return Promise.resolve(makeOk({ plan: "free", status: "active" }));
    if (url.includes("/trial"))                  return Promise.resolve({ ok: false, status: 404, json: async () => ({}) } as unknown as Response);
    return Promise.resolve({ ok: false, status: 404, json: async () => ({}) } as unknown as Response);
  });
}

import BillingPage from "../page";

beforeEach(() => {
  vi.clearAllMocks();
  localStorageMock.clear();
});

afterEach(() => {
  localStorageMock.clear();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("Billing — OrgSwitcher visibility", () => {
  it("renders OrgSwitcher when user has multiple orgs", async () => {
    setupFetches(MULTI_ORGS);
    render(<BillingPage />);

    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: "Cambiar organización" })).toBeInTheDocument()
    );
  });

  it("does NOT render OrgSwitcher when user has 1 org", async () => {
    setupFetches(SINGLE_ORG);
    render(<BillingPage />);

    await waitFor(() =>
      expect(mockAuthFetch).toHaveBeenCalledWith(expect.stringContaining("/api/organizations"))
    );
    await new Promise((r) => setTimeout(r, 50));

    expect(screen.queryByRole("combobox", { name: "Cambiar organización" })).toBeNull();
  });
});

describe("Billing — OrgSwitcher hydration", () => {
  it("defaults to orgs[0] when no localStorage value", async () => {
    setupFetches(MULTI_ORGS);
    render(<BillingPage />);

    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: "Cambiar organización" })).toBeInTheDocument()
    );

    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select.value).toBe("org-1");
  });

  it("uses stored org from localStorage when valid", async () => {
    localStorage.setItem("tk_selected_org_id", "org-2");
    setupFetches(MULTI_ORGS);
    render(<BillingPage />);

    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: "Cambiar organización" })).toBeInTheDocument()
    );

    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select.value).toBe("org-2");
  });
});

describe("Billing — OrgSwitcher switch behaviour", () => {
  it("persists new org to localStorage on switch", async () => {
    setupFetches(MULTI_ORGS);
    const user = userEvent.setup();
    render(<BillingPage />);

    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: "Cambiar organización" })).toBeInTheDocument()
    );

    await user.selectOptions(screen.getByRole("combobox"), "org-2");
    expect(localStorage.getItem("tk_selected_org_id")).toBe("org-2");
  });

  it("refetches billing data after org switch", async () => {
    setupFetches(MULTI_ORGS);
    const user = userEvent.setup();
    render(<BillingPage />);

    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: "Cambiar organización" })).toBeInTheDocument()
    );

    await user.selectOptions(screen.getByRole("combobox"), "org-2");

    await waitFor(() => {
      const org2SubCalls = mockAuthFetch.mock.calls.filter((c) =>
        (c[0] as string).includes("org-2") && (c[0] as string).includes("/subscription")
      ).length;
      expect(org2SubCalls).toBeGreaterThan(0);
    });
  });
});
