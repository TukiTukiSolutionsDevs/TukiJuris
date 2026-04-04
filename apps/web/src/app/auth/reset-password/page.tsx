"use client";

import { Suspense, useEffect, useState } from "react";
import { Circle, CheckCircle2, Loader2, XCircle, KeyRound } from "lucide-react";
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
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<"idle" | "success" | "invalid_token">("idle");

  useEffect(() => {
    const t = getToken();
    if (t) {
      router.push("/");
    }
  }, []);

  // Real-time validation state
  const allRulesPassed = RULES.every((r) => r.test(newPassword));
  const passwordsMatch = newPassword.length > 0 && newPassword === confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Client-side validation
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

  // --- Success screen ---
  if (status === "success") {
    return (
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-10">
          <img src="/brand/logo-full.png" alt="Logo" className="w-40 mx-auto mb-6" />
        </div>

        {/* Card */}
        <div className="bg-[#111116] border border-[#1E1E2A] rounded-2xl p-8">
          <div className="text-center space-y-4">
            <div className="w-14 h-14 bg-green-500/10 border border-green-500/20 rounded-2xl flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-7 h-7 text-green-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-[#F5F5F5]">¡Contraseña actualizada!</h2>
              <p className="text-[#9CA3AF] text-sm mt-1">
                Tu contraseña fue actualizada correctamente.
              </p>
            </div>
            <Link
              href="/auth/login"
              className="inline-flex items-center justify-center w-full h-12 bg-[#EAB308] hover:bg-[#D4A00A] text-[#0A0A0F] font-semibold rounded-xl px-4 transition-colors focus:outline-none focus:ring-2 focus:ring-[#EAB308]/30 mt-2"
            >
              Iniciar sesión
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // --- Invalid / expired token screen ---
  if (status === "invalid_token") {
    return (
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-10">
          <img src="/brand/logo-full.png" alt="Logo" className="w-40 mx-auto mb-6" />
        </div>

        {/* Card */}
        <div className="bg-[#111116] border border-[#1E1E2A] rounded-2xl p-8">
          <div className="text-center space-y-4">
            <div className="w-14 h-14 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center justify-center mx-auto">
              <XCircle className="w-7 h-7 text-red-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-[#F5F5F5]">Enlace inválido o expirado</h2>
              <p className="text-[#9CA3AF] text-sm mt-1">
                Este enlace ya fue usado o expiró. Los enlaces de recuperación son válidos por 15 minutos.
              </p>
            </div>
            <Link
              href="/auth/login"
              className="inline-flex items-center justify-center w-full h-12 bg-[#EAB308] hover:bg-[#D4A00A] text-[#0A0A0F] font-semibold rounded-xl px-4 transition-colors focus:outline-none focus:ring-2 focus:ring-[#EAB308]/30 mt-2"
            >
              Solicitar nuevo enlace
            </Link>
          </div>
        </div>

        {/* Back link */}
        <p className="text-center mt-6 text-sm text-[#9CA3AF]">
          <Link href="/auth/login" className="text-[#EAB308] hover:text-[#D4A00A] transition-colors">
            Volver al inicio de sesión
          </Link>
        </p>
      </div>
    );
  }

  // --- Main form ---
  return (
    <div className="w-full max-w-md">
      {/* Logo */}
      <div className="text-center mb-10">
        <img src="/brand/logo-full.png" alt="Logo" className="w-40 mx-auto mb-6" />
      </div>

      {/* Form card */}
      <div className="bg-[#111116] border border-[#1E1E2A] rounded-2xl p-8">
        <h1 className="text-2xl font-bold text-[#F5F5F5] mb-2">Restablecer Contraseña</h1>
        <p className="text-[#9CA3AF] text-sm mb-8">Ingresa tu nueva contraseña</p>

        <form onSubmit={handleSubmit} aria-label="Formulario de nueva contraseña" className="space-y-5">
          {/* Error banner */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          {/* New password */}
          <div>
            <label htmlFor="new-password" className="block text-sm text-[#9CA3AF] mb-1.5">
              Nueva contraseña
            </label>
            <input
              id="new-password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full h-12 bg-[#0A0A0F] border border-[#2A2A35] rounded-xl px-4 text-sm text-[#F5F5F5] placeholder-[#6B7280] focus:outline-none focus:border-[#EAB308] focus:ring-2 focus:ring-[#EAB308]/20 transition-colors"
              placeholder="Min. 8 caracteres (mayúscula, minúscula, número)"
              required
              minLength={8}
            />
          </div>

          {/* Password strength hints — shown once user starts typing */}
          {newPassword.length > 0 && (
            <ul className="space-y-1.5 px-1">
              {RULES.map((rule) => {
                const ok = rule.test(newPassword);
                return (
                  <li key={rule.label} className="flex items-center gap-2 text-xs">
                    {ok ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-green-400 shrink-0" />
                    ) : (
                      <Circle className="w-3.5 h-3.5 text-[#6B7280] shrink-0" />
                    )}
                    <span className={ok ? "text-green-400" : "text-[#6B7280]"}>{rule.label}</span>
                  </li>
                );
              })}
            </ul>
          )}

          {/* Confirm password */}
          <div>
            <label htmlFor="confirm-password" className="block text-sm text-[#9CA3AF] mb-1.5">
              Confirmar contraseña
            </label>
            <input
              id="confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full h-12 bg-[#0A0A0F] border border-[#2A2A35] rounded-xl px-4 text-sm text-[#F5F5F5] placeholder-[#6B7280] focus:outline-none focus:border-[#EAB308] focus:ring-2 focus:ring-[#EAB308]/20 transition-colors"
              placeholder="Repetí tu contraseña"
              required
            />
            {confirmPassword.length > 0 && (
              <p
                className={`mt-1.5 text-xs ${
                  passwordsMatch ? "text-green-400" : "text-red-400"
                }`}
              >
                {passwordsMatch ? "Las contraseñas coinciden ✓" : "Las contraseñas no coinciden"}
              </p>
            )}
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full h-12 bg-[#EAB308] hover:bg-[#D4A00A] disabled:bg-[#2A2A35] disabled:text-[#6B7280] disabled:cursor-not-allowed text-[#0A0A0F] font-semibold rounded-xl flex items-center justify-center gap-2 transition-all focus:outline-none focus:ring-2 focus:ring-[#EAB308]/30 hover:shadow-lg hover:shadow-[#EAB308]/20"
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
      <p className="text-center mt-6 text-sm text-[#9CA3AF]">
        <Link href="/auth/login" className="text-[#EAB308] hover:text-[#D4A00A] transition-colors">
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
    <main className="bg-[#0A0A0F] min-h-screen flex items-center justify-center px-4">
      <Suspense
        fallback={
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-[#EAB308]" />
          </div>
        }
      >
        <ResetPasswordForm />
      </Suspense>
    </main>
  );
}
