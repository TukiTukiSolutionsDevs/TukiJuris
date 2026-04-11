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

  const brandingPanelStyle = isDark
    ? {
        background: "linear-gradient(180deg, #1B2A4A 0%, #16233E 100%)",
      }
    : {
        background: "linear-gradient(180deg, #E7EEF8 0%, #D8E3F4 100%)",
      };

  const authMascotSrc = "/brand/tukan.png";

  const formShellStyle = isDark
    ? {
        background: "linear-gradient(180deg, #111116 0%, #0C0D12 100%)",
        border: "1px solid rgba(79,70,51,0.10)",
        boxShadow: "0 28px 80px rgba(0,0,0,0.34)",
      }
    : {
        background: "linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%)",
        border: "1px solid rgba(15,23,42,0.10)",
        boxShadow: "0 28px 80px rgba(15,23,42,0.10)",
      };

  const inputClassName = isDark
    ? "w-full h-12 bg-[#35343a] border border-transparent rounded-lg px-4 text-on-surface placeholder-on-surface/30 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all duration-200"
    : "w-full h-12 bg-[#F3F4F6] border border-[#D7DEE8] rounded-lg px-4 text-[#0F172A] placeholder-[#64748B] focus:outline-none focus:border-[#B88A00] focus:ring-2 focus:ring-[#E8C24A]/20 transition-all duration-200";

  const subtleTextClass = isDark ? "text-on-surface/50" : "text-[#5B6472]";
  const labelTextClass = isDark ? "text-on-surface/60" : "text-[#334155]";
  const dividerClass = isDark ? "border-[rgba(79,70,51,0.15)]" : "border-[rgba(148,163,184,0.45)]";
  const returnTo = searchParams.get("returnTo") || "/";

  useEffect(() => {
    let cancelled = false;

    const verify = async () => {
      const status = await validateSession();
      if (cancelled) return;

      if (status === "valid") {
        router.replace(returnTo);
        return;
      }

      if (status === "invalid") {
        clearAuth();
      }
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
      if (!res.ok) {
        setResetStatus("error");
        return;
      }
      setResetStatus("sent");
    } catch {
      setResetStatus("error");
    }
  };

  return (
    <main className="min-h-screen flex flex-col md:flex-row font-['Manrope']">

      {/* ── LEFT COLUMN — Branding ── */}
      <div className="hidden md:flex md:w-1/2 min-h-screen flex-col justify-center items-center px-16 relative overflow-hidden" style={brandingPanelStyle}>
        {/* Subtle radial glows */}
        <div className={`absolute top-0 right-0 w-96 h-96 rounded-full blur-3xl pointer-events-none ${isDark ? "bg-primary/5" : "bg-[#F8D76B]/20"}`} />
        <div className={`absolute bottom-0 left-0 w-64 h-64 rounded-full blur-3xl pointer-events-none ${isDark ? "bg-primary/3" : "bg-[#93C5FD]/20"}`} />

        <div className="relative z-10 flex flex-col items-center text-center max-w-sm">
          {/* Mascot + wordmark */}
          <div className="mb-8 px-8 py-4" style={isDark ? { background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)", borderRadius: "2rem", boxShadow: "0 18px 60px rgba(15,23,42,0.12)" } : undefined}>
            <div className="flex flex-col items-center text-center">
              <Image
                src={authMascotSrc}
                alt="Mascota TukiJuris"
                width={220}
                height={220}
                className="w-36 h-auto object-contain"
                priority
              />
              <div className={`mt-3 font-['Newsreader'] text-[2.8rem] leading-none tracking-[-0.05em] font-bold ${isDark ? "text-primary" : "text-[#1B2A4A]"}`}>
                TukiJuris
              </div>
              <div className={`mt-1 text-[0.72rem] uppercase tracking-[0.42em] ${isDark ? "text-on-surface/60" : "text-[#51627E]"}`}>
                Abogados
              </div>
            </div>
          </div>

          {/* Gold divider */}
          <div className={`w-24 h-px my-5 ${isDark ? "bg-primary/30" : "bg-[#B88A00]/35"}`} />

          {/* Subtitle */}
          <p className={`font-['Newsreader'] italic text-xl leading-snug ${isDark ? "text-on-surface/80" : "text-[#1E293B]"}`}>
            Asistente Legal IA
          </p>

          {/* Description */}
          <p className={`text-sm text-center mt-4 leading-relaxed ${subtleTextClass}`}>
            Consultas legales inteligentes con respuestas citadas del derecho peruano.
          </p>

          {/* Trust words */}
          <div className={`mt-10 pt-8 border-t w-full ${dividerClass}`}>
            <p className={`text-xs text-center tracking-widest uppercase ${isDark ? "text-primary/50" : "text-[#8A6A00]"}`}>
              Precisión · Autoridad · Eficiencia
            </p>
          </div>
        </div>

        {/* Status indicator — bottom right */}
        <div className="absolute bottom-6 right-6 flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
          </span>
          <span className={`text-xs uppercase tracking-widest ${isDark ? "text-on-surface/40" : "text-[#475569]"}`}>
            Sistemas Operativos
          </span>
        </div>
      </div>

      {/* ── MOBILE HEADER (small screens) ── */}
      <div className="flex md:hidden flex-col items-center pt-10 pb-6 px-6" style={brandingPanelStyle}>
        <Image
          src={authMascotSrc}
          alt="Mascota TukiJuris"
          width={148}
          height={148}
          className="w-24 h-auto object-contain mb-2"
          priority
        />
        <div className={`font-['Newsreader'] text-3xl leading-none tracking-[-0.05em] font-bold ${isDark ? "text-primary" : "text-[#1B2A4A]"}`}>
          TukiJuris
        </div>
        <div className={`mt-1 text-[0.65rem] uppercase tracking-[0.38em] ${isDark ? "text-on-surface/55" : "text-[#51627E]"}`}>
          Abogados
        </div>
        <p className={`font-['Newsreader'] italic text-base text-center ${isDark ? "text-on-surface/70" : "text-[#334155]"}`}>
          Asistente Legal IA
        </p>
      </div>

      {/* ── RIGHT COLUMN — Form ── */}
      <div className="w-full md:w-1/2 bg-background min-h-screen flex flex-col justify-center px-6 md:px-16">
        <div className="w-full max-w-lg mx-auto py-10 md:py-0">

          {/* Form card */}
          <div className="p-8 md:p-12 rounded-[1.75rem]" style={formShellStyle}>

            {/* Title area */}
            <div className="mb-8">
                <Link
                  href="/landing"
                  className={`mb-4 inline-flex items-center gap-2 text-xs uppercase tracking-widest transition-colors ${isDark ? "text-on-surface/45 hover:text-primary" : "text-[#64748B] hover:text-[#A67C00]"}`}
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  Volver al inicio
                </Link>
                <h2 className={`font-['Newsreader'] text-3xl mb-1 ${isDark ? "text-primary" : "text-[#A67C00]"}`}>
                  Iniciar Sesión
                </h2>
                <p className={`text-xs uppercase tracking-widest mt-2 ${subtleTextClass}`}>
                  Ingresá a tu cuenta para continuar
                </p>
              </div>

            {/* Error display */}
            {error && (
              <div className="flex items-start gap-3 bg-[#F87171]/10 border border-[#F87171]/20 rounded-lg p-4 text-[#F87171] text-sm mb-6">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Login form */}
            <form
              onSubmit={handleSubmit}
              aria-label="Formulario de inicio de sesión"
              className="space-y-5"
            >
              {/* Email field */}
              <div>
                <label
                  htmlFor="login-email"
                  className={`block text-xs uppercase tracking-widest mb-2 ${labelTextClass}`}
                >
                  Correo electrónico
                </label>
                <input
                  id="login-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={inputClassName}
                  placeholder="tu@email.com"
                  required
                  autoComplete="email"
                />
              </div>

              {/* Password field */}
              <div>
                <label
                  htmlFor="login-password"
                  className={`block text-xs uppercase tracking-widest mb-2 ${labelTextClass}`}
                >
                  Contraseña
                </label>
                <div className="relative">
                  <input
                    id="login-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={`${inputClassName} pr-12`}
                    placeholder="••••••••"
                    required
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className={`absolute right-3 top-1/2 -translate-y-1/2 transition-colors duration-200 p-1 ${isDark ? "text-on-surface/40 hover:text-primary" : "text-[#64748B] hover:text-[#A67C00]"}`}
                    aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                  >
                    {showPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Forgot password link */}
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => setShowResetForm(true)}
                  className={`text-xs uppercase tracking-widest transition-colors duration-200 ${isDark ? "text-primary/70 hover:text-primary" : "text-[#8A6A00] hover:text-[#A67C00]"}`}
                >
                  ¿Olvidaste tu contraseña?
                </button>
              </div>

              {/* Submit button */}
              <button
                type="submit"
                disabled={loading}
                className={`w-full h-12 text-on-primary font-bold uppercase tracking-widest text-xs rounded-lg flex items-center justify-center gap-2 transition-all duration-200 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed mt-6 ${isDark ? "bg-gradient-to-tr from-primary to-primary-container hover:shadow-lg hover:shadow-primary/20" : "bg-gradient-to-tr from-[#B88A00] to-[#E8C24A] hover:shadow-lg hover:shadow-[#E8C24A]/20"}`}
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : null}
                {loading ? "Ingresando..." : "Iniciar Sesión"}
              </button>
            </form>

            {/* Divider */}
            <div className="relative flex items-center my-8">
              <div className={`flex-1 border-t ${dividerClass}`} />
              <span className={`mx-4 text-xs uppercase tracking-widest ${isDark ? "text-on-surface/30" : "text-[#64748B]"}`}>
                o continuar con
              </span>
              <div className={`flex-1 border-t ${dividerClass}`} />
            </div>

            {/* SSO buttons */}
            <div className="grid grid-cols-2 gap-4">
              {/* Google */}
              <button
                type="button"
                onClick={handleGoogleLogin}
                disabled={ssoLoading !== null}
                aria-label="Iniciar sesión con Google"
                className={`h-12 border rounded-lg transition-all duration-200 flex items-center justify-center gap-3 text-xs uppercase tracking-widest disabled:opacity-50 disabled:cursor-not-allowed ${isDark ? "bg-[#111116] border-[rgba(79,70,51,0.2)] hover:border-primary/40 text-on-surface/70 hover:text-on-surface" : "bg-white border-[#D7DEE8] hover:border-[#B88A00]/40 text-[#334155] hover:text-[#0F172A]"}`}
              >
                {ssoLoading === "google" ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" aria-hidden="true">
                    <path
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      fill="#4285F4"
                    />
                    <path
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      fill="#34A853"
                    />
                    <path
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      fill="#FBBC05"
                    />
                    <path
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      fill="#EA4335"
                    />
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
                className={`h-12 border rounded-lg transition-all duration-200 flex items-center justify-center gap-3 text-xs uppercase tracking-widest disabled:opacity-50 disabled:cursor-not-allowed ${isDark ? "bg-[#111116] border-[rgba(79,70,51,0.2)] hover:border-primary/40 text-on-surface/70 hover:text-on-surface" : "bg-white border-[#D7DEE8] hover:border-[#B88A00]/40 text-[#334155] hover:text-[#0F172A]"}`}
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
            <p className={`text-center text-xs uppercase tracking-widest mt-8 ${isDark ? "text-on-surface/40" : "text-[#64748B]"}`}>
              ¿No tienes cuenta?{" "}
              <Link
                href="/auth/register"
                className={`font-['Newsreader'] italic normal-case tracking-normal text-sm transition-colors duration-200 ${isDark ? "text-primary/80 hover:text-primary" : "text-[#A67C00] hover:text-[#8A6A00]"}`}
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
          <div className="w-full max-w-md rounded-[1.5rem] p-8 relative" style={formShellStyle}>

            {/* Close button */}
            <button
              type="button"
              onClick={() => {
                setShowResetForm(false);
                setResetStatus("idle");
                setResetEmail("");
              }}
              className={`absolute top-4 right-4 transition-colors duration-200 p-1 rounded-lg ${isDark ? "text-on-surface/40 hover:text-on-surface hover:bg-[#35343a]" : "text-[#64748B] hover:text-[#0F172A] hover:bg-[#EEF2F7]"}`}
              aria-label="Cerrar"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className={`font-['Newsreader'] text-2xl mb-1 ${isDark ? "text-primary" : "text-[#A67C00]"}`}>
              Recuperar contraseña
            </h2>
            {/* Thin gold divider */}
            <div className={`w-16 h-px mb-4 ${isDark ? "bg-primary/30" : "bg-[#B88A00]/35"}`} />
            <p className={`text-xs uppercase tracking-widest mb-6 ${subtleTextClass}`}>
              Te enviamos un enlace para restablecer tu contraseña.
            </p>

            {/* Success state */}
            {resetStatus === "sent" ? (
              <div className="flex items-start gap-3 bg-green-500/10 border border-green-500/20 rounded-lg p-4 text-green-400 text-sm">
                <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" />
                <span>
                  Te enviamos un enlace de recuperación a tu email.
                </span>
              </div>
            ) : (
              <form onSubmit={handlePasswordReset} className="space-y-5">
                {/* Error in reset form */}
                {resetStatus === "error" && (
                  <div className="flex items-start gap-3 bg-[#F87171]/10 border border-[#F87171]/20 rounded-lg p-4 text-[#F87171] text-sm">
                    <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                    <span>Ocurrió un error. Intentá de nuevo.</span>
                  </div>
                )}

                <div>
                  <label
                    htmlFor="reset-email"
                    className={`block text-xs uppercase tracking-widest mb-2 ${labelTextClass}`}
                  >
                    Correo electrónico
                  </label>
                  <input
                    id="reset-email"
                    type="email"
                    value={resetEmail}
                    onChange={(e) => setResetEmail(e.target.value)}
                    className={inputClassName}
                    placeholder="tu@email.com"
                    required
                    autoComplete="email"
                  />
                </div>

                <button
                  type="submit"
                  disabled={resetStatus === "sending"}
                  className={`w-full h-12 text-on-primary font-bold uppercase tracking-widest text-xs rounded-lg flex items-center justify-center gap-2 transition-all duration-200 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed ${isDark ? "bg-gradient-to-tr from-primary to-primary-container hover:shadow-lg hover:shadow-primary/20" : "bg-gradient-to-tr from-[#B88A00] to-[#E8C24A] hover:shadow-lg hover:shadow-[#E8C24A]/20"}`}
                >
                  {resetStatus === "sending" && (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  )}
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
