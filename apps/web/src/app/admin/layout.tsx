"use client";

/**
 * Admin route guard — client-side role enforcement.
 *
 * Middleware (middleware.ts) handles the coarse "logged in?" check via the
 * tk_session cookie. THIS layout handles the fine "is admin?" check using the
 * decoded is_admin claim from the in-memory access token via AuthContext.
 *
 * Rendering contract:
 *  - isLoading          → neutral skeleton (prevents protected data flash)
 *  - !isAuthenticated   → redirect to /auth/login?returnTo=<current path>
 *  - isAuthenticated && !isAdmin → redirect to /  (user default route)
 *  - isAdmin            → render children
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/AuthContext";
import { ROUTE_AFTER_LOGIN_USER, ROUTE_LOGIN } from "@/lib/constants";

export default function AdminRouteLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isLoading, user } = useAuth();
  const router = useRouter();

  const isAuthenticated = user !== null;
  const isAdmin = user?.isAdmin === true;

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated) {
      // Middleware should have caught this first, but defense in depth.
      const returnTo =
        typeof window !== "undefined"
          ? encodeURIComponent(window.location.pathname)
          : "%2Fadmin";
      router.replace(`${ROUTE_LOGIN}?returnTo=${returnTo}`);
      return;
    }

    if (!isAdmin) {
      router.replace(ROUTE_AFTER_LOGIN_USER);
    }
  }, [isLoading, isAuthenticated, isAdmin, router]);

  // Render a neutral skeleton while loading or before guard resolves.
  // No protected content is painted until isAdmin is confirmed.
  if (isLoading || !isAuthenticated || !isAdmin) {
    return (
      <div
        aria-busy="true"
        aria-label="Cargando panel de administración"
        className="min-h-screen bg-background"
      />
    );
  }

  return <>{children}</>;
}
