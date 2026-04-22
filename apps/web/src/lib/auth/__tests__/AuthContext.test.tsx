import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import React from "react";
import { AuthProvider, useAuth } from "../AuthContext";
import { authFetch as clientAuthFetch, logout, setAccessToken } from "../authClient";
import { redirectToPublic } from "@/lib/auth/navigation";
import { server } from "@/test/msw/server";
import { authHandlers, ACCESS_TOKEN } from "@/test/msw/handlers";
import { http, HttpResponse } from "msw";

// Prevent actual navigation in jsdom
vi.mock("@/lib/auth/navigation", () => ({
  buildReturnTo: vi.fn(() => "/"),
  redirectToPublic: vi.fn(),
}));

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
);

beforeEach(() => {
  setAccessToken(null);
});

// ---------------------------------------------------------------------------
// Boot refresh
// ---------------------------------------------------------------------------
describe("AuthProvider boot refresh", () => {
  it("starts with isLoading=true, user=null", () => {
    // Delay refresh so we can observe the initial state
    server.use(
      http.post("/api/auth/refresh", async () => {
        await new Promise((r) => setTimeout(r, 50));
        return HttpResponse.json({ access_token: ACCESS_TOKEN, token_type: "bearer", expires_in: 900 });
      })
    );

    const { result } = renderHook(() => useAuth(), { wrapper });
    expect(result.current.isLoading).toBe(true);
    expect(result.current.user).toBeNull();
  });

  it("hydrates user with decoded claims after successful boot refresh", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.user).not.toBeNull();
    expect(result.current.user?.id).toBe("user-1");
    expect(result.current.user?.email).toBe("user@test.com");
    expect(result.current.user?.isAdmin).toBe(false);
    expect(result.current.accessToken).toBe(ACCESS_TOKEN);
  });

  it("maps is_admin=true from JWT claims for admin user", async () => {
    server.use(authHandlers.adminRefresh());
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.user?.isAdmin).toBe(true);
  });

  it("sets user=null and isLoading=false when refresh returns 401 (no cookie)", async () => {
    server.use(authHandlers.refreshFailure());
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.user).toBeNull();
    expect(result.current.accessToken).toBeNull();
  });

  it("sets user=null without throwing when refresh is a network error", async () => {
    server.use(http.post("/api/auth/refresh", () => HttpResponse.error()));
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.user).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// login()
// ---------------------------------------------------------------------------
describe("useAuth().login()", () => {
  it("sets user after successful login", async () => {
    // Suppress boot refresh to isolate login
    server.use(authHandlers.refreshFailure());
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // Now override refresh handler to succeed for post-login use
    server.use(
      http.post("/api/auth/login", () =>
        HttpResponse.json({ access_token: ACCESS_TOKEN, token_type: "bearer", expires_in: 900 })
      )
    );

    await act(async () => {
      await result.current.login("user@test.com", "password");
    });

    expect(result.current.user?.id).toBe("user-1");
    expect(result.current.accessToken).toBe(ACCESS_TOKEN);
  });

  it("throws on login failure and leaves user null", async () => {
    server.use(authHandlers.refreshFailure(), authHandlers.loginFailure());
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await expect(
      act(async () => { await result.current.login("bad@test.com", "wrong"); })
    ).rejects.toThrow();

    expect(result.current.user).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// logout()
// ---------------------------------------------------------------------------
describe("useAuth().logout()", () => {
  it("clears user and accessToken", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // Confirm we're logged in after boot refresh
    expect(result.current.user).not.toBeNull();

    await act(async () => { await result.current.logout(); });

    expect(result.current.user).toBeNull();
    expect(result.current.accessToken).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// onboardingCompleted
// ---------------------------------------------------------------------------
describe("useAuth().onboardingCompleted", () => {
  it("defaults to false while loading", () => {
    server.use(
      http.post("/api/auth/refresh", async () => {
        await new Promise((r) => setTimeout(r, 50));
        return HttpResponse.json({ access_token: ACCESS_TOKEN, token_type: "bearer", expires_in: 900 });
      })
    );
    const { result } = renderHook(() => useAuth(), { wrapper });
    expect(result.current.onboardingCompleted).toBe(false);
  });

  it("reads onboarding_completed=false from /me after boot refresh", async () => {
    // Default handler returns onboarding_completed: false
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.onboardingCompleted).toBe(false);
  });

  it("reads onboarding_completed=true from /me when server returns true", async () => {
    server.use(
      http.get("/api/auth/me", () =>
        HttpResponse.json({
          id: "user-1",
          email: "user@test.com",
          is_admin: false,
          onboarding_completed: true,
          plan: "free",
          entitlements: ["chat"],
        })
      )
    );
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.onboardingCompleted).toBe(true);
  });

  it("resets to false after logout", async () => {
    server.use(
      http.get("/api/auth/me", () =>
        HttpResponse.json({
          id: "user-1",
          email: "user@test.com",
          is_admin: false,
          onboarding_completed: true,
          plan: "free",
          entitlements: ["chat"],
        })
      )
    );
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.onboardingCompleted).toBe(true);

    await act(async () => { await result.current.logout(); });
    expect(result.current.onboardingCompleted).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// completeOnboarding()
// ---------------------------------------------------------------------------
describe("useAuth().completeOnboarding()", () => {
  it("calls POST /api/auth/me/onboarding then re-fetches /me", async () => {
    let onboardingCalled = false;
    let meCallCount = 0;

    server.use(
      http.post("/api/auth/me/onboarding", () => {
        onboardingCalled = true;
        return new HttpResponse(null, { status: 204 });
      }),
      http.get("/api/auth/me", () => {
        meCallCount++;
        return HttpResponse.json({
          id: "user-1",
          email: "user@test.com",
          is_admin: false,
          onboarding_completed: meCallCount > 1, // true on 2nd+ call
          plan: "free",
          entitlements: ["chat"],
        });
      })
    );

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // Before completeOnboarding: false
    expect(result.current.onboardingCompleted).toBe(false);

    await act(async () => { await result.current.completeOnboarding(); });

    expect(onboardingCalled).toBe(true);
    expect(result.current.onboardingCompleted).toBe(true);
  });

  it("updates onboardingCompleted to true in context after completion", async () => {
    server.use(
      http.get("/api/auth/me", (() => {
        let called = 0;
        return () => {
          called++;
          return HttpResponse.json({
            id: "user-1",
            email: "user@test.com",
            is_admin: false,
            onboarding_completed: called > 1,
            plan: "free",
            entitlements: ["chat"],
          });
        };
      })())
    );

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => { await result.current.completeOnboarding(); });

    expect(result.current.onboardingCompleted).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// logoutAll()
// ---------------------------------------------------------------------------
describe("useAuth().logoutAll()", () => {
  it("clears user and accessToken after logout-all", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.user).not.toBeNull();

    await act(async () => { await result.current.logoutAll(); });

    expect(result.current.user).toBeNull();
    expect(result.current.accessToken).toBeNull();
  });

  it("resets onboardingCompleted to false after logout-all", async () => {
    server.use(
      http.get("/api/auth/me", () =>
        HttpResponse.json({
          id: "user-1",
          email: "user@test.com",
          is_admin: false,
          onboarding_completed: true,
          plan: "free",
          entitlements: ["chat"],
        })
      )
    );

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.onboardingCompleted).toBe(true);

    await act(async () => { await result.current.logoutAll(); });

    expect(result.current.onboardingCompleted).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// FRT-3: onRefreshFailure clears state + redirects
// ---------------------------------------------------------------------------
describe("FRT-3: onRefreshFailure clears AuthContext + redirects", () => {
  it("clears user and calls redirectToPublic when a mid-session refresh fails", async () => {
    const mockRedirect = redirectToPublic as unknown as ReturnType<typeof vi.fn>;
    mockRedirect.mockClear();

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.user).not.toBeNull();

    // Simulate 401 on an authenticated request → authFetch calls refresh() → refresh fails
    server.use(
      authHandlers.refreshFailure(),
      http.get("/api/auth/me", () => new HttpResponse(null, { status: 401 })),
    );

    await act(async () => {
      await clientAuthFetch("/api/auth/me");
    });

    await waitFor(() => expect(result.current.user).toBeNull());
    expect(mockRedirect).toHaveBeenCalledWith("expired");
  });
});

// ---------------------------------------------------------------------------
// FRT-4: BroadcastChannel LOGOUT clears AuthContext state
// ---------------------------------------------------------------------------
describe("FRT-4: BroadcastChannel LOGOUT clears AuthContext state", () => {
  it("clears user when a LOGOUT message is received from another tab", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.user).not.toBeNull();

    // Simulate another tab posting LOGOUT on the shared channel
    const sender = new BroadcastChannel("tukijuris:auth");
    act(() => {
      sender.postMessage({ type: "LOGOUT" });
    });

    await waitFor(() => expect(result.current.user).toBeNull());
    sender.close();
  });
});

// ---------------------------------------------------------------------------
// FRT-5: authClient.logout() posts LOGOUT to BroadcastChannel
// ---------------------------------------------------------------------------
describe("FRT-5: authClient.logout posts LOGOUT message", () => {
  it("calls postMessage({ type: 'LOGOUT' }) when logout() is invoked", async () => {
    const spy = vi.spyOn(BroadcastChannel.prototype, "postMessage");
    await logout();
    expect(spy).toHaveBeenCalledWith({ type: "LOGOUT" });
    spy.mockRestore();
  });
});

// ---------------------------------------------------------------------------
// FRT-6: context logoutAll() posts LOGOUT to BroadcastChannel
// ---------------------------------------------------------------------------
describe("FRT-6: context logoutAll posts LOGOUT message", () => {
  it("calls postMessage({ type: 'LOGOUT' }) when logoutAll() is invoked", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    const spy = vi.spyOn(BroadcastChannel.prototype, "postMessage");
    await act(async () => { await result.current.logoutAll(); });
    expect(spy).toHaveBeenCalledWith({ type: "LOGOUT" });
    spy.mockRestore();
  });
});
