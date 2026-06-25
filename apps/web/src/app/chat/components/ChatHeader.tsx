"use client";

import Link from "next/link";
import { MessageSquare, Brain, CheckCircle2, Download, Loader2, Sparkles } from "lucide-react";
import { ShellUtilityActions } from "@/components/shell/ShellUtilityActions";
import { AreaChip } from "./AreaChip";
import { LEGAL_AREAS } from "../constants";

// ---------------------------------------------------------------------------
// ChatHeader — top bar of the chat screen, Notion-editorial (.c-topbar).
// Preserves all existing props/callbacks.
// ---------------------------------------------------------------------------

interface ChatHeaderProps {
  conversationTitle: string | null;
  selectedArea: string | null;
  currentConversationId: string | null;
  /** Orchestrator phase — drives the "ver razonamiento" button visibility. */
  orchPhase: string;
  /** Latest status line from the orchestrator (mobile pill). */
  orchStatusText: string;
  onShowOrchPanel: () => void;
  /** True when the conversation has at least one user message. */
  hasMessages: boolean;
  /** True while the PDF export is in-flight. */
  isExportingConversation: boolean;
  onExportConversation: () => void;
}

function StatusChip({ phase }: { phase: string }) {
  if (phase === "idle") {
    return (
      <span className="c-chip c-chip--neutral" role="status">
        <span className="c-chip__dot c-chip__dot--neutral" aria-hidden="true" />
        Sin actividad
      </span>
    );
  }
  if (phase === "done") {
    return (
      <span className="c-chip" role="status">
        <span className="c-chip__dot" aria-hidden="true" />
        Completado
      </span>
    );
  }
  return (
    <span className="c-chip" role="status">
      <span className="c-chip__dot" aria-hidden="true" />
      En curso
    </span>
  );
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
  const title = conversationTitle || "Nueva consulta";
  const areaMeta = selectedArea ? LEGAL_AREAS.find((a) => a.id === selectedArea) : null;
  const showOrchButton = orchPhase !== "idle";

  return (
    <header className="c-topbar" role="banner">
      <div className="c-topbar__left">
        <div className="c-crumbs">
          <MessageSquare size={14} strokeWidth={1.6} aria-hidden="true" />
          <span className="c-crumbs__path">Chat</span>
          <span className="c-crumbs__sep" aria-hidden="true">/</span>
          <span className="c-crumbs__current" title={title}>{title}</span>
        </div>
        <StatusChip phase={orchPhase} />
        {areaMeta && selectedArea && (
          <AreaChip area={selectedArea} dot={false} />
        )}
      </div>

      <div className="c-topbar__right">
        {showOrchButton && (
          <button
            type="button"
            className="c-btn c-btn--ghost"
            onClick={onShowOrchPanel}
            title="Ver razonamiento del análisis"
            aria-label="Abrir panel de razonamiento"
          >
            {orchPhase === "done" ? (
              <CheckCircle2 size={14} strokeWidth={1.6} />
            ) : (
              <Brain size={14} strokeWidth={1.6} />
            )}
            <span className="hidden sm:inline">
              {orchPhase === "done" ? "Razonamiento" : orchStatusText || "Analizando…"}
            </span>
          </button>
        )}

        {hasMessages && (
          <button
            type="button"
            className="c-btn c-btn--ghost"
            onClick={onExportConversation}
            disabled={isExportingConversation || !currentConversationId}
            aria-busy={isExportingConversation}
            title="Exportar conversación a PDF"
          >
            {isExportingConversation ? (
              <Loader2 size={14} strokeWidth={1.6} className="animate-spin" />
            ) : (
              <Download size={14} strokeWidth={1.6} />
            )}
            <span className="hidden sm:inline">
              {isExportingConversation ? "Exportando…" : "Exportar"}
            </span>
          </button>
        )}

        <span className="c-divider" aria-hidden="true" />

        <Link href="/analizar" className="c-btn c-btn--primary" aria-label="Analizar documento">
          <Sparkles size={14} strokeWidth={1.6} />
          <span className="hidden sm:inline">Analizar</span>
        </Link>

        {currentConversationId && (
          <span
            className="c-btn c-btn--ghost"
            style={{
              fontFamily: "ui-monospace, Menlo, monospace",
              fontSize: 11,
              pointerEvents: "none",
              opacity: 0.6,
            }}
            aria-label={`Conversación ${currentConversationId.slice(0, 8)}`}
          >
            #{currentConversationId.slice(0, 8)}
          </span>
        )}

        <ShellUtilityActions compact />
      </div>
    </header>
  );
}
