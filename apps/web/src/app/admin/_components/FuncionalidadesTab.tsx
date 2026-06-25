"use client";

import { useEffect, useState } from "react";
import { ToggleLeft, Loader2, AlertTriangle, Check, X } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";

interface PlanRow {
  id: string;
  display_name: string;
  features: Record<string, boolean>;
}

interface PlansConfig {
  plans: PlanRow[];
  all_feature_keys: string[];
}

const FEATURE_META: Record<string, { label: string; desc: string }> = {
  chat: { label: "Chat con IA legal", desc: "Acceso al asistente conversacional." },
  pdf_export: { label: "Exportar a PDF", desc: "Generar PDFs de conversaciones." },
  file_upload: { label: "Subida de archivos", desc: "Adjuntar PDF / DOCX al chat." },
  byok_enabled: { label: "BYOK (claves propias)", desc: "Usar OpenAI / Anthropic / etc. con clave del cliente." },
  team_seats: { label: "Asientos de equipo", desc: "Multi-usuario dentro de la organización." },
  priority_support: { label: "Soporte prioritario", desc: "Cola y SLA preferentes." },
};

export function FuncionalidadesTab() {
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
          {error ?? "Error cargando funcionalidades."}
        </div>
      </div>
    );

  return (
    <div className="w-full px-4 py-6 sm:py-8 lg:px-6 xl:px-8 space-y-6">
      <header className="flex items-center gap-3">
        <div className="w-11 h-11 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
          <ToggleLeft className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="font-['Newsreader'] text-2xl font-bold text-primary">Funcionalidades por plan</h2>
          <p className="text-xs text-on-surface/50">
            Matriz de feature flags · {data.all_feature_keys.length} funcionalidades × {data.plans.length} planes
          </p>
        </div>
      </header>

      <div
        className="bg-surface-container-low rounded-2xl overflow-hidden"
        style={{ border: "1px solid rgba(79,70,51,0.15)" }}
      >
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-on-surface/10">
              <th className="text-left text-[10px] uppercase tracking-[0.15em] text-on-surface/40 px-5 py-3">
                Funcionalidad
              </th>
              {data.plans.map((p) => (
                <th
                  key={p.id}
                  className="text-center text-[10px] uppercase tracking-[0.15em] text-on-surface/40 px-5 py-3"
                >
                  {p.display_name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.all_feature_keys.map((f) => {
              const meta = FEATURE_META[f] ?? { label: f, desc: "" };
              return (
                <tr key={f} className="border-b border-on-surface/5 last:border-0">
                  <td className="px-5 py-4">
                    <p className="font-medium text-sm text-on-surface">{meta.label}</p>
                    <p className="text-[11px] text-on-surface/40 mt-0.5">{meta.desc}</p>
                    <p className="font-mono text-[10px] text-on-surface/30 mt-1">{f}</p>
                  </td>
                  {data.plans.map((p) => (
                    <td key={p.id} className="px-5 py-4 text-center">
                      {p.features[f] ? (
                        <span className="inline-flex w-7 h-7 rounded-full bg-emerald-400/10 border border-emerald-400/20 items-center justify-center">
                          <Check className="w-3.5 h-3.5 text-emerald-300" />
                        </span>
                      ) : (
                        <span className="inline-flex w-7 h-7 rounded-full bg-on-surface/5 border border-on-surface/10 items-center justify-center">
                          <X className="w-3.5 h-3.5 text-on-surface/20" />
                        </span>
                      )}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-on-surface/40 italic">
        Edición requerida en <code className="bg-surface-container-low px-1 py-0.5 rounded">app/config/plans.py</code>.
        Migración a DB pendiente para edición en vivo.
      </p>
    </div>
  );
}
