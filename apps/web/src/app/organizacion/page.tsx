"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Building2,
  Users,
  Loader2,
  Plus,
  Trash2,
  Mail,
  Crown,
  AlertTriangle,
  CheckCircle2,
  BarChart3,
} from "lucide-react";
import Link from "next/link";
import { getToken } from "@/lib/auth";
import { AppLayout } from "@/components/AppLayout";
import { InternalPageHeader } from "@/components/shell/InternalPageHeader";
import { ShellUtilityActions } from "@/components/shell/ShellUtilityActions";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface OrgMember {
  user_id: string;
  name: string;
  email: string;
  role: string;
  joined_at: string;
}

interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: string;
  owner_id: string;
  members?: OrgMember[];
}

interface UsageStats {
  queries_used: number;
  queries_limit: number;
  period: string;
  // Backend fields (mapped in fetch)
  total_queries?: number;
  month?: string;
}

const PLAN_COLORS: Record<string, string> = {
  free: "bg-[#25242b] text-[#a09ba8]",
  base: "bg-primary/10 text-primary",
  enterprise: "bg-purple-500/20 text-purple-400",
};

const PLAN_LABELS: Record<string, string> = {
  free: "Free",
  base: "Base",
  enterprise: "Enterprise",
};

const ROLE_LABELS: Record<string, string> = {
  owner: "Propietario",
  admin: "Administrador",
  member: "Miembro",
};

