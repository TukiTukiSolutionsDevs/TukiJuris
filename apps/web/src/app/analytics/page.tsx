"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth/AuthContext";
import { AppLayout } from "@/components/AppLayout";
import { InternalPageHeader } from "@/components/shell/InternalPageHeader";
import { ShellUtilityActions } from "@/components/shell/ShellUtilityActions";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Minus,
  ThumbsUp,
  Timer,
  Users,
  RefreshCw,
  BookOpen,
  Shield,
  Briefcase,
  Landmark,
  Gavel,
  Building2,
  ScrollText,
  FileCheck,
  Globe,
  Lock,
  BadgeCheck,
  Download,
  DollarSign,
  MessageSquare,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const LEGAL_AREAS = [
  { id: "civil", name: "Civil", icon: BookOpen, color: "text-blue-400", bg: "bg-blue-500", hex: "#60a5fa" },
  { id: "penal", name: "Penal", icon: Shield, color: "text-red-400", bg: "bg-red-500", hex: "#f87171" },
  { id: "laboral", name: "Laboral", icon: Briefcase, color: "text-green-400", bg: "bg-green-500", hex: "#4ade80" },
  { id: "tributario", name: "Tributario", icon: Landmark, color: "text-yellow-400", bg: "bg-yellow-500", hex: "#facc15" },
  { id: "constitucional", name: "Constitucional", icon: Gavel, color: "text-purple-400", bg: "bg-purple-500", hex: "#c084fc" },
  { id: "administrativo", name: "Administrativo", icon: Building2, color: "text-orange-400", bg: "bg-orange-500", hex: "#fb923c" },
  { id: "corporativo", name: "Corporativo", icon: ScrollText, color: "text-cyan-400", bg: "bg-cyan-500", hex: "#22d3ee" },
  { id: "registral", name: "Registral", icon: FileCheck, color: "text-pink-400", bg: "bg-pink-500", hex: "#f472b6" },
  { id: "comercio_exterior", name: "Comercio Ext.", icon: Globe, color: "text-teal-400", bg: "bg-teal-500", hex: "#2dd4bf" },
  { id: "compliance", name: "Compliance", icon: Lock, color: "text-indigo-400", bg: "bg-indigo-500", hex: "#818cf8" },
  { id: "competencia", name: "Competencia/PI", icon: BadgeCheck, color: "text-amber-400", bg: "bg-amber-500", hex: "#f59e0b" },
];

