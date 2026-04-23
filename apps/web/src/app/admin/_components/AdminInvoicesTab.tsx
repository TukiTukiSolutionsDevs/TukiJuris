"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { Loader2, X, ChevronDown } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth/AuthContext";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AdminInvoiceRow {
  id: string;
  org_id: string;
  status: string;
  total: number;
  currency: string;
  created_at: string;
}

interface AdminInvoicePage {
  items: AdminInvoiceRow[];
  total: number;
  page: number;
  page_size: number;
}

type MutationAction = "refund" | "void";

const PAGE_SIZE = 20;

const STATUS_COLORS: Record<string, string> = {
  paid:          "bg-green-500/10 text-green-400",
  open:          "bg-primary/10 text-primary",
  void:          "bg-on-surface/10 text-on-surface/40",
  uncollectible: "bg-red-500/10 text-red-400",
  refunded:      "bg-blue-500/10 text-blue-400",
};

const STATUS_LABELS: Record<string, string> = {
  paid:          "Pagada",
  open:          "Pendiente",
  void:          "Anulada",
  uncollectible: "Incobrable",
  refunded:      "Reembolsada",
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
// Mutation Modal
// ---------------------------------------------------------------------------

interface MutationModalProps {
  invoice: AdminInvoiceRow;
  action: MutationAction;
  onClose: () => void;
  onSuccess: () => void;
}

function MutationModal({ invoice, action, onClose, onSuccess }: MutationModalProps) {
  const { authFetch } = useAuth();
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const isReasonValid = reason.trim().length > 0;

  const handleSubmit = async () => {
    if (!isReasonValid) return;
    setSubmitting(true);
    try {
      const res = await authFetch(`/api/admin/invoices/${invoice.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, reason: reason.trim() }),
      });

      if (res.ok) {
        const label = action === "refund" ? "reembolsada" : "anulada";
        toast.success(`Factura ${label}`);
        onSuccess();
        onClose();
        return;
      }

      toast.error(action === "refund" ? "No se pudo reembolsar la factura" : "No se pudo anular la factura");
    } catch {
      toast.error(action === "refund" ? "No se pudo reembolsar la factura" : "No se pudo anular la factura");
    } finally {
      setSubmitting(false);
    }
  };

  const actionLabel = action === "refund" ? "Reembolsar" : "Anular";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60"
      data-testid="mutation-modal"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="bg-surface-container-low border border-on-surface/15 rounded-xl p-6 w-full max-w-md relative"
        role="dialog"
        aria-modal="true"
        aria-label={`${actionLabel} factura`}
      >
        <button
          onClick={onClose}
          data-testid="modal-close-btn"
          className="absolute top-4 right-4 text-on-surface/40 hover:text-on-surface transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        <h2 className="font-['Newsreader'] text-xl font-bold text-on-surface mb-1">
          {actionLabel} factura
        </h2>
        <p className="text-xs text-on-surface/50 mb-4">
          ID: <span className="font-mono">{invoice.id.slice(0, 16)}…</span>
          {" · "}
          {formatAmount(invoice.total, invoice.currency)}
        </p>

        <div className="mb-4">
          <label
            htmlFor="mutation-reason"
            className="block text-[10px] uppercase tracking-widest text-on-surface/40 mb-1"
          >
            Motivo <span className="text-red-400">*</span>
          </label>
          <textarea
            id="mutation-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Describe el motivo de la acción..."
            rows={3}
            data-testid="reason-textarea"
            className="w-full text-sm bg-surface border border-on-surface/20 rounded-lg px-3 py-2 text-on-surface resize-none focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            data-testid="modal-cancel-btn"
            className="px-4 py-2 text-sm text-on-surface/60 hover:text-on-surface rounded-lg border border-on-surface/20 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={!isReasonValid || submitting}
            data-testid="modal-submit-btn"
            className="flex items-center gap-1.5 px-4 py-2 text-sm font-bold rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {submitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            {actionLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// AdminInvoicesTab — main component
// ---------------------------------------------------------------------------

export function AdminInvoicesTab() {
  const { authFetch } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // URL-committed filter state (mirrors AuditLogTab pattern)
  const page       = Math.max(1, parseInt(searchParams.get("inv_page") ?? "1", 10));
  const filterStatus = searchParams.get("inv_status")  ?? "";
  const filterOrg    = searchParams.get("inv_org_id")  ?? "";

  // Local (uncommitted) filter state
  const [localStatus, setLocalStatus] = useState(filterStatus);
  const [localOrg,    setLocalOrg]    = useState(filterOrg);

  const [data,           setData]           = useState<AdminInvoicePage | null>(null);
  const [loading,        setLoading]        = useState(true);
  const [selectedInvoice, setSelectedInvoice] = useState<AdminInvoiceRow | null>(null);
  const [mutationAction,  setMutationAction]  = useState<MutationAction | null>(null);
  const [openMenuId,      setOpenMenuId]      = useState<string | null>(null);

  // Push URL params without full navigation (mirrors AuditLogTab.pushParams)
  const pushParams = useCallback(
    (updates: Record<string, string>) => {
      const params = new URLSearchParams(searchParams.toString());
      for (const [k, v] of Object.entries(updates)) {
        if (v) params.set(k, v);
        else params.delete(k);
      }
      router.replace(`${pathname}?${params.toString()}`);
    },
    [searchParams, pathname, router]
  );

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page:      String(page),
        page_size: String(PAGE_SIZE),
      });
      if (filterStatus) params.set("status",  filterStatus);
      if (filterOrg)    params.set("org_id",  filterOrg);

      const res = await authFetch(`/api/admin/invoices?${params}`);
      if (!res.ok) throw new Error(`${res.status}`);
      setData(await res.json() as AdminInvoicePage);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [authFetch, page, filterStatus, filterOrg]);

  useEffect(() => { loadData(); }, [loadData]);

  // Sync local inputs when URL changes (e.g. browser back)
  useEffect(() => {
    setLocalStatus(filterStatus);
    setLocalOrg(filterOrg);
  }, [filterStatus, filterOrg]);

  const handleApply = () => {
    pushParams({
      inv_status: localStatus,
      inv_org_id: localOrg,
      inv_page:   "",          // reset to page 1
    });
  };

  const handleClear = () => {
    setLocalStatus("");
    setLocalOrg("");
    pushParams({ inv_status: "", inv_org_id: "", inv_page: "" });
  };

  const goPage = (p: number) => pushParams({ inv_page: String(p) });

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  const openMutation = (invoice: AdminInvoiceRow, action: MutationAction) => {
    setSelectedInvoice(invoice);
    setMutationAction(action);
    setOpenMenuId(null);
  };

  const handleMutationSuccess = () => {
    setSelectedInvoice(null);
    setMutationAction(null);
    loadData();
  };

  return (
    <div className="space-y-4" data-testid="admin-invoices-tab">
      {/* ── Filter bar ───────────────────────────────────────────────────── */}
      <div
        className="bg-surface-container-low rounded-lg p-4 flex flex-wrap gap-3 items-end"
        style={{ border: "1px solid rgba(79,70,51,0.15)" }}
        data-testid="inv-filter-bar"
      >
        <div className="flex flex-col gap-1">
          <label className="text-[10px] uppercase tracking-widest text-on-surface/40">
            Estado
          </label>
          <select
            value={localStatus}
            onChange={(e) => setLocalStatus(e.target.value)}
            aria-label="Filtrar por estado"
            data-testid="filter-status"
            className="text-xs bg-surface border border-on-surface/20 rounded-lg px-2 py-1.5 text-on-surface"
          >
            <option value="">Todos</option>
            <option value="paid">Pagada</option>
            <option value="open">Pendiente</option>
            <option value="void">Anulada</option>
            <option value="refunded">Reembolsada</option>
            <option value="uncollectible">Incobrable</option>
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-[10px] uppercase tracking-widest text-on-surface/40">
            Org ID
          </label>
          <input
            value={localOrg}
            onChange={(e) => setLocalOrg(e.target.value)}
            placeholder="UUID de organización"
            aria-label="Filtrar por organización"
            data-testid="filter-org-id"
            className="text-xs bg-surface border border-on-surface/20 rounded-lg px-2 py-1.5 text-on-surface w-44"
          />
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleApply}
            data-testid="apply-filters-btn"
            className="text-xs bg-primary/10 text-primary rounded-lg px-3 py-1.5 hover:bg-primary/20 transition-colors"
          >
            Aplicar
          </button>
          <button
            onClick={handleClear}
            data-testid="clear-filters-btn"
            className="text-xs bg-surface border border-on-surface/20 text-on-surface/60 rounded-lg px-3 py-1.5 hover:text-on-surface transition-colors"
          >
            Limpiar
          </button>
        </div>
      </div>

      {/* ── Results table ────────────────────────────────────────────────── */}
      <div
        className="bg-surface-container-low rounded-lg overflow-hidden"
        style={{ border: "1px solid rgba(79,70,51,0.15)" }}
      >
        {loading ? (
          <div
            className="flex items-center justify-center gap-2 py-16 text-on-surface/40"
            data-testid="inv-loading"
          >
            <Loader2 className="w-5 h-5 animate-spin" />
            <span className="text-sm">Cargando facturas…</span>
          </div>
        ) : !data || data.items.length === 0 ? (
          <div
            className="flex items-center justify-center py-16 text-on-surface/40 text-sm"
            data-testid="inv-empty"
          >
            No hay facturas que coincidan con los filtros.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="inv-table">
              <thead>
                <tr className="bg-surface-container-low">
                  <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                    Factura ID
                  </th>
                  <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                    Org ID
                  </th>
                  <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                    Fecha
                  </th>
                  <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                    Estado
                  </th>
                  <th className="text-right text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                    Total
                  </th>
                  <th className="text-center text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((inv, idx) => (
                  <tr
                    key={inv.id}
                    data-testid={`inv-row-${inv.id}`}
                    className={`transition-colors hover:bg-surface-container ${
                      idx % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                    }`}
                  >
                    <td className="px-5 py-3 text-xs font-mono text-on-surface/60">
                      {inv.id.slice(0, 12)}…
                    </td>
                    <td className="px-5 py-3 text-xs font-mono text-on-surface/50">
                      {inv.org_id.slice(0, 12)}…
                    </td>
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
                    <td className="px-5 py-3 text-center relative">
                      <button
                        onClick={() => setOpenMenuId(openMenuId === inv.id ? null : inv.id)}
                        data-testid={`action-menu-btn-${inv.id}`}
                        className="flex items-center gap-1 text-xs text-on-surface/50 hover:text-on-surface rounded-lg px-2 py-1 transition-colors mx-auto"
                      >
                        Acciones
                        <ChevronDown className="w-3 h-3" />
                      </button>
                      {openMenuId === inv.id && (
                        <div
                          className="absolute right-4 top-full mt-1 z-20 bg-surface-container-low border border-on-surface/20 rounded-lg shadow-lg overflow-hidden"
                          data-testid={`action-menu-${inv.id}`}
                        >
                          <button
                            onClick={() => openMutation(inv, "refund")}
                            data-testid={`refund-btn-${inv.id}`}
                            className="block w-full text-left text-xs px-4 py-2 hover:bg-surface-container text-on-surface/70 hover:text-on-surface transition-colors"
                          >
                            Reembolsar
                          </button>
                          <button
                            onClick={() => openMutation(inv, "void")}
                            data-testid={`void-btn-${inv.id}`}
                            className="block w-full text-left text-xs px-4 py-2 hover:bg-surface-container text-red-400 hover:text-red-300 transition-colors"
                          >
                            Anular
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* ── Pagination ────────────────────────────────────────────────── */}
        {data && data.total > PAGE_SIZE && (
          <div
            className="px-5 py-3 flex items-center justify-between"
            style={{ borderTop: "1px solid rgba(79,70,51,0.15)" }}
            data-testid="inv-pagination"
          >
            <span className="text-xs text-on-surface/40">
              Página {page} de {totalPages} · {data.total.toLocaleString("es-PE")} facturas
            </span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => goPage(page - 1)}
                data-testid="prev-page-btn"
                className="text-xs px-3 py-1 rounded-lg bg-surface border border-on-surface/20 disabled:opacity-40 hover:bg-surface-container transition-colors"
              >
                Anterior
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => goPage(page + 1)}
                data-testid="next-page-btn"
                className="text-xs px-3 py-1 rounded-lg bg-surface border border-on-surface/20 disabled:opacity-40 hover:bg-surface-container transition-colors"
              >
                Siguiente
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Mutation modal ───────────────────────────────────────────────── */}
      {selectedInvoice && mutationAction && (
        <MutationModal
          invoice={selectedInvoice}
          action={mutationAction}
          onClose={() => { setSelectedInvoice(null); setMutationAction(null); }}
          onSuccess={handleMutationSuccess}
        />
      )}
    </div>
  );
}
