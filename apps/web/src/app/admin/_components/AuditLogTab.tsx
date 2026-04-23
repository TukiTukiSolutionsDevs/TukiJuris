"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { Loader2, ChevronDown, ChevronRight } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AuditLogEntry {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

interface AuditLogPage {
  items: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
}

const PAGE_SIZE = 20;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AuditLogTab() {
  const { authFetch } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Read committed filter values from URL
  const page = Math.max(1, parseInt(searchParams.get("audit_page") ?? "1", 10));
  const filterActor   = searchParams.get("audit_actor")    ?? "";
  const filterAction  = searchParams.get("audit_action")   ?? "";
  const filterResource = searchParams.get("audit_resource") ?? "";
  const filterDateFrom = searchParams.get("audit_from")    ?? "";
  const filterDateTo   = searchParams.get("audit_to")      ?? "";

  // Local (uncommitted) filter input state
  const [localActor,    setLocalActor]    = useState(filterActor);
  const [localAction,   setLocalAction]   = useState(filterAction);
  const [localResource, setLocalResource] = useState(filterResource);
  const [localDateFrom, setLocalDateFrom] = useState(filterDateFrom);
  const [localDateTo,   setLocalDateTo]   = useState(filterDateTo);

  const [data,       setData]       = useState<AuditLogPage | null>(null);
  const [loading,    setLoading]    = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Helper: update URL params without full navigation
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
        page: String(page),
        page_size: String(PAGE_SIZE),
      });
      if (filterActor)    params.set("user_id",       filterActor);
      if (filterAction)   params.set("action",        filterAction);
      if (filterResource) params.set("resource_type", filterResource);
      if (filterDateFrom) params.set("date_from",     filterDateFrom);
      if (filterDateTo)   params.set("date_to",       filterDateTo);

      const res = await authFetch(`/api/admin/audit-log?${params}`);
      if (!res.ok) throw new Error(`${res.status}`);
      setData(await res.json() as AuditLogPage);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [authFetch, page, filterActor, filterAction, filterResource, filterDateFrom, filterDateTo]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Sync local inputs if URL changes (e.g. browser back)
  useEffect(() => {
    setLocalActor(filterActor);
    setLocalAction(filterAction);
    setLocalResource(filterResource);
    setLocalDateFrom(filterDateFrom);
    setLocalDateTo(filterDateTo);
  }, [filterActor, filterAction, filterResource, filterDateFrom, filterDateTo]);

  const handleApply = () => {
    pushParams({
      audit_actor:    localActor,
      audit_action:   localAction,
      audit_resource: localResource,
      audit_from:     localDateFrom,
      audit_to:       localDateTo,
      audit_page:     "",          // reset to page 1
    });
  };

  const handleClear = () => {
    setLocalActor("");
    setLocalAction("");
    setLocalResource("");
    setLocalDateFrom("");
    setLocalDateTo("");
    pushParams({
      audit_actor:    "",
      audit_action:   "",
      audit_resource: "",
      audit_from:     "",
      audit_to:       "",
      audit_page:     "",
    });
  };

  const goPage = (p: number) => {
    pushParams({ audit_page: String(p) });
  };

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  return (
    <div className="space-y-4" data-testid="audit-log-tab">
      {/* ── Filter bar ─────────────────────────────────────────────────── */}
      <div
        className="bg-surface-container-low rounded-lg p-4 flex flex-wrap gap-3 items-end"
        style={{ border: "1px solid rgba(79,70,51,0.15)" }}
        data-testid="audit-filter-bar"
      >
        <div className="flex flex-col gap-1">
          <label className="text-[10px] uppercase tracking-widest text-on-surface/40">
            Actor (user_id)
          </label>
          <input
            value={localActor}
            onChange={(e) => setLocalActor(e.target.value)}
            placeholder="UUID del actor"
            aria-label="Filtrar por actor"
            className="text-xs bg-surface border border-on-surface/20 rounded-lg px-2 py-1.5 text-on-surface w-44"
            data-testid="filter-actor"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-[10px] uppercase tracking-widest text-on-surface/40">
            Acción
          </label>
          <input
            value={localAction}
            onChange={(e) => setLocalAction(e.target.value)}
            placeholder="role.assign"
            aria-label="Filtrar por acción"
            className="text-xs bg-surface border border-on-surface/20 rounded-lg px-2 py-1.5 text-on-surface w-32"
            data-testid="filter-action"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-[10px] uppercase tracking-widest text-on-surface/40">
            Tipo recurso
          </label>
          <input
            value={localResource}
            onChange={(e) => setLocalResource(e.target.value)}
            placeholder="user_role"
            aria-label="Filtrar por tipo de recurso"
            className="text-xs bg-surface border border-on-surface/20 rounded-lg px-2 py-1.5 text-on-surface w-28"
            data-testid="filter-resource"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-[10px] uppercase tracking-widest text-on-surface/40">
            Desde
          </label>
          <input
            type="date"
            value={localDateFrom}
            onChange={(e) => setLocalDateFrom(e.target.value)}
            aria-label="Filtrar desde fecha"
            className="text-xs bg-surface border border-on-surface/20 rounded-lg px-2 py-1.5 text-on-surface"
            data-testid="filter-date-from"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-[10px] uppercase tracking-widest text-on-surface/40">
            Hasta
          </label>
          <input
            type="date"
            value={localDateTo}
            onChange={(e) => setLocalDateTo(e.target.value)}
            aria-label="Filtrar hasta fecha"
            className="text-xs bg-surface border border-on-surface/20 rounded-lg px-2 py-1.5 text-on-surface"
            data-testid="filter-date-to"
          />
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleApply}
            className="text-xs bg-primary/10 text-primary rounded-lg px-3 py-1.5 hover:bg-primary/20 transition-colors"
            data-testid="apply-filters-btn"
          >
            Aplicar
          </button>
          <button
            onClick={handleClear}
            className="text-xs bg-surface border border-on-surface/20 text-on-surface/60 rounded-lg px-3 py-1.5 hover:text-on-surface transition-colors"
            data-testid="clear-filters-btn"
          >
            Limpiar
          </button>
        </div>
      </div>

      {/* ── Results table ──────────────────────────────────────────────── */}
      <div
        className="bg-surface-container-low rounded-lg overflow-hidden"
        style={{ border: "1px solid rgba(79,70,51,0.15)" }}
      >
        {loading ? (
          <div
            className="flex items-center justify-center gap-2 py-16 text-on-surface/40"
            data-testid="audit-loading"
          >
            <Loader2 className="w-5 h-5 animate-spin" />
            <span className="text-sm">Cargando auditoría…</span>
          </div>
        ) : !data || data.items.length === 0 ? (
          <div
            className="flex items-center justify-center py-16 text-on-surface/40 text-sm"
            data-testid="audit-empty"
          >
            No hay entradas que coincidan con los filtros.
          </div>
        ) : (
          <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid="audit-table">
            <thead>
              <tr className="bg-surface-container-low">
                <th className="w-8 px-3 py-3" />
                <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                  Timestamp
                </th>
                <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                  Actor
                </th>
                <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                  Acción
                </th>
                <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                  Tipo recurso
                </th>
                <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-5 py-3">
                  ID recurso
                </th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((entry, idx) => {
                const isExpanded = expandedId === entry.id;
                return [
                  <tr
                    key={entry.id}
                    className={`cursor-pointer transition-colors hover:bg-surface-container ${
                      idx % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                    }`}
                    onClick={() => setExpandedId(isExpanded ? null : entry.id)}
                    data-testid={`audit-row-${entry.id}`}
                  >
                    <td className="px-3 py-3 text-on-surface/40">
                      {isExpanded ? (
                        <ChevronDown className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronRight className="w-3.5 h-3.5" />
                      )}
                    </td>
                    <td className="px-5 py-3 text-xs text-on-surface/30 whitespace-nowrap">
                      {new Date(entry.created_at).toLocaleString("es-PE")}
                    </td>
                    <td className="px-5 py-3 text-xs text-on-surface/50 font-mono">
                      {entry.user_id.slice(0, 8)}…
                    </td>
                    <td className="px-5 py-3 font-mono text-xs text-primary">
                      {entry.action}
                    </td>
                    <td className="px-5 py-3 text-xs text-on-surface/60">
                      {entry.resource_type}
                    </td>
                    <td className="px-5 py-3 text-xs text-on-surface/60">
                      {entry.resource_id ?? "—"}
                    </td>
                  </tr>,
                  isExpanded ? (
                    <tr key={`${entry.id}-expanded`} data-testid={`audit-row-${entry.id}-expanded`}>
                      <td colSpan={6} className="px-5 py-4 bg-surface-container-lowest">
                        <div className="grid sm:grid-cols-2 gap-4">
                          {entry.before_state !== null ? (
                            <div>
                              <p className="text-[10px] uppercase tracking-widest text-on-surface/40 mb-1">
                                Before
                              </p>
                              <div
                                className="overflow-auto max-h-40 bg-surface rounded-lg p-2"
                                style={{ border: "1px solid rgba(79,70,51,0.1)" }}
                              >
                                <pre className="text-xs text-on-surface/70 font-mono whitespace-pre-wrap">
                                  {JSON.stringify(entry.before_state, null, 2)}
                                </pre>
                              </div>
                            </div>
                          ) : null}
                          {entry.after_state !== null ? (
                            <div>
                              <p className="text-[10px] uppercase tracking-widest text-on-surface/40 mb-1">
                                After
                              </p>
                              <div
                                className="overflow-auto max-h-40 bg-surface rounded-lg p-2"
                                style={{ border: "1px solid rgba(79,70,51,0.1)" }}
                              >
                                <pre className="text-xs text-on-surface/70 font-mono whitespace-pre-wrap">
                                  {JSON.stringify(entry.after_state, null, 2)}
                                </pre>
                              </div>
                            </div>
                          ) : null}
                          {entry.before_state === null && entry.after_state === null && (
                            <p className="text-xs text-on-surface/30 col-span-2 italic">
                              Sin estado antes/después registrado
                            </p>
                          )}
                        </div>
                      </td>
                    </tr>
                  ) : null,
                ];
              })}
            </tbody>
          </table>
          </div>
        )}

        {/* ── Pagination ──────────────────────────────────────────────── */}
        {data && data.total > PAGE_SIZE && (
          <div
            className="px-5 py-3 flex items-center justify-between"
            style={{ borderTop: "1px solid rgba(79,70,51,0.15)" }}
            data-testid="audit-pagination"
          >
            <span className="text-xs text-on-surface/40">
              Página {page} de {totalPages} · {data.total.toLocaleString("es-PE")} entradas
            </span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => goPage(page - 1)}
                className="text-xs px-3 py-1 rounded-lg bg-surface border border-on-surface/20 disabled:opacity-40 hover:bg-surface-container transition-colors"
                data-testid="prev-page-btn"
              >
                Anterior
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => goPage(page + 1)}
                className="text-xs px-3 py-1 rounded-lg bg-surface border border-on-surface/20 disabled:opacity-40 hover:bg-surface-container transition-colors"
                data-testid="next-page-btn"
              >
                Siguiente
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
