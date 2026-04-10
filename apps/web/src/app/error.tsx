"use client";

import { useEffect } from "react";
import { AlertTriangle, RotateCcw, Home } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log to error reporting service (Sentry, etc.)
    console.error("[TukiJuris Error Boundary]", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {/* Icon */}
        <div className="w-16 h-16 rounded-2xl bg-tertiary/10 flex items-center justify-center mx-auto mb-6">
          <AlertTriangle className="w-8 h-8 text-tertiary" />
        </div>

        {/* Title */}
        <h1 className="font-['Newsreader'] text-2xl font-bold text-on-surface mb-2">
          Algo salio mal
        </h1>

        {/* Description */}
        <p className="text-on-surface-variant text-sm leading-relaxed mb-6">
          Ocurrio un error inesperado. Podes intentar de nuevo o volver al inicio.
          Si el problema persiste, contactanos a{" "}
          <a
            href="mailto:soporte@tukijuris.net.pe"
            className="text-primary hover:underline"
          >
            soporte@tukijuris.net.pe
          </a>
        </p>

        {/* Error digest (for support) */}
        {error.digest && (
          <p className="text-xs text-on-surface/30 font-mono mb-6">
            Ref: {error.digest}
          </p>
        )}

        {/* Actions */}
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-bold text-on-primary gold-gradient hover:opacity-90 transition-opacity"
          >
            <RotateCcw className="w-4 h-4" />
            Intentar de nuevo
          </button>
          <a
            href="/landing"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm text-on-surface-variant hover:text-on-surface ghost-border hover:bg-surface-container-high/40 transition-colors"
          >
            <Home className="w-4 h-4" />
            Ir al inicio
          </a>
        </div>
      </div>
    </div>
  );
}
