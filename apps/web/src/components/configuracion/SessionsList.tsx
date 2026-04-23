"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, Loader2, Monitor } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { getAccessToken } from "@/lib/auth/authClient";
import { decodeAccessClaims } from "@/lib/auth/jwt";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Session {
  jti: string;
  user_id: string;
  created_at: string;
  expires_at: string;
  last_used_at?: string;
  user_agent?: string;
  ip_address?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function truncateJti(jti: string): string {
  if (jti.length <= 8) return jti;
  return `${jti.slice(0, 8)}...`;
}

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

/**
 * Best-effort: decode the in-memory access token and extract `jti` if present.
 * Returns undefined when the token is absent, malformed, or has no jti claim.
 * On failure logs a dev warning and skips the current-session highlight.
 */
function resolveCurrentJti(): string | undefined {
  try {
    const token = getAccessToken();
    if (!token) return undefined;

    const claims = decodeAccessClaims(token);
    if (!claims) return undefined;

    // jti is not typed in AccessClaims but may exist in the token payload
    const jti = (claims as typeof claims & { jti?: string }).jti;
    if (typeof jti === "string" && jti) return jti;

    if (process.env.NODE_ENV !== "production") {
      console.warn(
        "[SessionsList] Access token has no jti claim — current session highlight skipped",
      );
    }
    return undefined;
  } catch {
    return undefined;
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function SessionsList() {
  const { authFetch } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  // Resolved once on mount — access token doesn't change while the page is open
  const [currentJti] = useState<string | undefined>(resolveCurrentJti);

  const loadSessions = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const res = await authFetch("/api/auth/sessions", {});
      if (!res.ok) {
        setError(true);
        return;
      }
      const data: unknown = await res.json();
      setSessions(
        Array.isArray(data)
          ? (data as Session[])
          : ((data as { sessions?: Session[] }).sessions ?? []),
      );
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [authFetch]);

  useEffect(() => {
    void loadSessions();
  }, [loadSessions]);

  if (loading) {
    return (
      <div
        className="flex items-center justify-center gap-2 py-6"
        data-testid="sessions-loading"
      >
        <Loader2 className="h-4 w-4 animate-spin text-primary" />
        <span className="text-xs text-on-surface/40">
          Cargando sesiones activas...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="flex items-center gap-2 rounded-lg bg-[#93000a]/10 px-3 py-2 text-xs text-[#ffb4ab]/70"
        data-testid="sessions-error"
      >
        <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
        <span>No se pudieron cargar las sesiones activas.</span>
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div
        className="flex flex-col items-center justify-center rounded-lg border border-dashed border-[rgba(79,70,51,0.15)] py-6 text-center"
        data-testid="sessions-empty"
      >
        <Monitor className="mb-2 h-7 w-7 text-on-surface/10" />
        <p className="text-xs text-on-surface/40">
          Sin sesiones activas registradas.
        </p>
      </div>
    );
  }

  return (
    <div data-testid="sessions-list">
      <div className="mb-2 flex items-center gap-2">
        <Monitor className="h-3.5 w-3.5 text-primary" />
        <h3 className="text-xs font-semibold uppercase tracking-[0.15em] text-on-surface/55">
          Sesiones activas
        </h3>
        <span className="ml-auto text-[10px] text-on-surface/30">
          Solo lectura · Usá &ldquo;Cerrar todas&rdquo; para revocar
        </span>
      </div>

      <div className="overflow-x-auto rounded-xl border border-[rgba(79,70,51,0.12)] bg-surface">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[rgba(79,70,51,0.12)] text-[10px] uppercase tracking-[0.14em] text-on-surface/35">
              <th className="px-3 py-2 text-left font-medium">ID sesión</th>
              <th className="px-3 py-2 text-left font-medium">Iniciada</th>
              <th className="px-3 py-2 text-left font-medium">Expira</th>
              <th className="px-3 py-2 text-left font-medium">Dispositivo</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((session) => {
              const isCurrent =
                currentJti !== undefined && session.jti === currentJti;
              return (
                <tr
                  key={session.jti}
                  className={`border-b border-[rgba(79,70,51,0.08)] last:border-0 ${
                    isCurrent ? "bg-primary/5" : ""
                  }`}
                  data-testid={`session-row-${session.jti}`}
                >
                  <td className="px-3 py-2.5 font-mono text-on-surface/60">
                    <span title={session.jti}>{truncateJti(session.jti)}</span>
                    {isCurrent && (
                      <span
                        className="ml-2 rounded-full bg-primary/15 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-primary"
                        data-testid="current-session-badge"
                      >
                        Sesión actual
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-on-surface/50">
                    {formatDate(session.created_at)}
                  </td>
                  <td className="px-3 py-2.5 text-on-surface/50">
                    {formatDate(session.expires_at)}
                  </td>
                  <td className="max-w-[12rem] truncate px-3 py-2.5 text-on-surface/40">
                    {session.user_agent ?? session.ip_address ?? "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
