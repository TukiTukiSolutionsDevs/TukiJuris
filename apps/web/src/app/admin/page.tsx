"use client";

import { useState, useEffect, useCallback } from "react";
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
  ArrowLeft,
} from "lucide-react";
import Link from "next/link";
import { getToken } from "@/lib/auth";
import { AdminLayout } from "@/components/AdminLayout";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

const PLAN_COLORS: Record<string, string> = {
  free: "bg-[#2A2A35] text-[#9CA3AF]",
  base: "bg-[#EAB308]/20 text-[#EAB308]",
  enterprise: "bg-purple-500/20 text-purple-400",
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
  competencia: "text-[#EAB308]",
};

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-4 sm:p-5">
      <div className="flex items-center justify-between mb-2 sm:mb-3">
        <span className="text-[10px] sm:text-xs text-[#6B7280] font-medium leading-tight">{label}</span>
        <div className={`w-7 h-7 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center shrink-0 ${color || "bg-[#EAB308]/10"}`}>
          <Icon className={`w-3.5 h-3.5 sm:w-4 sm:h-4 ${color ? "" : "text-[#EAB308]"}`} />
        </div>
      </div>
      <p className="text-2xl sm:text-3xl font-bold text-[#EAB308]">
        {typeof value === "number" ? value.toLocaleString("es-PE") : value}
      </p>
      {sub && <p className="text-xs text-[#6B7280] mt-1">{sub}</p>}
    </div>
  );
}

