/**
 * Chat page — conversation export integration tests.
 * AC IDs: FE-EXP-CHAT, FE-EXP-TESTS
 *
 * Strategy:
 *  - useAuth / useHasFeature mocked; mockAuthFetch forwards to native fetch → MSW.
 *  - Heavy sub-components (OrchestratorPanel, ChatComposer, etc.) mocked to isolate export.
 *  - sonner toast mocked to allow assertion without a DOM Toaster.
 *  - downloadBlob mocked at module level (avoids fragile document.createElement interception).
 *  - server.use() in beforeEach provides all endpoints the chat page hits on mount.
 */

import React, { Suspense } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/msw/server";

// ---------------------------------------------------------------------------
// Hoisted mocks
// ---------------------------------------------------------------------------

const { mockAuthFetch, mockHasFeature, mockSearchParamsGet, stableSearchParams, stableRouter } =
  vi.hoisted(() => {
    const mockSearchParamsGet = vi.fn().mockReturnValue(null);
    // Stable object — same reference across renders, so useCallback deps don't
    // change on every render and the search/conversation effect fires only when needed.
    const stableSearchParams = {
      get: (key: string) => mockSearchParamsGet(key),
      getAll: () => [] as string[],
      toString: () => "",
    };
    const stableRouter = { push: vi.fn(), replace: vi.fn() };
    return {
      mockAuthFetch: vi.fn(),
      mockHasFeature: vi.fn().mockReturnValue(true),
      mockSearchParamsGet,
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
  usePathname: () => "/",
}));

vi.mock("@/components/AppLayout", () => ({
  AppLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-layout">{children}</div>
  ),
}));

vi.mock("@/components/KeyboardShortcuts", () => ({
  default: () => null,
}));

vi.mock("@/app/chat/components/OrchestratorPanel", () => ({
  OrchestratorPanel: () => null,
}));

vi.mock("@/app/chat/components/ChatComposer", () => ({
  ChatComposer: () => <div data-testid="chat-composer" />,
}));

vi.mock("@/app/chat/components/ChatEmptyState", () => ({
  ChatEmptyState: () => <div data-testid="chat-empty-state">Sin mensajes</div>,
}));

vi.mock("@/app/chat/components/ChatBubble", () => ({
  ChatBubble: ({ message }: { message: { content: string } }) => (
    <div data-testid="chat-bubble">{message.content}</div>
  ),
}));

vi.mock("@/lib/models", () => ({
  MODEL_CATALOG: [{ id: "claude-haiku", name: "Claude Haiku" }],
  availableModelsForProviders: () => ["claude-haiku"],
  modelSupportsThinking: () => false,
}));

