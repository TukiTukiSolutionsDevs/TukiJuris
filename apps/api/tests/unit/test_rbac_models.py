"""Unit tests for RBAC SQLAlchemy models — RED phase (T1.1).

Tests model instantiation (pure Python objects, no DB round-trip).
All tests fail until app/rbac/models.py is created.
"""

import uuid

import pytest
from sqlalchemy import UniqueConstraint

from app.rbac.models import AuditLog, Permission, Role, RolePermission, UserRole


class TestRoleModel:
    def test_instantiation(self):
        role = Role(name="admin", display_name="Administrator")
        assert role.name == "admin"
        assert role.display_name == "Administrator"

    def test_default_is_system_true(self):
        """Column INSERT default for is_system must be True.

        SQLAlchemy non-dataclass ORM models apply `default` at INSERT time,
        not at Python constructor time — so we inspect the column metadata.
        """
        col_default = Role.__table__.c.is_system.default
        assert col_default is not None, "is_system must have a column default"
        assert col_default.arg is True, f"Expected default True, got {col_default.arg!r}"

    def test_tablename(self):
        assert Role.__tablename__ == "roles"

    def test_description_nullable(self):
        role = Role(name="admin", display_name="Administrator", description=None)
        assert role.description is None

    def test_with_description(self):
        role = Role(name="viewer", display_name="Viewer", description="Read-only access")
        assert role.description == "Read-only access"

    def test_is_system_can_be_false(self):
        role = Role(name="custom", display_name="Custom", is_system=False)
        assert role.is_system is False

    def test_name_stored(self):
        role = Role(name="super_admin", display_name="Super Administrator")
        assert role.name == "super_admin"


class TestPermissionModel:
    def test_instantiation(self):
        perm = Permission(resource="users", action="create")
        assert perm.resource == "users"
        assert perm.action == "create"

    def test_tablename(self):
        assert Permission.__tablename__ == "permissions"

    def test_unique_constraint_on_resource_action(self):
        """Permission.__table_args__ must contain UniqueConstraint(resource, action)."""
        table_args = Permission.__table_args__
        assert isinstance(table_args, tuple), "__table_args__ must be a tuple"
        has_unique = any(isinstance(c, UniqueConstraint) for c in table_args)
        assert has_unique, "Permission must have UniqueConstraint on (resource, action)"

    def test_unique_constraint_covers_both_columns(self):
        table_args = Permission.__table_args__
        for constraint in table_args:
            if isinstance(constraint, UniqueConstraint):
                col_names = {c.name for c in constraint.columns}
                assert col_names == {"resource", "action"}, (
                    f"UniqueConstraint must cover (resource, action), got: {col_names}"
                )

    def test_description_nullable(self):
        perm = Permission(resource="billing", action="read", description=None)
        assert perm.description is None

    def test_description_stored(self):
        perm = Permission(resource="audit_log", action="read", description="View audit log")
        assert perm.description == "View audit log"


class TestRolePermissionModel:
    def test_instantiation(self):
        role_id = uuid.uuid4()
        perm_id = uuid.uuid4()
        rp = RolePermission(role_id=role_id, permission_id=perm_id)
        assert rp.role_id == role_id
        assert rp.permission_id == perm_id

    def test_tablename(self):
        assert RolePermission.__tablename__ == "role_permissions"

    def test_different_ids_stored_independently(self):
        r1 = uuid.uuid4()
        r2 = uuid.uuid4()
        p1 = uuid.uuid4()
        rp1 = RolePermission(role_id=r1, permission_id=p1)
        rp2 = RolePermission(role_id=r2, permission_id=p1)
        assert rp1.role_id != rp2.role_id


class TestUserRoleModel:
    def test_instantiation(self):
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        ur = UserRole(user_id=user_id, role_id=role_id)
        assert ur.user_id == user_id
        assert ur.role_id == role_id

    def test_tablename(self):
        assert UserRole.__tablename__ == "user_roles"

    def test_assigned_by_nullable(self):
        ur = UserRole(user_id=uuid.uuid4(), role_id=uuid.uuid4(), assigned_by=None)
        assert ur.assigned_by is None

    def test_expires_at_nullable(self):
        ur = UserRole(user_id=uuid.uuid4(), role_id=uuid.uuid4(), expires_at=None)
        assert ur.expires_at is None

    def test_assigned_by_can_be_uuid(self):
        admin_id = uuid.uuid4()
        ur = UserRole(user_id=uuid.uuid4(), role_id=uuid.uuid4(), assigned_by=admin_id)
        assert ur.assigned_by == admin_id


class TestAuditLogModel:
    def test_instantiation(self):
        log = AuditLog(action="POST /api/users", resource_type="users")
        assert log.action == "POST /api/users"
        assert log.resource_type == "users"

    def test_tablename(self):
        assert AuditLog.__tablename__ == "audit_log"

    def test_user_id_nullable(self):
        log = AuditLog(action="GET /api/health", user_id=None)
        assert log.user_id is None

    def test_before_state_nullable(self):
        log = AuditLog(action="DELETE /api/cases/1", before_state=None)
        assert log.before_state is None

    def test_after_state_nullable(self):
        log = AuditLog(action="DELETE /api/cases/1", after_state=None)
        assert log.after_state is None

    def test_resource_id_nullable(self):
        log = AuditLog(action="POST /api/users", resource_id=None)
        assert log.resource_id is None

    def test_ip_address_nullable(self):
        log = AuditLog(action="POST /api/users", ip_address=None)
        assert log.ip_address is None

    def test_user_agent_nullable(self):
        log = AuditLog(action="POST /api/users", user_agent=None)
        assert log.user_agent is None

    def test_jsonb_fields_accept_dicts(self):
        log = AuditLog(
            action="PUT /api/cases/1",
            before_state={"status": "open"},
            after_state={"status": "closed"},
        )
        assert log.before_state == {"status": "open"}
        assert log.after_state == {"status": "closed"}
