"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowRight, Check, Loader2, Plus, X } from "lucide-react";

export type PendingQuestion = {
  slot: string;
  question: string;
  helper?: string;
  options?: string[];
  /** When true, the user can select multiple chips at once. */
  multi?: boolean;
};

interface QuestionFormProps {
  questions: PendingQuestion[];
  onSubmit: (formattedAnswer: string) => void;
  disabled?: boolean;
  loading?: boolean;
  /** Optional heading shown above the question list. */
  title?: string;
  /** Optional subtitle shown under the heading. */
  subtitle?: string;
  /** Optional CTA label override. Defaults to "Continuar". */
  ctaLabel?: string;
}

type AnswerState = {
  /** Selected chip values. Length ≤ 1 when `multi=false`. */
  selected: string[];
  /** Free-text addition typed in the "Otro…" input (always optional). */
  custom: string;
  /** Whether the "Otro…" input is visible. */
  customOpen: boolean;
};

const emptyAnswer = (): AnswerState => ({
  selected: [],
  custom: "",
  customOpen: false,
});

/**
 * Structured question form rendered during the case-analysis intake /
 * investigation phase. Each question is a card with quick-pick chips,
 * optional multi-select, and an "Otro…" free-text input that works
 * ALONGSIDE the chips. The user submits the batch as a single response
 * so the orchestrator can extract slots in one turn instead of forcing
 * the user to type a wall of text.
 */
