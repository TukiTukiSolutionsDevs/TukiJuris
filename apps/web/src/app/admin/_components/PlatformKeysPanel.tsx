"use client";

/**
 * PlatformKeysPanel — operator-managed LLM provider keys.
 *
 * UX contract:
 *  - Lists configured providers with non-sensitive hint (e.g. "sk-...3kF2"),
 *    last update, and connection test result.
 *  - Add/replace via inline form. Replacing a provider's key UPDATES the
 *    existing row in DB (no history kept — same provider key is a single
 *    rotating slot).
 *  - Test ping per row → small badge with OK/FAIL.
 *  - Delete with confirm.
 *
 * Permission: backend gates the GET/POST/DELETE/test routes behind
 * `platform_keys:write`. The link to this tab in AdminSidebar is also
 * gated by the same permission; this panel renders defensively (catches
 * 403 → hides itself).
 */

import { useCallback, useEffect, useState } from "react";
import {
  KeyRound,
  Plus,
  Trash2,
  TestTube2,
  CheckCircle2,
  XCircle,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import {
  PLATFORM_PROVIDERS,
  type PlatformKey,
  type PlatformProvider,
  fetchPlatformKeys,
  upsertPlatformKey,
  deletePlatformKey,
  testPlatformKey,
} from "@/lib/api/admin";

const PROVIDER_LABELS: Record<PlatformProvider, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google (Gemini)",
  deepseek: "DeepSeek",
  groq: "Groq",
  xai: "xAI (Grok)",
  openrouter: "OpenRouter",
};

