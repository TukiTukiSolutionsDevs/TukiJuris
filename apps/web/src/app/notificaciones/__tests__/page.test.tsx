/**
 * Notificaciones page tests — NFT-6..NFT-12
 *
 * Strategy:
 *  - useAuth is mocked; mockAuthFetch forwards to native fetch → MSW intercepts.
 *  - AppLayout, next/navigation, next/image mocked to avoid transitive deps.
 *  - server.use() in beforeEach sets default notification handlers.
 *  - Per-test server.use() overrides for specific scenarios.
 *  - Global setup.ts calls server.listen() / resetHandlers() / close().
 */

import React from "react";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/msw/server";
import type { NotificationOut } from "@/lib/api/notifications";
import * as notifService from "@/lib/api/notifications";

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
  usePathname: () => "/notificaciones",
}));

vi.mock("next/image", () => ({
  default: ({ src, alt }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} />
  ),
}));

// ---------------------------------------------------------------------------
// Import page AFTER mocks
// ---------------------------------------------------------------------------

import NotificacionesPage from "../page";

// ---------------------------------------------------------------------------
// Mock data helpers
// ---------------------------------------------------------------------------

function makeNotif(overrides: Partial<NotificationOut> = {}): NotificationOut {
  return {
    id: "notif-1",
    user_id: "user-1",
    type: "system",
    title: "Test notification",
    message: "Test message",
    is_read: true,
    action_url: null,
    extra_data: null,
    created_at: new Date(Date.now() - 60_000).toISOString(), // 1 min ago
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Global setup / teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  mockAuthFetch.mockReset();
  // Forward all calls to native fetch → MSW intercepts
  mockAuthFetch.mockImplementation((url: string, init?: RequestInit) =>
    fetch(url, init),
  );

  // Default handlers — empty list, no unread
  server.use(
    http.get("/api/notifications/", () =>
      HttpResponse.json({ notifications: [], unread_count: 0, total: 0 }),
    ),
    http.get("/api/notifications/unread-count", () =>
      HttpResponse.json({ count: 0 }),
    ),
    http.put("/api/notifications/read-all", () =>
      HttpResponse.json({ status: "ok", updated: 0 }),
    ),
    http.put("/api/notifications/:id/read", () =>
      HttpResponse.json({ status: "ok" }),
    ),
    http.delete("/api/notifications/:id", () =>
      HttpResponse.json({ status: "ok" }),
    ),
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// NFT-6: Page renders list of 3 items + "Página 1 de 1"
// ---------------------------------------------------------------------------

describe("NotificacionesPage — NFT-6", () => {
  it("renders 3 notification items and shows Página 1 de 1", async () => {
    server.use(
      http.get("/api/notifications/", () =>
        HttpResponse.json({
          notifications: [
            makeNotif({ id: "1", title: "Notif Alpha" }),
            makeNotif({ id: "2", title: "Notif Beta" }),
            makeNotif({ id: "3", title: "Notif Gamma" }),
          ],
          unread_count: 0,
          total: 3,
        }),
      ),
    );

    render(<NotificacionesPage />);

    await waitFor(() => {
      expect(screen.getByText("Notif Alpha")).toBeInTheDocument();
      expect(screen.getByText("Notif Beta")).toBeInTheDocument();
      expect(screen.getByText("Notif Gamma")).toBeInTheDocument();
    });
    expect(screen.getByText("Página 1 de 1")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// NFT-7: Pagination — click Siguiente fetches page=2
// ---------------------------------------------------------------------------

describe("NotificacionesPage — NFT-7", () => {
  it("clicking Siguiente re-fetches with page=2 and shows Página 2 de 3", async () => {
    server.use(
      http.get("/api/notifications/", ({ request }) => {
        const page = new URL(request.url).searchParams.get("page");
        if (page === "2") {
          return HttpResponse.json({
            notifications: [makeNotif({ id: "p2-1", title: "Page 2 Item" })],
            unread_count: 0,
            total: 50,
          });
        }
        return HttpResponse.json({
          notifications: [makeNotif({ id: "p1-1", title: "Page 1 Item" })],
          unread_count: 0,
          total: 50,
        });
      }),
    );

    const user = userEvent.setup();
    render(<NotificacionesPage />);

    await waitFor(() =>
      expect(screen.getByText("Page 1 Item")).toBeInTheDocument(),
    );

    await user.click(screen.getByRole("button", { name: /página siguiente/i }));

    await waitFor(() => {
      expect(screen.getByText("Page 2 Item")).toBeInTheDocument();
      expect(screen.getByText("Página 2 de 3")).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// NFT-8: unread_only toggle re-fetches with unread_only=true
// ---------------------------------------------------------------------------

describe("NotificacionesPage — NFT-8", () => {
  it("toggling Sin leer re-fetches with unread_only=true", async () => {
    let lastParams = new URLSearchParams();
    server.use(
      http.get("/api/notifications/", ({ request }) => {
        lastParams = new URL(request.url).searchParams;
        return HttpResponse.json({
          notifications: [],
          unread_count: 0,
          total: 0,
        });
      }),
    );

    const user = userEvent.setup();
    render(<NotificacionesPage />);

    // Wait for initial fetch (unread_only=false)
    await waitFor(() =>
      expect(lastParams.get("unread_only")).toBe("false"),
    );

    // Click the toggle
    await user.click(screen.getByRole("button", { name: /sin leer/i }));

    // Re-fetch should use unread_only=true
    await waitFor(() =>
      expect(lastParams.get("unread_only")).toBe("true"),
    );
  });
});

// ---------------------------------------------------------------------------
// NFT-9: Type chip filters list client-side
// ---------------------------------------------------------------------------

describe("NotificacionesPage — NFT-9", () => {
  it("clicking Facturación chip hides non-billing items", async () => {
    server.use(
      http.get("/api/notifications/", () =>
        HttpResponse.json({
          notifications: [
            makeNotif({ id: "1", type: "billing", title: "Billing One" }),
            makeNotif({ id: "2", type: "system", title: "System One" }),
            makeNotif({ id: "3", type: "billing", title: "Billing Two" }),
          ],
          unread_count: 0,
          total: 3,
        }),
      ),
    );

    const user = userEvent.setup();
    render(<NotificacionesPage />);

    // Wait for initial render with all 3 items
    await waitFor(() =>
      expect(screen.getByText("System One")).toBeInTheDocument(),
    );

    // Click the Facturación (billing) chip
    await user.click(screen.getByRole("button", { name: /facturación/i }));

    // After chip + re-fetch settle, only billing items visible
    await waitFor(() => {
      expect(screen.getByText("Billing One")).toBeInTheDocument();
      expect(screen.getByText("Billing Two")).toBeInTheDocument();
      expect(screen.queryByText("System One")).not.toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// NFT-10: Mark-read removes unread dot
// ---------------------------------------------------------------------------

describe("NotificacionesPage — NFT-10", () => {
  it("clicking Marcar leída removes the unread dot optimistically", async () => {
    server.use(
      http.get("/api/notifications/", () =>
        HttpResponse.json({
          notifications: [
            makeNotif({ id: "u1", title: "Unread Item", is_read: false }),
          ],
          unread_count: 1,
          total: 1,
        }),
      ),
    );

    const user = userEvent.setup();
    render(<NotificacionesPage />);

    await waitFor(() =>
      expect(screen.getByText("Unread Item")).toBeInTheDocument(),
    );

    // Unread dot is visible
    expect(screen.getByLabelText("No leída")).toBeInTheDocument();

    // Click "Marcar leída"
    await user.click(screen.getByRole("button", { name: /marcar leída/i }));

    // Dot disappears (optimistic)
    await waitFor(() =>
      expect(screen.queryByLabelText("No leída")).not.toBeInTheDocument(),
    );
  });
});

// ---------------------------------------------------------------------------
// NFT-11: Mark-all-read removes all unread dots
// ---------------------------------------------------------------------------

describe("NotificacionesPage — NFT-11", () => {
  it("clicking Marcar todas como leídas removes all unread dots", async () => {
    server.use(
      http.get("/api/notifications/", () =>
        HttpResponse.json({
          notifications: [
            makeNotif({ id: "u1", title: "Unread A", is_read: false }),
            makeNotif({ id: "u2", title: "Unread B", is_read: false }),
          ],
          unread_count: 2,
          total: 2,
        }),
      ),
    );

    const user = userEvent.setup();
    render(<NotificacionesPage />);

    await waitFor(() => {
      expect(screen.getAllByLabelText("No leída")).toHaveLength(2);
    });

    await user.click(
      screen.getByRole("button", { name: /marcar todas como leídas/i }),
    );

    await waitFor(() =>
      expect(screen.queryByLabelText("No leída")).not.toBeInTheDocument(),
    );
  });
});

// ---------------------------------------------------------------------------
// NFT-12: Delete optimistic + rollback on server error
// ---------------------------------------------------------------------------

describe("NotificacionesPage — NFT-12", () => {
  it("delete rolls back and shows error toast when server returns 500", async () => {
    server.use(
      http.get("/api/notifications/", () =>
        HttpResponse.json({
          notifications: [
            makeNotif({ id: "keep", title: "Keep Me" }),
            makeNotif({ id: "del", title: "Delete Me" }),
          ],
          unread_count: 0,
          total: 2,
        }),
      ),
      // Override DELETE to fail
      http.delete("/api/notifications/:id", () =>
        new HttpResponse(null, { status: 500 }),
      ),
    );

    const user = userEvent.setup();
    render(<NotificacionesPage />);

    await waitFor(() =>
      expect(screen.getByText("Delete Me")).toBeInTheDocument(),
    );

    // Click delete on second item
    const deleteButtons = screen.getAllByRole("button", {
      name: /eliminar notificación/i,
    });
    await user.click(deleteButtons[1]);

    // After rollback: item restored + error toast visible
    await waitFor(() => {
      expect(screen.getByText("Delete Me")).toBeInTheDocument();
      expect(screen.getByRole("alert")).toHaveTextContent(
        "No se pudo eliminar la notificación.",
      );
    });
  });
});

// ---------------------------------------------------------------------------
// NFT-14: 30s polling — re-fetches every interval and cleans up on unmount (NF-9)
// ---------------------------------------------------------------------------

describe("NotificacionesPage — NFT-14", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("re-fetches on 30s interval and stops polling after unmount", async () => {
    const listSpy = vi.spyOn(notifService, "listNotifications");

    const { unmount } = render(<NotificacionesPage />);

    // Flush initial mount effects
    await act(async () => {});
    const afterMount = listSpy.mock.calls.length;
    expect(afterMount).toBeGreaterThanOrEqual(1);

    // Advance 30s → interval fires → fetchData called again
    await act(async () => {
      vi.advanceTimersByTime(30_000);
    });
    expect(listSpy.mock.calls.length).toBeGreaterThan(afterMount);

    // Unmount → clearInterval → advancing time no longer triggers refetch
    unmount();
    const afterUnmount = listSpy.mock.calls.length;
    await act(async () => {
      vi.advanceTimersByTime(30_000);
    });
    expect(listSpy.mock.calls.length).toBe(afterUnmount);
  });
});

// ---------------------------------------------------------------------------
// NFT-15: Unread count refreshed after each mutation (NF-16)
// ---------------------------------------------------------------------------

describe("NotificacionesPage — NFT-15", () => {
  it("calls getUnreadCount after mark-read, mark-all-read, and delete", async () => {
    let unreadCalls = 0;
    server.use(
      http.get("/api/notifications/", () =>
        HttpResponse.json({
          notifications: [makeNotif({ id: "m1", is_read: false, title: "Mutable" })],
          unread_count: 1,
          total: 1,
        }),
      ),
      http.get("/api/notifications/unread-count", () => {
        unreadCalls++;
        return HttpResponse.json({ count: 1 });
      }),
    );

    const user = userEvent.setup();
    render(<NotificacionesPage />);

    await waitFor(() => expect(screen.getByText("Mutable")).toBeInTheDocument());
    const base = unreadCalls;

    // 1. mark-read → refreshUnreadCount called
    await user.click(screen.getByRole("button", { name: /marcar leída/i }));
    await waitFor(() => expect(unreadCalls).toBe(base + 1));

    // 2. mark-all-read → refreshUnreadCount called
    await user.click(screen.getByRole("button", { name: /marcar todas como leídas/i }));
    await waitFor(() => expect(unreadCalls).toBe(base + 2));

    // 3. delete → refreshUnreadCount called
    await user.click(screen.getByRole("button", { name: /eliminar notificación/i }));
    await waitFor(() => expect(unreadCalls).toBe(base + 3));
  });
});

// ---------------------------------------------------------------------------
// NFT-16: All-empty state (NF-17)
// ---------------------------------------------------------------------------

describe("NotificacionesPage — NFT-16", () => {
  it("shows logo and 'No tenés notificaciones todavía.' when list is empty", async () => {
    // Default beforeEach handler returns { notifications: [], unread_count: 0, total: 0 }
    render(<NotificacionesPage />);

    await waitFor(() => {
      expect(screen.getByAltText("TukiJuris")).toBeInTheDocument();
      expect(
        screen.getByText("No tenés notificaciones todavía."),
      ).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// NFT-17: Filter-empty state + Limpiar filtros resets view (NF-18)
// ---------------------------------------------------------------------------

describe("NotificacionesPage — NFT-17", () => {
  it("shows filter-empty state when chip filters all items and resets on Limpiar filtros", async () => {
    server.use(
      http.get("/api/notifications/", () =>
        HttpResponse.json({
          notifications: [
            makeNotif({ id: "s1", type: "system", title: "System Notif" }),
          ],
          unread_count: 0,
          total: 1,
        }),
      ),
    );

    const user = userEvent.setup();
    render(<NotificacionesPage />);

    await waitFor(() => expect(screen.getByText("System Notif")).toBeInTheDocument());

    // Click "Facturación" chip → filters out "system" type → filter-empty state
    await user.click(screen.getByRole("button", { name: /facturación/i }));

    await waitFor(() => {
      expect(
        screen.getByText("No hay notificaciones que coincidan con el filtro."),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /limpiar filtros/i }),
      ).toBeInTheDocument();
    });

    // Click "Limpiar filtros" → chips cleared → items reappear
    await user.click(screen.getByRole("button", { name: /limpiar filtros/i }));

    await waitFor(() => {
      expect(screen.getByText("System Notif")).toBeInTheDocument();
      expect(
        screen.queryByText("No hay notificaciones que coincidan con el filtro."),
      ).not.toBeInTheDocument();
    });
  });
});
