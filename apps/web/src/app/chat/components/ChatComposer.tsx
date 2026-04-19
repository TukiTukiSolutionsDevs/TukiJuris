"use client";
import { useState, useRef } from "react";
import {
  Send,
  Paperclip,
  FileText,
  X,
  Loader2,
  Settings2,
  Type,
  Bold,
  Italic,
  List,
  Code,
} from "lucide-react";
import { MODEL_CATALOG, modelSupportsThinking } from "@/lib/models";
import { LEGAL_AREAS } from "../constants";
import { insertMarkdownSyntax } from "../utils/markdown-format";
import HelpPopover from "@/components/HelpPopover";
import { t } from "@/lib/i18n";

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
  /** Optional external ref to keep focus control in parent (e.g. keyboard shortcuts) */
  inputRef?: React.RefObject<HTMLTextAreaElement | null>;
}

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
}: ChatComposerProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showFormattingTools, setShowFormattingTools] = useState(false);
  const internalRef = useRef<HTMLTextAreaElement>(null);
  const textareaRef = externalRef ?? internalRef;
  const fileInputRef = useRef<HTMLInputElement>(null);

  const selectedAreaMeta = selectedArea ? LEGAL_AREAS.find((a) => a.id === selectedArea) : null;
  const hasThinking = modelSupportsThinking(selectedModel);

  return (
    <div className="shrink-0 border-t border-outline-variant/30 bg-surface px-3 py-3 sm:px-4 sm:py-4">
      <div className="panel-raised mx-auto max-w-4xl rounded-[1.75rem] p-2.5 sm:p-3.5">

        {/* Advanced controls — hidden by default, toggled with Settings2 */}
        {showAdvanced && (
          <div className="mb-2.5 flex flex-wrap items-center gap-2 border-b border-outline-variant/30 pb-2.5 sm:mb-3 sm:pb-3">
            {selectedAreaMeta ? (
              <button
                type="button"
                onClick={onClearArea}
                className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.18em] text-primary"
              >
                {selectedAreaMeta.name}
                <X className="h-3 w-3" />
              </button>
            ) : (
              <span className="inline-flex items-center rounded-full border border-outline-variant/30 bg-surface px-2.5 py-1 text-[10px] uppercase tracking-[0.18em] text-on-surface/45">
                Consulta general
              </span>
            )}

            <label htmlFor="model-select" className="sr-only">
              {t("model.select")}
            </label>
            {availableModels.length === 0 ? (
              <a
                href="/configuracion"
                className="rounded-lg border border-primary/20 px-2 py-1 text-xs text-primary/70 transition-colors hover:text-primary"
                title="Configurar clave de IA"
              >
                Configurar modelos
              </a>
            ) : (
              <select
                id="model-select"
                value={selectedModel}
                onChange={(e) => onModelChange(e.target.value)}
                aria-label={t("model.select")}
                className="control-surface min-w-[10rem] rounded-xl px-3 py-2 text-xs text-on-surface/75 focus:border-primary/50 focus:outline-none"
              >
                {MODEL_CATALOG.filter((m) => availableModels.includes(m.id)).map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            )}

            {/* Reasoning pills */}
            <div
              className="control-surface flex items-center gap-0.5 rounded-xl p-0.5"
              title={
                hasThinking
                  ? "Controla qué tan profundo analiza la IA tu consulta"
                  : "Este modelo no soporta modos de razonamiento"
              }
            >
              {[
                { value: null, label: "Auto", tooltip: "La IA decide el nivel de análisis" },
                { value: "low", label: "Rápida", tooltip: "Respuesta directa y veloz" },
                { value: "medium", label: "Moderada", tooltip: "Análisis balanceado" },
                { value: "high", label: "Profunda", tooltip: "Análisis exhaustivo" },
              ].map((opt) => {
                const isDisabled = !hasThinking && opt.value !== null;
                return (
                  <button
                    key={opt.label}
                    type="button"
                    onClick={() => !isDisabled && onReasoningChange(opt.value)}
                    title={
                      isDisabled
                        ? `${MODEL_CATALOG.find((m) => m.id === selectedModel)?.name || selectedModel} no soporta "${opt.label}"`
                        : opt.tooltip
                    }
                    disabled={isDisabled}
                    className={`rounded px-2 py-1 text-[10px] font-medium transition-all ${
                      isDisabled
                        ? "cursor-not-allowed text-surface-container-high"
                        : reasoningEffort === opt.value
                          ? "bg-secondary-container text-secondary"
                          : "bg-surface text-on-surface/60 hover:bg-surface-container-high/80 hover:text-on-surface"
                    }`}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>

            {/* Formatting tools trigger */}
            <div className="relative ml-auto flex items-center gap-1">
              <button
                type="button"
                onClick={() => setShowFormattingTools((v) => !v)}
                className="control-surface rounded-xl p-2 text-on-surface/45 hover:text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
                title="Opciones de formato"
                aria-label="Opciones de formato"
              >
                <Type className="h-4 w-4" aria-hidden="true" />
              </button>
              {showFormattingTools && (
                <div className="panel-raised absolute bottom-full right-0 z-20 mb-2 min-w-[220px] rounded-2xl p-2">
                  <div className="mb-1 px-2 pt-1 text-[10px] uppercase tracking-[0.2em] text-on-surface/35">
                    Formato rápido
                  </div>
                  <div className="flex flex-wrap items-center gap-1">
                    {[
                      { icon: Bold, label: "Negrita", prefix: "**", suffix: "**", placeholder: "texto" },
                      { icon: Italic, label: "Cursiva", prefix: "*", suffix: "*", placeholder: "texto" },
                      { icon: List, label: "Lista", prefix: "\n- ", suffix: "", placeholder: "elemento" },
                      { icon: Code, label: "Codigo", prefix: "`", suffix: "`", placeholder: "codigo" },
                    ].map(({ icon: Icon, label, prefix, suffix, placeholder }) => (
                      <button
                        key={label}
                        type="button"
                        title={label}
                        onClick={() => {
                          if (textareaRef.current) {
                            insertMarkdownSyntax(textareaRef.current, prefix, suffix, placeholder, onInputChange);
                          }
                          setShowFormattingTools(false);
                        }}
                        aria-label={label}
                        className="control-surface inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs text-on-surface/65 hover:text-on-surface"
                      >
                        <Icon className="h-3.5 w-3.5" aria-hidden="true" />
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Attached file preview */}
        {attachedFile && (
          <div className="mb-2 flex items-center gap-2 rounded-lg border border-outline-variant/30 bg-surface-container px-3 py-2">
            <FileText className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
            <span className="flex-1 truncate text-xs text-on-surface/60">{attachedFile.name}</span>
            <button
              type="button"
              onClick={onRemoveFile}
              className="rounded-lg text-on-surface/40 transition-colors hover:text-on-surface/70 focus:outline-none focus:ring-2 focus:ring-primary/30"
              aria-label="Quitar archivo adjunto"
            >
              <X className="h-3 w-3" aria-hidden="true" />
            </button>
          </div>
        )}

        {/* Main input row */}
        <form
          onSubmit={onSubmit}
          aria-busy={isLoading}
          aria-label="Formulario de consulta legal"
          className="flex items-end gap-2"
        >
          <label htmlFor="chat-input" className="sr-only">
            {t("chat.placeholder")}
          </label>
          <textarea
            id="chat-input"
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                onSubmit(e as unknown as React.FormEvent);
              }
            }}
            aria-label={t("chat.placeholder")}
            className="min-h-[52px] max-h-28 flex-1 resize-none overflow-y-auto rounded-2xl border-2 border-outline-variant/30 bg-surface-container px-4 py-3 text-sm text-on-surface placeholder-on-surface/30 transition-colors focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20 sm:min-h-[56px] sm:max-h-32"
            disabled={isLoading || disabled}
            placeholder={disabled ? (disabledPlaceholder ?? t("chat.placeholder")) : t("chat.placeholder")}
            style={{ height: "auto" }}
            onInput={(e) => {
              const el = e.currentTarget;
              el.style.height = "auto";
              el.style.height = `${Math.min(el.scrollHeight, 128)}px`;
            }}
          />

          {/* Action buttons */}
          <div className="flex items-center gap-1 self-end">
            {/* Settings toggle */}
            <button
              type="button"
              onClick={() => setShowAdvanced((v) => !v)}
              className={`control-surface rounded-xl p-2.5 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30 ${
                showAdvanced ? "bg-primary/10 text-primary" : "text-on-surface/45 hover:text-on-surface"
              }`}
              title="Opciones avanzadas"
              aria-label="Opciones avanzadas"
              aria-pressed={showAdvanced}
            >
              <Settings2 className="h-4 w-4" aria-hidden="true" />
            </button>

            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.doc,.jpg,.jpeg,.png,.webp,.txt"
              onChange={onFileUpload}
              className="hidden"
            />

            {/* Paperclip */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="control-surface rounded-xl p-2.5 text-on-surface/45 transition-colors hover:text-primary disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-primary/30"
              title="Adjuntar archivo"
              aria-label="Adjuntar archivo"
            >
              {uploading ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <Paperclip className="h-4 w-4" aria-hidden="true" />
              )}
            </button>

            <HelpPopover onShowShortcuts={() => {}} />

            {/* Send */}
            <button
              type="submit"
              disabled={isLoading || !input.trim() || disabled}
              aria-label={t("chat.send")}
              className="gold-gradient rounded-2xl p-3 text-on-primary shadow-[0_14px_30px_rgba(0,0,0,0.18)] transition-all hover:opacity-95 disabled:bg-surface-container-low disabled:text-on-surface/20 disabled:shadow-none focus:outline-none focus:ring-2 focus:ring-primary/40"
            >
              <Send className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
        </form>

        <p className="mt-1.5 px-1 text-[10px] text-on-surface/25 sm:mt-2">
          Enter para enviar, Shift+Enter para nueva linea
        </p>
      </div>
    </div>
  );
}
