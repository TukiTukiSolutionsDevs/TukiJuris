/**
 * Buscar page — search-results export integration tests.
 * AC IDs: FE-EXP-BUSCAR, FE-EXP-TESTS
 *
 * Strategy:
 *  - Renders BuscarPageWrapper (includes the outer Suspense wrapper).
 *  - useAuth / useHasFeature mocked; mockAuthFetch forwards to native fetch → MSW.
 *  - sonner toast mocked for assertion without a DOM Toaster.
 *  - downloadBlob mocked at module level (avoids fragile document.createElement interception).
 *  - server.use() in beforeEach sets up all endpoints the buscar page hits on mount.
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/msw/server";

// ---------------------------------------------------------------------------
// Hoisted mocks
// ---------------------------------------------------------------------------

const {
  mockAuthFetch,
  mockHasFeature,
  mockSearchParamsGet,
  mockSearchParamsGetAll,
  stableSearchParams,
  stableRouter,
} = vi.hoisted(() => {
  const mockSearchParamsGet = vi.fn().mockReturnValue(null);
  const mockSearchParamsGetAll = vi.fn().mockReturnValue([] as string[]);
  // Stable object — same reference across renders so runSearch's useCallback deps
  // don't change every render, preventing the search effect from thrashing.
  const stableSearchParams = {
    get: (key: string) => mockSearchParamsGet(key),
    getAll: (key: string) => mockSearchParamsGetAll(key),
    toString: () => {
      const q = mockSearchParamsGet("q");
      return q ? `q=${encodeURIComponent(q)}` : "";
    },
  };
  const stableRouter = { push: vi.fn(), replace: vi.fn() };
  return {
    mockAuthFetch: vi.fn(),
    mockHasFeature: vi.fn().mockReturnValue(true),
    mockSearchParamsGet,
    mockSearchParamsGetAll,
    stableSearchParams,
    stableRouter,
  };
});

// ---------------------------------------------------------------------------
// Module mocks — must appear before component imports
// ---------------------------------------------------------------------------

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({
    authFetch: mockAuthFetch,
    user: { id: "user-1", email: "test@test.com", isAdmin: false, entitlements: ["pdf_export"] },
    isLoading: false,
  }),
  useHasFeature: (key: string) => mockHasFeature(key),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => stableRouter,
  useSearchParams: () => stableSearchParams,
  usePathname: () => "/buscar",
}));

vi.mock("@/components/AppLayout", () => ({
  AppLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-layout">{children}</div>
  ),
}));

vi.mock("@/components/shell/InternalPageHeader", () => ({
  InternalPageHeader: ({ title }: { title: string }) => (
    <div data-testid="page-header">{title}</div>
  ),
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
  default: ({
    href,
    children,
    className,
  }: {
    href: string;
    children: React.ReactNode;
    className?: string;
  }) => (
    <a href={href} className={className}>
      {children}
    </a>
  ),
}));

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock downloadBlob to avoid document.createElement interception issues
vi.mock("@/lib/export/downloadBlob", () => ({
  downloadBlob: vi.fn(),
  parseContentDispositionFilename: vi.fn(),
}));

// ---------------------------------------------------------------------------
// Import AFTER mocks
// ---------------------------------------------------------------------------

import BuscarPageWrapper from "../page";
import { toast } from "sonner";
import { downloadBlob } from "@/lib/export/downloadBlob";

// ---------------------------------------------------------------------------
// Test data
// ---------------------------------------------------------------------------

const SEARCH_RESULTS = {
  results: [
    {
      id: "res-1",
      document_id: "doc-1",
      title: "Ley de Productividad y Competitividad Laboral",
      document_type: "decreto_supremo",
      document_number: "DS-003-97-TR",
      legal_area: "laboral",
      hierarchy: "legal",
      source: "El Peruano",
      publication_date: "1997-03-27",
      snippet: "Artículo referente al despido arbitrario...",
      score: 0.92,
    },
  ],
  total: 1,
  total_pages: 1,
};

const QUERY = "derecho laboral";

function setupWithQuery() {
  mockSearchParamsGet.mockImplementation((key: string) =>
    key === "q" ? QUERY : null,
  );
  mockSearchParamsGetAll.mockReturnValue([]);
}

function renderPage() {
  return render(<BuscarPageWrapper />);
}

// ---------------------------------------------------------------------------
// Global setup / teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  mockAuthFetch.mockReset();
  mockHasFeature.mockReset();
  mockHasFeature.mockReturnValue(true);
  mockSearchParamsGet.mockReturnValue(null);
  mockSearchParamsGetAll.mockReturnValue([]);
  vi.mocked(downloadBlob).mockClear();
  vi.mocked(toast.success).mockClear();
  vi.mocked(toast.error).mockClear();

  // Forward all authFetch calls to native fetch → MSW intercepts
  mockAuthFetch.mockImplementation((url: string, init?: RequestInit) =>
    fetch(url, init),
  );

  // Default MSW handlers for all endpoints the buscar page hits
  server.use(
    http.get("/api/documents/", () => HttpResponse.json([])),
    http.get("/api/search/saved", () => HttpResponse.json([])),
    http.get("/api/search/history", () => HttpResponse.json([])),
    http.get("/api/search/suggestions", () =>
      HttpResponse.json({ suggestions: [] }),
    ),
    http.post("/api/search/advanced", () =>
      HttpResponse.json(SEARCH_RESULTS),
    ),
    http.get("/api/export/search-results/pdf", () =>
      HttpResponse.arrayBuffer(new ArrayBuffer(8), {
        headers: {
          "Content-Type": "application/pdf",
          "Content-Disposition": `attachment; filename="busqueda-derecho-laboral.pdf"`,
        },
      }),
    ),
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// FE-EXP-BUSCAR-1: Export button hidden when no search results
// ---------------------------------------------------------------------------

describe("FE-EXP-BUSCAR — empty state (no query)", () => {
  it("does not show export button when there are no search results", async () => {
    // No query in URL → browse mode, search never triggered
    renderPage();

    await waitFor(() =>
      expect(screen.getByTestId("page-header")).toBeInTheDocument(),
    );

    expect(
      screen.queryByRole("button", { name: /exportar resultados/i }),
    ).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// FE-EXP-BUSCAR-2: Export button visible after search; GET uses ?q= (not ?query=)
// ---------------------------------------------------------------------------

describe("FE-EXP-BUSCAR — export success", () => {
  it("shows export button after search and calls downloadBlob with correct ?q= param", async () => {
    setupWithQuery();

    let capturedUrl = "";
    server.use(
      http.get("/api/export/search-results/pdf", ({ request }) => {
        capturedUrl = request.url;
        return HttpResponse.arrayBuffer(new ArrayBuffer(8), {
          headers: {
            "Content-Type": "application/pdf",
            "Content-Disposition": `attachment; filename="busqueda-derecho-laboral.pdf"`,
          },
        });
      }),
    );

    renderPage();

    // HighlightedText splits the title across child elements so getByText on the
    // full title string finds nothing (testing-library only checks direct text nodes).
    // "El Peruano" lives in a plain <span> in the metadata row → safe to match.
    await waitFor(() =>
      expect(screen.getByText("El Peruano")).toBeInTheDocument(),
    );

    const exportBtn = await screen.findByRole("button", {
      name: /exportar resultados/i,
    });
    expect(exportBtn).toBeInTheDocument();

    await userEvent.click(exportBtn);

    await waitFor(() => {
      expect(downloadBlob).toHaveBeenCalled();
    });

    // Verify the URL uses ?q= (not ?query=) with correct value
    const url = new URL(capturedUrl, "http://localhost");
    expect(url.searchParams.get("q")).toBe(QUERY);
    expect(url.searchParams.has("query")).toBe(false);

    // Fallback filename is slug of the query
    const [, fallback] = vi.mocked(downloadBlob).mock.calls[0];
    expect(fallback).toContain(".pdf");

    expect(toast.success).toHaveBeenCalledWith("Resultados exportados");
  });
});

// ---------------------------------------------------------------------------
// FE-EXP-BUSCAR-3: Export error shows toast
// ---------------------------------------------------------------------------

describe("FE-EXP-BUSCAR — export error", () => {
  it("shows error toast when backend returns non-OK status", async () => {
    setupWithQuery();

    server.use(
      http.get("/api/export/search-results/pdf", () =>
        new HttpResponse(null, { status: 500 }),
      ),
    );

    renderPage();

    await waitFor(() =>
      expect(screen.getByText("El Peruano")).toBeInTheDocument(),
    );

    const exportBtn = await screen.findByRole("button", {
      name: /exportar resultados/i,
    });
    await userEvent.click(exportBtn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "No se pudo exportar. Intentá nuevamente.",
      );
    });

    expect(downloadBlob).not.toHaveBeenCalled();

    // Button returns to enabled state
    await waitFor(() => {
      const btn = screen.getByRole("button", { name: /exportar resultados/i });
      expect(btn).not.toBeDisabled();
    });
  });
});

// ---------------------------------------------------------------------------
// FE-EXP-BUSCAR-4: Feature gate — UpsellModal shown, no request sent
// ---------------------------------------------------------------------------

describe("FE-EXP-BUSCAR — feature gate", () => {
  it("shows UpsellModal and sends no export request when pdf_export entitlement is missing", async () => {
    setupWithQuery();
    mockHasFeature.mockReturnValue(false);

    let exportCalled = false;
    server.use(
      http.get("/api/export/search-results/pdf", () => {
        exportCalled = true;
        return HttpResponse.arrayBuffer(new ArrayBuffer(8));
      }),
    );

    renderPage();

    await waitFor(() =>
      expect(screen.getByText("El Peruano")).toBeInTheDocument(),
    );

    const exportBtn = await screen.findByRole("button", {
      name: /exportar resultados/i,
    });
    await userEvent.click(exportBtn);

    await waitFor(() =>
      expect(screen.getByText(/función exclusiva/i)).toBeInTheDocument(),
    );

    expect(exportCalled).toBe(false);
    expect(downloadBlob).not.toHaveBeenCalled();
  });
});
