"use client";

import { useEffect, useState } from "react";
import { Tag, Loader2, AlertTriangle, Check, X } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";

interface PlanRow {
  id: string;
  display_name: string;
  features: Record<string, boolean>;
  queries_day: number;
  reasoning_queries_day: number;
  byok_enabled: boolean;
  base_price_cents: number;
  seat_price_cents: number;
  base_seats_included: number;
}

interface PlansConfig {
  plans: PlanRow[];
  all_feature_keys: string[];
  beta_hard_limits: Record<string, unknown>;
  beta_mode: boolean;
}

const FEATURE_LABELS: Record<string, string> = {
  chat: "Chat con IA",
  pdf_export: "Exportar PDF",
  file_upload: "Subir archivos",
  byok_enabled: "BYOK habilitado",
  team_seats: "Asientos de equipo",
  priority_support: "Soporte prioritario",
};

function formatCurrency(cents: number): string {
  return new Intl.NumberFormat("es-PE", {
    style: "currency",
    currency: "PEN",
    minimumFractionDigits: 2,
  }).format(cents / 100);
}

function formatLimit(n: number): string {
  if (n === -1) return "∞";
  return n.toLocaleString("es-PE");
}

export function PlanesTab() {
  const { authFetch } = useAuth();
  const [data, setData] = useState<PlansConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void authFetch("/api/admin/config/plans", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then((d: PlansConfig) => setData(d))
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
          {error ?? "No se pudo cargar la configuración de planes."}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full px-4 py-6 sm:py-8 lg:px-6 xl:px-8 space-y-8">
      <header>
        <div className="flex items-center gap-3 mb-2">
          <div className="w-11 h-11 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
            <Tag className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="font-['Newsreader'] text-2xl font-bold text-primary">Planes</h2>
            <p className="text-xs text-on-surface/50">
              {data.plans.length} planes definidos — config en{" "}
              <code className="text-[10px] bg-surface-container-low px-1 py-0.5 rounded">app/config/plans.py</code>
            </p>
          </div>
          {data.beta_mode && (
            <span className="ml-auto text-[10px] uppercase tracking-[0.15em] text-amber-300 bg-amber-400/10 border border-amber-400/20 rounded-full px-3 py-1">
              Beta mode activo
            </span>
          )}
        </div>
      </header>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {data.plans.map((p) => (
          <div
            key={p.id}
            className="bg-surface-container-low rounded-2xl p-6"
            style={{ border: "1px solid rgba(79,70,51,0.15)" }}
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="font-['Newsreader'] text-xl font-bold text-on-surface">
                  {p.display_name}
                </p>
                <p className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40">{p.id}</p>
              </div>
              {p.byok_enabled && (
                <span className="text-[9px] uppercase tracking-[0.15em] text-violet-300 bg-violet-400/10 border border-violet-400/20 rounded-full px-2 py-0.5">
                  BYOK
                </span>
              )}
            </div>

            <div className="mb-5">
              <p className="font-['Newsreader'] text-3xl font-bold text-primary">
                {formatCurrency(p.base_price_cents)}
                <span className="text-sm text-on-surface/40 font-sans">/mes</span>
              </p>
              {p.seat_price_cents > 0 && (
                <p className="text-xs text-on-surface/50 mt-1">
                  + {formatCurrency(p.seat_price_cents)}/asiento extra
                  <br />
                  <span className="text-on-surface/40">
                    ({p.base_seats_included} asientos incluidos)
                  </span>
                </p>
              )}
            </div>

            <div className="space-y-2 mb-5 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-on-surface/60">Consultas normales / día</span>
                <span className="font-mono text-on-surface">{formatLimit(p.queries_day)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-on-surface/60">Razonamiento / día</span>
                <span className="font-mono text-on-surface">{formatLimit(p.reasoning_queries_day)}</span>
              </div>
            </div>

            <div className="space-y-1.5 border-t border-on-surface/10 pt-4">
              {data.all_feature_keys.map((f) => (
                <div key={f} className="flex items-center gap-2 text-xs">
                  {p.features[f] ? (
                    <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  ) : (
                    <X className="w-3.5 h-3.5 text-on-surface/20 shrink-0" />
                  )}
                  <span className={p.features[f] ? "text-on-surface" : "text-on-surface/30"}>
                    {FEATURE_LABELS[f] ?? f}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </section>

      <section
        className="bg-amber-400/5 border border-amber-400/20 rounded-xl p-4"
      >
        <p className="text-[10px] uppercase tracking-[0.2em] text-amber-300 mb-2">
          Beta hard limits
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          {Object.entries(data.beta_hard_limits).map(([k, v]) => (
            <div key={k}>
              <p className="text-on-surface/40">{k}</p>
              <p className="font-mono text-on-surface">{String(v)}</p>
            </div>
          ))}
        </div>
      </section>

      <p className="text-xs text-on-surface/40 italic">
        Edición de planes requiere migración a tabla DB. Por ahora cualquier cambio se hace en código.
      </p>
    </div>
  );
}