interface TestStatus {
  ok: boolean;
  message: string;
  testedAt: number;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function PlatformKeysPanel() {
  const { authFetch } = useAuth();
  const [keys, setKeys] = useState<PlatformKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [hidden, setHidden] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [formProvider, setFormProvider] = useState<PlatformProvider>("openai");
  const [formLabel, setFormLabel] = useState("");
  const [formKey, setFormKey] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const [testing, setTesting] = useState<Record<string, boolean>>({});
  const [testResults, setTestResults] = useState<Record<string, TestStatus>>({});

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchPlatformKeys(authFetch);
      setKeys(data);
    } catch (err) {
      const status = (err as { status?: number }).status;
      if (status === 403) {
        setHidden(true);
      } else {
        setError("No se pudieron cargar las claves de plataforma.");
      }
    } finally {
      setLoading(false);
    }
  }, [authFetch]);

  useEffect(() => {
    void load();
  }, [load]);

  if (hidden) return null;

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setSubmitError(null);
    try {
      await upsertPlatformKey(authFetch, {
        provider: formProvider,
        api_key: formKey,
        label: formLabel.trim() || null,
      });
      setShowForm(false);
      setFormKey("");
      setFormLabel("");
      await load();
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : "Error al guardar la clave."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const onDelete = async (provider: string) => {
    if (!confirm(`¿Eliminar la clave de plataforma de ${PROVIDER_LABELS[provider as PlatformProvider] ?? provider}?`)) {
      return;
    }
    try {
      await deletePlatformKey(authFetch, provider);
      await load();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Error al eliminar la clave."
      );
    }
  };

  const onTest = async (provider: string) => {
    setTesting((s) => ({ ...s, [provider]: true }));
    try {
      const result = await testPlatformKey(authFetch, provider);
      setTestResults((s) => ({
        ...s,
        [provider]: { ok: result.ok, message: result.message, testedAt: Date.now() },
      }));
    } catch (err) {
      setTestResults((s) => ({
        ...s,
        [provider]: {
          ok: false,
          message: err instanceof Error ? err.message : "Error",
          testedAt: Date.now(),
        },
      }));
    } finally {
      setTesting((s) => ({ ...s, [provider]: false }));
    }
  };

  return (
    <div
      className="bg-surface-container-low rounded-lg overflow-hidden"
      style={{ border: "1px solid rgba(79,70,51,0.15)" }}
    >
      {/* Header */}
      <div
        className="p-5 flex items-center gap-2"
        style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
      >
        <KeyRound className="w-4 h-4 text-primary" />
        <div className="flex-1">
          <h2 className="font-semibold text-sm text-on-surface">
            Claves de plataforma (Free/Pro)
          </h2>
          <p className="text-xs text-on-surface/40 mt-0.5">
            Estas claves alimentan los modelos gratuitos y pro que ofrecés a tus
            clientes. Cada cliente puede agregar la suya propia (BYOK) para uso
            ilimitado con su cuenta.
          </p>
        </div>
        <button
          onClick={() => {
            setShowForm((v) => !v);
            setSubmitError(null);
          }}
          className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          {showForm ? "Cancelar" : "Agregar / Reemplazar"}
        </button>
      </div>

      {/* Inline form */}
      {showForm && (
        <form
          onSubmit={onSubmit}
          className="p-5 space-y-3 bg-surface-container/30"
          style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] uppercase tracking-[0.15em] text-on-surface/50 mb-1">
                Proveedor
              </label>
              <select
                value={formProvider}
                onChange={(e) => setFormProvider(e.target.value as PlatformProvider)}
                className="w-full text-sm px-3 py-2 rounded-lg bg-surface border border-[rgba(79,70,51,0.2)] focus:outline-none focus:border-primary"
              >
                {PLATFORM_PROVIDERS.map((p) => (
                  <option key={p} value={p}>
                    {PROVIDER_LABELS[p]}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-[10px] uppercase tracking-[0.15em] text-on-surface/50 mb-1">
                Etiqueta (opcional)
              </label>
              <input
                type="text"
                value={formLabel}
                onChange={(e) => setFormLabel(e.target.value)}
                placeholder="ej. cuenta corporativa"
                className="w-full text-sm px-3 py-2 rounded-lg bg-surface border border-[rgba(79,70,51,0.2)] focus:outline-none focus:border-primary"
                maxLength={200}
              />
            </div>
          </div>
          <div>
            <label className="block text-[10px] uppercase tracking-[0.15em] text-on-surface/50 mb-1">
              API Key
            </label>
            <input
              type="password"
              value={formKey}
              onChange={(e) => setFormKey(e.target.value)}
              placeholder="sk-..."
              required
              minLength={4}
              className="w-full text-sm px-3 py-2 rounded-lg bg-surface border border-[rgba(79,70,51,0.2)] focus:outline-none focus:border-primary font-mono"
            />
            <p className="text-[10px] text-on-surface/40 mt-1">
              Se cifra al guardar (Fernet/AES). Solo se desencripta en memoria al usarse.
            </p>
          </div>
          {submitError && (
            <div className="flex items-start gap-2 text-xs text-red-400 bg-red-500/10 px-3 py-2 rounded-lg">
              <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
              <span>{submitError}</span>
            </div>
          )}
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={submitting || !formKey.trim()}
              className="inline-flex items-center gap-1.5 text-xs font-medium px-4 py-2 rounded-lg bg-primary text-on-primary hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {submitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              Guardar
            </button>
            <button
              type="button"
              onClick={() => {
                setShowForm(false);
                setFormKey("");
                setFormLabel("");
                setSubmitError(null);
              }}
              className="text-xs px-4 py-2 rounded-lg text-on-surface/60 hover:bg-surface-container-low transition-colors"
            >
              Cancelar
            </button>
          </div>
        </form>
      )}

      {/* Body */}
      {loading ? (
        <div className="p-8 flex items-center justify-center text-on-surface/40">
          <Loader2 className="w-4 h-4 animate-spin" />
        </div>
      ) : error ? (
        <div className="p-5 flex items-start gap-2 text-xs text-red-400">
          <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      ) : keys.length === 0 ? (
        <div className="p-8 text-center">
          <KeyRound className="w-8 h-8 text-on-surface/20 mx-auto mb-2" />
          <p className="text-sm text-on-surface/40">
            No hay claves de plataforma configuradas todavía.
          </p>
          <p className="text-xs text-on-surface/30 mt-1">
            Agregá al menos una para activar los modelos gratuitos.
          </p>
        </div>
      ) : (
        <table className="w-full text-sm">
          <thead className="bg-surface-container/40">
            <tr className="text-[10px] uppercase tracking-[0.15em] text-on-surface/40">
              <th className="text-left px-5 py-3">Proveedor</th>
              <th className="text-left px-5 py-3">Etiqueta</th>
              <th className="text-left px-5 py-3">Hint</th>
              <th className="text-left px-5 py-3">Estado</th>
              <th className="text-left px-5 py-3">Actualizada</th>
              <th className="text-right px-5 py-3">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {keys.map((k) => {
              const result = testResults[k.provider];
              const isTesting = testing[k.provider];
              return (
                <tr
                  key={k.provider}
                  className="border-t border-[rgba(79,70,51,0.1)] hover:bg-surface-container-low/50"
                >
                  <td className="px-5 py-3 font-medium text-on-surface">
                    {PROVIDER_LABELS[k.provider as PlatformProvider] ?? k.provider}
                  </td>
                  <td className="px-5 py-3 text-on-surface/60">
                    {k.label ?? <span className="text-on-surface/30">—</span>}
                  </td>
                  <td className="px-5 py-3 font-mono text-xs text-on-surface/60">
                    {k.api_key_hint}
                  </td>
                  <td className="px-5 py-3">
                    {result ? (
                      <span
                        title={result.message}
                        className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-md ${
                          result.ok
                            ? "bg-[#10B981]/10 text-[#10B981]"
                            : "bg-red-500/10 text-red-400"
                        }`}
                      >
                        {result.ok ? (
                          <CheckCircle2 className="w-2.5 h-2.5" />
                        ) : (
                          <XCircle className="w-2.5 h-2.5" />
                        )}
                        {result.ok ? "OK" : "FAIL"}
                      </span>
                    ) : k.is_active ? (
                      <span className="inline-flex items-center gap-1 text-[10px] text-on-surface/40">
                        Sin probar
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[10px] text-on-surface/40">
                        Inactiva
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-xs text-on-surface/50">
                    {formatDate(k.updated_at)}
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => onTest(k.provider)}
                        disabled={isTesting}
                        title="Probar conexión"
                        className="p-1.5 rounded-lg text-on-surface/40 hover:text-primary hover:bg-primary/10 disabled:opacity-50 transition-colors"
                      >
                        {isTesting ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <TestTube2 className="w-3.5 h-3.5" />
                        )}
                      </button>
                      <button
                        onClick={() => onDelete(k.provider)}
                        title="Eliminar"
                        className="p-1.5 rounded-lg text-on-surface/40 hover:text-red-400 hover:bg-red-400/10 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
