"""Unit tests for RBAC dependencies — RED phase (T3.1).

Tests the require_permission factory and get_user_permissions_dep.
All tests use mocked DB, Redis, and User — no real infrastructure required.
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_user(user_id: uuid.UUID | None = None) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = user_id or uuid.uuid4()
    user.is_active = True
    return user


def make_redis(cached_perms: list[str] | None = None) -> AsyncMock:
    """Redis mock — optionally returns a JSON-encoded permission list on get()."""
    redis = AsyncMock()
    if cached_perms is not None:
        redis.get = AsyncMock(return_value=json.dumps(cached_perms).encode())
    else:
        redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    return redis


def make_db(roles=None) -> AsyncMock:
    """DB mock — optionally returns role mocks from execute()."""
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = roles or []
    db.execute = AsyncMock(return_value=result_mock)
    return db


# ---------------------------------------------------------------------------
# T3.1 — require_permission factory
# ---------------------------------------------------------------------------


class TestRequirePermission:
    async def test_allows_user_with_single_permission(self):
        from app.rbac.dependencies import require_permission

        user = make_user()
        redis = make_redis(cached_perms=["users:read", "cases:read"])
        db = make_db()

        dep = require_permission("users:read")
        result = await dep(current_user=user, db=db, redis=redis)
        assert result is user

    async def test_raises_403_when_permission_missing(self):
        from app.rbac.dependencies import require_permission

        user = make_user()
        redis = make_redis(cached_perms=["cases:read"])
        db = make_db()

        dep = require_permission("users:delete")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=user, db=db, redis=redis)
        assert exc_info.value.status_code == 403

    async def test_403_detail_message(self):
        from app.rbac.dependencies import require_permission

        dep = require_permission("users:delete")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=make_user(), db=make_db(), redis=make_redis())
        assert exc_info.value.detail == "Insufficient permissions"

    async def test_allows_when_all_multiple_permissions_present(self):
        from app.rbac.dependencies import require_permission

        user = make_user()
        redis = make_redis(cached_perms=["users:read", "cases:read", "billing:read"])
        db = make_db()

        dep = require_permission("users:read", "cases:read")
        result = await dep(current_user=user, db=db, redis=redis)
        assert result is user

    async def test_raises_403_when_only_partial_permissions_present(self):
        from app.rbac.dependencies import require_permission

        user = make_user()
        redis = make_redis(cached_perms=["users:read"])  # missing users:delete
        db = make_db()

        dep = require_permission("users:read", "users:delete")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=user, db=db, redis=redis)
        assert exc_info.value.status_code == 403

    async def test_no_permissions_required_always_passes(self):
        """require_permission() with no args → always allowed."""
        from app.rbac.dependencies import require_permission

        user = make_user()
        redis = make_redis(cached_perms=[])
        db = make_db()

        dep = require_permission()
        result = await dep(current_user=user, db=db, redis=redis)
        assert result is user

    async def test_returns_the_current_user_on_success(self):
        from app.rbac.dependencies import require_permission

        user_id = uuid.uuid4()
        user = make_user(user_id)
        redis = make_redis(cached_perms=["reports:read"])
        db = make_db()

        dep = require_permission("reports:read")
        result = await dep(current_user=user, db=db, redis=redis)
        assert result.id == user_id

    async def test_cache_miss_falls_back_to_db(self):
        """Cache miss (redis.get returns None) → DB query → still works."""
        from app.rbac.dependencies import require_permission

        user = make_user()
        redis = make_redis(cached_perms=None)  # cache miss

        # Simulate DB returning a role with users:read
        rp = MagicMock()
        rp.permission.resource = "users"
        rp.permission.action = "read"
        role = MagicMock()
        role.role_permissions = [rp]
        db = make_db(roles=[role])

        dep = require_permission("users:read")
        result = await dep(current_user=user, db=db, redis=redis)
        assert result is user

    async def test_raises_403_on_db_miss_too(self):
        """Cache miss + no DB roles → 403."""
        from app.rbac.dependencies import require_permission

        user = make_user()
        redis = make_redis(cached_perms=None)
        db = make_db(roles=[])

        dep = require_permission("users:delete")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=user, db=db, redis=redis)
        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# T3.1 — get_user_permissions_dep
# ---------------------------------------------------------------------------


class TestGetUserPermissionsDep:
    async def test_returns_set_of_permissions(self):
        from app.rbac.dependencies import get_user_permissions_dep

        user = make_user()
        redis = make_redis(cached_perms=["users:read", "cases:read"])
        db = make_db()

        result = await get_user_permissions_dep(current_user=user, db=db, redis=redis)
        assert isinstance(result, set)
        assert "users:read" in result
        assert "cases:read" in result

    async def test_returns_empty_set_when_no_permissions(self):
        from app.rbac.dependencies import get_user_permissions_dep

        user = make_user()
        redis = make_redis(cached_perms=None)
        db = make_db(roles=[])

        result = await get_user_permissions_dep(current_user=user, db=db, redis=redis)
        assert result == set()

    async def test_returns_permissions_from_db_on_cache_miss(self):
        from app.rbac.dependencies import get_user_permissions_dep

        user = make_user()
        redis = make_redis(cached_perms=None)

        rp = MagicMock()
        rp.permission.resource = "billing"
        rp.permission.action = "read"
        role = MagicMock()
        role.role_permissions = [rp]
        db = make_db(roles=[role])

        result = await get_user_permissions_dep(current_user=user, db=db, redis=redis)
        assert "billing:read" in result
