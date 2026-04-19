"""Unit tests for RBAC Pydantic v2 schemas — RED phase (T3.3).

Tests will FAIL until app/rbac/schemas.py is created.
Pure Pydantic validation — no mocks, no DB, no Redis.
"""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# RoleResponse
# ---------------------------------------------------------------------------


class TestRoleResponse:
    def test_valid_full(self):
        from app.rbac.schemas import RoleResponse

        r = RoleResponse(
            id=uuid.uuid4(),
            name="admin",
            display_name="Administrador",
            description="Acceso completo",
            is_system=True,
        )
        assert r.name == "admin"
        assert r.is_system is True

    def test_description_optional(self):
        from app.rbac.schemas import RoleResponse

        r = RoleResponse(
            id=uuid.uuid4(),
            name="viewer",
            display_name="Solo Lectura",
            description=None,
            is_system=True,
        )
        assert r.description is None

    def test_missing_required_field_raises(self):
        from app.rbac.schemas import RoleResponse

        with pytest.raises(ValidationError):
            RoleResponse(name="admin", display_name="Admin", is_system=True)  # no id

    def test_id_is_uuid(self):
        from app.rbac.schemas import RoleResponse

        role_id = uuid.uuid4()
        r = RoleResponse(
            id=role_id,
            name="admin",
            display_name="Admin",
            description=None,
            is_system=False,
        )
        assert r.id == role_id


# ---------------------------------------------------------------------------
# PermissionResponse
# ---------------------------------------------------------------------------


class TestPermissionResponse:
    def test_valid(self):
        from app.rbac.schemas import PermissionResponse

        p = PermissionResponse(
            id=uuid.uuid4(),
            resource="users",
            action="read",
            description="Leer usuarios",
        )
        assert p.resource == "users"
        assert p.action == "read"

    def test_description_optional(self):
        from app.rbac.schemas import PermissionResponse

        p = PermissionResponse(
            id=uuid.uuid4(),
            resource="cases",
            action="write",
            description=None,
        )
        assert p.description is None

    def test_missing_resource_raises(self):
        from app.rbac.schemas import PermissionResponse

        with pytest.raises(ValidationError):
            PermissionResponse(id=uuid.uuid4(), action="read", description=None)


# ---------------------------------------------------------------------------
# UserRoleAssign
# ---------------------------------------------------------------------------


class TestUserRoleAssign:
    def test_valid(self):
        from app.rbac.schemas import UserRoleAssign

        role_id = uuid.uuid4()
        a = UserRoleAssign(role_id=role_id)
        assert a.role_id == role_id

    def test_missing_role_id_raises(self):
        from app.rbac.schemas import UserRoleAssign

        with pytest.raises(ValidationError):
            UserRoleAssign()

    def test_invalid_uuid_raises(self):
        from app.rbac.schemas import UserRoleAssign

        with pytest.raises(ValidationError):
            UserRoleAssign(role_id="not-a-uuid")


# ---------------------------------------------------------------------------
# UserRoleResponse
# ---------------------------------------------------------------------------


class TestUserRoleResponse:
    def _now(self) -> datetime:
        return datetime.now(UTC)

    def test_valid_full(self):
        from app.rbac.schemas import UserRoleResponse

        r = UserRoleResponse(
            role_id=uuid.uuid4(),
            role_name="admin",
            assigned_at=self._now(),
            assigned_by=uuid.uuid4(),
            expires_at=None,
        )
        assert r.role_name == "admin"
        assert r.expires_at is None

    def test_assigned_by_optional(self):
        from app.rbac.schemas import UserRoleResponse

        r = UserRoleResponse(
            role_id=uuid.uuid4(),
            role_name="viewer",
            assigned_at=self._now(),
            assigned_by=None,
            expires_at=None,
        )
        assert r.assigned_by is None

    def test_expires_at_can_be_set(self):
        from app.rbac.schemas import UserRoleResponse

        exp = self._now()
        r = UserRoleResponse(
            role_id=uuid.uuid4(),
            role_name="abogado",
            assigned_at=self._now(),
            assigned_by=None,
            expires_at=exp,
        )
        assert r.expires_at == exp

    def test_missing_role_id_raises(self):
        from app.rbac.schemas import UserRoleResponse

        with pytest.raises(ValidationError):
            UserRoleResponse(role_name="admin", assigned_at=self._now(), assigned_by=None, expires_at=None)


