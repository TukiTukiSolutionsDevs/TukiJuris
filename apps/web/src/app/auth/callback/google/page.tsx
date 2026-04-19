"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Scale, Loader2, AlertCircle } from "lucide-react";
import Link from "next/link";
import { decodeAccessClaims } from "@/lib/auth/jwt";
import { resolvePostLoginDestination } from "@/lib/auth/redirects";
// OAuth callbacks do a hard redirect so AuthContext boots fresh with the new cookie.

function GoogleCallbackInner() {
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state");

    if (!code) {
      setError("No se recibio el codigo de autorizacion de Google.");
      return;
    }

    const exchange = async () => {
      try {
        const res = await fetch("/api/auth/oauth/google/callback", {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code, state: state ?? "" }),
        });

        if (!res.ok) {
          const data = await res.json().catch(() => ({ detail: "Error desconocido" }));
          setError(data.detail ?? "Error al autenticar con Google.");
          return;
        }

        const data = await res.json();

        // Decode is_admin from the access token for role-based redirect (no extra RTT).
        const claims = decodeAccessClaims(data.access_token ?? "");
        const isAdmin = claims?.is_admin === true;
        const returnTo = searchParams.get("returnTo");

        // Check server-side onboarding flag — not in JWT, requires /me call.
        let onboardingCompleted = true; // optimistic default → skip onboarding gate on /me failure
        try {
          const meRes = await fetch("/api/auth/me", {
            credentials: "include",
            headers: { Authorization: `Bearer ${data.access_token}` },
          });
          if (meRes.ok) {
            const me = await meRes.json();
            onboardingCompleted = Boolean(me.onboarding_completed);
          }
        } catch {
          // If /me fails, proceed to role-based redirect — non-blocking
        }

        window.location.replace(
          resolvePostLoginDestination(returnTo, isAdmin, onboardingCompleted),
        );
      } catch {
        setError("No se pudo conectar con el servidor. Intenta de nuevo.");
      }
    };

    exchange();
  }, [searchParams]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <div className="w-full max-w-sm text-center">
          <div className="w-14 h-14 bg-red-500/10 border border-red-500/30 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-400" />
          </div>
          <h1 className="text-xl font-semibold text-white mb-2">Error de autenticacion</h1>
          <p className="text-sm text-[#9CA3AF] mb-6">{error}</p>
          <Link
            href="/auth/login"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#1A1A22] hover:bg-[#2A2A35] text-sm text-[#F5F5F5] rounded-xl transition-colors"
          >
            Volver al inicio de sesion
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="text-center">
        <div className="w-14 h-14 bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Scale className="w-8 h-8 text-white" />
        </div>
        <div className="flex items-center justify-center gap-2 text-[#9CA3AF] text-sm">
          <Loader2 className="w-4 h-4 animate-spin" />
          Autenticando con Google...
        </div>
      </div>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <GoogleCallbackInner />
    </Suspense>
  );
}
