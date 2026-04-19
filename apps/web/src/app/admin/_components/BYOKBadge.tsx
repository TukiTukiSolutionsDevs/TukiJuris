"use client";

/**
 * BYOKBadge — inline badge shown in the users table when byok_count > 0.
 * Pure presentational: no state, no network calls.
 */

import { Key } from "lucide-react";

interface BYOKBadgeProps {
  count: number;
}

export function BYOKBadge({ count }: BYOKBadgeProps) {
  if (count === 0) return null;

  return (
    <span
      className="inline-flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-primary/10 text-primary"
      title={`${count} clave${count !== 1 ? "s" : ""} BYOK activa${count !== 1 ? "s" : ""}`}
    >
      <Key className="w-2.5 h-2.5" />
      {count}
    </span>
  );
}
