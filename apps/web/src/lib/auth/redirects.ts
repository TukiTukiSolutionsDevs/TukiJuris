/**
 * Post-login redirect helpers.
 * Pure functions — no side effects, no imports from React or Next.js.
 * Safe to use in both client components and edge middleware logic.
 */

import { ROUTE_AFTER_LOGIN_ADMIN, ROUTE_AFTER_LOGIN_USER } from '@/lib/constants';

// ---------------------------------------------------------------------------
// validateReturnTo
// ---------------------------------------------------------------------------

/**
 * Accept only same-origin absolute paths as `returnTo` redirect targets.
 *
 * Rejects:
 * - null / undefined / empty string
 * - non-`/` prefix (catches `http://`, `https://`, etc.)
 * - protocol-relative URLs (`//evil.com`)
 * - `/auth/login` and `/auth/register` (redirect loop prevention)
 *
 * Returns the raw string unchanged if valid, or null if rejected.
 */
export function validateReturnTo(raw: string | null | undefined): string | null {
  if (!raw) return null;
  if (!raw.startsWith('/')) return null;   // rejects http://, https://, ...
  if (raw.startsWith('//')) return null;   // rejects //evil.com
  if (raw.startsWith('/auth/login')) return null;    // redirect loop
  if (raw.startsWith('/auth/register')) return null; // redirect loop
  return raw;
}

// ---------------------------------------------------------------------------
// resolvePostLoginDestination
// ---------------------------------------------------------------------------

/**
 * Compute the destination after a successful authentication.
 *
 * Precedence (highest to lowest):
 *   1. `returnTo` — if present AND passes same-origin validation
 *   2. Role-based default: `/admin` for admins, `/` for regular users
 *
 * @param returnTo  Raw value from the `?returnTo=` query parameter (may be null).
 * @param isAdmin   Whether the freshly-authenticated user holds the admin role.
 */
export function resolvePostLoginDestination(
  returnTo: string | null | undefined,
  isAdmin: boolean,
): string {
  const safe = validateReturnTo(returnTo);
  if (safe) return safe;
  return isAdmin ? ROUTE_AFTER_LOGIN_ADMIN : ROUTE_AFTER_LOGIN_USER;
}
