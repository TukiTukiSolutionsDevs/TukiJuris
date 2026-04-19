"""RBAC seed — idempotent setup of roles, permissions, and mappings."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.rbac.constants import SystemRole

SYSTEM_ROLES: list[dict] = [
    {"name": SystemRole.SUPER_ADMIN.value, "display_name": "Super Administrator",
     "description": "Full access to everything", "is_system": True},
    {"name": SystemRole.ADMIN.value, "display_name": "Administrator",
     "description": "Manages content, users, and org settings", "is_system": True},
    {"name": SystemRole.SUPPORT.value, "display_name": "Support",
     "description": "Read-only access plus limited write", "is_system": True},
    {"name": SystemRole.FINANCE.value, "display_name": "Finance",
     "description": "Billing and subscription access", "is_system": True},
    {"name": SystemRole.VIEWER.value, "display_name": "Viewer",
     "description": "Read-only access", "is_system": True},
]

SYSTEM_PERMISSIONS: list[dict] = [
    {"resource": "users",         "action": "create",      "description": "Create new users"},
    {"resource": "users",         "action": "read",        "description": "View user profiles"},
    {"resource": "users",         "action": "update",      "description": "Edit user profiles"},
    {"resource": "users",         "action": "delete",      "description": "Delete/deactivate users"},
    {"resource": "users",         "action": "impersonate", "description": "Impersonate another user"},
    {"resource": "cases",         "action": "create",      "description": "Create legal cases"},
    {"resource": "cases",         "action": "read",        "description": "View cases"},
    {"resource": "cases",         "action": "update",      "description": "Update case data"},
    {"resource": "cases",         "action": "delete",      "description": "Delete cases"},
    {"resource": "documents",     "action": "create",      "description": "Upload documents"},
    {"resource": "documents",     "action": "read",        "description": "View/download documents"},
    {"resource": "documents",     "action": "update",      "description": "Edit document metadata"},
    {"resource": "documents",     "action": "delete",      "description": "Delete documents"},
    {"resource": "billing",       "action": "read",        "description": "View billing info"},
    {"resource": "billing",       "action": "update",      "description": "Update billing/payment"},
    {"resource": "reports",       "action": "read",        "description": "View reports"},
    {"resource": "reports",       "action": "export",      "description": "Export reports"},
    {"resource": "settings",      "action": "read",        "description": "View system settings"},
    {"resource": "settings",      "action": "update",      "description": "Update system settings"},
    {"resource": "audit_log",     "action": "read",        "description": "View audit log"},
    {"resource": "roles",         "action": "read",        "description": "View roles"},
    {"resource": "roles",         "action": "write",       "description": "Assign/revoke roles"},
    {"resource": "organizations", "action": "read",        "description": "View organizations"},
    {"resource": "organizations", "action": "write",       "description": "Edit organizations"},
    {"resource": "plans",         "action": "read",        "description": "View subscription plans"},
    {"resource": "plans",         "action": "write",       "description": "Create/edit plans"},
    {"resource": "models",        "action": "read",        "description": "View AI models"},
    {"resource": "models",        "action": "sync",        "description": "Sync AI model catalog"},
]

ROLE_PERMISSION_MATRIX: dict[str, list[str]] = {
    SystemRole.SUPER_ADMIN.value: [
        "users:create", "users:read", "users:update", "users:delete", "users:impersonate",
        "cases:create", "cases:read", "cases:update", "cases:delete",
        "documents:create", "documents:read", "documents:update", "documents:delete",
        "billing:read", "billing:update",
        "reports:read", "reports:export",
        "settings:read", "settings:update",
        "audit_log:read",
        "roles:read", "roles:write",
        "organizations:read", "organizations:write",
        "plans:read", "plans:write",
        "models:read", "models:sync",
    ],
    SystemRole.ADMIN.value: [
        "users:create", "users:read", "users:update", "users:delete",
        "cases:create", "cases:read", "cases:update", "cases:delete",
        "documents:create", "documents:read", "documents:update", "documents:delete",
        "billing:read",
        "reports:read", "reports:export",
        "settings:read",
        "audit_log:read",
        "roles:read",
        "organizations:read", "organizations:write",
        "plans:read",
        "models:read",
    ],
    SystemRole.SUPPORT.value: [
        "users:read", "cases:read", "documents:read", "reports:read", "settings:read",
        "organizations:read",
    ],
    SystemRole.FINANCE.value: [
        "users:read", "cases:read", "documents:read",
        "billing:read", "billing:update", "reports:read",
        "organizations:read", "plans:read",
    ],
    SystemRole.VIEWER.value: [
        "users:read", "cases:read", "documents:read", "reports:read",
        "organizations:read", "plans:read", "models:read",
    ],
}


async def seed_roles_and_permissions(db: AsyncSession) -> None:
    """Insert system roles, permissions, and role-permission mappings.

    Idempotent: ON CONFLICT DO NOTHING makes repeated calls safe.
    """
    for role in SYSTEM_ROLES:
        await db.execute(
            text(
                "INSERT INTO roles (id, name, display_name, description, is_system, created_at) "
                "VALUES (gen_random_uuid(), :name, :display_name, :description, :is_system, now()) "
                "ON CONFLICT (name) DO NOTHING"
            ),
            role,
        )

    for perm in SYSTEM_PERMISSIONS:
        await db.execute(
            text(
                "INSERT INTO permissions (id, resource, action, description, created_at) "
                "VALUES (gen_random_uuid(), :resource, :action, :description, now()) "
                "ON CONFLICT (resource, action) DO NOTHING"
            ),
            perm,
        )

    for role_name, perms in ROLE_PERMISSION_MATRIX.items():
        for perm_str in perms:
            resource, action = perm_str.split(":", 1)
            await db.execute(
                text(
                    "INSERT INTO role_permissions (role_id, permission_id) "
                    "SELECT r.id, p.id FROM roles r, permissions p "
                    "WHERE r.name = :role_name "
                    "  AND p.resource = :resource AND p.action = :action "
                    "ON CONFLICT DO NOTHING"
                ),
                {"role_name": role_name, "resource": resource, "action": action},
            )

    await db.commit()