export default function AdminPage() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [kbStats, setKbStats] = useState<KBStats[]>([]);
  const [recentQueries, setRecentQueries] = useState<RecentQuery[]>([]);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const authHeaders = () => ({
    "Content-Type": "application/json",
    Authorization: "Bearer " + getToken(),
  });

  const loadData = useCallback(async () => {
    setError("");
    try {
      // Check admin status
      const meRes = await fetch(`${API_URL}/api/auth/me`, { headers: authHeaders() });
      if (!meRes.ok) throw new Error("No autenticado");
      const me = await meRes.json();

      if (!me.is_admin) {
        setIsAdmin(false);
        setLoading(false);
        return;
      }
      setIsAdmin(true);

      // Load all data in parallel
      const [healthRes, usersRes, statsRes, queriesRes] = await Promise.allSettled([
        fetch(`${API_URL}/api/health`, { headers: authHeaders() }),
        fetch(`${API_URL}/api/admin/users`, { headers: authHeaders() }),
        fetch(`${API_URL}/api/admin/stats`, { headers: authHeaders() }),
        fetch(`${API_URL}/api/admin/activity`, { headers: authHeaders() }),
      ]);

      if (healthRes.status === "fulfilled" && healthRes.value.ok) {
        const hd: HealthData = await healthRes.value.json();
        setHealth(hd);

        // Build KB stats from health data
        if (hd.knowledge_base?.areas) {
          const kb = Object.entries(hd.knowledge_base.areas).map(([area, chunks]) => ({
            area,
            chunks: chunks as number,
          })).sort((a, b) => b.chunks - a.chunks);
          setKbStats(kb);
        }
      }

      if (usersRes.status === "fulfilled" && usersRes.value.ok) {
        const ud = await usersRes.value.json();
        setUsers(Array.isArray(ud) ? ud : ud.users || []);
      }

      if (statsRes.status === "fulfilled" && statsRes.value.ok) {
        const sd = await statsRes.value.json();
        setStats(sd);
      } else {
        // Build stats from available data
        setStats({
          total_users: 0,
          total_organizations: 0,
          queries_today: 0,
          total_conversations: 0,
        });
      }

      if (queriesRes.status === "fulfilled" && queriesRes.value.ok) {
        const qd = await queriesRes.value.json();
        setRecentQueries(Array.isArray(qd) ? qd.slice(0, 20) : (qd.queries || []).slice(0, 20));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar datos");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
      <div className="min-h-full text-[#F5F5F5]">
        <div className="border-b border-[#1E1E2A] px-4 lg:px-6 py-4 flex items-center gap-3">
          <ShieldCheck className="w-5 h-5 text-[#EAB308]" />
          <h1 className="font-bold text-base">Panel de Administración</h1>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-[#2A2A35] text-sm text-[#F5F5F5] hover:text-white hover:border-[#EAB308]/30 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">Actualizar</span>
          </button>
        </div>

        <div className="max-w-7xl mx-auto px-4 lg:px-6 py-6 sm:py-8">
        {/* Error */}
        {error && (
          <div className="flex items-center gap-3 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl px-4 py-3 mb-6 text-sm">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-24 gap-3">
            <Loader2 className="w-8 h-8 text-[#EAB308] animate-spin" />
            <p className="text-sm text-[#6B7280]">Cargando panel de administracion...</p>
          </div>
        ) : !isAdmin ? (
          /* Access Denied */
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center justify-center mb-4">
              <ShieldCheck className="w-8 h-8 text-red-400" />
            </div>
            <h2 className="text-xl font-bold mb-2 text-[#F5F5F5]">Acceso restringido</h2>
            <p className="text-sm text-[#9CA3AF] max-w-sm">
              Esta seccion es exclusiva para administradores del sistema. Si crees que deberia tener acceso, contacta al equipo.
            </p>
            <Link href="/" className="mt-6 text-sm text-[#EAB308] hover:text-[#ca9a07] flex items-center gap-2">
              <ArrowLeft className="w-4 h-4" />
              Volver al chat
            </Link>
          </div>
        ) : (
          <div className="space-y-8">
            {/* System Stats */}
            <div>
              <h2 className="text-xs uppercase tracking-wider text-[#6B7280] mb-4 flex items-center gap-2">
                <TrendingUp className="w-3.5 h-3.5" />
                Estadisticas del sistema
              </h2>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                <StatCard
                  icon={Users}
                  label="Usuarios totales"
                  value={stats?.total_users ?? users.length}
                  sub="Registrados en la plataforma"
                  color="bg-blue-500/10 text-blue-400"
                />
                <StatCard
                  icon={Building2}
                  label="Organizaciones"
                  value={stats?.total_organizations ?? 0}
                  sub="Orgs activas"
                  color="bg-purple-500/10 text-purple-400"
                />
                <StatCard
                  icon={Zap}
                  label="Consultas hoy"
                  value={stats?.queries_today ?? 0}
                  sub="En las ultimas 24 horas"
                  color="bg-[#EAB308]/10 text-[#EAB308]"
                />
                <StatCard
                  icon={MessageSquare}
                  label="Conversaciones"
                  value={stats?.total_conversations ?? 0}
                  sub="Total acumulado"
                  color="bg-green-500/10 text-green-400"
                />
              </div>
            </div>

            {/* Health + KB Stats */}
            <div className="grid lg:grid-cols-2 gap-6">
              {/* System Health */}
              {health && (
                <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-5">
                  <h2 className="text-xs uppercase tracking-wider text-[#6B7280] mb-4 flex items-center gap-2">
                    <Activity className="w-3.5 h-3.5" />
                    Estado del sistema
                  </h2>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between py-2 border-b border-[#1E1E2A]">
                      <span className="text-sm text-[#9CA3AF]">Estado API</span>
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                        health.status === "ok" || health.status === "healthy"
                          ? "bg-green-500/20 text-green-400"
                          : "bg-red-500/20 text-red-400"
                      }`}>
                        {health.status === "ok" || health.status === "healthy" ? "Operativo" : health.status}
                      </span>
                    </div>
                    {health.models_available !== undefined && (
                      <div className="flex items-center justify-between py-2 border-b border-[#1E1E2A]">
                        <span className="text-sm text-[#9CA3AF]">Modelos disponibles</span>
                        <span className="text-sm font-semibold text-[#F5F5F5]">{health.models_available}</span>
                      </div>
                    )}
                    {health.knowledge_base?.total_chunks !== undefined && (
                      <div className="flex items-center justify-between py-2">
                        <span className="text-sm text-[#9CA3AF]">Chunks en base de conocimiento</span>
                        <span className="text-sm font-semibold text-[#F5F5F5]">
                          {health.knowledge_base.total_chunks.toLocaleString("es-PE")}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* KB Stats by area */}
              {kbStats.length > 0 && (
                <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-5">
                  <h2 className="text-xs uppercase tracking-wider text-[#6B7280] mb-4 flex items-center gap-2">
                    <Database className="w-3.5 h-3.5" />
                    Base de conocimiento por area
                  </h2>
                  <div className="space-y-2.5">
                    {kbStats.slice(0, 8).map((kb) => (
                      <div key={kb.area}>
                        <div className="flex items-center justify-between mb-1">
                          <span className={`text-xs capitalize ${AREA_COLORS[kb.area] || "text-[#9CA3AF]"}`}>
                            {kb.area.replace("_", " ")}
                          </span>
                          <span className="text-xs text-[#6B7280]">
                            {kb.chunks.toLocaleString("es-PE")} chunks
                          </span>
                        </div>
                        <div className="w-full bg-[#1A1A22] rounded-full h-1.5">
                          <div
                            className={`h-1.5 rounded-full ${AREA_COLORS[kb.area]?.replace("text-", "bg-") || "bg-[#EAB308]"}`}
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
              <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl">
                <div className="p-5 border-b border-[#1E1E2A] flex items-center gap-2 bg-[#1A1A22] rounded-t-xl">
                  <Users className="w-4 h-4 text-[#EAB308]" />
                  <h2 className="font-semibold text-sm text-[#F5F5F5]">Usuarios</h2>
                  <span className="ml-auto text-xs text-[#6B7280]">{users.length} usuarios</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[480px] text-sm">
                    <thead>
                      <tr className="border-b border-[#1E1E2A]">
                        <th className="text-left text-[10px] uppercase tracking-wider text-[#6B7280] px-4 sm:px-5 py-3">Usuario</th>
                        <th className="text-left text-[10px] uppercase tracking-wider text-[#6B7280] px-4 sm:px-5 py-3 hidden sm:table-cell">Plan</th>
                        <th className="text-left text-[10px] uppercase tracking-wider text-[#6B7280] px-4 sm:px-5 py-3 hidden md:table-cell">Organizacion</th>
                        <th className="text-right text-[10px] uppercase tracking-wider text-[#6B7280] px-4 sm:px-5 py-3 hidden lg:table-cell">Consultas/mes</th>
                        <th className="text-right text-[10px] uppercase tracking-wider text-[#6B7280] px-4 sm:px-5 py-3 hidden xl:table-cell">Registro</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1E1E2A]/50">
                      {users.map((user) => (
                        <tr key={user.id} className="hover:bg-[#1A1A22] transition-colors">
                          <td className="px-5 py-3">
                            <div>
                              <div className="flex items-center gap-2">
                                <p className="font-medium text-[#F5F5F5]">{user.full_name || "—"}</p>
                                {user.is_admin && (
                                  <ShieldCheck className="w-3.5 h-3.5 text-[#EAB308]" />
                                )}
                              </div>
                              <p className="text-xs text-[#6B7280]">{user.email}</p>
                            </div>
                          </td>
                          <td className="px-5 py-3 hidden sm:table-cell">
                            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full capitalize ${PLAN_COLORS[user.plan] || PLAN_COLORS.free}`}>
                              {user.plan}
                            </span>
                          </td>
                          <td className="px-5 py-3 text-xs text-[#9CA3AF] hidden md:table-cell">
                            {user.org_name || <span className="text-[#6B7280]">Sin org</span>}
                          </td>
                          <td className="px-5 py-3 text-right text-xs text-[#F5F5F5] hidden lg:table-cell">
                            {(user.queries_this_month || 0).toLocaleString("es-PE")}
                          </td>
                          <td className="px-5 py-3 text-right text-xs text-[#6B7280] hidden xl:table-cell">
                            {user.created_at
                              ? new Date(user.created_at).toLocaleDateString("es-PE")
                              : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Recent Queries Activity */}
            {recentQueries.length > 0 && (
              <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl">
                <div className="p-5 border-b border-[#1E1E2A] flex items-center gap-2 bg-[#1A1A22] rounded-t-xl">
                  <Activity className="w-4 h-4 text-[#EAB308]" />
                  <h2 className="font-semibold text-sm text-[#F5F5F5]">Actividad reciente</h2>
                  <span className="ml-auto text-xs text-[#6B7280]">Ultimas {recentQueries.length} consultas</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[400px] text-sm">
                    <thead>
                      <tr className="border-b border-[#1E1E2A]">
                        <th className="text-left text-[10px] uppercase tracking-wider text-[#6B7280] px-4 sm:px-5 py-3">Area</th>
                        <th className="text-left text-[10px] uppercase tracking-wider text-[#6B7280] px-4 sm:px-5 py-3 hidden sm:table-cell">Modelo</th>
                        <th className="text-right text-[10px] uppercase tracking-wider text-[#6B7280] px-4 sm:px-5 py-3">Latencia</th>
                        <th className="text-right text-[10px] uppercase tracking-wider text-[#6B7280] px-4 sm:px-5 py-3 hidden md:table-cell">Hora</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1E1E2A]/50">
                      {recentQueries.map((q) => (
                        <tr key={q.id} className="hover:bg-[#1A1A22] transition-colors">
                          <td className="px-5 py-3">
                            <span className={`text-xs capitalize ${AREA_COLORS[q.legal_area] || "text-[#9CA3AF]"}`}>
                              {q.legal_area?.replace("_", " ") || "General"}
                            </span>
                          </td>
                          <td className="px-5 py-3 hidden sm:table-cell">
                             <span className="text-xs text-[#9CA3AF] font-mono">
                              {q.model?.split("/").pop() || q.model || "—"}
                            </span>
                          </td>
                          <td className="px-5 py-3 text-right">
                            <div className="flex items-center justify-end gap-1">
                              <Clock className="w-3 h-3 text-[#6B7280]" />
                              <span className={`text-xs ${
                                q.latency_ms > 10000
                                  ? "text-red-400"
                                  : q.latency_ms > 5000
                                  ? "text-[#EAB308]"
                                  : "text-green-400"
                              }`}>
                                {q.latency_ms ? `${(q.latency_ms / 1000).toFixed(1)}s` : "—"}
                              </span>
                            </div>
                          </td>
                          <td className="px-5 py-3 text-right text-xs text-[#6B7280] hidden md:table-cell">
                            {q.created_at
                              ? new Date(q.created_at).toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit" })
                              : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Empty state if no data at all */}
            {users.length === 0 && recentQueries.length === 0 && kbStats.length === 0 && (
              <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-10 text-center">
                <BarChart3 className="w-10 h-10 text-[#2A2A35] mx-auto mb-3" />
                <p className="text-sm text-[#9CA3AF] mb-1">Sin datos disponibles</p>
                <p className="text-xs text-[#6B7280]">
                  Los endpoints de administracion podrian no estar implementados aun
                </p>
              </div>
            )}
          </div>
        )}
        </div>
      </div>
    </AdminLayout>
  );
}
