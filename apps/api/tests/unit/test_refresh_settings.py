"""Tests for Settings.redis_key_prefix — T-1.0 RED.

Verifies that:
- redis_key_prefix has a sensible non-empty default.
- It can be overridden via REDIS_KEY_PREFIX env var.
- Auth/RT Redis keys correctly incorporate the prefix.
"""

import pytest

from app.config import Settings


class TestRedisKeyPrefix:
    """Given the Settings model, when redis_key_prefix is accessed."""

    def test_redis_key_prefix_has_default(self):
        """Default prefix must be 'tukijuris:'."""
        s = Settings()
        assert s.redis_key_prefix == "tukijuris:"

    def test_redis_key_prefix_overrideable_via_env(self, monkeypatch):
        """When REDIS_KEY_PREFIX env var is set, it must override the default."""
        monkeypatch.setenv("REDIS_KEY_PREFIX", "custom:")
        s = Settings()
        assert s.redis_key_prefix == "custom:"

    def test_prefix_is_non_empty(self):
        """Prefix must be non-empty to avoid Redis key collisions across environments."""
        s = Settings()
        assert len(s.redis_key_prefix) > 0

    def test_auth_rt_key_composition(self):
        """Auth RT Redis key must incorporate the prefix + 'rt:family:' segment."""
        s = Settings()
        user_id = "abc-123"
        key = f"{s.redis_key_prefix}rt:family:{user_id}"
        assert key.startswith("tukijuris:")
        assert "rt:family:" in key
        assert user_id in key


class TestAccessTokenExpiry:
    """access_token_expire_minutes must default to 15 (spec-compliant short TTL)."""

    def test_access_token_expire_minutes_default_is_15(self):
        """Default must be 15 minutes — NOT 1440 (24 h) which is insecure."""
        s = Settings()
        assert s.access_token_expire_minutes == 15, (
            f"Expected 15 min default, got {s.access_token_expire_minutes}. "
            "Set ACCESS_TOKEN_EXPIRE_MINUTES env var to override in local dev."
        )

    def test_access_token_expire_minutes_overrideable(self, monkeypatch):
        """ACCESS_TOKEN_EXPIRE_MINUTES env var must override the default."""
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        s = Settings()
        assert s.access_token_expire_minutes == 60
