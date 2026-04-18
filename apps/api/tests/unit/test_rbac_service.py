"""Unit tests for RBACService — RED phase (T2.2).

Tests use mock DB session and mock PermissionCache.
All tests fail until app/rbac/service.py is created.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rbac.constants import SystemRole
from app.rbac.models import Role, UserRole
from app.rbac.service import RBACService


def make_cache(*, get_return=None) -> AsyncMock:
    cache = AsyncMock()
    cache.get_permissions = AsyncMock(return_value=get_return)
    cache.set_permissions = AsyncMock()
    cache.invalidate = AsyncMock()
    cache.invalidate_all = AsyncMock()
    return cache


def make_db() -> AsyncMock:
    db = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.delete = AsyncMock()
    db.commit = AsyncMock()
    return db


def make_role(name: str, perms: list[str]) -> MagicMock:
    """Build a mock Role with mock permissions."""
    role = MagicMock(spec=Role)
    role.name = name
    role.id = uuid.uuid4()
    role.role_permissions = []
    for p_str in perms:
        resource, action = p_str.split(":")
        rp = MagicMock()
        rp.permission = MagicMock()
        rp.permission.resource = resource
        rp.permission.action = action
        role.role_permissions.append(rp)
    return role


class TestGetUserPermissionsCacheHit:
    async def test_returns_cached_permissions(self):
        cached = {"users:read", "cases:read"}
        cache = make_cache(get_return=cached)
        db = make_db()
        svc = RBACService(db=db, cache=cache)
        result = await svc.get_user_permissions(uuid.uuid4())
        assert result == cached

    async def test_does_not_query_db_on_cache_hit(self):
        cache = make_cache(get_return={"users:read"})
        db = make_db()
        svc = RBACService(db=db, cache=cache)
        await svc.get_user_permissions(uuid.uuid4())
        db.execute.assert_not_called()

    async def test_does_not_set_cache_on_cache_hit(self):
        cache = make_cache(get_return={"users:read"})
        db = make_db()
        svc = RBACService(db=db, cache=cache)
        await svc.get_user_permissions(uuid.uuid4())
        cache.set_permissions.assert_not_called()


class TestGetUserPermissionsCacheMiss:
    async def test_queries_db_on_cache_miss(self):
        cache = make_cache(get_return=None)
        db = make_db()

        # Simulate scalars().all() returning user roles
        role = make_role("admin", ["users:read", "cases:read"])
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [role]
        db.execute.return_value = result_mock

        svc = RBACService(db=db, cache=cache)
        perms = await svc.get_user_permissions(uuid.uuid4())

        db.execute.assert_called_once()
        assert "users:read" in perms
        assert "cases:read" in perms

    async def test_stores_result_in_cache_after_db_query(self):
        cache = make_cache(get_return=None)
        db = make_db()

        role = make_role("viewer", ["users:read"])
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [role]
        db.execute.return_value = result_mock

        svc = RBACService(db=db, cache=cache)
        user_id = uuid.uuid4()
        await svc.get_user_permissions(user_id)

        cache.set_permissions.assert_called_once()
        call_args = cache.set_permissions.call_args
        assert call_args[0][0] == user_id

    async def test_returns_empty_set_when_no_roles(self):
        cache = make_cache(get_return=None)
        db = make_db()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        db.execute.return_value = result_mock

        svc = RBACService(db=db, cache=cache)
        result = await svc.get_user_permissions(uuid.uuid4())
        assert result == set()

    async def test_merges_permissions_from_multiple_roles(self):
        cache = make_cache(get_return=None)
        db = make_db()

        role1 = make_role("admin", ["users:read", "cases:read"])
        role2 = make_role("finance", ["billing:read", "billing:update"])
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [role1, role2]
        db.execute.return_value = result_mock

        svc = RBACService(db=db, cache=cache)
        result = await svc.get_user_permissions(uuid.uuid4())
        assert result == {"users:read", "cases:read", "billing:read", "billing:update"}


class TestCheckPermission:
    async def test_returns_true_when_permission_present(self):
        cache = make_cache(get_return={"users:read", "cases:read"})
        svc = RBACService(db=make_db(), cache=cache)
        assert await svc.check_permission(uuid.uuid4(), "users:read") is True

    async def test_returns_false_when_permission_absent(self):
        cache = make_cache(get_return={"users:read"})
        svc = RBACService(db=make_db(), cache=cache)
        assert await svc.check_permission(uuid.uuid4(), "users:delete") is False

    async def test_all_required_must_be_present(self):
        cache = make_cache(get_return={"users:read", "cases:read"})
        svc = RBACService(db=make_db(), cache=cache)
        # Both present → True
        assert await svc.check_permission(uuid.uuid4(), "users:read", "cases:read") is True

    async def test_partial_match_returns_false(self):
        cache = make_cache(get_return={"users:read"})
        svc = RBACService(db=make_db(), cache=cache)
        # Only one of two present → False
        assert await svc.check_permission(uuid.uuid4(), "users:read", "cases:delete") is False

    async def test_empty_required_returns_true(self):
        """No required permissions → always allowed."""
        cache = make_cache(get_return=set())
        svc = RBACService(db=make_db(), cache=cache)
        assert await svc.check_permission(uuid.uuid4()) is True


class TestCheckPermissionSuperAdmin:
    async def test_super_admin_bypasses_all_checks(self):
        """super_admin must pass check_permission regardless of DB permissions."""
        cache = make_cache(get_return=None)
        db = make_db()

        # super_admin role with ALL permissions
        from app.rbac.constants import ALL_PERMISSIONS
        role = make_role(SystemRole.SUPER_ADMIN.value, ALL_PERMISSIONS)
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [role]
        db.execute.return_value = result_mock

        svc = RBACService(db=db, cache=cache)
        user_id = uuid.uuid4()
        assert await svc.check_permission(user_id, "settings:update") is True
        assert await svc.check_permission(user_id, "audit_log:read") is True


class TestAssignRole:
    async def test_creates_user_role_record(self):
        cache = make_cache()
        db = make_db()
        svc = RBACService(db=db, cache=cache)

        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        assigned_by = uuid.uuid4()

        result = await svc.assign_role(user_id, role_id, assigned_by)

        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert isinstance(added, UserRole)
        assert added.user_id == user_id
        assert added.role_id == role_id
        assert added.assigned_by == assigned_by

    async def test_assign_role_invalidates_cache(self):
        cache = make_cache()
        db = make_db()
        svc = RBACService(db=db, cache=cache)
        user_id = uuid.uuid4()
        await svc.assign_role(user_id, uuid.uuid4(), None)
        cache.invalidate.assert_called_once_with(user_id)

    async def test_assign_role_assigned_by_can_be_none(self):
        cache = make_cache()
        db = make_db()
        svc = RBACService(db=db, cache=cache)
        result = await svc.assign_role(uuid.uuid4(), uuid.uuid4(), None)
        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.assigned_by is None

    async def test_assign_role_returns_user_role(self):
        cache = make_cache()
        db = make_db()
        svc = RBACService(db=db, cache=cache)
        result = await svc.assign_role(uuid.uuid4(), uuid.uuid4(), None)
        assert isinstance(result, UserRole)


class TestRevokeRole:
    async def test_revoke_role_executes_delete(self):
        cache = make_cache()
        db = make_db()
        result_mock = MagicMock()
        db.execute.return_value = result_mock

        svc = RBACService(db=db, cache=cache)
        await svc.revoke_role(uuid.uuid4(), uuid.uuid4())
        db.execute.assert_called_once()

    async def test_revoke_role_invalidates_cache(self):
        cache = make_cache()
        db = make_db()
        db.execute.return_value = MagicMock()

        svc = RBACService(db=db, cache=cache)
        user_id = uuid.uuid4()
        await svc.revoke_role(user_id, uuid.uuid4())
        cache.invalidate.assert_called_once_with(user_id)


class TestGetUserRoles:
    async def test_returns_list_of_roles(self):
        cache = make_cache()
        db = make_db()

        role1 = make_role("admin", [])
        role2 = make_role("viewer", [])
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [role1, role2]
        db.execute.return_value = result_mock

        svc = RBACService(db=db, cache=cache)
        roles = await svc.get_user_roles(uuid.uuid4())
        assert len(roles) == 2

    async def test_returns_empty_list_when_no_roles(self):
        cache = make_cache()
        db = make_db()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        db.execute.return_value = result_mock

        svc = RBACService(db=db, cache=cache)
        roles = await svc.get_user_roles(uuid.uuid4())
        assert roles == []


class TestFailOpenCache:
    async def test_get_permissions_works_when_cache_unavailable(self):
        """If cache.get raises, fall back to DB gracefully."""
        cache = make_cache()
        cache.get_permissions.side_effect = Exception("Redis down")
        db = make_db()

        role = make_role("viewer", ["users:read"])
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [role]
        db.execute.return_value = result_mock

        svc = RBACService(db=db, cache=cache)
        result = await svc.get_user_permissions(uuid.uuid4())
        assert "users:read" in result
