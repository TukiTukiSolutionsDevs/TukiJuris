"use client";

import { AlertTriangle } from "lucide-react";
import Link from "next/link";

export default function BillingCancelPage() {
  return (
    <main className="min-h-screen flex items-start sm:items-center justify-center bg-[#0A0A0F] px-4 pt-12 sm:pt-0">
      <div className="w-full max-w-sm pb-8">
        <div className="text-center space-y-4">
          {/* Icon */}
          <div className="w-14 h-14 bg-amber-500/20 border border-amber-500/30 rounded-2xl flex items-center justify-center mx-auto">
            <AlertTriangle className="w-7 h-7 text-amber-400" />
          </div>

          {/* Heading & subtext */}
          <div>
            <h2 className="text-xl font-semibold text-white">
              Pago no completado
            </h2>
            <p className="text-gray-400 text-sm mt-1">
              El proceso de pago fue cancelado o no se completó. No se realizó
              ningún cargo.
            </p>
          </div>

          {/* Primary CTA */}
          <Link
            href="/billing"
            className="inline-flex items-center justify-center w-full bg-[#EAB308] hover:bg-[#D4A00A] text-white font-medium rounded-xl px-4 py-3 transition-colors"
          >
            Volver a planes
          </Link>

          {/* Support link */}
          <p className="text-gray-500 text-sm">
            ¿Necesitás ayuda?{" "}
            <a
              href="mailto:soporte@tukijuris.net.pe"
              className="text-amber-400 hover:text-amber-300 transition-colors"
            >
              soporte@tukijuris.net.pe
            </a>
          </p>
        </div>
      </div>
    </main>
  );
}
