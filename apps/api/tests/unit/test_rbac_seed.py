"""Unit tests for RBAC seed function — RED phase (T1.1).

Strategy:
- Structural tests (no DB): ROLE_PERMISSION_MATRIX shape and correctness.
- Behavioural tests: seed_roles_and_permissions called with AsyncMock session.
  Verifies that the function calls db.execute and handles idempotent re-runs.

All tests fail until app/rbac/seed.py is created.
"""

from unittest.mock import AsyncMock, call, patch

import pytest

from app.rbac.constants import SystemRole
from app.rbac.seed import ROLE_PERMISSION_MATRIX, seed_roles_and_permissions

# ---------------------------------------------------------------------------
# ROLE_PERMISSION_MATRIX structure tests — pure Python, no DB
# ---------------------------------------------------------------------------


class TestRolePermissionMatrix:
    def test_has_five_roles(self):
        assert len(ROLE_PERMISSION_MATRIX) == 5

    def test_contains_all_system_roles(self):
        for role in SystemRole:
            assert role.value in ROLE_PERMISSION_MATRIX, (
                f"ROLE_PERMISSION_MATRIX missing role: {role.value!r}"
            )

    def test_all_permissions_are_strings(self):
        for role, perms in ROLE_PERMISSION_MATRIX.items():
            for perm in perms:
                assert isinstance(perm, str), f"Permission {perm!r} in {role!r} is not a string"

    def test_all_permissions_have_colon_separator(self):
        for role, perms in ROLE_PERMISSION_MATRIX.items():
            for perm in perms:
                assert ":" in perm, f"Permission {perm!r} in {role!r} missing ':' separator"

    def test_super_admin_has_all_28_permissions(self):
        super_admin_perms = ROLE_PERMISSION_MATRIX[SystemRole.SUPER_ADMIN.value]
        assert len(super_admin_perms) == 28

    def test_super_admin_has_audit_log_read(self):
        perms = ROLE_PERMISSION_MATRIX[SystemRole.SUPER_ADMIN.value]
        assert "audit_log:read" in perms

    def test_admin_has_audit_log_read(self):
        perms = ROLE_PERMISSION_MATRIX[SystemRole.ADMIN.value]
        assert "audit_log:read" in perms

    def test_admin_does_not_have_billing_update(self):
        perms = ROLE_PERMISSION_MATRIX[SystemRole.ADMIN.value]
        assert "billing:update" not in perms

    def test_support_is_read_only(self):
        perms = ROLE_PERMISSION_MATRIX[SystemRole.SUPPORT.value]
        write_actions = {"create", "update", "delete", "export"}
        for perm in perms:
            _, action = perm.split(":", 1)
            assert action not in write_actions, (
                f"support role must not have write permission: {perm!r}"
            )

    def test_viewer_is_read_only(self):
        perms = ROLE_PERMISSION_MATRIX[SystemRole.VIEWER.value]
        write_actions = {"create", "update", "delete", "export"}
        for perm in perms:
            _, action = perm.split(":", 1)
            assert action not in write_actions, (
                f"viewer role must not have write permission: {perm!r}"
            )

    def test_viewer_has_no_billing(self):
        perms = ROLE_PERMISSION_MATRIX[SystemRole.VIEWER.value]
        billing_perms = [p for p in perms if p.startswith("billing:")]
        assert not billing_perms, f"viewer must not have billing permissions: {billing_perms}"

    def test_finance_has_billing_update(self):
        perms = ROLE_PERMISSION_MATRIX[SystemRole.FINANCE.value]
        assert "billing:update" in perms

    def test_support_has_no_audit_log(self):
        perms = ROLE_PERMISSION_MATRIX[SystemRole.SUPPORT.value]
        audit_perms = [p for p in perms if p.startswith("audit_log:")]
        assert not audit_perms, f"support must not have audit_log permissions: {audit_perms}"

    def test_no_duplicate_permissions_per_role(self):
        for role, perms in ROLE_PERMISSION_MATRIX.items():
            assert len(perms) == len(set(perms)), (
                f"Duplicate permissions detected for role {role!r}: {perms}"
            )


# ---------------------------------------------------------------------------
# Behavioural tests — mocked AsyncSession
# ---------------------------------------------------------------------------


class TestSeedFunction:
    async def test_seed_is_async(self):
        """seed_roles_and_permissions must be a coroutine function."""
        import inspect
        assert inspect.iscoroutinefunction(seed_roles_and_permissions)

    async def test_seed_calls_db_execute(self):
        """seed must call db.execute at least once (roles + permissions inserts)."""
        mock_db = AsyncMock()
        await seed_roles_and_permissions(mock_db)
        assert mock_db.execute.call_count > 0, "seed must call db.execute to insert data"

    async def test_seed_idempotent_no_exception(self):
        """Calling seed twice on the same mock must not raise."""
        mock_db = AsyncMock()
        await seed_roles_and_permissions(mock_db)
        await seed_roles_and_permissions(mock_db)
        # If ON CONFLICT DO NOTHING logic is correct, no exception on second call

    async def test_seed_calls_commit(self):
        """seed must commit after inserting data."""
        mock_db = AsyncMock()
        await seed_roles_and_permissions(mock_db)
        mock_db.commit.assert_called()

    async def test_seed_execute_count_reasonable(self):
        """seed must call execute at least 3 times (roles, permissions, role_permissions)."""
        mock_db = AsyncMock()
        await seed_roles_and_permissions(mock_db)
        assert mock_db.execute.call_count >= 3, (
            f"Expected ≥3 execute calls, got {mock_db.execute.call_count}. "
            "Seed should insert roles, permissions, and role_permissions."
        )
