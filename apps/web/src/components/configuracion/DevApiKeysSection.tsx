"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, Key, Loader2, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth/AuthContext";
import { CopyOnceModal } from "@/components/ui/CopyOnceModal";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DevApiKey {
  id: string;
  name: string;
  prefix: string;
  scopes: string[];
  created_at: string;
  expires_at?: string | null;
  status: "active" | "revoked" | "expired";
}

interface CreateKeyResponse extends DevApiKey {
  full_key: string;
}

interface FastAPIValidationError {
  loc: string[];
  msg: string;
  type: string;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SCOPE_OPTIONS = [
  { value: "read", label: "Lectura" },
  { value: "write", label: "Escritura" },
];

const STATUS_STYLES: Record<string, string> = {
  active: "bg-[#1a3a2a] text-[#6ee7b7]",
  revoked: "bg-[#93000a]/20 text-[#ffb4ab]",
  expired: "bg-[#35343a] text-on-surface/55",
};

const STATUS_LABELS: Record<string, string> = {
  active: "Activa",
  revoked: "Revocada",
  expired: "Expirada",
};

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("es-AR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function DevApiKeysSection() {
  const { authFetch } = useAuth();

  // List state
  const [keys, setKeys] = useState<DevApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);

  // Revoke state
  const [revokingId, setRevokingId] = useState<string | null>(null);

