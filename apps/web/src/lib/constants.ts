/**
 * Route and auth constants — single source of truth for the frontend.
 * Import from here; never hard-code path strings in components.
 */

// ---------------------------------------------------------------------------
// Post-login destinations
// ---------------------------------------------------------------------------

export const ROUTE_AFTER_LOGIN_ADMIN = '/admin';
export const ROUTE_AFTER_LOGIN_USER = '/chat';

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
  '/onboarding',
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
// Admin-only path prefixes (client-side guard enforces; middleware only
// checks session presence — see middleware.ts for the trade-off comment).
// ---------------------------------------------------------------------------

export const ADMIN_PATH_PREFIXES = ['/admin'] as const;

// ---------------------------------------------------------------------------
// Session marker cookie
//
// Non-sensitive boolean presence hint written by the backend (Path=/, SameSite=Lax)
// alongside the httpOnly refresh_token (Path=/api/auth). Edge middleware reads
// THIS cookie because the refresh_token scope makes it invisible at paths like
// /, /admin, /chat. Carries zero secrets — see middleware.ts for full rationale.
// ---------------------------------------------------------------------------

export const SESSION_MARKER_COOKIE = 'tk_session';
