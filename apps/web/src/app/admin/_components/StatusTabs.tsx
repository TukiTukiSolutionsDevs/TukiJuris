"use client";

/**
 * StatusTabs — group of "current configuration status" tabs.
 *
 * These tabs render read-only views of env-var / external-config presence:
 *   - OAuthTab        — Google / Microsoft
 *   - PagosTab        — Culqi / Mercado Pago
 *   - SeguridadTab    — JWT, BYOK encryption
 *   - ObservabilidadTab — Sentry, logs
 *
 * Editing these requires touching .env + server restart (Phase 3).
 */

import { useEffect, useState } from "react";
import {
  Loader2, AlertTriangle, Plug, Banknote, Lock, Eye, Check, X, Copy,
} from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";

interface ProviderRow {
  id: string;
  name: string;
  configured: boolean;
  webhook_secret_configured?: boolean;
  callback_url?: string;
  webhook_url?: string;
}

function StatusPill({ ok, labelOk = "Configurado", labelKo = "Sin configurar" }: { ok: boolean; labelOk?: string; labelKo?: string }) {
  return ok ? (
    <span className="inline-flex items-center gap-1.5 text-[10px] uppercase tracking-[0.15em] text-emerald-300 bg-emerald-400/10 border border-emerald-400/20 rounded-full px-2.5 py-1">
      <Check className="w-3 h-3" />
      {labelOk}
    </span>
  ) : (
    <span className="inline-flex items-center gap-1.5 text-[10px] uppercase tracking-[0.15em] text-amber-300 bg-amber-400/10 border border-amber-400/20 rounded-full px-2.5 py-1">
      <X className="w-3 h-3" />
      {labelKo}
    </span>
  );
}

function PageShell({
  title,
  description,
  icon: Icon,
  children,
}: {
  title: string;
  description: string;
  icon: React.ElementType;
  children: React.ReactNode;
}) {
  return (
    <div className="w-full px-4 py-6 sm:py-8 lg:px-6 xl:px-8 space-y-6">
      <header className="flex items-center gap-3">
        <div className="w-11 h-11 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
          <Icon className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="font-['Newsreader'] text-2xl font-bold text-primary">{title}</h2>
          <p className="text-xs text-on-surface/50">{description}</p>
        </div>
      </header>
      {children}
    </div>
  );
}

// ----------------------------------------------------------------------------
// OAuth
// ----------------------------------------------------------------------------

interface OAuthConfig {
  providers: ProviderRow[];
}

export function OAuthTab() {
  const { authFetch } = useAuth();
  const [data, setData] = useState<OAuthConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void authFetch("/api/admin/config/oauth", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then(setData)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [authFetch]);

  if (loading) return <CenteredSpinner />;
  if (error || !data) return <ErrorBlock msg={error} />;

  return (
    <PageShell title="OAuth Providers" description="Identidad federada · status según variables de entorno." icon={Plug}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data.providers.map((p) => (
          <div
            key={p.id}
            className="bg-surface-container-low rounded-xl p-5"
            style={{ border: "1px solid rgba(79,70,51,0.15)" }}
          >
            <div className="flex items-center justify-between mb-3">
              <p className="font-medium text-on-surface">{p.name}</p>
              <StatusPill ok={p.configured} />
            </div>
            <p className="text-[10px] uppercase tracking-[0.15em] text-on-surface/40 mb-1">Callback</p>
            <p className="font-mono text-[11px] text-on-surface/70 break-all">{p.callback_url}</p>
          </div>
        ))}
      </div>
    </PageShell>
  );
}

// ----------------------------------------------------------------------------
// Pagos
// ----------------------------------------------------------------------------

interface PaymentsConfig {
  providers: ProviderRow[];
  beta_mode: boolean;
}

