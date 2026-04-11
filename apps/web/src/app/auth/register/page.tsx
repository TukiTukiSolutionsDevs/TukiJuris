"use client";

import { useEffect, useState } from "react";
import {
  Eye,
  EyeOff,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Circle,
  Mail,
  User,
  Lock,
} from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { register, getToken } from "@/lib/auth";
import { useTheme } from "@/components/ThemeProvider";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const passwordRegex = /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{8,}$/;

interface PasswordRule {
  label: string;
  test: (pwd: string) => boolean;
}

const PASSWORD_RULES: PasswordRule[] = [
  { label: "Mínimo 8 caracteres", test: (p) => p.length >= 8 },
  { label: "Una letra mayúscula", test: (p) => /[A-Z]/.test(p) },
  { label: "Una letra minúscula", test: (p) => /[a-z]/.test(p) },
  { label: "Un número", test: (p) => /\d/.test(p) },
];

export default function RegisterPage() {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [ssoLoading, setSsoLoading] = useState<"google" | "microsoft" | null>(null);
  const router = useRouter();

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
    ? "w-full h-[50px] bg-[#35343a] border border-transparent rounded-lg pl-10 pr-4 text-on-surface placeholder-on-surface/30 text-sm focus:outline-none focus:border-primary/40 focus:ring-1 focus:ring-primary/10 transition-all duration-200"
    : "w-full h-[50px] bg-[#F3F4F6] border border-[#D7DEE8] rounded-lg pl-10 pr-4 text-[#0F172A] placeholder-[#64748B] text-sm focus:outline-none focus:border-[#B88A00] focus:ring-2 focus:ring-[#E8C24A]/20 transition-all duration-200";

  const subtleTextClass = isDark ? "text-on-surface/50" : "text-[#5B6472]";
  const labelTextClass = isDark ? "text-on-surface/60" : "text-[#334155]";
  const dividerClass = isDark ? "bg-[rgba(79,70,51,0.2)]" : "bg-[rgba(148,163,184,0.45)]";

  useEffect(() => {
    const token = getToken();
    if (token) {
      router.push("/");
    }
  }, [router]);

  const handleGoogleSSO = async () => {
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

  const handleMicrosoftSSO = async () => {
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    if (!passwordRegex.test(password)) {
      setError("La contraseña debe tener mínimo 8 caracteres, una mayúscula, una minúscula y un número");
      setLoading(false);
      return;
    }

    try {
      await register(email, password, name || undefined);
      router.push("/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al registrar");
    } finally {
      setLoading(false);
    }
  };

  const isPasswordValid = passwordRegex.test(password);
  const isSubmitDisabled =
    loading ||
    !email ||
    !password ||
    !termsAccepted ||
    !isPasswordValid;

  return (
    <main className="min-h-screen flex flex-col md:flex-row bg-background font-['Manrope']">

      {/* ── LEFT COLUMN — Branding (55%) ── */}
      <div className="hidden md:flex md:w-[55%] min-h-screen flex-col justify-between relative overflow-hidden" style={brandingPanelStyle}>
        {/* Overlay gradient */}
        <div className="absolute inset-0 pointer-events-none" style={{ background: isDark ? "linear-gradient(135deg, rgba(27,42,74,0.92) 0%, rgba(22,34,64,0.96) 58%, rgba(13,24,41,1) 100%)" : "linear-gradient(135deg, rgba(231,238,248,0.94) 0%, rgba(216,227,244,0.98) 58%, rgba(199,213,234,1) 100%)" }} />
        {/* Gold glow blobs */}
        <div className={`absolute top-16 right-16 w-80 h-80 rounded-full blur-3xl pointer-events-none ${isDark ? "bg-primary/6" : "bg-[#F8D76B]/20"}`} />
        <div className={`absolute bottom-24 left-12 w-56 h-56 rounded-full blur-3xl pointer-events-none ${isDark ? "bg-primary/4" : "bg-[#93C5FD]/20"}`} />
        {/* Soft atmospheric glow — avoid noisy line texture */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: isDark
              ? "radial-gradient(circle at 22% 18%, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.00) 24%), radial-gradient(circle at 78% 24%, rgba(234,179,8,0.08) 0%, rgba(234,179,8,0.00) 26%), radial-gradient(circle at 52% 82%, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.00) 28%)"
              : "radial-gradient(circle at 22% 18%, rgba(255,255,255,0.22) 0%, rgba(255,255,255,0.00) 24%), radial-gradient(circle at 78% 24%, rgba(184,138,0,0.10) 0%, rgba(184,138,0,0.00) 26%), radial-gradient(circle at 52% 82%, rgba(255,255,255,0.16) 0%, rgba(255,255,255,0.00) 28%)",
          }}
        />

        {/* Top: logo */}
        <div className="relative z-10 pt-12 pl-14">
          <div className="inline-flex flex-col items-center px-4 py-3" style={isDark ? { background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)", borderRadius: "1.75rem", boxShadow: "0 18px 60px rgba(15,23,42,0.12)" } : undefined}>
            <Image
              src={authMascotSrc}
              alt="Mascota TukiJuris"
              width={220}
              height={220}
              className="w-36 h-auto object-contain"
              priority
            />
            <div className={`mt-2 font-['Newsreader'] text-[2rem] leading-none tracking-[-0.05em] font-bold ${isDark ? "text-primary" : "text-[#1B2A4A]"}`}>
              TukiJuris
            </div>
            <div className={`mt-1 text-[0.6rem] uppercase tracking-[0.42em] ${isDark ? "text-on-surface/55" : "text-[#51627E]"}`}>
              Abogados
            </div>
          </div>
        </div>

        {/* Center: headline */}
        <div className="relative z-10 px-14 flex flex-col gap-6">
          <h1 className={`font-['Newsreader'] text-5xl leading-tight ${isDark ? "text-white" : "text-[#0F172A]"}`}>
            Únete a la plataforma<br />
            <span className={isDark ? "text-primary" : "text-[#A67C00]"}>jurídica del futuro</span>
          </h1>
          <p className={`text-base max-w-sm leading-relaxed ${isDark ? "text-[#7a9cc4]" : "text-[#52627A]"}`}>
            Inteligencia artificial entrenada en derecho peruano. Automatiza contratos, analiza jurisprudencia y potencia tu práctica legal.
          </p>

          {/* Trust badges */}
          <div className="flex gap-8 mt-4">
            {[
              { value: "3 meses", label: "gratis" },
              { value: "Sin", label: "tarjeta" },
              { value: "100%", label: "seguro" },
            ].map(({ value, label }) => (
              <div key={label} className="flex flex-col">
                <span className={`font-bold text-sm uppercase tracking-widest ${isDark ? "text-primary" : "text-[#A67C00]"}`}>{value}</span>
                <span className={`text-xs uppercase tracking-wider mt-0.5 ${isDark ? "text-[#7a9cc4]" : "text-[#52627A]"}`}>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom: latin quote */}
        <div className="relative z-10 pb-12 px-14">
          <div className={`border-t pt-8 ${isDark ? "border-[rgba(79,70,51,0.15)]" : "border-[rgba(148,163,184,0.45)]"}`}>
            <p className={`font-['Newsreader'] italic text-sm leading-relaxed ${isDark ? "text-[#7a9cc4]/70" : "text-[#64748B]"}`}>
              &ldquo;Lex est ratio summa, insita in natura, quae iubet ea quae facienda sunt.&rdquo;
            </p>
            <p className={`text-xs uppercase tracking-widest mt-2 ${isDark ? "text-primary/50" : "text-[#8A6A00]"}`}>— Cicerón, De Legibus</p>
          </div>
        </div>
      </div>

      {/* ── MOBILE HEADER ── */}
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
        <p className={`text-sm text-center font-['Newsreader'] italic ${isDark ? "text-[#7a9cc4]" : "text-[#334155]"}`}>
          Crea tu cuenta en TukiJuris
        </p>
      </div>

      {/* ── RIGHT COLUMN — Form (45%) ── */}
      <div className="flex-1 md:w-[45%] bg-background min-h-screen flex flex-col justify-center px-6 md:px-14">
        <div className="w-full max-w-[420px] mx-auto py-10 md:py-0">

          <div className="rounded-[1.75rem] p-8 md:p-10" style={formShellStyle}>

          {/* Title */}
          <div className="mb-8">
            <h2 className={`font-['Newsreader'] text-4xl mb-2 ${isDark ? "text-white" : "text-[#A67C00]"}`}>
              Crear cuenta
            </h2>
            <p className={`text-sm ${subtleTextClass}`}>
              Comienza gratis y transformá tu práctica legal
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-start gap-3 bg-[#F87171]/10 border border-[#F87171]/20 rounded-lg p-4 text-[#F87171] text-sm mb-6">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form
            onSubmit={handleSubmit}
            aria-label="Formulario de registro"
            className="space-y-5"
          >
            {/* Name */}
            <div>
              <label
                htmlFor="register-name"
                className={`block text-xs uppercase tracking-widest ml-1 mb-2 ${labelTextClass}`}
              >
                Nombre completo
              </label>
              <div className="relative">
                <User className={`absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none ${isDark ? "text-on-surface-variant/40" : "text-[#64748B]"}`} />
                <input
                  id="register-name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className={inputClassName}
                  placeholder="Tu nombre"
                  autoComplete="name"
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label
                htmlFor="register-email"
                className={`block text-xs uppercase tracking-widest ml-1 mb-2 ${labelTextClass}`}
              >
                Correo electrónico
              </label>
              <div className="relative">
                <Mail className={`absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none ${isDark ? "text-on-surface-variant/40" : "text-[#64748B]"}`} />
                <input
                  id="register-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={inputClassName}
                  placeholder="tu@email.com"
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="register-password"
                className={`block text-xs uppercase tracking-widest ml-1 mb-2 ${labelTextClass}`}
              >
                Contraseña
              </label>
              <div className="relative">
                <Lock className={`absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none ${isDark ? "text-on-surface-variant/40" : "text-[#64748B]"}`} />
                <input
                  id="register-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`${inputClassName} pr-12`}
                  placeholder="Mín. 8 caracteres"
                  required
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className={`absolute right-3.5 top-1/2 -translate-y-1/2 transition-colors duration-200 p-1 ${isDark ? "text-on-surface-variant/40 hover:text-on-surface-variant/80" : "text-[#64748B] hover:text-[#0F172A]"}`}
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {/* Password rules */}
              {password.length > 0 && (
                <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5">
                  {PASSWORD_RULES.map((rule) => {
                    const passes = rule.test(password);
                    return (
                      <div
                        key={rule.label}
                        className="flex items-center gap-2 transition-colors duration-200"
                      >
                        {passes ? (
                          <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-[#4ade80]" />
                        ) : (
                          <Circle className="w-3.5 h-3.5 shrink-0 text-on-surface/20" />
                        )}
                        <span
                          className={`text-[11px] uppercase tracking-wider ${
                            passes ? "text-[#4ade80]" : isDark ? "text-on-surface/60" : "text-[#64748B]"
                          }`}
                        >
                          {rule.label}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Terms */}
            <label className="flex items-start gap-3 mt-1 cursor-pointer group">
              <div className="relative mt-0.5">
                <input
                  type="checkbox"
                  checked={termsAccepted}
                  onChange={(e) => setTermsAccepted(e.target.checked)}
                  className={`peer appearance-none w-4 h-4 rounded transition-all cursor-pointer focus:outline-none ${isDark ? "border border-[rgba(79,70,51,0.4)] bg-[#35343a] checked:bg-primary checked:border-primary focus:ring-1 focus:ring-primary/20" : "border border-[#CBD5E1] bg-[#F8FAFC] checked:bg-[#B88A00] checked:border-[#B88A00] focus:ring-2 focus:ring-[#E8C24A]/20"}`}
                />
                <svg
                  className="absolute top-0.5 left-0.5 w-3 h-3 text-on-primary opacity-0 peer-checked:opacity-100 pointer-events-none"
                  viewBox="0 0 12 12"
                  fill="none"
                >
                  <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <span className={`text-sm leading-relaxed ${isDark ? "text-on-surface-variant/70" : "text-[#475569]"}`}>
                Acepto los{" "}
                <a
                  href="/terminos"
                  className={`font-bold uppercase tracking-widest transition-colors duration-200 text-xs ${isDark ? "text-primary hover:text-[#ffdf9a]" : "text-[#A67C00] hover:text-[#8A6A00]"}`}
                >
                  Términos
                </a>{" "}
                y la{" "}
                <a
                  href="/privacidad"
                  className={`font-bold uppercase tracking-widest transition-colors duration-200 text-xs ${isDark ? "text-primary hover:text-[#ffdf9a]" : "text-[#A67C00] hover:text-[#8A6A00]"}`}
                >
                  Privacidad
                </a>
              </span>
            </label>

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitDisabled}
              className={`w-full h-[50px] text-on-primary font-bold rounded-lg uppercase tracking-widest text-sm flex items-center justify-center gap-2 transition-all duration-200 hover:brightness-105 disabled:opacity-40 disabled:cursor-not-allowed mt-2 ${isDark ? "bg-gradient-to-br from-primary to-primary-container shadow-lg shadow-primary/10 hover:shadow-primary/20" : "bg-gradient-to-br from-[#B88A00] to-[#E8C24A] shadow-lg shadow-[#E8C24A]/10 hover:shadow-[#E8C24A]/20"}`}
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              {loading ? "Creando cuenta..." : "Crear Cuenta Gratis"}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-4 my-7">
            <div className={`flex-1 h-px ${dividerClass}`} />
            <span className={`text-xs uppercase tracking-widest ${isDark ? "text-on-surface-variant/40" : "text-[#64748B]"}`}>o registrarse con</span>
            <div className={`flex-1 h-px ${dividerClass}`} />
          </div>

          {/* SSO buttons */}
          <div className="grid grid-cols-2 gap-3">
            {/* Google */}
            <button
              type="button"
              onClick={handleGoogleSSO}
              disabled={ssoLoading !== null}
              aria-label="Registrarse con Google"
              className={`h-[46px] border rounded-lg transition-all duration-200 flex items-center justify-center gap-2.5 text-sm disabled:opacity-50 disabled:cursor-not-allowed ${isDark ? "bg-transparent border-[rgba(79,70,51,0.3)] hover:border-primary/40 hover:bg-primary/5 text-on-surface-variant" : "bg-white border-[#D7DEE8] hover:border-[#B88A00]/40 text-[#334155]"}`}
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
              onClick={handleMicrosoftSSO}
              disabled={ssoLoading !== null}
              aria-label="Registrarse con Microsoft"
              className={`h-[46px] border rounded-lg transition-all duration-200 flex items-center justify-center gap-2.5 text-sm disabled:opacity-50 disabled:cursor-not-allowed ${isDark ? "bg-transparent border-[rgba(79,70,51,0.3)] hover:border-primary/40 hover:bg-primary/5 text-on-surface-variant" : "bg-white border-[#D7DEE8] hover:border-[#B88A00]/40 text-[#334155]"}`}
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

          {/* Login link */}
          <p className={`text-center text-sm mt-8 ${isDark ? "text-on-surface-variant/50" : "text-[#64748B]"}`}>
            ¿Ya tenés cuenta?{" "}
            <Link
              href="/auth/login"
              className={`font-bold uppercase tracking-widest transition-colors duration-200 text-xs ${isDark ? "text-primary hover:text-[#ffdf9a]" : "text-[#A67C00] hover:text-[#8A6A00]"}`}
            >
              Iniciar sesión
            </Link>
          </p>
          </div>
        </div>
      </div>
    </main>
  );
}
