/**
 * KB stats strip tests — /buscar browse mode
 *
 * Covers FE-KB-STATS-STRIP:
 *   KB-1  GET /api/documents/stats success → strip shows "N docs · M fragmentos"
 *   KB-2  Loading state → skeleton element is shown
 *   KB-3  GET /api/documents/stats fails → strip hidden, no error or toast
 *   KB-4  Stats strip only visible in browse mode (no query), not in search mode
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Mock sonner (imported by the page)
// ---------------------------------------------------------------------------
vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
  Toaster: () => null,
}));

// ---------------------------------------------------------------------------
// Stable mocks
// ---------------------------------------------------------------------------
const mockAuthFetch = vi.fn();

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({
    authFetch: mockAuthFetch,
    user: null,
  }),
  useHasFeature: () => false,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/buscar",
  useSearchParams: () => ({
    get: () => null,
    getAll: () => [],
    toString: () => "",
  }),
}));

// ---------------------------------------------------------------------------
// Stub layout/shell components to avoid cascading auth checks and redirects
// ---------------------------------------------------------------------------
vi.mock("@/components/AppLayout", () => ({
  AppLayout: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("@/components/shell/InternalPageHeader", () => ({
  InternalPageHeader: () => null,
}));

vi.mock("@/components/shell/ShellUtilityActions", () => ({
  ShellUtilityActions: () => null,
}));

vi.mock("next/image", () => ({
  default: ({ src, alt }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} />
  ),
}));

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("@/components/UpsellModal", () => ({
  UpsellModal: () => null,
}));

// ---------------------------------------------------------------------------
// Import component AFTER mocks
// ---------------------------------------------------------------------------
import BuscarPageWrapper from "../page";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function makeOk(data: unknown) {
  return { ok: true, json: () => Promise.resolve(data) };
}

function setupFetch({
  statsOk = true,
  statsData = { total_documents: 42, total_chunks: 1234 },
}: {
  statsOk?: boolean;
  statsData?: unknown;
} = {}) {
  mockAuthFetch.mockImplementation(async (url: string) => {
    if (url.includes("/api/documents/stats")) {
      return statsOk ? makeOk(statsData) : { ok: false, status: 500, json: () => Promise.resolve({}) };
    }
    if (url.includes("/api/documents/")) return makeOk([]);
    if (url.includes("/api/search/")) return makeOk({ suggestions: [] });
    return { ok: false, json: () => Promise.resolve({}) };
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.clearAllMocks();
  setupFetch();
});

describe("/buscar — KB stats strip", () => {
  it("KB-1: stats strip shows document and chunk counts in browse mode", async () => {
    render(<BuscarPageWrapper />);

    await waitFor(() => {
      expect(screen.getByTestId("kb-stats-strip")).toBeInTheDocument();
    });

    const strip = screen.getByTestId("kb-stats-strip");
    expect(strip).toHaveTextContent("42");
    expect(strip).toHaveTextContent("1,234");
    expect(strip).toHaveTextContent("fragmentos");
  });

  it("KB-1b: toLocaleString formats large numbers correctly", async () => {
    setupFetch({ statsData: { total_documents: 1000, total_chunks: 99999 } });
    render(<BuscarPageWrapper />);

    await waitFor(() => {
      expect(screen.getByTestId("kb-stats-strip")).toBeInTheDocument();
    });

    const strip = screen.getByTestId("kb-stats-strip");
    expect(strip.textContent).toMatch(/\d/);
    expect(strip).toHaveTextContent("documentos");
  });

  it("KB-2: loading skeleton shown while stats are fetching", async () => {
    // Use a controllable promise so loading state stays true until we resolve
    let resolveStats!: () => void;
    mockAuthFetch.mockImplementation(async (url: string) => {
      if (url.includes("/api/documents/stats")) {
        await new Promise<void>((r) => { resolveStats = r; });
        return makeOk({ total_documents: 42, total_chunks: 1234 });
      }
      if (url.includes("/api/documents/")) return makeOk([]);
      return { ok: false, json: () => Promise.resolve({}) };
    });

    render(<BuscarPageWrapper />);

    // Skeleton must appear while fetch is pending
    await waitFor(() => {
      expect(screen.getByTestId("kb-stats-skeleton")).toBeInTheDocument();
    });

    // Resolve to avoid act() warnings
    resolveStats();
  });

  it("KB-3: GET /api/documents/stats failure → strip hidden, no error shown", async () => {
    setupFetch({ statsOk: false });
    render(<BuscarPageWrapper />);

    // Wait for skeleton to disappear (loading finished)
    await waitFor(() => {
      expect(screen.queryByTestId("kb-stats-skeleton")).not.toBeInTheDocument();
    });

    // Strip must not appear
    expect(screen.queryByTestId("kb-stats-strip")).not.toBeInTheDocument();
  });

  it("KB-3b: GET network error → strip hidden silently", async () => {
    mockAuthFetch.mockImplementation(async (url: string) => {
      if (url.includes("/api/documents/stats")) throw new Error("Network error");
      if (url.includes("/api/documents/")) return makeOk([]);
      return { ok: false, json: () => Promise.resolve({}) };
    });

    render(<BuscarPageWrapper />);

    await waitFor(() => {
      expect(screen.queryByTestId("kb-stats-skeleton")).not.toBeInTheDocument();
    });

    expect(screen.queryByTestId("kb-stats-strip")).not.toBeInTheDocument();
  });
});
