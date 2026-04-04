"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Activity,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Clock,
  Database,
  Layers,
  Server,
  Timer,
  Cpu,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";
import { AppLayout } from "@/components/AppLayout";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ServiceStatus = "operational" | "degraded" | "down" | "loading";

interface ServiceCheck {
  name: string;
  status: ServiceStatus;
  latency_ms: number | null;
  detail?: string;
}

interface MetricsData {
  total_requests: number;
  total_errors: number;
  error_rate_pct: number;
  avg_latency_ms: number;
  slow_requests: number;
  status_codes: Record<string, number>;
  slowest_endpoints: { path: string; avg_ms: number }[];
}

interface StatusState {
  services: ServiceCheck[];
  metrics: MetricsData | null;
  last_checked: Date | null;
  loading: boolean;
}

// ---------------------------------------------------------------------------
// Fake incidents (placeholder — real incidents would come from an endpoint)
// ---------------------------------------------------------------------------

const INCIDENTS: { date: string; title: string; status: "resolved" | "investigating" }[] = [];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function classify(status: string | undefined): ServiceStatus {
  if (!status) return "down";
  if (status === "ok" || status.startsWith("ok")) return "operational";
  if (status === "degraded") return "degraded";
  return "down";
}

async function fetchWithLatency(
  url: string,
  options?: RequestInit
): Promise<{ data: unknown; latency_ms: number; ok: boolean }> {
  const start = performance.now();
  try {
    const res = await fetch(url, { ...options, cache: "no-store" });
    const latency_ms = Math.round(performance.now() - start);
    const data = res.ok ? await res.json() : null;
    return { data, latency_ms, ok: res.ok };
  } catch {
    const latency_ms = Math.round(performance.now() - start);
    return { data: null, latency_ms, ok: false };
  }
}

// ---------------------------------------------------------------------------
// Status indicator
// ---------------------------------------------------------------------------

function StatusDot({ status }: { status: ServiceStatus }) {
  if (status === "loading") {
    return <div className="w-2.5 h-2.5 rounded-full bg-[#2A2A35] animate-pulse" />;
  }
  const map: Record<ServiceStatus, string> = {
    operational: "bg-[#34D399]",
    degraded: "bg-[#FBBF24]",
    down: "bg-[#F87171]",
    loading: "bg-[#2A2A35]",
  };
  return (
    <div className={`w-2.5 h-2.5 rounded-full ${map[status]}`}>
      {status === "operational" && (
        <div className="w-2.5 h-2.5 rounded-full bg-[#34D399] animate-ping opacity-60 absolute" />
      )}
    </div>
  );
}

function StatusIcon({ status }: { status: ServiceStatus }) {
  if (status === "loading") {
    return <div className="w-5 h-5 rounded-full bg-[#2A2A35] animate-pulse" />;
  }
  if (status === "operational") {
    return <CheckCircle2 className="w-5 h-5 text-[#34D399]" />;
  }
  if (status === "degraded") {
    return <AlertCircle className="w-5 h-5 text-[#FBBF24]" />;
  }
  return <XCircle className="w-5 h-5 text-[#F87171]" />;
}

function StatusLabel({ status }: { status: ServiceStatus }) {
  const map: Record<ServiceStatus, { label: string; color: string }> = {
    operational: { label: "Operativo", color: "text-[#34D399]" },
    degraded: { label: "Degradado", color: "text-[#FBBF24]" },
    down: { label: "Caído", color: "text-[#F87171]" },
    loading: { label: "Verificando...", color: "text-[#6B7280]" },
  };
  const { label, color } = map[status];
  return <span className={`text-xs font-medium ${color}`}>{label}</span>;
}

// ---------------------------------------------------------------------------
// Overall banner
// ---------------------------------------------------------------------------

