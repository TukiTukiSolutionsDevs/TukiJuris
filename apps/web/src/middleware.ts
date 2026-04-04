import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Pages that don't require auth (client-side auth guard in AppLayout handles the rest)
const PUBLIC_PATHS = [
  "/landing",
  "/auth/login",
  "/auth/register",
  "/auth/callback",
  "/auth/reset-password",
  "/compartido",
  "/onboarding",
  "/status",
  "/guia",
  "/docs",
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Allow Next.js internal routes and static assets
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/favicon") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // Note: This app uses localStorage for tokens (not cookies).
  // The middleware cannot read localStorage — it only runs on the server edge.
  // Real auth protection is handled client-side in AppLayout's useEffect guard.
  //
  // What we CAN do here: redirect unauthenticated root requests to /landing
  // by checking for a cookie-based hint (if ever implemented).
  // For now, we pass through and let AppLayout handle it.
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
