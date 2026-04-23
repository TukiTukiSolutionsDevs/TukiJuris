/**
 * Notifications service tests — NFT-1..NFT-5
 *
 * Strategy:
 *  - authFetch is a thin wrapper over native fetch so MSW intercepts all calls.
 *  - Per-test server.use() overrides set up the expected handler.
 *  - Global setup.ts already calls server.listen() / resetHandlers() / close().
 */

import { describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/msw/server";
import {
  deleteNotification,
  getUnreadCount,
  listNotifications,
  markAllAsRead,
  markAsRead,
} from "../notifications";

// authFetch that forwards to native fetch — MSW intercepts in node mode
const authFetch = (input: string, init?: RequestInit) => fetch(input, init);

// ---------------------------------------------------------------------------
// NFT-1: listNotifications hits GET with correct params
// ---------------------------------------------------------------------------

describe("listNotifications — NFT-1", () => {
  it("calls GET /api/notifications/ with page, per_page, unread_only params", async () => {
    let capturedUrl = "";
    server.use(
      http.get("/api/notifications/", ({ request }) => {
        capturedUrl = request.url;
        return HttpResponse.json({
          notifications: [],
          unread_count: 0,
          total: 0,
        });
      }),
    );

    const result = await listNotifications(authFetch, {
      page: 2,
      per_page: 10,
      unread_only: true,
    });

    const params = new URL(capturedUrl).searchParams;
    expect(params.get("page")).toBe("2");
    expect(params.get("per_page")).toBe("10");
    expect(params.get("unread_only")).toBe("true");
    expect(result.notifications).toHaveLength(0);
    expect(result.total).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// NFT-2: markAsRead uses PUT
// ---------------------------------------------------------------------------

describe("markAsRead — NFT-2", () => {
  it("calls PUT /api/notifications/:id/read and returns { status: 'ok' }", async () => {
    let capturedMethod = "";
    let capturedPath = "";
    server.use(
      http.put("/api/notifications/:id/read", ({ request, params }) => {
        capturedMethod = request.method;
        capturedPath = String(params.id);
        return HttpResponse.json({ status: "ok" });
      }),
    );

    const result = await markAsRead(authFetch, "uuid-abc");
    expect(capturedMethod).toBe("PUT");
    expect(capturedPath).toBe("uuid-abc");
    expect(result).toEqual({ status: "ok" });
  });
});

// ---------------------------------------------------------------------------
// NFT-3: markAllAsRead uses PUT
// ---------------------------------------------------------------------------

describe("markAllAsRead — NFT-3", () => {
  it("calls PUT /api/notifications/read-all and returns { status, updated }", async () => {
    let capturedMethod = "";
    server.use(
      http.put("/api/notifications/read-all", ({ request }) => {
        capturedMethod = request.method;
        return HttpResponse.json({ status: "ok", updated: 3 });
      }),
    );

    const result = await markAllAsRead(authFetch);
    expect(capturedMethod).toBe("PUT");
    expect(result).toEqual({ status: "ok", updated: 3 });
  });
});

// ---------------------------------------------------------------------------
// NFT-4: deleteNotification throws on 404
// ---------------------------------------------------------------------------

describe("deleteNotification — NFT-4", () => {
  it("throws when backend returns 404", async () => {
    server.use(
      http.delete("/api/notifications/:id", () =>
        new HttpResponse(null, { status: 404 }),
      ),
    );

    await expect(
      deleteNotification(authFetch, "uuid-not-found"),
    ).rejects.toThrow("deleteNotification failed: 404");
  });
});

// ---------------------------------------------------------------------------
// NFT-5: getUnreadCount returns count
// ---------------------------------------------------------------------------

describe("getUnreadCount — NFT-5", () => {
  it("returns { count: 7 } from GET /api/notifications/unread-count", async () => {
    server.use(
      http.get("/api/notifications/unread-count", () =>
        HttpResponse.json({ count: 7 }),
      ),
    );

    const result = await getUnreadCount(authFetch);
    expect(result).toEqual({ count: 7 });
  });
});
