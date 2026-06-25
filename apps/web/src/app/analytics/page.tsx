"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/AuthContext";
import { AppLayout } from "@/components/AppLayout";
import { InternalPageHeader } from "@/components/shell/InternalPageHeader";
import { ShellUtilityActions } from "@/components/shell/ShellUtilityActions";
import { OrgSwitcher } from "@/components/OrgSwitcher";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Minus,
  ThumbsUp,
  Timer,
  Users,
  RefreshCw,
  Download,
  DollarSign,
  MessageSquare,
} from "lucide-react";
import { LEGAL_AREAS, AREA_HEX_COLORS } from "@/app/chat/constants";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

// Extend each area with its hex color for chart consumers that need a literal value.
const AREA_MAP = Object.fromEntries(
  LEGAL_AREAS.map((a) => [a.id, { ...a, hex: AREA_HEX_COLORS[a.id] ?? "#6b7280" }])
);

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface OverviewData {
  queries_today: number;
  queries_today_vs_yesterday_pct: number;
  queries_week: number;
  queries_month: number;
  queries_trend: { date: string; count: number }[];
  top_areas: { area: string; count: number }[];
  top_models: { model: string; count: number }[];
  avg_latency_ms: number;
  satisfaction_rate: number;
  active_users: number;
}

interface AreaData {
  area: string;
  count: number;
  percentage: number;
  avg_latency_ms: number;
  prev_period_count: number;
  change_pct: number | null;
  trend: "up" | "down" | "stable";
}

interface ModelData {
  model: string;
  count: number;
  percentage: number;
  avg_latency_ms: number;
  min_latency_ms: number | null;
  max_latency_ms: number | null;
}

interface QueryRow {
  id: string;
  created_at: string | null;
  user_email: string;
  legal_area: string | null;
  agent_used: string | null;
  model: string | null;
  latency_ms: number | null;
}

interface CostModelData {
  model: string;
  total_tokens: number;
  estimated_cost_usd: number;
  query_count: number;
  avg_tokens_per_query: number;
}

interface CostsData {
  models: CostModelData[];
  total_cost_usd: number;
  window_days: number;
}

interface TopQueryItem {
  query_preview: string;
  count: number;
  legal_areas: string[];
  last_asked: string | null;
}

interface TopQueriesData {
  queries: TopQueryItem[];
  window_days: number;
}

// ---------------------------------------------------------------------------
// Skeleton component
// ---------------------------------------------------------------------------

function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={`animate-pulse bg-surface-container rounded ${className ?? ""}`}
    />
  );
}

// ---------------------------------------------------------------------------
// Stat card
// ---------------------------------------------------------------------------

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: React.ReactNode;
  icon?: React.ReactNode;
  loading?: boolean;
}

