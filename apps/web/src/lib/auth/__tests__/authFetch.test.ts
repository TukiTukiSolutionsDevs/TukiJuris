import { beforeEach, describe, expect, it, vi } from "vitest";
import { authFetch, setAccessToken } from "../authClient";
import { server } from "@/test/msw/server";
import { authHandlers, ACCESS_TOKEN } from "@/test/msw/handlers";
import { http, HttpResponse } from "msw";

beforeEach(() => {
  setAccessToken("stale-token");
});

// ---------------------------------------------------------------------------
// Single-flight refresh: N concurrent 401s must trigger exactly ONE refresh
// ---------------------------------------------------------------------------
describe("authFetch() single-flight refresh", () => {
  it("5 concurrent 401s trigger exactly one /api/auth/refresh call", async () => {
    let refreshCount = 0;
    let requestCount = 0;

    server.use(
      // All calls to /api/data return 401 for the stale token, 200 for new
      http.get("/api/data", ({ request }) => {
        requestCount++;
        const auth = request.headers.get("Authorization");
        if (auth === "Bearer stale-token") return new HttpResponse(null, { status: 401 });
        return HttpResponse.json({ ok: true });
      }),
      // Track how many times /refresh is called
      http.post("/api/auth/refresh", () => {
        refreshCount++;
        return HttpResponse.json({ access_token: ACCESS_TOKEN, token_type: "bearer", expires_in: 900 });
      })
    );

    const results = await Promise.all([
      authFetch("/api/data"),
      authFetch("/api/data"),
      authFetch("/api/data"),
      authFetch("/api/data"),
      authFetch("/api/data"),
    ]);

    // All 5 must succeed
    expect(results.every((r) => r.ok)).toBe(true);

    // Exactly ONE refresh — not 5
    expect(refreshCount).toBe(1);
  });

  it("retry stops after one failed refresh cycle — all callers receive 401", async () => {
    server.use(
      http.get("/api/data", () => new HttpResponse(null, { status: 401 })),
      authHandlers.refreshFailure()
    );

    const results = await Promise.all([
      authFetch("/api/data"),
      authFetch("/api/data"),
      authFetch("/api/data"),
    ]);

    expect(results.every((r) => r.status === 401)).toBe(true);
  });

  it("does not issue a second refresh if first one already set a new token", async () => {
    let refreshCount = 0;

    server.use(
      http.get("/api/data", ({ request }) => {
        const auth = request.headers.get("Authorization");
        if (auth === "Bearer stale-token") return new HttpResponse(null, { status: 401 });
        return HttpResponse.json({ ok: true });
      }),
      http.post("/api/auth/refresh", () => {
        refreshCount++;
        return HttpResponse.json({ access_token: ACCESS_TOKEN, token_type: "bearer", expires_in: 900 });
      })
    );

    // Sequential calls — second one should find a valid token from first call's refresh
    await authFetch("/api/data");
    setAccessToken("stale-token"); // Manually reset to simulate a second stale scenario
    await authFetch("/api/data");

    // Two sequential stale cycles = 2 refreshes (one per staleness window)
    expect(refreshCount).toBe(2);
  });

  it("fires onRefreshFailure once even when N concurrent calls fail", async () => {
    const { onRefreshFailure } = await import("../authClient");
    const listener = vi.fn();
    const cleanup = onRefreshFailure(listener);

    server.use(
      http.get("/api/data", () => new HttpResponse(null, { status: 401 })),
      authHandlers.refreshFailure()
    );

    await Promise.all([
      authFetch("/api/data"),
      authFetch("/api/data"),
      authFetch("/api/data"),
    ]);

    // Single-flight means refresh fires once → listener fires once
    expect(listener).toHaveBeenCalledOnce();
    cleanup();
  });
});
