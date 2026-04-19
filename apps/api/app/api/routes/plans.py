"""Public plans catalog endpoint.

GET /api/plans — no authentication required.
Returns all three subscription plans with pricing, features, and limits.
Response is cached for 1 hour via Cache-Control header.

Design decisions:
- Reuses PlanService.get_config() as the single read path (no direct PLANS import).
- Reuses compute_invoice_amounts() from invoice_pricing for IGV breakdown.
- FEATURE_LABELS inline (6 keys, v1 — extract if surface grows past ~15).
- display_name sourced from PlanConfig.display_name (canonical es-PE localization).
- limits.chat_per_day = None for unlimited (queries_day == -1 sentinel).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Response

from app.config import settings
from app.schemas.plans import PlanResponse, PlansListResponse
from app.services.invoice_pricing import compute_invoice_amounts
from app.services.plan_service import PlanService

router = APIRouter(prefix="/plans", tags=["plans"])

# ---------------------------------------------------------------------------
# FEATURE_LABELS — es-PE human-readable strings for PlanConfig.features keys.
# Kept inline for v1 (6 keys, no reuse yet). Insertion order matches
# ALL_FEATURE_KEYS tuple in config/plans.py so the emitted list is stable.
# ---------------------------------------------------------------------------
FEATURE_LABELS: dict[str, str] = {
    "chat": "Chat con IA legal",
    "pdf_export": "Exportar conversaciones a PDF",
    "file_upload": "Subir archivos (PDF, DOCX)",
    "byok_enabled": "Trae tu propia API key (BYOK)",
    "team_seats": "Asientos para tu equipo",
    "priority_support": "Soporte prioritario",
}

_CENTS = Decimal("0.01")
_PLAN_ORDER: tuple[str, ...] = ("free", "pro", "studio")


def _cents_to_pen(cents: int) -> Decimal:
    """Integer cents → Decimal(10,2) PEN. Same quantization as invoice_pricing."""
    from decimal import ROUND_HALF_UP

    return (Decimal(cents) / 100).quantize(_CENTS, ROUND_HALF_UP)


def _enabled_feature_labels(features: dict[str, bool]) -> list[str]:
    """Return human labels for feature flags set to True.

    Iterates FEATURE_LABELS insertion order so the list is deterministic.
    Unknown machine keys (future PlanConfig additions not yet mapped) are
    silently skipped — the unit test test_every_feature_key_has_a_label
    enforces we never ship that state to production.
    """
    return [FEATURE_LABELS[k] for k in FEATURE_LABELS if features.get(k)]


def _limits_for(queries_day: int) -> dict[str, Optional[int]]:
    """-1 sentinel → None (unlimited). Positive → integer cap."""
    return {"chat_per_day": None if queries_day == -1 else queries_day}


@router.get(
    "",
    response_model=PlansListResponse,
    summary="List available subscription plans",
    description=(
        "Public endpoint returning the full plan catalog with pricing, features, "
        "and usage limits. No authentication required. Cached for 1 hour."
    ),
)
async def get_plans(response: Response) -> PlansListResponse:
    """Return all subscription plans with computed IGV amounts."""
    # Cache aggressively — plans change at deploy time only, never at runtime.
    response.headers["Cache-Control"] = "public, max-age=3600"

    plans: list[PlanResponse] = []
    for plan_id in _PLAN_ORDER:
        cfg = PlanService.get_config(plan_id)
        amounts = compute_invoice_amounts(plan_id, seats_count=cfg.base_seats_included)

        plans.append(
            PlanResponse(
                id=plan_id,
                display_name=cfg.display_name,
                currency="PEN",
                base_price=_cents_to_pen(cfg.base_price_cents),
                seat_price=_cents_to_pen(cfg.seat_price_cents),
                base_seats_included=cfg.base_seats_included,
                subtotal_amount=amounts["subtotal_amount"],
                tax_amount=amounts["tax_amount"],
                total_amount=amounts["total_amount"],
                features=_enabled_feature_labels(cfg.features),
                limits=_limits_for(cfg.queries_day),
                byok_supported=cfg.byok_enabled,
            )
        )

    return PlansListResponse(
        plans=plans,
        beta_mode=settings.beta_mode,
        currency_default="PEN",
    )
