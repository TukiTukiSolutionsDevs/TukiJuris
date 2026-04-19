"""
Webhook strict-mode startup validation tests (AC7, AC8, AC9).

Verifies that:
  - AC7: beta_mode=False + empty mp_webhook_secret → StartupConfigurationError
  - AC8: beta_mode=False + empty culqi_webhook_secret → StartupConfigurationError
  - AC8b: beta_mode=False + BOTH secrets missing → error lists BOTH
  - AC9: beta_mode=True + empty secrets → WARNING logged, no exception

These are pure-function tests — no event loop, no DB, no HTTP. Fast.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/integration/test_webhook_strict_mode.py -v
"""

import logging

import pytest

from app.config import Settings
from app.core.startup_validation import StartupConfigurationError, validate_production_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _settings(beta_mode: bool, **overrides) -> Settings:
    """
    Build a Settings instance with app_env=development so the existing
    JWT/production checks don't interfere. The beta_mode check is independent
    of app_env — it fires in any environment.
    """
    base: dict = {
        "app_env": "development",
        "mp_webhook_secret": "",
        "culqi_webhook_secret": "",
        "beta_mode": beta_mode,
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# AC7 — beta_mode=False + missing MP webhook secret
# ---------------------------------------------------------------------------


class TestStrictModeProductionFailures:
    def test_beta_false_missing_mp_secret_raises(self):
        """AC7: beta_mode=False + empty mp_webhook_secret must raise StartupConfigurationError."""
        s = _settings(beta_mode=False, mp_webhook_secret="", culqi_webhook_secret="real-culqi-secret")
        with pytest.raises(StartupConfigurationError, match="MP_WEBHOOK_SECRET"):
            validate_production_config(s)

    def test_beta_false_missing_culqi_secret_raises(self):
        """AC8: beta_mode=False + empty culqi_webhook_secret must raise StartupConfigurationError."""
        s = _settings(beta_mode=False, mp_webhook_secret="real-mp-secret", culqi_webhook_secret="")
        with pytest.raises(StartupConfigurationError, match="CULQI_WEBHOOK_SECRET"):
            validate_production_config(s)

    def test_beta_false_both_missing_lists_all_in_error(self):
        """AC7+AC8: error message must list BOTH missing secrets when both absent."""
        s = _settings(beta_mode=False, mp_webhook_secret="", culqi_webhook_secret="")
        with pytest.raises(StartupConfigurationError) as exc_info:
            validate_production_config(s)
        msg = str(exc_info.value)
        assert "MP_WEBHOOK_SECRET" in msg
        assert "CULQI_WEBHOOK_SECRET" in msg

    def test_beta_false_both_secrets_set_no_raise(self):
        """beta_mode=False with both secrets configured must NOT raise."""
        s = _settings(
            beta_mode=False,
            mp_webhook_secret="real-mp-hmac-secret",
            culqi_webhook_secret="real-culqi-hmac-secret",
        )
        validate_production_config(s)  # must not raise


# ---------------------------------------------------------------------------
# AC9 — beta_mode=True + missing secrets → warning only
# ---------------------------------------------------------------------------


class TestDevModeWarnings:
    def test_beta_true_missing_secrets_does_not_raise(self):
        """AC9: beta_mode=True + empty secrets must NOT raise."""
        s = _settings(beta_mode=True, mp_webhook_secret="", culqi_webhook_secret="")
        validate_production_config(s)  # must not raise

    def test_beta_true_missing_mp_secret_logs_warning(self, caplog):
        """AC9: beta_mode=True + empty mp_webhook_secret must log a WARNING."""
        s = _settings(beta_mode=True, mp_webhook_secret="", culqi_webhook_secret="")
        with caplog.at_level(logging.WARNING, logger="app.core.startup_validation"):
            validate_production_config(s)
        warning_msgs = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        assert any("MP_WEBHOOK_SECRET" in m for m in warning_msgs), (
            f"Expected warning about MP_WEBHOOK_SECRET, got: {warning_msgs}"
        )

    def test_beta_true_missing_culqi_secret_logs_warning(self, caplog):
        """AC9: beta_mode=True + empty culqi_webhook_secret must log a WARNING."""
        s = _settings(beta_mode=True, mp_webhook_secret="", culqi_webhook_secret="")
        with caplog.at_level(logging.WARNING, logger="app.core.startup_validation"):
            validate_production_config(s)
        warning_msgs = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        assert any("CULQI_WEBHOOK_SECRET" in m for m in warning_msgs), (
            f"Expected warning about CULQI_WEBHOOK_SECRET, got: {warning_msgs}"
        )

    def test_beta_true_with_secrets_no_warning(self, caplog):
        """beta_mode=True + both secrets set — no warnings needed."""
        s = _settings(
            beta_mode=True,
            mp_webhook_secret="real-mp-secret",
            culqi_webhook_secret="real-culqi-secret",
        )
        with caplog.at_level(logging.WARNING, logger="app.core.startup_validation"):
            validate_production_config(s)
        webhook_warnings = [
            r for r in caplog.records
            if r.levelno == logging.WARNING
            and ("MP_WEBHOOK_SECRET" in r.message or "CULQI_WEBHOOK_SECRET" in r.message)
        ]
        assert not webhook_warnings, f"Unexpected warnings: {webhook_warnings}"


# ---------------------------------------------------------------------------
# Regression: existing production checks unaffected
# ---------------------------------------------------------------------------


def test_existing_production_jwt_check_still_works(monkeypatch):
    """Existing production JWT validation must still fire (no regression)."""
    monkeypatch.setenv("BETA_MODE", "true")
    s = Settings(
        _env_file=None,  # type: ignore[call-arg]
        app_env="production",
        jwt_secret="dev-only-secret-change-in-production",
        beta_mode=True,
        mp_webhook_secret="real-mp",
        culqi_webhook_secret="real-culqi",
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_production_config(s)
