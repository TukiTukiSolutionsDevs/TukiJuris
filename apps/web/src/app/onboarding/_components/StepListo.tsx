"use client";

import Link from "next/link";
import { Check, ChevronRight, Info } from "lucide-react";
import { SUGGESTED_QUERIES_BY_AREA } from "../_constants";
import type { OnboardingState } from "../_types";

export function StepListo({
  state,
  onFinish,
}: {
  state: OnboardingState;
  onFinish: () => void;
}) {
  const suggestions = state.areas
    .slice(0, 3)
    .map((a) => SUGGESTED_QUERIES_BY_AREA[a])
    .filter(Boolean);

  const defaultSuggestions = [
    "Cuales son los requisitos para un despido justificado?",
    "Como se calcula la CTS en Peru?",
    "Que dice el Art. 1351 del Codigo Civil sobre contratos?",
  ];

  const displaySuggestions =
    suggestions.length > 0 ? suggestions : defaultSuggestions;

  return (
    <div className="max-w-lg mx-auto text-center">
      {/* Success icon */}
      <div className="w-16 h-16 sm:w-20 sm:h-20 mx-auto mb-6 rounded-full bg-primary flex items-center justify-center shadow-[0_0_24px_rgba(234,179,8,0.25)]">
        <Check className="w-8 h-8 sm:w-10 sm:h-10 text-on-primary" strokeWidth={2.5} />
      </div>

      <h2 className="font-['Newsreader'] text-2xl sm:text-3xl text-on-surface mb-2 leading-tight">
        Todo listo!
      </h2>
      <p className="text-on-surface-variant text-sm mb-6 max-w-sm mx-auto">
        Tu cuenta esta configurada y lista para usar.
      </p>

      {!state.apiKeySaved && (
        <div className="flex items-start gap-2.5 mb-6 px-4 py-3 bg-primary/10 border-2 border-primary/20 rounded-lg text-xs sm:text-sm text-on-surface-variant text-left">
          <Info className="w-4 h-4 text-primary mt-0.5 shrink-0" />
          <span>
            Recorda configurar tu clave API en{" "}
            <a href="/configuracion" className="text-primary font-semibold hover:underline">
              Configuracion
            </a>{" "}
            para acceder a modelos premium.
          </span>
        </div>
      )}

      {/* Suggestions */}
      <p className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant/50 mb-3">
        Prueba estas consultas
      </p>
      <div className="text-left space-y-2 mb-8">
        {displaySuggestions.map((s) => (
          <Link
            key={s}
            href={`/?q=${encodeURIComponent(s)}`}
            className="block rounded-lg p-3.5 text-xs sm:text-sm text-on-surface-variant border-2 border-outline-variant/20 bg-surface-container hover:border-primary/30 hover:text-on-surface transition-all duration-150"
          >
            &ldquo;{s}&rdquo;
          </Link>
        ))}
      </div>

      {/* CTA */}
      <button
        onClick={onFinish}
        className="group inline-flex items-center gap-3 h-12 sm:h-14 px-8 sm:px-10 bg-gradient-to-br from-primary to-primary-container text-on-primary font-bold rounded-lg uppercase tracking-wider text-sm transition-all duration-200 hover:shadow-[0_8px_24px_rgba(234,179,8,0.3)] active:scale-[0.97]"
      >
        Ir al Chat
        <ChevronRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
      </button>
    </div>
  );
}
