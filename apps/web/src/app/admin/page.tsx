"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import {
  ShieldCheck,
  Loader2,
  AlertTriangle,
  Users,
  Building2,
  MessageSquare,
  BarChart3,
  Activity,
  Clock,
  Database,
  RefreshCw,
  TrendingUp,
  Zap,
  HardDrive,
  CheckCircle2,
  XCircle,
  FileText,
  Layers,
  Cpu,
  Server,
} from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { AdminLayout } from "@/components/AdminLayout";
import { InternalPageHeader } from "@/components/shell/InternalPageHeader";
import { ShellUtilityActions } from "@/components/shell/ShellUtilityActions";
// admin-saas-panel components — T2.7
// State pattern: plain useState/useCallback/authFetch (mirrors existing page pattern, no new library)
import { RevenueCards } from "./_components/RevenueCards";
import { BYOKBadge } from "./_components/BYOKBadge";
import { BYOKTable } from "./_components/BYOKTable";
import { InvoicesTable } from "./_components/InvoicesTable";
import { UsersPagination } from "./_components/UsersPagination";
import { UserRolesPanel } from "./_components/UserRolesPanel";
import { AuditLogTab } from "./_components/AuditLogTab";

interface SystemStats {
  total_users: number;
  total_organizations: number;
  queries_today: number;
  total_conversations: number;
}

interface UserRow {
  id: string;
  email: string;
  full_name?: string;
  plan: string;
  org_name?: string;
  queries_this_month: number;
  created_at: string;
  is_admin?: boolean;
  last_active?: string | null;  // admin-saas-panel: latest refresh_token.created_at
  byok_count?: number;          // admin-saas-panel: active BYOK key count
}

interface KBStats {
  area: string;
  chunks: number;
}

interface RecentQuery {
  id: string;
  legal_area: string;
  model: string;
  latency_ms: number;
  created_at: string;
  user_email?: string;
}

interface HealthData {
  status: string;
  models_available?: number;
  knowledge_base?: {
    total_chunks?: number;
    areas?: Record<string, number>;
  };
}

interface KBHealthData {
  status: string;
  total_documents: number;
  total_chunks: number;
  embedded_chunks: number;
  embedding_coverage: number;
  chunks_by_area: Record<string, number>;
}

interface ReadyData {
  status: string;
  checks: {
    database: string;
    pgvector: string;
  };
}

const PLAN_COLORS: Record<string, string> = {
  free: "bg-surface-container-low text-on-surface/50",
  pro: "bg-primary/10 text-primary",
  studio: "bg-[#a78bfa]/10 text-[#a78bfa]",
};

const AREA_COLORS: Record<string, string> = {
  civil: "text-blue-400",
  penal: "text-red-400",
  laboral: "text-green-400",
  tributario: "text-yellow-400",
  constitucional: "text-purple-400",
  administrativo: "text-orange-400",
  corporativo: "text-cyan-400",
  registral: "text-pink-400",
  comercio_exterior: "text-teal-400",
  compliance: "text-indigo-400",
  competencia: "text-primary",
};

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  iconBg,
  iconColor,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  sub?: string;
  iconBg?: string;
  iconColor?: string;
}) {
  return (
    <div
      className="bg-surface-container-low rounded-lg p-4 sm:p-5"
      style={{ border: "1px solid rgba(79,70,51,0.15)" }}
    >
      <div className="flex items-center justify-between mb-2 sm:mb-3">
        <span className="text-[10px] sm:text-xs text-on-surface/40 font-medium leading-tight uppercase tracking-[0.1em]">
          {label}
        </span>
        <div
          className={`w-7 h-7 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center shrink-0 ${iconBg || "bg-primary/10"}`}
        >
          <Icon className={`w-3.5 h-3.5 sm:w-4 sm:h-4 ${iconColor || "text-primary"}`} />
        </div>
      </div>
      <p className="font-['Newsreader'] text-3xl font-bold text-primary">
        {typeof value === "number" ? value.toLocaleString("es-PE") : value}
      </p>
      {sub && <p className="text-xs text-on-surface/40 mt-1">{sub}</p>}
    </div>
  );
}

