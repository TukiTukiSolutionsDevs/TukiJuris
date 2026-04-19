"""
Production startup configuration validation.

Exposes a single pure function `validate_production_config(settings)` that
raises `RuntimeError` when the application is being started in production
mode with insecure or incomplete configuration.

Called from the FastAPI lifespan handler in `app.main`, so failures crash
the process at startup BEFORE serving any request — fail fast, fail loud.

Why this lives in its own module:
- Pure function = trivial to unit-test (no event loop, no DB).
- Single source of truth — when a new prod-only invariant is needed,
  add it here and add a test in `tests/test_startup_validation.py`.
"""

from __future__ import annotations

from app.config import Settings


# Substrings that indicate a JWT secret is still a placeholder, not a real one.
# Lowercased comparison.
_JWT_PLACEHOLDER_MARKERS: tuple[str, ...] = (
    "dev-only",
    "change",
    "placeholder",
    "example",
)


def _jwt_secret_is_placeholder(secret: str) -> bool:
    """Return True if `secret` looks like the shipped default, not a real key."""
    lowered = secret.lower()
    return any(marker in lowered for marker in _JWT_PLACEHOLDER_MARKERS)


def validate_production_config(settings: Settings) -> None:
    """
    Enforce production-grade configuration. No-op in non-production envs.

    Raises:
        RuntimeError: with a clear message identifying the offending
            setting. Designed to be unrecoverable so the process exits
            and ops sees the error immediately.
    """
    if settings.app_env != "production":
        return

    # ── 1) JWT secret must be a real, high-entropy value ──────────────────
    if _jwt_secret_is_placeholder(settings.jwt_secret):
        raise RuntimeError(
            "FATAL: JWT_SECRET is still a development placeholder. "
            "Set a strong random secret in .env.production before starting "
            "(e.g. `python -c \"import secrets; print(secrets.token_urlsafe(48))\"`)."
        )

    # ── 2) If MercadoPago is configured, its webhook secret is MANDATORY ──
    # Without it, payment_service.MercadoPagoProvider.verify_webhook silently
    # falls back to "DEV MODE" and accepts unsigned webhooks → anyone could
    # forge a webhook to activate a paid plan without paying.
    if settings.mp_access_token and not settings.mp_webhook_secret:
        raise RuntimeError(
            "FATAL: MercadoPago is configured (mp_access_token set) but "
            "MP_WEBHOOK_SECRET is empty. Webhook HMAC verification would be "
            "SKIPPED, allowing forged webhooks to activate paid plans. "
            "Set MP_WEBHOOK_SECRET in .env.production."
        )

    # ── 3) Same rule for Culqi ────────────────────────────────────────────
    if settings.culqi_secret_key and not settings.culqi_webhook_secret:
        raise RuntimeError(
            "FATAL: Culqi is configured (culqi_secret_key set) but "
            "CULQI_WEBHOOK_SECRET is empty. Webhook HMAC verification would be "
            "SKIPPED, allowing forged webhooks to activate paid plans. "
            "Set CULQI_WEBHOOK_SECRET in .env.production."
        )

    # ── 4) BETA_MODE must be an explicit decision in production ───────────
    # pydantic-settings provides a default of True, so settings.beta_mode
    # always has a value. We check os.environ raw to detect "no explicit
    # decision" — an implicit default in prod is dangerous (silently grants
    # all features to all users).
    import os

    if "BETA_MODE" not in os.environ:
        raise RuntimeError(
            "FATAL: BETA_MODE is not set in production. Refusing to start. "
            "Set BETA_MODE=true to enable beta access for all users, or "
            "BETA_MODE=false to enforce plan-based feature gating."
        )
