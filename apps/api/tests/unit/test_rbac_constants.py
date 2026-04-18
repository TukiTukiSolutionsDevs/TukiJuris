"""Unit tests for RBAC constants — RED phase (T1.1).

Tests will fail until app/rbac/constants.py is created.
No DB required — pure Python.
"""

import pytest

from app.rbac.constants import (
    ALL_PERMISSIONS,
    PERM_AUDIT_LOG_READ,
    PERM_BILLING_READ,
    PERM_BILLING_UPDATE,
    PERM_CASES_CREATE,
    PERM_CASES_DELETE,
    PERM_CASES_READ,
    PERM_CASES_UPDATE,
    PERM_DOCUMENTS_CREATE,
    PERM_DOCUMENTS_DELETE,
    PERM_DOCUMENTS_READ,
    PERM_DOCUMENTS_UPDATE,
    PERM_MODELS_READ,
    PERM_MODELS_SYNC,
    PERM_ORGANIZATIONS_READ,
    PERM_ORGANIZATIONS_WRITE,
    PERM_PLANS_READ,
    PERM_PLANS_WRITE,
    PERM_REPORTS_EXPORT,
    PERM_REPORTS_READ,
    PERM_ROLES_READ,
    PERM_ROLES_WRITE,
    PERM_SETTINGS_READ,
    PERM_SETTINGS_UPDATE,
    PERM_USERS_CREATE,
    PERM_USERS_DELETE,
    PERM_USERS_IMPERSONATE,
    PERM_USERS_READ,
    PERM_USERS_UPDATE,
    SystemRole,
)

ALL_PERMS = ALL_PERMISSIONS


class TestSystemRole:
    def test_has_five_roles(self):
        assert len(SystemRole) == 5

    def test_super_admin_value(self):
        assert SystemRole.SUPER_ADMIN.value == "super_admin"

    def test_admin_value(self):
        assert SystemRole.ADMIN.value == "admin"

    def test_support_value(self):
        assert SystemRole.SUPPORT.value == "support"

    def test_finance_value(self):
        assert SystemRole.FINANCE.value == "finance"

    def test_viewer_value(self):
        assert SystemRole.VIEWER.value == "viewer"

    def test_is_str_enum(self):
        """SystemRole must be a str enum so it serialises naturally."""
        assert isinstance(SystemRole.SUPER_ADMIN, str)

    def test_all_values_unique(self):
        values = [r.value for r in SystemRole]
        assert len(values) == len(set(values))


class TestPermissionConstants:
    def test_total_count(self):
        assert len(ALL_PERMS) == 28

    def test_all_unique(self):
        assert len(set(ALL_PERMS)) == 28, "Duplicate permission detected"

    def test_format_resource_colon_action(self):
        for perm in ALL_PERMS:
            assert ":" in perm, f"{perm!r} missing ':' separator"
            resource, action = perm.split(":", 1)
            assert resource, f"{perm!r}: resource must not be empty"
            assert action, f"{perm!r}: action must not be empty"

    def test_users_create(self):
        assert PERM_USERS_CREATE == "users:create"

    def test_users_read(self):
        assert PERM_USERS_READ == "users:read"

    def test_users_update(self):
        assert PERM_USERS_UPDATE == "users:update"

    def test_users_delete(self):
        assert PERM_USERS_DELETE == "users:delete"

    def test_cases_create(self):
        assert PERM_CASES_CREATE == "cases:create"

    def test_cases_read(self):
        assert PERM_CASES_READ == "cases:read"

    def test_cases_update(self):
        assert PERM_CASES_UPDATE == "cases:update"

    def test_cases_delete(self):
        assert PERM_CASES_DELETE == "cases:delete"

    def test_documents_create(self):
        assert PERM_DOCUMENTS_CREATE == "documents:create"

    def test_documents_read(self):
        assert PERM_DOCUMENTS_READ == "documents:read"

    def test_documents_update(self):
        assert PERM_DOCUMENTS_UPDATE == "documents:update"

    def test_documents_delete(self):
        assert PERM_DOCUMENTS_DELETE == "documents:delete"

    def test_billing_read(self):
        assert PERM_BILLING_READ == "billing:read"

    def test_billing_update(self):
        assert PERM_BILLING_UPDATE == "billing:update"

    def test_reports_read(self):
        assert PERM_REPORTS_READ == "reports:read"

    def test_reports_export(self):
        assert PERM_REPORTS_EXPORT == "reports:export"

    def test_settings_read(self):
        assert PERM_SETTINGS_READ == "settings:read"

    def test_settings_update(self):
        assert PERM_SETTINGS_UPDATE == "settings:update"

    def test_audit_log_read(self):
        assert PERM_AUDIT_LOG_READ == "audit_log:read"

    def test_no_spaces_in_any_permission(self):
        for perm in ALL_PERMS:
            assert " " not in perm, f"{perm!r} contains a space"
