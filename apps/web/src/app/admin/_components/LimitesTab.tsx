"use client";

import { useEffect, useState } from "react";
import { Gauge, Loader2, AlertTriangle, Upload, KeyRound, Activity } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";

interface RateLimitRow {
  plan: string;
  requests_per_minute: number;
  requests_per_day: number | null;
}

interface LimitsConfig {
  rate_limits: RateLimitRow[];
  tier_limits_per_day: Record<string, Record<string, number>>;
  upload: { max_bytes: number; max_mb: number; accepted_formats: string[] };
  auth: {
    access_token_minutes: number;
    refresh_token_days: number;
    login_rate_window_seconds: number;
    oauth_state_max_age_seconds: number;
  };
}

function fmt(n: number | null): string {
  if (n === null) return "∞";
  if (n === -1) return "∞";
  return n.toLocaleString("es-PE");
}

export function LimitesTab() {
  const { authFetch } = useAuth();
  const [data, setData] = useState<LimitsConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void authFetch("/api/admin/config/limits", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then((d: LimitsConfig) => setData(d))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [authFetch]);

  if (loading)
    return (
      <div className="w-full px-4 py-12 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-primary" />
      </div>
    );
  if (error || !data)
    return (
      <div className="w-full px-4 py-6">
        <div className="bg-red-500/10 border border-red-400/20 text-red-300 rounded-xl px-4 py-3 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          {error ?? "Error cargando límites."}
        </div>
      </div>
    );

  const tierKeys = Object.keys(data.tier_limits_per_day);
  const tierColumns = ["tier_1", "tier_2", "tier_3", "tier_4"];
  const tierLabels: Record<string, string> = {
    tier_1: "Económico",
    tier_2: "Standard",
    tier_3: "Premium",
    tier_4: "Ultra",
  };

  return (
    <div className="w-full px-4 py-6 sm:py-8 lg:px-6 xl:px-8 space-y-8">
      <header className="flex items-center gap-3">
        <div className="w-11 h-11 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
          <Gauge className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="font-['Newsreader'] text-2xl font-bold text-primary">Límites & Cuotas</h2>
          <p className="text-xs text-on-surface/50">
            Rate limits, cuotas por tier de modelo, uploads y TTL de sesiones.
          </p>
        </div>
      </header>

      {/* Rate limits */}
      <section>
        <div className="flex items-center gap-2 mb-3">
          <Activity className="w-4 h-4 text-on-surface/40" />
          <h3 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40">
            Rate limits por plan
          </h3>
        </div>
        <div
          className="bg-surface-container-low rounded-2xl overflow-hidden"
          style={{ border: "1px solid rgba(79,70,51,0.15)" }}
        >
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-on-surface/10">
                <th className="text-left text-[10px] uppercase tracking-[0.15em] text-on-surface/40 px-5 py-3">Plan</th>
                <th className="text-right text-[10px] uppercase tracking-[0.15em] text-on-surface/40 px-5 py-3">RPM</th>
                <th className="text-right text-[10px] uppercase tracking-[0.15em] text-on-surface/40 px-5 py-3">RPD</th>
              </tr>
            </thead>
            <tbody>
              {data.rate_limits.map((r) => (
                <tr key={r.plan} className="border-b border-on-surface/5 last:border-0">
                  <td className="px-5 py-3 text-on-surface capitalize">{r.plan}</td>
                  <td className="px-5 py-3 text-right font-mono text-on-surface/80">{fmt(r.requests_per_minute)}</td>
                  <td className="px-5 py-3 text-right font-mono text-on-surface/80">{fmt(r.requests_per_day)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Tier limits per plan */}
      <section>
        <h3 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-3">
          Límites por tier de modelo (consultas/día)
        </h3>
        <div
          className="bg-surface-container-low rounded-2xl overflow-hidden"
          style={{ border: "1px solid rgba(79,70,51,0.15)" }}
        >
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-on-surface/10">
                <th className="text-left text-[10px] uppercase tracking-[0.15em] text-on-surface/40 px-5 py-3">Plan</th>
                {tierColumns.map((tc) => (
                  <th
                    key={tc}
                    className="text-right text-[10px] uppercase tracking-[0.15em] text-on-surface/40 px-5 py-3"
                  >
                    {tierLabels[tc]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tierKeys.map((plan) => (
                <tr key={plan} className="border-b border-on-surface/5 last:border-0">
                  <td className="px-5 py-3 text-on-surface capitalize">{plan}</td>
                  {tierColumns.map((tc) => {
                    const v = data.tier_limits_per_day[plan]?.[tc] ?? 0;
                    const isDisabled = v === 0;
                    return (
                      <td key={tc} className="px-5 py-3 text-right">
                        <span
                          className={`font-mono text-xs ${
                            isDisabled ? "text-on-surface/20" : v === -1 ? "text-emerald-300" : "text-on-surface"
                          }`}
                        >
                          {isDisabled ? "—" : fmt(v)}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[10px] text-on-surface/40 mt-2">
          "—" = tier no disponible para ese plan · "∞" = ilimitado
        </p>
      </section>

      {/* Upload */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          className="bg-surface-container-low rounded-xl p-5"
          style={{ border: "1px solid rgba(79,70,51,0.15)" }}
        >
          <div className="flex items-center gap-2 mb-3">
            <Upload className="w-4 h-4 text-on-surface/40" />
            <h3 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40">Subida de archivos</h3>
          </div>
          <p className="font-['Newsreader'] text-2xl font-bold text-primary mb-1">
            {data.upload.max_mb} MB
          </p>
          <p className="text-xs text-on-surface/50 mb-3">tamaño máximo por archivo</p>
          <div className="flex flex-wrap gap-1.5">
            {data.upload.accepted_formats.map((f) => (
              <span
                key={f}
                className="text-[10px] uppercase tracking-[0.15em] bg-surface px-2 py-1 rounded-md text-on-surface/60 border border-on-surface/10"
              >
                {f}
              </span>
            ))}
          </div>
        </div>

        <div
          className="bg-surface-container-low rounded-xl p-5"
          style={{ border: "1px solid rgba(79,70,51,0.15)" }}
        >
          <div className="flex items-center gap-2 mb-3">
            <KeyRound className="w-4 h-4 text-on-surface/40" />
            <h3 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40">Tokens / sesiones</h3>
          </div>
          <dl className="space-y-2 text-xs">
            <div className="flex justify-between">
              <dt className="text-on-surface/60">Access token TTL</dt>
              <dd className="font-mono text-on-surface">{data.auth.access_token_minutes} min</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-on-surface/60">Refresh token TTL</dt>
              <dd className="font-mono text-on-surface">{data.auth.refresh_token_days} días</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-on-surface/60">Login rate window</dt>
              <dd className="font-mono text-on-surface">{data.auth.login_rate_window_seconds}s</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-on-surface/60">OAuth state TTL</dt>
              <dd className="font-mono text-on-surface">{data.auth.oauth_state_max_age_seconds}s</dd>
            </div>
          </dl>
        </div>
      </section>
    </div>
  );
}
