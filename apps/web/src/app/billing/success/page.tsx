"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Clock, AlertTriangle } from "lucide-react";
import Link from "next/link";
import { getToken } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function BillingSuccessInner() {
  const searchParams = useSearchParams();
  const collectionStatus = searchParams.get("collection_status");
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    // Refresh user plan data
    const token = getToken();
    if (token) {
      fetch(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {});
    }
  }, []);

  useEffect(() => {
    if (collectionStatus === "pending") return; // Don't auto-redirect on pending
    const timer = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) {
          window.location.href = "/";
          return 0;
        }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [collectionStatus]);

  const isPending = collectionStatus === "pending";
  const isRejected = collectionStatus === "rejected";

  if (isRejected) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        {/* Ambient glow */}
        <div className="pointer-events-none fixed inset-0 overflow-hidden">
          <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full bg-red-500/5 blur-[120px]" />
        </div>

        <div className="relative w-full max-w-md">
          <div className="bg-[#111116] border border-[rgba(79,70,51,0.15)] rounded-lg px-8 py-10 text-center">
            <div className="w-16 h-16 bg-red-500/10 border border-[rgba(79,70,51,0.15)] rounded-lg flex items-center justify-center mx-auto mb-6">
              <AlertTriangle className="w-8 h-8 text-red-400" />
            </div>
            <h1 className="font-['Newsreader'] text-3xl text-on-surface mb-3">
              Pago rechazado
            </h1>
            <p className="text-on-surface-variant text-sm mb-8 leading-relaxed">
              El pago no pudo ser procesado. Intentá con otro método de pago.
            </p>
            <Link
              href="/billing"
              className="inline-flex items-center justify-center w-full bg-gradient-to-br from-primary to-primary-container text-on-primary font-bold px-6 py-3 rounded-lg transition-opacity hover:opacity-90"
            >
              Volver a planes
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (isPending) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        {/* Ambient glow */}
        <div className="pointer-events-none fixed inset-0 overflow-hidden">
          <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full bg-primary-container/5 blur-[120px]" />
        </div>

        <div className="relative w-full max-w-md">
          <div className="bg-[#111116] border border-[rgba(79,70,51,0.15)] rounded-lg px-8 py-10 text-center">
            <div className="w-16 h-16 bg-primary-container/10 border border-[rgba(79,70,51,0.15)] rounded-lg flex items-center justify-center mx-auto mb-6">
              <Clock className="w-8 h-8 text-primary-container" />
            </div>
            <h1 className="font-['Newsreader'] text-3xl text-on-surface mb-3">
              Pago pendiente
            </h1>
            <p className="text-on-surface-variant text-sm mb-8 leading-relaxed">
              Tu pago está siendo procesado. Te notificaremos por email cuando se confirme.
            </p>
            <Link
              href="/"
              className="inline-flex items-center justify-center w-full bg-gradient-to-br from-primary to-primary-container text-on-primary font-bold px-6 py-3 rounded-lg transition-opacity hover:opacity-90"
            >
              Ir al dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      {/* Ambient glow */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full bg-primary-container/5 blur-[120px]" />
      </div>

      <div className="relative w-full max-w-md">
        <div className="bg-[#111116] border border-[rgba(79,70,51,0.15)] rounded-lg px-8 py-10 text-center">
          {/* Gold check icon */}
          <div className="w-16 h-16 bg-primary-container/10 border border-[rgba(79,70,51,0.15)] rounded-lg flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 className="w-8 h-8 text-primary-container" />
          </div>

          <h1 className="font-['Newsreader'] text-3xl text-on-surface mb-3">
            ¡Pago exitoso!
          </h1>
          <p className="text-on-surface-variant text-sm leading-relaxed mb-2">
            Tu plan fue actualizado correctamente. Ya podés disfrutar de todas las funcionalidades.
          </p>
          <p className="text-[#6B7280] text-xs mb-8">
            Recibirás un email con la confirmación de tu pago.
          </p>

          <Link
            href="/"
            className="inline-flex items-center justify-center w-full bg-gradient-to-br from-primary to-primary-container text-on-primary font-bold px-6 py-3 rounded-lg transition-opacity hover:opacity-90"
          >
            Ir al dashboard
          </Link>

          <p className="text-[#4B5563] text-xs mt-5">
            Redirigiendo en {countdown}s...
          </p>
        </div>
      </div>
    </div>
  );
}

export default function BillingSuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-background">
          <div className="w-5 h-5 border-2 border-primary-container border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <BillingSuccessInner />
    </Suspense>
  );
}
