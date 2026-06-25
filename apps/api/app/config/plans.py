"""
Canonical plan definitions — single source of truth for TukiJuris plans.

IMPORTANT: This module MUST NOT import from app.services, app.models, or app.api.
It is a pure leaf module: only stdlib + dataclasses. This keeps it unit-testable
without fixtures and import-safe in migration context.

Plan IDs (final, Sprint 2): free | pro | studio
Legacy DB values (pre-007 migration): base -> pro, enterprise -> studio
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

PlanId = Literal["free", "pro", "studio"]

FeatureKey = Literal[
    "chat",
    "pdf_export",
    "file_upload",
    "byok_enabled",
    "team_seats",
    "priority_support",
]

# ---------------------------------------------------------------------------
# Plan config dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlanConfig:
    """Immutable plan descriptor.

    frozen=True: zero-overhead, hashable, safe to use as dict key.
    No Pydantic here — no validation needed for hardcoded values,
    and avoids importing Pydantic in a hot/shared path.
    """

    id: PlanId
    display_name: str                   # localized display name (es-PE)
    features: dict[FeatureKey, bool]    # authoritative feature matrix
    queries_day: int                    # daily NORMAL query cap; -1 = unlimited
    reasoning_queries_day: int          # daily REASONING query cap; -1 = unlimited
    byok_enabled: bool
    base_price_cents: int               # 0 for free; PEN cents
    # Recommended default model for users on this plan who haven't picked a
    # preference yet. Replaces the prior "first FREE_TIER_MODELS with a key"
    # fallback chain — that one silently swapped paid model choices for free
    # ones and confused users. Now each plan declares its default explicitly.
    default_model: str = "groq/llama-3.3-70b-versatile"
    seat_price_cents: int = 0           # per-seat overage (studio only)
    base_seats_included: int = 1        # seats included before overage


# ---------------------------------------------------------------------------
# PLANS — authoritative plan registry
# ---------------------------------------------------------------------------

PLANS: dict[PlanId, PlanConfig] = {
    "free": PlanConfig(
        id="free",
        display_name="Gratuito",
        features={
            "chat": True,
            "pdf_export": False,
            "file_upload": False,
            "byok_enabled": False,
            "team_seats": False,
            "priority_support": False,
        },
        queries_day=4,
        reasoning_queries_day=1,
        byok_enabled=False,
        base_price_cents=0,
        # Free plan default: Groq llama 70B — gratis vía platform key, sin
        # quemar saldo OpenAI. Tier 1 (sin restricción de cuota).
        default_model="groq/llama-3.3-70b-versatile",
    ),
    "pro": PlanConfig(
        id="pro",
        display_name="Profesional",
        features={
            "chat": True,
            "pdf_export": True,
            "file_upload": True,
            # BYOK no es self-service — solo plan Empresarial (contacto comercial).
            "byok_enabled": False,
            "team_seats": False,
            "priority_support": True,
        },
        queries_day=-1,
        reasoning_queries_day=-1,
        byok_enabled=False,
        base_price_cents=7000,   # S/ 70.00
        # Pro plan default: gpt-5.5 vía codex-proxy — mejor calidad
        # jurídica + costo accesible. Tier 2 (ilimitado en este plan).
        default_model="openai/gpt-5.5",
    ),
    "studio": PlanConfig(
        id="studio",
        display_name="Estudio",
        features={
            "chat": True,
            "pdf_export": True,
            "file_upload": True,
            # BYOK no es self-service — solo plan Empresarial (contacto comercial).
            "byok_enabled": False,
            "team_seats": True,
            "priority_support": True,
        },
        queries_day=-1,
        reasoning_queries_day=-1,
        byok_enabled=False,
        base_price_cents=29900,  # S/ 299.00
        seat_price_cents=4000,   # S/ 40.00 per extra seat
        base_seats_included=5,
        # Studio plan default: gpt-5.4-mini — 400K contexto, thinking mode,
        # ideal para análisis complejos multi-paso. Tier 2 (ilimitado).
        default_model="openai/gpt-5.4-mini",
    ),
}

# ---------------------------------------------------------------------------
# Beta hard limits — enforced regardless of BETA_MODE=True
# ---------------------------------------------------------------------------

BETA_HARD_LIMITS: dict[str, object] = {
    # Free tier daily caps are always enforced — even in beta.
    # 4 normal + 1 reasoning = 5 total queries/day.
    "free_queries_day": 4,
    "free_reasoning_queries_day": 1,
    # BYOK remains restricted to paid plans — even in beta.
    "byok_paid_only": True,
}

# ---------------------------------------------------------------------------
# Convenience accessors
# ---------------------------------------------------------------------------

ALL_FEATURE_KEYS: tuple[FeatureKey, ...] = (
    "chat",
    "pdf_export",
    "file_upload",
    "byok_enabled",
    "team_seats",
    "priority_support",
)
