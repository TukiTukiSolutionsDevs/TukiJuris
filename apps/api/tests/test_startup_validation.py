"""
Tests for production startup configuration validation.

The application must REFUSE to start in production mode if critical
secrets are missing or still set to their development defaults. This
prevents shipping a publicly-accessible API with insecure defaults.

Tested invariants:
- In `development`, no validation runs (devs can use defaults freely).
- In `production`, JWT_SECRET cannot be the placeholder.
- In `production`, if a payment provider is configured, its webhook
  secret is required (otherwise forged webhooks would be accepted).
- In `production`, full config passes silently.

These are pure-function tests — no event loop, no DB, no HTTP. Fast.
"""

import pytest

from app.config import Settings
from app.core.startup_validation import validate_production_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _prod_settings(**overrides) -> Settings:
    """
    Build a Settings instance scoped to production with sane defaults.

    `_env_file=None` isolates the test from any local .env file so that
    APP_ENV / JWT_SECRET in the dev environment cannot bleed into tests.
    """
    base = {
        "app_env": "production",
        "jwt_secret": "real-strong-production-secret-32chars-abcdef",
        "mp_access_token": "",
        "mp_webhook_secret": "",
        "culqi_secret_key": "",
        "culqi_webhook_secret": "",
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Environment gating — only production triggers validation
# ---------------------------------------------------------------------------


def test_development_skips_all_checks():
    """In development, the placeholder JWT secret is allowed."""
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        app_env="development",
        jwt_secret="dev-only-secret-change-in-production",
    )
    validate_production_config(settings)  # must not raise


def test_staging_environment_skips_checks():
    """Any non-production environment is exempt (e.g. 'staging', 'test')."""
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        app_env="staging",
        jwt_secret="dev-only-change-me",
    )
    validate_production_config(settings)  # must not raise


# ---------------------------------------------------------------------------
# JWT_SECRET checks
# ---------------------------------------------------------------------------


def test_prod_with_default_jwt_secret_raises():
    """Production must reject the shipped placeholder secret."""
    settings = _prod_settings(jwt_secret="dev-only-secret-change-in-production")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_production_config(settings)


def test_prod_with_change_keyword_in_jwt_secret_raises():
    """Any secret containing the word 'change' is treated as placeholder."""
    settings = _prod_settings(jwt_secret="please-change-this-before-prod")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_production_config(settings)


def test_prod_with_strong_jwt_secret_passes():
    """A real high-entropy secret is accepted."""
    settings = _prod_settings(jwt_secret="9f8e7d6c5b4a3210fedcba9876543210abcdef00")
    validate_production_config(settings)  # must not raise


# ---------------------------------------------------------------------------
# MercadoPago webhook secret coupling
# ---------------------------------------------------------------------------


def test_prod_without_mp_token_skips_mp_webhook_check():
    """If MercadoPago isn't configured, no mp_webhook_secret is needed."""
    settings = _prod_settings(mp_access_token="", mp_webhook_secret="")
    validate_production_config(settings)  # must not raise


def test_prod_with_mp_token_but_missing_webhook_secret_raises():
    """Configured MP without webhook secret = unsigned webhook acceptance."""
    settings = _prod_settings(
        mp_access_token="APP_USR-12345-67890",
        mp_webhook_secret="",
    )
    with pytest.raises(RuntimeError, match="MP_WEBHOOK_SECRET"):
        validate_production_config(settings)


def test_prod_with_full_mp_config_passes():
    """Token + webhook secret is the safe configuration."""
    settings = _prod_settings(
        mp_access_token="APP_USR-12345",
        mp_webhook_secret="mp-real-hmac-secret-9876543210",
    )
    validate_production_config(settings)


# ---------------------------------------------------------------------------
# Culqi webhook secret coupling
# ---------------------------------------------------------------------------


def test_prod_without_culqi_key_skips_culqi_webhook_check():
    """If Culqi isn't configured, no culqi_webhook_secret is needed."""
    settings = _prod_settings(culqi_secret_key="", culqi_webhook_secret="")
    validate_production_config(settings)


def test_prod_with_culqi_key_but_missing_webhook_secret_raises():
    """Configured Culqi without webhook secret = same risk as MP case."""
    settings = _prod_settings(
        culqi_secret_key="sk_live_abcdef1234567890",
        culqi_webhook_secret="",
    )
    with pytest.raises(RuntimeError, match="CULQI_WEBHOOK_SECRET"):
        validate_production_config(settings)


def test_prod_with_full_culqi_config_passes():
    settings = _prod_settings(
        culqi_secret_key="sk_live_abcdef",
        culqi_webhook_secret="culqi-real-hmac-secret-1234567890",
    )
    validate_production_config(settings)


# ---------------------------------------------------------------------------
# Full integration + ordering
# ---------------------------------------------------------------------------


def test_prod_with_full_dual_provider_config_passes():
    """Both providers fully configured — common production scenario."""
    settings = _prod_settings(
        mp_access_token="APP_USR-12345",
        mp_webhook_secret="mp-hmac-secret",
        culqi_secret_key="sk_live_abc",
        culqi_webhook_secret="culqi-hmac-secret",
    )
    validate_production_config(settings)


def test_prod_jwt_failure_takes_precedence_over_payment():
    """JWT_SECRET is checked first — its error surfaces even if payment is also broken."""
    settings = _prod_settings(
        jwt_secret="please-change-me",
        mp_access_token="APP_USR-x",
        mp_webhook_secret="",  # also broken
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_production_config(settings)
