"use client";

import { LEGAL_AREAS, AREA_HEX_COLORS } from "@/app/chat/constants";

interface AreaBadgeProps {
  area: string | null | undefined;
  size?: "sm" | "md" | "lg";
  variant?: "solid" | "dot" | "outline";
  className?: string;
}

const SIZE_CLASSES: Record<"sm" | "md" | "lg", string> = {
  sm: "text-[10px] px-1.5 py-[2px] gap-1",
  md: "text-[11px] px-2 py-[3px] gap-1.5",
  lg: "text-[12px] px-2.5 py-1 gap-1.5",
};

const DOT_SIZE: Record<"sm" | "md" | "lg", string> = {
  sm: "h-1.5 w-1.5",
  md: "h-[7px] w-[7px]",
  lg: "h-2 w-2",
};

/**
 * Canonical area badge — single source of truth for "labeled chip per legal
 * area" across /analizar, /historial, /marcadores, /analytics, /buscar.
 *
 * Pulls label from LEGAL_AREAS and color from AREA_HEX_COLORS. Falls back to
 * a neutral chip when the area id is unknown.
 */
export function AreaBadge({
  area,
  size = "md",
  variant = "solid",
  className = "",
}: AreaBadgeProps) {
  if (!area) return null;
  const meta = LEGAL_AREAS.find((a) => a.id === area);
  const hex = AREA_HEX_COLORS[area] ?? "#6b7280";
  const label = meta?.name ?? area;

  if (variant === "dot") {
    return (
      <span
        className={`inline-flex items-center font-semibold uppercase tracking-[0.06em] text-on-surface-variant ${SIZE_CLASSES[size]} ${className}`}
      >
        <span
          className={`shrink-0 rounded-full ${DOT_SIZE[size]}`}
          style={{ background: hex }}
        />
        {label}
      </span>
    );
  }

  if (variant === "outline") {
    return (
      <span
        className={`inline-flex items-center rounded-md border font-bold uppercase tracking-[0.1em] ${SIZE_CLASSES[size]} ${className}`}
        style={{
          borderColor: `${hex}55`,
          color: hex,
        }}
      >
        {label}
      </span>
    );
  }

  // solid (default) — soft colored chip
  return (
    <span
      className={`inline-flex items-center rounded-md font-bold uppercase tracking-[0.1em] ${SIZE_CLASSES[size]} ${className}`}
      style={{
        background: `${hex}22`,
        color: hex,
      }}
    >
      {label}
    </span>
  );
}
