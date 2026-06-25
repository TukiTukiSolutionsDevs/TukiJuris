"use client";

/**
 * UsageBadge — daily quota indicator for the current user.
 *
 * The plan has TWO independent pools (free tier = 4 normal + 1 reasoning):
 *   - Normal queries     → blue/neutral tone
 *   - Reasoning queries  → purple tone (matches the "thinking" UX cue)
 *
 * For unlimited plans (pro/studio) we collapse both pools into a single
 * "sin límite diario" line to avoid clutter.
 *
 * Tone shifts to amber when remaining <= 1 in any pool.
 */

import { Sparkles, Brain } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";

const PLAN_LABEL: Record<string, string> = {
  free: "Modo gratuito",
  pro: "Plan Pro",
  studio: "Plan Studio",
};

function formatResetTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "00:00";
  }
}

interface PoolPillProps {
  icon: React.ElementType;
  label: string;
  used: number;
  limit: number;
  remaining: number;
  toneClass: string;
}

function PoolPill({ icon: Icon, label, used, limit, remaining, toneClass }: PoolPillProps) {
  const lowQuota = remaining <= 1;
  const tone = lowQuota
    ? "border-amber-400/40 bg-amber-400/10 text-amber-700 dark:text-amber-300"
    : toneClass;
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-xs px-2 py-1 rounded-md border ${tone}`}
      title={`${label}: ${used}/${limit} consumidas hoy`}
    >
      <Icon className="w-3 h-3 shrink-0" aria-hidden="true" />
      <span className="font-semibold tabular-nums">{used}</span>
      <span className="text-on-surface/40">/</span>
      <span className="tabular-nums">{limit}</span>
      <span className="text-on-surface/50">{label}</span>
    </span>
  );
}

export function UsageBadge({ className = "" }: { className?: string }) {
  const { usage } = useAuth();
  if (!usage) return null;

  const {
    plan,
    used_today,
    daily_limit,
    remaining_today,
    used_today_reasoning,
    reasoning_limit,
    remaining_reasoning,
    reset_at,
  } = usage;
  const planLabel = PLAN_LABEL[plan] ?? `Plan ${plan}`;
  const isUnlimited = daily_limit === -1 && reasoning_limit === -1;

  if (isUnlimited) {
    return (
      <div
        role="status"
        aria-live="polite"
        className={`inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg border border-[rgba(79,70,51,0.2)] bg-surface-container-low text-on-surface/70 ${className}`}
      >
        <Sparkles className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
        <span className="font-medium">{planLabel}</span>
        <span className="text-on-surface/30" aria-hidden="true">·</span>
        <span>sin límite diario</span>
      </div>
    );
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className={`inline-flex flex-wrap items-center gap-2 text-xs px-3 py-1.5 rounded-lg border border-[rgba(79,70,51,0.2)] bg-surface-container-low ${className}`}
    >
      <span className="inline-flex items-center gap-1.5 font-medium text-on-surface/70">
        <Sparkles className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
        {planLabel}
      </span>

      {daily_limit !== -1 && (
        <PoolPill
          icon={Sparkles}
          label="normales"
          used={used_today}
          limit={daily_limit}
          remaining={remaining_today}
          toneClass="border-[rgba(79,70,51,0.2)] bg-surface text-on-surface/70"
        />
      )}

      {reasoning_limit !== -1 && (
        <PoolPill
          icon={Brain}
          label="razonamiento"
          used={used_today_reasoning}
          limit={reasoning_limit}
          remaining={remaining_reasoning}
          toneClass="border-purple-400/30 bg-purple-400/10 text-purple-700 dark:text-purple-300"
        />
      )}

      <span className="text-on-surface/30" aria-hidden="true">·</span>
      <span className="text-on-surface/50">
        reinicia {formatResetTime(reset_at)}
      </span>
    </div>
  );
}
