"use client";

import {
  Pin,
  Share2,
  MessageSquare,
  Folder,
  MoreHorizontal,
  Check,
} from "lucide-react";
import { AreaChip } from "../../chat/components/AreaChip";

// ---------------------------------------------------------------------------
// ConversationCard — list item for /historial. Cozy + compact densities.
// ---------------------------------------------------------------------------

export interface ConversationCardData {
  id: string;
  title: string | null;
  legal_area?: string | null;
  is_pinned: boolean;
  is_shared: boolean;
  message_count: number;
  last_message_at?: string; // ISO
  preview?: string | null;
  tags?: { id: string; name: string }[];
}

export type CardDensity = "cozy" | "compact";

interface ConversationCardProps {
  conv: ConversationCardData;
  density?: CardDensity;
  selected?: boolean;
  hasSelection?: boolean;
  dragging?: boolean;
  onClick?: () => void;
  onToggleSelect?: () => void;
  onRightClick?: (e: React.MouseEvent) => void;
  onTogglePin?: () => void;
  onMove?: () => void;
  onShare?: () => void;
  onMore?: (e: React.MouseEvent) => void;
  /** Formatter for the relative date — callers own the locale/logic. */
  formatDate?: (iso: string) => string;
}

function cx(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

function defaultFormatDate(iso: string): string {
  const d = new Date(iso);
  const now = Date.now();
  const diff = now - d.getTime();
  const hour = 3_600_000;
  const day = 24 * hour;

  if (diff < hour) return "recién";
  if (diff < day) return `hace ${Math.floor(diff / hour)} h`;
  if (diff < 2 * day) return "ayer";
  if (diff < 7 * day) return `hace ${Math.floor(diff / day)} d`;
  return d.toLocaleDateString("es-PE", { day: "numeric", month: "short" });
}

export function ConversationCard({
  conv,
  density = "cozy",
  selected = false,
  hasSelection = false,
  dragging = false,
  onClick,
  onToggleSelect,
  onRightClick,
  onTogglePin,
  onMove,
  onShare,
  onMore,
  formatDate = defaultFormatDate,
}: ConversationCardProps) {
  const compact = density === "compact";
  const dateLabel = conv.last_message_at ? formatDate(conv.last_message_at) : "";
  const titleText = conv.title || "Sin título";

  return (
    <div
      role="button"
      tabIndex={0}
      className={cx(
        "hst-card",
        compact && "hst-card--compact",
        selected && "is-selected",
        conv.is_pinned && "hst-card--pinned",
        dragging && "is-dragging",
        hasSelection && "hst-has-selection"
      )}
      onClick={onClick}
      onContextMenu={(e) => {
        if (onRightClick) {
          e.preventDefault();
          onRightClick(e);
        }
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter" && onClick) onClick();
      }}
    >
      {onToggleSelect && (
        <button
          type="button"
          className={cx("hst-card__check", selected && "is-checked")}
          onClick={(e) => {
            e.stopPropagation();
            onToggleSelect();
          }}
          aria-label={selected ? "Deseleccionar" : "Seleccionar"}
          aria-pressed={selected}
        >
          {selected && <Check size={12} strokeWidth={2.5} />}
        </button>
      )}

      <div className="hst-card__body">
        <div className="hst-card__titlerow">
          {conv.is_pinned && (
            <Pin size={12} strokeWidth={2} className="hst-card__pin" fill="currentColor" />
          )}
          <span
            className={cx("hst-card__title", !conv.title && "hst-card__title--empty")}
            title={titleText}
          >
            {titleText}
          </span>
          {conv.is_shared && (
            <Share2 size={13} strokeWidth={1.6} className="hst-card__share" aria-label="Compartida" />
          )}
        </div>

        {!compact && conv.preview && (
          <div className="hst-card__preview">{conv.preview}</div>
        )}

        <div className="hst-card__meta">
          {conv.legal_area && <AreaChip area={conv.legal_area} />}
          <span className="hst-card__msgs" aria-label={`${conv.message_count} mensajes`}>
            <MessageSquare size={11} strokeWidth={1.6} />
            {conv.message_count} msg
          </span>
          {conv.tags && conv.tags.length > 0 && (
            <span className="hst-card__tags">
              {conv.tags.slice(0, 3).map((t) => (
                <span key={t.id} className="hst-tagchip">
                  <span className="hst-tagchip__hash">#</span>
                  {t.name}
                </span>
              ))}
              {conv.tags.length > 3 && (
                <span className="hst-tagchip" style={{ opacity: 0.7 }}>
                  +{conv.tags.length - 3}
                </span>
              )}
            </span>
          )}
        </div>
      </div>

      <div className="hst-card__right">
        {dateLabel && <span className="hst-card__date">{dateLabel}</span>}
        <div className="hst-card__actions" onClick={(e) => e.stopPropagation()}>
          {onTogglePin && (
            <button
              type="button"
              className="hst-actbtn"
              onClick={(e) => {
                e.stopPropagation();
                onTogglePin();
              }}
              aria-label={conv.is_pinned ? "Desfijar" : "Fijar"}
              title={conv.is_pinned ? "Desfijar" : "Fijar"}
            >
              <Pin
                size={13}
                strokeWidth={1.6}
                fill={conv.is_pinned ? "currentColor" : "none"}
              />
            </button>
          )}
          {onMove && (
            <button
              type="button"
              className="hst-actbtn"
              onClick={(e) => {
                e.stopPropagation();
                onMove();
              }}
              aria-label="Mover a carpeta"
              title="Mover"
            >
              <Folder size={13} strokeWidth={1.6} />
            </button>
          )}
          {onShare && (
            <button
              type="button"
              className="hst-actbtn"
              onClick={(e) => {
                e.stopPropagation();
                onShare();
              }}
              aria-label="Compartir"
              title="Compartir"
            >
              <Share2 size={13} strokeWidth={1.6} />
            </button>
          )}
          {onMore && (
            <button
              type="button"
              className="hst-actbtn"
              onClick={(e) => {
                e.stopPropagation();
                onMore(e);
              }}
              aria-label="Más opciones"
              title="Más opciones"
            >
              <MoreHorizontal size={13} strokeWidth={2} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
