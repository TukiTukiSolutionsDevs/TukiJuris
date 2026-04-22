/**
 * Auth navigation helpers.
 * Pure functions — no dependency on token storage or fetch.
 */

/**
 * Build a safe returnTo path from Next.js pathname + search params.
 * Always returns a string that starts with "/" so it is safe to use as a
 * same-origin redirect target.
 */
export function buildReturnTo(
  pathname?: string | null,
  search?: string | null
): string {
  const safePathname =
    pathname && pathname.startsWith("/") ? pathname : "/";
  const safeSearch =
    search && search.startsWith("?") ? search : "";
  return `${safePathname}${safeSearch}`;
}

/**
 * Redirect the browser to a public (unauthenticated) page.
 *
 * - "missing" → /landing  (user was never logged in)
 * - "expired" → /auth/login?reason=expired[&returnTo=...]
 * - "offline"  → /auth/login?reason=offline[&returnTo=...]
 */
export function redirectToPublic(
  reason: "missing" | "expired" | "offline",
  returnTo?: string
): void {
  if (typeof window === "undefined") return;

  if (reason === "missing") {
    // Already on /landing → skip redirect to prevent boot-refresh loops
    // when the AuthProvider fires onRefreshFailure on a public page.
    if (window.location.pathname === "/landing") return;
    window.location.href = "/landing";
    return;
  }

  // Already on /auth/login → skip redirect. The refresh-failure listener
  // fires a redirect even when we're already on the login page; without
  // this guard, window.location.href triggers a reload, the AuthProvider
  // remounts, refresh() runs again, fails, and we loop forever (and
  // saturate the backend /auth/refresh rate limiter to 429).
  if (window.location.pathname === "/auth/login") return;

  const url = new URL("/auth/login", window.location.origin);
  if (returnTo) url.searchParams.set("returnTo", returnTo);
  url.searchParams.set("reason", reason);
  window.location.href = url.toString();
}
