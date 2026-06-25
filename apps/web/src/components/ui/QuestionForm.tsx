"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowRight, Check, Loader2 } from "lucide-react";

export type PendingQuestion = {
  slot: string;
  question: string;
  helper?: string;
  options?: string[];
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
  /** Selected chip value, OR custom text when `isCustom` is true. */
  value: string;
  /** True when the user clicked "Otro…" and is typing a free-text answer. */
  isCustom: boolean;
};

/**
 * Structured question form rendered during the case-analysis intake /
 * investigation phase. Each question is a card with quick-pick chips +
 * an "Otro…" free-text input. The user can answer some or all questions
 * and submit them as a single batched response so the orchestrator can
 * extract slots in one turn instead of forcing the user to type a wall
 * of text.
 */
export function QuestionForm({
  questions,
  onSubmit,
  disabled,
  loading,
  title = "Para avanzar, ayudame con estos datos",
  subtitle = "Marcá la opción que más se acerque o escribí libremente. Podés saltar las que no apliquen.",
  ctaLabel = "Continuar",
}: QuestionFormProps) {
  const [answers, setAnswers] = useState<Record<string, AnswerState>>({});
  // Tracks which "Otro…" inputs the user has opened (used to autofocus).
  const customRefs = useRef<Record<string, HTMLInputElement | null>>({});

  // Reset internal state if the question list itself changes (new intake).
  const questionsKey = useMemo(
    () => questions.map((q) => q.slot).join("|"),
    [questions],
  );
  useEffect(() => {
    setAnswers({});
  }, [questionsKey]);

  const answeredCount = Object.values(answers).filter(
    (a) => a.value.trim().length > 0,
  ).length;
  const total = questions.length;
  const canSubmit = answeredCount > 0 && !disabled && !loading;

  const pickOption = (slot: string, value: string) => {
    setAnswers((prev) => ({
      ...prev,
      [slot]: { value, isCustom: false },
    }));
  };

  const openCustom = (slot: string) => {
    setAnswers((prev) => ({
      ...prev,
      [slot]: { value: prev[slot]?.isCustom ? prev[slot].value : "", isCustom: true },
    }));
    requestAnimationFrame(() => customRefs.current[slot]?.focus());
  };

  const setCustomValue = (slot: string, value: string) => {
    setAnswers((prev) => ({
      ...prev,
      [slot]: { value, isCustom: true },
    }));
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
      if (!a || !a.value.trim()) return;
      lines.push(`${i + 1}. **${q.question}** — ${a.value.trim()}`);
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
          const ans = answers[q.slot];
          const selected = ans?.value;
          const options = q.options ?? [];
          const hasOptions = options.length > 0;
          return (
            <div
              key={q.slot}
              className="rounded-[11px] border border-outline-variant bg-surface-container-low p-3.5"
            >
              <div className="flex items-baseline justify-between gap-2">
                <div className="text-[13.5px] font-semibold text-on-surface-strong">
                  {q.question}
                </div>
                {selected && (
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

              {hasOptions ? (
                <div className="mt-2.5 flex flex-wrap gap-1.5">
                  {options.map((opt) => {
                    const isSelected = !ans?.isCustom && selected === opt;
                    return (
                      <button
                        key={opt}
                        type="button"
                        onClick={() => pickOption(q.slot, opt)}
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
                  <button
                    type="button"
                    onClick={() => openCustom(q.slot)}
                    className={
                      ans?.isCustom
                        ? "inline-flex h-[30px] items-center rounded-full border border-primary/55 bg-[rgba(201,168,76,0.14)] px-3 text-[12px] font-semibold text-primary"
                        : "inline-flex h-[30px] items-center rounded-full border border-dashed border-outline-variant bg-transparent px-3 text-[12px] text-on-surface-subtle transition-colors hover:border-primary/35 hover:text-on-surface-variant"
                    }
                  >
                    Otro…
                  </button>
                </div>
              ) : null}

              {(ans?.isCustom || !hasOptions) && (
                <input
                  ref={(el) => {
                    customRefs.current[q.slot] = el;
                  }}
                  type="text"
                  value={ans?.value ?? ""}
                  onChange={(e) => setCustomValue(q.slot, e.target.value)}
                  placeholder={hasOptions ? "Escribí tu respuesta…" : "Tu respuesta…"}
                  className="mt-2.5 w-full rounded-[9px] border border-outline-variant bg-surface px-3 py-2 text-[13px] text-on-surface placeholder-on-surface-subtle focus:border-primary/55 focus:outline-none"
                />
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
