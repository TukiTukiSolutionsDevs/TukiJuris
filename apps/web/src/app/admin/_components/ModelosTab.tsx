"use client";

import { useEffect, useState } from "react";
import { Cpu, Loader2, AlertTriangle, Zap, Star, Crown, Sparkles } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";

interface TierGroup {
  tier: number;
  label: string;
  models: string[];
}

interface FreeModel {
  id: string;
  provider: string;
  name: string;
  description: string;
  tier: string;
  cost_per_1k_tokens: number;
  is_platform_provided: boolean;
}

interface ModelsConfig {
  tiers: TierGroup[];
  free_tier_models: FreeModel[];
  default_provider: string;
  default_model: string;
  total_models: number;
}

const TIER_META: Record<number, { color: string; bg: string; border: string; icon: typeof Zap; cost: string }> = {
  1: { color: "text-emerald-300", bg: "bg-emerald-400/10", border: "border-emerald-400/20", icon: Zap, cost: "$0.001 – $0.01 / query" },
  2: { color: "text-blue-300", bg: "bg-blue-400/10", border: "border-blue-400/20", icon: Star, cost: "$0.01 – $0.03 / query" },
  3: { color: "text-violet-300", bg: "bg-violet-400/10", border: "border-violet-400/20", icon: Sparkles, cost: "$0.03 – $0.07 / query" },
  4: { color: "text-amber-300", bg: "bg-amber-400/10", border: "border-amber-400/20", icon: Crown, cost: "$0.08 – $0.12 / query" },
};

export function ModelosTab() {
  const { authFetch } = useAuth();
  const [data, setData] = useState<ModelsConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void authFetch("/api/admin/config/models", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then((d: ModelsConfig) => setData(d))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [authFetch]);

  if (loading) {
    return (
      <div className="w-full px-4 py-12 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-primary" />
      </div>
    );
  }
  if (error || !data) {
    return (
      <div className="w-full px-4 py-6">
        <div className="bg-red-500/10 border border-red-400/20 text-red-300 rounded-xl px-4 py-3 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          {error ?? "No se pudo cargar la configuración de modelos."}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full px-4 py-6 sm:py-8 lg:px-6 xl:px-8 space-y-8">
      <header className="space-y-2">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
            <Cpu className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="font-['Newsreader'] text-2xl font-bold text-primary">Modelos LLM</h2>
            <p className="text-xs text-on-surface/50">
              {data.total_models} modelos clasificados en 4 tiers — config en{" "}
              <code className="text-[10px] bg-surface-container-low px-1 py-0.5 rounded">app/services/llm_adapter.py</code>
            </p>
          </div>
        </div>
      </header>

      {/* Defaults */}
      <section
        className="bg-surface-container-low rounded-xl p-5"
        style={{ border: "1px solid rgba(79,70,51,0.15)" }}
      >
        <h3 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-3">
          Por defecto del sistema
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-on-surface/40 mb-1">Proveedor por defecto</p>
            <p className="font-mono text-sm text-on-surface">{data.default_provider}</p>
          </div>
          <div>
            <p className="text-xs text-on-surface/40 mb-1">Modelo por defecto</p>
            <p className="font-mono text-sm text-on-surface">{data.default_model}</p>
          </div>
        </div>
      </section>

      {/* Free tier */}
      <section>
        <h3 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-3">
          Modelos gratuitos provistos por la plataforma
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          {data.free_tier_models.map((m) => (
            <div
              key={m.id}
              className="bg-surface-container-low rounded-xl p-4"
              style={{ border: "1px solid rgba(79,70,51,0.15)" }}
            >
              <div className="flex items-start justify-between mb-2">
                <span className="font-medium text-sm text-on-surface">{m.name}</span>
                <span className="text-[9px] uppercase tracking-[0.15em] text-emerald-300 bg-emerald-400/10 border border-emerald-400/20 rounded-full px-2 py-0.5">
                  Free
                </span>
              </div>
              <p className="text-xs text-on-surface/50 mb-2 leading-relaxed">{m.description}</p>
              <p className="font-mono text-[10px] text-on-surface/40">{m.id}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Tiers */}
      <section className="space-y-4">
        <h3 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40">
          Matriz de tiers ({data.total_models} modelos)
        </h3>
        {data.tiers.map((t) => {
          const meta = TIER_META[t.tier];
          const Icon = meta.icon;
          return (
            <div
              key={t.tier}
              className={`bg-surface-container-low rounded-xl p-5 border ${meta.border}`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-lg ${meta.bg} flex items-center justify-center`}>
                    <Icon className={`w-4 h-4 ${meta.color}`} />
                  </div>
                  <div>
                    <p className={`text-sm font-bold ${meta.color}`}>
                      Tier {t.tier} — {t.label}
                    </p>
                    <p className="text-[10px] text-on-surface/40">{meta.cost}</p>
                  </div>
                </div>
                <span className="text-xs text-on-surface/50">
                  {t.models.length} modelo{t.models.length === 1 ? "" : "s"}
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {t.models.map((m) => (
                  <div
                    key={m}
                    className="font-mono text-[11px] bg-surface px-3 py-2 rounded-lg text-on-surface/70 border border-on-surface/5"
                  >
                    {m}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </section>

      <p className="text-xs text-on-surface/40 italic">
        Edición de la matriz requiere migración a tabla DB y endpoints PUT — pendiente de Fase 3.
      </p>
    </div>
  );
}
