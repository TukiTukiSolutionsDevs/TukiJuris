"use client";

// ---------------------------------------------------------------------------
// TypingIndicator — pulse + phase label. Uses `.c-typing` namespace.
// ---------------------------------------------------------------------------

type Phase = "consultando" | "redactando" | "citando";

const LABELS: Record<Phase, string> = {
  consultando: "TukiJuris está consultando fuentes…",
  redactando: "Redactando respuesta…",
  citando: "Cruzando jurisprudencia…",
};

interface TypingIndicatorProps {
  phase?: Phase;
  /** Fallback label when no phase matches; overrides the preset text. */
  label?: string;
}

export function TypingIndicator({ phase = "consultando", label }: TypingIndicatorProps) {
  const text = label ?? LABELS[phase];
  return (
    <div className="c-typing" aria-live="polite">
      <span className="c-typing__pulse" aria-hidden="true" />
      <span className="c-typing__label">{text}</span>
    </div>
  );
}
