"use client";

import { Move, Tags, Download, Archive, Trash2, X } from "lucide-react";

// ---------------------------------------------------------------------------
// BulkActionBar — sticky bar shown when one or more conversations are
// selected. All callbacks optional so the caller controls feature availability.
// ---------------------------------------------------------------------------

interface BulkActionBarProps {
  count: number;
  onClear: () => void;
  onMove?: () => void;
  onTag?: () => void;
  onExport?: () => void;
  onArchive?: () => void;
  onDelete?: () => void;
}

export function BulkActionBar({
  count,
  onClear,
  onMove,
  onTag,
  onExport,
  onArchive,
  onDelete,
}: BulkActionBarProps) {
  if (count === 0) return null;

  return (
    <div className="hst-bulk" role="toolbar" aria-label="Acciones en lote">
      <span className="hst-bulk__count">
        <span className="hst-bulk__num" aria-label={`${count} seleccionadas`}>
          {count}
        </span>
        {count === 1 ? "conversación seleccionada" : "conversaciones seleccionadas"}
      </span>
      <div className="hst-bulk__spacer" />

      {onMove && (
        <button type="button" className="hst-bulk__btn" onClick={onMove}>
          <Move size={13} strokeWidth={1.6} />
          Mover a…
        </button>
      )}
      {onTag && (
        <button type="button" className="hst-bulk__btn" onClick={onTag}>
          <Tags size={13} strokeWidth={1.6} />
          Tagear
        </button>
      )}
      {onExport && (
        <button type="button" className="hst-bulk__btn" onClick={onExport}>
          <Download size={13} strokeWidth={1.6} />
          Exportar
        </button>
      )}
      {onArchive && (
        <button type="button" className="hst-bulk__btn" onClick={onArchive}>
          <Archive size={13} strokeWidth={1.6} />
          Archivar
        </button>
      )}
      {onDelete && (
        <button
          type="button"
          className="hst-bulk__btn hst-bulk__btn--danger"
          onClick={onDelete}
        >
          <Trash2 size={13} strokeWidth={1.6} />
          Eliminar
        </button>
      )}

      <button
        type="button"
        className="hst-bulk__x"
        onClick={onClear}
        aria-label="Deseleccionar todo"
        title="Deseleccionar"
      >
        <X size={14} strokeWidth={2} />
      </button>
    </div>
  );
}
