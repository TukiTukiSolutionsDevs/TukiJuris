"use client";

import { useState, useEffect } from "react";
import { Loader2, Zap } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { fetchCurrentTrial, startTrial, type Trial } from "@/lib/api/trial";
import { TrialStatusBadge } from "./TrialStatusBadge";

function daysRemaining(endsAt: string): number {
  const diff = new Date(endsAt).getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
}

export function StartTrialButton() {
  const { authFetch } = useAuth();
  const [trial, setTrial] = useState<Trial | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCurrentTrial(authFetch)
      .then(setTrial)
      .catch(() => setTrial(null))
      .finally(() => setLoading(false));
  }, [authFetch]);

  async function handleStart() {
    setStarting(true);
    setError(null);
    try {
      const t = await startTrial(authFetch);
      setTrial(t);
    } catch {
      setError("No se pudo iniciar la prueba. Intenta nuevamente.");
    } finally {
      setStarting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-on-surface/40" data-testid="trial-loading">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm">Cargando…</span>
      </div>
    );
  }

  if (trial) {
    const days = daysRemaining(trial.ends_at);
    return (
      <div className="flex items-center gap-3" data-testid="trial-status">
        <TrialStatusBadge status={trial.status} />
        {trial.status === "active" && (
          <span className="text-xs text-on-surface/60">
            {days} día{days !== 1 ? "s" : ""} restante{days !== 1 ? "s" : ""}
          </span>
        )}
      </div>
    );
  }

  return (
    <div>
      <button
        onClick={handleStart}
        disabled={starting}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-on-primary text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
        data-testid="start-trial-btn"
      >
        {starting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
        Iniciar prueba gratuita
      </button>
      {error && (
        <p className="mt-2 text-xs text-red-600" data-testid="trial-error">
          {error}
        </p>
      )}
    </div>
  );
}
