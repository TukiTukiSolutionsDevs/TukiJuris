"use client";

/**
 * InvoicesTable — admin paginated table of invoices.
 *
 * - Mirrors BYOKTable pattern: authFetch + useState/useEffect/useCallback.
 * - Silently unmounts on 403 (non-admin).
 * - Status badges: paid (green), failed (red), pending (yellow),
 *   refunded/voided (grey).
 * - Amounts displayed as S/ x.xx (PEN).
 */

import { useState, useEffect, useCallback } from "react";
import {
  Receipt,
  Loader2,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
} from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { fetchAdminInvoices, type InvoiceRow } from "@/lib/api/admin";
import { UsersPagination } from "./UsersPagination";

const STATUS_COLORS: Record<string, string> = {
  paid: "text-green-700 bg-green-50",
  failed: "text-red-700 bg-red-50",
  pending: "text-yellow-700 bg-yellow-50",
  refunded: "text-gray-600 bg-gray-100",
  voided: "text-gray-500 bg-gray-100",
};

const PROVIDER_LABELS: Record<string, string> = {
  culqi: "Culqi",
  mercadopago: "MercadoPago",
};

function StatusBadge({ status }: { status: string }) {
  const cls = STATUS_COLORS[status] ?? "text-gray-500 bg-gray-100";
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium uppercase tracking-wide ${cls}`}
    >
      {status === "paid" && <CheckCircle2 className="w-3 h-3" />}
      {status === "failed" && <XCircle className="w-3 h-3" />}
      {status === "pending" && <Clock className="w-3 h-3" />}
      {status}
    </span>
  );
}

function formatAmount(amount: string, currency: string): string {
  const num = parseFloat(amount);
  if (isNaN(num)) return amount;
  const symbol = currency === "PEN" ? "S/" : currency;
  return `${symbol} ${num.toFixed(2)}`;
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function InvoicesTable() {
  const { authFetch } = useAuth();
  const [items, setItems] = useState<InvoiceRow[]>([]);
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
        const data = await fetchAdminInvoices(authFetch, p, perPage);
        setItems(data.items);
        setTotal(data.total);
      } catch (err: unknown) {
        const status = (err as { status?: number }).status;
        if (status === 403) {
          setHidden(true);
        } else {
          setError("No se pudieron cargar las facturas.");
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
      data-testid="invoices-table"
    >
      {/* Header */}
      <div
        className="p-5 flex items-center gap-2"
        style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
      >
        <Receipt className="w-4 h-4 text-primary" />
        <h2 className="font-semibold text-sm text-on-surface">Facturas</h2>
        <span className="ml-auto text-xs text-on-surface/30">
          {total} total
        </span>
        <button
          onClick={() => load(page)}
          className="ml-2 p-1 rounded hover:bg-surface-container-high transition-colors"
          aria-label="Recargar facturas"
        >
          <RefreshCw className="w-3.5 h-3.5 text-on-surface/40" />
        </button>
      </div>

      {/* Body */}
      {loading ? (
        <div className="flex items-center justify-center py-10 gap-2 text-on-surface/40">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span className="text-sm">Cargando facturas…</span>
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 p-5 text-red-600">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">{error}</span>
        </div>
      ) : items.length === 0 ? (
        <div className="py-10 text-center text-sm text-on-surface/40">
          No hay facturas registradas.
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="bg-surface-container-low">
                  {["Proveedor", "Cargo ID", "Plan", "Total", "Estado", "Fecha"].map(
                    (h) => (
                      <th
                        key={h}
                        className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-4 sm:px-5 py-3"
                      >
                        {h}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody>
                {items.map((inv, i) => (
                  <tr
                    key={inv.id}
                    className={
                      i % 2 === 0
                        ? "bg-surface-container-low"
                        : "bg-surface-container"
                    }
                  >
                    <td className="px-4 sm:px-5 py-3 font-medium text-on-surface">
                      {PROVIDER_LABELS[inv.provider] ?? inv.provider}
                    </td>
                    <td className="px-4 sm:px-5 py-3 text-on-surface/60 font-mono text-xs">
                      {inv.provider_charge_id}
                    </td>
                    <td className="px-4 sm:px-5 py-3 capitalize text-on-surface/80">
                      {inv.plan}
                    </td>
                    <td className="px-4 sm:px-5 py-3 text-on-surface font-medium">
                      {formatAmount(inv.total_amount, inv.currency)}
                    </td>
                    <td className="px-4 sm:px-5 py-3">
                      <StatusBadge status={inv.status} />
                    </td>
                    <td className="px-4 sm:px-5 py-3 text-on-surface/60">
                      {formatDate(inv.paid_at ?? inv.failed_at ?? inv.created_at)}
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