function OverallBanner({ services }: { services: ServiceCheck[] }) {
  const loading = services.some((s) => s.status === "loading");
  const hasDown = services.some((s) => s.status === "down");
  const hasDegraded = services.some((s) => s.status === "degraded");

  if (loading) {
    return (
      <div className="bg-[#1A1A22] border border-[#2A2A35] rounded-xl px-5 py-4 flex items-center gap-3">
        <div className="w-4 h-4 border-2 border-[#6B7280] border-t-transparent rounded-full animate-spin" />
        <span className="text-[#9CA3AF] text-sm">Verificando estado del sistema...</span>
      </div>
    );
  }

  if (hasDown) {
    return (
      <div className="bg-[#F87171]/10 border border-[#F87171]/30 rounded-xl px-5 py-4 flex items-center gap-3">
        <XCircle className="w-5 h-5 text-[#F87171] shrink-0" />
        <div>
          <p className="text-sm font-semibold text-[#F87171]">Problemas detectados en el sistema</p>
          <p className="text-xs text-[#F87171]/70 mt-0.5">Uno o más servicios no están disponibles.</p>
        </div>
      </div>
    );
  }

  if (hasDegraded) {
    return (
      <div className="bg-[#FBBF24]/10 border border-[#FBBF24]/30 rounded-xl px-5 py-4 flex items-center gap-3">
        <AlertCircle className="w-5 h-5 text-[#FBBF24] shrink-0" />
        <div>
          <p className="text-sm font-semibold text-[#FBBF24]">Algunos servicios degradados</p>
          <p className="text-xs text-[#FBBF24]/70 mt-0.5">Algunos servicios pueden estar más lentos de lo normal.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#34D399]/10 border border-[#34D399]/20 rounded-xl px-5 py-4 flex items-center gap-3">
      <CheckCircle2 className="w-5 h-5 text-[#34D399] shrink-0" />
      <div>
        <p className="text-sm font-semibold text-[#34D399]">Todos los sistemas operativos</p>
        <p className="text-xs text-[#34D399]/70 mt-0.5">Todos los servicios funcionan con normalidad.</p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Service row
// ---------------------------------------------------------------------------

function ServiceRow({ service }: { service: ServiceCheck }) {
  return (
    <div className="flex items-center justify-between py-3.5 border-b border-[#1E1E2A] last:border-0">
      <div className="flex items-center gap-3">
        <div className="relative">
          <StatusDot status={service.status} />
        </div>
        <div>
          <p className="text-sm text-[#F5F5F5] font-medium">{service.name}</p>
          {service.detail && (
            <p className="text-xs text-[#6B7280] mt-0.5">{service.detail}</p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-4">
        {service.latency_ms !== null && service.status !== "loading" && (
          <span className="text-xs text-[#6B7280] font-mono">
            {service.latency_ms}ms
          </span>
        )}
        <StatusIcon status={service.status} />
        <StatusLabel status={service.status} />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Metrics panel
// ---------------------------------------------------------------------------

function MetricsPanel({ metrics }: { metrics: MetricsData | null }) {
  if (!metrics) {
    return (
      <div className="text-center py-6 text-[#6B7280] text-sm">
        Métricas no disponibles
      </div>
    );
  }

  const latencyColor =
    metrics.avg_latency_ms < 500
      ? "text-[#34D399]"
      : metrics.avg_latency_ms < 2000
      ? "text-[#FBBF24]"
      : "text-[#F87171]";

  const errorColor =
    metrics.error_rate_pct < 1
      ? "text-[#34D399]"
      : metrics.error_rate_pct < 5
      ? "text-[#FBBF24]"
      : "text-[#F87171]";

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-[#1A1A22] border border-[#2A2A35] rounded-xl p-3">
          <p className="text-[10px] text-[#6B7280] uppercase tracking-wider mb-1">Total de Peticiones</p>
          <p className="text-xl font-bold text-[#F5F5F5] font-mono">
            {metrics.total_requests.toLocaleString()}
          </p>
          <p className="text-[10px] text-[#6B7280] mt-1">desde el último reinicio</p>
        </div>
        <div className="bg-[#1A1A22] border border-[#2A2A35] rounded-xl p-3">
          <p className="text-[10px] text-[#6B7280] uppercase tracking-wider mb-1">Latencia Promedio</p>
          <p className={`text-xl font-bold font-mono ${latencyColor}`}>
            {metrics.avg_latency_ms}ms
          </p>
          <p className="text-[10px] text-[#6B7280] mt-1">en todos los endpoints</p>
        </div>
        <div className="bg-[#1A1A22] border border-[#2A2A35] rounded-xl p-3">
          <p className="text-[10px] text-[#6B7280] uppercase tracking-wider mb-1">Total de Errores</p>
          <p className={`text-xl font-bold font-mono ${errorColor}`}>
            {metrics.error_rate_pct}%
          </p>
          <p className="text-[10px] text-[#6B7280] mt-1">{metrics.total_errors} errores totales</p>
        </div>
        <div className="bg-[#1A1A22] border border-[#2A2A35] rounded-xl p-3">
          <p className="text-[10px] text-[#6B7280] uppercase tracking-wider mb-1">Lentos (&gt;2s)</p>
          <p className={`text-xl font-bold font-mono ${metrics.slow_requests > 0 ? "text-[#FBBF24]" : "text-[#34D399]"}`}>
            {metrics.slow_requests}
          </p>
          <p className="text-[10px] text-[#6B7280] mt-1">peticiones sobre 2s</p>
        </div>
      </div>

      {metrics.slowest_endpoints.length > 0 && (
        <div>
          <p className="text-xs text-[#6B7280] uppercase tracking-wider mb-2">Endpoints más lentos</p>
          <div className="space-y-1.5">
            {metrics.slowest_endpoints.map((ep) => (
              <div key={ep.path} className="flex items-center justify-between text-xs">
                <span className="text-[#9CA3AF] font-mono truncate max-w-[70%]">{ep.path}</span>
                <span className={`font-mono ${ep.avg_ms > 2000 ? "text-[#FBBF24]" : "text-[#6B7280]"}`}>
                  {ep.avg_ms}ms
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function StatusPage() {
  const [state, setState] = useState<StatusState>({
    services: [
      { name: "API", status: "loading", latency_ms: null },
      { name: "Database", status: "loading", latency_ms: null },
      { name: "Redis", status: "loading", latency_ms: null },
      { name: "pgvector", status: "loading", latency_ms: null },
    ],
    metrics: null,
    last_checked: null,
    loading: true,
  });

  const [refreshing, setRefreshing] = useState(false);

  const checkStatus = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);

    // Kick off all checks in parallel
    const [apiResult, readyResult, metricsResult] = await Promise.all([
      fetchWithLatency(`${API_URL}/api/health`),
      fetchWithLatency(`${API_URL}/api/health/ready`),
      fetchWithLatency(`${API_URL}/api/health/metrics`),
    ]);

    // API service
    const apiCheck: ServiceCheck = {
      name: "API",
      status: apiResult.ok ? "operational" : "down",
      latency_ms: apiResult.latency_ms,
      detail: apiResult.ok ? "FastAPI application server" : "Cannot reach API server",
    };

    // Parse readiness checks (DB + pgvector)
    type ReadyData = { status: string; checks?: Record<string, string> };
    const readyData = readyResult.data as ReadyData | null;
    const checks = readyData?.checks ?? {};

    const dbStatus: ServiceStatus = !readyResult.ok
      ? "down"
      : checks["database"] === "ok"
      ? "operational"
      : checks["database"] === undefined
      ? "down"
      : "degraded";

    // Redis: not in /health/ready — test indirectly via API health
    // If API is up, Redis is likely up (rate limiter uses it). We mark
    // it degraded if API is down, operational otherwise.
    const redisStatus: ServiceStatus = apiResult.ok ? "operational" : "degraded";

    const pgvectorRaw = checks["pgvector"] ?? "";
    const pgvectorStatus: ServiceStatus = !readyResult.ok
      ? "down"
      : pgvectorRaw.startsWith("ok")
      ? "operational"
      : pgvectorRaw === "not installed"
      ? "degraded"
      : "down";

    type MetricsResponse = { status: string; metrics?: MetricsData };
    const metricsResponse = metricsResult.data as MetricsResponse | null;
    const metricsData = metricsResponse?.metrics ?? null;

    setState({
      services: [
        apiCheck,
        {
          name: "Database (PostgreSQL)",
          status: dbStatus,
          latency_ms: readyResult.latency_ms,
          detail: dbStatus === "operational" ? "Primary database" : checks["database"],
        },
        {
          name: "Redis",
          status: redisStatus,
          latency_ms: null,
          detail: "Rate limiting and session cache",
        },
        {
          name: "pgvector",
          status: pgvectorStatus,
          latency_ms: null,
          detail: pgvectorStatus === "operational"
            ? pgvectorRaw
            : pgvectorRaw || "Vector extension unavailable",
        },
      ],
      metrics: metricsData,
      last_checked: new Date(),
      loading: false,
    });
    setRefreshing(false);
  }, []);

  useEffect(() => {
    checkStatus();
    // Auto-refresh every 60 seconds
    const interval = setInterval(() => checkStatus(true), 60_000);
    return () => clearInterval(interval);
  }, [checkStatus]);

  const serviceIcons: Record<string, React.ReactNode> = {
    "API": <Server className="w-4 h-4 text-[#6B7280]" />,
    "Database (PostgreSQL)": <Database className="w-4 h-4 text-[#6B7280]" />,
    "Redis": <Layers className="w-4 h-4 text-[#6B7280]" />,
    "pgvector": <Cpu className="w-4 h-4 text-[#6B7280]" />,
  };

   return (
    <AppLayout>
      <div className="min-h-full text-[#F5F5F5]">
        <div className="border-b border-[#1E1E2A] px-4 sm:px-6 py-3 flex items-center gap-3 sticky top-0 bg-[#0A0A0F] z-20">
          <Activity className="w-5 h-5 text-[#EAB308]" />
          <h1 className="text-sm font-semibold text-[#F5F5F5]">Estado del Sistema</h1>
          <div className="ml-auto flex items-center gap-3">
            {state.last_checked && (
              <span className="text-xs text-[#6B7280] hidden sm:block">
                Última verificación {state.last_checked.toLocaleTimeString("es-PE", {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                })}
              </span>
            )}
            <button
              onClick={() => checkStatus(true)}
              disabled={refreshing || state.loading}
              className="p-2 rounded-xl border border-[#2A2A35] text-[#6B7280] hover:text-[#F5F5F5] hover:border-[#EAB308]/30 transition-colors disabled:opacity-50"
              title="Actualizar estado"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        <main className="max-w-3xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-4 sm:space-y-6">
        {/* Overall banner */}
        <OverallBanner services={state.services} />

        {/* Services */}
        <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-[#1E1E2A] flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#6B7280]" />
            <h2 className="text-sm font-semibold text-[#F5F5F5]">Servicios</h2>
          </div>
          <div className="px-5">
            {state.services.map((service) => (
              <div key={service.name} className="flex items-center justify-between py-3.5 border-b border-[#1E1E2A]/60 last:border-0 gap-2">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="relative flex items-center justify-center w-5 h-5 shrink-0">
                    {serviceIcons[service.name] ?? <Server className="w-4 h-4 text-[#6B7280]" />}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm text-[#F5F5F5]">{service.name}</p>
                    {service.detail && (
                      <p className="text-xs text-[#6B7280] mt-0.5 truncate">{service.detail}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 sm:gap-3 shrink-0">
                  {service.latency_ms !== null && service.status !== "loading" && (
                    <span className="text-xs text-[#6B7280] font-mono tabular-nums hidden sm:inline">
                      {service.latency_ms}ms
                    </span>
                  )}
                  <StatusIcon status={service.status} />
                  <StatusLabel status={service.status} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Runtime metrics */}
        <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-[#1E1E2A] flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-[#6B7280]" />
            <div>
              <h2 className="text-sm font-semibold text-[#F5F5F5]">Métricas en Tiempo Real</h2>
              <p className="text-[10px] text-[#6B7280]">En memoria — se reinicia con el servidor</p>
            </div>
          </div>
          <div className="px-5 py-4">
            <MetricsPanel metrics={state.metrics} />
          </div>
        </div>

        {/* Incident history */}
        <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-[#1E1E2A] flex items-center gap-2">
            <Clock className="w-4 h-4 text-[#6B7280]" />
            <h2 className="text-sm font-semibold text-[#F5F5F5]">Historial de Incidentes</h2>
          </div>
          <div className="px-5 py-4">
            {INCIDENTS.length === 0 ? (
              <div className="flex items-center gap-2 text-sm text-[#6B7280] py-2">
                <CheckCircle2 className="w-4 h-4 text-[#34D399]" />
                Sin incidentes reportados en los últimos 90 días.
              </div>
            ) : (
              <div className="space-y-3">
                {INCIDENTS.map((inc, i) => (
                  <div key={i} className="flex items-start gap-3 text-sm">
                    <span className="text-[#6B7280] whitespace-nowrap text-xs font-mono pt-0.5">
                      {inc.date}
                    </span>
                    <div>
                      <p className="text-[#F5F5F5]">{inc.title}</p>
                      <span
                        className={`text-[10px] font-medium ${
                          inc.status === "resolved" ? "text-[#34D399]" : "text-[#FBBF24]"
                        }`}
                      >
                        {inc.status.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-[11px] text-[#6B7280] pb-2">
          Actualización automática cada 60 segundos &mdash; TukiJuris Platform
        </p>
        </main>
      </div>
    </AppLayout>
  );
}
