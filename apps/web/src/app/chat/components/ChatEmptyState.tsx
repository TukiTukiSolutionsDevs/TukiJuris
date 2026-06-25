"use client";

import Image from "next/image";
import { ArrowUp, Scale, Shield, FileText, Building2 } from "lucide-react";
import { QUERY_TEMPLATES, LEGAL_AREAS } from "../constants";

// ---------------------------------------------------------------------------
// ChatEmptyState — first landing when no messages yet. Notion-editorial style.
// Uses `.c-empty` namespace.
// ---------------------------------------------------------------------------

interface ChatEmptyStateProps {
  selectedArea: string | null;
  onSelectTemplate: (query: string) => void;
}

// Fallback prompt meta icons per area. Chosen for visual variety.
const AREA_ICON: Record<string, React.ComponentType<{ size?: number; strokeWidth?: number }>> = {
  laboral: Scale,
  penal: Shield,
  civil: FileText,
  tributario: Building2,
  constitucional: Scale,
  administrativo: Building2,
  corporativo: Building2,
  registral: FileText,
  competencia: Shield,
  compliance: Shield,
  comercio_exterior: Building2,
  general: Scale,
};

export function ChatEmptyState({ selectedArea, onSelectTemplate }: ChatEmptyStateProps) {
  const activeArea = selectedArea && QUERY_TEMPLATES[selectedArea] ? selectedArea : "general";
  const templates = (QUERY_TEMPLATES[activeArea] ?? QUERY_TEMPLATES.general).slice(0, 4);
  const areaMeta = selectedArea ? LEGAL_AREAS.find((a) => a.id === selectedArea) : null;

  return (
    <div className="c-empty">
      <div className="c-empty__mark">
        <Image
          src="/brand/logo-tj.png"
          alt=""
          width={60}
          height={60}
          priority
        />
      </div>

      <div className="c-empty__eyebrow">TukiJuris · Derecho peruano</div>

      <h1 className="c-empty__h">¿En qué te ayudo hoy?</h1>

      <p className="c-empty__lede">
        Consultá normativa, jurisprudencia y doctrina peruana. Respuestas con
        cita al artículo o casación exacta.
      </p>

      <div className="c-prompts" role="list">
        {templates.map((tpl) => {
          const Icon = AREA_ICON[activeArea] ?? Scale;
          const areaLabel = areaMeta?.name ?? "General";
          return (
            <button
              key={tpl.label}
              type="button"
              role="listitem"
              className="c-prompt"
              onClick={() => onSelectTemplate(tpl.query)}
              title={tpl.query}
            >
              <span className="c-prompt__icon" aria-hidden="true">
                <Icon size={16} strokeWidth={1.6} />
              </span>
              <span className="c-prompt__body">
                <span className="c-prompt__label">{tpl.label}</span>
                <span className="c-prompt__area">{areaLabel}</span>
              </span>
              <ArrowUp size={14} className="c-prompt__go" aria-hidden="true" />
            </button>
          );
        })}
      </div>
    </div>
  );
}
