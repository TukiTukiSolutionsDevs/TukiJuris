/**
 * Auth client — pure TypeScript, no React, no localStorage.
 *
 * Token storage contract:
 *   access_token  → module-level variable (memory only, never persisted)
 *   refresh_token → httpOnly cookie set by the backend (JS cannot read it)
 *
 * All fetch calls use credentials: "include" so the browser sends the
 * refresh_token cookie automatically on /api/auth/* requests.
 *
 * The Next.js dev proxy (next.config.ts) rewrites /api/* → backend, making
 * all requests same-origin so SameSite=Lax cookies are sent correctly.
 */

// ---------------------------------------------------------------------------
// In-memory state
// ---------------------------------------------------------------------------

let _accessToken: string | null = null;

/** Active single-flight refresh promise — null when no refresh is in progress */
let _refreshInflight: Promise<string | null> | null = null;

type RefreshFailureListener = () => void;
const _refreshFailureListeners = new Set<RefreshFailureListener>();

// ---------------------------------------------------------------------------
// Cross-tab logout sync
// ---------------------------------------------------------------------------

let _bc: BroadcastChannel | null = null;

/** Lazy, SSR-safe BroadcastChannel accessor. Returns null in SSR environments. */
export function getAuthChannel(): BroadcastChannel | null {
  if (typeof BroadcastChannel === "undefined") return null;
  if (!_bc) _bc = new BroadcastChannel("tukijuris:auth");
  return _bc;
}

// ---------------------------------------------------------------------------
// Accessors
// ---------------------------------------------------------------------------

export function getAccessToken(): string | null {
  return _accessToken;
}

export function setAccessToken(token: string | null): void {
  _accessToken = token;
}

/**
 * Register a callback that fires when a refresh attempt fails (session expired).
 * Returns a cleanup function to remove the listener.
 */
export function onRefreshFailure(fn: RefreshFailureListener): () => void {
  _refreshFailureListeners.add(fn);
  return () => _refreshFailureListeners.delete(fn);
}

// ---------------------------------------------------------------------------
// Auth actions
// ---------------------------------------------------------------------------

export async function login(email: string, password: string): Promise<string> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Credenciales invalidas" }));
    throw new Error((err as { detail?: string }).detail || "Credenciales invalidas");
  }
  const data = (await res.json()) as { access_token: string };
  setAccessToken(data.access_token);
  return data.access_token;
}

export async function register(
  email: string,
  password: string,
  fullName?: string
): Promise<string> {
  const res = await fetch("/api/auth/register", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error al registrar" }));
    throw new Error((err as { detail?: string }).detail || "Error al registrar");
  }
  const data = (await res.json()) as { access_token: string };
  setAccessToken(data.access_token);
  return data.access_token;
}

export async function logout(): Promise<void> {
  try {
    await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
      headers: _accessToken ? { Authorization: `Bearer ${_accessToken}` } : {},
    });
  } catch {
    // Network errors on logout are acceptable — local clear is what matters
  }
  setAccessToken(null);
  getAuthChannel()?.postMessage({ type: "LOGOUT" });
}

/**
 * Attempt to restore the session from the refresh-token cookie.
 *
 * Single-flight: concurrent calls share the same in-flight promise so we
 * never fire multiple /api/auth/refresh requests simultaneously.
 *
 * Returns the new access token on success, null on failure (cookie absent,
 * expired, or revoked).
 */
export function refresh(): Promise<string | null> {
  if (_refreshInflight) return _refreshInflight;

  _refreshInflight = (async (): Promise<string | null> => {
    try {
      const res = await fetch("/api/auth/refresh", {
        method: "POST",
        credentials: "include",
      });
      if (!res.ok) {
        setAccessToken(null);
        _refreshFailureListeners.forEach((fn) => fn());
        return null;
      }
      const data = (await res.json()) as { access_token: string };
      setAccessToken(data.access_token);
      return data.access_token;
    } catch {
      // Network failure — treat as unauthenticated, do not fire failure listeners
      // (offline != expired)
      setAccessToken(null);
      return null;
    } finally {
      _refreshInflight = null;
    }
  })();

  return _refreshInflight;
}

// ---------------------------------------------------------------------------
// authFetch — authenticated fetch with single-flight 401 retry
// ---------------------------------------------------------------------------

/**
 * Drop-in replacement for fetch() that:
 *  1. Injects Authorization: Bearer <access_token> if available.
 *  2. On 401 → attempts exactly ONE token refresh (single-flight shared lock).
 *  3. If refresh succeeds → retries the original request with the new token.
 *  4. If refresh fails   → returns the 401 response to the caller.
 *     (onRefreshFailure listeners will fire, triggering redirect.)
 *
 * Use this for ALL authenticated API calls.
 */
export async function authFetch(
  input: string,
  init: RequestInit = {}
): Promise<Response> {
  const doFetch = (token: string | null): Promise<Response> => {
    const headers = new Headers(init.headers);
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (!headers.has("Content-Type") && init.body && typeof init.body === "string") {
      headers.set("Content-Type", "application/json");
    }
    return fetch(input, { ...init, credentials: "include", headers });
  };

  const res = await doFetch(_accessToken);
  if (res.status !== 401) return res;

  // 401 → attempt refresh, then retry once
  const newToken = await refresh();
  if (!newToken) {
    // Refresh failed — caller sees 401; listeners will redirect to login
    return res;
  }

  return doFetch(newToken);
}