export default function AdminPage() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [usersTotal, setUsersTotal] = useState(0);
  const [usersPage, setUsersPage] = useState(1);
  const [usersPerPage] = useState(20);
  const [kbStats, setKbStats] = useState<KBStats[]>([]);
  const [recentQueries, setRecentQueries] = useState<RecentQuery[]>([]);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [kbHealth, setKbHealth] = useState<KBHealthData | null>(null);
  const [readyData, setReadyData] = useState<ReadyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [expandedUserId, setExpandedUserId] = useState<string | null>(null);

  const { authFetch, hasPermission, user: currentUser } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const tab = searchParams.get("tab") ?? "resumen";

  const loadData = useCallback(async () => {
    setError("");

    try {
      // Load all data in parallel; KB health uses two-step fallback (B4)
      const [healthRes, usersRes, statsRes, queriesRes, readyRes] = await Promise.allSettled([
        authFetch("/api/health"),
        authFetch(`/api/admin/users?page=${usersPage}&per_page=${usersPerPage}`),
        authFetch("/api/admin/stats"),
        authFetch("/api/admin/activity"),
        authFetch("/api/health/ready"),
      ]);

      // Prefer /api/admin/knowledge; silently fall back to /api/health/knowledge on non-ok or 403
      const kbHealthRes = await (async (): Promise<PromiseSettledResult<Response>> => {
        try {
          const primary = await authFetch("/api/admin/knowledge");
          if (primary.ok) return { status: "fulfilled", value: primary };
          const fallback = await authFetch("/api/health/knowledge");
          return { status: "fulfilled", value: fallback };
        } catch (e) {
          return { status: "rejected", reason: e };
        }
      })();

      if (healthRes.status === "fulfilled" && healthRes.value.ok) {
        const hd: HealthData = await healthRes.value.json();
        setHealth(hd);

        if (hd.knowledge_base?.areas) {
          const kb = Object.entries(hd.knowledge_base.areas)
            .map(([area, chunks]) => ({ area, chunks: chunks as number }))
            .sort((a, b) => b.chunks - a.chunks);
          setKbStats(kb);
        }
      }

      if (usersRes.status === "fulfilled" && usersRes.value.ok) {
        const ud = await usersRes.value.json();
        setUsers(Array.isArray(ud) ? ud : ud.users || []);
        if (ud.total !== undefined) setUsersTotal(ud.total);
      }

      if (statsRes.status === "fulfilled" && statsRes.value.ok) {
        const sd = await statsRes.value.json();
        setStats(sd);
      } else {
        setStats({
          total_users: 0,
          total_organizations: 0,
          queries_today: 0,
          total_conversations: 0,
        });
      }

      if (queriesRes.status === "fulfilled" && queriesRes.value.ok) {
        const qd = await queriesRes.value.json();
        setRecentQueries(
          Array.isArray(qd) ? qd.slice(0, 20) : (qd.queries || []).slice(0, 20)
        );
      }

      if (kbHealthRes.status === "fulfilled" && kbHealthRes.value.ok) {
        // Defensive mapping: normalize optional fields so renders never crash (B4)
        const raw = await kbHealthRes.value.json() as Partial<KBHealthData>;
        const kbd: KBHealthData = {
          status: raw.status ?? "ok",
          total_documents: raw.total_documents ?? 0,
          total_chunks: raw.total_chunks ?? 0,
          embedded_chunks: raw.embedded_chunks ?? 0,
          embedding_coverage: raw.embedding_coverage ?? 0,
          chunks_by_area: raw.chunks_by_area ?? {},
        };
        setKbHealth(kbd);
        // Also populate kbStats from this more complete endpoint
        if (kbd.chunks_by_area) {
          const kb = Object.entries(kbd.chunks_by_area)
            .map(([area, chunks]) => ({ area, chunks }))
            .sort((a, b) => b.chunks - a.chunks);
          setKbStats(kb);
        }
      }

      if (readyRes.status === "fulfilled" && readyRes.value.ok) {
        setReadyData(await readyRes.value.json());
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar datos");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [usersPage, usersPerPage, authFetch]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const maxKbChunks = kbStats.length > 0 ? Math.max(...kbStats.map((k) => k.chunks)) : 1;

  return (
    <AdminLayout>
      <div className="flex min-h-full flex-col text-on-surface">
        <InternalPageHeader
          icon={<ShieldCheck className="w-5 h-5 text-primary" />}
          eyebrow="Operación"
          title="Panel de administración"
          description="Monitoreo sistémico, salud de infraestructura y control operativo con el mismo contrato espacial del shell admin."
          utilitySlot={<div className="hidden md:flex"><ShellUtilityActions /></div>}
          actions={
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="control-surface flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm text-on-surface hover:text-white disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
              <span className="hidden sm:inline">Actualizar</span>
            </button>
          }
        />

        {/* ── Tab navigation ─────────────────────────────────────────── */}
        <div
          className="w-full px-4 lg:px-6 xl:px-8 pt-4"
          role="tablist"
          aria-label="Secciones del panel de administración"
        >
          <div className="flex gap-1 border-b border-on-surface/10">
            {(["resumen", "auditoria"] as const).map((t) => (
              <button
                key={t}
                role="tab"
                aria-selected={tab === t}
                onClick={() => {
                  const params = new URLSearchParams(searchParams.toString());
                  params.set("tab", t);
                  router.replace(`${pathname}?${params.toString()}`);
                }}
                className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                  tab === t
                    ? "border-primary text-primary"
                    : "border-transparent text-on-surface/50 hover:text-on-surface"
                }`}
              >
                {t === "resumen" ? "Resumen" : "Auditoría"}
              </button>
            ))}
          </div>
        </div>

        {/* ── Auditoría tab ───────────────────────────────────────────── */}
        {tab === "auditoria" && (
          <div className="w-full px-4 py-6 sm:py-8 lg:px-6 xl:px-8">
            <AuditLogTab />
          </div>
        )}

        {/* ── Resumen tab ─────────────────────────────────────────────── */}
        {tab === "resumen" && (
        <div className="w-full px-4 py-6 sm:py-8 lg:px-6 xl:px-8">
          {/* Error */}
          {error && (
            <div className="flex items-center gap-3 bg-red-500/10 text-red-400 rounded-lg px-4 py-3 mb-6 text-sm" style={{ border: "1px solid rgba(239,68,68,0.3)" }}>
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div className="flex flex-col items-center justify-center py-24 gap-3">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
              <p className="text-sm text-on-surface/40">Cargando panel de administración...</p>
            </div>
          ) : (
            <div className="space-y-8">
              {/* Revenue — pre-gated by billing:read; component also unmounts on 403 (defense-in-depth) */}
              {hasPermission("billing:read") && <RevenueCards />}

              {/* System Stats */}
              <div>
                 <h2 className="section-eyebrow text-on-surface/40 mb-4 flex items-center gap-2">
                  <TrendingUp className="w-3.5 h-3.5" />
                  Estadísticas del sistema
                </h2>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                  <StatCard
                    icon={Users}
                    label="Usuarios totales"
                    value={stats?.total_users ?? users.length}
                    sub="Registrados en la plataforma"
                    iconBg="bg-blue-500/10"
                    iconColor="text-blue-400"
                  />
                  <StatCard
                    icon={Building2}
                    label="Organizaciones"
                    value={stats?.total_organizations ?? 0}
                    sub="Orgs activas"
                    iconBg="bg-purple-500/10"
                    iconColor="text-purple-400"
                  />
                  <StatCard
                    icon={Zap}
                    label="Consultas hoy"
                    value={stats?.queries_today ?? 0}
                    sub="En las últimas 24 horas"
                  />
                  <StatCard
                    icon={MessageSquare}
                    label="Conversaciones"
                    value={stats?.total_conversations ?? 0}
                    sub="Total acumulado"
                    iconBg="bg-green-500/10"
                    iconColor="text-green-400"
                  />
                </div>
              </div>

              {/* ═══ Respaldo & Base de Conocimiento ═══ */}
              {kbHealth && (
                <div>
                  <h2 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-4 flex items-center gap-2">
                    <HardDrive className="w-3.5 h-3.5" />
                    Respaldo &amp; Base de conocimiento
                  </h2>

                  {/* Infrastructure health row */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-4">
                    {/* DB Status */}
                    <div
                       className="panel-base rounded-xl p-4"
                      style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <Server className="w-3.5 h-3.5 text-on-surface/40" />
                        <span className="text-[10px] uppercase tracking-[0.1em] text-on-surface/40">PostgreSQL</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {readyData?.checks?.database === "ok" ? (
                          <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                        ) : (
                          <XCircle className="w-4 h-4 text-red-400" />
                        )}
                        <span className={`text-sm font-semibold ${readyData?.checks?.database === "ok" ? "text-[#10B981]" : "text-red-400"}`}>
                          {readyData?.checks?.database === "ok" ? "Operativo" : "Sin conexión"}
                        </span>
                      </div>
                    </div>

                    {/* pgvector Status */}
                    <div
                       className="panel-base rounded-xl p-4"
                      style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <Cpu className="w-3.5 h-3.5 text-on-surface/40" />
                        <span className="text-[10px] uppercase tracking-[0.1em] text-on-surface/40">pgvector</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {readyData?.checks?.pgvector?.includes("ok") ? (
                          <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                        ) : (
                          <XCircle className="w-4 h-4 text-red-400" />
                        )}
                        <span className={`text-sm font-semibold ${readyData?.checks?.pgvector?.includes("ok") ? "text-[#10B981]" : "text-red-400"}`}>
                          {readyData?.checks?.pgvector || "—"}
                        </span>
                      </div>
                    </div>

                    {/* Embedding Coverage */}
                    <div
                       className="panel-base rounded-xl p-4"
                      style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <Layers className="w-3.5 h-3.5 text-on-surface/40" />
                        <span className="text-[10px] uppercase tracking-[0.1em] text-on-surface/40">Embeddings</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {kbHealth.embedding_coverage === 100 ? (
                          <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                        ) : kbHealth.embedding_coverage > 0 ? (
                          <AlertTriangle className="w-4 h-4 text-primary" />
                        ) : (
                          <XCircle className="w-4 h-4 text-red-400" />
                        )}
                        <span className={`text-sm font-semibold ${
                          kbHealth.embedding_coverage === 100 ? "text-[#10B981]" :
                          kbHealth.embedding_coverage > 0 ? "text-primary" : "text-red-400"
                        }`}>
                          {kbHealth.embedding_coverage}% cobertura
                        </span>
                      </div>
                    </div>

                    {/* Total Data */}
                    <div
                      className="bg-surface-container-low rounded-lg p-4"
                      style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <Database className="w-3.5 h-3.5 text-on-surface/40" />
                        <span className="text-[10px] uppercase tracking-[0.1em] text-on-surface/40">Datos totales</span>
                      </div>
                      <p className="font-['Newsreader'] text-2xl font-bold text-primary">
                        {kbHealth.total_chunks.toLocaleString("es-PE")}
                      </p>
                      <p className="text-[10px] text-on-surface/40">chunks indexados</p>
                    </div>
                  </div>

                  {/* Data inventory card */}
                  <div className="grid lg:grid-cols-3 gap-4">
                    {/* Documents / Chunks / Embeddings summary */}
                    <div
                      className="bg-surface-container-low rounded-lg p-5"
                      style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                    >
                      <h3 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-4 flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5" />
                        Inventario
                      </h3>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-on-surface/50">Documentos legales</span>
                          <span className="font-['Newsreader'] text-lg font-bold text-on-surface">
                            {kbHealth.total_documents}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-on-surface/50">Chunks de texto</span>
                          <span className="font-['Newsreader'] text-lg font-bold text-on-surface">
                            {kbHealth.total_chunks}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-on-surface/50">Con embedding (768-dim)</span>
                          <span className="font-['Newsreader'] text-lg font-bold text-on-surface">
                            {kbHealth.embedded_chunks}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-on-surface/50">Áreas del derecho</span>
                          <span className="font-['Newsreader'] text-lg font-bold text-on-surface">
                            {Object.keys(kbHealth.chunks_by_area).length}
                          </span>
                        </div>
                        {/* Embedding progress bar */}
                        <div className="pt-2">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-[10px] uppercase tracking-widest text-on-surface-variant">Cobertura embeddings</span>
                            <span className="text-xs text-primary font-bold">{kbHealth.embedding_coverage}%</span>
                          </div>
                          <div className="w-full bg-surface rounded-full h-2">
                            <div
                              className="h-2 rounded-full bg-gradient-to-r from-primary to-primary-container transition-all duration-500"
                              style={{ width: `${kbHealth.embedding_coverage}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Full area breakdown */}
                    <div
                      className="lg:col-span-2 bg-surface-container-low rounded-lg p-5"
                      style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                    >
                      <h3 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-4 flex items-center gap-2">
                        <Database className="w-3.5 h-3.5" />
                        Distribución por área ({kbStats.length} áreas)
                      </h3>
                      <div className="grid sm:grid-cols-2 gap-x-6 gap-y-2">
                        {kbStats.map((kb) => (
                          <div key={kb.area}>
                            <div className="flex items-center justify-between mb-0.5">
                              <span className={`text-xs capitalize ${AREA_COLORS[kb.area] || "text-on-surface/50"}`}>
                                {kb.area.replace("_", " ")}
                              </span>
                              <span className="text-xs text-on-surface/30 font-mono">
                                {kb.chunks}
                              </span>
                            </div>
                            <div className="w-full bg-surface rounded-full h-1.5">
                              <div
                                className="h-1.5 rounded-full bg-gradient-to-r from-primary to-primary-container"
                                style={{ width: `${Math.round((kb.chunks / maxKbChunks) * 100)}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Backup instructions */}
                  <div
                    className="mt-4 bg-surface rounded-lg p-4 flex items-start gap-3"
                    style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                  >
                    <HardDrive className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm text-on-surface/70 mb-1">
                        <span className="text-primary font-bold">Respaldo local:</span> La base completa pesa ~1.6 MB comprimida.
                      </p>
                      <div className="flex flex-wrap gap-3 mt-2">
                        <code className="text-xs bg-surface-container-lowest text-primary px-2.5 py-1.5 rounded-lg font-mono">
                          make db-backup
                        </code>
                        <code className="text-xs bg-surface-container-lowest text-on-surface/60 px-2.5 py-1.5 rounded-lg font-mono">
                          make db-restore FILE=backups/xxx.dump
                        </code>
                        <code className="text-xs bg-surface-container-lowest text-on-surface/60 px-2.5 py-1.5 rounded-lg font-mono">
                          make db-seed-full
                        </code>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Health + KB Stats */}
              <div className="grid lg:grid-cols-2 gap-6">
                {/* System Health */}
                {health && (
                  <div
                    className="bg-surface-container-low rounded-lg p-5"
                    style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                  >
                    <h2 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-4 flex items-center gap-2">
                      <Activity className="w-3.5 h-3.5" />
                      Estado del sistema
                    </h2>
                    <div className="space-y-0">
                      <div className="flex items-center justify-between py-3" style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}>
                        <span className="text-sm text-on-surface/50">Estado API</span>
                        <span
                          className={`text-xs font-semibold px-2 py-0.5 rounded-lg ${
                            health.status === "ok" || health.status === "healthy"
                              ? "bg-[#10B981]/10 text-[#10B981]"
                              : "bg-red-500/10 text-red-400"
                          }`}
                        >
                          {health.status === "ok" || health.status === "healthy"
                            ? "Operativo"
                            : health.status}
                        </span>
                      </div>
                      {health.models_available !== undefined && (
                        <div className="flex items-center justify-between py-3" style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}>
                          <span className="text-sm text-on-surface/50">Modelos disponibles</span>
                          <span className="text-sm font-semibold text-on-surface">
                            {health.models_available}
                          </span>
                        </div>
                      )}
                      {health.knowledge_base?.total_chunks !== undefined && (
                        <div className="flex items-center justify-between py-3">
                          <span className="text-sm text-on-surface/50">Chunks en base de conocimiento</span>
                          <span className="text-sm font-semibold text-on-surface">
                            {health.knowledge_base.total_chunks.toLocaleString("es-PE")}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* KB Stats by area */}
                {kbStats.length > 0 && (
                  <div
                    className="bg-surface-container-low rounded-lg p-5"
                    style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                  >
                    <h2 className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-4 flex items-center gap-2">
                      <Database className="w-3.5 h-3.5" />
                      Base de conocimiento por área
                    </h2>
                    <div className="space-y-2.5">
                      {kbStats.slice(0, 8).map((kb) => (
                        <div key={kb.area}>
                          <div className="flex items-center justify-between mb-1">
                            <span className={`text-xs capitalize ${AREA_COLORS[kb.area] || "text-on-surface/50"}`}>
                              {kb.area.replace("_", " ")}
                            </span>
                            <span className="text-xs text-on-surface/30">
                              {kb.chunks.toLocaleString("es-PE")} chunks
                            </span>
                          </div>
                          <div className="w-full bg-surface rounded-full h-1.5">
                            <div
                              className={`h-1.5 rounded-full ${AREA_COLORS[kb.area]?.replace("text-", "bg-") || "bg-primary"}`}
                              style={{ width: `${Math.round((kb.chunks / maxKbChunks) * 100)}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Users Table */}
              {users.length > 0 && (
                <div
                  className="bg-surface-container-low rounded-lg overflow-hidden"
                  style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                >
                  <div
                    className="p-5 flex items-center gap-2 bg-surface-container-low rounded-t-lg"
                    style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
                  >
                    <Users className="w-4 h-4 text-primary" />
                    <h2 className="font-semibold text-sm text-on-surface">Usuarios</h2>
                    <span className="ml-auto text-xs text-on-surface/30">{users.length} usuarios</span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[480px] text-sm">
                      <thead>
                        <tr className="bg-surface-container-low">
                          <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-4 sm:px-5 py-3">
                            Usuario
                          </th>
                          <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-4 sm:px-5 py-3 hidden sm:table-cell">
                            Plan
                          </th>
                          <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-4 sm:px-5 py-3 hidden md:table-cell">
                            Organización
                          </th>
                          <th className="text-right text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-4 sm:px-5 py-3 hidden lg:table-cell">
                            Consultas/mes
                          </th>
                          <th className="text-right text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-4 sm:px-5 py-3 hidden xl:table-cell">
                            Registro
                          </th>
                          <th className="text-right text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-4 sm:px-5 py-3 hidden xl:table-cell">
                            Último acceso
                          </th>
                          <th className="text-center text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-4 sm:px-5 py-3 hidden lg:table-cell">
                             BYOK
                          </th>
                          {hasPermission("roles:write") && (
                            <th className="text-center text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-4 sm:px-5 py-3">
                              Roles
                            </th>
                          )}
                        </tr>
                      </thead>
                      <tbody>
                        {users.map((user, idx) => [
                          <tr
                            key={user.id}
                            className={`transition-colors hover:bg-surface-container-low ${
                              idx % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                            }`}
                          >
                            <td className="px-5 py-3">
                              <div>
                                <div className="flex items-center gap-2">
                                  <p className="font-medium text-on-surface">
                                    {user.full_name || "—"}
                                  </p>
                                  {user.is_admin && (
                                    <ShieldCheck className="w-3.5 h-3.5 text-primary" />
                                  )}
                                </div>
                                <p className="text-xs text-on-surface/40">{user.email}</p>
                              </div>
                            </td>
                            <td className="px-5 py-3 hidden sm:table-cell">
                              <span
                                className={`text-[10px] font-semibold px-2 py-0.5 rounded-lg capitalize ${
                                  PLAN_COLORS[user.plan] || PLAN_COLORS.free
                                }`}
                              >
                                {user.plan}
                              </span>
                            </td>
                            <td className="px-5 py-3 text-xs text-on-surface/50 hidden md:table-cell">
                              {user.org_name || (
                                <span className="text-on-surface/30">Sin org</span>
                              )}
                            </td>
                            <td className="px-5 py-3 text-right text-xs text-on-surface hidden lg:table-cell">
                              {(user.queries_this_month || 0).toLocaleString("es-PE")}
                            </td>
                            <td className="px-5 py-3 text-right text-xs text-on-surface/30 hidden xl:table-cell">
                              {user.created_at
                                ? new Date(user.created_at).toLocaleDateString("es-PE")
                                : "—"}
                            </td>
                            <td className="px-5 py-3 text-right text-xs text-on-surface/30 hidden xl:table-cell">
                              {user.last_active
                                ? new Date(user.last_active).toLocaleDateString("es-PE")
                                : "—"}
                            </td>
                            <td className="px-5 py-3 text-center hidden lg:table-cell">
                              <BYOKBadge count={user.byok_count ?? 0} />
                            </td>
                            {hasPermission("roles:write") && (
                              <td className="px-5 py-3 text-center">
                                <button
                                  onClick={() =>
                                    setExpandedUserId(
                                      expandedUserId === user.id ? null : user.id
                                    )
                                  }
                                  className={`text-xs rounded-lg px-2 py-0.5 transition-colors ${
                                    expandedUserId === user.id
                                      ? "bg-primary/20 text-primary"
                                      : "bg-surface text-on-surface/50 hover:text-primary"
                                  }`}
                                  data-testid={`roles-btn-${user.id}`}
                                >
                                  Roles
                                </button>
                              </td>
                            )}
                          </tr>,
                          hasPermission("roles:write") && expandedUserId === user.id ? (
                            <tr key={`${user.id}-roles`}>
                              <td colSpan={8} className="p-0">
                                <UserRolesPanel
                                  userId={user.id}
                                  currentUserId={currentUser?.id ?? ""}
                                  canWrite={hasPermission("roles:write")}
                                />
                              </td>
                            </tr>
                          ) : null,
                        ])}
                      </tbody>
                    </table>
                  </div>
                  {usersTotal > usersPerPage && (
                    <div className="px-5 py-3" style={{ borderTop: "1px solid rgba(79,70,51,0.15)" }}>
                      <UsersPagination
                        page={usersPage}
                        perPage={usersPerPage}
                        total={usersTotal}
                        onPageChange={setUsersPage}
                      />
                    </div>
                  )}
                </div>
              )}

              {/* BYOK Keys — self-fetching; silently unmounts on 403 */}
              <BYOKTable />

              {/* Invoices — self-fetching; silently unmounts on 403 */}
              <InvoicesTable />

              {/* Recent Queries Activity */}
              {recentQueries.length > 0 && (
                <div
                  className="bg-surface-container-low rounded-lg overflow-hidden"
                  style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                >
                  <div
                    className="p-5 flex items-center gap-2"
                    style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
                  >
                    <Activity className="w-4 h-4 text-primary" />
                    <h2 className="font-semibold text-sm text-on-surface">Actividad reciente</h2>
                    <span className="ml-auto text-xs text-on-surface/30">
                      Últimas {recentQueries.length} consultas
                    </span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[400px] text-sm">
                      <thead>
                        <tr className="bg-surface-container-low">
                          <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-4 sm:px-5 py-3">
                            Área
                          </th>
                          <th className="text-left text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-4 sm:px-5 py-3 hidden sm:table-cell">
                            Modelo
                          </th>
                          <th className="text-right text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-4 sm:px-5 py-3">
                            Latencia
                          </th>
                          <th className="text-right text-[10px] uppercase tracking-[0.1em] text-on-surface/40 px-4 sm:px-5 py-3 hidden md:table-cell">
                            Hora
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {recentQueries.map((q, idx) => (
                          <tr
                            key={q.id}
                            className={`transition-colors hover:bg-surface-container-low ${
                              idx % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                            }`}
                          >
                            <td className="px-5 py-3">
                              <span
                                className={`text-xs capitalize ${
                                  AREA_COLORS[q.legal_area] || "text-on-surface/50"
                                }`}
                              >
                                {q.legal_area?.replace("_", " ") || "General"}
                              </span>
                            </td>
                            <td className="px-5 py-3 hidden sm:table-cell">
                              <span className="text-xs text-on-surface/40 font-mono">
                                {q.model?.split("/").pop() || q.model || "—"}
                              </span>
                            </td>
                            <td className="px-5 py-3 text-right">
                              <div className="flex items-center justify-end gap-1">
                                <Clock className="w-3 h-3 text-on-surface/30" />
                                <span
                                  className={`text-xs ${
                                    q.latency_ms > 10000
                                      ? "text-red-400"
                                      : q.latency_ms > 5000
                                      ? "text-primary"
                                      : "text-[#10B981]"
                                  }`}
                                >
                                  {q.latency_ms ? `${(q.latency_ms / 1000).toFixed(1)}s` : "—"}
                                </span>
                              </div>
                            </td>
                            <td className="px-5 py-3 text-right text-xs text-on-surface/30 hidden md:table-cell">
                              {q.created_at
                                ? new Date(q.created_at).toLocaleTimeString("es-PE", {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                  })
                                : "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Empty state */}
              {users.length === 0 && recentQueries.length === 0 && kbStats.length === 0 && (
                <div
                  className="bg-surface-container-low rounded-lg p-10 text-center"
                  style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                >
                  <BarChart3 className="w-10 h-10 text-on-surface/10 mx-auto mb-3" />
                  <p className="text-sm text-on-surface/50 mb-1">Sin datos disponibles</p>
                  <p className="text-xs text-on-surface/30">
                    Los endpoints de administración podrían no estar implementados aún
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
        )}
      </div>
    </AdminLayout>
  );
}
