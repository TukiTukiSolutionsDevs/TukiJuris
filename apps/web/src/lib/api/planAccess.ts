/**
 * Shared client for the per-user plan/model access endpoint.
 *
 * `GET /api/plans/me` returns the caller's plan plus the data required to
 * decide which models are usable: per-tier daily caps + per-model tier map.
 * Both /configuracion (model picker) and /analizar (sanity-check the saved
 * preference) consume this — keeping the logic here ensures both pages
 * agree on what counts as "blocked vs available".
 */

export type PlanId = "free" | "pro" | "studio";

export interface PlanAccessInfo {
  plan_id: PlanId;
  display_name: string;
  /** Recommended default model when the user hasn't picked one. */
  default_model: string;
  /** tier_number → daily cap. 0 = blocked on this plan, -1 = unlimited. */
  tier_limits_day: Record<string, number>;
  byok_enabled: boolean;
  queries_day: number;
  reasoning_queries_day: number;
  /** model_id → tier_number (1..4). */
  model_tiers: Record<string, number>;
}

export type ModelAccessVerdict =
  | { allowed: true; limit: number }
  | { allowed: false; reason: string; minimum_plan?: PlanId };

/** Human-readable lower bound for the plan that unlocks a given tier. */
const TIER_MIN_PLAN: Record<number, PlanId> = {
  1: "free",
  2: "free",
  3: "pro",
  4: "studio",
};

export async function fetchPlanAccess(
  authFetch: (input: RequestInfo, init?: RequestInit) => Promise<Response>,
): Promise<PlanAccessInfo | null> {
  try {
    const res = await authFetch("/api/plans/me");
    if (!res.ok) return null;
    return (await res.json()) as PlanAccessInfo;
  } catch {
    return null;
  }
}

/** Decide whether a model is usable on the user's current plan. */
export function checkModelAccess(
  modelId: string,
  access: PlanAccessInfo | null,
): ModelAccessVerdict {
  if (!access) return { allowed: true, limit: -1 };
  const tier = access.model_tiers[modelId];
  // Unknown model: be permissive — backend will enforce on actual call.
  if (!tier) return { allowed: true, limit: -1 };
  const limit = access.tier_limits_day[String(tier)] ?? 0;
  if (limit === 0) {
    const minimum = TIER_MIN_PLAN[tier];
    const minLabel: Record<PlanId, string> = {
      free: "Gratuito",
      pro: "Profesional",
      studio: "Estudio",
    };
    return {
      allowed: false,
      reason: minimum
        ? `Disponible en plan ${minLabel[minimum]} o superior`
        : "No disponible en tu plan",
      minimum_plan: minimum,
    };
  }
  return { allowed: true, limit };
}
