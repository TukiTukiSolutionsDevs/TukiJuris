import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import React from "react";
import { AuthProvider, useAuth } from "../AuthContext";
import { setAccessToken } from "../authClient";
import { server } from "@/test/msw/server";
import { authHandlers, ACCESS_TOKEN, ADMIN_ACCESS_TOKEN } from "@/test/msw/handlers";
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
