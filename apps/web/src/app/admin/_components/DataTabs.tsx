"use client";

/**
 * DataTabs — group of data-driven admin tabs that consume live API endpoints.
 *
 * Each tab is a small read-only inventory plus, where useful, light actions.
 * Backend mutation hooks are added on a per-tab basis as we wire them up.
 */

import { useEffect, useState } from "react";
import {
  Loader2, AlertTriangle, Users, Building2, Clock, BookOpen, KeyRound, ShieldCheck,
  Heart, CreditCard, Bell, BarChart3, Check, X, Database, Cpu, FileText, Layers, Zap, Activity,
} from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { AdminTrialsTable } from "./AdminTrialsTable";
import { BYOKTable } from "./BYOKTable";
import { UserRolesPanel } from "./UserRolesPanel";

// ----------------------------------------------------------------------------
// Shared helpers
// ----------------------------------------------------------------------------

function Shell({
  icon: Icon,
  title,
  description,
  right,
  children,
}: {
  icon: React.ElementType;
  title: string;
  description?: string;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="w-full px-4 py-6 sm:py-8 lg:px-6 xl:px-8 space-y-6">
      <header className="flex items-center gap-3">
        <div className="w-11 h-11 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
          <Icon className="w-5 h-5 text-primary" />
        </div>
        <div className="flex-1">
          <h2 className="font-['Newsreader'] text-2xl font-bold text-primary">{title}</h2>
          {description && <p className="text-xs text-on-surface/50">{description}</p>}
        </div>
        {right}
      </header>
      {children}
    </div>
  );
}

function Empty({ msg }: { msg: string }) {
  return (
    <div className="bg-surface-container-low rounded-xl px-5 py-8 text-center text-sm text-on-surface/40" style={{ border: "1px solid rgba(79,70,51,0.15)" }}>
      {msg}
    </div>
  );
}

function Err({ msg }: { msg: string }) {
  return (
    <div className="bg-red-500/10 border border-red-400/20 text-red-300 rounded-xl px-4 py-3 text-sm flex items-center gap-2">
      <AlertTriangle className="w-4 h-4" />
      {msg}
    </div>
  );
}

function Spinner() {
  return (
    <div className="w-full py-12 flex items-center justify-center">
      <Loader2 className="w-6 h-6 animate-spin text-primary" />
    </div>
  );
}

function useFetchJson<T>(url: string | null, deps: unknown[] = []) {
  const { authFetch } = useAuth();
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(!!url);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!url) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    void authFetch(url, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject(`${r.status} ${r.statusText}`)))
      .then((d: T) => { if (!cancelled) setData(d); })
      .catch((e) => { if (!cancelled) setError(String(e)); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, authFetch, ...deps]);

  return { data, loading, error };
}

// ============================================================================
// Usuarios — standalone tab (richer than the embedded one in Resumen)
// ============================================================================

interface AdminUser {
  id: string;
  email: string;
  full_name?: string | null;
  is_active: boolean;
  is_admin: boolean;
  plan: string;
  created_at: string;
  org_name?: string | null;
  queries_this_month: number;
  last_active?: string | null;
  byok_count: number;
}

interface AdminUsersResponse {
  users: AdminUser[];
  total: number;
  page: number;
  per_page: number;
}

