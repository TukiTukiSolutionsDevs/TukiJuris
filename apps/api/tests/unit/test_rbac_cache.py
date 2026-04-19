"""Unit tests for RBAC PermissionCache — RED phase (T2.1).

Tests use a mock Redis client (no real Redis required).
All tests fail until app/rbac/cache.py is created.
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rbac.cache import PermissionCache

REDIS_PREFIX = "tukijuris:rbac:perms:"
TTL = 3600


def make_redis(*, get_return=None, get_side_effect=None) -> AsyncMock:
    """Build a minimal async Redis mock."""
    redis = AsyncMock()
    if get_side_effect is not None:
        redis.get.side_effect = get_side_effect
    else:
        redis.get.return_value = get_return
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.scan = AsyncMock(return_value=(0, []))
    return redis


class TestPermissionCacheKey:
    def test_key_format(self):
        cache = PermissionCache(redis=make_redis())
        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        assert cache._key(user_id) == f"{REDIS_PREFIX}{user_id}"

    def test_key_varies_by_user(self):
        cache = PermissionCache(redis=make_redis())
        u1, u2 = uuid.uuid4(), uuid.uuid4()
        assert cache._key(u1) != cache._key(u2)


class TestPermissionCacheGet:
    async def test_returns_none_on_cache_miss(self):
        redis = make_redis(get_return=None)
        cache = PermissionCache(redis=redis)
        result = await cache.get_permissions(uuid.uuid4())
        assert result is None

    async def test_returns_set_on_cache_hit(self):
        perms = ["users:read", "cases:read", "documents:read"]
        redis = make_redis(get_return=json.dumps(perms).encode())
        cache = PermissionCache(redis=redis)
        result = await cache.get_permissions(uuid.uuid4())
        assert result == set(perms)

    async def test_calls_redis_get_with_correct_key(self):
        redis = make_redis(get_return=None)
        cache = PermissionCache(redis=redis)
        user_id = uuid.uuid4()
        await cache.get_permissions(user_id)
        redis.get.assert_called_once_with(f"{REDIS_PREFIX}{user_id}")

    async def test_returns_none_on_redis_error(self):
        """Fail-open: Redis errors must NOT raise, return None instead."""
        redis = make_redis(get_side_effect=Exception("Redis down"))
        cache = PermissionCache(redis=redis)
        result = await cache.get_permissions(uuid.uuid4())
        assert result is None

    async def test_deserializes_json_list_to_set(self):
        perms = ["billing:read", "billing:update"]
        redis = make_redis(get_return=json.dumps(perms))
        cache = PermissionCache(redis=redis)
        result = await cache.get_permissions(uuid.uuid4())
        assert isinstance(result, set)
        assert result == {"billing:read", "billing:update"}


class TestPermissionCacheSet:
    async def test_stores_permissions_as_json(self):
        redis = make_redis()
        cache = PermissionCache(redis=redis)
        user_id = uuid.uuid4()
        perms = {"users:read", "cases:read"}
        await cache.set_permissions(user_id, perms)
        redis.set.assert_called_once()
        call_args = redis.set.call_args
        key = call_args[0][0]
        stored = call_args[0][1]
        assert key == f"{REDIS_PREFIX}{user_id}"
        assert set(json.loads(stored)) == perms

    async def test_stores_with_correct_ttl(self):
        redis = make_redis()
        cache = PermissionCache(redis=redis)
        await cache.set_permissions(uuid.uuid4(), {"users:read"})
        call_kwargs = redis.set.call_args[1]
        assert call_kwargs.get("ex") == TTL

    async def test_does_not_raise_on_redis_error(self):
        """Fail-open: set errors must NOT propagate."""
        redis = make_redis()
        redis.set.side_effect = Exception("Redis down")
        cache = PermissionCache(redis=redis)
        # Must not raise
        await cache.set_permissions(uuid.uuid4(), {"users:read"})

    async def test_empty_set_stored(self):
        redis = make_redis()
        cache = PermissionCache(redis=redis)
        await cache.set_permissions(uuid.uuid4(), set())
        redis.set.assert_called_once()


class TestPermissionCacheInvalidate:
    async def test_invalidate_deletes_correct_key(self):
        redis = make_redis()
        cache = PermissionCache(redis=redis)
        user_id = uuid.uuid4()
        await cache.invalidate(user_id)
        redis.delete.assert_called_once_with(f"{REDIS_PREFIX}{user_id}")

    async def test_invalidate_does_not_raise_on_redis_error(self):
        redis = make_redis()
        redis.delete.side_effect = Exception("Redis down")
        cache = PermissionCache(redis=redis)
        await cache.invalidate(uuid.uuid4())  # Must not raise

    async def test_invalidate_all_scans_and_deletes(self):
        key1 = f"{REDIS_PREFIX}{uuid.uuid4()}".encode()
        key2 = f"{REDIS_PREFIX}{uuid.uuid4()}".encode()
        redis = make_redis()
        # scan returns cursor=0 (done), two keys
        redis.scan = AsyncMock(return_value=(0, [key1, key2]))
        cache = PermissionCache(redis=redis)
        await cache.invalidate_all()
        redis.scan.assert_called_once()
        redis.delete.assert_called_once_with(key1, key2)

    async def test_invalidate_all_no_keys_does_not_call_delete(self):
        redis = make_redis()
        redis.scan = AsyncMock(return_value=(0, []))
        cache = PermissionCache(redis=redis)
        await cache.invalidate_all()
        redis.delete.assert_not_called()

    async def test_invalidate_all_does_not_raise_on_redis_error(self):
        redis = make_redis()
        redis.scan.side_effect = Exception("Redis down")
        cache = PermissionCache(redis=redis)
        await cache.invalidate_all()  # Must not raise
