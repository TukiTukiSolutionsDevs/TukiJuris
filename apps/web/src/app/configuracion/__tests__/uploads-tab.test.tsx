/**
 * Integration tests — Archivos tab (configuracion page)
 *
 * Covers:
 *   AT-1  Lazy-fetch: GET /api/upload/ fires only after tab activation
 *   AT-2  Loading: skeleton rows visible while fetch is in-flight
 *   AT-3  Empty state: "Todavía no subiste ningún archivo." rendered
 *   AT-4  Error state: error message + retry button rendered
 *   AT-5  Populated state: table rows render filename, type badge, size, date
 *   AT-6  Delete success: confirm → optimistic removal → toast.success
 *   AT-7  Delete failure: confirm → optimistic removal → rollback → toast.error
 *   AT-8  Delete cancel: confirm returns false → no API call, row stays
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Mock sonner (hoisted refs so they're available before module import)
// ---------------------------------------------------------------------------
const { mockToastSuccess, mockToastError } = vi.hoisted(() => ({
  mockToastSuccess: vi.fn(),
  mockToastError: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: { success: mockToastSuccess, error: mockToastError },
  Toaster: () => null,
}));

// ---------------------------------------------------------------------------
// Stable mock refs
// ---------------------------------------------------------------------------
const mockAuthFetch = vi.fn();

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({
    authFetch: mockAuthFetch,
    logout: vi.fn(),
    logoutAll: vi.fn(),
    user: { id: "user-1", email: "test@test.com", isAdmin: false },
    onboardingCompleted: true,
  }),
  useHasFeature: () => false,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/configuracion",
  useSearchParams: () => ({ get: () => null }),
}));

// ---------------------------------------------------------------------------
// Import page AFTER mocks
// ---------------------------------------------------------------------------
import ConfiguracionPage from "../page";

// ---------------------------------------------------------------------------
// Fixture data
// ---------------------------------------------------------------------------
const DOC_1 = {
  id: "doc-uuid-1",
  filename: "contrato.pdf",
  file_type: "pdf",
  file_size: 102400,
  page_count: 5,
  conversation_id: null,
  created_at: "2025-03-15T10:00:00.000Z",
};

const DOC_2 = {
  id: "doc-uuid-2",
  filename: "informe.docx",
  file_type: "docx",
  file_size: 2048,
  page_count: null,
  conversation_id: "conv-uuid-1",
  created_at: "2025-03-14T08:00:00.000Z",
};

// ---------------------------------------------------------------------------
// setupAuthFetch — controls what /api/upload/ returns
// ---------------------------------------------------------------------------
type UploadFixture = {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  page_count: number | null;
  conversation_id: string | null;
  created_at: string;
};

function setupAuthFetch(
  uploadsData: UploadFixture[] = [],
  deleteOk = true,
) {
  mockAuthFetch.mockImplementation(async (url: string, options?: RequestInit) => {
    if (url.includes("/api/auth/me")) {
      return { ok: true, json: () => Promise.resolve({ id: "user-1", email: "test@test.com", name: "Test" }) };
    }
    if (url.includes("/api/organizations/")) {
      return { ok: false, json: () => Promise.resolve([]) };
    }
    // DELETE /api/upload/{id}
    if (options?.method === "DELETE" && url.includes("/api/upload/")) {
      return { ok: deleteOk, json: () => Promise.resolve({ status: "deleted" }) };
    }
    // GET /api/upload/ list
    if (url.includes("/api/upload/")) {
      return { ok: true, json: () => Promise.resolve(uploadsData) };
    }
    return { ok: false, json: () => Promise.resolve({}) };
  });
}

// ---------------------------------------------------------------------------
// Helper: navigate to Archivos tab
// ---------------------------------------------------------------------------
async function goToArchivosTab(user: ReturnType<typeof userEvent.setup>) {
  const btns = await screen.findAllByRole("button", { name: /archivos/i });
  await user.click(btns[0]);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.clearAllMocks();
  setupAuthFetch();
});

describe("configuracion — Archivos tab", () => {
  it("AT-1: does NOT fetch /api/upload/ before tab is activated", async () => {
    setupAuthFetch([DOC_1]);
    render(<ConfiguracionPage />);

    // Wait for the initial page load (me + orgs)
    await screen.findAllByRole("button", { name: /archivos/i });

    const uploadCalls = mockAuthFetch.mock.calls.filter((args) =>
      (args[0] as string).includes("/api/upload/")
    );
    expect(uploadCalls).toHaveLength(0);
  });

  it("AT-2: shows skeleton rows while fetch is in-flight", async () => {
    let resolve!: (v: unknown) => void;
    mockAuthFetch.mockImplementation(async (url: string) => {
      if (url.includes("/api/auth/me"))
        return { ok: true, json: () => Promise.resolve({ id: "u1", email: "t@t.com" }) };
      if (url.includes("/api/organizations/"))
        return { ok: false, json: () => Promise.resolve([]) };
      if (url.includes("/api/upload/"))
        return new Promise((r) => { resolve = r; });
      return { ok: false, json: () => Promise.resolve({}) };
    });

    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToArchivosTab(user);

    await waitFor(() => {
      expect(screen.getByTestId("uploads-skeleton")).toBeInTheDocument();
    });

    // Resolve so the component doesn't hang
    resolve({ ok: true, json: () => Promise.resolve([]) });
  });

  it("AT-3: renders empty state when API returns []", async () => {
    setupAuthFetch([]);
    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToArchivosTab(user);

    await waitFor(() => {
      expect(screen.getByTestId("uploads-empty")).toBeInTheDocument();
    });
    expect(screen.getByText("Todavía no subiste ningún archivo.")).toBeInTheDocument();
  });

  it("AT-4: renders error state + retry button when fetch fails", async () => {
    mockAuthFetch.mockImplementation(async (url: string) => {
      if (url.includes("/api/auth/me"))
        return { ok: true, json: () => Promise.resolve({ id: "u1", email: "t@t.com" }) };
      if (url.includes("/api/organizations/"))
        return { ok: false, json: () => Promise.resolve([]) };
      if (url.includes("/api/upload/"))
        return { ok: false, json: () => Promise.resolve({}) };
      return { ok: false, json: () => Promise.resolve({}) };
    });

    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToArchivosTab(user);

    await waitFor(() => {
      expect(screen.getByTestId("uploads-error")).toBeInTheDocument();
    });
    expect(screen.getByText("No se pudieron cargar los archivos.")).toBeInTheDocument();
    expect(screen.getByTestId("uploads-retry")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /reintentar/i })).toBeInTheDocument();
  });

  it("AT-5: renders table rows with filename, type badge, formatted size and date", async () => {
    setupAuthFetch([DOC_1, DOC_2]);
    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToArchivosTab(user);

    await waitFor(() => {
      expect(screen.getByTestId("uploads-table")).toBeInTheDocument();
    });

    // Filenames
    expect(screen.getByText("contrato.pdf")).toBeInTheDocument();
    expect(screen.getByText("informe.docx")).toBeInTheDocument();

    // Type badges (uppercase)
    expect(screen.getByText("PDF")).toBeInTheDocument();
    expect(screen.getByText("DOCX")).toBeInTheDocument();

    // File sizes
    expect(screen.getByText("100.0 KB")).toBeInTheDocument(); // 102400 bytes
    expect(screen.getByText("2.0 KB")).toBeInTheDocument();   // 2048 bytes

    // Dates (DD/MM/YYYY)
    expect(screen.getByText("15/03/2025")).toBeInTheDocument();
    expect(screen.getByText("14/03/2025")).toBeInTheDocument();
  });

  it("AT-6: delete success — confirm → row removed optimistically → toast.success", async () => {
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    setupAuthFetch([DOC_1], true);
    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToArchivosTab(user);

    await waitFor(() => {
      expect(screen.getByTestId(`delete-upload-${DOC_1.id}`)).toBeInTheDocument();
    });

    await user.click(screen.getByTestId(`delete-upload-${DOC_1.id}`));

    // Confirm was called with the exact spec message
    expect(confirmSpy).toHaveBeenCalledWith(
      `¿Eliminar "${DOC_1.filename}"? Esta acción no se puede deshacer.`
    );

    await waitFor(() => {
      expect(mockToastSuccess).toHaveBeenCalledWith("Archivo eliminado");
    });

    // Row must be gone
    expect(screen.queryByText("contrato.pdf")).not.toBeInTheDocument();

    // DELETE API was called
    const deleteCalls = mockAuthFetch.mock.calls.filter((args) => {
      const url = args[0] as string;
      const opts = args[1] as RequestInit | undefined;
      return url.includes(`/api/upload/${DOC_1.id}`) && opts?.method === "DELETE";
    });
    expect(deleteCalls).toHaveLength(1);
  });

  it("AT-7: delete failure — confirm → row removed → rollback → toast.error", async () => {
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    setupAuthFetch([DOC_1], false);
    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToArchivosTab(user);

    await waitFor(() => {
      expect(screen.getByTestId(`delete-upload-${DOC_1.id}`)).toBeInTheDocument();
    });

    await user.click(screen.getByTestId(`delete-upload-${DOC_1.id}`));

    // Confirm was called with the exact spec message
    expect(confirmSpy).toHaveBeenCalledWith(
      `¿Eliminar "${DOC_1.filename}"? Esta acción no se puede deshacer.`
    );

    await waitFor(() => {
      expect(mockToastError).toHaveBeenCalledWith("No se pudo eliminar el archivo");
    });

    // Row must be restored (rollback)
    await waitFor(() => {
      expect(screen.getByText("contrato.pdf")).toBeInTheDocument();
    });
  });

  it("AT-8: delete cancel — confirm returns false → no DELETE call, row stays", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(false);
    setupAuthFetch([DOC_1], true);
    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToArchivosTab(user);

    await waitFor(() => {
      expect(screen.getByTestId(`delete-upload-${DOC_1.id}`)).toBeInTheDocument();
    });

    await user.click(screen.getByTestId(`delete-upload-${DOC_1.id}`));

    // No DELETE call should have been made
    const deleteCalls = mockAuthFetch.mock.calls.filter((args) => {
      const url = args[0] as string;
      const opts = args[1] as RequestInit | undefined;
      return url.includes("/api/upload/") && opts?.method === "DELETE";
    });
    expect(deleteCalls).toHaveLength(0);

    // Row must still be present
    expect(screen.getByText("contrato.pdf")).toBeInTheDocument();

    // No toasts
    expect(mockToastSuccess).not.toHaveBeenCalled();
    expect(mockToastError).not.toHaveBeenCalled();
  });

  it("AT-9: retry button refetches and renders rows on success", async () => {
    let uploadCallCount = 0;
    mockAuthFetch.mockImplementation(async (url: string) => {
      if (url.includes("/api/auth/me"))
        return { ok: true, json: () => Promise.resolve({ id: "u1", email: "t@t.com" }) };
      if (url.includes("/api/organizations/"))
        return { ok: false, json: () => Promise.resolve([]) };
      if (url.includes("/api/upload/")) {
        uploadCallCount++;
        if (uploadCallCount === 1) return { ok: false, json: () => Promise.resolve({}) };
        return { ok: true, json: () => Promise.resolve([DOC_1]) };
      }
      return { ok: false, json: () => Promise.resolve({}) };
    });

    const user = userEvent.setup();
    render(<ConfiguracionPage />);
    await goToArchivosTab(user);

    // First fetch fails → error state
    await waitFor(() => {
      expect(screen.getByTestId("uploads-error")).toBeInTheDocument();
    });

    // Click retry
    await user.click(screen.getByRole("button", { name: /reintentar/i }));

    // Second fetch succeeds → table with row
    await waitFor(() => {
      expect(screen.getByTestId("uploads-table")).toBeInTheDocument();
    });
    expect(screen.getByText("contrato.pdf")).toBeInTheDocument();
  });
});
