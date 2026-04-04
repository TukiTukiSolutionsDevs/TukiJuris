"use client";

import { useEffect, useState } from "react";
import {
  Eye,
  EyeOff,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Circle,
} from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { register, getToken } from "@/lib/auth";

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
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [ssoLoading, setSsoLoading] = useState<"google" | "microsoft" | null>(null);
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (token) {
      router.push("/");
    }
  }, []);

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

    // Validate password policy before hitting the API
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
    <main className="min-h-screen flex flex-col md:flex-row">
      {/* ── LEFT COLUMN — Branding (55%) ── */}
      <div className="hidden md:flex md:w-[55%] bg-[#2C3E50] min-h-screen flex-col justify-center items-center px-16 relative overflow-hidden">
        {/* Subtle background texture */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#2C3E50] via-[#263545] to-[#1a2535] pointer-events-none" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#EAB308]/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-[#EAB308]/3 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col items-center text-center max-w-md">
          {/* Logo */}
          <div className="mb-10">
            <Image
              src="/brand/logo-full.png"
              alt="TukiJuris"
              width={256}
              height={96}
              className="w-64 object-contain"
              priority
            />
          </div>

          {/* Tagline */}
          <h1 className="text-2xl font-bold text-white leading-tight">
            Crea tu cuenta
          </h1>

          {/* Subtitle */}
          <p className="text-[#9CA3AF] text-base text-center max-w-md mt-4 leading-relaxed">
            Únete a la plataforma de IA jurídica más avanzada del Perú.
          </p>

          {/* Trust indicators */}
          <div className="mt-16 pt-8 border-t border-[#1E1E2A] w-full">
            <p className="text-sm text-[#9CA3AF]/60 text-center tracking-wide">
              Registro gratuito · Sin tarjeta de crédito · 3 meses gratis
            </p>
          </div>
        </div>
      </div>

      {/* ── MOBILE HEADER (visible only on small screens) ── */}
      <div className="flex md:hidden flex-col items-center pt-10 pb-6 px-6 bg-[#2C3E50]">
        <Image
          src="/brand/logo-full.png"
          alt="TukiJuris"
          width={128}
          height={48}
          className="w-32 object-contain mb-3"
          priority
        />
        <p className="text-sm text-[#9CA3AF] text-center">
          Crea tu cuenta en TukiJuris
        </p>
      </div>

      {/* ── RIGHT COLUMN — Form (45%) ── */}
      <div className="flex-1 md:w-[45%] bg-[#0A0A0F] min-h-screen flex flex-col justify-center px-6 md:px-16">
        <div className="w-full max-w-lg mx-auto py-10 md:py-0">
          {/* Title area */}
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-[#F5F5F5] mb-2">
              Crear Cuenta
            </h2>
            <p className="text-[#9CA3AF]">
              Comienza gratis y transforma tu práctica legal
            </p>
          </div>

          {/* Error display */}
          {error && (
            <div className="flex items-start gap-3 bg-[#F87171]/10 border border-[#F87171]/20 rounded-xl p-4 text-[#F87171] text-sm mb-6">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Register form */}
          <form
            onSubmit={handleSubmit}
            aria-label="Formulario de registro"
            className="space-y-5"
          >
            {/* Name field */}
            <div>
              <label
                htmlFor="register-name"
                className="block text-sm font-medium text-[#9CA3AF] mb-2"
              >
                Nombre completo
              </label>
              <input
                id="register-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full h-12 bg-[#111116] border border-[#2A2A35] rounded-xl px-4 text-[#F5F5F5] placeholder-[#6B7280] focus:outline-none focus:border-[#EAB308] focus:ring-1 focus:ring-[#EAB308]/20 transition-all duration-200"
                placeholder="Tu nombre"
                autoComplete="name"
              />
            </div>

            {/* Email field */}
            <div>
              <label
                htmlFor="register-email"
                className="block text-sm font-medium text-[#9CA3AF] mb-2"
              >
                Correo electrónico
              </label>
              <input
                id="register-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full h-12 bg-[#111116] border border-[#2A2A35] rounded-xl px-4 text-[#F5F5F5] placeholder-[#6B7280] focus:outline-none focus:border-[#EAB308] focus:ring-1 focus:ring-[#EAB308]/20 transition-all duration-200"
                placeholder="tu@email.com"
                required
                autoComplete="email"
              />
            </div>

            {/* Password field */}
            <div>
              <label
                htmlFor="register-password"
                className="block text-sm font-medium text-[#9CA3AF] mb-2"
              >
                Contraseña
              </label>
              <div className="relative">
                <input
                  id="register-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full h-12 bg-[#111116] border border-[#2A2A35] rounded-xl px-4 pr-12 text-[#F5F5F5] placeholder-[#6B7280] focus:outline-none focus:border-[#EAB308] focus:ring-1 focus:ring-[#EAB308]/20 transition-all duration-200"
                  placeholder="Mín. 8 caracteres"
                  required
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6B7280] hover:text-[#9CA3AF] transition-colors duration-200 p-1"
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>

              {/* Password validation hints */}
              {password.length > 0 && (
                <div className="mt-3 space-y-1.5">
                  {PASSWORD_RULES.map((rule) => {
                    const passes = rule.test(password);
                    return (
                      <div
                        key={rule.label}
                        className={`flex items-center gap-2 text-xs transition-colors duration-200 ${
                          passes ? "text-[#34D399]" : "text-[#6B7280]"
                        }`}
                      >
                        {passes ? (
                          <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                        ) : (
                          <Circle className="w-3.5 h-3.5 shrink-0" />
                        )}
                        <span>{rule.label}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Terms checkbox */}
            <label className="flex items-start gap-3 mt-4 cursor-pointer">
              <input
                type="checkbox"
                checked={termsAccepted}
                onChange={(e) => setTermsAccepted(e.target.checked)}
                className="mt-1 rounded border-[#2A2A35] bg-[#111116] text-[#EAB308] focus:ring-[#EAB308] focus:ring-offset-[#0A0A0F]"
              />
              <span className="text-sm text-[#9CA3AF] leading-relaxed">
                Acepto los{" "}
                <a
                  href="/terminos"
                  className="text-[#EAB308] hover:text-[#D4A00A] transition-colors duration-200"
                >
                  Términos de Servicio
                </a>{" "}
                y la{" "}
                <a
                  href="/privacidad"
                  className="text-[#EAB308] hover:text-[#D4A00A] transition-colors duration-200"
                >
                  Política de Privacidad
                </a>
              </span>
            </label>

            {/* Submit button */}
            <button
              type="submit"
              disabled={isSubmitDisabled}
              className="w-full h-12 bg-[#EAB308] hover:bg-[#D4A00A] text-[#0A0A0F] font-semibold rounded-xl flex items-center justify-center gap-2 transition-all duration-200 hover:shadow-lg hover:shadow-[#EAB308]/20 disabled:opacity-50 disabled:cursor-not-allowed mt-6"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : null}
              {loading ? "Creando cuenta..." : "Crear Cuenta Gratis"}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-4 my-8">
            <div className="flex-1 h-px bg-[#1E1E2A]" />
            <span className="text-sm text-[#6B7280]">o registrarse con</span>
            <div className="flex-1 h-px bg-[#1E1E2A]" />
          </div>

          {/* OAuth buttons */}
          <div className="grid grid-cols-2 gap-4">
            {/* Google */}
            <button
              type="button"
              onClick={handleGoogleSSO}
              disabled={ssoLoading !== null}
              aria-label="Registrarse con Google"
              className="h-12 bg-[#111116] border border-[#2A2A35] rounded-xl hover:border-[#EAB308]/50 transition-all duration-200 flex items-center justify-center gap-3 text-[#F5F5F5] text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
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
              onClick={handleMicrosoftSSO}
              disabled={ssoLoading !== null}
              aria-label="Registrarse con Microsoft"
              className="h-12 bg-[#111116] border border-[#2A2A35] rounded-xl hover:border-[#EAB308]/50 transition-all duration-200 flex items-center justify-center gap-3 text-[#F5F5F5] text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
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
          <p className="text-center text-[#9CA3AF] text-sm mt-8">
            ¿Ya tienes cuenta?{" "}
            <Link
              href="/auth/login"
              className="text-[#EAB308] hover:text-[#D4A00A] font-medium transition-colors duration-200"
            >
              Inicia sesión
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
