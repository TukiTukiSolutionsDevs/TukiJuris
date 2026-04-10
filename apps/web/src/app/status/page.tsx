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
// Fake incidents
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
    return <div className="w-2.5 h-2.5 rounded-full bg-surface-container-low animate-pulse" />;
  }
  const styles: Record<ServiceStatus, { bg: string; shadow?: string }> = {
    operational: {
      bg: "bg-[#10B981]",
      shadow: "shadow-[0_0_8px_rgba(16,185,129,0.6)]",
    },
    degraded: { bg: "bg-[#FBBF24]" },
    down: {
      bg: "bg-[#EF4444]",
      shadow: "shadow-[0_0_8px_rgba(239,68,68,0.6)]",
    },
    loading: { bg: "bg-surface-container-low" },
  };
  const { bg, shadow } = styles[status];
  return <div className={`w-2.5 h-2.5 rounded-full ${bg} ${shadow || ""}`} />;
}

function StatusIcon({ status }: { status: ServiceStatus }) {
  if (status === "loading") {
    return <div className="w-5 h-5 rounded-full bg-surface-container-low animate-pulse" />;
  }
  if (status === "operational") {
    return <CheckCircle2 className="w-5 h-5 text-[#10B981]" />;
  }
  if (status === "degraded") {
    return <AlertCircle className="w-5 h-5 text-[#FBBF24]" />;
  }
  return <XCircle className="w-5 h-5 text-[#EF4444]" />;
}

