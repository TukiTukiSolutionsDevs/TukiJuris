/**
 * Plan definitions and display helpers — frontend side.
 *
 * Plan IDs (canonical, Sprint 2): free | pro | studio
 * Display names (es-PE): Gratuito | Profesional | Estudio
 *
 * This module is the ONLY place that maps plan IDs to display strings.
 * All UI copy that refers to plans MUST go through planDisplayName() —
 * never hardcode "Profesional" or "Estudio" in component JSX.
 */

export type PlanId = 'free' | 'pro' | 'studio';

// ---------------------------------------------------------------------------
// Display names (es-PE)
// ---------------------------------------------------------------------------

const DISPLAY_NAMES: Record<PlanId, string> = {
  free: 'Gratuito',
  pro: 'Profesional',
  studio: 'Estudio',
};

/**
 * Return the localised display name for a plan ID.
 * Falls back to 'Desconocido' for unrecognised IDs — never throws.
 */
export function planDisplayName(id: string): string {
  return DISPLAY_NAMES[id as PlanId] ?? 'Desconocido';
}

/**
 * Type guard — returns true if `s` is a valid canonical plan ID.
 */
export function isValidPlanId(s: string): s is PlanId {
  return s === 'free' || s === 'pro' || s === 'studio';
}

// ---------------------------------------------------------------------------
// Plan metadata (used for billing UI)
// ---------------------------------------------------------------------------

export interface PlanMeta {
  id: PlanId;
  displayName: string;
  basePriceCents: number;  // PEN integer cents
  priceSoles: string;      // formatted display (e.g. "S/ 70")
  seatPriceCents: number;
  baseSeatsIncluded: number;
}

export const PLAN_META: Record<PlanId, PlanMeta> = {
  free: {
    id: 'free',
    displayName: 'Gratuito',
    basePriceCents: 0,
    priceSoles: 'S/ 0',
    seatPriceCents: 0,
    baseSeatsIncluded: 1,
  },
  pro: {
    id: 'pro',
    displayName: 'Profesional',
    basePriceCents: 7000,
    priceSoles: 'S/ 70',
    seatPriceCents: 0,
    baseSeatsIncluded: 1,
  },
  studio: {
    id: 'studio',
    displayName: 'Estudio',
    basePriceCents: 29900,
    priceSoles: 'S/ 299',
    seatPriceCents: 4000,
    baseSeatsIncluded: 5,
  },
};
