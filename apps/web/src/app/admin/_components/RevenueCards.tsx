"use client";

/**
 * RevenueCards — MRR/ARR + per-plan breakdown for the admin SaaS panel.
 *
 * Visibility logic (defense-in-depth on the UI side):
 *   1. Only mounted when the parent has determined the user likely has billing:read.
 *   2. If the API call returns 403 the component unmounts silently (no toast).
 *
 * Data fetching mirrors the admin/page.tsx pattern: plain authFetch, no extra library.
 * Pattern comment per T2.2 requirement.
 */

import { useState, useEffect, useCallback } from "react";
import { TrendingUp, DollarSign, BarChart3, AlertCircle, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { fetchRevenue, type RevenueData } from "@/lib/api/admin";

const PLAN_DISPLAY: Record<string, string> = {
  free: "Gratuito",
  pro: "Profesional",
  studio: "Estudio",
};

function cents(c: number): string {
  return `S/ ${(c / 100).toLocaleString("es-PE", { minimumFractionDigits: 2 })}`;
}

export function RevenueCards() {
  const { authFetch } = useAuth();
  const [data, setData] = useState<RevenueData | null>(null);
  const [hidden, setHidden] = useState(false); // 403 → hide silently
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const d = await fetchRevenue(authFetch);
      setData(d);
    } catch (err: unknown) {
      const status = (err as { status?: number }).status;
      if (status === 403) {
        // User lacks billing:read — unmount silently per design §5
        setHidden(true);
      } else {
        setError("No se pudo cargar los datos de ingresos.");
      }
    } finally {
      setLoading(false);
    }
  }, [authFetch]);

  useEffect(() => {
    load();
  }, [load]);

  if (hidden) return null;

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-6 text-sm text-on-surface/40">
        <Loader2 className="w-4 h-4 animate-spin" />
        Cargando ingresos…
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 py-4 text-sm text-red-400">
        <AlertCircle className="w-4 h-4 shrink-0" />
        {error}
      </div>
    );
  }

  if (!data) return null;

  return (
    <div>
      <h2 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-4 flex items-center gap-2">
        <TrendingUp className="w-3.5 h-3.5" />
        Ingresos recurrentes
        <span className="ml-auto text-[9px] normal-case tracking-normal text-on-surface/30">
          Fuente: {data.source}
        </span>
      </h2>

      {/* MRR / ARR cards */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4 mb-4">
        <div
          className="bg-surface-container-low rounded-lg p-4 sm:p-5"
          style={{ border: "1px solid rgba(79,70,51,0.15)" }}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] uppercase tracking-[0.1em] text-on-surface/40">
              MRR mensual
            </span>
            <DollarSign className="w-4 h-4 text-primary/50" />
          </div>
          <p className="font-['Newsreader'] text-3xl font-bold text-primary">
            {cents(data.mrr_cents)}
          </p>
        </div>

        <div
          className="bg-surface-container-low rounded-lg p-4 sm:p-5"
          style={{ border: "1px solid rgba(79,70,51,0.15)" }}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] uppercase tracking-[0.1em] text-on-surface/40">
              ARR anual
            </span>
            <BarChart3 className="w-4 h-4 text-primary/50" />
          </div>
          <p className="font-['Newsreader'] text-3xl font-bold text-primary">
            {cents(data.arr_cents)}
          </p>
        </div>
      </div>

      {/* Per-plan breakdown */}
      {data.breakdown.length > 0 && (
        <div
          className="bg-surface-container-low rounded-lg overflow-hidden"
          style={{ border: "1px solid rgba(79,70,51,0.15)" }}
        >
          <div className="overflow-x-auto">
            <table className="w-full min-w-[400px] text-sm">
              <thead>
                <tr>
                  <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                    Plan
                  </th>
                  <th className="text-right text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                    Orgs activas
                  </th>
                  <th className="text-right text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                    Ingreso/mes
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.breakdown.map((item, idx) => (
                  <tr
                    key={item.plan}
                    className={idx % 2 === 0 ? "bg-surface" : "bg-surface-container-low"}
                  >
                    <td className="px-5 py-3 text-sm font-medium text-on-surface">
                      {PLAN_DISPLAY[item.plan] ?? item.display_name}
                    </td>
                    <td className="px-5 py-3 text-right text-sm text-on-surface/60">
                      {item.org_count.toLocaleString("es-PE")}
                    </td>
                    <td className="px-5 py-3 text-right text-sm font-semibold text-primary">
                      {cents(item.revenue_cents)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
