"use client";

import { AlertTriangle } from "lucide-react";
import Link from "next/link";

export default function BillingCancelPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      {/* Ambient glow */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full bg-primary-container/5 blur-[120px]" />
      </div>

      <div className="relative w-full max-w-md">
        <div className="bg-[#111116] border border-[rgba(79,70,51,0.15)] rounded-lg px-8 py-10 text-center">
          {/* Amber warning icon */}
          <div className="w-16 h-16 bg-primary-container/10 border border-[rgba(79,70,51,0.15)] rounded-lg flex items-center justify-center mx-auto mb-6">
            <AlertTriangle className="w-8 h-8 text-primary-container" />
          </div>

          <h1 className="font-['Newsreader'] text-3xl text-on-surface mb-3">
            Pago no completado
          </h1>
          <p className="text-on-surface-variant text-sm leading-relaxed mb-8">
            El proceso de pago fue cancelado o no se completó. No se realizó
            ningún cargo.
          </p>

          {/* Primary CTA — ghost style */}
          <Link
            href="/billing"
            className="inline-flex items-center justify-center w-full border border-[rgba(79,70,51,0.15)] text-on-surface font-medium px-6 py-3 rounded-lg hover:border-[rgba(79,70,51,0.35)] hover:bg-surface-container-low transition-colors"
          >
            Volver a planes
          </Link>

          {/* Support link */}
          <p className="text-[#4B5563] text-xs mt-6">
            ¿Necesitás ayuda?{" "}
            <a
              href="mailto:soporte@tukijuris.net.pe"
              className="text-primary-container/70 hover:text-primary-container transition-colors"
            >
              soporte@tukijuris.net.pe
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
