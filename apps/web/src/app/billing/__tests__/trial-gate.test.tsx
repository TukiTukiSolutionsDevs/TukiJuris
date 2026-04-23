/**
 * Billing page — TrialRetryBanner gate integration tests.
 * Spec: billing/spec.md — Trial Retry Banner
 *
 * Verifies that the page-level condition `trial?.status === "charge_failed"`
 * controls banner visibility when the /api/billing/{orgId}/trial endpoint
 * returns different statuses.
 */
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, beforeAll } from "vitest";
import React from "react";

// ---------------------------------------------------------------------------
// localStorage stub
// ---------------------------------------------------------------------------

const lsStore: Record<string, string> = {};
const localStorageMock: Storage = {
  getItem:    (key: string) => lsStore[key] ?? null,
  setItem:    (key: string, value: string) => { lsStore[key] = value; },
  removeItem: (key: string) => { delete lsStore[key]; },
  clear:      () => { Object.keys(lsStore).forEach((k) => delete lsStore[k]); },
  key:        (index: number) => Object.keys(lsStore)[index] ?? null,
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

// Stub sub-components that make their own fetches — TrialRetryBanner with testid
vi.mock("../_components/TrialRetryBanner", () => ({
  TrialRetryBanner: ({ trialId }: { trialId: string }) => (
    <div data-testid="trial-retry-banner" data-trial-id={trialId} />
  ),
}));

vi.mock("../_components/InvoiceHistorySection", () => ({
  InvoiceHistorySection: ({ orgId }: { orgId: string }) => (
    <div data-testid={`invoice-history-${orgId}`} />
  ),
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const ORG = { id: "org-1", name: "Alpha Legal" };

function makeOk(data: unknown) {
  return { ok: true, status: 200, json: async () => data } as unknown as Response;
}

function makeFail() {
  return { ok: false, status: 404, json: async () => ({}) } as unknown as Response;
}

function setupFetches(trialStatus: string | null) {
  mockAuthFetch.mockImplementation((url: string) => {
    if (url.includes("/api/organizations"))  return Promise.resolve(makeOk([ORG]));
    if (url.includes("/api/billing/config")) return Promise.resolve(makeOk({ payments_enabled: false, providers: [] }));
    if (url.includes("/usage"))              return Promise.resolve(makeOk({ queries_used: 0, queries_limit: 10, period: "week" }));
    if (url.includes("/subscription"))       return Promise.resolve(makeOk({ plan: "free", status: "active" }));
    if (url.includes("/trial")) {
      return trialStatus
        ? Promise.resolve(makeOk({ id: "trial-1", status: trialStatus }))
        : Promise.resolve(makeFail());
    }
    return Promise.resolve(makeFail());
  });
}

import BillingPage from "../page";

beforeEach(() => {
  vi.clearAllMocks();
  localStorageMock.clear();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("Billing — TrialRetryBanner page-level gate", () => {
  it("renders TrialRetryBanner when trial.status === 'charge_failed'", async () => {
    setupFetches("charge_failed");
    render(<BillingPage />);

    await waitFor(() =>
      expect(screen.getByTestId("trial-retry-banner")).toBeInTheDocument()
    );
  });

  it("does NOT render TrialRetryBanner when trial.status !== 'charge_failed'", async () => {
    setupFetches("active");
    render(<BillingPage />);

    // Wait until billing data has loaded (subscription is fetched)
    await waitFor(() =>
      expect(mockAuthFetch).toHaveBeenCalledWith(
        expect.stringContaining("/subscription")
      )
    );
    // Allow async state updates to settle
    await new Promise((r) => setTimeout(r, 50));

    expect(screen.queryByTestId("trial-retry-banner")).toBeNull();
  });
});
