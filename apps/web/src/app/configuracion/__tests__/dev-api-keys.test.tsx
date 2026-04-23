/**
 * Integration tests for DevApiKeysSection
 *
 * Covers:
 *  - AC1.1–AC1.5: List states (populated, empty, loading) + revoke success/failure
 *  - AC2.1–AC2.5: Create form (success, 422, server error)
 *  - AC3.1–AC3.5: Show-once modal (appears, copy, close refetches list)
 *  - AC6.2: MSW-backed scenarios
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/msw/server";

// ---------------------------------------------------------------------------
// Clipboard — userEvent.setup() installs a stub on navigator.clipboard;
// spy on it INSIDE the test that needs it (after setup() has been called).
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockAuthFetch = vi.fn();

vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({ authFetch: mockAuthFetch }),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

// ---------------------------------------------------------------------------
// Import after mocks
// ---------------------------------------------------------------------------

import { DevApiKeysSection } from "@/components/configuracion/DevApiKeysSection";
import { toast } from "sonner";

// ---------------------------------------------------------------------------
// Test data
// ---------------------------------------------------------------------------

const ACTIVE_KEY = {
  id: "key-1",
  name: "Mi integración",
  prefix: "tk_live_abc12",
  scopes: ["read", "write"],
  created_at: "2026-01-15T10:00:00Z",
  expires_at: null,
  status: "active",
};

const REVOKED_KEY = {
  id: "key-2",
  name: "Antigua clave",
  prefix: "tk_live_xyz99",
  scopes: ["read"],
  created_at: "2025-12-01T08:00:00Z",
  expires_at: "2026-03-01T00:00:00Z",
  status: "revoked",
};

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

beforeEach(() => {
  mockAuthFetch
    .mockReset()
    .mockImplementation((url: string, init?: RequestInit) => fetch(url, init));

  server.use(http.get("/api/keys", () => HttpResponse.json([])));

  vi.mocked(toast.success).mockReset();
  vi.mocked(toast.error).mockReset();
});

// ---------------------------------------------------------------------------
// AC1 — List states
// ---------------------------------------------------------------------------

describe("DevApiKeysSection — list", () => {
  it("renders the table when keys exist", async () => {
    server.use(
      http.get("/api/keys", () => HttpResponse.json([ACTIVE_KEY, REVOKED_KEY])),
    );
    render(<DevApiKeysSection />);

    await waitFor(() => {
      expect(screen.getByTestId("dev-keys-table")).toBeInTheDocument();
    });
    expect(screen.getByText("Mi integración")).toBeInTheDocument();
    expect(screen.getByText("Antigua clave")).toBeInTheDocument();
  });

  it("renders empty state when no keys exist", async () => {
    render(<DevApiKeysSection />);

    await waitFor(() => {
      expect(screen.getByTestId("dev-keys-empty")).toBeInTheDocument();
    });
  });

  it("renders loading state initially", () => {
    server.use(
      http.get("/api/keys", async () => {
        await new Promise((r) => setTimeout(r, 300));
        return HttpResponse.json([]);
      }),
    );
    render(<DevApiKeysSection />);
    expect(screen.getByTestId("dev-keys-loading")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// AC1.4–AC1.5 — Revoke
// ---------------------------------------------------------------------------

describe("DevApiKeysSection — revoke", () => {
  beforeEach(() => {
    server.use(http.get("/api/keys", () => HttpResponse.json([ACTIVE_KEY])));
    vi.spyOn(window, "confirm").mockReturnValue(true);
  });

  it("shows success toast and refetches on revoke success", async () => {
    const user = userEvent.setup();
    server.use(
      http.delete("/api/keys/:id", () => new HttpResponse(null, { status: 204 })),
    );

    render(<DevApiKeysSection />);

    const revokeBtn = await screen.findByTestId("revoke-btn-key-1");
    await user.click(revokeBtn);

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith("Clave revocada");
    });
  });

  it("shows error toast on revoke failure", async () => {
    const user = userEvent.setup();
    server.use(
      http.delete("/api/keys/:id", () =>
        HttpResponse.json({ detail: "No autorizado" }, { status: 403 }),
      ),
    );

    render(<DevApiKeysSection />);

    const revokeBtn = await screen.findByTestId("revoke-btn-key-1");
    await user.click(revokeBtn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("No autorizado");
    });
  });
});

// ---------------------------------------------------------------------------
// AC2 — Create
// ---------------------------------------------------------------------------

describe("DevApiKeysSection — create", () => {
  it("opens the create form on button click", async () => {
    const user = userEvent.setup();
    render(<DevApiKeysSection />);

    await screen.findByTestId("dev-keys-empty");
    await user.click(screen.getByTestId("create-dev-key-btn"));

    expect(screen.getByTestId("create-dev-key-form")).toBeInTheDocument();
  });

  it("shows CopyOnceModal with full_key on create success", async () => {
    const user = userEvent.setup();
    server.use(
      http.post("/api/keys", () =>
        HttpResponse.json({
          ...ACTIVE_KEY,
          full_key: "tk_live_supersecret_abc123xyz",
        }),
      ),
    );

    render(<DevApiKeysSection />);

    await screen.findByTestId("dev-keys-empty");
    await user.click(screen.getByTestId("create-dev-key-btn"));
    await user.type(screen.getByTestId("create-name-input"), "Mi nueva clave");
    await user.click(screen.getByTestId("create-submit-btn"));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(screen.getByTestId("copy-once-secret")).toHaveTextContent(
      "tk_live_supersecret_abc123xyz",
    );
  });

  it("copies the full_key when copy button is clicked in the modal", async () => {
    const user = userEvent.setup();
    // userEvent.setup() installs the clipboard stub; spy on writeText now
    const writeTextSpy = vi.spyOn(navigator.clipboard, "writeText");

    server.use(
      http.post("/api/keys", () =>
        HttpResponse.json({ ...ACTIVE_KEY, full_key: "tk_live_copy_test" }),
      ),
    );

    render(<DevApiKeysSection />);

    await screen.findByTestId("dev-keys-empty");
    await user.click(screen.getByTestId("create-dev-key-btn"));
    await user.type(screen.getByTestId("create-name-input"), "Clave copia");
    await user.click(screen.getByTestId("create-submit-btn"));

    await screen.findByRole("dialog");
    await user.click(screen.getByTestId("copy-once-copy-btn"));

    expect(writeTextSpy).toHaveBeenCalledWith("tk_live_copy_test");
  });

  it("shows inline 422 validation error", async () => {
    const user = userEvent.setup();
    server.use(
      http.post("/api/keys", () =>
        HttpResponse.json({ detail: "El nombre ya existe" }, { status: 422 }),
      ),
    );

    render(<DevApiKeysSection />);

    await screen.findByTestId("dev-keys-empty");
    await user.click(screen.getByTestId("create-dev-key-btn"));
    await user.type(screen.getByTestId("create-name-input"), "Duplicada");
    await user.click(screen.getByTestId("create-submit-btn"));

    await waitFor(() => {
      expect(screen.getByTestId("create-error-msg")).toHaveTextContent(
        "El nombre ya existe",
      );
    });
  });

  it("shows field-level 422 error next to the name input when detail is an array", async () => {
    const user = userEvent.setup();
    server.use(
      http.post("/api/keys", () =>
        HttpResponse.json(
          {
            detail: [
              {
                loc: ["body", "name"],
                msg: "El nombre ya existe",
                type: "value_error",
              },
            ],
          },
          { status: 422 },
        ),
      ),
    );

    render(<DevApiKeysSection />);

    await screen.findByTestId("dev-keys-empty");
    await user.click(screen.getByTestId("create-dev-key-btn"));
    await user.type(screen.getByTestId("create-name-input"), "Duplicada");
    await user.click(screen.getByTestId("create-submit-btn"));

    await waitFor(() => {
      expect(screen.getByTestId("create-error-name")).toHaveTextContent(
        "El nombre ya existe",
      );
    });
    // Global alert should NOT appear when a field error is present
    expect(screen.queryByTestId("create-error-msg")).not.toBeInTheDocument();
  });

  it("shows inline server error on 500", async () => {
    const user = userEvent.setup();
    server.use(
      http.post("/api/keys", () =>
        HttpResponse.json({ detail: "Error interno" }, { status: 500 }),
      ),
    );

    render(<DevApiKeysSection />);

    await screen.findByTestId("dev-keys-empty");
    await user.click(screen.getByTestId("create-dev-key-btn"));
    await user.type(screen.getByTestId("create-name-input"), "Error key");
    await user.click(screen.getByTestId("create-submit-btn"));

    await waitFor(() => {
      expect(screen.getByTestId("create-error-msg")).toHaveTextContent(
        "Error interno",
      );
    });
  });

  it("refetches the list after modal is closed", async () => {
    const user = userEvent.setup();
    const newKey = { ...ACTIVE_KEY, id: "key-new", name: "Clave recién creada" };

    server.use(
      http.post("/api/keys", () =>
        HttpResponse.json({ ...newKey, full_key: "tk_live_xyz" }),
      ),
    );

    let listCallCount = 0;
    server.use(
      http.get("/api/keys", () => {
        listCallCount++;
        return listCallCount === 1
          ? HttpResponse.json([])
          : HttpResponse.json([newKey]);
      }),
    );

    render(<DevApiKeysSection />);

    await screen.findByTestId("dev-keys-empty");
    await user.click(screen.getByTestId("create-dev-key-btn"));
    await user.type(
      screen.getByTestId("create-name-input"),
      "Clave recién creada",
    );
    await user.click(screen.getByTestId("create-submit-btn"));

    await screen.findByRole("dialog");
    await user.click(screen.getByTestId("copy-once-close-btn"));

    await waitFor(() => {
      expect(screen.getByText("Clave recién creada")).toBeInTheDocument();
    });
  });
});
