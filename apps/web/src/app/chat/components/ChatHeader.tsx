"use client";

import { Bot, Brain, CheckCircle2, Download, Loader2 } from "lucide-react";
import { ShellUtilityActions } from "@/components/shell/ShellUtilityActions";
import { LEGAL_AREAS } from "../constants";

interface ChatHeaderProps {
  conversationTitle: string | null;
  selectedArea: string | null;
  currentConversationId: string | null;
  /** Current orchestrator phase — drives the mini-button visibility */
  orchPhase: string;
  /** Latest status text shown inside the mini-button */
  orchStatusText: string;
  onShowOrchPanel: () => void;
  /** Whether the current conversation has at least one message */
  hasMessages: boolean;
  /** True while the export request is in-flight */
  isExportingConversation: boolean;
  /** Called when the user clicks "Exportar conversación" */
  onExportConversation: () => void;
}

export function ChatHeader({
  conversationTitle,
  selectedArea,
  currentConversationId,
  orchPhase,
  orchStatusText,
  onShowOrchPanel,
  hasMessages,
  isExportingConversation,
  onExportConversation,
}: ChatHeaderProps) {
  const selectedAreaMeta = selectedArea
    ? LEGAL_AREAS.find((a) => a.id === selectedArea)
    : null;

  return (
    <header className="border-b border-outline-variant/30 bg-surface px-4 py-3 lg:px-6 shrink-0">
      <div className="flex items-center justify-between gap-4">
        {/* Left: icon + title + area badge */}
        <div className="min-w-0 flex-1 flex items-center gap-2.5">
          <Bot className="w-5 h-5 text-primary shrink-0" aria-hidden="true" />
          <h1 className="truncate text-base font-medium tracking-[-0.02em] text-on-surface lg:text-lg">
            {conversationTitle || "Nueva consulta"}
          </h1>
          <span className="hidden sm:inline-flex shrink-0 items-center rounded-full border border-outline-variant/30 bg-surface-container-low px-2.5 py-1 text-[10px] uppercase tracking-[0.18em] text-on-surface/45">
            {selectedAreaMeta ? selectedAreaMeta.name : "General"}
          </span>
        </div>

        {/* Right: export button + orchestrator mini-button (mobile) + conv ID + utility actions */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Export conversation button — only shown when there are messages */}
          {hasMessages && (
            <button
              type="button"
              onClick={onExportConversation}
              disabled={isExportingConversation || !currentConversationId}
              aria-busy={isExportingConversation}
              aria-label={
                isExportingConversation
                  ? "Exportando conversación..."
                  : "Exportar conversación"
              }
              className="flex items-center gap-1.5 text-xs font-medium text-on-surface/60 hover:text-on-surface border border-outline-variant/30 hover:border-primary/30 rounded-lg px-3 py-1.5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Exportar conversación a PDF"
            >
              {isExportingConversation ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Download className="w-3.5 h-3.5" />
              )}
              {isExportingConversation ? "Exportando..." : "Exportar conversación"}
            </button>
          )}

          {orchPhase !== "idle" && (
            <button
              type="button"
              onClick={onShowOrchPanel}
              className="xl:hidden group flex items-center gap-2 rounded-[1.25rem] border border-primary/15 bg-[radial-gradient(circle_at_left,rgba(201,169,97,0.12),transparent_38%),linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0))] px-3 py-2 shadow-[0_12px_28px_rgba(0,0,0,0.08)] transition hover:border-primary/25 hover:bg-primary/5"
              aria-label="Abrir razonamiento del análisis"
            >
              <div
                className={`relative flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                  orchPhase === "done" ? "bg-emerald-400/12 text-emerald-500" : "bg-primary/12 text-primary"
                }`}
              >
                <span
                  className={`absolute inset-0 rounded-full animate-ping ${
                    orchPhase === "done" ? "bg-emerald-400/10" : "bg-primary/10"
                  }`}
                />
                {orchPhase === "done" ? (
                  <CheckCircle2 className="relative h-4 w-4" />
                ) : (
                  <Brain className="relative h-4 w-4" />
                )}
              </div>
              <div className="min-w-0 hidden sm:block">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-primary/80">
                  Mirá el razonamiento
                </p>
                <p className="mt-0.5 truncate text-[10px] text-on-surface/58 max-w-[130px]">
                  {orchStatusText || "Analizando..."}
                </p>
              </div>
            </button>
          )}

          {currentConversationId && (
            <span className="hidden md:inline-flex rounded-lg border border-outline-variant/30 bg-surface-container-low px-2 py-1 text-[10px] text-on-surface/35">
              #{currentConversationId.slice(0, 8)}
            </span>
          )}
          <ShellUtilityActions />
        </div>
      </div>
    </header>
  );
}
