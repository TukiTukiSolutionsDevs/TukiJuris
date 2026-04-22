import { NextResponse, type NextRequest } from 'next/server';
import {
  PUBLIC_PATHS,
  AUTH_BOUNCE_PATHS,
  ADMIN_PATH_PREFIXES,
  ADMIN_MARKER_COOKIE,
  ADMIN_MARKER_VALUE,
  ROUTE_LOGIN,
  ROUTE_AFTER_LOGIN_USER,
  SESSION_MARKER_COOKIE,
} from '@/lib/constants';

// ---------------------------------------------------------------------------
// Architecture note — cookie-based session and role gating
//
// `fix-auth-tokens` scopes the httpOnly refresh cookie to Path=/api/auth so it
// is never sent to app routes like /, /admin, or /chat. Edge middleware runs on
// ALL matched paths and therefore CANNOT see `refresh_token`.
//
// Two marker cookies (both httpOnly, Path=/, written by the backend):
//  - `tk_session=1`  (SameSite=Lax)    — "is this user logged in?"
//  - `tk_admin=1`    (SameSite=Strict)  — "is this user an admin?"
//    tk_admin is SET on login/register/refresh for admin users and actively
//    DELETED for non-admins, so it cannot be stale-elevated.
//
// Security properties:
//  - Neither cookie carries JWT material — an attacker who forges them still
//    gets a 401/403 on the first real API call (backend RBAC is authoritative).
//  - SameSite=Strict on tk_admin prevents it being sent on cross-site navigations
//    (tighter than tk_session's Lax).
//  - Four-layer model: middleware = "logged in? admin?", /admin/layout.tsx =
//    client-side defence-in-depth, analytics page = useEffect guard,
//    backend RBAC = authoritative truth on every mutation.
// ---------------------------------------------------------------------------

const STATIC_PREFIXES = ['/_next', '/api', '/favicon'] as const;

function isStaticOrApi(pathname: string): boolean {
  return (
    (STATIC_PREFIXES as readonly string[]).some((p) => pathname.startsWith(p)) ||
    pathname.includes('.')
  );
}

function isPublic(pathname: string): boolean {
  return (PUBLIC_PATHS as readonly string[]).some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );
}

function isAuthBounce(pathname: string): boolean {
  return (AUTH_BOUNCE_PATHS as readonly string[]).some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );
}

function isAdminPath(pathname: string): boolean {
  return (ADMIN_PATH_PREFIXES as readonly string[]).some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );
}

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  // 1. Static assets and proxied API routes pass through unconditionally.
  if (isStaticOrApi(pathname)) return NextResponse.next();

  const hasSession = request.cookies.has(SESSION_MARKER_COOKIE);

  // 2. Public route — allow, but bounce authenticated users away from
  //    /auth/login and /auth/register so they don't see the login form again.
  if (isPublic(pathname)) {
    if (hasSession && isAuthBounce(pathname)) {
      const params = new URLSearchParams(request.nextUrl.search);
      const returnTo = params.get('returnTo');
      const url = request.nextUrl.clone();
      // Accept same-origin absolute paths only (same validation as validateReturnTo).
      url.pathname =
        returnTo &&
        returnTo.startsWith('/') &&
        !returnTo.startsWith('//') &&
        !returnTo.startsWith('/auth/')
          ? returnTo
          : ROUTE_AFTER_LOGIN_USER;
      url.search = '';
      return NextResponse.redirect(url);
    }
    return NextResponse.next();
  }

  // 3. Protected route without a session → redirect to login with returnTo.
  if (!hasSession) {
    const url = request.nextUrl.clone();
    url.pathname = ROUTE_LOGIN;
    url.search = `?returnTo=${encodeURIComponent(pathname + search)}`;
    return NextResponse.redirect(url);
  }

  // 4. Admin-only path — verify tk_admin marker cookie.
  //    tk_admin=1 is set by the backend on login/refresh for admin users and
  //    actively deleted for non-admins, so it cannot be stale-elevated.
  if (isAdminPath(pathname)) {
    const isAdmin =
      request.cookies.get(ADMIN_MARKER_COOKIE)?.value === ADMIN_MARKER_VALUE;
    if (!isAdmin) {
      const url = request.nextUrl.clone();
      url.pathname = ROUTE_AFTER_LOGIN_USER;
      url.search = '';
      return NextResponse.redirect(url);
    }
  }

  // 5. Protected route with a valid session (and admin check passed if needed).
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
