"""Tests for migration 004_add_rbac — RED phase (T1.1).

Structural tests (no DB): migration file exists and has correct metadata.
Schema tests (require DB with migration applied): tables, columns, FKs, indexes.
"""

import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

from app.config import settings

MIGRATION_FILE = (
    Path(__file__).parent.parent.parent
    / "alembic"
    / "versions"
    / "004_add_rbac.py"
)


# ---------------------------------------------------------------------------
# Structural tests — no DB required
# ---------------------------------------------------------------------------


class TestRBACMigrationStructure:
    def test_migration_file_exists(self):
        assert MIGRATION_FILE.exists(), (
            f"Migration file not found: {MIGRATION_FILE}\n"
            "Create it as: apps/api/alembic/versions/004_add_rbac.py"
        )

    def test_migration_has_upgrade_and_downgrade(self):
        if not MIGRATION_FILE.exists():
            pytest.skip("Migration file not found")
        spec = importlib.util.spec_from_file_location("migration_004", MIGRATION_FILE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert callable(getattr(mod, "upgrade", None)), "upgrade() not found"
        assert callable(getattr(mod, "downgrade", None)), "downgrade() not found"

    def test_migration_revision_chain(self):
        if not MIGRATION_FILE.exists():
            pytest.skip("Migration file not found")
        spec = importlib.util.spec_from_file_location("migration_004", MIGRATION_FILE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.down_revision == "003_add_refresh_tokens", (
            f"Expected down_revision='003_add_refresh_tokens', got: {mod.down_revision!r}"
        )

    def test_migration_revision_id(self):
        if not MIGRATION_FILE.exists():
            pytest.skip("Migration file not found")
        spec = importlib.util.spec_from_file_location("migration_004", MIGRATION_FILE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.revision == "004_add_rbac", (
            f"Expected revision='004_add_rbac', got: {mod.revision!r}"
        )


# ---------------------------------------------------------------------------
# Schema tests — require DB with migration applied (alembic upgrade head)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sync_engine():
    engine = create_engine(settings.database_url_sync)
    yield engine
    engine.dispose()


RBAC_TABLES = {"roles", "permissions", "role_permissions", "user_roles", "audit_log"}


class TestRBACSchema:
    def test_all_tables_exist(self, sync_engine):
        inspector = inspect(sync_engine)
        existing = set(inspector.get_table_names())
        missing = RBAC_TABLES - existing
        assert not missing, (
            f"Missing RBAC tables: {missing}\n"
            "Run: cd apps/api && alembic upgrade head"
        )

    def test_roles_columns(self, sync_engine):
        inspector = inspect(sync_engine)
        if "roles" not in inspector.get_table_names():
            pytest.fail("roles table missing — run: alembic upgrade head")
        cols = {c["name"] for c in inspector.get_columns("roles")}
        required = {"id", "name", "display_name", "description", "is_system", "created_at"}
        missing = required - cols
        assert not missing, f"Missing columns on roles: {missing}"

    def test_permissions_columns(self, sync_engine):
        inspector = inspect(sync_engine)
        if "permissions" not in inspector.get_table_names():
            pytest.fail("permissions table missing — run: alembic upgrade head")
        cols = {c["name"] for c in inspector.get_columns("permissions")}
        required = {"id", "resource", "action", "description", "created_at"}
        missing = required - cols
        assert not missing, f"Missing columns on permissions: {missing}"

    def test_user_roles_columns(self, sync_engine):
        inspector = inspect(sync_engine)
        if "user_roles" not in inspector.get_table_names():
            pytest.fail("user_roles table missing — run: alembic upgrade head")
        cols = {c["name"] for c in inspector.get_columns("user_roles")}
        required = {"user_id", "role_id", "assigned_by", "assigned_at", "expires_at"}
        missing = required - cols
        assert not missing, f"Missing columns on user_roles: {missing}"

    def test_audit_log_columns(self, sync_engine):
        inspector = inspect(sync_engine)
        if "audit_log" not in inspector.get_table_names():
            pytest.fail("audit_log table missing — run: alembic upgrade head")
        cols = {c["name"] for c in inspector.get_columns("audit_log")}
        required = {
            "id", "user_id", "action", "resource_type", "resource_id",
            "before_state", "after_state", "ip_address", "user_agent", "created_at",
        }
        missing = required - cols
        assert not missing, f"Missing columns on audit_log: {missing}"

    def test_roles_name_index_exists(self, sync_engine):
        inspector = inspect(sync_engine)
        if "roles" not in inspector.get_table_names():
            pytest.fail("roles table missing")
        indexes = inspector.get_indexes("roles")
        name_indexes = [idx for idx in indexes if "name" in idx["column_names"]]
        assert name_indexes, "No index on roles.name"

    def test_permissions_unique_constraint(self, sync_engine):
        inspector = inspect(sync_engine)
        if "permissions" not in inspector.get_table_names():
            pytest.fail("permissions table missing")
        # Check for unique constraint or unique index on (resource, action)
        indexes = inspector.get_indexes("permissions")
        unique_on_resource_action = [
            idx for idx in indexes
            if idx.get("unique") and set(idx["column_names"]) == {"resource", "action"}
        ]
        unique_constraints = inspector.get_unique_constraints("permissions")
        covered_by_constraint = any(
            set(c["column_names"]) == {"resource", "action"} for c in unique_constraints
        )
        assert unique_on_resource_action or covered_by_constraint, (
            "permissions must have UNIQUE constraint or index on (resource, action)"
        )

    def test_user_roles_fk_to_users(self, sync_engine):
        inspector = inspect(sync_engine)
        if "user_roles" not in inspector.get_table_names():
            pytest.fail("user_roles table missing")
        fks = inspector.get_foreign_keys("user_roles")
        user_fks = [fk for fk in fks if "user_id" in fk["constrained_columns"]]
        assert user_fks, "No FK on user_roles.user_id"
        assert user_fks[0]["referred_table"] == "users"

    def test_user_roles_fk_to_roles(self, sync_engine):
        inspector = inspect(sync_engine)
        if "user_roles" not in inspector.get_table_names():
            pytest.fail("user_roles table missing")
        fks = inspector.get_foreign_keys("user_roles")
        role_fks = [fk for fk in fks if "role_id" in fk["constrained_columns"]]
        assert role_fks, "No FK on user_roles.role_id"
        assert role_fks[0]["referred_table"] == "roles"