export function UsuariosTab() {
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const perPage = 20;
  const { data, loading, error } = useFetchJson<AdminUsersResponse>(
    `/api/admin/users?page=${page}&per_page=${perPage}${q ? `&search=${encodeURIComponent(q)}` : ""}`,
    [page, q]
  );

  return (
    <Shell
      icon={Users}
      title="Usuarios"
      description="Gestión completa, búsqueda y roles"
      right={
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Buscar por email…"
            value={q}
            onChange={(e) => { setQ(e.target.value); setPage(1); }}
            className="bg-surface-container-low border border-on-surface/15 rounded-lg px-3 py-1.5 text-xs text-on-surface placeholder:text-on-surface/30 w-48"
          />
        </div>
      }
    >
      {loading ? <Spinner /> : error ? <Err msg={error} /> : !data || data.users.length === 0 ? (
        <Empty msg="No hay usuarios registrados." />
      ) : (
        <>
          <p className="text-xs text-on-surface/40">
            {data.total} usuario{data.total === 1 ? "" : "s"} · página {data.page}
          </p>
          <div className="bg-surface-container-low rounded-2xl overflow-hidden" style={{ border: "1px solid rgba(79,70,51,0.15)" }}>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-on-surface/10 text-[10px] uppercase tracking-[0.15em] text-on-surface/40">
                  <th className="text-left px-5 py-3">Usuario</th>
                  <th className="text-left px-5 py-3">Plan</th>
                  <th className="text-left px-5 py-3 hidden md:table-cell">Org</th>
                  <th className="text-right px-5 py-3 hidden lg:table-cell">Consultas/mes</th>
                  <th className="text-right px-5 py-3 hidden lg:table-cell">BYOK</th>
                  <th className="text-center px-5 py-3 hidden xl:table-cell">Estado</th>
                </tr>
              </thead>
              <tbody>
                {data.users.map((u) => (
                  <tr key={u.id} className="border-b border-on-surface/5 last:border-0">
                    <td className="px-5 py-3">
                      <p className="text-on-surface text-sm font-medium">{u.full_name || u.email}</p>
                      <p className="text-[11px] text-on-surface/40">{u.email}</p>
                    </td>
                    <td className="px-5 py-3">
                      <span className="text-[10px] uppercase tracking-[0.15em] bg-surface px-2 py-1 rounded-md text-on-surface/70 border border-on-surface/10">
                        {u.plan}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-xs text-on-surface/60 hidden md:table-cell">{u.org_name ?? "—"}</td>
                    <td className="px-5 py-3 text-right font-mono text-xs hidden lg:table-cell">{u.queries_this_month}</td>
                    <td className="px-5 py-3 text-right font-mono text-xs hidden lg:table-cell">{u.byok_count}</td>
                    <td className="px-5 py-3 text-center hidden xl:table-cell">
                      <span className={`inline-block w-2 h-2 rounded-full ${u.is_active ? "bg-emerald-400" : "bg-red-400"}`} />
                      {u.is_admin && <span className="ml-1.5 text-[9px] uppercase tracking-[0.15em] text-primary">Admin</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {data.total > perPage && (
            <div className="flex items-center justify-between text-xs">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1.5 rounded-lg border border-on-surface/15 text-on-surface/60 hover:text-on-surface disabled:opacity-30"
              >
                ← Anterior
              </button>
              <span className="text-on-surface/40">
                {(page - 1) * perPage + 1}–{Math.min(page * perPage, data.total)} de {data.total}
              </span>
              <button
                disabled={page * perPage >= data.total}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1.5 rounded-lg border border-on-surface/15 text-on-surface/60 hover:text-on-surface disabled:opacity-30"
              >
                Siguiente →
              </button>
            </div>
          )}
        </>
      )}
    </Shell>
  );
}

// ============================================================================
// Organizaciones
// ============================================================================

interface OrgRow {
  id: string;
  name: string;
  slug?: string;
  plan?: string;
  created_at?: string;
  member_count?: number;
}

export function OrganizacionesTab() {
  const { data, loading, error } = useFetchJson<OrgRow[]>("/api/organizations/");

  return (
    <Shell icon={Building2} title="Organizaciones" description="Workspaces multi-tenant del sistema">
      {loading ? <Spinner /> : error ? <Err msg={error} /> : !data || data.length === 0 ? (
        <Empty msg="No hay organizaciones creadas todavía." />
      ) : (
        <div className="bg-surface-container-low rounded-2xl overflow-hidden" style={{ border: "1px solid rgba(79,70,51,0.15)" }}>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-on-surface/10 text-[10px] uppercase tracking-[0.15em] text-on-surface/40">
                <th className="text-left px-5 py-3">Organización</th>
                <th className="text-left px-5 py-3">Plan</th>
                <th className="text-right px-5 py-3">Miembros</th>
                <th className="text-right px-5 py-3">Creada</th>
              </tr>
            </thead>
            <tbody>
              {data.map((o) => (
                <tr key={o.id} className="border-b border-on-surface/5 last:border-0">
                  <td className="px-5 py-3">
                    <p className="text-on-surface font-medium">{o.name}</p>
                    {o.slug && <p className="font-mono text-[10px] text-on-surface/30">{o.slug}</p>}
                  </td>
                  <td className="px-5 py-3 text-xs text-on-surface/70">{o.plan ?? "—"}</td>
                  <td className="px-5 py-3 text-right font-mono text-xs">{o.member_count ?? "—"}</td>
                  <td className="px-5 py-3 text-right text-xs text-on-surface/50">
                    {o.created_at ? new Date(o.created_at).toLocaleDateString("es-PE") : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Shell>
  );
}

// ============================================================================
// Trials — reuses existing AdminTrialsTable
// ============================================================================

export function TrialsTab() {
  return (
    <Shell icon={Clock} title="Trials" description="Periodos de prueba activos y conversión">
      <AdminTrialsTable />
    </Shell>
  );
}

// ============================================================================
// Conocimiento (Knowledge Base)
// ============================================================================

interface KnowledgeChunk {
  area: string;
  count: number;
}

interface KnowledgeDoc {
  id: string;
  title: string;
  legal_area?: string;
  source?: string;
  created_at?: string;
}

interface KnowledgePayload {
  chunks_by_area: KnowledgeChunk[];
  documents: KnowledgeDoc[];
  embedding_coverage: {
    total_chunks: number;
    embedded_chunks: number;
    coverage_pct: number;
  };
}

export function ConocimientoTab() {
  const { data, loading, error } = useFetchJson<KnowledgePayload>("/api/admin/knowledge");

  return (
    <Shell icon={BookOpen} title="Base de conocimiento" description="Documentos, chunks, embeddings y áreas del derecho">
      {loading ? <Spinner /> : error ? <Err msg={error} /> : !data ? (
        <Empty msg="Sin datos." />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Stat label="Documentos" value={data.documents.length} icon={FileText} color="text-blue-400" bg="bg-blue-500/10" />
            <Stat label="Chunks indexados" value={data.embedding_coverage.total_chunks} icon={Layers} color="text-purple-400" bg="bg-purple-500/10" />
            <Stat label="Cobertura embeddings" value={`${data.embedding_coverage.coverage_pct.toFixed(1)}%`} icon={Database} color="text-emerald-400" bg="bg-emerald-500/10" />
          </div>

          <section>
            <h3 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-3">
              Distribución por área ({data.chunks_by_area.length})
            </h3>
            {data.chunks_by_area.length === 0 ? (
              <Empty msg="La base no contiene documentos todavía. Corré 'make db-seed-full' o ingestá vía /api/upload." />
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                {data.chunks_by_area.map((c) => (
                  <div key={c.area} className="bg-surface-container-low rounded-lg p-3 flex flex-col" style={{ border: "1px solid rgba(79,70,51,0.15)" }}>
                    <span className="text-[10px] uppercase tracking-[0.15em] text-on-surface/40 truncate">{c.area}</span>
                    <span className="font-['Newsreader'] text-xl font-bold text-on-surface">{c.count}</span>
                  </div>
                ))}
              </div>
            )}
          </section>

          {data.documents.length > 0 && (
            <section>
              <h3 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-3">Documentos recientes</h3>
              <div className="bg-surface-container-low rounded-2xl overflow-hidden" style={{ border: "1px solid rgba(79,70,51,0.15)" }}>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-on-surface/10 text-[10px] uppercase tracking-[0.15em] text-on-surface/40">
                      <th className="text-left px-5 py-3">Título</th>
                      <th className="text-left px-5 py-3">Área</th>
                      <th className="text-left px-5 py-3">Fuente</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.documents.slice(0, 10).map((d) => (
                      <tr key={d.id} className="border-b border-on-surface/5 last:border-0">
                        <td className="px-5 py-3 text-on-surface text-sm">{d.title}</td>
                        <td className="px-5 py-3 text-xs text-on-surface/60">{d.legal_area ?? "—"}</td>
                        <td className="px-5 py-3 text-xs text-on-surface/40">{d.source ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </>
      )}
    </Shell>
  );
}

// ============================================================================
// BYOK overview — reuses BYOKTable
// ============================================================================

export function BYOKOverviewTab() {
  return (
    <Shell icon={KeyRound} title="BYOK · Bring Your Own Key" description="Claves de proveedores LLM que los usuarios cargaron en sus cuentas">
      <BYOKTable />
    </Shell>
  );
}

// ============================================================================
// Roles & Permisos
// ============================================================================

interface RoleRow {
  id: string;
  name: string;
  display_name: string;
  description: string;
  is_system: boolean;
}

interface PermissionRow {
  id: string;
  resource: string;
  action: string;
  description?: string;
}

export function RolesTab() {
  const { data: roles, loading, error } = useFetchJson<RoleRow[]>("/api/admin/roles");
  const [activeRoleId, setActiveRoleId] = useState<string | null>(null);
  const { data: perms } = useFetchJson<PermissionRow[]>(
    activeRoleId ? `/api/admin/roles/${activeRoleId}/permissions` : null,
    [activeRoleId]
  );

  // Auto-select the first role once the list loads. This is derived from
  // async data (no external store), so the rule's recommended alternatives
  // don't apply.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (roles && roles.length && !activeRoleId) setActiveRoleId(roles[0].id);
  }, [roles, activeRoleId]);

  return (
    <Shell icon={ShieldCheck} title="Roles & Permisos" description="RBAC del sistema y permisos granulares por rol">
      {loading ? <Spinner /> : error ? <Err msg={error} /> : !roles ? <Empty msg="Sin datos." /> : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <aside className="space-y-1">
            {roles.map((r) => (
              <button
                key={r.id}
                onClick={() => setActiveRoleId(r.id)}
                className={`w-full text-left px-4 py-3 rounded-xl transition-colors ${
                  activeRoleId === r.id ? "bg-primary/10 border-primary/30 text-primary" : "bg-surface-container-low border-on-surface/10 text-on-surface/70 hover:text-on-surface"
                } border`}
              >
                <p className="font-medium text-sm">{r.display_name}</p>
                <p className="font-mono text-[10px] opacity-70">{r.name}</p>
                {r.is_system && <span className="text-[9px] uppercase tracking-[0.15em] text-primary/60 mt-1 inline-block">System</span>}
              </button>
            ))}
          </aside>

          <section className="lg:col-span-2">
            {activeRoleId ? (
              perms ? (
                <div className="bg-surface-container-low rounded-2xl p-5" style={{ border: "1px solid rgba(79,70,51,0.15)" }}>
                  <h3 className="text-sm font-medium text-on-surface mb-3">
                    Permisos · {perms.length}
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                    {perms.map((p) => (
                      <div key={p.id} className="flex items-center gap-2 text-xs">
                        <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        <code className="font-mono text-on-surface/80">{p.resource}:{p.action}</code>
                      </div>
                    ))}
                  </div>
                </div>
              ) : <Spinner />
            ) : <Empty msg="Selecciona un rol." />}
          </section>
        </div>
      )}
    </Shell>
  );
}

// ============================================================================
// Salud
// ============================================================================

interface HealthMetrics {
  status: string;
  metrics: {
    total_requests: number;
    total_errors: number;
    error_rate_pct: number;
    avg_latency_ms: number;
    slow_requests: number;
    status_codes: Record<string, number>;
    slowest_endpoints: Array<{ path: string; avg_ms: number }>;
  };
}

interface ReadyChecks {
  status: string;
  checks: Record<string, string>;
}

export function SaludTab() {
  const { data: metrics, loading: ml, error: me } = useFetchJson<HealthMetrics>("/api/health/metrics");
  const { data: ready } = useFetchJson<ReadyChecks>("/api/health/ready");

  return (
    <Shell icon={Heart} title="Salud del sistema" description="Health-checks, latencia y status codes">
      {ml ? <Spinner /> : me ? <Err msg={me} /> : !metrics ? <Empty msg="Sin datos." /> : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Stat label="Status" value={metrics.status} icon={Heart} color="text-emerald-400" bg="bg-emerald-500/10" />
            <Stat label="Requests" value={metrics.metrics.total_requests} icon={Activity} color="text-blue-400" bg="bg-blue-500/10" />
            <Stat label="Errores" value={`${metrics.metrics.error_rate_pct.toFixed(2)}%`} icon={AlertTriangle} color={metrics.metrics.error_rate_pct > 1 ? "text-red-400" : "text-emerald-400"} bg={metrics.metrics.error_rate_pct > 1 ? "bg-red-500/10" : "bg-emerald-500/10"} />
            <Stat label="Latencia media" value={`${metrics.metrics.avg_latency_ms.toFixed(0)} ms`} icon={Zap} color="text-violet-400" bg="bg-violet-500/10" />
          </div>

          {ready && (
            <section>
              <h3 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-3">Componentes</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {Object.entries(ready.checks).map(([name, status]) => (
                  <div key={name} className="bg-surface-container-low rounded-xl px-4 py-3 flex items-center justify-between" style={{ border: "1px solid rgba(79,70,51,0.15)" }}>
                    <span className="text-sm text-on-surface capitalize">{name}</span>
                    <span className="font-mono text-xs text-emerald-300">{status}</span>
                  </div>
                ))}
              </div>
            </section>
          )}

          <section>
            <h3 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-3">Endpoints más lentos</h3>
            <div className="bg-surface-container-low rounded-2xl overflow-hidden" style={{ border: "1px solid rgba(79,70,51,0.15)" }}>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-on-surface/10 text-[10px] uppercase tracking-[0.15em] text-on-surface/40">
                    <th className="text-left px-5 py-3">Path</th>
                    <th className="text-right px-5 py-3">Latencia avg</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.metrics.slowest_endpoints.map((e) => (
                    <tr key={e.path} className="border-b border-on-surface/5 last:border-0">
                      <td className="px-5 py-3 font-mono text-xs text-on-surface/80">{e.path}</td>
                      <td className="px-5 py-3 text-right font-mono text-xs">{e.avg_ms.toFixed(1)} ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h3 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-3">Códigos de respuesta</h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(metrics.metrics.status_codes).map(([code, n]) => (
                <span key={code} className={`text-xs px-3 py-1.5 rounded-lg font-mono ${
                  code.startsWith("2") ? "bg-emerald-500/10 text-emerald-300 border border-emerald-400/20" :
                  code.startsWith("4") ? "bg-amber-500/10 text-amber-300 border border-amber-400/20" :
                  "bg-red-500/10 text-red-300 border border-red-400/20"
                }`}>
                  {code}: {n}
                </span>
              ))}
            </div>
          </section>
        </>
      )}
    </Shell>
  );
}

// ============================================================================
// Suscripciones
// ============================================================================

export function SuscripcionesTab() {
  return (
    <Shell icon={CreditCard} title="Suscripciones" description="Estado de suscripción por organización">
      <Empty msg="No hay organizaciones con suscripción activa todavía. Las suscripciones se gestionan vía /api/billing/{org_id}/subscription una vez que existan orgs." />
    </Shell>
  );
}

// ============================================================================
// Notificaciones
// ============================================================================

const NOTIFICATION_KINDS = [
  { id: "subscription_activated", label: "Suscripción activada", channels: ["email"] },
  { id: "subscription_expiring", label: "Suscripción por vencer", channels: ["email", "in_app"] },
  { id: "payment_failed", label: "Pago fallido", channels: ["email"] },
  { id: "trial_started", label: "Trial iniciado", channels: ["email", "in_app"] },
  { id: "trial_expired", label: "Trial vencido", channels: ["email"] },
  { id: "quota_warning", label: "Cuota próxima a límite", channels: ["in_app"] },
];

export function NotificacionesTab() {
  return (
    <Shell icon={Bell} title="Notificaciones" description="Templates y canales del sistema de notificaciones">
      <div className="bg-surface-container-low rounded-2xl overflow-hidden" style={{ border: "1px solid rgba(79,70,51,0.15)" }}>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-on-surface/10 text-[10px] uppercase tracking-[0.15em] text-on-surface/40">
              <th className="text-left px-5 py-3">Evento</th>
              <th className="text-left px-5 py-3">Canales</th>
            </tr>
          </thead>
          <tbody>
            {NOTIFICATION_KINDS.map((n) => (
              <tr key={n.id} className="border-b border-on-surface/5 last:border-0">
                <td className="px-5 py-3">
                  <p className="text-sm text-on-surface">{n.label}</p>
                  <p className="font-mono text-[10px] text-on-surface/40">{n.id}</p>
                </td>
                <td className="px-5 py-3">
                  <div className="flex gap-1.5">
                    {n.channels.map((c) => (
                      <span key={c} className="text-[10px] uppercase tracking-[0.15em] bg-surface px-2 py-1 rounded-md text-on-surface/70 border border-on-surface/10">{c}</span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-on-surface/40 italic">
        Templates renderizados en <code className="bg-surface-container-low px-1 py-0.5 rounded">app/services/email_service.py</code>.
        Editor de templates pendiente.
      </p>
    </Shell>
  );
}

// ============================================================================
// Analytics (system-level)
// ============================================================================

export function AnalyticsTab() {
  const { data, loading, error } = useFetchJson<HealthMetrics>("/api/health/metrics");

  return (
    <Shell icon={BarChart3} title="Analytics" description="Uso del sistema y métricas agregadas">
      {loading ? <Spinner /> : error ? <Err msg={error} /> : !data ? <Empty msg="Sin datos." /> : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Stat label="Total requests" value={data.metrics.total_requests} icon={Activity} color="text-blue-400" bg="bg-blue-500/10" />
            <Stat label="Errores" value={data.metrics.total_errors} icon={AlertTriangle} color="text-red-400" bg="bg-red-500/10" />
            <Stat label="Lentos" value={data.metrics.slow_requests} icon={Zap} color="text-amber-400" bg="bg-amber-500/10" />
            <Stat label="Latencia avg" value={`${data.metrics.avg_latency_ms.toFixed(0)}ms`} icon={Cpu} color="text-violet-400" bg="bg-violet-500/10" />
          </div>
          <p className="text-xs text-on-surface/40 italic">
            Analytics por organización disponibles vía <code className="bg-surface-container-low px-1 py-0.5 rounded">/api/analytics/{"{org_id}"}/overview</code>.
            Dashboard por-org pendiente.
          </p>
        </>
      )}
    </Shell>
  );
}

// ----------------------------------------------------------------------------
// Stat card primitive
// ----------------------------------------------------------------------------

function Stat({
  icon: Icon, label, value, color, bg,
}: { icon: React.ElementType; label: string; value: string | number; color: string; bg: string }) {
  return (
    <div className="bg-surface-container-low rounded-xl p-4 flex flex-col" style={{ border: "1px solid rgba(79,70,51,0.15)" }}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] uppercase tracking-[0.15em] text-on-surface/40">{label}</span>
        <div className={`w-7 h-7 rounded-lg ${bg} flex items-center justify-center`}>
          <Icon className={`w-3.5 h-3.5 ${color}`} />
        </div>
      </div>
      <p className="font-['Newsreader'] text-2xl font-bold text-primary">{value}</p>
    </div>
  );
}