export function QuestionForm({
  questions,
  onSubmit,
  disabled,
  loading,
  title = "Para avanzar, ayudame con estos datos",
  subtitle = "Marcá las opciones que apliquen o escribí en \"Otro…\". Podés combinar ambas.",
  ctaLabel = "Continuar",
}: QuestionFormProps) {
  const [answers, setAnswers] = useState<Record<string, AnswerState>>({});
  const customRefs = useRef<Record<string, HTMLInputElement | null>>({});

  // Reset state when the question list itself changes (new intake turn).
  const questionsKey = useMemo(
    () => questions.map((q) => q.slot).join("|"),
    [questions],
  );
  useEffect(() => {
    setAnswers({});
  }, [questionsKey]);

  const hasAnswer = (a: AnswerState | undefined) =>
    !!a && (a.selected.length > 0 || a.custom.trim().length > 0);

  const answeredCount = questions.filter((q) => hasAnswer(answers[q.slot])).length;
  const total = questions.length;
  const canSubmit = answeredCount > 0 && !disabled && !loading;

  const toggleOption = (q: PendingQuestion, value: string) => {
    setAnswers((prev) => {
      const cur = prev[q.slot] ?? emptyAnswer();
      if (q.multi) {
        const exists = cur.selected.includes(value);
        return {
          ...prev,
          [q.slot]: {
            ...cur,
            selected: exists
              ? cur.selected.filter((v) => v !== value)
              : [...cur.selected, value],
          },
        };
      }
      // Single-select: clicking the same chip clears it; otherwise replace.
      const next = cur.selected[0] === value ? [] : [value];
      return { ...prev, [q.slot]: { ...cur, selected: next } };
    });
  };

  const openCustom = (slot: string) => {
    setAnswers((prev) => {
      const cur = prev[slot] ?? emptyAnswer();
      return { ...prev, [slot]: { ...cur, customOpen: true } };
    });
    requestAnimationFrame(() => customRefs.current[slot]?.focus());
  };

  const closeCustom = (slot: string) => {
    setAnswers((prev) => {
      const cur = prev[slot] ?? emptyAnswer();
      return { ...prev, [slot]: { ...cur, custom: "", customOpen: false } };
    });
  };

  const setCustomValue = (slot: string, value: string) => {
    setAnswers((prev) => {
      const cur = prev[slot] ?? emptyAnswer();
      return { ...prev, [slot]: { ...cur, custom: value, customOpen: true } };
    });
  };

  const clearAnswer = (slot: string) => {
    setAnswers((prev) => {
      const next = { ...prev };
      delete next[slot];
      return next;
    });
  };

  const handleSubmit = () => {
    if (!canSubmit) return;
    const lines: string[] = ["Respuestas a las preguntas:"];
    questions.forEach((q, i) => {
      const a = answers[q.slot];
      if (!hasAnswer(a)) return;
      const parts: string[] = [];
      if (a!.selected.length > 0) parts.push(a!.selected.join(", "));
      const customClean = a!.custom.trim();
      if (customClean) {
        parts.push(parts.length ? `otros: ${customClean}` : customClean);
      }
      lines.push(`${i + 1}. **${q.question}** — ${parts.join(". ")}`);
    });
    onSubmit(lines.join("\n"));
  };

  if (questions.length === 0) return null;

  return (
    <div className="card-canon p-5">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="font-['Newsreader'] text-[18px] font-semibold leading-tight text-on-surface-strong">
            {title}
          </h3>
          {subtitle && (
            <p className="mt-1 text-[12.5px] leading-[1.45] text-on-surface-variant">
              {subtitle}
            </p>
          )}
        </div>
        <span className="shrink-0 rounded-md bg-surface-container px-2 py-1 font-mono text-[10.5px] font-bold tabular-nums text-on-surface-variant">
          {answeredCount}/{total}
        </span>
      </div>

      <div className="flex flex-col gap-4">
        {questions.map((q) => {
          const ans = answers[q.slot] ?? emptyAnswer();
          const options = q.options ?? [];
          const hasOptions = options.length > 0;
          const showCustomInput = ans.customOpen || !hasOptions;
          return (
            <div
              key={q.slot}
              className="rounded-[11px] border border-outline-variant bg-surface-container-low p-3.5"
            >
              <div className="flex items-baseline justify-between gap-2">
                <div className="flex items-baseline gap-2 text-[13.5px] font-semibold text-on-surface-strong">
                  <span>{q.question}</span>
                  {q.multi && (
                    <span className="text-[9.5px] font-bold uppercase tracking-[0.1em] text-on-surface-subtle">
                      multi
                    </span>
                  )}
                </div>
                {hasAnswer(ans) && (
                  <button
                    type="button"
                    onClick={() => clearAnswer(q.slot)}
                    className="text-[10.5px] font-medium uppercase tracking-[0.1em] text-on-surface-subtle hover:text-on-surface-variant"
                  >
                    Limpiar
                  </button>
                )}
              </div>
              {q.helper && (
                <div className="mt-1 text-[11.5px] leading-[1.4] text-on-surface-variant">
                  {q.helper}
                </div>
              )}

              {hasOptions && (
                <div className="mt-2.5 flex flex-wrap gap-1.5">
                  {options.map((opt) => {
                    const isSelected = ans.selected.includes(opt);
                    return (
                      <button
                        key={opt}
                        type="button"
                        onClick={() => toggleOption(q, opt)}
                        className={
                          isSelected
                            ? "inline-flex h-[30px] items-center gap-1.5 rounded-full border border-primary/55 bg-[rgba(201,168,76,0.14)] px-3 text-[12px] font-semibold text-primary"
                            : "inline-flex h-[30px] items-center rounded-full border border-outline-variant bg-surface px-3 text-[12px] text-on-surface-variant transition-colors hover:border-primary/35 hover:text-on-surface-strong"
                        }
                      >
                        {isSelected && (
                          <Check className="h-3 w-3" strokeWidth={2.6} />
                        )}
                        {opt}
                      </button>
                    );
                  })}
                  {!ans.customOpen && (
                    <button
                      type="button"
                      onClick={() => openCustom(q.slot)}
                      className="inline-flex h-[30px] items-center gap-1 rounded-full border border-dashed border-outline-variant bg-transparent px-3 text-[12px] text-on-surface-subtle transition-colors hover:border-primary/35 hover:text-on-surface-variant"
                    >
                      <Plus className="h-3 w-3" strokeWidth={2.4} />
                      Otro…
                    </button>
                  )}
                </div>
              )}

              {showCustomInput && (
                <div className="mt-2.5 flex items-center gap-2">
                  <input
                    ref={(el) => {
                      customRefs.current[q.slot] = el;
                    }}
                    type="text"
                    value={ans.custom}
                    onChange={(e) => setCustomValue(q.slot, e.target.value)}
                    placeholder={
                      hasOptions && ans.selected.length > 0
                        ? "Sumá detalles extra…"
                        : hasOptions
                          ? "Escribí tu respuesta…"
                          : "Tu respuesta…"
                    }
                    className="flex-1 rounded-[9px] border border-outline-variant bg-surface px-3 py-2 text-[13px] text-on-surface placeholder-on-surface-subtle focus:border-primary/55 focus:outline-none"
                  />
                  {hasOptions && (
                    <button
                      type="button"
                      onClick={() => closeCustom(q.slot)}
                      className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[9px] text-on-surface-subtle transition-colors hover:bg-surface-container hover:text-on-surface-variant"
                      aria-label="Cerrar campo libre"
                    >
                      <X className="h-3.5 w-3.5" strokeWidth={2} />
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-4 flex items-center justify-between gap-3">
        <span className="text-[11px] text-on-surface-subtle">
          {answeredCount === 0
            ? "Respondé al menos una para continuar"
            : answeredCount < total
              ? `Faltan ${total - answeredCount} — podés enviar parcial`
              : "Listo para continuar"}
        </span>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="gold-gradient inline-flex h-9 items-center gap-1.5 rounded-lg px-4 text-[12.5px] font-bold text-on-primary transition-opacity hover:opacity-95 disabled:cursor-not-allowed disabled:grayscale disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <ArrowRight className="h-3.5 w-3.5" strokeWidth={2.2} />
          )}
          {ctaLabel}
        </button>
      </div>
    </div>
  );
}
