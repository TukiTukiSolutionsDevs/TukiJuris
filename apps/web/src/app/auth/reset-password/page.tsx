"use client";

import { Suspense, useEffect, useState } from "react";
import {
  Circle,
  CheckCircle2,
  Loader2,
  XCircle,
  KeyRound,
  Eye,
  EyeOff,
  Lock,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { getToken } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Password rule hints
// ---------------------------------------------------------------------------

interface Rule {
  label: string;
  test: (pw: string) => boolean;
}

const RULES: Rule[] = [
  { label: "Mínimo 8 caracteres", test: (pw) => pw.length >= 8 },
  { label: "Al menos una mayúscula", test: (pw) => /[A-Z]/.test(pw) },
  { label: "Al menos una minúscula", test: (pw) => /[a-z]/.test(pw) },
  { label: "Al menos un número", test: (pw) => /[0-9]/.test(pw) },
];

// ---------------------------------------------------------------------------
// Inner component (needs useSearchParams — must be inside Suspense)
// ---------------------------------------------------------------------------

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<"idle" | "success" | "invalid_token">("idle");

  useEffect(() => {
    const t = getToken();
    if (t) {
      router.push("/");
    }
  }, []);

  const allRulesPassed = RULES.every((r) => r.test(newPassword));
  const passwordsMatch = newPassword.length > 0 && newPassword === confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!allRulesPassed) {
      setError("La contraseña no cumple con los requisitos de seguridad.");
      return;
    }
    if (!passwordsMatch) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/auth/password-reset/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: newPassword }),
      });

      if (!res.ok) {
        if (res.status === 400) {
          setStatus("invalid_token");
          return;
        }
        const data = await res.json().catch(() => null);
        setError(
          data?.detail ?? "Ocurrió un error al restablecer la contraseña. Intentá de nuevo."
        );
        return;
      }

      setStatus("success");
    } catch {
      setError("No se pudo conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  };

  // ── Success screen ──
  if (status === "success") {
    return (
      <div className="w-full max-w-[420px]">
        {/* Logo */}
        <div className="text-center mb-10">
          <img src="/brand/logo-full.png" alt="TukiJuris" className="w-36 mx-auto mb-6 object-contain" />
        </div>

        {/* Card */}
        <div className="bg-surface-container border border-[rgba(79,70,51,0.1)] rounded-lg shadow-[0_32px_64px_-12px_rgba(0,0,0,0.5)] p-8">
          <div className="text-center space-y-5">
            {/* Green check icon */}
            <div className="w-16 h-16 bg-[#4ade80]/10 border border-[#4ade80]/20 rounded-lg flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-8 h-8 text-[#4ade80]" />
            </div>

            <div>
              <h2 className="font-['Newsreader'] text-2xl text-white mb-1.5">
                ¡Contraseña actualizada!
              </h2>
              <p className="text-on-surface-variant/60 text-sm leading-relaxed">
                Tu contraseña fue actualizada correctamente. Ya podés iniciar sesión.
              </p>
            </div>

            <Link
              href="/auth/login"
              className="inline-flex items-center justify-center w-full h-[50px] bg-gradient-to-br from-primary to-primary-container text-on-primary font-bold rounded-lg shadow-lg shadow-primary/10 uppercase tracking-widest text-sm transition-all hover:brightness-105 mt-2"
            >
              Iniciar sesión
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // ── Invalid / expired token screen ──
  if (status === "invalid_token") {
    return (
      <div className="w-full max-w-[420px]">
        {/* Logo */}
        <div className="text-center mb-10">
          <img src="/brand/logo-full.png" alt="TukiJuris" className="w-36 mx-auto mb-6 object-contain" />
        </div>

        {/* Card */}
        <div className="bg-surface-container border border-[rgba(79,70,51,0.1)] rounded-lg shadow-[0_32px_64px_-12px_rgba(0,0,0,0.5)] p-8">
          <div className="text-center space-y-5">
            {/* Red X icon */}
            <div className="w-16 h-16 bg-[#f87171]/10 border border-[#f87171]/20 rounded-lg flex items-center justify-center mx-auto">
              <XCircle className="w-8 h-8 text-[#f87171]" />
            </div>

            <div>
              <h2 className="font-['Newsreader'] text-2xl text-white mb-1.5">
                Enlace inválido o expirado
              </h2>
              <p className="text-on-surface-variant/60 text-sm leading-relaxed">
                Este enlace ya fue usado o expiró. Los enlaces de recuperación son válidos por 15 minutos.
              </p>
            </div>

            <Link
              href="/auth/login"
              className="inline-flex items-center justify-center w-full h-[50px] bg-gradient-to-br from-primary to-primary-container text-on-primary font-bold rounded-lg shadow-lg shadow-primary/10 uppercase tracking-widest text-sm transition-all hover:brightness-105 mt-2"
            >
              Solicitar nuevo enlace
            </Link>
          </div>
        </div>

        <p className="text-center mt-6 text-sm">
          <Link
            href="/auth/login"
            className="text-primary font-bold uppercase tracking-widest hover:text-[#ffdf9a] transition-colors text-xs"
          >
            Volver al inicio de sesión
          </Link>
        </p>
      </div>
    );
  }

  // ── Main form ──
  return (
    <div className="w-full max-w-[420px]">
      {/* Logo */}
      <div className="text-center mb-10">
        <img src="/brand/logo-full.png" alt="TukiJuris" className="w-36 mx-auto mb-6 object-contain" />
      </div>

      {/* Card */}
      <div className="bg-surface-container border border-[rgba(79,70,51,0.1)] rounded-lg shadow-[0_32px_64px_-12px_rgba(0,0,0,0.5)] p-8">
        {/* Gavel / key icon header */}
        <div className="flex flex-col items-center mb-7">
          <div className="w-14 h-14 bg-primary/10 border border-primary/20 rounded-lg flex items-center justify-center mb-5">
            <KeyRound className="w-6 h-6 text-primary" />
          </div>
          <h1 className="font-['Newsreader'] text-3xl text-white text-center mb-2">
            Restablecer contraseña
          </h1>
          <p className="text-on-surface-variant/60 text-sm text-center">
            Ingresá tu nueva contraseña segura
          </p>
        </div>

        <form onSubmit={handleSubmit} aria-label="Formulario de nueva contraseña" className="space-y-5">
          {/* Error banner */}
          {error && (
            <div className="flex items-start gap-3 bg-[#F87171]/10 border border-[#F87171]/20 rounded-lg p-3.5 text-[#F87171] text-sm">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* New password */}
          <div>
            <label
              htmlFor="new-password"
              className="block text-xs uppercase tracking-widest text-on-surface-variant ml-1 mb-2"
            >
              Nueva contraseña
            </label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant/40 pointer-events-none" />
              <input
                id="new-password"
                type={showNewPassword ? "text" : "password"}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full h-[50px] bg-[#35343a] border border-transparent rounded-lg pl-10 pr-12 text-on-surface placeholder-on-surface/30 text-sm focus:outline-none focus:border-primary/40 focus:ring-1 focus:ring-primary/10 transition-all duration-200"
                placeholder="Mín. 8 caracteres"
                required
                minLength={8}
              />
              <button
                type="button"
                onClick={() => setShowNewPassword(!showNewPassword)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-on-surface-variant/40 hover:text-on-surface-variant/80 transition-colors duration-200 p-1"
                aria-label={showNewPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
              >
                {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Password rules — grid 2 cols */}
          {newPassword.length > 0 && (
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 px-1">
              {RULES.map((rule) => {
                const ok = rule.test(newPassword);
                return (
                  <div key={rule.label} className="flex items-center gap-2 transition-colors duration-200">
                    {ok ? (
                      <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-[#4ade80]" />
                    ) : (
                      <Circle className="w-3.5 h-3.5 shrink-0 text-on-surface/20" />
                    )}
                    <span
                      className={`text-[11px] uppercase tracking-wider ${
                        ok ? "text-[#4ade80]" : "text-on-surface/60"
                      }`}
                    >
                      {rule.label}
                    </span>
                  </div>
                );
              })}
            </div>
          )}

          {/* Confirm password */}
          <div>
            <label
              htmlFor="confirm-password"
              className="block text-xs uppercase tracking-widest text-on-surface-variant ml-1 mb-2"
            >
              Confirmar contraseña
            </label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant/40 pointer-events-none" />
              <input
                id="confirm-password"
                type={showConfirmPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full h-[50px] bg-[#35343a] border border-transparent rounded-lg pl-10 pr-12 text-on-surface placeholder-on-surface/30 text-sm focus:outline-none focus:border-primary/40 focus:ring-1 focus:ring-primary/10 transition-all duration-200"
                placeholder="Repetí tu contraseña"
                required
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-on-surface-variant/40 hover:text-on-surface-variant/80 transition-colors duration-200 p-1"
                aria-label={showConfirmPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
              >
                {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {confirmPassword.length > 0 && (
              <p
                className={`mt-2 text-xs uppercase tracking-wider ml-1 ${
                  passwordsMatch ? "text-[#4ade80]" : "text-[#f87171]"
                }`}
              >
                {passwordsMatch ? "Las contraseñas coinciden ✓" : "Las contraseñas no coinciden"}
              </p>
            )}
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full h-[50px] bg-gradient-to-br from-primary to-primary-container text-on-primary font-bold rounded-lg shadow-lg shadow-primary/10 uppercase tracking-widest text-sm flex items-center justify-center gap-2 transition-all duration-200 hover:brightness-105 hover:shadow-primary/20 disabled:opacity-40 disabled:cursor-not-allowed mt-2"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <KeyRound className="w-4 h-4" />
            )}
            {loading ? "Guardando..." : "Restablecer contraseña"}
          </button>
        </form>
      </div>

      {/* Back to login */}
      <p className="text-center mt-6 text-sm">
        <Link
          href="/auth/login"
          className="text-primary font-bold uppercase tracking-widest hover:text-[#ffdf9a] transition-colors text-xs"
        >
          Volver al inicio de sesión
        </Link>
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page wrapper — Suspense required by Next.js for useSearchParams
// ---------------------------------------------------------------------------

export default function ResetPasswordPage() {
  return (
    <main className="bg-background min-h-screen flex items-center justify-center px-4 py-12">
      <Suspense
        fallback={
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
          </div>
        }
      >
        <ResetPasswordForm />
      </Suspense>
    </main>
  );
}
