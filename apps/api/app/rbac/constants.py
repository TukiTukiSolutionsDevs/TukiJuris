"""RBAC constants — SystemRole enum and permission strings."""

from enum import Enum


class SystemRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    SUPPORT = "support"
    FINANCE = "finance"
    VIEWER = "viewer"


# 19 permission constants — format: "{resource}:{action}"
PERM_USERS_CREATE = "users:create"
PERM_USERS_READ = "users:read"
PERM_USERS_UPDATE = "users:update"
PERM_USERS_DELETE = "users:delete"

PERM_CASES_CREATE = "cases:create"
PERM_CASES_READ = "cases:read"
PERM_CASES_UPDATE = "cases:update"
PERM_CASES_DELETE = "cases:delete"

PERM_DOCUMENTS_CREATE = "documents:create"
PERM_DOCUMENTS_READ = "documents:read"
PERM_DOCUMENTS_UPDATE = "documents:update"
PERM_DOCUMENTS_DELETE = "documents:delete"

PERM_BILLING_READ = "billing:read"
PERM_BILLING_UPDATE = "billing:update"

PERM_REPORTS_READ = "reports:read"
PERM_REPORTS_EXPORT = "reports:export"

PERM_SETTINGS_READ = "settings:read"
PERM_SETTINGS_UPDATE = "settings:update"

PERM_AUDIT_LOG_READ = "audit_log:read"

PERM_ROLES_READ = "roles:read"
PERM_ROLES_WRITE = "roles:write"

# Domain-specific permissions (Plan Maestro spec)
PERM_USERS_IMPERSONATE = "users:impersonate"
PERM_ORGANIZATIONS_READ = "organizations:read"
PERM_ORGANIZATIONS_WRITE = "organizations:write"
PERM_PLANS_READ = "plans:read"
PERM_PLANS_WRITE = "plans:write"
PERM_MODELS_READ = "models:read"
PERM_MODELS_SYNC = "models:sync"

ALL_PERMISSIONS: list[str] = [
    PERM_USERS_CREATE, PERM_USERS_READ, PERM_USERS_UPDATE, PERM_USERS_DELETE,
    PERM_USERS_IMPERSONATE,
    PERM_CASES_CREATE, PERM_CASES_READ, PERM_CASES_UPDATE, PERM_CASES_DELETE,
    PERM_DOCUMENTS_CREATE, PERM_DOCUMENTS_READ, PERM_DOCUMENTS_UPDATE, PERM_DOCUMENTS_DELETE,
    PERM_BILLING_READ, PERM_BILLING_UPDATE,
    PERM_REPORTS_READ, PERM_REPORTS_EXPORT,
    PERM_SETTINGS_READ, PERM_SETTINGS_UPDATE,
    PERM_AUDIT_LOG_READ,
    PERM_ROLES_READ, PERM_ROLES_WRITE,
    PERM_ORGANIZATIONS_READ, PERM_ORGANIZATIONS_WRITE,
    PERM_PLANS_READ, PERM_PLANS_WRITE,
    PERM_MODELS_READ, PERM_MODELS_SYNC,
]
