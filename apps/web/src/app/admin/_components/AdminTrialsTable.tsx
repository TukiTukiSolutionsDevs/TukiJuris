"use client";

/**
 * AdminTrialsTable — paginated admin view of all trials.
 *
 * - Mirrors InvoicesTable pattern: authFetch + useState/useEffect/useCallback.
 * - Silently unmounts on 403 (non-admin).
 * - Cancel action: PATCH /admin/trials/{id} → { action: "force_downgrade", reason: "..." }.
 */

import { useState, useEffect, useCallback } from "react";
import { Clock, Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { fetchAdminTrials, patchAdminTrial, type TrialAdminRow } from "@/lib/api/admin";
import { TrialStatusBadge } from "@/components/trials/TrialStatusBadge";
import { UsersPagination } from "./UsersPagination";

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}


export function AdminTrialsTable() {
  const { authFetch } = useAuth();
  const [items, setItems] = useState<TrialAdminRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [loading, setLoading] = useState(true);
  const [hidden, setHidden] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState<string | null>(null);

  const load = useCallback(
    async (p: number) => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchAdminTrials(authFetch, p, perPage);
        setItems(data.items);
        setTotal(data.total);
      } catch (err: unknown) {
        const status = (err as { status?: number }).status;
        if (status === 403) {
          setHidden(true);
        } else {
          setError("No se pudieron cargar los trials.");
        }
      } finally {
        setLoading(false);
      }
    },
    [authFetch, perPage],
  );

  useEffect(() => {
    load(page);
  }, [load, page]);

  async function handleCancel(id: string) {
    setCancelling(id);
    try {
      const updated = await patchAdminTrial(authFetch, id, {
        action: "force_downgrade",
        reason: "Admin cancelled trial",
      });
      setItems((prev) => prev.map((t) => (t.id === id ? updated : t)));
    } catch {
      // silently ignore — user can retry via refresh
    } finally {
      setCancelling(null);
    }
  }

  if (hidden) return null;

  return (
    <div
      className="bg-surface-container-low rounded-lg overflow-hidden"
      style={{ border: "1px solid rgba(79,70,51,0.15)" }}
      data-testid="admin-trials-table"
    >
      {/* Header */}
      <div
        className="p-5 flex items-center gap-2"
        style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
      >
        <Clock className="w-4 h-4 text-primary" />
        <h2 className="font-semibold text-sm text-on-surface">Trials</h2>
        <span className="ml-auto text-xs text-on-surface/30">{total} total</span>
        <button
          onClick={() => load(page)}
          className="ml-2 p-1 rounded hover:bg-surface-container-high transition-colors"
          aria-label="Recargar trials"
        >
          <RefreshCw className="w-3.5 h-3.5 text-on-surface/40" />
        </button>
      </div>

      {/* Body */}
      {loading ? (
        <div className="flex items-center justify-center py-10 gap-2 text-on-surface/40">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span className="text-sm">Cargando trials…</span>
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 p-5 text-red-600">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">{error}</span>
        </div>
      ) : items.length === 0 ? (
        <div className="py-10 text-center text-sm text-on-surface/40">
          No hay trials registrados.
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="bg-surface-container-low">
                  {["Usuario", "Estado", "Vence", "Plan", "Proveedor", "Acción"].map((h) => (
                    <th
                      key={h}
                      className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-4 sm:px-5 py-3"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.map((trial, i) => (
                  <tr
                    key={trial.id}
                    className={i % 2 === 0 ? "bg-surface-container-low" : "bg-surface-container"}
                  >
                    <td className="px-4 sm:px-5 py-3 font-mono text-xs text-on-surface/80">
                      {trial.user_id}
                    </td>
                    <td className="px-4 sm:px-5 py-3">
                      <TrialStatusBadge status={trial.status} />
                    </td>
                    <td className="px-4 sm:px-5 py-3 text-on-surface/60">
                      {formatDate(trial.ends_at)}
                    </td>
                    <td className="px-4 sm:px-5 py-3 text-on-surface font-medium capitalize">
                      {trial.plan_code}
                    </td>
                    <td className="px-4 sm:px-5 py-3 text-on-surface/60 capitalize">
                      {trial.provider ?? "—"}
                    </td>
                    <td className="px-4 sm:px-5 py-3">
                      {trial.status === "active" && (
                        <button
                          onClick={() => handleCancel(trial.id)}
                          disabled={cancelling === trial.id}
                          className="text-xs text-red-600 hover:underline disabled:opacity-50"
                          data-testid={`cancel-trial-${trial.id}`}
                        >
                          {cancelling === trial.id ? "Cancelando…" : "Cancelar"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {total > perPage && (
            <div className="p-4 border-t border-on-surface/10">
              <UsersPagination
                page={page}
                perPage={perPage}
                total={total}
                onPageChange={setPage}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}
