"use client";

/**
 * AuthContext — React context wrapping the pure authClient.
 *
 * Responsibilities:
 *  - Boot-time refresh: on first mount, calls refresh() to exchange the
 *    httpOnly cookie for an in-memory access token.
 *  - Exposes decoded user identity (sub, email, isAdmin) derived from the
 *    access token via the JWT decoder.
 *  - Fetches /api/auth/me after boot refresh to populate plan + entitlements.
 *  - Wires onRefreshFailure → redirectToPublic so all 401s auto-redirect.
 *  - Provides login / register / logout / authFetch to the component tree.
 *
 * ENTITLEMENTS: The /me endpoint is the authoritative source for plan and
 * feature flags. Frontend never duplicates the BETA_MODE gating logic —
 * it reads the server-computed `entitlements` array.
 *
 * Graceful fallback: if /me fails or returns no entitlements (e.g. stale
 * session), user sees locked UI (empty entitlements → all hasFeature() = false).
 * This is over-restrictive, not permissive — safe default.
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  authFetch as clientAuthFetch,
  getAccessToken,
  login as clientLogin,
  logout as clientLogout,
  onRefreshFailure,
  refresh,
  register as clientRegister,
} from "@/lib/auth/authClient";
import { decodeAccessClaims } from "@/lib/auth/jwt";
import { redirectToPublic } from "@/lib/auth/navigation";
import type { PlanId } from "@/lib/plans";

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export interface AuthUser {
  id: string;
  email: string;
  isAdmin: boolean;
  /** Canonical plan ID: 'free' | 'pro' | 'studio'. Populated from /me. */
  plan: PlanId | null;
  /**
   * Feature keys the user can access — server-computed, BETA_MODE-aware.
   * Empty array while loading or when /me hasn't responded yet.
   * Use useHasFeature() instead of reading this directly.
   */
  entitlements: string[];
}

interface AuthContextValue {
  /** Decoded user from the current access token + /me data. Null while loading or unauthenticated. */
  user: AuthUser | null;
  /** Raw access token — prefer `user` for identity checks. */
  accessToken: string | null;
  /** True while the boot-time refresh is in progress. Gate UIs on this. */
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  /** Authenticated fetch — injects Bearer, auto-refreshes on 401. */
  authFetch: typeof clientAuthFetch;
  /**
   * RBAC permission names granted to the current user (e.g. "billing:read", "users:read").
   * Populated from /api/auth/me/permissions after boot refresh.
   * Empty array while loading or unauthenticated — safe default (deny-by-default).
   */
  permissions: string[];
  /** Returns true if the current user holds the given RBAC permission name. */
  hasPermission: (name: string) => boolean;
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const AuthContext = createContext<AuthContextValue | null>(null);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setToken] = useState<string | null>(getAccessToken);
  const [isLoading, setIsLoading] = useState(true);
  /** plan + entitlements + permissions fetched from /me and /me/permissions — null until fetched. */
  const [meData, setMeData] = useState<{
    plan: PlanId | null;
    entitlements: string[];
    permissions: string[];
  } | null>(null);

  // Derive user from token + meData. No extra network call for identity —
  // plan/entitlements come from /me fetch after boot refresh.
  const user = useMemo<AuthUser | null>(() => {
    if (!accessToken) return null;
    try {
      const claims = decodeAccessClaims(accessToken);
      if (!claims) return null;
      return {
        id: claims.sub,
        email: claims.email ?? "",
        isAdmin: claims.is_admin ?? false,
        plan: meData?.plan ?? null,
        entitlements: meData?.entitlements ?? [],
      };
    } catch {
      return null;
    }
  }, [accessToken, meData]);

  /** Fetch /me and /me/permissions in parallel; populate meData. Silently ignores errors. */
  const fetchMe = useCallback(async () => {
    try {
      const [meRes, permRes] = await Promise.all([
        clientAuthFetch("/api/auth/me"),
        clientAuthFetch("/api/auth/me/permissions"),
      ]);
      const data = meRes.ok ? await meRes.json() : {};
      const permData = permRes.ok ? await permRes.json() : {};
      setMeData({
        plan: (data.plan as PlanId) ?? null,
        entitlements: Array.isArray(data.entitlements) ? data.entitlements : [],
        permissions: Array.isArray(permData.permissions) ? permData.permissions : [],
      });
    } catch {
      // Fail silently — deny-by-default (empty entitlements/permissions).
    }
  }, []);

  useEffect(() => {
    // 1. Boot refresh — try to get an access token from the httpOnly cookie
    refresh()
      .then((token) => {
        setToken(token);
        // 2. Fetch /me to get plan + entitlements after successful boot refresh.
        if (token) {
          fetchMe();
        }
      })
      .finally(() => setIsLoading(false));

    // 3. When any refresh fails (session expired/revoked) → redirect to login
    const cleanup = onRefreshFailure(() => {
      setToken(null);
      setMeData(null);
      redirectToPublic("expired");
    });

    return cleanup;
  }, [fetchMe]);

  const login = useCallback(
    async (email: string, password: string) => {
      const token = await clientLogin(email, password);
      setToken(token);
      // Re-fetch /me so plan + entitlements are populated immediately after login.
      if (token) await fetchMe();
    },
    [fetchMe]
  );

  const register = useCallback(
    async (email: string, password: string, fullName?: string) => {
      const token = await clientRegister(email, password, fullName);
      setToken(token);
      if (token) await fetchMe();
    },
    [fetchMe]
  );

  const logout = useCallback(async () => {
    await clientLogout();
    setToken(null);
    setMeData(null);
  }, []);

  const permissions = useMemo(() => meData?.permissions ?? [], [meData]);

  const hasPermission = useCallback(
    (name: string) => permissions.includes(name),
    [permissions]
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken,
      isLoading,
      login,
      register,
      logout,
      authFetch: clientAuthFetch,
      permissions,
      hasPermission,
    }),
    [user, accessToken, isLoading, login, register, logout, permissions, hasPermission]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}

/** Convenience hook — returns the decoded user or null. */
export function useUser(): AuthUser | null {
  return useAuth().user;
}

/** Convenience hook — returns true only when the user is authenticated and has the admin role. */
export function useIsAdmin(): boolean {
  return useAuth().user?.isAdmin === true;
}

/**
 * Returns the list of feature keys the current user can access.
 * Graceful fallback: [] when unauthenticated or /me hasn't loaded yet.
 */
export function useEntitlements(): string[] {
  return useAuth().user?.entitlements ?? [];
}

/**
 * Returns true if the current user has access to the given feature key.
 * Use this for all feature-gating decisions in the UI.
 *
 * @example
 *   const canExportPdf = useHasFeature('pdf_export');
 */
export function useHasFeature(key: string): boolean {
  return useEntitlements().includes(key);
}

/**
 * Returns the list of RBAC permission names granted to the current user.
 * Populated from /api/auth/me/permissions after boot refresh.
 * Graceful fallback: [] when unauthenticated or still loading.
 */
export function usePermissions(): string[] {
  return useAuth().permissions;
}

/**
 * Returns true if the current user holds the given RBAC permission name.
 * Deny-by-default: returns false while loading or unauthenticated.
 *
 * @example
 *   const canReadBilling = useHasPermission('billing:read');
 */
export function useHasPermission(name: string): boolean {
  return useAuth().hasPermission(name);
}