vi.mock("next/image", () => ({
  default: ({ src, alt }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} />
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

import Home from "../page";
import { toast } from "sonner";
import { downloadBlob } from "@/lib/export/downloadBlob";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const CONV_ID = "conv-abc-123";

const MESSAGES_RESPONSE = {
  id: CONV_ID,
  title: "Test Conversation",
  legal_area: "civil",
  messages: [
    { id: "msg-1", role: "user", content: "Hola, tengo una consulta" },
    { id: "msg-2", role: "assistant", content: "Con gusto te ayudo." },
  ],
};

function setupLoadedConversation() {
  mockSearchParamsGet.mockImplementation((key: string) =>
    key === "conversation" ? CONV_ID : null,
  );
}

function renderPage() {
  return render(
    <Suspense fallback={null}>
      <Home />
    </Suspense>,
  );
}

// ---------------------------------------------------------------------------
// Global setup / teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  // jsdom doesn't implement scrollIntoView — mock it to prevent effect crashes
  window.HTMLElement.prototype.scrollIntoView = vi.fn();

  // jsdom doesn't provide localStorage by default in this env — provide a minimal stub
  Object.defineProperty(globalThis, "localStorage", {
    value: {
      getItem: vi.fn().mockReturnValue(null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    },
    writable: true,
    configurable: true,
  });

  mockAuthFetch.mockReset();
  mockHasFeature.mockReset();
  mockHasFeature.mockReturnValue(true);
  mockSearchParamsGet.mockReturnValue(null);
  vi.mocked(downloadBlob).mockClear();
  vi.mocked(toast.success).mockClear();
  vi.mocked(toast.error).mockClear();

  // Forward all authFetch calls to native fetch → MSW intercepts
  mockAuthFetch.mockImplementation((url: string, init?: RequestInit) =>
    fetch(url, init),
  );

  // Default MSW handlers for all endpoints the chat page hits on mount
  server.use(
    http.get("/api/keys/llm-keys", () =>
      HttpResponse.json([{ provider: "anthropic" }]),
    ),
    http.get("/api/conversations/", () => HttpResponse.json([])),
    http.get(`/api/conversations/${CONV_ID}`, () =>
      HttpResponse.json(MESSAGES_RESPONSE),
    ),
    http.post("/api/export/conversation/pdf", () =>
      HttpResponse.arrayBuffer(new ArrayBuffer(8), {
        headers: {
          "Content-Type": "application/pdf",
          "Content-Disposition": `attachment; filename="conversacion-${CONV_ID}.pdf"`,
        },
      }),
    ),
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// FE-EXP-CHAT-1: Export button absent when no active conversation (empty state)
// ---------------------------------------------------------------------------

describe("FE-EXP-CHAT — empty conversation", () => {
  it("does not show export button when there are no messages", async () => {
    // No conversation loaded — default empty state
    renderPage();

    // Give effects time to settle
    await waitFor(() =>
      expect(screen.getByTestId("chat-empty-state")).toBeInTheDocument(),
    );

    expect(
      screen.queryByRole("button", { name: /exportar conversación/i }),
    ).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// FE-EXP-CHAT-2: Export button visible and triggers POST on success
// ---------------------------------------------------------------------------

describe("FE-EXP-CHAT — export success", () => {
  it("shows export button after conversation loads, asserts aria-busy while pending, and calls downloadBlob on success", async () => {
    setupLoadedConversation();

    // Deferred handler — suspends the response until we manually resolve,
    // allowing us to assert aria-busy="true" while the request is in-flight.
    let resolveExport!: () => void;
    const exportGate = new Promise<void>((res) => {
      resolveExport = res;
    });

    server.use(
      http.post("/api/export/conversation/pdf", async () => {
        await exportGate;
        return HttpResponse.arrayBuffer(new ArrayBuffer(8), {
          headers: {
            "Content-Type": "application/pdf",
            "Content-Disposition": `attachment; filename="conversacion-${CONV_ID}.pdf"`,
          },
        });
      }),
    );

    renderPage();

    // Wait for messages to render (conversation loaded via loadConversation)
    await waitFor(() =>
      expect(screen.getAllByTestId("chat-bubble").length).toBeGreaterThan(0),
    );

    const exportBtn = await screen.findByRole("button", {
      name: /exportar conversación/i,
    });
    expect(exportBtn).toBeInTheDocument();

    // Click starts the async flow; userEvent resolves after React processes
    // the click event but before handleExportConversation's first await returns.
    await userEvent.click(exportBtn);

    // While the request is blocked, the button must carry aria-busy="true"
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /exportando conversación/i }),
      ).toHaveAttribute("aria-busy", "true");
    });

    // Unblock the MSW handler — response now completes
    resolveExport();

    await waitFor(() => {
      expect(downloadBlob).toHaveBeenCalled();
    });

    // Fallback filename includes the conversation ID
    const [, fallback] = vi.mocked(downloadBlob).mock.calls[0];
    expect(fallback).toContain(CONV_ID);
    expect(fallback).toContain(".pdf");

    expect(toast.success).toHaveBeenCalledWith("Conversación exportada");
  });
});

// ---------------------------------------------------------------------------
// FE-EXP-CHAT-3: Export error shows toast and resets state
// ---------------------------------------------------------------------------

describe("FE-EXP-CHAT — export error", () => {
  it("shows error toast when backend returns non-OK status", async () => {
    setupLoadedConversation();

    server.use(
      http.post("/api/export/conversation/pdf", () =>
        new HttpResponse(null, { status: 500 }),
      ),
    );

    renderPage();

    await waitFor(() =>
      expect(screen.getAllByTestId("chat-bubble").length).toBeGreaterThan(0),
    );

    const exportBtn = await screen.findByRole("button", {
      name: /exportar conversación/i,
    });
    await userEvent.click(exportBtn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        "No se pudo exportar. Intentá nuevamente.",
      );
    });

    // downloadBlob should NOT have been called
    expect(downloadBlob).not.toHaveBeenCalled();

    // Button should return to non-exporting state
    await waitFor(() => {
      const btn = screen.getByRole("button", { name: /exportar conversación/i });
      expect(btn).not.toBeDisabled();
    });
  });
});

// ---------------------------------------------------------------------------
// FE-EXP-CHAT-4: Feature gate — UpsellModal shown, no request sent
// ---------------------------------------------------------------------------

describe("FE-EXP-CHAT — feature gate", () => {
  it("shows UpsellModal and sends no request when pdf_export entitlement is missing", async () => {
    setupLoadedConversation();
    mockHasFeature.mockReturnValue(false);

    let exportCalled = false;
    server.use(
      http.post("/api/export/conversation/pdf", () => {
        exportCalled = true;
        return HttpResponse.arrayBuffer(new ArrayBuffer(8));
      }),
    );

    renderPage();

    await waitFor(() =>
      expect(screen.getAllByTestId("chat-bubble").length).toBeGreaterThan(0),
    );

    const exportBtn = await screen.findByRole("button", {
      name: /exportar conversación/i,
    });
    await userEvent.click(exportBtn);

    // UpsellModal should appear
    await waitFor(() =>
      expect(screen.getByText(/función exclusiva/i)).toBeInTheDocument(),
    );

    expect(exportCalled).toBe(false);
    expect(downloadBlob).not.toHaveBeenCalled();
  });
});
