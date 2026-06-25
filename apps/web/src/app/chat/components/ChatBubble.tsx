"use client";

import Image from "next/image";
import { ThumbsUp, ThumbsDown, Bookmark, Download, Copy } from "lucide-react";
import { renderMarkdown } from "@/lib/markdown";
import { t } from "@/lib/i18n";
import type { Message } from "../types";
import { SourcesCard } from "./SourcesCard";
import { AreaChip } from "./AreaChip";

// ---------------------------------------------------------------------------
// ChatBubble — one conversation turn. Notion-editorial style (.c-msg).
// Props/logic identical to the previous implementation; only the markup changed.
// ---------------------------------------------------------------------------

interface ChatBubbleProps {
  message: Message;
  onFeedback: (id: string, rating: "thumbs_up" | "thumbs_down") => void;
  onToggleBookmark: (msg: Message) => void;
  onDownloadPDF: (msg: Message) => void;
  /** Optional — pass true while this specific message is still streaming. */
  streaming?: boolean;
}

function UserAvatar({ initial }: { initial: string }) {
  return (
    <div className="c-avatar" aria-hidden="true">
      {initial}
    </div>
  );
}

function AssistantAvatar() {
  return (
    <div className="c-avatar c-avatar--brand" aria-hidden="true">
      <Image src="/brand/logo-icon.png" alt="" width={30} height={30} />
    </div>
  );
}

export function ChatBubble({
  message: msg,
  onFeedback,
  onToggleBookmark,
  onDownloadPDF,
  streaming = false,
}: ChatBubbleProps) {
  const isUser = msg.role === "user";

  // For user messages, keep it simple and serif-styled.
  if (isUser) {
    const initial = "T"; // "Tú" — caller can override via props later if needed.
    return (
      <div className="c-msg is-user">
        <div className="c-msg__avatar">
          <UserAvatar initial={initial} />
        </div>
        <div className="c-msg__body">
          <div className="c-msg__head">
            <span className="c-msg__who">Tú</span>
          </div>
          <div className="c-msg__text c-msg__text--serif">
            {msg.content.split("\n\n").map((p, i) => (
              <p key={i}>{p}</p>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Assistant message.
  const latencySec = msg.latency_ms ? (msg.latency_ms / 1000).toFixed(1) + "s" : null;
  const modelShort = msg.model_used ? msg.model_used.split("/").pop() : null;

  return (
    <div className="c-msg is-assistant">
      <div className="c-msg__avatar">
        <AssistantAvatar />
      </div>
      <div className="c-msg__body">
        <div className="c-msg__head">
          <span className="c-msg__who">TukiJuris</span>
          {modelShort && (
            <span className="c-msg__model">
              · {modelShort}
              {latencySec && ` · ${latencySec}`}
            </span>
          )}
          {msg.legal_area && (
            <span className="c-msg__area">
              <AreaChip area={msg.legal_area} dot={false} />
            </span>
          )}
          {msg.is_multi_area && (
            <span className="c-msg__area">
              <span className="c-area" title="Se consultó más de un agente especializado">
                Multi-área
              </span>
            </span>
          )}
        </div>

        {/* Markdown body */}
        <div
          className="c-msg__text"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
        />
        {streaming && <span className="c-caret" aria-hidden="true" />}

        {/* Citations */}
        {msg.citations && msg.citations.length > 0 && (
          <SourcesCard citations={msg.citations} />
        )}

        {/* Action row — only when message is "settled" (has agent_used) */}
        {msg.agent_used && !streaming && (
          <div className="c-msg__actions" role="toolbar" aria-label="Acciones del mensaje">
            <button
              type="button"
              className="c-msgbtn"
              onClick={() => {
                void navigator.clipboard.writeText(msg.content);
              }}
              title="Copiar al portapapeles"
            >
              <Copy size={12} strokeWidth={1.8} style={{ marginRight: 4, verticalAlign: -2 }} />
              Copiar
            </button>

            <button
              type="button"
              className={`c-msgbtn${msg.is_bookmarked ? " is-active" : ""}`}
              onClick={() => onToggleBookmark(msg)}
              aria-pressed={!!msg.is_bookmarked}
              title={msg.is_bookmarked ? "Quitar marcador" : "Guardar"}
            >
              <Bookmark
                size={12}
                strokeWidth={1.8}
                fill={msg.is_bookmarked ? "currentColor" : "none"}
                style={{ marginRight: 4, verticalAlign: -2 }}
              />
              {msg.is_bookmarked ? "Guardado" : "Guardar"}
            </button>

            <button
              type="button"
              className="c-msgbtn"
              onClick={() => onDownloadPDF(msg)}
              title={t("chat.download.pdf")}
            >
              <Download size={12} strokeWidth={1.8} style={{ marginRight: 4, verticalAlign: -2 }} />
              PDF
            </button>

            <span className="c-msg__sep" aria-hidden="true" />

            <button
              type="button"
              className={`c-msgbtn c-msgbtn--good${msg.feedback === "thumbs_up" ? " is-active" : ""}`}
              onClick={() => onFeedback(msg.id, "thumbs_up")}
              aria-pressed={msg.feedback === "thumbs_up"}
              aria-label={t("chat.feedback.good")}
              title={t("chat.feedback.good")}
            >
              <ThumbsUp
                size={12}
                strokeWidth={1.8}
                style={{
                  marginRight: 4,
                  verticalAlign: -2,
                  fill: msg.feedback === "thumbs_up" ? "currentColor" : "none",
                }}
              />
              Útil
            </button>

            <button
              type="button"
              className={`c-msgbtn${msg.feedback === "thumbs_down" ? " is-active" : ""}`}
              onClick={() => onFeedback(msg.id, "thumbs_down")}
              aria-pressed={msg.feedback === "thumbs_down"}
              aria-label={t("chat.feedback.bad")}
              title={t("chat.feedback.bad")}
            >
              <ThumbsDown
                size={12}
                strokeWidth={1.8}
                style={{
                  marginRight: 4,
                  verticalAlign: -2,
                  fill: msg.feedback === "thumbs_down" ? "currentColor" : "none",
                }}
              />
              No útil
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
