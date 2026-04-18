"use client";

import { useEffect, useState } from "react";
import {
  Eye,
  EyeOff,
  Loader2,
  AlertCircle,
  CheckCircle2,
  ArrowLeft,
  X,
} from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { clearAuth, login, validateSession } from "@/lib/auth";
import { useTheme } from "@/components/ThemeProvider";
import { cn } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [ssoLoading, setSsoLoading] = useState<"google" | "microsoft" | null>(null);
  const [showResetForm, setShowResetForm] = useState(false);
  const [resetEmail, setResetEmail] = useState("");
  const [resetStatus, setResetStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnTo = searchParams.get("returnTo") || "/";

  useEffect(() => {
    let cancelled = false;
    const verify = async () => {
      const status = await validateSession();
      if (cancelled) return;
      if (status === "valid") { router.replace(returnTo); return; }
      if (status === "invalid") { clearAuth(); }
    };
    verify();
    const handleOnline = () => { void verify(); };
    window.addEventListener("online", handleOnline);
    let interval: number | null = null;
    if (searchParams.get("reason") === "offline") {
      interval = window.setInterval(() => { void verify(); }, 5000);
    }
    return () => {
      cancelled = true;
      window.removeEventListener("online", handleOnline);
      if (interval) window.clearInterval(interval);
    };
  }, [router, returnTo, searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push(returnTo);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar sesión");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError("");
    setSsoLoading("google");
    try {
      const res = await fetch(`${API_URL}/api/auth/oauth/google/authorize`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: "Error al iniciar Google SSO" }));
        setError(data.detail ?? "Error al iniciar Google SSO");
        return;
      }
      const { url } = await res.json();
      window.location.href = url;
    } catch {
      setError("No se pudo conectar con el servidor.");
    } finally {
      setSsoLoading(null);
    }
  };

  const handleMicrosoftLogin = async () => {
    setError("");
    setSsoLoading("microsoft");
    try {
      const res = await fetch(`${API_URL}/api/auth/oauth/microsoft/authorize`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: "Error al iniciar Microsoft SSO" }));
        setError(data.detail ?? "Error al iniciar Microsoft SSO");
        return;
      }
      const { url } = await res.json();
      window.location.href = url;
    } catch {
      setError("No se pudo conectar con el servidor.");
    } finally {
      setSsoLoading(null);
    }
  };

  const handlePasswordReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setResetStatus("sending");
    try {
      const res = await fetch(`${API_URL}/api/auth/password-reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: resetEmail }),
      });
      if (!res.ok) { setResetStatus("error"); return; }
      setResetStatus("sent");
    } catch {
      setResetStatus("error");
    }
  };

  return (
    <main className="min-h-screen flex flex-col md:flex-row font-body bg-background">

      {/* ── LEFT COLUMN — Branding (desktop only) ── */}
      <div className="hidden md:flex md:w-1/2 min-h-screen flex-col justify-center items-center px-16 relative overflow-hidden bg-secondary-container/20">
        {/* Subtle radial glows */}
        <div className="absolute top-0 right-0 w-96 h-96 rounded-full blur-3xl pointer-events-none bg-primary/5" />
        <div className="absolute bottom-0 left-0 w-64 h-64 rounded-full blur-3xl pointer-events-none bg-secondary/5" />

        <div className="relative z-10 flex flex-col items-center text-center max-w-sm">
          {/* Mascot */}
          <Image
            src="/brand/tukan.png"
            alt="Mascota TukiJuris"
            width={220}
            height={220}
            className="w-40 h-auto object-contain mb-4"
            priority
          />
          <div className="font-headline text-[2.8rem] leading-none tracking-[-0.05em] font-bold text-primary">
            TukiJuris
          </div>
          <div className="mt-1 text-[0.72rem] uppercase tracking-[0.42em] text-on-surface-variant/60">
            Abogados
          </div>

          {/* Gold divider */}
          <div className="w-24 h-px my-5 bg-primary/30" />

          <p className="font-headline italic text-xl leading-snug text-on-surface/80">
            Asistente Legal IA
          </p>
          <p className="text-sm text-center mt-4 leading-relaxed text-on-surface-variant/50">
            Consultas legales inteligentes con respuestas citadas del derecho peruano.
          </p>

          {/* Trust words */}
          <div className="mt-10 pt-8 border-t border-ghost-border w-full">
            <p className="text-xs text-center tracking-widest uppercase text-primary/50">
              Precisión · Autoridad · Eficiencia
            </p>
          </div>
        </div>
      </div>

      {/* ── MOBILE HEADER (compact) ── */}
      <div className="flex md:hidden items-center gap-3 pt-8 pb-4 px-6 bg-background">
        <Image
          src="/brand/logo-icon.png"
          alt="TukiJuris"
          width={40}
          height={40}
          className="w-10 h-10 object-contain"
          priority
        />
        <div>
          <div className="font-headline text-xl leading-none font-bold text-primary">
            TukiJuris
          </div>
          <div className="text-[0.6rem] uppercase tracking-[0.3em] text-on-surface-variant/50">
            Asistente Legal IA
          </div>
        </div>
      </div>

      {/* ── RIGHT COLUMN — Form ── */}
      <div className="w-full md:w-1/2 bg-background min-h-0 md:min-h-screen flex flex-col justify-center px-4 sm:px-6 md:px-16">
        <div className="w-full max-w-lg mx-auto py-6 md:py-0">

          {/* Form card */}
          <div className="p-6 sm:p-8 md:p-12 rounded-xl panel-raised">

            {/* Title area */}
            <div className="mb-8">
              <Link
                href="/landing"
                className="mb-4 inline-flex items-center gap-2 text-xs uppercase tracking-widest transition-colors text-on-surface-variant/45 hover:text-primary"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Volver al inicio
              </Link>
              <h2 className="font-headline text-3xl text-primary">
                Iniciar Sesión
              </h2>
              <p className="text-xs uppercase tracking-widest mt-2 text-on-surface-variant/50">
                Ingresá a tu cuenta para continuar
              </p>
            </div>

            {/* Error display */}
            {error && (
              <div className="flex items-start gap-3 bg-error-container/10 border border-error/20 rounded-lg p-4 text-error text-sm mb-6">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Login form */}
            <form onSubmit={handleSubmit} aria-label="Formulario de inicio de sesión" className="space-y-5">
              {/* Email */}
              <div>
                <label htmlFor="login-email" className="block text-xs uppercase tracking-widest mb-2 text-on-surface-variant/60">
                  Correo electrónico
                </label>
                <input
                  id="login-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full h-12 rounded-lg px-4 text-on-surface placeholder-on-surface/30 transition-all duration-200 control-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20"
                  placeholder="tu@email.com"
                  required
                  autoComplete="email"
                />
              </div>

              {/* Password */}
              <div>
                <label htmlFor="login-password" className="block text-xs uppercase tracking-widest mb-2 text-on-surface-variant/60">
                  Contraseña
                </label>
                <div className="relative">
                  <input
                    id="login-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full h-12 rounded-lg px-4 pr-12 text-on-surface placeholder-on-surface/30 transition-all duration-200 control-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20"
                    placeholder="••••••••"
                    required
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 transition-colors duration-200 p-1 text-on-surface-variant/40 hover:text-primary"
                    aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Forgot password */}
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => setShowResetForm(true)}
                  className="text-xs uppercase tracking-widest transition-colors duration-200 text-primary/70 hover:text-primary"
                >
                  ¿Olvidaste tu contraseña?
                </button>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={loading}
                className="w-full h-12 text-on-primary font-bold uppercase tracking-widest text-xs rounded-lg flex items-center justify-center gap-2 transition-all duration-200 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed mt-6 gold-gradient hover:shadow-lg hover:shadow-primary/20"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                {loading ? "Ingresando..." : "Iniciar Sesión"}
              </button>
            </form>

            {/* Divider */}
            <div className="relative flex items-center my-8">
              <div className="flex-1 border-t border-ghost-border" />
              <span className="mx-4 text-xs uppercase tracking-widest text-on-surface-variant/30">
                o continuar con
              </span>
              <div className="flex-1 border-t border-ghost-border" />
            </div>

            {/* SSO buttons */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Google */}
              <button
                type="button"
                onClick={handleGoogleLogin}
                disabled={ssoLoading !== null}
                aria-label="Iniciar sesión con Google"
                className="h-12 rounded-lg transition-all duration-200 flex items-center justify-center gap-3 text-xs uppercase tracking-widest disabled:opacity-50 disabled:cursor-not-allowed control-surface hover:border-primary/30 text-on-surface-variant"
              >
                {ssoLoading === "google" ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                  </svg>
                )}
                Google
              </button>

              {/* Microsoft */}
              <button
                type="button"
                onClick={handleMicrosoftLogin}
                disabled={ssoLoading !== null}
                aria-label="Iniciar sesión con Microsoft"
                className="h-12 rounded-lg transition-all duration-200 flex items-center justify-center gap-3 text-xs uppercase tracking-widest disabled:opacity-50 disabled:cursor-not-allowed control-surface hover:border-primary/30 text-on-surface-variant"
              >
                {ssoLoading === "microsoft" ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <svg className="w-4 h-4 shrink-0" viewBox="0 0 23 23" aria-hidden="true">
                    <rect x="1" y="1" width="10" height="10" fill="#F25022" />
                    <rect x="12" y="1" width="10" height="10" fill="#7FBA00" />
                    <rect x="1" y="12" width="10" height="10" fill="#00A4EF" />
                    <rect x="12" y="12" width="10" height="10" fill="#FFB900" />
                  </svg>
                )}
                Microsoft
              </button>
            </div>

            {/* Register link */}
            <p className="text-center text-xs uppercase tracking-widest mt-8 text-on-surface-variant/40">
              ¿No tienes cuenta?{" "}
              <Link
                href="/auth/register"
                className="font-headline italic normal-case tracking-normal text-sm transition-colors duration-200 text-primary/80 hover:text-primary"
              >
                Regístrate
              </Link>
            </p>
          </div>
        </div>
      </div>

      {/* ── PASSWORD RESET OVERLAY ── */}
      {showResetForm && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 px-4">
          <div className="w-full max-w-md rounded-xl p-8 relative panel-raised">
            {/* Close */}
            <button
              type="button"
              onClick={() => { setShowResetForm(false); setResetStatus("idle"); setResetEmail(""); }}
              className="absolute top-4 right-4 transition-colors duration-200 p-1 rounded-lg text-on-surface-variant/40 hover:text-on-surface hover:bg-surface-container"
              aria-label="Cerrar"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="font-headline text-2xl text-primary mb-1">
              Recuperar contraseña
            </h2>
            <div className="w-16 h-px mb-4 bg-primary/30" />
            <p className="text-xs uppercase tracking-widest mb-6 text-on-surface-variant/50">
              Te enviamos un enlace para restablecer tu contraseña.
            </p>

            {resetStatus === "sent" ? (
              <div className="flex items-start gap-3 bg-green-500/10 border border-green-500/20 rounded-lg p-4 text-green-400 text-sm">
                <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" />
                <span>Te enviamos un enlace de recuperación a tu email.</span>
              </div>
            ) : (
              <form onSubmit={handlePasswordReset} className="space-y-5">
                {resetStatus === "error" && (
                  <div className="flex items-start gap-3 bg-error-container/10 border border-error/20 rounded-lg p-4 text-error text-sm">
                    <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                    <span>Ocurrió un error. Intentá de nuevo.</span>
                  </div>
                )}
                <div>
                  <label htmlFor="reset-email" className="block text-xs uppercase tracking-widest mb-2 text-on-surface-variant/60">
                    Correo electrónico
                  </label>
                  <input
                    id="reset-email"
                    type="email"
                    value={resetEmail}
                    onChange={(e) => setResetEmail(e.target.value)}
                    className="w-full h-12 rounded-lg px-4 text-on-surface placeholder-on-surface/30 transition-all duration-200 control-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20"
                    placeholder="tu@email.com"
                    required
                    autoComplete="email"
                  />
                </div>
                <button
                  type="submit"
                  disabled={resetStatus === "sending"}
                  className="w-full h-12 text-on-primary font-bold uppercase tracking-widest text-xs rounded-lg flex items-center justify-center gap-2 transition-all duration-200 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed gold-gradient hover:shadow-lg hover:shadow-primary/20"
                >
                  {resetStatus === "sending" && <Loader2 className="w-4 h-4 animate-spin" />}
                  {resetStatus === "sending" ? "Enviando..." : "Enviar enlace"}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
