"""
Production startup configuration validation.

Exposes a single pure function `validate_production_config(settings)` that
raises `RuntimeError` (or `StartupConfigurationError`) when the application
is being started with insecure or incomplete configuration.

Called from the FastAPI lifespan handler in `app.main`, so failures crash
the process at startup BEFORE serving any request — fail fast, fail loud.

Why this lives in its own module:
- Pure function = trivial to unit-test (no event loop, no DB).
- Single source of truth — when a new prod-only invariant is needed,
  add it here and add a test in `tests/test_startup_validation.py`.

Production posture is gated by `app_debug=False` (not by env name), because
the env name can be typo'd (`prod`, `staging`, missing) without anyone
noticing — but APP_DEBUG=false is an explicit, auditable decision.
"""

from __future__ import annotations

import logging
import os

from app.config import Settings

logger = logging.getLogger(__name__)


class StartupConfigurationError(RuntimeError):
    """
    Raised when the application starts with a configuration that would allow
    security vulnerabilities in production.  Unlike generic RuntimeError,
    this is catchable specifically by callers that want to handle config errors
    (e.g. tests asserting against configuration invariants).
    """


# Substrings that indicate a JWT secret is still a placeholder, not a real one.
# Lowercased comparison.
_JWT_PLACEHOLDER_MARKERS: tuple[str, ...] = (
    "dev-only",
    "change",
    "placeholder",
    "example",
    "your-secret",
    "secret-here",
)


def _jwt_secret_is_placeholder(secret: str) -> bool:
    """Return True if `secret` looks like the shipped default, not a real one."""
    lowered = secret.lower()
    return any(marker in lowered for marker in _JWT_PLACEHOLDER_MARKERS)


def _is_production_posture(settings: Settings) -> bool:
    """Production posture = explicit non-debug. Env name is informational only.

    APP_DEBUG=false is the contract: anything that defaults to true (or is left
    unset) is treated as dev/staging and validation relaxes accordingly.
    """
    return settings.app_debug is False


def validate_production_config(settings: Settings) -> None:
    """
    Enforce production-grade configuration.

    Two tiers:

    Tier 1 — webhook secret strict mode (ANY environment):
      If beta_mode=False, BOTH webhook secrets are MANDATORY.
      In beta mode, missing secrets log WARNING (dev ergonomics).

    Tier 2 — production-posture checks (app_debug=False):
      JWT strength, BYOK key, provider secret coupling, CORS hardening,
      explicit BETA_MODE decision.

    Raises:
        StartupConfigurationError: when beta_mode=False and webhook secrets missing.
        RuntimeError: for production-only invariants.
    """
    # ── Tier 1: Webhook strict mode — based on beta_mode, not posture ─────
    if settings.beta_mode is False:
        missing: list[str] = []
        if not settings.culqi_webhook_secret:
            missing.append("CULQI_WEBHOOK_SECRET")
        if missing:
            raise StartupConfigurationError(
                f"Webhook strict mode (BETA_MODE=false): the following webhook "
                f"secrets are required but missing: {', '.join(missing)}. "
                f"Set them before starting the service, or set BETA_MODE=true "
                f"to allow permissive dev mode."
            )
    else:
        if not settings.culqi_webhook_secret:
            logger.warning(
                "CULQI_WEBHOOK_SECRET is empty — signature verification is permissive "
                "(BETA_MODE=true). Set CULQI_WEBHOOK_SECRET before going to production."
            )

    # ── Tier 2: Production posture invariants (app_debug=False) ───────────
    if not _is_production_posture(settings):
        return

    # 1) JWT secret must be a real, high-entropy value
    if _jwt_secret_is_placeholder(settings.jwt_secret):
        raise RuntimeError(
            "FATAL: JWT_SECRET is still a placeholder. "
            "Set a strong random secret in .env.production before starting "
            "(e.g. `python3 -c \"import secrets; print(secrets.token_urlsafe(64))\"`)."
        )
    if len(settings.jwt_secret) < 32:
        raise RuntimeError(
            "FATAL: JWT_SECRET is too short (< 32 chars). Use a 64-char random "
            "secret in production."
        )

    # 2) BYOK_ENCRYPTION_KEY mandatory in production
    if not (settings.byok_encryption_key or "").strip():
        raise RuntimeError(
            "FATAL: BYOK_ENCRYPTION_KEY is unset. BYOK LLM keys would be encrypted "
            "with a JWT_SECRET-derived fallback that breaks on JWT rotation. "
            "Generate with: python3 -c 'from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())'"
        )

    # 3) Culqi configured ⇒ webhook secret REQUIRED (forged webhooks → free upgrades)
    if settings.culqi_secret_key and not settings.culqi_webhook_secret:
        raise RuntimeError(
            "FATAL: Culqi is configured (culqi_secret_key set) but "
            "CULQI_WEBHOOK_SECRET is empty. Webhook HMAC verification would be "
            "SKIPPED, allowing forged webhooks to activate paid plans. "
            "Set CULQI_WEBHOOK_SECRET in .env.production."
        )

    # 4) MercadoPago coupling (kept defensive even though MP is deprecated in PE deploy)
    if settings.mp_access_token and not settings.mp_webhook_secret:
        raise RuntimeError(
            "FATAL: MercadoPago is configured (mp_access_token set) but "
            "MP_WEBHOOK_SECRET is empty. Webhook verification would be skipped. "
            "Either unset MP_ACCESS_TOKEN or set MP_WEBHOOK_SECRET."
        )

    # 5) CORS origins must NOT include http:// in production posture
    bad_origins = [
        origin for origin in settings.cors_origins
        if origin.startswith("http://") and "localhost" not in origin and "127.0.0.1" not in origin
    ]
    if bad_origins:
        raise RuntimeError(
            f"FATAL: CORS_ORIGINS contains insecure http:// entries in production: "
            f"{bad_origins}. Use https:// only."
        )

    # 6) BETA_MODE must be an explicit env-var decision in production
    # pydantic-settings provides a default of True; we check os.environ raw to detect
    # "no explicit decision" — an implicit default in prod is dangerous.
    if "BETA_MODE" not in os.environ:
        raise RuntimeError(
            "FATAL: BETA_MODE is not set in production. Refusing to start. "
            "Set BETA_MODE=true to enable beta access for all users, or "
            "BETA_MODE=false to enforce plan-based feature gating."
        )
