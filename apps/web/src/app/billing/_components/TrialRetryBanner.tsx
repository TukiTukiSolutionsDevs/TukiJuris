"use client";

import { useState } from "react";
import { AlertTriangle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth/AuthContext";

// ---------------------------------------------------------------------------
// TrialRetryBanner — shown when trial.status === "charge_failed"
// Calls POST /api/trials/{trial_id}/retry-charge via authFetch.
// ---------------------------------------------------------------------------

interface TrialRetryBannerProps {
  trialId: string;
  onSuccess: () => void;
}

export function TrialRetryBanner({ trialId, onSuccess }: TrialRetryBannerProps) {
  const [pending, setPending] = useState(false);
  const { authFetch } = useAuth();

  const handleRetry = async () => {
    setPending(true);
    try {
      const res = await authFetch(`/api/trials/${trialId}/retry-charge`, {
        method: "POST",
      });

      if (res.ok) {
        toast.success("Cobro reintentado. Actualizando estado...");
        onSuccess();
        return;
      }

      if (res.status === 503) {
        toast.error("El sistema de prueba no está disponible en este momento.");
      } else {
        toast.error("No se pudo reintentar el cobro. Intentá nuevamente.");
      }
    } catch {
      toast.error("No se pudo reintentar el cobro. Intentá nuevamente.");
    } finally {
      setPending(false);
    }
  };

  return (
    <div
      className="flex items-start sm:items-center gap-3 bg-red-500/10 border border-red-500/30 rounded-lg px-5 py-4 mb-6"
      data-testid="trial-retry-banner"
      role="alert"
    >
      <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5 sm:mt-0" />
      <div className="flex-1">
        <p className="text-sm font-semibold text-red-300">Cobro del periodo de prueba fallido</p>
        <p className="text-xs text-red-300/70 mt-0.5">
          Hubo un problema al procesar el pago de tu periodo de prueba.
        </p>
      </div>
      <button
        onClick={handleRetry}
        disabled={pending}
        aria-busy={pending}
        data-testid="retry-charge-btn"
        className="shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-bold text-red-300 border border-red-400/30 hover:bg-red-500/10 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
      >
        {pending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
        Reintentar cobro
      </button>
    </div>
  );
}
