"use client";
import Image from "next/image";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { QUERY_TEMPLATES, LEGAL_AREAS } from "../constants";

interface ChatEmptyStateProps {
  selectedArea: string | null;
  onSelectTemplate: (query: string) => void;
}

export function ChatEmptyState({ selectedArea, onSelectTemplate }: ChatEmptyStateProps) {
  const [showAll, setShowAll] = useState(false);
  const activeTemplates =
    selectedArea && QUERY_TEMPLATES[selectedArea]
      ? QUERY_TEMPLATES[selectedArea]
      : QUERY_TEMPLATES.general;
  const visibleTemplates = showAll ? activeTemplates : activeTemplates.slice(0, 4);
  const selectedAreaMeta = selectedArea ? LEGAL_AREAS.find((a) => a.id === selectedArea) : null;

  return (
    <div className="mx-auto flex h-full w-full max-w-2xl flex-col items-center justify-center px-4 py-6 text-center">
      {/* Hero compact */}
      <div className="mb-5 flex flex-col items-center gap-2">
        <Image
          src="/brand/logo-full.png"
          className="w-9 opacity-80 md:w-11"
          alt="TukiJuris"
          width={44}
          height={44}
        />
        <h2 className="font-headline text-2xl font-bold tracking-tight text-on-surface md:text-3xl">
          ¿En qué te ayudo?
        </h2>
        <p className="max-w-sm text-sm leading-relaxed text-on-surface/55">
          Consultá normativa y orientación legal sobre derecho peruano al instante.
        </p>
      </div>

      {/* Section label */}
      {selectedArea && selectedAreaMeta ? (
        <p className="section-eyebrow mb-3 text-on-surface/35">
          {selectedAreaMeta.name} — consultas frecuentes
        </p>
      ) : (
        <p className="mb-3 text-[11px] font-medium uppercase tracking-[0.18em] text-on-surface/38">
          Sugerencias rápidas
        </p>
      )}

      {/* Template cards — compact 2-col */}
      <div className="grid w-full grid-cols-2 gap-2 sm:gap-3">
        {visibleTemplates.map((tpl) => (
          <button
            key={tpl.label}
            onClick={() => onSelectTemplate(tpl.query)}
            title={tpl.query}
            className="panel-base rounded-2xl border-2 border-outline-variant/30 px-3 py-2.5 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-md"
          >
            <span className="block text-sm font-medium text-on-surface">{tpl.label}</span>
          </button>
        ))}
      </div>

      {activeTemplates.length > 4 && (
        <button
          onClick={() => setShowAll((v) => !v)}
          className="mt-3 flex items-center gap-1.5 text-xs text-on-surface/40 transition-colors hover:text-on-surface/70"
        >
          {showAll ? (
            <>
              <ChevronUp className="h-3.5 w-3.5" /> Ver menos
            </>
          ) : (
            <>
              <ChevronDown className="h-3.5 w-3.5" /> Ver más ({activeTemplates.length - 4})
            </>
          )}
        </button>
      )}
    </div>
  );
}