const AREA_MAP = Object.fromEntries(LEGAL_AREAS.map((a) => [a.id, a]));

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
      className={`animate-pulse bg-[#25242b] rounded ${className ?? ""}`}
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
        <p className="section-eyebrow text-[#7c7885] leading-tight">{label}</p>
        {icon && <div className="text-[#7c7885] shrink-0">{icon}</div>}
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
            className="flex-1 animate-pulse rounded bg-[#25242b]"
            style={{ height: `${height}%` }}
          />
        ))}
      </div>
    );
  }

  if (!data.length) {
    return (
      <div className="h-36 flex items-center justify-center text-[#7c7885] text-sm">
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
            <div className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 hidden group-hover:block bg-[#0e0e12] border border-[rgba(79,70,51,0.3)] rounded px-2 py-1 text-[10px] text-on-surface whitespace-nowrap z-10 pointer-events-none">
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
      <div className="h-40 flex items-center justify-center text-[#7c7885] text-sm">
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
              <span className="text-[#a09ba8] truncate">{area?.name ?? d.area}</span>
              <span className="text-[#7c7885] ml-auto pl-2">{pct}%</span>
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
  if (ms === null || ms === undefined) return <span className="text-[#7c7885]">—</span>;
  const color =
    ms < 2000 ? "text-green-400" : ms < 5000 ? "text-primary" : "text-red-400";
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
    return <span className="text-[#7c7885] text-xs">—</span>;
  }
  if (value > 0) {
    return (
      <span className="flex items-center gap-0.5 text-xs text-green-400">
        <TrendingUp className="w-3 h-3" />
        +{value}{suffix}
      </span>
    );
  }
  if (value < 0) {
    return (
      <span className="flex items-center gap-0.5 text-xs text-red-400">
        <TrendingDown className="w-3 h-3" />
        {value}{suffix}
      </span>
    );
  }
  return (
    <span className="flex items-center gap-0.5 text-xs text-[#7c7885]">
      <Minus className="w-3 h-3" />
      0{suffix}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Area badge (inline)
// ---------------------------------------------------------------------------

function AreaBadge({ area }: { area: string | null }) {
  if (!area) return <span className="text-[#7c7885] text-xs">—</span>;
  const a = AREA_MAP[area];
  return (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-surface-container-low border border-[rgba(79,70,51,0.15)]">
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

  const { authFetch } = useAuth();

  // Fetch user's organization on mount
  useEffect(() => {
    authFetch("/api/organizations/")
      .then((r) => (r.ok ? r.json() : []))
      .then((orgs: { id: string }[]) => {
        if (orgs.length > 0) {
          setOrgId(orgs[0].id);
        }
      })
      .catch(() => {
        // silently fail — no org found
      })
      .finally(() => setOrgLoading(false));
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
    [days, orgId]
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
  }, [days, orgId]);

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
            <div className="flex items-center gap-1 bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-1">
              {dateRangeOptions.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setDays(opt.value)}
                  className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                    days === opt.value
                      ? "bg-primary/10 text-primary"
                      : "text-[#a09ba8] hover:text-on-surface"
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
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold uppercase tracking-widest text-on-surface border border-[rgba(79,70,51,0.15)] hover:bg-surface-container-high transition-colors disabled:opacity-50"
              title="Exportar CSV"
            >
              <Download className={`w-3.5 h-3.5 ${exporting ? "animate-bounce" : ""}`} />
              <span className="hidden sm:inline">Exportar CSV</span>
            </button>

            {/* Refresh button */}
            <button
              onClick={() => fetchData(true)}
              disabled={refreshing}
              className="p-2 rounded-lg text-[#7c7885] hover:text-on-surface border border-[rgba(79,70,51,0.15)] hover:bg-surface-container-high transition-colors disabled:opacity-50"
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
              <span className="text-[#a09ba8] text-sm">Cargando organización...</span>
            </div>
          )}

          {/* No org state */}
          {!orgLoading && !orgId && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <BarChart3 className="w-12 h-12 text-[#25242b] mb-4" />
              <h2 className="font-['Newsreader'] text-3xl font-bold text-on-surface mb-2">
                Sin organización
              </h2>
              <p className="text-[#7c7885] text-sm max-w-sm">
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
            <div className="bg-red-950/50 border border-red-800/50 rounded-lg px-4 py-3 text-sm text-red-300">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Main content — only shown when orgId is resolved */}
          {!orgLoading && orgId && (
            <>
              {/* Tab navigation */}
              <div className="flex items-center gap-1 border-b border-[rgba(79,70,51,0.15)] -mb-2">
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
                        : "border-transparent text-[#7c7885] hover:text-on-surface"
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
                        <p className="text-xs text-[#7c7885]">
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
                          <div className="flex items-center gap-1 text-xs text-[#7c7885]">
                            <ThumbsUp className="w-3 h-3 text-green-400" />
                            <span>{overview.satisfaction_rate}% satisfacción</span>
                          </div>
                        ) : null
                      }
                    />
                  </div>

                  {/* Charts row */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* Bar chart */}
                    <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h2 className="font-['Newsreader'] text-lg font-bold text-on-surface">
                            Volumen de consultas
                          </h2>
                          <p className="text-xs text-[#7c7885]">Últimos {days} días</p>
                        </div>
                        <BarChart3 className="w-4 h-4 text-[#25242b]" />
                      </div>
                      <BarChart data={overview?.queries_trend ?? []} loading={loading} />
                      {!loading && overview?.queries_trend && overview.queries_trend.length > 1 && (
                        <div className="flex justify-between mt-1 text-[10px] text-[#7c7885]">
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
                    <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h2 className="font-['Newsreader'] text-lg font-bold text-on-surface">
                            Por área jurídica
                          </h2>
                          <p className="text-xs text-[#7c7885]">Distribución del periodo</p>
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
                    <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg overflow-hidden">
                      <div className="px-5 py-4 border-b border-[rgba(79,70,51,0.15)] bg-surface">
                        <h2 className="font-['Newsreader'] text-base font-bold text-on-surface">
                          Áreas más consultadas
                        </h2>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full min-w-[380px] text-xs">
                          <thead>
                            <tr className="border-b border-[rgba(79,70,51,0.15)] bg-surface">
                              <th className="text-left px-5 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                                Área
                              </th>
                              <th className="text-right px-4 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                                Consultas
                              </th>
                              <th className="text-right px-4 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                                %
                              </th>
                              <th className="text-right px-5 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                                Tendencia
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {loading
                              ? Array.from({ length: 5 }).map((_, i) => (
                                  <tr
                                    key={i}
                                    className={`border-b border-[rgba(79,70,51,0.1)] ${
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
                                  <td colSpan={4} className="px-5 py-8 text-center text-[#7c7885]">
                                    Sin datos disponibles
                                  </td>
                                </tr>
                              )
                              : areas.map((a, idx) => {
                                  const meta = AREA_MAP[a.area];
                                  return (
                                    <tr
                                      key={a.area}
                                      className={`border-b border-[rgba(79,70,51,0.1)] hover:bg-[#25242b] transition-colors ${
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
                                          <div className="w-12 h-1.5 bg-[#25242b] rounded-full overflow-hidden">
                                            <div
                                              className="h-full rounded-full"
                                              style={{
                                                width: `${a.percentage}%`,
                                                background: meta?.hex ?? "#6b7280",
                                              }}
                                            />
                                          </div>
                                          <span className="text-[#a09ba8] w-8 text-right">
                                            {a.percentage}%
                                          </span>
                                        </div>
                                      </td>
                                      <td className="px-5 py-3 text-right">
                                        {a.trend === "up" ? (
                                          <span className="flex items-center justify-end gap-0.5 text-green-400">
                                            <TrendingUp className="w-3 h-3" />
                                            {a.change_pct !== null ? `+${a.change_pct}%` : ""}
                                          </span>
                                        ) : a.trend === "down" ? (
                                          <span className="flex items-center justify-end gap-0.5 text-red-400">
                                            <TrendingDown className="w-3 h-3" />
                                            {a.change_pct !== null ? `${a.change_pct}%` : ""}
                                          </span>
                                        ) : (
                                          <span className="flex items-center justify-end gap-0.5 text-[#7c7885]">
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
                    <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg overflow-hidden">
                      <div className="px-5 py-4 border-b border-[rgba(79,70,51,0.15)] bg-surface">
                        <h2 className="font-['Newsreader'] text-base font-bold text-on-surface">
                          Uso por modelo
                        </h2>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full min-w-[360px] text-xs">
                          <thead>
                            <tr className="border-b border-[rgba(79,70,51,0.15)] bg-surface">
                              <th className="text-left px-5 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                                Modelo
                              </th>
                              <th className="text-right px-4 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                                Consultas
                              </th>
                              <th className="text-right px-5 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                                Latencia prom.
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {loading
                              ? Array.from({ length: 4 }).map((_, i) => (
                                  <tr
                                    key={i}
                                    className={`border-b border-[rgba(79,70,51,0.1)] ${
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
                                  <td colSpan={3} className="px-5 py-8 text-center text-[#7c7885]">
                                    Sin datos disponibles
                                  </td>
                                </tr>
                              )
                              : models.map((m, idx) => (
                                  <tr
                                    key={m.model}
                                    className={`border-b border-[rgba(79,70,51,0.1)] hover:bg-[#25242b] transition-colors ${
                                      idx % 2 === 0 ? "bg-surface-container-low" : "bg-surface"
                                    }`}
                                  >
                                    <td className="px-5 py-3">
                                      <div className="space-y-0.5">
                                        <p className="text-on-surface font-medium">
                                          {m.model.split("/").pop() ?? m.model}
                                        </p>
                                        <div className="w-24 h-1 bg-[#25242b] rounded-full overflow-hidden">
                                          <div
                                            className="h-full bg-primary rounded-full"
                                            style={{ width: `${m.percentage}%` }}
                                          />
                                        </div>
                                      </div>
                                    </td>
                                    <td className="px-4 py-3 text-right text-on-surface font-mono">
                                      {m.count.toLocaleString()}
                                      <span className="text-[#7c7885] ml-1">({m.percentage}%)</span>
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
                  <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg overflow-hidden">
                    <div className="px-5 py-4 border-b border-[rgba(79,70,51,0.15)] bg-surface flex items-center justify-between">
                      <div>
                        <h2 className="font-['Newsreader'] text-base font-bold text-on-surface">
                          Consultas recientes
                        </h2>
                        <p className="text-xs text-[#7c7885]">Últimas 20 respuestas del asistente</p>
                      </div>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[600px] text-xs">
                        <thead>
                          <tr className="border-b border-[rgba(79,70,51,0.15)] bg-surface">
                            <th className="text-left px-5 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                              Fecha
                            </th>
                            <th className="text-left px-4 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                              Usuario
                            </th>
                            <th className="text-left px-4 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                              Área
                            </th>
                            <th className="text-left px-4 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                              Modelo
                            </th>
                            <th className="text-right px-5 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                              Latencia
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {loading
                            ? Array.from({ length: 8 }).map((_, i) => (
                                <tr
                                  key={i}
                                  className={`border-b border-[rgba(79,70,51,0.1)] ${
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
                                <td colSpan={5} className="px-5 py-10 text-center text-[#7c7885]">
                                  No hay consultas registradas en este periodo
                                </td>
                              </tr>
                            )
                            : queries.map((q, idx) => (
                                <tr
                                  key={q.id}
                                  className={`border-b border-[rgba(79,70,51,0.1)] hover:bg-[#25242b] transition-colors ${
                                    idx % 2 === 0 ? "bg-surface-container-low" : "bg-surface"
                                  }`}
                                >
                                  <td className="px-5 py-3 text-[#7c7885] whitespace-nowrap">
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
                                  <td className="px-4 py-3 text-[#a09ba8] max-w-[140px] truncate">
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

                  <p className="text-center text-[11px] text-[#25242b] pb-2">
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
                      sub={<p className="text-xs text-[#7c7885]">Estimado USD</p>}
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
                  <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg overflow-hidden">
                    <div className="px-5 py-4 border-b border-[rgba(79,70,51,0.15)] bg-surface">
                      <h2 className="font-['Newsreader'] text-base font-bold text-on-surface">
                        Desglose por modelo
                      </h2>
                      <p className="text-xs text-[#7c7885]">
                        Costo estimado basado en tokens usados
                      </p>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[540px] text-xs">
                        <thead>
                          <tr className="border-b border-[rgba(79,70,51,0.15)] bg-surface">
                            <th className="text-left px-5 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                              Modelo
                            </th>
                            <th className="text-right px-4 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                              Consultas
                            </th>
                            <th className="text-right px-4 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                              Tokens totales
                            </th>
                            <th className="text-right px-4 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                              Tokens / consulta
                            </th>
                            <th className="text-right px-5 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                              Costo USD
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {loading ? (
                            Array.from({ length: 4 }).map((_, i) => (
                              <tr
                                key={i}
                                className={`border-b border-[rgba(79,70,51,0.1)] ${
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
                              <td colSpan={5} className="px-5 py-10 text-center text-[#7c7885]">
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
                                    className={`border-b border-[rgba(79,70,51,0.1)] hover:bg-[#25242b] transition-colors ${
                                      idx % 2 === 0 ? "bg-surface-container-low" : "bg-surface"
                                    }`}
                                  >
                                    <td className="px-5 py-3">
                                      <div className="space-y-1">
                                        <p className="text-on-surface font-medium">
                                          {m.model.split("/").pop() ?? m.model}
                                        </p>
                                        <div className="w-28 h-1.5 bg-[#25242b] rounded-full overflow-hidden">
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
                                    <td className="px-4 py-3 text-right text-[#a09ba8] font-mono">
                                      {Math.round(m.avg_tokens_per_query).toLocaleString()}
                                    </td>
                                    <td className="px-5 py-3 text-right">
                                      <span className="text-green-400 font-mono font-medium">
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
                            <tr className="border-t border-[rgba(79,70,51,0.2)] bg-surface">
                              <td className="px-5 py-3 text-[#a09ba8] font-medium">
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

                  <p className="text-center text-[11px] text-[#25242b] pb-2">
                    Costos estimados · Las tarifas reales pueden variar según el proveedor
                  </p>
                </>
              )}
              {/* ── END COSTOS TAB ──────────────────────────────────────── */}

              {/* ── CONSULTAS FRECUENTES TAB ────────────────────────────── */}
              {activeTab === "frecuentes" && (
                <>
                  <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg overflow-hidden">
                    <div className="px-5 py-4 border-b border-[rgba(79,70,51,0.15)] bg-surface flex items-center justify-between">
                      <div>
                        <h2 className="font-['Newsreader'] text-base font-bold text-on-surface">
                          Patrones de consulta más frecuentes
                        </h2>
                        <p className="text-xs text-[#7c7885]">
                          Agrupados por los primeros 100 caracteres · Últimos {days} días
                        </p>
                      </div>
                      <MessageSquare className="w-4 h-4 text-[#25242b]" />
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[560px] text-xs">
                        <thead>
                          <tr className="border-b border-[rgba(79,70,51,0.15)] bg-surface">
                            <th className="text-left px-5 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                              Vista previa
                            </th>
                            <th className="text-right px-4 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                              Veces
                            </th>
                            <th className="text-left px-4 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                              Áreas
                            </th>
                            <th className="text-right px-5 py-3 text-[#7c7885] font-medium uppercase tracking-wider">
                              Última vez
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {loading ? (
                            Array.from({ length: 8 }).map((_, i) => (
                              <tr
                                key={i}
                                className={`border-b border-[rgba(79,70,51,0.1)] ${
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
                              <td colSpan={4} className="px-5 py-10 text-center text-[#7c7885]">
                                Sin consultas registradas en este periodo
                              </td>
                            </tr>
                          ) : (
                            topQueries.queries.map((q, idx) => (
                              <tr
                                key={idx}
                                className={`border-b border-[rgba(79,70,51,0.1)] hover:bg-[#25242b] transition-colors ${
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
                                      <span className="text-[#7c7885]">—</span>
                                    )}
                                  </div>
                                </td>
                                <td className="px-5 py-3 text-right text-[#7c7885] whitespace-nowrap">
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

                  <p className="text-center text-[11px] text-[#25242b] pb-2">
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
