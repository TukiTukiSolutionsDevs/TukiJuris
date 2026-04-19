import { NextResponse, type NextRequest } from 'next/server';
import {
  PUBLIC_PATHS,
  AUTH_BOUNCE_PATHS,
  ROUTE_LOGIN,
  ROUTE_AFTER_LOGIN_USER,
  SESSION_MARKER_COOKIE,
} from '@/lib/constants';

// ---------------------------------------------------------------------------
// Architecture note — why we read `tk_session` and NOT `refresh_token`
//
// `fix-auth-tokens` scopes the httpOnly refresh cookie to Path=/api/auth so it
// is never sent to app routes like /, /admin, or /chat. Edge middleware runs on
// ALL matched paths and therefore CANNOT see `refresh_token`.
//
// Resolution: the backend writes a non-sensitive session marker cookie
// `tk_session=1` (Path=/, SameSite=Lax) in the same response as every
// refresh_token mutation (login, register, refresh rotation, OAuth callbacks,
// logout). This middleware reads that marker as a boolean presence hint.
//
// Security properties:
//  - `tk_session` carries ZERO secrets — it is not httpOnly deliberately.
//  - An attacker who sets `tk_session` manually bypasses this coarse gate but
//    their first protected API call (no valid Bearer token) returns 401 and
//    authFetch redirects them to login.
//  - Role (is_admin) enforcement is intentionally CLIENT-SIDE in
//    /admin/layout.tsx — the access token is in-memory and unreachable here.
//  - Three-layer model: middleware = "logged in?", /admin/layout.tsx = "admin?",
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

  // 4. Protected route with a session → allow through.
  //    /admin role-gating is handled client-side (see architecture note above).
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
