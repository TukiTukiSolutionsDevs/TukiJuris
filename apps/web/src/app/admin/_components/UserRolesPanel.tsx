"use client";

import { useState, useEffect, useCallback } from "react";
import { X, Plus, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth/AuthContext";
import {
  fetchUserRoles,
  assignUserRole,
  revokeUserRole,
  type RoleItem,
} from "@/lib/api/admin";

interface Props {
  userId: string;
  /** ID of the currently logged-in admin — used to disable self-row revoke. */
  currentUserId: string;
  /** Whether the current admin holds roles:write permission. */
  canWrite: boolean;
}

export function UserRolesPanel({ userId, currentUserId, canWrite }: Props) {
  const { authFetch } = useAuth();

  const [roles, setRoles] = useState<RoleItem[]>([]);
  const [allRoles, setAllRoles] = useState<RoleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [assigning, setAssigning] = useState(false);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [selectedRoleId, setSelectedRoleId] = useState("");

  const isSelfRow = userId === currentUserId;

  const loadRoles = useCallback(async () => {
    setLoading(true);
    try {
      const [userRoles, systemRolesRes] = await Promise.all([
        fetchUserRoles(authFetch, userId),
        authFetch("/api/admin/roles"),
      ]);
      setRoles(userRoles);
      if (systemRolesRes.ok) {
        const sr: RoleItem[] = await systemRolesRes.json();
        setAllRoles(sr);
      }
    } catch {
      toast.error("Error al cargar roles del usuario");
    } finally {
      setLoading(false);
    }
  }, [authFetch, userId]);

  useEffect(() => {
    loadRoles();
  }, [loadRoles]);

  const handleAssign = async () => {
    if (!selectedRoleId) return;
    const role = allRoles.find((r) => r.id === selectedRoleId);
    if (!role) return;

    // super_admin confirmation gate — NEVER bypass
    if (role.name === "super_admin") {
      const confirmed = window.confirm(
        "¿Estás seguro? Asignar super_admin otorga acceso total."
      );
      if (!confirmed) return;
    }

    setAssigning(true);
    // Optimistic update
    setRoles((prev) => [...prev, role]);
    try {
      await assignUserRole(authFetch, userId, selectedRoleId);
      toast.success("Rol asignado");
      setSelectedRoleId("");
    } catch (err) {
      // Rollback on failure
      setRoles((prev) => prev.filter((r) => r.id !== selectedRoleId));
      if ((err as { status?: number }).status === 409) {
        toast.error("No podés modificar tus propios roles");
      } else {
        toast.error("No se pudo modificar los roles");
      }
    } finally {
      setAssigning(false);
    }
  };

  const handleRevoke = async (roleId: string) => {
    const snapshot = roles;
    setRevokingId(roleId);
    // Optimistic update
    setRoles((prev) => prev.filter((r) => r.id !== roleId));
    try {
      await revokeUserRole(authFetch, userId, roleId);
      toast.success("Rol revocado");
    } catch (err) {
      // Rollback
      setRoles(snapshot);
      if ((err as { status?: number }).status === 409) {
        toast.error("No podés modificar tus propios roles");
      } else {
        toast.error("No se pudo modificar los roles");
      }
    } finally {
      setRevokingId(null);
    }
  };

  const assignableRoles = allRoles.filter(
    (r) => !roles.some((ur) => ur.id === r.id)
  );

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-5 py-3 text-on-surface/40">
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
        <span className="text-xs">Cargando roles…</span>
      </div>
    );
  }

  return (
    <div
      className="px-5 py-4 bg-surface-container-lowest"
      style={{ borderTop: "1px solid rgba(79,70,51,0.1)" }}
      data-testid="user-roles-panel"
    >
      <p className="text-[10px] uppercase tracking-[0.15em] text-on-surface/40 mb-3">
        Roles asignados
      </p>

      {/* Current roles */}
      <div className="flex flex-wrap gap-2 mb-4" data-testid="role-chips">
        {roles.length === 0 && (
          <span className="text-xs text-on-surface/30 italic">Sin roles asignados</span>
        )}
        {roles.map((role) => (
          <span
            key={role.id}
            className="inline-flex items-center gap-1 text-xs bg-primary/10 text-primary rounded-lg px-2.5 py-1"
          >
            {role.display_name}
            {canWrite && (
              <span
                title={
                  isSelfRow
                    ? "No podés modificar tus propios roles"
                    : `Revocar ${role.display_name}`
                }
              >
                <button
                  disabled={isSelfRow || revokingId === role.id}
                  onClick={() => handleRevoke(role.id)}
                  className="ml-0.5 rounded hover:text-red-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  aria-label={`Revocar ${role.display_name}`}
                  data-testid={`revoke-btn-${role.id}`}
                >
                  {revokingId === role.id ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <X className="w-3 h-3" />
                  )}
                </button>
              </span>
            )}
          </span>
        ))}
      </div>

      {/* Assign new role */}
      {canWrite && (
        <div className="flex items-center gap-2" data-testid="assign-role-form">
          <select
            value={selectedRoleId}
            onChange={(e) => setSelectedRoleId(e.target.value)}
            disabled={assignableRoles.length === 0}
            className="text-xs bg-surface border border-on-surface/20 rounded-lg px-2 py-1.5 text-on-surface disabled:opacity-40"
            aria-label="Seleccionar rol para asignar"
            data-testid="role-select"
          >
            <option value="">
              {assignableRoles.length === 0 ? "Todos los roles asignados" : "Asignar rol…"}
            </option>
            {assignableRoles.map((r) => (
              <option key={r.id} value={r.id}>
                {r.display_name}
              </option>
            ))}
          </select>

          <button
            disabled={!selectedRoleId || assigning}
            onClick={handleAssign}
            className="inline-flex items-center gap-1 text-xs bg-primary/10 text-primary rounded-lg px-3 py-1.5 disabled:opacity-40 hover:bg-primary/20 transition-colors"
            data-testid="assign-btn"
          >
            {assigning ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Plus className="w-3 h-3" />
            )}
            Asignar
          </button>
        </div>
      )}
    </div>
  );
}