export function PagosTab() {
  const { authFetch } = useAuth();
  const [data, setData] = useState<PaymentsConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void authFetch("/api/admin/config/payments", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then(setData)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [authFetch]);

  if (loading) return <CenteredSpinner />;
  if (error || !data) return <ErrorBlock msg={error} />;

  return (
    <PageShell title="Proveedores de pago" description="Culqi y Mercado Pago · llaves jamás se exponen, solo el estado." icon={Banknote}>
      {data.beta_mode && (
        <div className="bg-amber-400/5 border border-amber-400/20 rounded-xl px-4 py-3 text-xs text-amber-300">
          Beta mode activo: validación de webhook permisiva. Configurar webhook secrets antes de salir de beta.
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data.providers.map((p) => (
          <div
            key={p.id}
            className="bg-surface-container-low rounded-xl p-5"
            style={{ border: "1px solid rgba(79,70,51,0.15)" }}
          >
            <div className="flex items-center justify-between mb-3">
              <p className="font-medium text-on-surface">{p.name}</p>
              <StatusPill ok={p.configured} labelOk="Activo" labelKo="Inactivo" />
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-on-surface/50">Webhook secret</span>
                <StatusPill ok={!!p.webhook_secret_configured} labelOk="Set" labelKo="Vacío" />
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-[0.15em] text-on-surface/40 mb-1">Webhook URL</p>
                <p className="font-mono text-[11px] text-on-surface/70 break-all">{p.webhook_url}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
      <p className="text-xs text-on-surface/40 italic">
        Configuración en <code className="bg-surface-container-low px-1 py-0.5 rounded">.env</code>:
        CULQI_PUBLIC_KEY, CULQI_SECRET_KEY, CULQI_WEBHOOK_SECRET, MP_ACCESS_TOKEN, MP_PUBLIC_KEY, MP_WEBHOOK_SECRET.
      </p>
    </PageShell>
  );
}

// ----------------------------------------------------------------------------
// Seguridad
// ----------------------------------------------------------------------------

interface SecurityConfig {
  jwt: {
    algorithm: string;
    secret_configured: boolean;
    access_token_minutes: number;
    refresh_token_days: number;
  };
  byok: {
    encryption_key_configured: boolean;
    using_jwt_fallback: boolean;
    warning: string | null;
  };
  rate_limit_window_seconds: number;
}

export function SeguridadTab() {
  const { authFetch } = useAuth();
  const [data, setData] = useState<SecurityConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void authFetch("/api/admin/config/security", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then(setData)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [authFetch]);

  if (loading) return <CenteredSpinner />;
  if (error || !data) return <ErrorBlock msg={error} />;

  return (
    <PageShell title="Seguridad & Encriptación" description="JWT, BYOK encryption, ventanas de rate-limit." icon={Lock}>
      {data.byok.warning && (
        <div className="bg-red-500/10 border border-red-400/30 rounded-xl px-4 py-3 text-xs text-red-300 flex gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          {data.byok.warning}
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          className="bg-surface-container-low rounded-xl p-5"
          style={{ border: "1px solid rgba(79,70,51,0.15)" }}
        >
          <p className="font-medium text-on-surface mb-3">JWT</p>
          <dl className="space-y-2 text-xs">
            <Row k="Algorithm" v={<span className="font-mono">{data.jwt.algorithm}</span>} />
            <Row k="Secret" v={<StatusPill ok={data.jwt.secret_configured} labelOk="Set" labelKo="Vacío" />} />
            <Row k="Access TTL" v={<span className="font-mono">{data.jwt.access_token_minutes} min</span>} />
            <Row k="Refresh TTL" v={<span className="font-mono">{data.jwt.refresh_token_days} días</span>} />
          </dl>
        </div>

        <div
          className="bg-surface-container-low rounded-xl p-5"
          style={{ border: "1px solid rgba(79,70,51,0.15)" }}
        >
          <p className="font-medium text-on-surface mb-3">BYOK Encryption</p>
          <dl className="space-y-2 text-xs">
            <Row k="BYOK_ENCRYPTION_KEY" v={<StatusPill ok={data.byok.encryption_key_configured} labelOk="Set" labelKo="Vacío" />} />
            <Row k="Fallback JWT" v={data.byok.using_jwt_fallback ? <span className="text-amber-300">Activo (inseguro)</span> : <span className="text-emerald-300">No usado</span>} />
            <Row k="Login window" v={<span className="font-mono">{data.rate_limit_window_seconds}s</span>} />
          </dl>
        </div>
      </div>
    </PageShell>
  );
}

// ----------------------------------------------------------------------------
// Observabilidad
// ----------------------------------------------------------------------------

interface ObservabilityConfig {
  sentry: { configured: boolean; dsn_host: string | null };
  logs: { level: string; format: string };
}

export function ObservabilidadTab() {
  const { authFetch } = useAuth();
  const [data, setData] = useState<ObservabilityConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void authFetch("/api/admin/config/observability", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then(setData)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [authFetch]);

  if (loading) return <CenteredSpinner />;
  if (error || !data) return <ErrorBlock msg={error} />;

  return (
    <PageShell title="Observabilidad" description="Sentry, logs, alertas." icon={Eye}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-surface-container-low rounded-xl p-5" style={{ border: "1px solid rgba(79,70,51,0.15)" }}>
          <div className="flex items-center justify-between mb-3">
            <p className="font-medium text-on-surface">Sentry</p>
            <StatusPill ok={data.sentry.configured} />
          </div>
          {data.sentry.dsn_host && (
            <p className="font-mono text-[11px] text-on-surface/60">{data.sentry.dsn_host}</p>
          )}
          {!data.sentry.configured && (
            <p className="text-xs text-on-surface/40">
              SENTRY_DSN vacío — los errores no se reportan.
            </p>
          )}
        </div>

        <div className="bg-surface-container-low rounded-xl p-5" style={{ border: "1px solid rgba(79,70,51,0.15)" }}>
          <p className="font-medium text-on-surface mb-3">Logs</p>
          <dl className="space-y-2 text-xs">
            <Row k="Nivel" v={<span className="font-mono uppercase">{data.logs.level}</span>} />
            <Row k="Formato" v={<span className="font-mono">{data.logs.format}</span>} />
          </dl>
        </div>
      </div>
    </PageShell>
  );
}

// ----------------------------------------------------------------------------
// Helpers
// ----------------------------------------------------------------------------

function CenteredSpinner() {
  return (
    <div className="w-full px-4 py-12 flex items-center justify-center">
      <Loader2 className="w-6 h-6 animate-spin text-primary" />
    </div>
  );
}

function ErrorBlock({ msg }: { msg: string | null }) {
  return (
    <div className="w-full px-4 py-6">
      <div className="bg-red-500/10 border border-red-400/20 text-red-300 rounded-xl px-4 py-3 text-sm flex items-center gap-2">
        <AlertTriangle className="w-4 h-4" />
        {msg ?? "Error cargando datos."}
      </div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-on-surface/60">{k}</dt>
      <dd>{v}</dd>
    </div>
  );
}
