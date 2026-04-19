"use client";

/**
 * BYOKTable — paginated table of BYOK key configurations.
 *
 * - No encrypted key material shown (api_key_hint only).
 * - Mirrors admin/page.tsx data-fetch pattern: authFetch + useState/useEffect.
 * - Empty and error states included per AC5 / design §7.
 */

import { useState, useEffect, useCallback } from "react";
import { Key, Loader2, AlertCircle, CheckCircle2, XCircle } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { fetchBYOK, type BYOKItem } from "@/lib/api/admin";
import { UsersPagination } from "./UsersPagination";

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function BYOKTable() {
  const { authFetch } = useAuth();
  const [items, setItems] = useState<BYOKItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [loading, setLoading] = useState(true);
  const [hidden, setHidden] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (p: number) => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchBYOK(authFetch, p, perPage);
        setItems(data.items);
        setTotal(data.total);
      } catch (err: unknown) {
        const status = (err as { status?: number }).status;
        if (status === 403) {
          setHidden(true);
        } else {
          setError("No se pudieron cargar las claves BYOK.");
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

  if (hidden) return null;

  return (
    <div
      className="bg-surface-container-low rounded-lg overflow-hidden"
      style={{ border: "1px solid rgba(79,70,51,0.15)" }}
    >
      {/* Header */}
      <div
        className="p-5 flex items-center gap-2"
        style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
      >
        <Key className="w-4 h-4 text-primary" />
        <h2 className="font-semibold text-sm text-on-surface">Claves BYOK</h2>
        <span className="ml-auto text-xs text-on-surface/30">
          {total.toLocaleString("es-PE")} configuraciones
        </span>
      </div>

      {loading && (
        <div className="flex items-center justify-center gap-2 py-10 text-sm text-on-surface/40">
          <Loader2 className="w-4 h-4 animate-spin" />
          Cargando claves…
        </div>
      )}

      {!loading && error && (
        <div className="flex items-center gap-2 px-5 py-6 text-sm text-red-400">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <div className="px-5 py-10 text-center text-sm text-on-surface/40">
          No hay claves BYOK registradas.
        </div>
      )}

      {!loading && !error && items.length > 0 && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-sm">
              <thead>
                <tr className="bg-surface-container-low">
                  <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                    Usuario
                  </th>
                  <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                    Proveedor
                  </th>
                  <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3 hidden sm:table-cell">
                    Hint
                  </th>
                  <th className="text-center text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                    Estado
                  </th>
                  <th className="text-right text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3 hidden md:table-cell">
                    Última rotación
                  </th>
                </tr>
              </thead>
              <tbody>
                {items.map((item, idx) => (
                  <tr
                    key={`${item.user_id}-${item.provider}`}
                    className={idx % 2 === 0 ? "bg-surface" : "bg-surface-container-low"}
                  >
                    <td className="px-5 py-3 text-xs text-on-surface/70">
                      {item.user_email}
                    </td>
                    <td className="px-5 py-3">
                      <span className="text-xs font-mono font-semibold text-on-surface">
                        {item.provider}
                      </span>
                    </td>
                    <td className="px-5 py-3 hidden sm:table-cell">
                      <span className="text-xs font-mono text-on-surface/50">
                        {item.api_key_hint}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-center">
                      {item.is_active ? (
                        <CheckCircle2 className="w-4 h-4 text-green-400 inline-block" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-400 inline-block" />
                      )}
                    </td>
                    <td className="px-5 py-3 text-right text-xs text-on-surface/40 hidden md:table-cell">
                      {formatDate(item.last_rotation_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ borderTop: "1px solid rgba(79,70,51,0.15)" }}>
            <UsersPagination
              page={page}
              perPage={perPage}
              total={total}
              onPageChange={setPage}
            />
          </div>
        </>
      )}
    </div>
  );
}
