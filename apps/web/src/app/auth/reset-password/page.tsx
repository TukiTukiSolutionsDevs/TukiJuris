"use client";

import { Suspense, useEffect, useState } from "react";
import {
  Circle, CheckCircle2, Loader2, XCircle, KeyRound, Eye, EyeOff, Lock, AlertCircle,
} from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth/AuthContext";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const RULES = [
  { label: "Mínimo 8 caracteres", test: (pw: string) => pw.length >= 8 },
  { label: "Al menos una mayúscula", test: (pw: string) => /[A-Z]/.test(pw) },
  { label: "Al menos una minúscula", test: (pw: string) => /[a-z]/.test(pw) },
  { label: "Al menos un número", test: (pw: string) => /[0-9]/.test(pw) },
];

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

  const { user, isLoading } = useAuth();
  useEffect(() => {
    if (!isLoading && user) router.push("/");
  }, [isLoading, user, router]);

  const allRulesPassed = RULES.every((r) => r.test(newPassword));
  const passwordsMatch = newPassword.length > 0 && newPassword === confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!allRulesPassed) { setError("La contraseña no cumple los requisitos."); return; }
    if (!passwordsMatch) { setError("Las contraseñas no coinciden."); return; }
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/auth/password-reset/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: newPassword }),
      });
      if (!res.ok) {
        if (res.status === 400) { setStatus("invalid_token"); return; }
        const data = await res.json().catch(() => null);
        setError(data?.detail ?? "Error al restablecer. Intentá de nuevo.");
        return;
      }
      setStatus("success");
    } catch { setError("No se pudo conectar con el servidor."); } finally { setLoading(false); }
  };

  // ── Success ──
  if (status === "success") {
    return (
      <div className="w-full max-w-[420px]">
        <div className="text-center mb-10">
          <Image src="/brand/logo-icon.png" alt="TukiJuris" width={56} height={56} className="w-14 mx-auto mb-4 object-contain" />
          <span className="font-headline text-xl font-bold text-primary">TukiJuris</span>
        </div>
        <div className="panel-raised rounded-xl p-8">
          <div className="text-center space-y-5">
            <div className="w-16 h-16 bg-[#4ade80]/10 border border-[#4ade80]/20 rounded-xl flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-8 h-8 text-[#4ade80]" />
            </div>
            <div>
              <h2 className="font-headline text-2xl text-on-surface mb-1.5">¡Contraseña actualizada!</h2>
              <p className="text-on-surface-variant/60 text-sm leading-relaxed">
                Tu contraseña fue actualizada correctamente. Ya podés iniciar sesión.
              </p>
            </div>
            <Link href="/auth/login" className="inline-flex items-center justify-center w-full h-12 gold-gradient text-on-primary font-bold rounded-lg uppercase tracking-widest text-sm transition-all hover:opacity-90 hover:shadow-lg hover:shadow-primary/20 mt-2">
              Iniciar sesión
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // ── Invalid token ──
  if (status === "invalid_token") {
    return (
      <div className="w-full max-w-[420px]">
        <div className="text-center mb-10">
          <Image src="/brand/logo-icon.png" alt="TukiJuris" width={56} height={56} className="w-14 mx-auto mb-4 object-contain" />
          <span className="font-headline text-xl font-bold text-primary">TukiJuris</span>
        </div>
        <div className="panel-raised rounded-xl p-8">
          <div className="text-center space-y-5">
            <div className="w-16 h-16 bg-error/10 border border-error/20 rounded-xl flex items-center justify-center mx-auto">
              <XCircle className="w-8 h-8 text-error" />
            </div>
            <div>
              <h2 className="font-headline text-2xl text-on-surface mb-1.5">Enlace inválido o expirado</h2>
              <p className="text-on-surface-variant/60 text-sm leading-relaxed">
                Este enlace ya fue usado o expiró. Los enlaces de recuperación son válidos por 15 minutos.
              </p>
            </div>
            <Link href="/auth/login" className="inline-flex items-center justify-center w-full h-12 gold-gradient text-on-primary font-bold rounded-lg uppercase tracking-widest text-sm transition-all hover:opacity-90 hover:shadow-lg hover:shadow-primary/20 mt-2">
              Solicitar nuevo enlace
            </Link>
          </div>
        </div>
        <p className="text-center mt-6 text-sm">
          <Link href="/auth/login" className="text-primary font-bold uppercase tracking-widest hover:text-primary/80 transition-colors text-xs">
            Volver al inicio de sesión
          </Link>
        </p>
      </div>
    );
  }

  // ── Main form ──
  return (
    <div className="w-full max-w-[420px]">
      <div className="text-center mb-10">
        <Image src="/brand/logo-icon.png" alt="TukiJuris" width={56} height={56} className="w-14 mx-auto mb-4 object-contain" />
        <span className="font-headline text-xl font-bold text-primary">TukiJuris</span>
      </div>

      <div className="panel-raised rounded-xl p-8">
        <div className="flex flex-col items-center mb-7">
          <div className="w-14 h-14 bg-primary/10 border border-primary/20 rounded-xl flex items-center justify-center mb-5 icon-glow">
            <KeyRound className="w-6 h-6 text-primary" />
          </div>
          <h1 className="font-headline text-3xl text-on-surface text-center mb-2">Restablecer contraseña</h1>
          <p className="text-on-surface-variant/60 text-sm text-center">Ingresá tu nueva contraseña segura</p>
        </div>

        <form onSubmit={handleSubmit} aria-label="Nueva contraseña" className="space-y-5">
          {error && (
            <div className="flex items-start gap-3 bg-error-container/10 border border-error/20 rounded-lg p-3.5 text-error text-sm">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" /><span>{error}</span>
            </div>
          )}

          {/* New password */}
          <div>
            <label htmlFor="new-pw" className="block text-xs uppercase tracking-widest text-on-surface-variant/60 ml-1 mb-2">Nueva contraseña</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant/40 pointer-events-none" />
              <input id="new-pw" type={showNewPassword ? "text" : "password"} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="w-full h-12 rounded-lg pl-10 pr-12 text-on-surface placeholder-on-surface/30 text-sm control-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all" placeholder="Mín. 8 caracteres" required minLength={8} />
              <button type="button" onClick={() => setShowNewPassword(!showNewPassword)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-on-surface-variant/40 hover:text-primary transition-colors p-1" aria-label={showNewPassword ? "Ocultar" : "Mostrar"}>
                {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Rules */}
          {newPassword.length > 0 && (
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 px-1">
              {RULES.map((rule) => {
                const ok = rule.test(newPassword);
                return (
                  <div key={rule.label} className="flex items-center gap-2">
                    {ok ? <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-[#4ade80]" /> : <Circle className="w-3.5 h-3.5 shrink-0 text-on-surface/20" />}
                    <span className={`text-[11px] uppercase tracking-wider ${ok ? "text-[#4ade80]" : "text-on-surface-variant/60"}`}>{rule.label}</span>
                  </div>
                );
              })}
            </div>
          )}

          {/* Confirm */}
          <div>
            <label htmlFor="confirm-pw" className="block text-xs uppercase tracking-widest text-on-surface-variant/60 ml-1 mb-2">Confirmar contraseña</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant/40 pointer-events-none" />
              <input id="confirm-pw" type={showConfirmPassword ? "text" : "password"} value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="w-full h-12 rounded-lg pl-10 pr-12 text-on-surface placeholder-on-surface/30 text-sm control-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all" placeholder="Repetí tu contraseña" required />
              <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-on-surface-variant/40 hover:text-primary transition-colors p-1" aria-label={showConfirmPassword ? "Ocultar" : "Mostrar"}>
                {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {confirmPassword.length > 0 && (
              <p className={`mt-2 text-xs uppercase tracking-wider ml-1 ${passwordsMatch ? "text-[#4ade80]" : "text-error"}`}>
                {passwordsMatch ? "Las contraseñas coinciden ✓" : "Las contraseñas no coinciden"}
              </p>
            )}
          </div>

          <button type="submit" disabled={loading} className="w-full h-12 gold-gradient text-on-primary font-bold rounded-lg uppercase tracking-widest text-sm flex items-center justify-center gap-2 transition-all hover:opacity-90 hover:shadow-lg hover:shadow-primary/20 disabled:opacity-40 disabled:cursor-not-allowed mt-2">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <KeyRound className="w-4 h-4" />}
            {loading ? "Guardando..." : "Restablecer contraseña"}
          </button>
        </form>
      </div>

      <p className="text-center mt-6 text-sm">
        <Link href="/auth/login" className="text-primary font-bold uppercase tracking-widest hover:text-primary/80 transition-colors text-xs">
          Volver al inicio de sesión
        </Link>
      </p>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <main className="bg-background min-h-screen flex items-center justify-center px-4 py-12 font-body">
      <Suspense fallback={<div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>}>
        <ResetPasswordForm />
      </Suspense>
    </main>
  );
}
