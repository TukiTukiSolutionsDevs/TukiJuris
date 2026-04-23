"use client";

import { useState, useEffect, useCallback } from "react";
import { Loader2, AlertTriangle, RefreshCw, X } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface InvoiceRow {
  id: string;
  status: string;
  total: number;
  currency: string;
  created_at: string;
}

interface InvoiceDetail extends InvoiceRow {
  subtotal?: number;
  tax?: number;
  items?: { description: string; amount: number }[];
}

const STATUS_COLORS: Record<string, string> = {
  paid: "bg-green-500/10 text-green-400",
  open: "bg-primary/10 text-primary",
  void: "bg-on-surface/10 text-on-surface/40",
  uncollectible: "bg-red-500/10 text-red-400",
};

const STATUS_LABELS: Record<string, string> = {
  paid: "Pagada",
  open: "Pendiente",
  void: "Anulada",
  uncollectible: "Incobrable",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("es-PE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function formatAmount(total: number, currency: string): string {
  return new Intl.NumberFormat("es-PE", {
    style: "currency",
    currency: currency?.toUpperCase() || "PEN",
    minimumFractionDigits: 2,
  }).format(total / 100);
}

// ---------------------------------------------------------------------------
// Skeleton rows
// ---------------------------------------------------------------------------

function SkeletonRow() {
  return (
    <tr>
      <td className="px-5 py-3"><div className="animate-pulse bg-on-surface/10 h-3 w-24 rounded" /></td>
      <td className="px-5 py-3"><div className="animate-pulse bg-on-surface/10 h-5 w-16 rounded-lg" /></td>
      <td className="px-5 py-3 text-right"><div className="animate-pulse bg-on-surface/10 h-3 w-16 rounded ml-auto" /></td>
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Detail Modal
// ---------------------------------------------------------------------------

interface DetailModalProps {
  orgId: string;
  invoiceId: string;
  onClose: () => void;
}

function InvoiceDetailModal({ orgId, invoiceId, onClose }: DetailModalProps) {
  const { authFetch } = useAuth();
  const [detail, setDetail] = useState<InvoiceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      try {
        const r = await authFetch(`/api/billing/${orgId}/invoices/${invoiceId}`);
        if (!r.ok) throw new Error("fetch failed");
        const d: InvoiceDetail = await r.json();
        setDetail(d);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [authFetch, orgId, invoiceId]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60"
      data-testid="invoice-detail-modal"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="bg-surface-container-low border border-on-surface/15 rounded-xl p-6 w-full max-w-md relative"
        role="dialog"
        aria-modal="true"
        aria-label="Detalle de factura"
      >
        <button
          onClick={onClose}
          data-testid="modal-close-btn"
          className="absolute top-4 right-4 text-on-surface/40 hover:text-on-surface transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
        <h2 className="font-['Newsreader'] text-xl font-bold text-on-surface mb-4">
          Detalle de factura
        </h2>

        {loading && (
          <div className="flex items-center justify-center py-10 gap-2" data-testid="detail-loading">
            <Loader2 className="w-5 h-5 animate-spin text-primary" />
            <span className="text-sm text-on-surface/40">Cargando...</span>
          </div>
        )}

        {error && !loading && (
          <p className="text-sm text-red-400 text-center py-10" data-testid="detail-error">
            No se pudo cargar el detalle de la factura.
          </p>
        )}

        {detail && !loading && (
          <div className="space-y-3" data-testid="invoice-detail-content">
            <div className="flex justify-between text-sm">
              <span className="text-on-surface/50">ID</span>
              <span className="font-mono text-xs text-on-surface/70">{detail.id.slice(0, 16)}…</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-on-surface/50">Fecha</span>
              <span className="text-on-surface">{formatDate(detail.created_at)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-on-surface/50">Estado</span>
              <span className={`text-xs px-2 py-0.5 rounded-lg font-semibold ${STATUS_COLORS[detail.status] || "bg-on-surface/10 text-on-surface/50"}`}>
                {STATUS_LABELS[detail.status] || detail.status}
              </span>
            </div>
            {detail.subtotal !== undefined && (
              <div className="flex justify-between text-sm">
                <span className="text-on-surface/50">Subtotal</span>
                <span className="text-on-surface">{formatAmount(detail.subtotal, detail.currency)}</span>
              </div>
            )}
            {detail.tax !== undefined && (
              <div className="flex justify-between text-sm">
                <span className="text-on-surface/50">IGV</span>
                <span className="text-on-surface">{formatAmount(detail.tax, detail.currency)}</span>
              </div>
            )}
            <div className="flex justify-between text-sm font-bold border-t border-on-surface/15 pt-2 mt-2">
              <span className="text-on-surface">Total</span>
              <span className="text-primary">{formatAmount(detail.total, detail.currency)}</span>
            </div>
            {detail.items && detail.items.length > 0 && (
              <div className="mt-4">
                <p className="text-[10px] uppercase tracking-widest text-on-surface/40 mb-2">Líneas</p>
                <div className="space-y-1">
                  {detail.items.map((item, i) => (
                    <div key={i} className="flex justify-between text-xs text-on-surface/70">
                      <span>{item.description}</span>
                      <span>{formatAmount(item.amount, detail.currency)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// InvoiceHistorySection — main component
// ---------------------------------------------------------------------------

interface InvoiceHistorySectionProps {
  orgId: string;
}

export function InvoiceHistorySection({ orgId }: InvoiceHistorySectionProps) {
  const { authFetch } = useAuth();
  const [invoices, setInvoices] = useState<InvoiceRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null);

  const loadInvoices = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const res = await authFetch(`/api/billing/${orgId}/invoices`);
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      setInvoices(Array.isArray(data) ? data : data.invoices ?? []);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [authFetch, orgId]);

  useEffect(() => {
    loadInvoices();
  }, [loadInvoices]);

  return (
    <div
      className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg overflow-hidden mt-8"
      data-testid="invoice-history-section"
    >
      <div
        className="px-5 py-4 flex items-center justify-between"
        style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
      >
        <h2 className="font-['Newsreader'] text-lg font-bold text-on-surface">
          Historial de pagos
        </h2>
      </div>

      {/* Loading — 3 skeleton rows */}
      {loading && (
        <div className="overflow-x-auto" data-testid="invoice-loading">
          <table className="w-full text-sm">
            <tbody>
              <SkeletonRow />
              <SkeletonRow />
              <SkeletonRow />
            </tbody>
          </table>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div
          className="flex flex-col items-center gap-3 py-10 text-center"
          data-testid="invoice-error"
        >
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <p className="text-sm text-on-surface/60">No se pudieron cargar las facturas.</p>
          <button
            onClick={loadInvoices}
            data-testid="invoice-retry-btn"
            className="flex items-center gap-1.5 text-xs text-primary hover:underline"
          >
            <RefreshCw className="w-3 h-3" />
            Reintentar
          </button>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && invoices.length === 0 && (
        <div
          className="py-10 text-center text-sm text-on-surface/40"
          data-testid="invoice-empty"
        >
          Todavía no tenés facturas.
        </div>
      )}

      {/* Table */}
      {!loading && !error && invoices.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[380px] text-sm" data-testid="invoice-table">
            <thead>
              <tr className="bg-surface-container-low">
                <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                  Fecha
                </th>
                <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                  Estado
                </th>
                <th className="text-right text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                  Total
                </th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv, idx) => (
                <tr
                  key={inv.id}
                  onClick={() => setSelectedInvoiceId(inv.id)}
                  data-testid={`invoice-row-${inv.id}`}
                  className={`cursor-pointer transition-colors hover:bg-surface-container ${
                    idx % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                  }`}
                >
                  <td className="px-5 py-3 text-xs text-on-surface/60 whitespace-nowrap">
                    {formatDate(inv.created_at)}
                  </td>
                  <td className="px-5 py-3">
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-lg ${
                        STATUS_COLORS[inv.status] || "bg-on-surface/10 text-on-surface/50"
                      }`}
                    >
                      {STATUS_LABELS[inv.status] || inv.status}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right text-xs font-mono text-on-surface">
                    {formatAmount(inv.total, inv.currency)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Detail modal */}
      {selectedInvoiceId && (
        <InvoiceDetailModal
          orgId={orgId}
          invoiceId={selectedInvoiceId}
          onClose={() => setSelectedInvoiceId(null)}
        />
      )}
    </div>
  );
}
