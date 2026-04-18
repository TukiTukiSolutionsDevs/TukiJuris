"use client";

import { useEffect, useState } from "react";
import {
  Eye, EyeOff, Loader2, AlertCircle, CheckCircle2, Circle, Mail, User, Lock,
} from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { register, getToken } from "@/lib/auth";
import { useTheme } from "@/components/ThemeProvider";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const passwordRegex = /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{8,}$/;

const PASSWORD_RULES = [
  { label: "Mínimo 8 caracteres", test: (p: string) => p.length >= 8 },
  { label: "Una mayúscula", test: (p: string) => /[A-Z]/.test(p) },
  { label: "Una minúscula", test: (p: string) => /[a-z]/.test(p) },
  { label: "Un número", test: (p: string) => /\d/.test(p) },
];

export default function RegisterPage() {
  const { theme } = useTheme();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [ssoLoading, setSsoLoading] = useState<"google" | "microsoft" | null>(null);
  const router = useRouter();

  useEffect(() => { if (getToken()) router.push("/"); }, [router]);

  const handleSSO = async (provider: "google" | "microsoft") => {
    setError(""); setSsoLoading(provider);
    try {
      const res = await fetch(`${API_URL}/api/auth/oauth/${provider}/authorize`);
      if (!res.ok) { const d = await res.json().catch(() => ({})); setError(d.detail ?? `Error SSO ${provider}`); return; }
      window.location.href = (await res.json()).url;
    } catch { setError("No se pudo conectar con el servidor."); } finally { setSsoLoading(null); }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(""); setLoading(true);
    if (!passwordRegex.test(password)) { setError("La contraseña no cumple los requisitos"); setLoading(false); return; }
    try { await register(email, password, name || undefined); router.push("/onboarding"); }
    catch (err) { setError(err instanceof Error ? err.message : "Error al registrar"); }
    finally { setLoading(false); }
  };

  const isPasswordValid = passwordRegex.test(password);
  const isSubmitDisabled = loading || !email || !password || !termsAccepted || !isPasswordValid;

  return (
    <main className="min-h-screen flex flex-col md:flex-row bg-background font-body">
      {/* ── LEFT — Branding (desktop) ── */}
      <div className="hidden md:flex md:w-1/2 min-h-screen flex-col justify-between relative overflow-hidden bg-secondary-container/20">
        <div className="absolute top-16 right-16 w-80 h-80 rounded-full blur-3xl pointer-events-none bg-primary/5" />
        <div className="absolute bottom-24 left-12 w-56 h-56 rounded-full blur-3xl pointer-events-none bg-secondary/5" />

        <div className="relative z-10 pt-12 pl-14">
          <div className="inline-flex flex-col items-center px-4 py-3">
            <Image src="/brand/tukan.png" alt="TukiJuris" width={220} height={220} className="w-36 h-auto object-contain" priority />
            <div className="mt-2 font-headline text-[2rem] leading-none tracking-[-0.05em] font-bold text-primary">TukiJuris</div>
            <div className="mt-1 text-[0.6rem] uppercase tracking-[0.42em] text-on-surface-variant/55">Abogados</div>
          </div>
        </div>

        <div className="relative z-10 px-14 flex flex-col gap-6">
          <h1 className="font-headline text-4xl xl:text-5xl leading-tight text-on-surface">
            Únete a la plataforma<br /><span className="text-primary">jurídica del futuro</span>
          </h1>
          <p className="text-base max-w-sm leading-relaxed text-on-surface-variant/60">
            Inteligencia artificial entrenada en derecho peruano. Consulta normativa, jurisprudencia y potencia tu práctica legal.
          </p>
          <div className="flex gap-8 mt-4">
            {[{ value: "Gratis", label: "para empezar" }, { value: "Sin", label: "tarjeta" }, { value: "100%", label: "seguro" }].map(({ value, label }) => (
              <div key={label} className="flex flex-col">
                <span className="font-bold text-sm uppercase tracking-widest text-primary">{value}</span>
                <span className="text-xs uppercase tracking-wider mt-0.5 text-on-surface-variant/50">{label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10 pb-12 px-14">
          <div className="border-t border-ghost-border pt-8">
            <p className="text-xs uppercase tracking-widest text-primary/50">Precisión · Autoridad · Eficiencia</p>
          </div>
        </div>
      </div>

      {/* ── MOBILE HEADER (compact) ── */}
      <div className="flex md:hidden items-center gap-3 pt-8 pb-4 px-6 bg-background">
        <Image src="/brand/logo-icon.png" alt="TukiJuris" width={40} height={40} className="w-10 h-10 object-contain" priority />
        <div>
          <div className="font-headline text-xl leading-none font-bold text-primary">TukiJuris</div>
          <div className="text-[0.6rem] uppercase tracking-[0.3em] text-on-surface-variant/50">Crea tu cuenta gratis</div>
        </div>
      </div>

      {/* ── RIGHT — Form ── */}
      <div className="flex-1 md:w-1/2 bg-background min-h-0 md:min-h-screen flex flex-col justify-center px-4 sm:px-6 md:px-14">
        <div className="w-full max-w-[440px] mx-auto py-6 md:py-0">
          <div className="rounded-xl p-6 sm:p-8 md:p-10 panel-raised">
            <div className="mb-7">
              <h2 className="font-headline text-3xl sm:text-4xl text-primary mb-2">Crear cuenta</h2>
              <p className="text-sm text-on-surface-variant/50">Comienza gratis y transformá tu práctica legal</p>
            </div>

            {error && (
              <div className="flex items-start gap-3 bg-error-container/10 border border-error/20 rounded-lg p-4 text-error text-sm mb-6">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" /><span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} aria-label="Registro" className="space-y-5">
              {/* Name */}
              <div>
                <label htmlFor="r-name" className="block text-xs uppercase tracking-widest ml-1 mb-2 text-on-surface-variant/60">Nombre completo</label>
                <div className="relative">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none text-on-surface-variant/40" />
                  <input id="r-name" type="text" value={name} onChange={(e) => setName(e.target.value)} className="w-full h-12 rounded-lg pl-10 pr-4 text-sm text-on-surface placeholder-on-surface/30 control-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all" placeholder="Tu nombre" autoComplete="name" />
                </div>
              </div>

              {/* Email */}
              <div>
                <label htmlFor="r-email" className="block text-xs uppercase tracking-widest ml-1 mb-2 text-on-surface-variant/60">Correo electrónico</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none text-on-surface-variant/40" />
                  <input id="r-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full h-12 rounded-lg pl-10 pr-4 text-sm text-on-surface placeholder-on-surface/30 control-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all" placeholder="tu@email.com" required autoComplete="email" />
                </div>
              </div>

              {/* Password */}
              <div>
                <label htmlFor="r-pw" className="block text-xs uppercase tracking-widest ml-1 mb-2 text-on-surface-variant/60">Contraseña</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none text-on-surface-variant/40" />
                  <input id="r-pw" type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} className="w-full h-12 rounded-lg pl-10 pr-12 text-sm text-on-surface placeholder-on-surface/30 control-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all" placeholder="Mín. 8 caracteres" required autoComplete="new-password" />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3.5 top-1/2 -translate-y-1/2 p-1 text-on-surface-variant/40 hover:text-primary transition-colors" aria-label={showPassword ? "Ocultar" : "Mostrar"}>
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {password.length > 0 && (
                  <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1.5">
                    {PASSWORD_RULES.map((rule) => {
                      const ok = rule.test(password);
                      return (
                        <div key={rule.label} className="flex items-center gap-2">
                          {ok ? <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-[#4ade80]" /> : <Circle className="w-3.5 h-3.5 shrink-0 text-on-surface/20" />}
                          <span className={`text-[11px] uppercase tracking-wider ${ok ? "text-[#4ade80]" : "text-on-surface-variant/60"}`}>{rule.label}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Terms — FIXED links */}
              <label className="flex items-start gap-3 mt-1 cursor-pointer">
                <div className="relative mt-0.5">
                  <input type="checkbox" checked={termsAccepted} onChange={(e) => setTermsAccepted(e.target.checked)} className="peer appearance-none w-4 h-4 rounded border border-outline-variant bg-surface-container transition-all cursor-pointer checked:bg-primary checked:border-primary focus:outline-none focus:ring-1 focus:ring-primary/20" />
                  <svg className="absolute top-0.5 left-0.5 w-3 h-3 text-on-primary opacity-0 peer-checked:opacity-100 pointer-events-none" viewBox="0 0 12 12" fill="none"><path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
                </div>
                <span className="text-sm leading-relaxed text-on-surface-variant/70">
                  Acepto los <Link href="/terms" className="font-bold uppercase tracking-widest text-xs text-primary hover:text-primary/80 transition-colors">Términos</Link> y la <Link href="/privacy" className="font-bold uppercase tracking-widest text-xs text-primary hover:text-primary/80 transition-colors">Privacidad</Link>
                </span>
              </label>

              <button type="submit" disabled={isSubmitDisabled} className="w-full h-12 text-on-primary font-bold rounded-lg uppercase tracking-widest text-sm flex items-center justify-center gap-2 transition-all hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed mt-2 gold-gradient hover:shadow-lg hover:shadow-primary/20">
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                {loading ? "Creando cuenta..." : "Crear Cuenta Gratis"}
              </button>
            </form>

            {/* Divider */}
            <div className="flex items-center gap-4 my-7">
              <div className="flex-1 h-px bg-ghost-border" />
              <span className="text-xs uppercase tracking-widest text-on-surface-variant/40">o registrarse con</span>
              <div className="flex-1 h-px bg-ghost-border" />
            </div>

            {/* SSO */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button type="button" onClick={() => handleSSO("google")} disabled={ssoLoading !== null} className="h-12 rounded-lg flex items-center justify-center gap-2.5 text-sm disabled:opacity-50 control-surface hover:border-primary/30 text-on-surface-variant transition-all">
                {ssoLoading === "google" ? <Loader2 className="w-4 h-4 animate-spin" /> : <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.07 5.07 0 01-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09a6.96 6.96 0 010-4.18V7.07H2.18A11.99 11.99 0 001 12c0 1.78.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>}
                Google
              </button>
              <button type="button" onClick={() => handleSSO("microsoft")} disabled={ssoLoading !== null} className="h-12 rounded-lg flex items-center justify-center gap-2.5 text-sm disabled:opacity-50 control-surface hover:border-primary/30 text-on-surface-variant transition-all">
                {ssoLoading === "microsoft" ? <Loader2 className="w-4 h-4 animate-spin" /> : <svg className="w-4 h-4 shrink-0" viewBox="0 0 23 23"><rect x="1" y="1" width="10" height="10" fill="#F25022"/><rect x="12" y="1" width="10" height="10" fill="#7FBA00"/><rect x="1" y="12" width="10" height="10" fill="#00A4EF"/><rect x="12" y="12" width="10" height="10" fill="#FFB900"/></svg>}
                Microsoft
              </button>
            </div>

            <p className="text-center text-sm mt-8 text-on-surface-variant/50">
              ¿Ya tenés cuenta? <Link href="/auth/login" className="font-bold uppercase tracking-widest text-xs text-primary hover:text-primary/80 transition-colors">Iniciar sesión</Link>
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
