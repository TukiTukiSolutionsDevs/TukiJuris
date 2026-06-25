"use client";

// ---------------------------------------------------------------------------
// AreaChip — small uppercase pill identifying a legal area
// Uses the `.c-area` CSS namespace (see apps/web/src/app/globals.css).
// ---------------------------------------------------------------------------

import { AREA_LABELS } from "../constants";

interface AreaChipProps {
  area: string;
  dot?: boolean;
  compact?: boolean;
}

export function AreaChip({ area, dot = true }: AreaChipProps) {
  const label = AREA_LABELS[area] ?? area;
  return (
    <span className={`c-area c-area--${area}`}>
      {dot && <span className="c-area__dot" aria-hidden="true" />}
      {label}
    </span>
  );
}

export { AREA_LABELS };
