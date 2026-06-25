"use client";

import { useRef } from "react";
import Link from "next/link";
import {
  Paperclip,
  Loader2,
  Scale,
  ChevronDown,
  ArrowUp,
  AlertCircle,
  X,
} from "lucide-react";
import { MODEL_CATALOG, modelSupportsThinking } from "@/lib/models";
import { LEGAL_AREAS } from "../constants";
import HelpPopover from "@/components/HelpPopover";
import { t } from "@/lib/i18n";
import { AttachmentChip } from "./AttachmentChip";

// ---------------------------------------------------------------------------
// ChatComposer — Notion-editorial composer. `.c-composer` namespace.
// Contract preserved: same props as before. Removed "showAdvanced" toggle —
// the new design always surfaces scope / model / depth in a single top row.
// ---------------------------------------------------------------------------

interface AttachedFile {
  id: string;
  name: string;
  type: string;
  preview: string;
}

interface ChatComposerProps {
  input: string;
  onInputChange: (value: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  disabled: boolean;
  disabledPlaceholder?: string;
  selectedArea: string | null;
  onClearArea: () => void;
  selectedModel: string;
  onModelChange: (model: string) => void;
  availableModels: string[];
  reasoningEffort: string | null;
  onReasoningChange: (effort: string | null) => void;
  attachedFile: AttachedFile | null;
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onRemoveFile: () => void;
  uploading: boolean;
  inputRef?: React.RefObject<HTMLTextAreaElement | null>;
  /** Optional error message shown above the composer box. */
  errorText?: string;
  onRetry?: () => void;
  mobile?: boolean;
}

const REASONING_CYCLE: Array<{ value: string | null; label: string }> = [
  { value: null, label: "Auto" },
  { value: "low", label: "Rápida" },
  { value: "medium", label: "Moderada" },
  { value: "high", label: "Profunda" },
];

function nextReasoning(current: string | null): string | null {
  const idx = REASONING_CYCLE.findIndex((r) => r.value === current);
  return REASONING_CYCLE[(idx + 1) % REASONING_CYCLE.length].value;
}

function reasoningLabel(current: string | null): string {
  return REASONING_CYCLE.find((r) => r.value === current)?.label ?? "Auto";
}

const MAX_CHARS = 4000;

export function ChatComposer({
  input,
  onInputChange,
  onSubmit,
  isLoading,
  disabled,
  disabledPlaceholder,
  selectedArea,
  onClearArea,
  selectedModel,
  onModelChange,
  availableModels,
  reasoningEffort,
  onReasoningChange,
  attachedFile,
  onFileUpload,
  onRemoveFile,
  uploading,
  inputRef: externalRef,
  errorText,
  onRetry,
  mobile = false,
}: ChatComposerProps) {
  const internalRef = useRef<HTMLTextAreaElement>(null);
  const textareaRef = externalRef ?? internalRef;
  const fileInputRef = useRef<HTMLInputElement>(null);

  const areaMeta = selectedArea ? LEGAL_AREAS.find((a) => a.id === selectedArea) : null;
  const scopeLabel = areaMeta ? areaMeta.name : "Consulta general";

  const modelMeta = MODEL_CATALOG.find((m) => m.id === selectedModel);
  const modelSummary = modelMeta?.name ?? selectedModel;
  const hasThinking = modelSupportsThinking(selectedModel);
  const hasModels = availableModels.length > 0;

  const placeholder = disabled
    ? disabledPlaceholder ?? t("chat.placeholder")
    : "Escribí tu consulta jurídica. Usá / para comandos, @ para citar fuentes.";

  const composerClass = `c-composer${mobile ? " c-composer--mobile" : ""}`;
  const sendDisabled = isLoading || disabled || !input.trim();

  return (
    <div className="c-composer-wrap">
      <div className={composerClass}>
        {errorText && (
          <div className="c-composer__error" role="alert">
            <AlertCircle size={14} strokeWidth={1.6} aria-hidden="true" />
            <span>{errorText}</span>
            {onRetry && (
              <button type="button" className="c-error__retry" onClick={onRetry}>
                Reintentar
              </button>
            )}
          </div>
        )}

        <form
          onSubmit={onSubmit}
          aria-busy={isLoading}
          aria-label="Formulario de consulta legal"
        >
          <div className="c-composer__box">
            {attachedFile && (
              <div className="c-composer__attachments">
                <AttachmentChip
                  file={{ name: attachedFile.name, type: attachedFile.type }}
                  onRemove={onRemoveFile}
                />
              </div>
            )}

            {/* Scope / model / depth row */}
            <div className="c-composer__top">
              <button
                type="button"
                className="c-scope"
                onClick={areaMeta ? onClearArea : undefined}
                title={areaMeta ? "Quitar filtro de área" : "Área detectada automáticamente"}
              >
                <Scale size={14} strokeWidth={1.6} aria-hidden="true" />
                <span>{scopeLabel}</span>
                {areaMeta ? (
                  <X size={12} strokeWidth={2} aria-hidden="true" />
                ) : (
                  <ChevronDown size={12} strokeWidth={1.8} aria-hidden="true" />
                )}
              </button>

              <span className="c-composer__sep" aria-hidden="true">·</span>

              {hasModels ? (
                <label className="c-composer__model" style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
                  <span className="sr-only">{t("model.select")}</span>
                  <select
                    value={selectedModel}
                    onChange={(e) => onModelChange(e.target.value)}
                    aria-label={t("model.select")}
                    style={{
                      background: "transparent",
                      color: "inherit",
                      font: "inherit",
                      border: 0,
                      outline: 0,
                      cursor: "pointer",
                    }}
                  >
                    {MODEL_CATALOG.filter((m) => availableModels.includes(m.id)).map((m) => (
                      <option key={m.id} value={m.id} style={{ background: "#1F1F1E", color: "#ECEAE3" }}>
                        {m.name}
                      </option>
                    ))}
                  </select>
                </label>
              ) : (
                <Link
                  href="/configuracion"
                  className="c-composer__model"
                  style={{ color: "var(--n-accent)", textDecoration: "none" }}
                  title="Configurá tu API key"
                >
                  Configurar modelos →
                </Link>
              )}

              <span className="c-composer__sep" aria-hidden="true">·</span>

              <button
                type="button"
                className="c-depth"
                onClick={() => hasThinking && onReasoningChange(nextReasoning(reasoningEffort))}
                disabled={!hasThinking}
                title={
                  hasThinking
                    ? `Profundidad de análisis: ${reasoningLabel(reasoningEffort)}. Click para cambiar.`
                    : `${modelSummary} no soporta modos de razonamiento`
                }
                style={!hasThinking ? { opacity: 0.4, cursor: "not-allowed" } : undefined}
              >
                {reasoningLabel(reasoningEffort)}
              </button>
            </div>

            <textarea
              id="chat-input"
              ref={textareaRef}
              rows={3}
              value={input}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  onSubmit(e as unknown as React.FormEvent);
                }
              }}
              aria-label={t("chat.placeholder")}
              className="c-composer__input"
              disabled={isLoading || disabled}
              placeholder={placeholder}
              maxLength={MAX_CHARS}
              onInput={(e) => {
                const el = e.currentTarget;
                el.style.height = "auto";
                el.style.height = `${Math.min(el.scrollHeight, 240)}px`;
              }}
            />

            <div className="c-composer__bottom">
              <div className="c-composer__tools">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.doc,.jpg,.jpeg,.png,.webp,.txt"
                  onChange={onFileUpload}
                  className="hidden"
                  style={{ display: "none" }}
                />
                <button
                  type="button"
                  className="c-iconbtn"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  aria-label="Adjuntar documento"
                  title="Adjuntar documento"
                >
                  {uploading ? (
                    <Loader2 size={15} strokeWidth={1.6} className="animate-spin" />
                  ) : (
                    <Paperclip size={15} strokeWidth={1.6} />
                  )}
                </button>

                {!mobile && <span className="c-composer__divider" aria-hidden="true" />}
                {!mobile && (
                  <span className="c-composer__counter" aria-live="off">
                    {input.length.toLocaleString("es-PE")} / {MAX_CHARS.toLocaleString("es-PE")}
                  </span>
                )}
              </div>

              <div className="c-composer__send">
                {!mobile && (
                  <span className="c-hint">
                    <kbd>Enter</kbd> envía · <kbd>⇧</kbd><kbd>Enter</kbd> nueva línea
                  </span>
                )}
                <HelpPopover onShowShortcuts={() => {}} />
                <button
                  type="submit"
                  className="c-send"
                  disabled={sendDisabled}
                  aria-label={t("chat.send")}
                  title={t("chat.send")}
                >
                  {isLoading ? (
                    <Loader2 size={16} strokeWidth={2} className="animate-spin" />
                  ) : (
                    <ArrowUp size={16} strokeWidth={2} />
                  )}
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
