"use client";
import { Bot, ThumbsUp, ThumbsDown, Bookmark, Download } from "lucide-react";
import { renderMarkdown } from "@/lib/markdown";
import { t } from "@/lib/i18n";
import type { Message } from "../types";

interface ChatBubbleProps {
  message: Message;
  onFeedback: (id: string, rating: "thumbs_up" | "thumbs_down") => void;
  onToggleBookmark: (msg: Message) => void;
  onDownloadPDF: (msg: Message) => void;
}

export function ChatBubble({ message: msg, onFeedback, onToggleBookmark, onDownloadPDF }: ChatBubbleProps) {
  if (msg.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-tr-md border-2 border-primary/15 bg-primary/8 px-4 py-3">
          <p className="text-sm whitespace-pre-wrap leading-relaxed text-on-surface">{msg.content}</p>
        </div>
      </div>
    );
  }

  // Assistant bubble
  return (
    <div className="flex gap-2.5">
      <div className="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-primary/10">
        <Bot className="h-3.5 w-3.5 text-primary" />
      </div>
      <div className="panel-base max-w-[92%] rounded-2xl rounded-tl-md border-2 border-outline-variant/30 px-4 py-3">
        {/* Markdown content */}
        <div
          className="text-sm leading-relaxed text-on-surface"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
        />

        {/* Citations */}
        {msg.citations && msg.citations.length > 0 && (
          <details className="mt-2 border-t border-outline-variant/20 pt-2">
            <summary className="cursor-pointer select-none text-[10px] text-on-surface/40 transition-colors hover:text-on-surface/70">
              📜 {msg.citations.length} referencia{msg.citations.length > 1 ? "s" : ""} normativa
              {msg.citations.length > 1 ? "s" : ""}
            </summary>
            <div className="mt-1.5 flex flex-wrap gap-1">
              {msg.citations.slice(0, 20).map((cit, i) => (
                <span
                  key={i}
                  className="rounded-lg bg-surface-container-low px-1.5 py-0.5 text-[9px] text-on-surface/60"
                  title={cit.text}
                >
                  {cit.text.length > 40 ? cit.text.slice(0, 37) + "..." : cit.text}
                </span>
              ))}
            </div>
          </details>
        )}

        {/* Agent badge + actions */}
        {msg.agent_used && (
          <div className="mt-2 flex items-center justify-between border-t border-outline-variant/20 pt-2 text-xs text-on-surface/40">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-lg bg-surface-container-high px-2 py-0.5 text-[10px] uppercase text-on-surface/60">
                {msg.agent_used}
              </span>
              {msg.model_used && (
                <span className="text-[10px] text-on-surface/30">{msg.model_used.split("/").pop()}</span>
              )}
              {msg.latency_ms && (
                <span className="text-on-surface/30">{(msg.latency_ms / 1000).toFixed(1)}s</span>
              )}
              {msg.is_multi_area && (
                <span className="rounded-lg border-2 border-primary/20 bg-primary/10 px-1.5 py-0.5 text-[10px] text-primary">
                  Multi-área
                </span>
              )}
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => onFeedback(msg.id, "thumbs_up")}
                aria-label={t("chat.feedback.good")}
                className={`rounded-lg p-1 transition-colors hover:bg-surface-container-low ${
                  msg.feedback === "thumbs_up" ? "text-green-400" : "text-on-surface/30 hover:text-primary"
                }`}
              >
                <ThumbsUp className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => onFeedback(msg.id, "thumbs_down")}
                aria-label={t("chat.feedback.bad")}
                className={`rounded-lg p-1 transition-colors hover:bg-surface-container-low ${
                  msg.feedback === "thumbs_down" ? "text-red-400" : "text-on-surface/30 hover:text-primary"
                }`}
              >
                <ThumbsDown className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => onToggleBookmark(msg)}
                aria-label={msg.is_bookmarked ? "Quitar marcador" : "Guardar marcador"}
                className={`rounded-lg p-1 transition-colors hover:bg-surface-container-low ${
                  msg.is_bookmarked ? "text-primary" : "text-on-surface/30 hover:text-primary"
                }`}
              >
                <Bookmark className="h-3.5 w-3.5" fill={msg.is_bookmarked ? "currentColor" : "none"} />
              </button>
              <button
                onClick={() => onDownloadPDF(msg)}
                aria-label={t("chat.download.pdf")}
                className="rounded-lg p-1 text-on-surface/30 transition-colors hover:bg-surface-container-low hover:text-primary"
              >
                <Download className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
