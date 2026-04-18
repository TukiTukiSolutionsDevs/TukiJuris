"""Unit tests for TokenDenylist — Redis client mocked via AsyncMock.

Verifies: add/contains, TTL equality, missing key (False), prefix namespacing,
and default-prefix derivation from settings.redis_key_prefix.
"""

import uuid
from unittest.mock import AsyncMock

import pytest


# ---------------------------------------------------------------------------
# T-5.0 — add()
# ---------------------------------------------------------------------------


class TestTokenDenylistAdd:
    """add() stores the jti in Redis with the correct key and TTL."""

    @pytest.mark.asyncio
    async def test_add_calls_set_with_prefixed_key_and_ttl(self):
        from app.core.token_denylist import TokenDenylist

        redis = AsyncMock()
        denylist = TokenDenylist(redis, prefix="test:")
        jti = str(uuid.uuid4())

        await denylist.add(jti, ttl_seconds=300)

        redis.set.assert_awaited_once_with(f"test:{jti}", 1, ex=300)

    @pytest.mark.asyncio
    async def test_add_uses_configured_prefix(self):
        from app.core.token_denylist import TokenDenylist

        redis = AsyncMock()
        denylist = TokenDenylist(redis, prefix="myapp:deny:")

        await denylist.add("abc123", ttl_seconds=60)

        args = redis.set.call_args[0]
        assert args[0] == "myapp:deny:abc123"

    @pytest.mark.asyncio
    async def test_add_ttl_matches_parameter_exactly(self):
        from app.core.token_denylist import TokenDenylist

        redis = AsyncMock()
        denylist = TokenDenylist(redis, prefix="t:")

        await denylist.add("jti1", ttl_seconds=7200)

        redis.set.assert_awaited_once_with("t:jti1", 1, ex=7200)


# ---------------------------------------------------------------------------
# T-5.0 — contains()
# ---------------------------------------------------------------------------


class TestTokenDenylistContains:
    """contains() returns True/False based on Redis key existence."""

    @pytest.mark.asyncio
    async def test_returns_true_when_key_exists(self):
        from app.core.token_denylist import TokenDenylist

        redis = AsyncMock()
        redis.exists.return_value = 1
        denylist = TokenDenylist(redis, prefix="test:")
        jti = str(uuid.uuid4())

        result = await denylist.contains(jti)

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_key_missing(self):
        from app.core.token_denylist import TokenDenylist

        redis = AsyncMock()
        redis.exists.return_value = 0
        denylist = TokenDenylist(redis, prefix="test:")

        result = await denylist.contains("nonexistent-jti")

        assert result is False

    @pytest.mark.asyncio
    async def test_contains_uses_prefix_in_lookup_key(self):
        from app.core.token_denylist import TokenDenylist

        redis = AsyncMock()
        redis.exists.return_value = 0
        denylist = TokenDenylist(redis, prefix="prefix:")

        await denylist.contains("myjti")

        redis.exists.assert_awaited_once_with("prefix:myjti")

    @pytest.mark.asyncio
    async def test_contains_returns_bool_not_int(self):
        from app.core.token_denylist import TokenDenylist

        redis = AsyncMock()
        redis.exists.return_value = 1
        denylist = TokenDenylist(redis, prefix="t:")

        result = await denylist.contains("any")

        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# T-5.0 — prefix / default prefix from settings
# ---------------------------------------------------------------------------


class TestTokenDenylistPrefix:
    """Default prefix is derived from settings.redis_key_prefix when not provided."""

    @pytest.mark.asyncio
    async def test_default_prefix_uses_settings_redis_key_prefix(self):
        from app.core.token_denylist import TokenDenylist
        from app.config import settings

        redis = AsyncMock()
        redis.exists.return_value = 0
        denylist = TokenDenylist(redis)  # no explicit prefix

        await denylist.contains("testjti")

        expected_key = f"{settings.redis_key_prefix}denylist:testjti"
        redis.exists.assert_awaited_once_with(expected_key)

    @pytest.mark.asyncio
    async def test_explicit_prefix_overrides_settings(self):
        from app.core.token_denylist import TokenDenylist
        from app.config import settings

        redis = AsyncMock()
        redis.exists.return_value = 0
        custom_prefix = "custom:"
        denylist = TokenDenylist(redis, prefix=custom_prefix)

        await denylist.contains("jti")

        # Must NOT use the settings prefix
        expected_key = f"{custom_prefix}jti"
        redis.exists.assert_awaited_once_with(expected_key)
        settings_key = f"{settings.redis_key_prefix}denylist:jti"
        assert redis.exists.call_args[0][0] != settings_key or custom_prefix == f"{settings.redis_key_prefix}denylist:"
