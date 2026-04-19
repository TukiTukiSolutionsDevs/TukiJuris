"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, PanelRightClose } from "lucide-react";
import type { OrchestratorState } from "../types";
import { LEGAL_AREAS } from "../constants";

interface OrchestratorPanelProps {
  variant: "rail" | "sheet";
  orchState: OrchestratorState;
  onClose: () => void;
}

// ---------------------------------------------------------------------------
// Radar SVG sub-component (same file — no separate file needed)
// ---------------------------------------------------------------------------
function OrchestratorRadar({
  radarAreas,
  phase,
}: {
  radarAreas: typeof LEGAL_AREAS;
  phase: OrchestratorState["phase"];
}) {
  return (
    <div className="relative flex h-24 w-24 shrink-0 items-center justify-center rounded-[1.4rem] border border-outline-variant/15 bg-surface-container-lowest">
      <svg viewBox="0 0 120 120" className="h-20 w-20" aria-hidden="true">
        <defs>
          <linearGradient id="analysis-ring" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#A78BFA" />
            <stop offset="100%" stopColor="#34D399" />
          </linearGradient>
        </defs>
        <circle cx="60" cy="60" r="38" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1.5" />
        <circle cx="60" cy="60" r="28" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
        {radarAreas.map((area, index) => {
          const positions = [
            { x: 60, y: 18 },
            { x: 92, y: 76 },
            { x: 28, y: 78 },
          ];
          const point = positions[index];
          return (
            <g key={area.id}>
              <line
                x1="60" y1="60" x2={point.x} y2={point.y}
                stroke="url(#analysis-ring)"
                strokeOpacity="0.45"
                strokeWidth="1.5"
                strokeDasharray="4 4"
              >
                <animate attributeName="stroke-dashoffset" values="0;-16" dur="1.8s" repeatCount="indefinite" />
              </line>
              <circle
                cx={point.x} cy={point.y} r="6"
                fill={index === 0 && phase !== "idle" ? "#34D399" : "#A78BFA"}
              >
                <animate attributeName="r" values="5.5;7.5;5.5" dur={`${1.8 + index * 0.25}s`} repeatCount="indefinite" />
                <animate attributeName="opacity" values="0.7;1;0.7" dur={`${1.8 + index * 0.25}s`} repeatCount="indefinite" />
              </circle>
            </g>
          );
        })}
        <circle
          cx="60" cy="60" r="12"
          fill={phase === "done" ? "#34D399" : "#C9A961"}
          fillOpacity="0.2"
          stroke="url(#analysis-ring)"
          strokeWidth="2.5"
        >
          <animate attributeName="r" values="11;13;11" dur="2.4s" repeatCount="indefinite" />
        </circle>
        {phase === "done" ? (
          <path d="M54 60l5 5 9-12" fill="none" stroke="#34D399" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        ) : (
          <path d="M52 47c-4 2-6 6-6 11 0 8 6 14 14 14 3 0 6-1 8-3m-2-22c4 2 6 6 6 11" fill="none" stroke="#C9A961" strokeWidth="3" strokeLinecap="round" />
        )}
      </svg>
      <div className="pointer-events-none absolute inset-0 rounded-[1.4rem] bg-[radial-gradient(circle,rgba(201,169,97,0.12),transparent_60%)]" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// OrchestratorPanel — unified rail + sheet, ONE content path
// ---------------------------------------------------------------------------
export function OrchestratorPanel({ variant, orchState, onClose }: OrchestratorPanelProps) {
  const [isTimelineOpen, setIsTimelineOpen] = useState(false);

  // ---- derived values (moved from page.tsx) ----
  const involvedAreas = LEGAL_AREAS.filter(
    (area) => orchState.activeAgents.includes(area.id) || orchState.secondaryAreas.includes(area.id)
  );
  const highlightedAreas = LEGAL_AREAS.filter(
    (area) => orchState.primaryArea === area.id || orchState.secondaryAreas.includes(area.id)
  );
  const radarAreas = (
    highlightedAreas.length > 0
      ? highlightedAreas
      : involvedAreas.length > 0
        ? involvedAreas
        : LEGAL_AREAS.slice(0, 3)
  ).slice(0, 3);

  const processSteps = [
    { id: "received",  label: "Nos contás tu caso",                        done: orchState.steps.length > 0 },
    { id: "detected",  label: "Detectamos áreas relevantes",               done: orchState.activeAgents.length > 0 },
    { id: "prepared",  label: "Preparamos una orientación más precisa",    done: orchState.phase === "done" },
  ];

  const currentAnalysisStep =
    [...orchState.steps].reverse().find((s) => !s.done) ??
    orchState.steps[orchState.steps.length - 1] ??
    null;
  const currentStepElapsed =
    currentAnalysisStep && orchState.startTime > 0
      ? ((currentAnalysisStep.ts - orchState.startTime) / 1000).toFixed(1)
      : null;

  const analysisHeadline =
    orchState.phase === "done"
      ? "Análisis completado"
      : orchState.phase === "evaluating"
        ? "Estamos revisando tu consulta"
        : "Listo para revisar tu consulta";

  const analysisSupportingText =
    orchState.phase === "done"
      ? highlightedAreas.length > 0
        ? `Detectamos ${highlightedAreas.map((a) => a.label).join(", ")} como ${
            highlightedAreas.length === 1 ? "área relevante" : "áreas relevantes"
          } para tu caso.`
        : "Terminamos la revisión inicial de tu consulta."
      : orchState.phase === "evaluating"
        ? orchState.statusText || "Estamos identificando los temas legales que podrían intervenir en tu caso."
        : "Cuando nos cuentes tu situación, vamos a identificar qué áreas legales podrían intervenir para orientarte mejor.";

  const getAreaPresentation = (areaId: string) => {
    const isPrimary  = orchState.primaryArea === areaId;
    const isSecondary = orchState.secondaryAreas.includes(areaId);
    const isActive   = orchState.activeAgents.includes(areaId);

    if (isPrimary)
      return {
        badge: "Prioritaria",
        containerClass: "border-primary/30 bg-primary/10 shadow-[0_0_0_1px_rgba(201,169,97,0.08)]",
        iconClass:      "text-primary bg-primary/15",
        badgeClass:     "bg-primary/15 text-primary",
      };
    if (isSecondary)
      return {
        badge: "Detectada",
        containerClass: "border-secondary/30 bg-secondary/10",
        iconClass:      "text-secondary bg-secondary/15",
        badgeClass:     "bg-secondary/15 text-secondary/80",
      };
    if (isActive)
      return {
        badge: "En revisión",
        containerClass: "border-emerald-400/20 bg-emerald-400/10",
        iconClass:      "text-emerald-300 bg-emerald-400/10",
        badgeClass:     "bg-emerald-400/10 text-emerald-300",
      };
    return {
      badge: "Disponible",
      containerClass: "border-outline-variant/10 bg-surface-container-low/60",
      iconClass:      "text-on-surface/55 bg-surface-container-high/70",
      badgeClass:     "bg-surface-container-high/70 text-on-surface/45",
    };
  };

  // ---- shared panel content — ONE rendering path ----
  const panelContent = (
    <>
      {/* Panel header */}
      <div className="px-4 py-4 bg-surface-container-low flex items-start justify-between shrink-0 border-b border-outline-variant/10">
        <div className="max-w-[260px]">
          <span className="text-[10px] font-bold uppercase tracking-[0.22em] text-primary/75">Análisis de tu caso</span>
          <p className="mt-2 text-[12px] text-on-surface/72 leading-relaxed">
            Identificamos las áreas legales que podrían intervenir para orientarte mejor.
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-on-surface/40 hover:text-on-surface/70 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30 rounded-lg"
          aria-label="Cerrar panel de análisis"
        >
          <PanelRightClose className="w-4 h-4" />
        </button>
      </div>

      {/* Radar card */}
      <div className="px-4 py-4 bg-surface shrink-0 border-b border-outline-variant/10">
        <div className="overflow-hidden rounded-[1.6rem] border border-outline-variant/15 bg-[radial-gradient(circle_at_top,rgba(167,139,250,0.18),transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0))] p-4 shadow-[0_24px_60px_rgba(0,0,0,0.28)]">
          <div className="flex items-start gap-4">
            <OrchestratorRadar radarAreas={radarAreas} phase={orchState.phase} />
            <div className="min-w-0 flex-1">
              <p className="text-[11px] uppercase tracking-[0.18em] text-on-surface/45">Estado del análisis</p>
              <h3 className="mt-1 text-[1.15rem] font-semibold tracking-[-0.02em] text-on-surface">
                {analysisHeadline}
              </h3>
              <p className="mt-1.5 text-[11px] text-on-surface/68 leading-relaxed">{analysisSupportingText}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {radarAreas.map((area, index) => (
                  <span
                    key={area.id}
                    className={`rounded-full px-2.5 py-1 text-[10px] ${
                      index === 0 ? "bg-primary/12 text-primary" : "bg-outline-variant/10 text-on-surface/55"
                    }`}
                  >
                    {area.name}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {(orchState.confidence > 0 || orchState.latencyMs > 0 || orchState.citationCount > 0) && (
            <div className="mt-3 flex flex-wrap gap-2">
              {orchState.confidence > 0 && (
                <span className="rounded-full bg-surface-container-high px-2.5 py-1 text-[10px] text-on-surface/60">
                  Confianza {Math.round(orchState.confidence * 100)}%
                </span>
              )}
              {orchState.latencyMs > 0 && (
                <span className="rounded-full bg-surface-container-high px-2.5 py-1 text-[10px] text-on-surface/60">
                  {(orchState.latencyMs / 1000).toFixed(1)}s
                </span>
              )}
              {orchState.citationCount > 0 && (
                <span className="rounded-full bg-surface-container-high px-2.5 py-1 text-[10px] text-on-surface/60">
                  {orchState.citationCount} referencias
                </span>
              )}
            </div>
          )}

          {/* How it works */}
          <div className="mt-4 space-y-2 rounded-2xl border border-outline-variant/10 bg-surface-container-lowest/50 p-3">
            <p className="text-[10px] uppercase tracking-[0.18em] text-on-surface/45">Cómo funciona</p>
            {processSteps.map((step) => (
              <div key={step.id} className="flex items-center gap-2.5 text-[11px]">
                <span
                  className={`flex h-5 w-5 items-center justify-center rounded-full border text-[10px] ${
                    step.done
                      ? "border-primary/30 bg-primary/10 text-primary"
                      : "border-outline-variant/15 bg-surface text-on-surface/40"
                  }`}
                >
                  {step.done ? "✓" : processSteps.findIndex((item) => item.id === step.id) + 1}
                </span>
                <span className={step.done ? "text-on-surface/80" : "text-on-surface/50"}>{step.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Evaluation reason */}
      {orchState.evaluationReason && orchState.phase === "done" && (
        <div className="px-4 py-3 bg-surface-container-low shrink-0 border-b border-outline-variant/10">
          <p className="text-[10px] uppercase tracking-[0.18em] text-secondary/75 mb-1">Por qué estas áreas</p>
          <p className="text-[11px] text-on-surface/65 leading-relaxed">{orchState.evaluationReason}</p>
        </div>
      )}

      {/* Scrollable area cards */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        <div>
          <p className="text-[10px] uppercase tracking-[0.18em] text-on-surface/45 mb-2">Áreas legales involucradas</p>
          <p className="text-[11px] text-on-surface/55 leading-relaxed mb-3">
            Estas áreas se activan según el contenido de tu consulta. No todas participan siempre.
          </p>
        </div>
        <div className="space-y-2">
          {LEGAL_AREAS.map((area) => {
            const AreaIcon = area.icon;
            const pres = getAreaPresentation(area.id);
            return (
              <div
                key={area.id}
                className={`rounded-2xl border px-3 py-3 transition-all duration-500 ${pres.containerClass}`}
              >
                <div className="flex items-start gap-3">
                  <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition-all duration-500 ${pres.iconClass}`}>
                    <AreaIcon className="w-4 h-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-[12px] font-medium text-on-surface">{area.label}</p>
                        <p className="mt-1 text-[10px] leading-relaxed text-on-surface/55">{area.description}</p>
                      </div>
                      <span className={`shrink-0 rounded-full px-2 py-1 text-[9px] font-medium ${pres.badgeClass}`}>
                        {pres.badge}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Result summary */}
        <div className="rounded-2xl border border-outline-variant/10 bg-surface-container-low/70 p-4">
          <p className="text-[10px] uppercase tracking-[0.18em] text-on-surface/45">Resultado del análisis</p>
          {orchState.phase === "done" && involvedAreas.length > 0 ? (
            <>
              <p className="mt-2 text-sm font-medium text-on-surface">
                Detectamos {involvedAreas.map((a) => a.label).join(", ")}
              </p>
              <p className="mt-1 text-[11px] leading-relaxed text-on-surface/60">
                Estas áreas aparecen porque encontramos elementos de tu consulta que podrían requerir una revisión combinada.
              </p>
            </>
          ) : (
            <>
              <p className="mt-2 text-sm font-medium text-on-surface">Todavía no recibimos una consulta</p>
              <p className="mt-1 text-[11px] leading-relaxed text-on-surface/60">
                Apenas escribas tu caso, te mostraremos qué áreas detectamos y por qué podrían intervenir.
              </p>
            </>
          )}
        </div>
      </div>

      {/* Timeline accordion */}
      {orchState.steps.length > 0 && currentAnalysisStep && (
        <div className="bg-surface-container-low px-4 py-3 shrink-0 border-t border-outline-variant/10">
          <button
            type="button"
            onClick={() => setIsTimelineOpen((prev) => !prev)}
            className="flex w-full items-center gap-3 rounded-2xl border border-outline-variant/10 bg-surface-container/5 px-3 py-3 text-left transition hover:bg-surface-container/10"
            aria-expanded={isTimelineOpen}
            aria-label="Mostrar seguimiento del análisis"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <span className="text-sm">{currentAnalysisStep.icon}</span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[10px] uppercase tracking-[0.18em] text-on-surface/42">Seguimiento del análisis</p>
              <p className="mt-1 truncate text-[11px] text-on-surface/72">{currentAnalysisStep.text}</p>
            </div>
            <div className="flex items-center gap-2">
              {currentStepElapsed && (
                <span className="text-[10px] tabular-nums text-on-surface/35">{currentStepElapsed}s</span>
              )}
              {isTimelineOpen
                ? <ChevronUp className="h-4 w-4 text-on-surface/40" />
                : <ChevronDown className="h-4 w-4 text-on-surface/40" />
              }
            </div>
          </button>
          {isTimelineOpen && (
            <div className="mt-2 max-h-48 overflow-y-auto rounded-2xl border border-outline-variant/10 bg-surface-container-lowest/50 p-3">
              <div className="space-y-1.5">
                {orchState.steps.map((step, i) => {
                  const elapsed =
                    orchState.startTime > 0
                      ? ((step.ts - orchState.startTime) / 1000).toFixed(1)
                      : null;
                  const isCurrent =
                    currentAnalysisStep.ts === step.ts && currentAnalysisStep.text === step.text;
                  return (
                    <div
                      key={i}
                      className={`flex items-center gap-2 rounded-xl px-2 py-1.5 text-[11px] ${
                        isCurrent ? "bg-primary/10 text-on-surface" : "text-on-surface/55"
                      }`}
                    >
                      <span className="w-4 text-center">{step.icon}</span>
                      <span
                        className={`flex-1 truncate ${
                          isCurrent ? "text-on-surface" : step.done ? "text-on-surface/50" : "text-primary"
                        }`}
                      >
                        {step.text}
                      </span>
                      {elapsed && (
                        <span className="text-[9px] text-on-surface/25 tabular-nums flex-shrink-0">{elapsed}s</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );

  // ---- variant wrapper — only the shell changes ----
  if (variant === "rail") {
    return (
      <aside className="flex h-full w-[22rem] border-l border-outline-variant/30 bg-surface flex-col overflow-hidden flex-shrink-0">
        {panelContent}
      </aside>
    );
  }

  return (
    <div className="flex max-h-[70vh] flex-col overflow-hidden bg-surface rounded-t-lg md:max-h-full md:h-full md:rounded-none">
      {panelContent}
    </div>
  );
}