// Role badge styling — design system spec
function RoleBadge({ role }: { role: string }) {
  const styles: Record<string, string> = {
    owner: "bg-primary/10 text-primary",
    admin: "bg-secondary-container text-secondary",
    member: "bg-surface-container-low border border-[rgba(79,70,51,0.15)] text-on-surface/60",
  };
  return (
    <span
      className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-lg ${
        styles[role] ?? styles.member
      }`}
    >
      {role === "owner" && <Crown className="w-3 h-3" />}
      {ROLE_LABELS[role] || role}
    </span>
  );
}

export default function OrganizacionPage() {
  const [org, setOrg] = useState<Organization | null>(null);
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Create org form
  const [createName, setCreateName] = useState("");
  const [createSlug, setCreateSlug] = useState("");
  const [creating, setCreating] = useState(false);

  // Invite form
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [inviting, setInviting] = useState(false);

  // Remove member
  const [removingId, setRemovingId] = useState<string | null>(null);

  const authHeaders = () => ({
    "Content-Type": "application/json",
    Authorization: "Bearer " + getToken(),
  });

  const fetchMembers = async (orgId: string): Promise<OrgMember[]> => {
    try {
      const res = await fetch(`${API_URL}/api/organizations/${orgId}/members`, {
        headers: authHeaders(),
      });
      if (res.ok) return await res.json();
    } catch {}
    return [];
  };

  const showSuccess = (msg: string) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(""), 3000);
  };

  const loadOrg = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/organizations/`, {
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error("No se pudo cargar la organizacion");
      const data = await res.json();
      const orgs: Organization[] = Array.isArray(data) ? data : data.organizations || [];
      if (orgs.length > 0) {
        const first = orgs[0];
        setOrg(first);
        // Load members separately (GET /organizations/ doesn't return members)
        const orgMembers = await fetchMembers(String(first.id));
        setMembers(orgMembers);
        // Load usage
        const usageRes = await fetch(`${API_URL}/api/billing/${first.id}/usage`, {
          headers: authHeaders(),
        });
        if (usageRes.ok) {
          const raw = await usageRes.json();
          setUsage({
            queries_used: raw.total_queries ?? raw.queries_used ?? 0,
            queries_limit: raw.queries_limit ?? -1,
            period: raw.month ?? raw.period ?? "",
          });
        }
      } else {
        setOrg(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error de red");
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadOrg();
  }, [loadOrg]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createName.trim() || !createSlug.trim()) return;
    setCreating(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/organizations/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ name: createName, slug: createSlug }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "No se pudo crear la organizacion");
      }
      showSuccess("Organización creada exitosamente");
      await loadOrg();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear");
    } finally {
      setCreating(false);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim() || !org) return;
    setInviting(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/organizations/${org.id}/invite`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ email: inviteEmail, role: inviteRole }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "No se pudo enviar la invitacion");
      }
      showSuccess(`Invitación enviada a ${inviteEmail}`);
      setInviteEmail("");
      await loadOrg();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al invitar");
    } finally {
      setInviting(false);
    }
  };

  const handleRemoveMember = async (userId: string) => {
    if (!org) return;
    setRemovingId(userId);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/organizations/${org.id}/members/${userId}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error("No se pudo eliminar el miembro");
      showSuccess("Miembro eliminado");
      await loadOrg();
      if (org) {
        const updatedMembers = await fetchMembers(String(org.id));
        setMembers(updatedMembers);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al eliminar");
    } finally {
      setRemovingId(null);
    }
  };

  const usagePercent =
    usage && usage.queries_limit > 0
      ? Math.min(100, Math.round((usage.queries_used / usage.queries_limit) * 100))
      : 0;

  return (
    <AppLayout>
      <div className="flex min-h-full flex-col text-on-surface">
        <InternalPageHeader
          icon={<Users className="w-5 h-5 text-primary" />}
          eyebrow="Equipo"
          title="Organización"
          description="Gestioná miembros, roles, plan y uso compartido con una cabecera consistente con el resto de pantallas internas."
          utilitySlot={<div className="hidden md:flex"><ShellUtilityActions /></div>}
        />

        <div className="w-full px-4 py-6 sm:py-8 lg:px-6 xl:px-8">
          {/* Alerts */}
          {error && (
            <div className="flex items-center gap-3 bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg px-4 py-3 mb-6 text-sm">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}
          {successMsg && (
            <div className="flex items-center gap-3 bg-green-500/10 border border-green-500/30 text-green-400 rounded-lg px-4 py-3 mb-6 text-sm">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {loading ? (
            <div className="flex flex-col items-center justify-center py-24 gap-3">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
              <p className="text-sm text-[#7c7885]">Cargando organización...</p>
            </div>
          ) : org === null ? (
            /* CREATE ORG FORM */
              <div className="max-w-lg mx-auto">
                <div className="text-center mb-8">
                  <div className="panel-base mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl">
                    <Building2 className="w-8 h-8 text-[#7c7885]" />
                  </div>
                <h2 className="font-['Newsreader'] text-3xl font-bold text-on-surface mb-2">
                  Sin organización
                </h2>
                <p className="text-sm text-[#a09ba8]">
                  Crea una organización para gestionar miembros, permisos y uso compartido de la plataforma.
                </p>
              </div>

              <form
                onSubmit={handleCreate}
                className="panel-raised rounded-2xl p-6 space-y-4"
              >
                <div>
                  <label className="block text-xs font-medium text-[#a09ba8] mb-1.5">
                    Nombre de la organización
                  </label>
                  <input
                    type="text"
                    value={createName}
                    onChange={(e) => {
                      setCreateName(e.target.value);
                      setCreateSlug(
                        e.target.value
                          .toLowerCase()
                          .replace(/\s+/g, "-")
                          .replace(/[^a-z0-9-]/g, "")
                      );
                    }}
                    placeholder="Estudio Jurídico Ejemplo SAC"
                     className="control-surface w-full rounded-xl px-3 py-2.5 text-sm text-on-surface placeholder-[#55535d] focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/15 transition-colors"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-[#a09ba8] mb-1.5">
                    Identificador (slug)
                  </label>
                  <input
                    type="text"
                    value={createSlug}
                    onChange={(e) =>
                      setCreateSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ""))
                    }
                    placeholder="estudio-juridico-ejemplo"
                     className="control-surface w-full rounded-xl px-3 py-2.5 text-sm text-on-surface placeholder-[#55535d] focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/15 transition-colors"
                    required
                  />
                  <p className="text-[10px] text-[#55535d] mt-1">
                    Solo letras minúsculas, números y guiones
                  </p>
                </div>
                <button
                  type="submit"
                  disabled={creating || !createName.trim() || !createSlug.trim()}
                   className="gold-gradient w-full text-on-primary font-bold rounded-xl py-2.5 text-sm flex items-center justify-center gap-2 shadow-[0_12px_24px_rgba(0,0,0,0.14)] hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
                >
                  {creating ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Plus className="w-4 h-4" />
                  )}
                  {creating ? "Creando..." : "Crear organización"}
                </button>
              </form>
            </div>
          ) : (
            /* ORG DASHBOARD */
            <div className="space-y-6">
              {/* Org Header Card */}
               <div className="panel-base rounded-xl p-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-primary/10 border border-primary/20 rounded-lg flex items-center justify-center">
                      <Building2 className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                      <h2 className="font-['Newsreader'] text-xl font-bold text-on-surface">
                        {org.name}
                      </h2>
                      <p className="text-sm text-[#7c7885]">/{org.slug}</p>
                    </div>
                  </div>
                  <span
                    className={`text-xs font-semibold px-3 py-1 rounded-lg self-start sm:self-auto ${
                      PLAN_COLORS[org.plan] || PLAN_COLORS.free
                    }`}
                  >
                    {PLAN_LABELS[org.plan] || org.plan}
                  </span>
                </div>
              </div>

              <div className="grid lg:grid-cols-3 gap-4 sm:gap-6">
                {/* Members Table */}
                 <div className="panel-base lg:col-span-2 rounded-xl">
                  <div className="p-4 sm:p-5 border-b border-[rgba(79,70,51,0.15)] bg-surface rounded-t-lg flex items-center gap-2">
                    <Users className="w-4 h-4 text-primary" />
                    <h3 className="font-semibold text-sm text-on-surface">Miembros</h3>
                    <span className="ml-auto text-xs text-[#7c7885]">
                      {members.length} miembro{members.length !== 1 ? "s" : ""}
                    </span>
                  </div>

                  {members.length === 0 ? (
                    <div className="py-10 text-center text-sm text-[#7c7885]">
                      <Users className="w-8 h-8 mx-auto mb-2 text-[#25242b]" />
                      No hay miembros en esta organización
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[500px] text-sm">
                        <thead>
                          <tr className="border-b border-[rgba(79,70,51,0.15)] bg-surface">
                            <th className="text-left text-[10px] uppercase tracking-wider text-[#7c7885] px-5 py-3">
                              Miembro
                            </th>
                            <th className="text-left text-[10px] uppercase tracking-wider text-[#7c7885] px-5 py-3 hidden sm:table-cell">
                              Rol
                            </th>
                            <th className="text-left text-[10px] uppercase tracking-wider text-[#7c7885] px-5 py-3 hidden md:table-cell">
                              Ingreso
                            </th>
                            <th className="px-5 py-3" />
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[rgba(79,70,51,0.1)]">
                          {members.map((member, idx) => (
                            <tr
                              key={member.user_id}
                              className={`hover:bg-[#25242b] transition-colors ${
                                idx % 2 === 0 ? "bg-surface-container-low" : "bg-surface"
                              }`}
                            >
                              <td className="px-5 py-3">
                                <div>
                                  <p className="font-medium text-on-surface">
                                    {member.name || "—"}
                                  </p>
                                  <p className="text-xs text-[#7c7885]">{member.email}</p>
                                </div>
                              </td>
                              <td className="px-5 py-3 hidden sm:table-cell">
                                <RoleBadge role={member.role} />
                              </td>
                              <td className="px-5 py-3 text-xs text-[#7c7885] hidden md:table-cell">
                                {member.joined_at
                                  ? new Date(member.joined_at).toLocaleDateString("es-PE")
                                  : "—"}
                              </td>
                              <td className="px-5 py-3 text-right">
                                {member.role !== "owner" && (
                                  <button
                                    onClick={() => handleRemoveMember(member.user_id)}
                                    disabled={removingId === member.user_id}
                                    className="p-1.5 rounded-lg text-[#7c7885] hover:text-red-400 hover:bg-red-400/10 transition-colors disabled:opacity-50"
                                    title="Eliminar miembro"
                                  >
                                    {removingId === member.user_id ? (
                                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                    ) : (
                                      <Trash2 className="w-3.5 h-3.5" />
                                    )}
                                  </button>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* Invite Form */}
                  <div className="p-4 sm:p-5 border-t border-[rgba(79,70,51,0.15)]">
                    <h4 className="text-xs font-semibold text-[#a09ba8] uppercase tracking-wider mb-3">
                      Invitar miembro
                    </h4>
                    <form onSubmit={handleInvite} className="flex flex-col gap-2">
                      <div className="flex-1 relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#7c7885]" />
                        <input
                          type="email"
                          value={inviteEmail}
                          onChange={(e) => setInviteEmail(e.target.value)}
                          placeholder="correo@ejemplo.com"
                          className="w-full bg-surface border border-[rgba(79,70,51,0.2)] rounded-lg pl-9 pr-3 py-2 text-sm text-on-surface placeholder-[#55535d] focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/15 transition-colors"
                          required
                        />
                      </div>
                      <select
                        value={inviteRole}
                        onChange={(e) => setInviteRole(e.target.value)}
                        className="bg-surface border border-[rgba(79,70,51,0.2)] rounded-lg px-3 py-2 text-sm text-on-surface focus:outline-none focus:border-primary/50 transition-colors"
                      >
                        <option value="member">Miembro</option>
                        <option value="admin">Administrador</option>
                      </select>
                      <button
                        type="submit"
                        disabled={inviting || !inviteEmail.trim()}
                        className="w-full sm:w-auto bg-gradient-to-br from-primary to-primary-container hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed text-on-primary font-bold rounded-lg px-4 py-3 sm:py-2 text-sm flex items-center justify-center gap-2 transition-opacity whitespace-nowrap"
                      >
                        {inviting ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Plus className="w-3.5 h-3.5" />
                        )}
                        Invitar
                      </button>
                    </form>
                  </div>
                </div>

                {/* Usage Stats */}
                <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg">
                  <div className="p-5 border-b border-[rgba(79,70,51,0.15)] bg-surface rounded-t-lg flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-primary" />
                    <h3 className="font-semibold text-sm text-on-surface">Uso del Plan</h3>
                  </div>
                  <div className="p-5">
                    {usage ? (
                      <div className="space-y-4">
                        <div>
                          <div className="flex justify-between items-end mb-2">
                            <span className="text-xs text-[#a09ba8]">Consultas este mes</span>
                            <span className="text-xs font-semibold text-on-surface">
                              {usage.queries_used.toLocaleString("es-PE")}{" "}
                              <span className="text-[#7c7885]">
                                /{" "}
                                {usage.queries_limit === -1
                                  ? "Ilimitado"
                                  : usage.queries_limit.toLocaleString("es-PE")}
                              </span>
                            </span>
                          </div>
                          {usage.queries_limit !== -1 && (
                            <div className="w-full bg-[#25242b] rounded-full h-2">
                              <div
                                className={`h-2 rounded-full transition-all ${
                                  usagePercent >= 90
                                    ? "bg-red-500"
                                    : usagePercent >= 70
                                    ? "bg-primary"
                                    : "bg-green-500"
                                }`}
                                style={{ width: `${usagePercent}%` }}
                              />
                            </div>
                          )}
                          {usage.queries_limit !== -1 && (
                            <p className="text-[10px] text-[#7c7885] mt-1.5 text-right">
                              {usagePercent}% utilizado
                            </p>
                          )}
                        </div>

                        <div className="pt-4 border-t border-[rgba(79,70,51,0.15)]">
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-[#7c7885]">Plan actual</span>
                            <span
                              className={`text-xs font-semibold px-2 py-0.5 rounded-lg ${
                                PLAN_COLORS[org.plan] || PLAN_COLORS.free
                              }`}
                            >
                              {PLAN_LABELS[org.plan] || org.plan}
                            </span>
                          </div>
                        </div>

                        <Link
                          href="/billing"
                          className="block w-full text-center text-sm text-primary hover:text-primary-container border border-primary/20 hover:border-primary/40 rounded-lg py-2 transition-colors"
                        >
                          Ver planes y facturación
                        </Link>
                      </div>
                    ) : (
                      <div className="py-6 text-center text-sm text-[#7c7885]">
                        <BarChart3 className="w-6 h-6 mx-auto mb-2 text-[#25242b]" />
                        Sin datos de uso disponibles
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
