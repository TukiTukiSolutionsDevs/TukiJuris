"use client";

import { TrendingDown, TrendingUp, Minus } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  trend?: number | null;
  trendSuffix?: string;
  trendLabel?: string;
  sub?: React.ReactNode;
  icon?: React.ReactNode;
  loading?: boolean;
}

/**
 * Canonical statistic card — used in /analytics, /billing, /organizacion.
 * Visual: Newsreader number 30px gold, eyebrow label, optional trend with arrow.
 */
export function StatCard({
  label,
  value,
  trend,
  trendSuffix = "%",
  trendLabel = "vs mes ant.",
  sub,
  icon,
  loading,
}: StatCardProps) {
  if (loading) {
    return (
      <div className="card-canon p-5">
        <div className="mb-2 h-3 w-24 animate-pulse rounded bg-surface-container" />
        <div className="mb-2 h-8 w-32 animate-pulse rounded bg-surface-container" />
        <div className="h-3 w-20 animate-pulse rounded bg-surface-container" />
      </div>
    );
  }

  const trendColor =
    trend == null
      ? "text-on-surface-subtle"
      : trend > 0
        ? "text-status-success"
        : trend < 0
          ? "text-status-danger"
          : "text-on-surface-subtle";

  return (
    <div className="card-canon p-5">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[9.5px] font-extrabold uppercase tracking-[0.14em] text-on-surface-subtle">
          {label}
        </p>
        {icon ? <div className="shrink-0 text-on-surface-subtle">{icon}</div> : null}
      </div>
      <div className="stat-number mt-2">{value}</div>
      {trend != null ? (
        <div
          className={`mt-1.5 inline-flex items-center gap-1 text-[11.5px] font-bold ${trendColor}`}
        >
          {trend > 0 ? (
            <TrendingUp className="h-3 w-3" strokeWidth={2.4} />
          ) : trend < 0 ? (
            <TrendingDown className="h-3 w-3" strokeWidth={2.4} />
          ) : (
            <Minus className="h-3 w-3" strokeWidth={2.4} />
          )}
          <span>
            {trend > 0 ? "+" : ""}
            {trend}
            {trendSuffix}
          </span>
          <span className="font-medium text-on-surface-subtle">{trendLabel}</span>
        </div>
      ) : sub ? (
        <div className="mt-1.5 text-[12px] text-on-surface-variant">{sub}</div>
      ) : null}
    </div>
  );
}
