import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  authFetch,
  getAccessToken,
  login,
  logout,
  onRefreshFailure,
  refresh,
  setAccessToken,
} from "../authClient";
import { server } from "@/test/msw/server";
import { authHandlers, ACCESS_TOKEN } from "@/test/msw/handlers";
import { http, HttpResponse } from "msw";

// ---------------------------------------------------------------------------
// Reset module-level state between tests
// ---------------------------------------------------------------------------
beforeEach(() => {
  setAccessToken(null);
});

// ---------------------------------------------------------------------------
// login()
// ---------------------------------------------------------------------------
describe("login()", () => {
  it("stores the access token and returns it on success", async () => {
    const token = await login("user@test.com", "password");
    expect(token).toBe(ACCESS_TOKEN);
    expect(getAccessToken()).toBe(ACCESS_TOKEN);
  });

  it("throws with detail message on 401", async () => {
    server.use(authHandlers.loginFailure());
    await expect(login("bad@test.com", "wrong")).rejects.toThrow("Credenciales inválidas");
  });

  it("leaves token null after failure", async () => {
    server.use(authHandlers.loginFailure());
    await login("bad@test.com", "wrong").catch(() => {});
    expect(getAccessToken()).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// logout()
// ---------------------------------------------------------------------------
describe("logout()", () => {
  it("clears the access token", async () => {
    setAccessToken(ACCESS_TOKEN);
    await logout();
    expect(getAccessToken()).toBeNull();
  });

  it("clears the token even when the request fails", async () => {
    server.use(http.post("/api/auth/logout", () => HttpResponse.error()));
    setAccessToken(ACCESS_TOKEN);
    await logout(); // should not throw
    expect(getAccessToken()).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// refresh()
// ---------------------------------------------------------------------------
describe("refresh()", () => {
  it("returns a new access token and stores it", async () => {
    const token = await refresh();
    expect(token).toBe(ACCESS_TOKEN);
    expect(getAccessToken()).toBe(ACCESS_TOKEN);
  });

  it("returns null and clears state on 401", async () => {
    server.use(authHandlers.refreshFailure());
    const token = await refresh();
    expect(token).toBeNull();
    expect(getAccessToken()).toBeNull();
  });

  it("fires onRefreshFailure listeners on 401", async () => {
    server.use(authHandlers.refreshFailure());
    const listener = vi.fn();
    const cleanup = onRefreshFailure(listener);
    await refresh();
    expect(listener).toHaveBeenCalledOnce();
    cleanup();
  });

  it("does NOT fire listeners on network error (offline != expired)", async () => {
    server.use(http.post("/api/auth/refresh", () => HttpResponse.error()));
    const listener = vi.fn();
    const cleanup = onRefreshFailure(listener);
    await refresh();
    expect(listener).not.toHaveBeenCalled();
    cleanup();
  });

  it("cleans up listener correctly", async () => {
    server.use(authHandlers.refreshFailure());
    const listener = vi.fn();
    const cleanup = onRefreshFailure(listener);
    cleanup(); // remove before firing
    await refresh();
    expect(listener).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// authFetch() — basic injection
// ---------------------------------------------------------------------------
describe("authFetch()", () => {
  it("injects Authorization header when token is set", async () => {
    setAccessToken(ACCESS_TOKEN);
    let capturedAuth: string | null = null;
    server.use(
      http.get("/api/test", ({ request }) => {
        capturedAuth = request.headers.get("Authorization");
        return HttpResponse.json({ ok: true });
      })
    );
    await authFetch("/api/test");
    expect(capturedAuth).toBe(`Bearer ${ACCESS_TOKEN}`);
  });

  it("sends request without Authorization when no token", async () => {
    let capturedAuth: string | null = null;
    server.use(
      http.get("/api/test", ({ request }) => {
        capturedAuth = request.headers.get("Authorization");
        return HttpResponse.json({ ok: true });
      })
    );
    await authFetch("/api/test");
    expect(capturedAuth).toBeNull();
  });

  it("retries with new token after 401 and refresh succeeds", async () => {
    setAccessToken("old-token");
    let callCount = 0;
    server.use(
      http.get("/api/protected", ({ request }) => {
        callCount++;
        const auth = request.headers.get("Authorization");
        if (auth === "Bearer old-token") return new HttpResponse(null, { status: 401 });
        return HttpResponse.json({ ok: true });
      })
    );
    const res = await authFetch("/api/protected");
    expect(res.ok).toBe(true);
    expect(callCount).toBe(2); // initial + retry
  });

  it("returns 401 when refresh also fails", async () => {
    setAccessToken("bad-token");
    server.use(
      http.get("/api/protected", () => new HttpResponse(null, { status: 401 })),
      authHandlers.refreshFailure()
    );
    const res = await authFetch("/api/protected");
    expect(res.status).toBe(401);
  });
});
