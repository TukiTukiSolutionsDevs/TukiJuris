/**
 * Historial page — folder rename integration tests
 * AC coverage: FE-FOLDER-RENAME-UI:4,5,6 | VALIDATION:2 | NETWORK:1-5 | TESTS:1-4
 *
 * Strategy:
 *  - useAuth mocked; mockAuthFetch forwards to native fetch → MSW intercepts.
 *  - AppLayout, InternalPageHeader, ShellUtilityActions, next/navigation, next/image mocked.
 *  - server.use() in beforeEach sets default handlers for conversations, tags, folders, PUT.
 *  - Per-test server.use() overrides for specific rename responses.
 *  - <Toaster /> included in render so toast assertions work via getByText.
 *  - Global setup.ts handles server.listen() / resetHandlers() / close().
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { Toaster } from "sonner";
import { server } from "@/test/msw/server";

// ---------------------------------------------------------------------------
// Stable mock refs (hoisted so vi.mock factories can reference them)
// ---------------------------------------------------------------------------

const { mockAuthFetch } = vi.hoisted(() => ({
  mockAuthFetch: vi.fn(),
}));

// ---------------------------------------------------------------------------
// Module mocks — must appear before component import
// ---------------------------------------------------------------------------

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({
    authFetch: mockAuthFetch,
    user: { id: "user-1", email: "test@test.com", isAdmin: false },
    logout: vi.fn(),
    isLoading: false,
  }),
}));

vi.mock("@/components/AppLayout", () => ({
  AppLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-layout">{children}</div>
  ),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/historial",
}));

vi.mock("next/image", () => ({
  default: ({ src, alt }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} />
  ),
}));

vi.mock("@/components/shell/InternalPageHeader", () => ({
  InternalPageHeader: () => <div data-testid="page-header" />,
}));

vi.mock("@/components/shell/ShellUtilityActions", () => ({
  ShellUtilityActions: () => <div />,
}));

// ---------------------------------------------------------------------------
// Import page AFTER mocks
// ---------------------------------------------------------------------------

import HistorialPage from "../page";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const FOLDER_1 = {
  id: "f1",
  name: "Derecho Civil",
  icon: "folder",
  position: 0,
  conversation_count: 2,
};

const FOLDER_2 = {
  id: "f2",
  name: "Derecho Laboral",
  icon: "folder",
  position: 1,
  conversation_count: 1,
};

// ---------------------------------------------------------------------------
// Render helper — includes Toaster so toast assertions work
// ---------------------------------------------------------------------------

function renderPage() {
  return render(
    <>
      <HistorialPage />
      <Toaster />
    </>
  );
}

// ---------------------------------------------------------------------------
// Global setup / teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  mockAuthFetch.mockReset();
  mockAuthFetch.mockImplementation((url: string, init?: RequestInit) =>
    fetch(url, init)
  );

  server.use(
    http.get("/api/conversations/", () => HttpResponse.json([])),
    http.get("/api/tags/", () => HttpResponse.json([])),
    http.get("/api/folders/", () => HttpResponse.json([FOLDER_1])),
    http.put("/api/folders/:id", () => new HttpResponse(null, { status: 200 })),
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// Helper: wait for folder to load and click the rename button
// ---------------------------------------------------------------------------

async function openRenameInput(user: ReturnType<typeof userEvent.setup>) {
  await waitFor(() =>
    expect(screen.getByText("Derecho Civil")).toBeInTheDocument()
  );
  await user.click(screen.getByRole("button", { name: "Renombrar" }));
  return screen.findByRole("textbox", { name: "Renombrar carpeta" });
}

// ---------------------------------------------------------------------------
// Test 1: Happy path — Enter commits, server 200, toast success, name updated
// FE-FOLDER-RENAME-UI:4 | NETWORK:1-3 | TESTS:2-4
// ---------------------------------------------------------------------------

describe("folder rename — Enter commits (happy path)", () => {
  it("Enter commits → server 200 → toast success → name updated in sidebar", async () => {
    const user = userEvent.setup();
    renderPage();

    const input = await openRenameInput(user);

    await user.clear(input);
    await user.type(input, "Derecho Penal");
    await user.keyboard("{Enter}");

    await waitFor(() =>
      expect(screen.getByText("Carpeta renombrada")).toBeInTheDocument()
    );
    await waitFor(() => {
      expect(screen.getByText("Derecho Penal")).toBeInTheDocument();
      expect(screen.queryByText("Derecho Civil")).not.toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// Test 2: Blur commits rename — server 200 → toast success
// FE-FOLDER-RENAME-UI:6 | NETWORK:1-3 | TESTS:2-4
// ---------------------------------------------------------------------------

describe("folder rename — blur commits", () => {
  it("blur triggers same commit path → server 200 → toast success", async () => {
    const user = userEvent.setup();
    renderPage();

    const input = await openRenameInput(user);

    await user.clear(input);
    await user.type(input, "Nuevo Nombre");
    await user.tab(); // moves focus away → blur fires

    await waitFor(() =>
      expect(screen.getByText("Carpeta renombrada")).toBeInTheDocument()
    );
    await waitFor(() =>
      expect(screen.getByText("Nuevo Nombre")).toBeInTheDocument()
    );
  });
});

// ---------------------------------------------------------------------------
// Test 3: 409 conflict → error toast, name reverted
// FE-FOLDER-RENAME-NETWORK:4 | TESTS:2-4
// ---------------------------------------------------------------------------

describe("folder rename — 409 conflict", () => {
  it("409 → error toast 'Ya existe...' → name reverted to original", async () => {
    server.use(
      http.put("/api/folders/:id", () =>
        new HttpResponse(null, { status: 409 })
      )
    );

    const user = userEvent.setup();
    renderPage();

    const input = await openRenameInput(user);

    await user.clear(input);
    await user.type(input, "Nombre Duplicado");
    await user.keyboard("{Enter}");

    await waitFor(() =>
      expect(
        screen.getByText("Ya existe una carpeta con ese nombre")
      ).toBeInTheDocument()
    );
    await waitFor(() =>
      expect(screen.getByText("Derecho Civil")).toBeInTheDocument()
    );
  });
});

// ---------------------------------------------------------------------------
// Test 4: Generic error (500) → error toast, name reverted
// FE-FOLDER-RENAME-NETWORK:5 | TESTS:2-4
// ---------------------------------------------------------------------------

describe("folder rename — generic server error", () => {
  it("500 → error toast 'No se pudo...' → name reverted to original", async () => {
    server.use(
      http.put("/api/folders/:id", () =>
        new HttpResponse(null, { status: 500 })
      )
    );

    const user = userEvent.setup();
    renderPage();

    const input = await openRenameInput(user);

    await user.clear(input);
    await user.type(input, "Error Name");
    await user.keyboard("{Enter}");

    await waitFor(() =>
      expect(
        screen.getByText("No se pudo renombrar la carpeta")
      ).toBeInTheDocument()
    );
    await waitFor(() =>
      expect(screen.getByText("Derecho Civil")).toBeInTheDocument()
    );
  });
});

// ---------------------------------------------------------------------------
// Test 5: Escape cancels — no network call, name unchanged
// FE-FOLDER-RENAME-UI:5 | TESTS:2-4
// ---------------------------------------------------------------------------

describe("folder rename — Escape cancels", () => {
  it("Escape exits edit mode without firing PUT, name unchanged", async () => {
    let putCalled = false;
    server.use(
      http.put("/api/folders/:id", () => {
        putCalled = true;
        return new HttpResponse(null, { status: 200 });
      })
    );

    const user = userEvent.setup();
    renderPage();

    const input = await openRenameInput(user);

    await user.clear(input);
    await user.type(input, "Nuevo Nombre");
    await user.keyboard("{Escape}");

    await waitFor(() => {
      expect(
        screen.queryByRole("textbox", { name: "Renombrar carpeta" })
      ).not.toBeInTheDocument();
      expect(screen.getByText("Derecho Civil")).toBeInTheDocument();
    });

    expect(putCalled).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Test 6: Empty/whitespace input → no network call, edit cancelled
// FE-FOLDER-RENAME-VALIDATION:2 | TESTS:2-4
// ---------------------------------------------------------------------------

describe("folder rename — empty input validation", () => {
  it("clearing input and pressing Enter cancels without firing PUT", async () => {
    let putCalled = false;
    server.use(
      http.put("/api/folders/:id", () => {
        putCalled = true;
        return new HttpResponse(null, { status: 200 });
      })
    );

    const user = userEvent.setup();
    renderPage();

    const input = await openRenameInput(user);

    await user.clear(input);
    // input value is now empty
    await user.keyboard("{Enter}");

    await waitFor(() => {
      expect(
        screen.queryByRole("textbox", { name: "Renombrar carpeta" })
      ).not.toBeInTheDocument();
    });

    expect(putCalled).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Test 7: Cross-folder switch → cancel current edit, open new edit, no PUT
// FE-FOLDER-RENAME-UI:8 | TESTS:2-4
// ---------------------------------------------------------------------------

describe("folder rename — cross-folder pencil switch", () => {
  it("clicking another folder's pencil cancels current edit without firing PUT", async () => {
    // Override GET to return two folders
    server.use(
      http.get("/api/folders/", () =>
        HttpResponse.json([FOLDER_1, FOLDER_2])
      )
    );

    let putCalled = false;
    server.use(
      http.put("/api/folders/:id", () => {
        putCalled = true;
        return new HttpResponse(null, { status: 200 });
      })
    );

    const user = userEvent.setup();
    renderPage();

    // Wait for both folders to load
    await waitFor(() => {
      expect(screen.getByText("Derecho Civil")).toBeInTheDocument();
      expect(screen.getByText("Derecho Laboral")).toBeInTheDocument();
    });

    // Click folder A (FOLDER_1) rename pencil — both pencils are in DOM
    const pencils = screen.getAllByRole("button", { name: "Renombrar" });
    await user.click(pencils[0]); // folder A enters edit mode

    // Type a new name but do NOT commit
    const inputA = await screen.findByRole("textbox", { name: "Renombrar carpeta" });
    await user.clear(inputA);
    await user.type(inputA, "Nombre Sin Guardar");

    // Folder A is editing → only folder B's pencil remains in DOM
    const folderBPencil = screen.getByRole("button", { name: "Renombrar" });

    // Click folder B's pencil — should cancel A (blur guard) and open B
    await user.click(folderBPencil);

    // Folder A name must still be the original (no optimistic update was applied)
    await waitFor(() => {
      expect(screen.getByText("Derecho Civil")).toBeInTheDocument();
    });

    // Folder B's input must now be active
    await waitFor(() => {
      expect(
        screen.getByRole("textbox", { name: "Renombrar carpeta" })
      ).toBeInTheDocument();
    });

    // No PUT was issued for folder A
    expect(putCalled).toBe(false);
  });
});