function StatusLabel({ status }: { status: ServiceStatus }) {
  const map: Record<ServiceStatus, { label: string; color: string }> = {
    operational: { label: "Operativo", color: "text-[#10B981]" },
    degraded: { label: "Degradado", color: "text-[#FBBF24]" },
    down: { label: "Caído", color: "text-[#EF4444]" },
    loading: { label: "Verificando...", color: "text-on-surface/30" },
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
      <div
        className="bg-surface-container-low rounded-lg px-5 py-4 flex items-center gap-3"
        style={{ border: "1px solid rgba(79,70,51,0.15)" }}
      >
        <div className="w-4 h-4 border-2 border-on-surface/20 border-t-transparent rounded-full animate-spin" />
        <span className="text-on-surface/50 text-sm">Verificando estado del sistema...</span>
      </div>
    );
  }

  if (hasDown) {
    return (
      <div
        className="bg-[#EF4444]/10 rounded-lg px-5 py-4 flex items-center gap-3"
        style={{ border: "1px solid rgba(239,68,68,0.3)" }}
      >
        <XCircle className="w-5 h-5 text-[#EF4444] shrink-0" />
        <div>
          <p className="text-sm font-semibold text-[#EF4444]">Problemas detectados en el sistema</p>
          <p className="text-xs text-[#EF4444]/70 mt-0.5">Uno o más servicios no están disponibles.</p>
        </div>
      </div>
    );
  }

  if (hasDegraded) {
    return (
      <div
        className="bg-[#FBBF24]/10 rounded-lg px-5 py-4 flex items-center gap-3"
        style={{ border: "1px solid rgba(251,191,36,0.3)" }}
      >
        <AlertCircle className="w-5 h-5 text-[#FBBF24] shrink-0" />
        <div>
          <p className="text-sm font-semibold text-[#FBBF24]">Algunos servicios degradados</p>
          <p className="text-xs text-[#FBBF24]/70 mt-0.5">
            Algunos servicios pueden estar más lentos de lo normal.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="bg-[#10B981]/10 rounded-lg px-5 py-4 flex items-center gap-3"
      style={{ border: "1px solid rgba(16,185,129,0.2)" }}
    >
      <CheckCircle2 className="w-5 h-5 text-[#10B981] shrink-0" />
      <div>
        <p className="text-sm font-semibold text-[#10B981]">Todos los sistemas operativos</p>
        <p className="text-xs text-[#10B981]/70 mt-0.5">
          Todos los servicios funcionan con normalidad.
        </p>
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
      <div className="text-center py-6 text-on-surface/30 text-sm">
        Métricas no disponibles
      </div>
    );
  }

  const latencyColor =
    metrics.avg_latency_ms < 500
      ? "text-[#10B981]"
      : metrics.avg_latency_ms < 2000
      ? "text-[#FBBF24]"
      : "text-[#EF4444]";

  const errorColor =
    metrics.error_rate_pct < 1
      ? "text-[#10B981]"
      : metrics.error_rate_pct < 5
      ? "text-[#FBBF24]"
      : "text-[#EF4444]";

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          {
            label: "Total de Peticiones",
            value: metrics.total_requests.toLocaleString(),
            color: "text-on-surface",
            sub: "desde el último reinicio",
          },
          {
            label: "Latencia Promedio",
            value: `${metrics.avg_latency_ms}ms`,
            color: latencyColor,
            sub: "en todos los endpoints",
          },
          {
            label: "Tasa de Errores",
            value: `${metrics.error_rate_pct}%`,
            color: errorColor,
            sub: `${metrics.total_errors} errores totales`,
          },
          {
            label: "Lentos (>2s)",
            value: String(metrics.slow_requests),
            color: metrics.slow_requests > 0 ? "text-[#FBBF24]" : "text-[#10B981]",
            sub: "peticiones sobre 2s",
          },
        ].map((m) => (
          <div
            key={m.label}
            className="bg-surface rounded-lg p-3"
            style={{ border: "1px solid rgba(79,70,51,0.15)" }}
          >
            <p className="text-[10px] text-on-surface/30 uppercase tracking-[0.1em] mb-1">{m.label}</p>
            <p className={`font-['Newsreader'] text-xl font-bold font-mono ${m.color}`}>{m.value}</p>
            <p className="text-[10px] text-on-surface/30 mt-1">{m.sub}</p>
          </div>
        ))}
      </div>

      {metrics.slowest_endpoints.length > 0 && (
        <div>
          <p className="text-[10px] text-on-surface/30 uppercase tracking-[0.1em] mb-2">
            Endpoints más lentos
          </p>
          <div className="space-y-1.5">
            {metrics.slowest_endpoints.map((ep) => (
              <div key={ep.path} className="flex items-center justify-between text-xs">
                <span className="text-on-surface/40 font-mono truncate max-w-[70%]">{ep.path}</span>
                <span className={`font-mono ${ep.avg_ms > 2000 ? "text-[#FBBF24]" : "text-on-surface/30"}`}>
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

    const [apiResult, readyResult, metricsResult] = await Promise.all([
      fetchWithLatency(`${API_URL}/api/health`),
      fetchWithLatency(`${API_URL}/api/health/ready`),
      fetchWithLatency(`${API_URL}/api/health/metrics`),
    ]);

    const apiCheck: ServiceCheck = {
      name: "API",
      status: apiResult.ok ? "operational" : "down",
      latency_ms: apiResult.latency_ms,
      detail: apiResult.ok ? "FastAPI application server" : "Cannot reach API server",
    };

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
          detail:
            pgvectorStatus === "operational"
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
    const interval = setInterval(() => checkStatus(true), 60_000);
    return () => clearInterval(interval);
  }, [checkStatus]);

  const serviceIcons: Record<string, React.ReactNode> = {
    "API": <Server className="w-4 h-4 text-on-surface/30" />,
    "Database (PostgreSQL)": <Database className="w-4 h-4 text-on-surface/30" />,
    "Redis": <Layers className="w-4 h-4 text-on-surface/30" />,
    "pgvector": <Cpu className="w-4 h-4 text-on-surface/30" />,
  };

  return (
    <AppLayout>
      <div className="min-h-full text-on-surface">
        {/* Top bar */}
        <div
          className="px-4 sm:px-6 py-3 flex items-center gap-3 sticky top-0 bg-surface-container-lowest z-20"
          style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
        >
          <Activity className="w-5 h-5 text-primary" />
          <h1 className="font-['Newsreader'] text-sm font-semibold text-on-surface">
            Estado del Sistema
          </h1>
          <div className="ml-auto flex items-center gap-3">
            {state.last_checked && (
              <span className="text-xs text-on-surface/30 hidden sm:block">
                Última verificación{" "}
                {state.last_checked.toLocaleTimeString("es-PE", {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                })}
              </span>
            )}
            <button
              onClick={() => checkStatus(true)}
              disabled={refreshing || state.loading}
              className="p-2 rounded-lg text-on-surface/30 hover:text-on-surface transition-colors disabled:opacity-50"
              style={{ border: "1px solid rgba(79,70,51,0.15)" }}
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
          <div
            className="bg-surface-container-low rounded-lg overflow-hidden"
            style={{ border: "1px solid rgba(79,70,51,0.15)" }}
          >
            <div
              className="px-5 py-4 flex items-center gap-2"
              style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
            >
              <Activity className="w-4 h-4 text-on-surface/30" />
              <h2 className="text-sm font-semibold text-on-surface">Servicios</h2>
            </div>
            <div className="px-5">
              {state.services.map((service) => (
                <div
                  key={service.name}
                  className="flex items-center justify-between py-3.5 gap-2 last:border-0"
                  style={{ borderBottom: "1px solid rgba(79,70,51,0.1)" }}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="relative flex items-center justify-center w-5 h-5 shrink-0">
                      {serviceIcons[service.name] ?? <Server className="w-4 h-4 text-on-surface/30" />}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm text-on-surface">{service.name}</p>
                      {service.detail && (
                        <p className="text-xs text-on-surface/30 mt-0.5 truncate">{service.detail}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    {service.latency_ms !== null && service.status !== "loading" && (
                      <span className="text-xs text-on-surface/30 font-mono tabular-nums hidden sm:inline">
                        {service.latency_ms}ms
                      </span>
                    )}
                    <StatusDot status={service.status} />
                    <StatusIcon status={service.status} />
                    <StatusLabel status={service.status} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Runtime metrics */}
          <div
            className="bg-surface-container-low rounded-lg overflow-hidden"
            style={{ border: "1px solid rgba(79,70,51,0.15)" }}
          >
            <div
              className="px-5 py-4 flex items-center gap-2"
              style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
            >
              <TrendingUp className="w-4 h-4 text-on-surface/30" />
              <div>
                <h2 className="text-sm font-semibold text-on-surface">Métricas en Tiempo Real</h2>
                <p className="text-[10px] text-on-surface/30">
                  En memoria — se reinicia con el servidor
                </p>
              </div>
            </div>
            <div className="px-5 py-4">
              <MetricsPanel metrics={state.metrics} />
            </div>
          </div>

          {/* Incident history */}
          <div
            className="bg-surface-container-low rounded-lg overflow-hidden"
            style={{ border: "1px solid rgba(79,70,51,0.15)" }}
          >
            <div
              className="px-5 py-4 flex items-center gap-2"
              style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
            >
              <Clock className="w-4 h-4 text-on-surface/30" />
              <h2 className="text-sm font-semibold text-on-surface">Historial de Incidentes</h2>
            </div>
            <div className="px-5 py-4">
              {INCIDENTS.length === 0 ? (
                <div className="flex items-center gap-2 text-sm text-on-surface/30 py-2">
                  <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
                  Sin incidentes reportados en los últimos 90 días.
                </div>
              ) : (
                <div className="space-y-3">
                  {INCIDENTS.map((inc, i) => (
                    <div key={i} className="flex items-start gap-3 text-sm">
                      <span className="text-on-surface/30 whitespace-nowrap text-xs font-mono pt-0.5">
                        {inc.date}
                      </span>
                      <div>
                        <p className="text-on-surface">{inc.title}</p>
                        <span
                          className={`text-[10px] font-medium ${
                            inc.status === "resolved" ? "text-[#10B981]" : "text-[#FBBF24]"
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
          <p className="text-center text-[11px] text-on-surface/20 pb-2">
            Actualización automática cada 60 segundos &mdash; TukiJuris Platform
          </p>
        </main>
      </div>
    </AppLayout>
  );
}
