/**
 * NotificationBell tests — FRT-1, FRT-2
 *
 * Strategy:
 *  - vi.hoisted() declares mockAuthFetch BEFORE vi.mock hoisting runs.
 *  - vi.mock '@/lib/auth/authClient' returns { authFetch: mockAuthFetch }.
 *  - token prop = "test-token" so the component renders (non-null guard passes).
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Hoist mock ref so vi.mock factory can reference it
// ---------------------------------------------------------------------------

const { mockAuthFetch } = vi.hoisted(() => ({
  mockAuthFetch: vi.fn(),
}));

// ---------------------------------------------------------------------------
// Mock authClient — must appear before component import
// ---------------------------------------------------------------------------

vi.mock("@/lib/auth/authClient", () => ({
  authFetch: mockAuthFetch,
}));

// ---------------------------------------------------------------------------
// Import component AFTER mocks
// ---------------------------------------------------------------------------

import NotificationBell from "../NotificationBell";

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

beforeEach(() => {
  mockAuthFetch.mockReset();
});

// ---------------------------------------------------------------------------
// FRT-1: NotificationBell uses authFetch
// ---------------------------------------------------------------------------

describe("NotificationBell — FRT-1: uses authFetch", () => {
  it("calls authFetch with the unread-count endpoint and renders the badge", async () => {
    mockAuthFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ count: 5 }), { status: 200 })
    );

    render(<NotificationBell token="test-token" />);

    await waitFor(() => {
      expect(mockAuthFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/notifications/unread-count")
      );
    });

    await waitFor(() => {
      expect(screen.getByText("5")).toBeInTheDocument();
    });
  });
});

// ---------------------------------------------------------------------------
// FRT-2: NotificationBell catch resets unreadCount to 0
// ---------------------------------------------------------------------------

describe("NotificationBell — FRT-2: catch resets count to 0", () => {
  it("renders bell without badge and does not crash when authFetch throws", async () => {
    mockAuthFetch.mockRejectedValueOnce(new Error("Network error"));

    render(<NotificationBell token="test-token" />);

    await waitFor(() => expect(mockAuthFetch).toHaveBeenCalled());

    // unreadCount === 0 → badge span is not rendered
    expect(screen.queryByText(/^\d+$/)).not.toBeInTheDocument();
    // Component did not crash — bell button is still present
    expect(
      screen.getByRole("button", { name: /notificaciones/i })
    ).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// NFT-13: NotificationBell dropdown shows "Ver todas" link
// ---------------------------------------------------------------------------

describe("NotificationBell — NFT-13: Ver todas link", () => {
  it("shows 'Ver todas' link pointing to /notificaciones in dropdown footer", async () => {
    // First call: fetchUnreadCount on mount
    mockAuthFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ count: 0 }), { status: 200 })
    );
    // Second call: fetchNotifications when dropdown opens
    mockAuthFetch.mockResolvedValueOnce(
      new Response(
        JSON.stringify({ notifications: [], unread_count: 0, total: 0 }),
        { status: 200 }
      )
    );

    const user = userEvent.setup();
    render(<NotificationBell token="test-token" />);

    // Wait for mount effect (unread-count fetch)
    await waitFor(() =>
      expect(mockAuthFetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/notifications/unread-count")
      )
    );

    // Open dropdown
    await user.click(screen.getByRole("button", { name: /notificaciones/i }));

    // "Ver todas" link must be present with correct href
    const link = await screen.findByRole("link", { name: /ver todas/i });
    expect(link).toHaveAttribute("href", "/notificaciones");
  });
});