function StatCard({ label, value, sub, icon, loading }: StatCardProps) {
  if (loading) {
    return (
      <div className="panel-base rounded-xl p-6">
        <Skeleton className="h-3 w-24 mb-4" />
        <Skeleton className="h-8 w-32 mb-2" />
        <Skeleton className="h-3 w-20" />
      </div>
    );
  }
  return (
    <div className="panel-base rounded-xl p-6 transition-transform duration-200 hover:-translate-y-0.5">
      <div className="flex items-center justify-between mb-3">
        <p className="section-eyebrow text-on-surface-subtle leading-tight">{label}</p>
        {icon && <div className="text-on-surface-subtle shrink-0">{icon}</div>}
      </div>
      <p className="font-['Newsreader'] text-3xl font-bold tracking-[-0.03em] text-primary">{value}</p>
      {sub && <div className="mt-2">{sub}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Bar chart (pure CSS)
// ---------------------------------------------------------------------------

function BarChart({
  data,
  loading,
}: {
  data: { date: string; count: number }[];
  loading: boolean;
}) {
  const loadingHeights = [24, 38, 52, 44, 66, 58, 34, 48, 72, 60, 42, 56, 28, 46, 64, 36, 54, 68, 40, 50];

  if (loading) {
    return (
      <div className="flex items-end gap-1 h-36">
        {loadingHeights.map((height, i) => (
          <div
            key={i}
            className="flex-1 animate-pulse rounded bg-surface-container"
            style={{ height: `${height}%` }}
          />
        ))}
      </div>
    );
  }

  if (!data.length) {
    return (
      <div className="h-36 flex items-center justify-center text-on-surface-subtle text-sm">
        Sin datos en este periodo
      </div>
    );
  }

  const max = Math.max(...data.map((d) => d.count), 1);

  return (
    <div className="flex items-end gap-0.5 h-36 w-full">
      {data.map((d) => {
        const heightPct = Math.max((d.count / max) * 100, 2);
        return (
          <div
            key={d.date}
            className="flex-1 flex flex-col items-center gap-0.5 group relative"
            title={`${d.date}: ${d.count} consultas`}
          >
            <div
              className="w-full bg-primary hover:bg-primary-container rounded-t-sm transition-colors cursor-default"
              style={{ height: `${heightPct}%` }}
            />
            <div className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 hidden group-hover:block bg-surface-dim border border-outline rounded px-2 py-1 text-[10px] text-on-surface whitespace-nowrap z-10 pointer-events-none">
              {d.date}: {d.count}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Donut chart (conic-gradient CSS)
// ---------------------------------------------------------------------------

function DonutChart({
  data,
  loading,
}: {
  data: { area: string; count: number }[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-40">
        <Skeleton className="w-36 h-36 rounded-full" />
      </div>
    );
  }

  if (!data.length) {
    return (
      <div className="h-40 flex items-center justify-center text-on-surface-subtle text-sm">
        Sin datos
      </div>
    );
  }

  const total = data.reduce((s, d) => s + d.count, 0) || 1;

  const segments = data.reduce<Array<{ color: string; start: number; end: number }>>((acc, d) => {
    const pct = (d.count / total) * 100;
    const area = AREA_MAP[d.area];
    const color = area?.hex ?? "#6b7280";
    const start = acc.length > 0 ? acc[acc.length - 1].end : 0;
    return [...acc, { color, start, end: start + pct }];
  }, []);

  const gradient = segments
    .map((s) => `${s.color} ${s.start}% ${s.end}%`)
    .join(", ");

  return (
    <div className="flex items-center gap-4">
      <div
        className="shrink-0 rounded-full"
        style={{
          width: 120,
          height: 120,
          background: `conic-gradient(${gradient})`,
          WebkitMask:
            "radial-gradient(farthest-side, transparent calc(100% - 18px), #000 calc(100% - 18px))",
          mask: "radial-gradient(farthest-side, transparent calc(100% - 18px), #000 calc(100% - 18px))",
        }}
      />
      <div className="space-y-1.5 min-w-0">
        {data.slice(0, 6).map((d) => {
          const area = AREA_MAP[d.area];
          const pct = Math.round((d.count / total) * 100);
          return (
            <div key={d.area} className="flex items-center gap-2 text-xs">
              <span
                className="w-2.5 h-2.5 rounded-sm shrink-0"
                style={{ background: area?.hex ?? "#6b7280" }}
              />
              <span className="text-on-surface-variant truncate">{area?.name ?? d.area}</span>
              <span className="text-on-surface-subtle ml-auto pl-2">{pct}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Latency badge
// ---------------------------------------------------------------------------

function LatencyBadge({ ms }: { ms: number | null }) {
  if (ms === null || ms === undefined) return <span className="text-on-surface-subtle">—</span>;
  const color =
    ms < 2000 ? "text-status-success" : ms < 5000 ? "text-primary" : "text-status-danger";
  return <span className={`font-mono ${color}`}>{Math.round(ms)}ms</span>;
}

// ---------------------------------------------------------------------------
// Trend indicator
// ---------------------------------------------------------------------------

function TrendIndicator({
  value,
  suffix = "%",
}: {
  value: number | null;
  suffix?: string;
}) {
  if (value === null || value === undefined) {
    return <span className="text-on-surface-subtle text-xs">—</span>;
  }
  if (value > 0) {
    return (
      <span className="flex items-center gap-0.5 text-xs text-status-success">
        <TrendingUp className="w-3 h-3" />
        +{value}{suffix}
      </span>
    );
  }
  if (value < 0) {
    return (
      <span className="flex items-center gap-0.5 text-xs text-status-danger">
        <TrendingDown className="w-3 h-3" />
        {value}{suffix}
      </span>
    );
  }
  return (
    <span className="flex items-center gap-0.5 text-xs text-on-surface-subtle">
      <Minus className="w-3 h-3" />
      0{suffix}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Area badge (inline)
// ---------------------------------------------------------------------------

function AreaBadge({ area }: { area: string | null }) {
  if (!area) return <span className="text-on-surface-subtle text-xs">—</span>;
  const a = AREA_MAP[area];
  return (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-surface-container-low border border-outline-variant">
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{ background: a?.hex ?? "#6b7280" }}
      />
      <span className="text-on-surface">{a?.name ?? area}</span>
    </span>
  );
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

type TabId = "overview" | "costos" | "frecuentes";

export default function AnalyticsPage() {
  const [days, setDays] = useState(30);
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [orgs, setOrgs] = useState<{ id: string; name: string }[]>([]);
  const [orgId, setOrgId] = useState<string | null>(null);
  const [orgLoading, setOrgLoading] = useState(true);
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [areas, setAreas] = useState<AreaData[]>([]);
  const [models, setModels] = useState<ModelData[]>([]);
  const [queries, setQueries] = useState<QueryRow[]>([]);
  const [costs, setCosts] = useState<CostsData | null>(null);
  const [topQueries, setTopQueries] = useState<TopQueriesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { authFetch, user } = useAuth();
  const router = useRouter();
  // Analytics is a user/org-facing feature (see plan "Pro" in /billing).
  // Backend analytics.py allows any org member; only admin bypasses org-role gating.
  // No admin guard here — access is gated by session + backend RBAC.
  void user; void router;

  // Fetch user's organizations on mount; hydrate selected org from localStorage.
  useEffect(() => {
    authFetch("/api/organizations/")
      .then((r) => (r.ok ? r.json() : []))
      .then((data: { id: string; name: string }[] | { organizations: { id: string; name: string }[] }) => {
        const list = Array.isArray(data) ? data : (data as { organizations: { id: string; name: string }[] }).organizations ?? [];
        setOrgs(list);
        if (list.length > 0) {
          const stored = localStorage.getItem("tk_selected_org_id");
          const isValid = stored !== null && list.some((o) => o.id === stored);
          setOrgId(isValid ? stored : list[0].id);
        }
      })
      .catch(() => {
        // silently fail — no org found
      })
      .finally(() => setOrgLoading(false));
  }, [authFetch]);

  const handleOrgChange = useCallback((id: string) => {
    localStorage.setItem("tk_selected_org_id", id);
    setOrgId(id);
    // fetchData re-runs automatically because orgId is in its dependency chain
  }, []);

  const fetchData = useCallback(
    async (isRefresh = false) => {
      if (!orgId) return;
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      try {
        const [overviewRes, areasRes, modelsRes, queriesRes, costsRes, topQueriesRes] =
          await Promise.all([
            authFetch(`/api/analytics/${orgId}/overview?days=${days}`),
            authFetch(`/api/analytics/${orgId}/areas?days=${days}`),
            authFetch(`/api/analytics/${orgId}/models?days=${days}`),
            authFetch(`/api/analytics/${orgId}/queries?per_page=20`),
            authFetch(`/api/analytics/${orgId}/costs?days=${days}`),
            authFetch(`/api/analytics/${orgId}/top-queries?days=${days}&limit=15`),
          ]);

        if (!overviewRes.ok) {
          throw new Error(`Error ${overviewRes.status}: ${await overviewRes.text()}`);
        }

        const [overviewData, areasData, modelsData, queriesData, costsData, topQueriesData] =
          await Promise.all([
            overviewRes.json(),
            areasRes.ok ? areasRes.json() : { areas: [] },
            modelsRes.ok ? modelsRes.json() : { models: [] },
            queriesRes.ok ? queriesRes.json() : { queries: [] },
            costsRes.ok ? costsRes.json() : { models: [], total_cost_usd: 0, window_days: days },
            topQueriesRes.ok ? topQueriesRes.json() : { queries: [], window_days: days },
          ]);

        setOverview(overviewData);
        setAreas(areasData.areas ?? []);
        setModels(modelsData.models ?? []);
        setQueries(queriesData.queries ?? []);
        setCosts(costsData);
        setTopQueries(topQueriesData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error al cargar datos");
        setOverview({
          queries_today: 0,
          queries_today_vs_yesterday_pct: 0,
          queries_week: 0,
          queries_month: 0,
          queries_trend: [],
          top_areas: [],
          top_models: [],
          avg_latency_ms: 0,
          satisfaction_rate: 0,
          active_users: 0,
        });
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [authFetch, days, orgId]
  );

  useEffect(() => {
    if (orgId) fetchData();
  }, [fetchData, orgId]);

  const handleExport = useCallback(async () => {
    if (!orgId) return;
    setExporting(true);
    try {
      const res = await authFetch(`/api/analytics/${orgId}/export?days=${days}`);
      if (!res.ok) throw new Error(`Export failed: ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const today = new Date().toISOString().slice(0, 10);
      a.href = url;
      a.download = `tukijuris-analytics-${orgId}-${today}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export error:", err);
    } finally {
      setExporting(false);
    }
  }, [authFetch, days, orgId]);

  const dateRangeOptions = [
    { label: "7d", value: 7 },
    { label: "30d", value: 30 },
    { label: "90d", value: 90 },
  ];

  return (
    <AppLayout>
      <div className="flex min-h-full flex-col text-on-surface">
        <InternalPageHeader
          icon={<BarChart3 className="w-5 h-5 text-primary" />}
          eyebrow="Organización"
          title="Analytics"
          description="Métricas de uso, costos y consultas frecuentes dentro del mismo lenguaje espacial del shell privado."
          utilitySlot={<div className="hidden md:flex"><ShellUtilityActions /></div>}
          actions={<div className="flex items-center gap-2">
            {/* Date range selector */}
            <div className="flex items-center gap-1 bg-surface-container-low border border-outline-variant rounded-lg p-1">
              {dateRangeOptions.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setDays(opt.value)}
                  className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                    days === opt.value
                      ? "bg-primary/10 text-primary"
                      : "text-on-surface-variant hover:text-on-surface"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            {/* Export button */}
            <button
              onClick={handleExport}
              disabled={exporting}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold uppercase tracking-widest text-on-surface border border-outline-variant hover:bg-surface-container-high transition-colors disabled:opacity-50"
              title="Exportar CSV"
            >
              <Download className={`w-3.5 h-3.5 ${exporting ? "animate-bounce" : ""}`} />
              <span className="hidden sm:inline">Exportar CSV</span>
            </button>

            {/* Refresh button */}
            <button
              onClick={() => fetchData(true)}
              disabled={refreshing}
              className="p-2 rounded-lg text-on-surface-subtle hover:text-on-surface border border-outline-variant hover:bg-surface-container-high transition-colors disabled:opacity-50"
              title="Actualizar datos"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            </button>
          </div>}
        />

        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
          {/* Loading org state */}
          {orgLoading && (
            <div className="flex items-center justify-center py-20">
              <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin mr-3" />
              <span className="text-on-surface-variant text-sm">Cargando organización...</span>
            </div>
          )}

          {/* No org state */}
          {!orgLoading && !orgId && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <BarChart3 className="w-12 h-12 text-surface-container-high mb-4" />
              <h2 className="font-['Newsreader'] text-3xl font-bold text-on-surface mb-2">
                Sin organización
              </h2>
              <p className="text-on-surface-subtle text-sm max-w-sm">
                Crea una organización para ver analytics.
              </p>
              <a
                href="/organizacion"
                className="mt-4 inline-flex items-center gap-2 bg-gradient-to-br from-primary to-primary-container hover:opacity-90 text-on-primary text-sm font-bold px-4 py-2 rounded-lg transition-opacity"
              >
                Crear organización
              </a>
            </div>
          )}

          {/* Error banner */}
          {!orgLoading && orgId && error && (
            <div className="bg-status-danger/10 border border-status-danger/30 rounded-lg px-4 py-3 text-sm text-status-danger">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Main content — only shown when orgId is resolved */}
          {!orgLoading && orgId && (
            <>
              {/* Org switcher — hidden for single-org users */}
              {orgs.length > 1 && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-on-surface/40">Organización:</span>
                  <OrgSwitcher
                    orgs={orgs}
                    selectedOrgId={orgId}
                    onChange={handleOrgChange}
                  />
                </div>
              )}

              {/* Tab navigation */}
              <div className="flex items-center gap-1 border-b border-outline-variant -mb-2">
                {(
                  [
                    { id: "overview", label: "Resumen", icon: BarChart3 },
                    { id: "costos", label: "Costos", icon: DollarSign },
                    { id: "frecuentes", label: "Consultas Frecuentes", icon: MessageSquare },
                  ] as { id: TabId; label: string; icon: React.ComponentType<{ className?: string }> }[]
                ).map(({ id, label, icon: Icon }) => (
                  <button
                    key={id}
                    onClick={() => setActiveTab(id)}
                    className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium border-b-2 transition-colors ${
                      activeTab === id
                        ? "border-primary text-primary"
                        : "border-transparent text-on-surface-subtle hover:text-on-surface"
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {label}
                  </button>
                ))}
              </div>

              {/* ── OVERVIEW TAB ──────────────────────────────────────────── */}
              {activeTab === "overview" && (
                <>
                  {/* Stat cards */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                    <StatCard
                      loading={loading}
                      label="Consultas hoy"
                      value={overview?.queries_today ?? 0}
                      icon={<BarChart3 className="w-4 h-4" />}
                      sub={
                        <TrendIndicator value={overview?.queries_today_vs_yesterday_pct ?? null} />
                      }
                    />
                    <StatCard
                      loading={loading}
                      label={`Consultas (${days}d)`}
                      value={overview?.queries_month ?? 0}
                      icon={<TrendingUp className="w-4 h-4" />}
                      sub={
                        <p className="text-xs text-on-surface-subtle">
                          {overview?.queries_week ?? 0} esta semana
                        </p>
                      }
                    />
                    <StatCard
                      loading={loading}
                      label="Latencia promedio"
                      value={`${Math.round(overview?.avg_latency_ms ?? 0)}ms`}
                      icon={<Timer className="w-4 h-4" />}
                      sub={<LatencyBadge ms={overview?.avg_latency_ms ?? null} />}
                    />
                    <StatCard
                      loading={loading}
                      label="Usuarios activos"
                      value={overview?.active_users ?? 0}
                      icon={<Users className="w-4 h-4" />}
                      sub={
                        overview?.satisfaction_rate ? (
                          <div className="flex items-center gap-1 text-xs text-on-surface-subtle">
                            <ThumbsUp className="w-3 h-3 text-status-success" />
                            <span>{overview.satisfaction_rate}% satisfacción</span>
                          </div>
                        ) : null
                      }
                    />
                  </div>

                  {/* Charts row */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* Bar chart */}
                    <div className="bg-surface-container-low border border-outline-variant rounded-lg p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h2 className="font-['Newsreader'] text-lg font-bold text-on-surface">
                            Volumen de consultas
                          </h2>
                          <p className="text-xs text-on-surface-subtle">Últimos {days} días</p>
                        </div>
                        <BarChart3 className="w-4 h-4 text-surface-container-high" />
                      </div>
                      <BarChart data={overview?.queries_trend ?? []} loading={loading} />
                      {!loading && overview?.queries_trend && overview.queries_trend.length > 1 && (
                        <div className="flex justify-between mt-1 text-[10px] text-on-surface-subtle">
                          <span>{overview.queries_trend[0]?.date.slice(5)}</span>
                          <span>
                            {
                              overview.queries_trend[
                                Math.floor(overview.queries_trend.length / 2)
                              ]?.date.slice(5)
                            }
                          </span>
                          <span>
                            {overview.queries_trend[overview.queries_trend.length - 1]?.date.slice(5)}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Donut chart */}
                    <div className="bg-surface-container-low border border-outline-variant rounded-lg p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h2 className="font-['Newsreader'] text-lg font-bold text-on-surface">
                            Por área jurídica
                          </h2>
                          <p className="text-xs text-on-surface-subtle">Distribución del periodo</p>
                        </div>
                      </div>
                      <DonutChart
                        data={overview?.top_areas ?? []}
                        loading={loading}
                      />
                    </div>
                  </div>

                  {/* Tables row */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* Top legal areas table */}
                    <div className="bg-surface-container-low border border-outline-variant rounded-lg overflow-hidden">
                      <div className="px-5 py-4 border-b border-outline-variant bg-surface">
                        <h2 className="font-['Newsreader'] text-base font-bold text-on-surface">
                          Áreas más consultadas
                        </h2>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full min-w-[380px] text-xs">
                          <thead>
                            <tr className="border-b border-outline-variant bg-surface">
                              <th className="text-left px-5 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                                Área
                              </th>
                              <th className="text-right px-4 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                                Consultas
                              </th>
                              <th className="text-right px-4 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                                %
                              </th>
                              <th className="text-right px-5 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                                Tendencia
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {loading
                              ? Array.from({ length: 5 }).map((_, i) => (
                                  <tr
                                    key={i}
                                    className={`border-b border-outline-variant/60 ${
                                      i % 2 === 0 ? "bg-surface-container-low" : "bg-surface"
                                    }`}
                                  >
                                    <td className="px-5 py-3">
                                      <Skeleton className="h-3 w-24" />
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                      <Skeleton className="h-3 w-10 ml-auto" />
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                      <Skeleton className="h-3 w-8 ml-auto" />
                                    </td>
                                    <td className="px-5 py-3 text-right">
                                      <Skeleton className="h-3 w-12 ml-auto" />
                                    </td>
                                  </tr>
                                ))
                              : areas.length === 0
                              ? (
                                <tr>
                                  <td colSpan={4} className="px-5 py-8 text-center text-on-surface-subtle">
                                    Sin datos disponibles
                                  </td>
                                </tr>
                              )
                              : areas.map((a, idx) => {
                                  const meta = AREA_MAP[a.area];
                                  return (
                                    <tr
                                      key={a.area}
                                      className={`border-b border-outline-variant/60 hover:bg-surface-container transition-colors ${
                                        idx % 2 === 0 ? "bg-surface-container-low" : "bg-surface"
                                      }`}
                                    >
                                      <td className="px-5 py-3">
                                        <div className="flex items-center gap-2">
                                          <span
                                            className="w-2 h-2 rounded-full shrink-0"
                                            style={{ background: meta?.hex ?? "#6b7280" }}
                                          />
                                          <span className="text-on-surface">{meta?.name ?? a.area}</span>
                                        </div>
                                      </td>
                                      <td className="px-4 py-3 text-right text-on-surface font-mono">
                                        {a.count.toLocaleString()}
                                      </td>
                                      <td className="px-4 py-3 text-right">
                                        <div className="flex items-center justify-end gap-1.5">
                                          <div className="w-12 h-1.5 bg-surface-container rounded-full overflow-hidden">
                                            <div
                                              className="h-full rounded-full"
                                              style={{
                                                width: `${a.percentage}%`,
                                                background: meta?.hex ?? "#6b7280",
                                              }}
                                            />
                                          </div>
                                          <span className="text-on-surface-variant w-8 text-right">
                                            {a.percentage}%
                                          </span>
                                        </div>
                                      </td>
                                      <td className="px-5 py-3 text-right">
                                        {a.trend === "up" ? (
                                          <span className="flex items-center justify-end gap-0.5 text-status-success">
                                            <TrendingUp className="w-3 h-3" />
                                            {a.change_pct !== null ? `+${a.change_pct}%` : ""}
                                          </span>
                                        ) : a.trend === "down" ? (
                                          <span className="flex items-center justify-end gap-0.5 text-status-danger">
                                            <TrendingDown className="w-3 h-3" />
                                            {a.change_pct !== null ? `${a.change_pct}%` : ""}
                                          </span>
                                        ) : (
                                          <span className="flex items-center justify-end gap-0.5 text-on-surface-subtle">
                                            <Minus className="w-3 h-3" />
                                          </span>
                                        )}
                                      </td>
                                    </tr>
                                  );
                                })}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Model usage table */}
                    <div className="bg-surface-container-low border border-outline-variant rounded-lg overflow-hidden">
                      <div className="px-5 py-4 border-b border-outline-variant bg-surface">
                        <h2 className="font-['Newsreader'] text-base font-bold text-on-surface">
                          Uso por modelo
                        </h2>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full min-w-[360px] text-xs">
                          <thead>
                            <tr className="border-b border-outline-variant bg-surface">
                              <th className="text-left px-5 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                                Modelo
                              </th>
                              <th className="text-right px-4 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                                Consultas
                              </th>
                              <th className="text-right px-5 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                                Latencia prom.
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {loading
                              ? Array.from({ length: 4 }).map((_, i) => (
                                  <tr
                                    key={i}
                                    className={`border-b border-outline-variant/60 ${
                                      i % 2 === 0 ? "bg-surface-container-low" : "bg-surface"
                                    }`}
                                  >
                                    <td className="px-5 py-3">
                                      <Skeleton className="h-3 w-28" />
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                      <Skeleton className="h-3 w-10 ml-auto" />
                                    </td>
                                    <td className="px-5 py-3 text-right">
                                      <Skeleton className="h-3 w-14 ml-auto" />
                                    </td>
                                  </tr>
                                ))
                              : models.length === 0
                              ? (
                                <tr>
                                  <td colSpan={3} className="px-5 py-8 text-center text-on-surface-subtle">
                                    Sin datos disponibles
                                  </td>
                                </tr>
                              )
                              : models.map((m, idx) => (
                                  <tr
                                    key={m.model}
                                    className={`border-b border-outline-variant/60 hover:bg-surface-container transition-colors ${
                                      idx % 2 === 0 ? "bg-surface-container-low" : "bg-surface"
                                    }`}
                                  >
                                    <td className="px-5 py-3">
                                      <div className="space-y-0.5">
                                        <p className="text-on-surface font-medium">
                                          {m.model.split("/").pop() ?? m.model}
                                        </p>
                                        <div className="w-24 h-1 bg-surface-container rounded-full overflow-hidden">
                                          <div
                                            className="h-full bg-primary rounded-full"
                                            style={{ width: `${m.percentage}%` }}
                                          />
                                        </div>
                                      </div>
                                    </td>
                                    <td className="px-4 py-3 text-right text-on-surface font-mono">
                                      {m.count.toLocaleString()}
                                      <span className="text-on-surface-subtle ml-1">({m.percentage}%)</span>
                                    </td>
                                    <td className="px-5 py-3 text-right">
                                      <LatencyBadge ms={m.avg_latency_ms} />
                                    </td>
                                  </tr>
                                ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>

                  {/* Recent queries */}
                  <div className="bg-surface-container-low border border-outline-variant rounded-lg overflow-hidden">
                    <div className="px-5 py-4 border-b border-outline-variant bg-surface flex items-center justify-between">
                      <div>
                        <h2 className="font-['Newsreader'] text-base font-bold text-on-surface">
                          Consultas recientes
                        </h2>
                        <p className="text-xs text-on-surface-subtle">Últimas 20 respuestas del asistente</p>
                      </div>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[600px] text-xs">
                        <thead>
                          <tr className="border-b border-outline-variant bg-surface">
                            <th className="text-left px-5 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                              Fecha
                            </th>
                            <th className="text-left px-4 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                              Usuario
                            </th>
                            <th className="text-left px-4 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                              Área
                            </th>
                            <th className="text-left px-4 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                              Modelo
                            </th>
                            <th className="text-right px-5 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                              Latencia
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {loading
                            ? Array.from({ length: 8 }).map((_, i) => (
                                <tr
                                  key={i}
                                  className={`border-b border-outline-variant/60 ${
                                    i % 2 === 0 ? "bg-surface-container-low" : "bg-surface"
                                  }`}
                                >
                                  {Array.from({ length: 5 }).map((__, j) => (
                                    <td key={j} className="px-5 py-3">
                                      <Skeleton className="h-3 w-full" />
                                    </td>
                                  ))}
                                </tr>
                              ))
                            : queries.length === 0
                            ? (
                              <tr>
                                <td colSpan={5} className="px-5 py-10 text-center text-on-surface-subtle">
                                  No hay consultas registradas en este periodo
                                </td>
                              </tr>
                            )
                            : queries.map((q, idx) => (
                                <tr
                                  key={q.id}
                                  className={`border-b border-outline-variant/60 hover:bg-surface-container transition-colors ${
                                    idx % 2 === 0 ? "bg-surface-container-low" : "bg-surface"
                                  }`}
                                >
                                  <td className="px-5 py-3 text-on-surface-subtle whitespace-nowrap">
                                    {q.created_at
                                      ? new Date(q.created_at).toLocaleString("es-PE", {
                                          month: "short",
                                          day: "numeric",
                                          hour: "2-digit",
                                          minute: "2-digit",
                                        })
                                      : "—"}
                                  </td>
                                  <td className="px-4 py-3 text-on-surface max-w-[160px] truncate">
                                    {q.user_email}
                                  </td>
                                  <td className="px-4 py-3">
                                    <AreaBadge area={q.legal_area} />
                                  </td>
                                  <td className="px-4 py-3 text-on-surface-variant max-w-[140px] truncate">
                                    {q.model?.split("/").pop() ?? "—"}
                                  </td>
                                  <td className="px-5 py-3 text-right">
                                    <LatencyBadge ms={q.latency_ms} />
                                  </td>
                                </tr>
                              ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <p className="text-center text-[11px] text-surface-container-high pb-2">
                    Datos en tiempo real — actualizado al momento de la carga
                  </p>
                </>
              )}
              {/* ── END OVERVIEW TAB ────────────────────────────────────── */}

              {/* ── COSTOS TAB ─────────────────────────────────────────── */}
              {activeTab === "costos" && (
                <>
                  {/* Summary cards */}
                  <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                    <StatCard
                      loading={loading}
                      label={`Costo total (${days}d)`}
                      value={costs ? `$${costs.total_cost_usd.toFixed(4)}` : "$0.0000"}
                      icon={<DollarSign className="w-4 h-4" />}
                      sub={<p className="text-xs text-on-surface-subtle">Estimado USD</p>}
                    />
                    <StatCard
                      loading={loading}
                      label="Modelos en uso"
                      value={costs?.models.length ?? 0}
                      icon={<BarChart3 className="w-4 h-4" />}
                    />
                    <StatCard
                      loading={loading}
                      label="Costo promedio / consulta"
                      value={
                        costs && costs.models.reduce((s, m) => s + m.query_count, 0) > 0
                          ? `$${(
                              costs.total_cost_usd /
                              costs.models.reduce((s, m) => s + m.query_count, 0)
                            ).toFixed(5)}`
                          : "$0.00000"
                      }
                      icon={<TrendingUp className="w-4 h-4" />}
                    />
                  </div>

                  {/* Cost breakdown table */}
                  <div className="bg-surface-container-low border border-outline-variant rounded-lg overflow-hidden">
                    <div className="px-5 py-4 border-b border-outline-variant bg-surface">
                      <h2 className="font-['Newsreader'] text-base font-bold text-on-surface">
                        Desglose por modelo
                      </h2>
                      <p className="text-xs text-on-surface-subtle">
                        Costo estimado basado en tokens usados
                      </p>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[540px] text-xs">
                        <thead>
                          <tr className="border-b border-outline-variant bg-surface">
                            <th className="text-left px-5 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                              Modelo
                            </th>
                            <th className="text-right px-4 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                              Consultas
                            </th>
                            <th className="text-right px-4 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                              Tokens totales
                            </th>
                            <th className="text-right px-4 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                              Tokens / consulta
                            </th>
                            <th className="text-right px-5 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                              Costo USD
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {loading ? (
                            Array.from({ length: 4 }).map((_, i) => (
                              <tr
                                key={i}
                                className={`border-b border-outline-variant/60 ${
                                  i % 2 === 0 ? "bg-surface-container-low" : "bg-surface"
                                }`}
                              >
                                {Array.from({ length: 5 }).map((__, j) => (
                                  <td key={j} className="px-5 py-3">
                                    <Skeleton className="h-3 w-full" />
                                  </td>
                                ))}
                              </tr>
                            ))
                          ) : !costs || costs.models.length === 0 ? (
                            <tr>
                              <td colSpan={5} className="px-5 py-10 text-center text-on-surface-subtle">
                                Sin datos disponibles
                              </td>
                            </tr>
                          ) : (
                            (() => {
                              const maxCost = Math.max(
                                ...costs.models.map((m) => m.estimated_cost_usd),
                                0.000001
                              );
                              return costs.models.map((m, idx) => {
                                const barPct = Math.max(
                                  (m.estimated_cost_usd / maxCost) * 100,
                                  2
                                );
                                return (
                                  <tr
                                    key={m.model}
                                    className={`border-b border-outline-variant/60 hover:bg-surface-container transition-colors ${
                                      idx % 2 === 0 ? "bg-surface-container-low" : "bg-surface"
                                    }`}
                                  >
                                    <td className="px-5 py-3">
                                      <div className="space-y-1">
                                        <p className="text-on-surface font-medium">
                                          {m.model.split("/").pop() ?? m.model}
                                        </p>
                                        <div className="w-28 h-1.5 bg-surface-container rounded-full overflow-hidden">
                                          <div
                                            className="h-full bg-primary rounded-full"
                                            style={{ width: `${barPct}%` }}
                                          />
                                        </div>
                                      </div>
                                    </td>
                                    <td className="px-4 py-3 text-right text-on-surface font-mono">
                                      {m.query_count.toLocaleString()}
                                    </td>
                                    <td className="px-4 py-3 text-right text-on-surface font-mono">
                                      {m.total_tokens.toLocaleString()}
                                    </td>
                                    <td className="px-4 py-3 text-right text-on-surface-variant font-mono">
                                      {Math.round(m.avg_tokens_per_query).toLocaleString()}
                                    </td>
                                    <td className="px-5 py-3 text-right">
                                      <span className="text-status-success font-mono font-medium">
                                        ${m.estimated_cost_usd.toFixed(4)}
                                      </span>
                                    </td>
                                  </tr>
                                );
                              });
                            })()
                          )}
                        </tbody>
                        {costs && costs.models.length > 0 && (
                          <tfoot>
                            <tr className="border-t border-outline-variant bg-surface">
                              <td className="px-5 py-3 text-on-surface-variant font-medium">
                                Total
                              </td>
                              <td className="px-4 py-3 text-right text-on-surface font-mono font-medium">
                                {costs.models
                                  .reduce((s, m) => s + m.query_count, 0)
                                  .toLocaleString()}
                              </td>
                              <td className="px-4 py-3 text-right text-on-surface font-mono font-medium">
                                {costs.models
                                  .reduce((s, m) => s + m.total_tokens, 0)
                                  .toLocaleString()}
                              </td>
                              <td className="px-4 py-3" />
                              <td className="px-5 py-3 text-right">
                                <span className="font-['Newsreader'] text-base font-bold text-primary">
                                  ${costs.total_cost_usd.toFixed(4)}
                                </span>
                              </td>
                            </tr>
                          </tfoot>
                        )}
                      </table>
                    </div>
                  </div>

                  <p className="text-center text-[11px] text-surface-container-high pb-2">
                    Costos estimados · Las tarifas reales pueden variar según el proveedor
                  </p>
                </>
              )}
              {/* ── END COSTOS TAB ──────────────────────────────────────── */}

              {/* ── CONSULTAS FRECUENTES TAB ────────────────────────────── */}
              {activeTab === "frecuentes" && (
                <>
                  <div className="bg-surface-container-low border border-outline-variant rounded-lg overflow-hidden">
                    <div className="px-5 py-4 border-b border-outline-variant bg-surface flex items-center justify-between">
                      <div>
                        <h2 className="font-['Newsreader'] text-base font-bold text-on-surface">
                          Patrones de consulta más frecuentes
                        </h2>
                        <p className="text-xs text-on-surface-subtle">
                          Agrupados por los primeros 100 caracteres · Últimos {days} días
                        </p>
                      </div>
                      <MessageSquare className="w-4 h-4 text-surface-container-high" />
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[560px] text-xs">
                        <thead>
                          <tr className="border-b border-outline-variant bg-surface">
                            <th className="text-left px-5 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                              Vista previa
                            </th>
                            <th className="text-right px-4 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                              Veces
                            </th>
                            <th className="text-left px-4 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                              Áreas
                            </th>
                            <th className="text-right px-5 py-3 text-on-surface-subtle font-medium uppercase tracking-wider">
                              Última vez
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {loading ? (
                            Array.from({ length: 8 }).map((_, i) => (
                              <tr
                                key={i}
                                className={`border-b border-outline-variant/60 ${
                                  i % 2 === 0 ? "bg-surface-container-low" : "bg-surface"
                                }`}
                              >
                                {Array.from({ length: 4 }).map((__, j) => (
                                  <td key={j} className="px-5 py-3">
                                    <Skeleton className="h-3 w-full" />
                                  </td>
                                ))}
                              </tr>
                            ))
                          ) : !topQueries || topQueries.queries.length === 0 ? (
                            <tr>
                              <td colSpan={4} className="px-5 py-10 text-center text-on-surface-subtle">
                                Sin consultas registradas en este periodo
                              </td>
                            </tr>
                          ) : (
                            topQueries.queries.map((q, idx) => (
                              <tr
                                key={idx}
                                className={`border-b border-outline-variant/60 hover:bg-surface-container transition-colors ${
                                  idx % 2 === 0 ? "bg-surface-container-low" : "bg-surface"
                                }`}
                              >
                                <td className="px-5 py-3 max-w-[280px]">
                                  <p
                                    className="text-on-surface truncate"
                                    title={q.query_preview}
                                  >
                                    {q.query_preview}
                                  </p>
                                </td>
                                <td className="px-4 py-3 text-right">
                                  <span className="inline-flex items-center justify-center w-8 h-6 rounded bg-primary/10 border border-primary/20 text-primary font-mono font-bold">
                                    {q.count}
                                  </span>
                                </td>
                                <td className="px-4 py-3">
                                  <div className="flex flex-wrap gap-1">
                                    {q.legal_areas.length > 0 ? (
                                      q.legal_areas.slice(0, 3).map((area) => (
                                        <AreaBadge key={area} area={area} />
                                      ))
                                    ) : (
                                      <span className="text-on-surface-subtle">—</span>
                                    )}
                                  </div>
                                </td>
                                <td className="px-5 py-3 text-right text-on-surface-subtle whitespace-nowrap">
                                  {q.last_asked
                                    ? new Date(q.last_asked).toLocaleDateString("es-PE", {
                                        month: "short",
                                        day: "numeric",
                                      })
                                    : "—"}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <p className="text-center text-[11px] text-surface-container-high pb-2">
                    Patrones calculados sobre los primeros 100 caracteres normalizados de cada consulta
                  </p>
                </>
              )}
              {/* ── END CONSULTAS FRECUENTES TAB ────────────────────────── */}
            </>
          )}
        </main>
      </div>
    </AppLayout>
  );
}