# ---------------------------------------------------------------------------
# PermissionSetResponse
# ---------------------------------------------------------------------------


class TestPermissionSetResponse:
    def test_valid(self):
        from app.rbac.schemas import PermissionSetResponse

        r = PermissionSetResponse(permissions=["users:read", "cases:read"])
        assert "users:read" in r.permissions

    def test_empty_list_valid(self):
        from app.rbac.schemas import PermissionSetResponse

        r = PermissionSetResponse(permissions=[])
        assert r.permissions == []

    def test_missing_permissions_raises(self):
        from app.rbac.schemas import PermissionSetResponse

        with pytest.raises(ValidationError):
            PermissionSetResponse()


# ---------------------------------------------------------------------------
# AuditLogEntry
# ---------------------------------------------------------------------------


class TestAuditLogEntry:
    def _now(self) -> datetime:
        return datetime.now(UTC)

    def test_valid_minimal(self):
        from app.rbac.schemas import AuditLogEntry

        e = AuditLogEntry(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            action="assign_role",
            resource_type="user_role",
            resource_id=None,
            before_state=None,
            after_state=None,
            ip_address=None,
            created_at=self._now(),
        )
        assert e.action == "assign_role"

    def test_valid_full(self):
        from app.rbac.schemas import AuditLogEntry

        e = AuditLogEntry(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            action="revoke_role",
            resource_type="user_role",
            resource_id=str(uuid.uuid4()),
            before_state={"role": "admin"},
            after_state=None,
            ip_address="127.0.0.1",
            created_at=self._now(),
        )
        assert e.ip_address == "127.0.0.1"
        assert e.before_state == {"role": "admin"}

    def test_optional_fields_can_be_none(self):
        from app.rbac.schemas import AuditLogEntry

        e = AuditLogEntry(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            action="assign_role",
            resource_type="user",
            resource_id=None,
            before_state=None,
            after_state=None,
            ip_address=None,
            created_at=self._now(),
        )
        assert e.resource_id is None
        assert e.ip_address is None

    def test_missing_user_id_raises(self):
        from app.rbac.schemas import AuditLogEntry

        with pytest.raises(ValidationError):
            AuditLogEntry(
                id=uuid.uuid4(),
                action="assign_role",
                resource_type="user",
                resource_id=None,
                before_state=None,
                after_state=None,
                ip_address=None,
                created_at=self._now(),
            )


# ---------------------------------------------------------------------------
# AuditLogPage
# ---------------------------------------------------------------------------


class TestAuditLogPage:
    def _entry(self) -> dict:
        return {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "action": "assign_role",
            "resource_type": "user",
            "resource_id": None,
            "before_state": None,
            "after_state": None,
            "ip_address": None,
            "created_at": datetime.now(UTC),
        }

    def test_valid(self):
        from app.rbac.schemas import AuditLogEntry, AuditLogPage

        page = AuditLogPage(
            items=[AuditLogEntry(**self._entry())],
            total=1,
            page=1,
            page_size=20,
        )
        assert page.total == 1
        assert len(page.items) == 1

    def test_empty_items(self):
        from app.rbac.schemas import AuditLogPage

        page = AuditLogPage(items=[], total=0, page=1, page_size=20)
        assert page.items == []

    def test_missing_total_raises(self):
        from app.rbac.schemas import AuditLogPage

        with pytest.raises(ValidationError):
            AuditLogPage(items=[], page=1, page_size=20)

    def test_page_size_field_present(self):
        from app.rbac.schemas import AuditLogPage

        page = AuditLogPage(items=[], total=0, page=2, page_size=50)
        assert page.page == 2
        assert page.page_size == 50
