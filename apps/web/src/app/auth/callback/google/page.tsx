"use client";

import { Suspense, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Scale, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { decodeAccessClaims } from "@/lib/auth/jwt";
import { resolvePostLoginDestination } from "@/lib/auth/redirects";
// OAuth callbacks do a hard redirect so AuthContext boots fresh with the new cookie.

function GoogleCallbackInner() {
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state");

    if (!code) {
      toast.error("No se recibio el codigo de autorizacion de Google.");
      router.push("/login?error=oauth_failed");
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
          toast.error(data.detail ?? "Error al autenticar con Google.");
          router.push("/login?error=oauth_failed");
          return;
        }

        const data = await res.json();

        // Decode is_admin from the access token for role-based redirect (no extra RTT).
        const claims = decodeAccessClaims(data.access_token ?? "");
        const isAdmin = claims?.is_admin === true;
        const returnto = data.returnto ?? null;

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

        router.push(
          resolvePostLoginDestination(returnto, isAdmin, onboardingCompleted),
        );
      } catch {
        toast.error("No se pudo conectar con el servidor. Intenta de nuevo.");
        router.push("/login?error=oauth_failed");
      }
    };

    exchange();
  }, [searchParams]);

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
