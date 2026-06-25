"""Admin configuration introspection.

Read-only endpoints that expose hardcoded config matrices (plans, models,
limits, features, OAuth, security, observability) so the admin UI can
render them without having to mirror the values in TypeScript.

All endpoints require platform-admin scope. They never expose secrets —
provider keys are read from .env presence only, not their values.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.config.plans import PLANS, BETA_HARD_LIMITS, ALL_FEATURE_KEYS
from app.core.rate_limiter import RATE_LIMIT_TIERS
from app.models.user import User
from app.rbac.dependencies import require_permission
from app.services.llm_adapter import MODEL_TIERS, FREE_TIER_MODELS

router = APIRouter(prefix="/admin/config", tags=["admin-config"])


def _has_env(*names: str) -> bool:
    """True if all named env vars are set to a non-empty string."""
    return all(bool(os.environ.get(n, "").strip()) for n in names)


@router.get("/models")
async def get_models_config(
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    """Return the LLM model tier matrix + free tier list + defaults.

    Tier ranges (as documented in llm_adapter.py):
      tier 1: economic   ($0.001-0.01/query)
      tier 2: standard   ($0.01-0.03/query)
      tier 3: premium    ($0.03-0.07/query)
      tier 4: ultra      ($0.08-0.12/query)
    """
    tier_labels = {
        1: "Económico",
        2: "Standard",
        3: "Premium",
        4: "Ultra",
    }

    # Group models by tier
    by_tier: dict[int, list[str]] = {1: [], 2: [], 3: [], 4: []}
    for model_id, tier in MODEL_TIERS.items():
        by_tier.setdefault(tier, []).append(model_id)
    for tier in by_tier:
        by_tier[tier].sort()

    return {
        "tiers": [
            {
                "tier": t,
                "label": tier_labels.get(t, f"Tier {t}"),
                "models": by_tier.get(t, []),
            }
            for t in sorted(by_tier.keys())
        ],
        "free_tier_models": FREE_TIER_MODELS,
        "default_provider": os.environ.get("DEFAULT_LLM_PROVIDER", "openai"),
        "default_model": os.environ.get("DEFAULT_LLM_MODEL", "gpt-4o-mini"),
        "total_models": len(MODEL_TIERS),
    }


@router.get("/plans")
async def get_plans_config(
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    """Return the canonical plan registry.

    Same data as /api/plans but as admin-facing detail (raw cents,
    features matrix, beta hard limits).
    """
    plans: list[dict[str, Any]] = []
    for plan_id, cfg in PLANS.items():
        plans.append({
            "id": cfg.id,
            "display_name": cfg.display_name,
            "features": dict(cfg.features),
            "queries_day": cfg.queries_day,
            "reasoning_queries_day": cfg.reasoning_queries_day,
            "byok_enabled": cfg.byok_enabled,
            "base_price_cents": cfg.base_price_cents,
            "seat_price_cents": cfg.seat_price_cents,
            "base_seats_included": cfg.base_seats_included,
        })

    return {
        "plans": plans,
        "all_feature_keys": list(ALL_FEATURE_KEYS),
        "beta_hard_limits": dict(BETA_HARD_LIMITS),
        "beta_mode": os.environ.get("BETA_MODE", "true").lower() == "true",
    }


@router.get("/limits")
async def get_limits_config(
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    """Return rate limits + tier limits + upload caps.

    Source of truth:
      - core/rate_limiter.py:RATE_LIMIT_TIERS
      - services/usage.py:_TIER_LIMITS_DAY
      - api/routes/upload.py:MAX_UPLOAD_BYTES
    """
    # _TIER_LIMITS_DAY is private; mirror it here to avoid importing private.
    # If it drifts, update both. (Could be moved to config later.)
    from app.services.usage import _TIER_LIMITS_DAY

    return {
        "rate_limits": [
            {
                "plan": plan,
                "requests_per_minute": rpm,
                "requests_per_day": rpd,
            }
            for plan, (rpm, rpd) in RATE_LIMIT_TIERS.items()
        ],
        "tier_limits_per_day": {
            plan: {f"tier_{t}": v for t, v in tiers.items()}
            for plan, tiers in _TIER_LIMITS_DAY.items()
        },
        "upload": {
            "max_bytes": int(os.environ.get("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024))),
            "max_mb": int(os.environ.get("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024))) // (1024 * 1024),
            "accepted_formats": ["pdf", "docx"],
        },
        "auth": {
            "access_token_minutes": int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15")),
            "refresh_token_days": int(os.environ.get("REFRESH_TOKEN_TTL_DAYS", "30")),
            "login_rate_window_seconds": 900,
            "oauth_state_max_age_seconds": 600,
        },
    }


@router.get("/oauth")
async def get_oauth_config(
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    """Return OAuth provider status (configured or not — values never exposed)."""
    return {
        "providers": [
            {
                "id": "google",
                "name": "Google",
                "configured": _has_env("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"),
                "callback_url": "/api/auth/oauth/google/callback",
            },
            {
                "id": "microsoft",
                "name": "Microsoft",
                "configured": _has_env("MICROSOFT_CLIENT_ID", "MICROSOFT_CLIENT_SECRET"),
                "callback_url": "/api/auth/oauth/microsoft/callback",
            },
        ],
    }


@router.get("/security")
async def get_security_config(
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    """Return security/encryption configuration status."""
    jwt_secret_set = bool(os.environ.get("JWT_SECRET", "").strip())
    byok_key_set = bool(os.environ.get("BYOK_ENCRYPTION_KEY", "").strip())

    return {
        "jwt": {
            "algorithm": os.environ.get("JWT_ALGORITHM", "HS256"),
            "secret_configured": jwt_secret_set,
            "access_token_minutes": int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15")),
            "refresh_token_days": int(os.environ.get("REFRESH_TOKEN_TTL_DAYS", "30")),
        },
        "byok": {
            "encryption_key_configured": byok_key_set,
            "using_jwt_fallback": (not byok_key_set) and jwt_secret_set,
            "warning": (
                "BYOK_ENCRYPTION_KEY no está seteada — usando fallback derivado de JWT_SECRET. "
                "Insegura para producción."
            ) if not byok_key_set else None,
        },
        "rate_limit_window_seconds": 900,
    }


@router.get("/observability")
async def get_observability_config(
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    """Return observability/monitoring status."""
    sentry = os.environ.get("SENTRY_DSN", "").strip()
    return {
        "sentry": {
            "configured": bool(sentry),
            "dsn_host": sentry.split("@")[-1].split("/")[0] if sentry and "@" in sentry else None,
        },
        "logs": {
            "level": os.environ.get("LOG_LEVEL", "INFO"),
            "format": os.environ.get("LOG_FORMAT", "text"),
        },
    }


@router.get("/payments")
async def get_payments_config(
    _: User = Depends(require_permission("billing:read")),
) -> dict[str, Any]:
    """Return payment provider status (configured or not — never exposes secret values)."""
    return {
        "providers": [
            {
                "id": "culqi",
                "name": "Culqi",
                "configured": _has_env("CULQI_PUBLIC_KEY", "CULQI_SECRET_KEY"),
                "webhook_secret_configured": _has_env("CULQI_WEBHOOK_SECRET"),
                "webhook_url": "/api/billing/webhook/culqi",
            },
            {
                "id": "mercado_pago",
                "name": "Mercado Pago",
                "configured": _has_env("MP_ACCESS_TOKEN", "MP_PUBLIC_KEY"),
                "webhook_secret_configured": _has_env("MP_WEBHOOK_SECRET"),
                "webhook_url": "/api/billing/webhook/mp",
            },
        ],
        "beta_mode": os.environ.get("BETA_MODE", "true").lower() == "true",
    }
