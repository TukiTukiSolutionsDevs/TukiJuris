"""Unit tests for AuditService and RBACService audit integration.

T4.1 — AuditService: log_action and query_log
T4.2 — RBACService: audit entries created on assign_role and revoke_role

All tests use mock DB — no real infrastructure required.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.rbac.audit import AuditService
from app.rbac.models import AuditLog


def make_db() -> AsyncMock:
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.execute = AsyncMock()
    return db


def make_cache() -> AsyncMock:
    cache = AsyncMock()
    cache.get_permissions = AsyncMock(return_value=None)
    cache.set_permissions = AsyncMock()
    cache.invalidate = AsyncMock()
    return cache


def make_audit() -> AsyncMock:
    audit = AsyncMock(spec=AuditService)
    audit.log_action = AsyncMock(return_value=MagicMock(spec=AuditLog))
    return audit


# ---------------------------------------------------------------------------
# T4.1 — AuditService.log_action
# ---------------------------------------------------------------------------


class TestLogAction:
    async def test_creates_audit_log_record(self):
        db = make_db()
        svc = AuditService(db=db)
        user_id = uuid.uuid4()

        await svc.log_action(
            user_id=user_id,
            action="role.assign",
            resource_type="user_role",
        )

        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert isinstance(added, AuditLog)
        assert added.user_id == user_id
        assert added.action == "role.assign"
        assert added.resource_type == "user_role"

    async def test_with_before_and_after_state(self):
        db = make_db()
        svc = AuditService(db=db)
        before = {"role": "viewer"}
        after = {"role": "admin"}

        await svc.log_action(
            user_id=uuid.uuid4(),
            action="role.assign",
            resource_type="user_role",
            before_state=before,
            after_state=after,
        )

        added = db.add.call_args[0][0]
        assert added.before_state == before
        assert added.after_state == after

    async def test_with_null_optional_fields(self):
        db = make_db()
        svc = AuditService(db=db)

        await svc.log_action(
            user_id=None,
            action="system.event",
            resource_type=None,
        )

        added = db.add.call_args[0][0]
        assert added.user_id is None
        assert added.resource_type is None
        assert added.resource_id is None
        assert added.before_state is None
        assert added.after_state is None
        assert added.ip_address is None
        assert added.user_agent is None

    async def test_with_resource_id_ip_and_user_agent(self):
        db = make_db()
        svc = AuditService(db=db)

        await svc.log_action(
            user_id=uuid.uuid4(),
            action="users:delete",
            resource_type="users",
            resource_id="target-user-id",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        added = db.add.call_args[0][0]
        assert added.resource_id == "target-user-id"
        assert added.ip_address == "192.168.1.1"
        assert added.user_agent == "Mozilla/5.0"

    async def test_flushes_to_db(self):
        db = make_db()
        svc = AuditService(db=db)

        await svc.log_action(
            user_id=uuid.uuid4(),
            action="role.assign",
            resource_type="user_role",
        )

        db.flush.assert_called_once()

    async def test_returns_audit_log_instance(self):
        db = make_db()
        svc = AuditService(db=db)

        result = await svc.log_action(
            user_id=uuid.uuid4(),
            action="role.assign",
            resource_type="user_role",
        )

        assert isinstance(result, AuditLog)


# ---------------------------------------------------------------------------
# T4.1 — AuditService.query_log
# ---------------------------------------------------------------------------


class TestQueryLog:
    def _make_rows(self, n: int) -> list[MagicMock]:
        return [MagicMock(spec=AuditLog) for _ in range(n)]

    def _make_db(self, total: int, rows: list) -> AsyncMock:
        db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = total
        rows_result = MagicMock()
        rows_result.scalars.return_value.all.return_value = rows
        db.execute = AsyncMock(side_effect=[count_result, rows_result])
        return db

    async def test_returns_items_and_total(self):
        rows = self._make_rows(3)
        db = self._make_db(3, rows)
        svc = AuditService(db=db)

        items, total = await svc.query_log(page=1, page_size=10, filters={})

        assert total == 3
        assert len(items) == 3

    async def test_pagination_executes_two_queries(self):
        db = self._make_db(25, self._make_rows(5))
        svc = AuditService(db=db)

        items, total = await svc.query_log(page=3, page_size=5, filters={})

        assert db.execute.call_count == 2
        assert total == 25
        assert len(items) == 5

    async def test_with_user_id_filter(self):
        db = self._make_db(1, self._make_rows(1))
        svc = AuditService(db=db)

        items, total = await svc.query_log(
            page=1, page_size=10, filters={"user_id": uuid.uuid4()}
        )

        assert db.execute.call_count == 2
        assert total == 1

    async def test_with_action_filter_returns_empty(self):
        db = self._make_db(0, [])
        svc = AuditService(db=db)

        items, total = await svc.query_log(
            page=1, page_size=10, filters={"action": "role.assign"}
        )

        assert total == 0
        assert items == []

    async def test_with_date_range_filter(self):
        rows = self._make_rows(2)
        db = self._make_db(2, rows)
        svc = AuditService(db=db)

        items, total = await svc.query_log(
            page=1,
            page_size=10,
            filters={
                "date_from": datetime(2026, 1, 1, tzinfo=UTC),
                "date_to": datetime(2026, 12, 31, tzinfo=UTC),
            },
        )

        assert total == 2
        assert len(items) == 2


# ---------------------------------------------------------------------------
# T4.2 — RBACService.assign_role audit integration
# ---------------------------------------------------------------------------


class TestAssignRoleAudit:
    async def test_assign_role_logs_audit_entry(self):
        from app.rbac.service import RBACService

        audit = make_audit()
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        role = MagicMock()
        role.name = "admin"
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = role
        db.execute = AsyncMock(return_value=result_mock)

        svc = RBACService(db=db, cache=make_cache(), audit=audit)
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        assigned_by = uuid.uuid4()

        await svc.assign_role(user_id, role_id, assigned_by)

        audit.log_action.assert_called_once()
        call_kwargs = audit.log_action.call_args[1]
        assert call_kwargs["action"] == "role.assign"
        assert call_kwargs["resource_type"] == "user_role"
        after = call_kwargs["after_state"]
        assert after["user_id"] == str(user_id)
        assert after["role_id"] == str(role_id)
        assert after["assigned_by"] == str(assigned_by)

    async def test_assign_role_audit_includes_role_name(self):
        from app.rbac.service import RBACService

        audit = make_audit()
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        role = MagicMock()
        role.name = "super_admin"
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = role
        db.execute = AsyncMock(return_value=result_mock)

        svc = RBACService(db=db, cache=make_cache(), audit=audit)
        await svc.assign_role(uuid.uuid4(), uuid.uuid4(), None)

        after = audit.log_action.call_args[1]["after_state"]
        assert after["role_name"] == "super_admin"

    async def test_assign_role_no_audit_when_audit_is_none(self):
        """Backward compat: audit=None → no log_action, no role lookup."""
        from app.rbac.service import RBACService

        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        svc = RBACService(db=db, cache=make_cache(), audit=None)
        # Must not raise and must not call execute (no role lookup needed)
        await svc.assign_role(uuid.uuid4(), uuid.uuid4(), None)
        db.execute.assert_not_called()


# ---------------------------------------------------------------------------
# T4.2 — RBACService.revoke_role audit integration
# ---------------------------------------------------------------------------


class TestRevokeRoleAudit:
    async def test_revoke_role_logs_audit_entry(self):
        from app.rbac.service import RBACService

        audit = make_audit()
        db = AsyncMock()

        role = MagicMock()
        role.name = "admin"
        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = role
        delete_result = MagicMock()
        db.execute = AsyncMock(side_effect=[role_result, delete_result])

        svc = RBACService(db=db, cache=make_cache(), audit=audit)
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()

        await svc.revoke_role(user_id, role_id)

        audit.log_action.assert_called_once()
        call_kwargs = audit.log_action.call_args[1]
        assert call_kwargs["action"] == "role.revoke"
        assert call_kwargs["resource_type"] == "user_role"
        before = call_kwargs["before_state"]
        assert before["user_id"] == str(user_id)
        assert before["role_id"] == str(role_id)
        assert before["role_name"] == "admin"

    async def test_revoke_role_before_state_has_correct_keys(self):
        from app.rbac.service import RBACService

        audit = make_audit()
        db = AsyncMock()

        role = MagicMock()
        role.name = "viewer"
        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = role
        delete_result = MagicMock()
        db.execute = AsyncMock(side_effect=[role_result, delete_result])

        svc = RBACService(db=db, cache=make_cache(), audit=audit)
        await svc.revoke_role(uuid.uuid4(), uuid.uuid4())

        before = audit.log_action.call_args[1]["before_state"]
        assert set(before.keys()) == {"user_id", "role_id", "role_name"}

    async def test_revoke_role_no_audit_when_audit_is_none(self):
        """Backward compat: audit=None → single execute (delete only)."""
        from app.rbac.service import RBACService

        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock())

        svc = RBACService(db=db, cache=make_cache(), audit=None)
        await svc.revoke_role(uuid.uuid4(), uuid.uuid4())

        # Only the DELETE is executed — no role lookup
        db.execute.assert_called_once()
