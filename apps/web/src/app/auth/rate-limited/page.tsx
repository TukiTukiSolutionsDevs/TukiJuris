"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Clock, RefreshCw } from "lucide-react";

/**
 * Rate-limited interstitial.
 *
 * When `authClient.refresh()` hits a 429 from `/api/auth/refresh` (the
 * user slammed F5, opened too many tabs, or a background process is
 * polling too hard), we land the user here instead of flashing a blank
 * AppLayout or looping through the login bounce.
 *
 * Behaviour:
 *   - Shows a friendly "vas muy rápido" card with a live countdown.
 *   - When the timer hits zero the page auto-reloads to `returnTo` (or
 *     `/` if absent). By then the sliding window has freed a slot and
 *     the boot refresh should succeed.
 *   - A manual "Reintentar ahora" button is shown but disabled until
 *     the timer elapses — lets the user feel in control without
 *     actually re-hammering the API before the window frees up.
 *
 * URL contract:
 *   /auth/rate-limited?retry=<seconds>&returnTo=<same-origin-path>
 *
 * Defaults: retry=60 (matches the refresh bucket's 1-min window),
 * returnTo=/.
 */

const DEFAULT_RETRY_SECONDS = 60;

function RateLimitedInner() {
  const searchParams = useSearchParams();

  const retryParam = Number.parseInt(searchParams.get("retry") ?? "", 10);
  const retrySeconds = Number.isFinite(retryParam) && retryParam > 0
    ? Math.min(retryParam, 300)  // cap at 5 min so a bad param never traps the user
    : DEFAULT_RETRY_SECONDS;

  const returnToRaw = searchParams.get("returnTo");
  const returnTo =
    returnToRaw &&
    returnToRaw.startsWith("/") &&
    !returnToRaw.startsWith("//") &&
    !returnToRaw.startsWith("/auth/rate-limited")
      ? returnToRaw
      : "/";

  const [remaining, setRemaining] = useState(retrySeconds);

  useEffect(() => {
    if (remaining <= 0) {
      // Auto-recover — by now the 1-min sliding window should have freed
      // at least one slot. Use location.href (not router.push) to blow
      // away the in-memory authClient state and force a fresh boot.
      window.location.href = returnTo;
      return;
    }
    const id = setInterval(() => setRemaining((s) => s - 1), 1000);
    return () => clearInterval(id);
  }, [remaining, returnTo]);

  const canRetry = remaining <= 0;

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full bg-primary-container/5 blur-[120px]" />
      </div>

      <div className="relative w-full max-w-md">
        <div className="bg-[#111116] border border-[rgba(79,70,51,0.15)] rounded-lg px-8 py-10 text-center">
          <div className="w-16 h-16 bg-primary-container/10 border border-[rgba(79,70,51,0.15)] rounded-lg flex items-center justify-center mx-auto mb-6">
            <Clock className="w-8 h-8 text-primary-container" />
          </div>

          <h1 className="font-['Newsreader'] text-3xl text-on-surface mb-3">
            Vas muy rápido
          </h1>
          <p className="text-on-surface-variant text-sm leading-relaxed mb-2">
            Detectamos demasiadas peticiones en poco tiempo. Es una medida de
            seguridad para proteger tu sesión.
          </p>
          <p className="text-on-surface-variant text-sm leading-relaxed mb-8">
            Esperá unos segundos y volvé a intentar.
          </p>

          <div
            role="status"
            aria-live="polite"
            className="mb-6 font-['Newsreader'] text-5xl text-primary-container tabular-nums"
          >
            {remaining}
            <span className="ml-2 text-base text-on-surface-variant align-baseline">s</span>
          </div>

          <button
            type="button"
            disabled={!canRetry}
            onClick={() => {
              window.location.href = returnTo;
            }}
            className={`inline-flex items-center justify-center gap-2 w-full font-bold px-6 py-3 rounded-lg transition ${
              canRetry
                ? "bg-gradient-to-br from-primary to-primary-container text-on-primary hover:opacity-90"
                : "bg-surface-container-low text-on-surface/40 cursor-not-allowed"
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${canRetry ? "" : "opacity-40"}`} />
            {canRetry ? "Reintentar ahora" : `Disponible en ${remaining}s`}
          </button>

          <p className="text-[#4B5563] text-xs mt-5">
            Se reintenta automáticamente cuando el contador llegue a 0.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function RateLimitedPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-background">
          <div className="w-5 h-5 border-2 border-primary-container border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <RateLimitedInner />
    </Suspense>
  );
}