  // Create form state
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createScopes, setCreateScopes] = useState<string[]>(["read"]);
  const [createExpiry, setCreateExpiry] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Show-once modal state
  const [showOnceOpen, setShowOnceOpen] = useState(false);
  const [showOnceSecret, setShowOnceSecret] = useState("");

  const loadKeys = useCallback(async () => {
    setLoading(true);
    setLoadError(false);
    try {
      const res = await authFetch("/api/keys", {});
      if (!res.ok) {
        setLoadError(true);
        return;
      }
      const data: unknown = await res.json();
      setKeys(
        Array.isArray(data)
          ? (data as DevApiKey[])
          : ((data as { keys?: DevApiKey[] }).keys ?? []),
      );
    } catch {
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  }, [authFetch]);

  useEffect(() => {
    void loadKeys();
  }, [loadKeys]);

  const handleRevoke = async (id: string, name: string) => {
    if (!confirm(`¿Revocar la clave "${name}"? Esta acción es irreversible.`))
      return;
    setRevokingId(id);
    try {
      const res = await authFetch(`/api/keys/${id}`, { method: "DELETE" });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        toast.error(
          (d as { detail?: string }).detail ?? "No se pudo revocar la clave",
        );
        return;
      }
      toast.success("Clave revocada");
      await loadKeys();
    } catch {
      toast.error("Error al revocar la clave");
    } finally {
      setRevokingId(null);
    }
  };

  const handleScopeToggle = (scope: string) => {
    setCreateScopes((prev) =>
      prev.includes(scope)
        ? prev.filter((s) => s !== scope)
        : [...prev, scope],
    );
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createName.trim()) return;
    setCreating(true);
    setCreateError("");
    setFieldErrors({});
    try {
      const body: Record<string, unknown> = {
        name: createName.trim(),
        scopes: createScopes,
      };
      if (createExpiry) body.expires_at = createExpiry;

      const res = await authFetch("/api/keys", {
        method: "POST",
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        const rawDetail = (d as { detail?: unknown }).detail;

        if (res.status === 422 && Array.isArray(rawDetail)) {
          // FastAPI field-level validation: { detail: [{ loc: ["body", field], msg, type }] }
          const newFieldErrors: Record<string, string> = {};
          for (const err of rawDetail as FastAPIValidationError[]) {
            const field = err.loc?.[1];
            if (typeof field === "string" && field) {
              newFieldErrors[field] = err.msg;
            }
          }
          setFieldErrors(newFieldErrors);
          if (Object.keys(newFieldErrors).length === 0) {
            setCreateError("La solicitud no es válida. Revisá los campos.");
          }
        } else {
          const detail = typeof rawDetail === "string" ? rawDetail : undefined;
          setCreateError(
            res.status === 422
              ? (detail ?? "La solicitud no es válida. Revisá los campos.")
              : (detail ?? "No se pudo crear la clave. Intentá de nuevo."),
          );
        }
        return;
      }

      const created: CreateKeyResponse = (await res.json()) as CreateKeyResponse;

      // Show the full key exactly once — this is the ONLY time it will be visible
      setShowOnceSecret(created.full_key);
      setShowOnceOpen(true);

      // Reset form
      setShowCreateForm(false);
      setCreateName("");
      setCreateScopes(["read"]);
      setCreateExpiry("");
    } catch {
      setCreateError("Error de red. Intentá de nuevo.");
    } finally {
      setCreating(false);
    }
  };

  const handleModalClose = async () => {
    // Clear the secret from memory, then refresh the list
    setShowOnceOpen(false);
    setShowOnceSecret("");
    await loadKeys();
  };

  const inputCls =
    "w-full rounded-xl border border-[rgba(79,70,51,0.2)] bg-surface px-3 py-2.5 text-sm text-on-surface placeholder-on-surface/30 focus:outline-none focus:border-primary transition-colors";
  const labelCls =
    "mb-1.5 block text-[11px] font-medium uppercase tracking-[0.18em] text-on-surface/42";

  return (
    <>
      <CopyOnceModal
        open={showOnceOpen}
        secret={showOnceSecret}
        onClose={() => void handleModalClose()}
      />

      <section
        className="panel-base rounded-[1.35rem] p-5 sm:p-6"
        data-testid="dev-api-keys-section"
      >
        {/* Header */}
        <div className="mb-5 flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <Key className="h-4 w-4" />
            </div>
            <div>
              <h2 className="font-['Newsreader'] text-[1.35rem] font-bold leading-none tracking-[-0.02em] text-on-surface">
                Claves de API
              </h2>
              <p className="mt-1.5 text-sm leading-6 text-on-surface/55">
                Generá claves para integrar TukiJuris en tus propias
                aplicaciones. La clave completa solo se muestra al crearla.
              </p>
            </div>
          </div>

          {!showCreateForm && (
            <button
              type="button"
              onClick={() => setShowCreateForm(true)}
              className="flex shrink-0 items-center gap-1.5 rounded-xl border border-[rgba(79,70,51,0.15)] bg-surface px-3 py-2 text-xs font-medium text-on-surface/65 transition-colors hover:border-primary/30 hover:text-on-surface"
              data-testid="create-dev-key-btn"
            >
              <Plus className="h-3.5 w-3.5 text-primary" />
              Nueva clave
            </button>
          )}
        </div>

        {/* Create form */}
        {showCreateForm && (
          <form
            onSubmit={(e) => void handleCreate(e)}
            className="mb-5 space-y-4 rounded-xl border border-[rgba(79,70,51,0.15)] bg-surface p-4"
            data-testid="create-dev-key-form"
          >
            <h3 className="text-sm font-semibold text-on-surface">
              Nueva clave de API
            </h3>

            {createError && (
              <div className="flex items-center gap-2 rounded-lg bg-[#93000a]/20 px-3 py-2 text-xs text-[#ffb4ab]">
                <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                <span data-testid="create-error-msg">{createError}</span>
              </div>
            )}

            <div>
              <label className={labelCls}>
                Nombre <span className="text-[#ffb4ab]">*</span>
              </label>
              <input
                type="text"
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
                placeholder="Ej: App de integración"
                required
                className={inputCls}
                data-testid="create-name-input"
              />
              {fieldErrors.name && (
                <p
                  className="mt-1 text-xs text-[#ffb4ab]"
                  data-testid="create-error-name"
                >
                  {fieldErrors.name}
                </p>
              )}
            </div>

            <div>
              <label className={labelCls}>Permisos</label>
              <div className="flex flex-wrap gap-3">
                {SCOPE_OPTIONS.map((opt) => (
                  <label
                    key={opt.value}
                    className="flex cursor-pointer items-center gap-2 text-sm text-on-surface"
                  >
                    <input
                      type="checkbox"
                      checked={createScopes.includes(opt.value)}
                      onChange={() => handleScopeToggle(opt.value)}
                      className="rounded border-[rgba(79,70,51,0.2)] bg-surface text-primary"
                      data-testid={`scope-${opt.value}`}
                    />
                    {opt.label}
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className={labelCls}>
                Expiración{" "}
                <span className="text-on-surface/30">(opcional)</span>
              </label>
              <input
                type="date"
                value={createExpiry}
                onChange={(e) => setCreateExpiry(e.target.value)}
                className={inputCls}
                data-testid="create-expiry-input"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false);
                  setCreateError("");
                  setFieldErrors({});
                }}
                className="rounded-xl border border-[rgba(79,70,51,0.15)] px-4 py-2 text-xs text-on-surface/55 transition-colors hover:text-on-surface"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={
                  creating || !createName.trim() || createScopes.length === 0
                }
                aria-busy={creating}
                className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-primary to-primary-container px-4 py-2 text-xs font-bold text-on-primary transition-opacity disabled:opacity-40"
                data-testid="create-submit-btn"
              >
                {creating ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Key className="h-3.5 w-3.5" />
                )}
                Crear clave
              </button>
            </div>
          </form>
        )}

        {/* List states */}
        {loading ? (
          <div
            className="flex items-center justify-center gap-2 py-10"
            data-testid="dev-keys-loading"
          >
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            <span className="text-sm text-on-surface/40">
              Cargando claves...
            </span>
          </div>
        ) : loadError ? (
          <div
            className="flex flex-col items-center justify-center rounded-lg border border-dashed border-[rgba(79,70,51,0.15)] py-10 text-center"
            data-testid="dev-keys-error"
          >
            <AlertTriangle className="mb-2 h-8 w-8 text-on-surface/20" />
            <p className="text-sm text-on-surface/40">
              No se pudieron cargar las claves
            </p>
          </div>
        ) : keys.length === 0 ? (
          <div
            className="flex flex-col items-center justify-center rounded-lg border border-dashed border-[rgba(79,70,51,0.15)] py-10 text-center"
            data-testid="dev-keys-empty"
          >
            <Key className="mb-3 h-10 w-10 text-on-surface/10" />
            <p className="text-sm font-medium text-on-surface/40">
              No tenés claves creadas todavía
            </p>
            <p className="mt-1 max-w-xs text-xs text-on-surface/25">
              Generá tu primera clave para empezar a integrar TukiJuris.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto" data-testid="dev-keys-table">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[rgba(79,70,51,0.15)] text-[10px] uppercase tracking-[0.15em] text-on-surface/38">
                  <th className="pb-2 text-left font-medium">Nombre</th>
                  <th className="pb-2 text-left font-medium">Prefijo</th>
                  <th className="pb-2 text-left font-medium">Permisos</th>
                  <th className="pb-2 text-left font-medium">Creada</th>
                  <th className="pb-2 text-left font-medium">Expira</th>
                  <th className="pb-2 text-left font-medium">Estado</th>
                  <th className="pb-2" />
                </tr>
              </thead>
              <tbody>
                {keys.map((key) => (
                  <tr
                    key={key.id}
                    className="border-b border-[rgba(79,70,51,0.08)] last:border-0"
                    data-testid={`dev-key-row-${key.id}`}
                  >
                    <td className="py-3 pr-4 font-medium text-on-surface">
                      {key.name}
                    </td>
                    <td className="py-3 pr-4 font-mono text-xs text-on-surface/60">
                      {key.prefix}
                    </td>
                    <td className="py-3 pr-4">
                      <div className="flex flex-wrap gap-1">
                        {key.scopes.map((s) => (
                          <span
                            key={s}
                            className="rounded bg-surface px-1.5 py-0.5 text-[10px] text-on-surface/50"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-xs text-on-surface/50">
                      {formatDate(key.created_at)}
                    </td>
                    <td className="py-3 pr-4 text-xs text-on-surface/50">
                      {key.expires_at ? formatDate(key.expires_at) : "—"}
                    </td>
                    <td className="py-3 pr-4">
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.12em] ${STATUS_STYLES[key.status] ?? "bg-[#35343a] text-on-surface/55"}`}
                      >
                        {STATUS_LABELS[key.status] ?? key.status}
                      </span>
                    </td>
                    <td className="py-3">
                      {key.status === "active" && (
                        <button
                          type="button"
                          onClick={() => void handleRevoke(key.id, key.name)}
                          disabled={revokingId === key.id}
                          className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-[#ffb4ab]/60 transition-colors hover:bg-[#93000a]/20 hover:text-[#ffb4ab] disabled:opacity-50"
                          data-testid={`revoke-btn-${key.id}`}
                        >
                          {revokingId === key.id ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <Trash2 className="h-3 w-3" />
                          )}
                          Revocar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
