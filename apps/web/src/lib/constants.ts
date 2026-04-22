/**
 * Route and auth constants — single source of truth for the frontend.
 * Import from here; never hard-code path strings in components.
 */

// ---------------------------------------------------------------------------
// Post-login destinations
// ---------------------------------------------------------------------------

export const ROUTE_AFTER_LOGIN_ADMIN = '/admin';
// The chat UI lives at `/` (see apps/web/src/app/page.tsx). The ./chat
// subdirectory holds components, not a route. Do NOT change this to '/chat' —
// that path returns 404 and causes a post-login redirect loop.
export const ROUTE_AFTER_LOGIN_USER = '/';

// ---------------------------------------------------------------------------
// Auth entry points
// ---------------------------------------------------------------------------

export const ROUTE_LOGIN = '/auth/login';
export const ROUTE_LANDING = '/landing';

// ---------------------------------------------------------------------------
// Public paths (middleware allowlist — no session required)
// Keep in sync with the app router pages.
// ---------------------------------------------------------------------------

export const PUBLIC_PATHS = [
  '/landing',
  '/auth/login',
  '/auth/register',
  '/auth/callback',
  '/auth/reset-password',
  '/compartido',
  '/status',
  '/guia',
  '/docs',
  '/caracteristicas',
  '/precios',
] as const;

// ---------------------------------------------------------------------------
// Auth pages that should bounce already-authenticated users away
// ---------------------------------------------------------------------------

export const AUTH_BOUNCE_PATHS = ['/auth/login', '/auth/register'] as const;

// ---------------------------------------------------------------------------
// Admin-only path prefixes — checked by BOTH middleware (tk_admin cookie) and
// client-side guards. Add any new admin-gated paths here.
// ---------------------------------------------------------------------------

export const ADMIN_PATH_PREFIXES = ['/admin', '/analytics'] as const;

// ---------------------------------------------------------------------------
// Admin marker cookie — written by the backend on every login/refresh when
// user.is_admin is True; actively deleted for non-admins. Edge middleware
// reads this to gate ADMIN_PATH_PREFIXES without decoding a JWT.
// ---------------------------------------------------------------------------

export const ADMIN_MARKER_COOKIE = 'tk_admin';
export const ADMIN_MARKER_VALUE = '1';

// ---------------------------------------------------------------------------
// Session marker cookie
//
// Non-sensitive boolean presence hint written by the backend (Path=/, SameSite=Lax)
// alongside the httpOnly refresh_token (Path=/api/auth). Edge middleware reads
// THIS cookie because the refresh_token scope makes it invisible at paths like
// /, /admin, /chat. Carries zero secrets — see middleware.ts for full rationale.
// ---------------------------------------------------------------------------

export const SESSION_MARKER_COOKIE = 'tk_session';
