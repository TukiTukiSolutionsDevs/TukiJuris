"use client";

import { FileText, X } from "lucide-react";

// ---------------------------------------------------------------------------
// AttachmentChip — preview of an uploaded file in the composer.
// Uses `.c-attach` namespace.
// ---------------------------------------------------------------------------

interface AttachmentChipFile {
  name: string;
  size?: number; // bytes
  type?: string;
}

interface AttachmentChipProps {
  file: AttachmentChipFile;
  onRemove?: () => void;
}

function formatSize(bytes?: number): string | null {
  if (typeof bytes !== "number" || bytes <= 0) return null;
  const mb = bytes / 1024 / 1024;
  if (mb < 0.1) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${mb.toFixed(1)} MB`;
}

export function AttachmentChip({ file, onRemove }: AttachmentChipProps) {
  const size = formatSize(file.size);
  return (
    <div className="c-attach">
      <FileText size={15} strokeWidth={1.6} aria-hidden="true" />
      <span className="c-attach__name" title={file.name}>
        {file.name}
      </span>
      {size && <span className="c-attach__size">{size}</span>}
      {onRemove && (
        <button
          type="button"
          className="c-attach__x"
          aria-label={`Quitar ${file.name}`}
          onClick={onRemove}
        >
          <X size={12} strokeWidth={2} aria-hidden="true" />
        </button>
      )}
    </div>
  );
}
