"""Add RBAC tables: roles, permissions, role_permissions, user_roles, audit_log.

Seeds system roles and permissions, then migrates existing admins to super_admin.

Revision ID: 004_add_rbac
Revises: 003_add_refresh_tokens
Create Date: 2026-04-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_add_rbac"
down_revision: Union[str, None] = "003_add_refresh_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. Create tables                                                     #
    # ------------------------------------------------------------------ #

    op.create_table(
        "roles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("uq_roles_name", "roles", ["name"], unique=True)

    op.create_table(
        "permissions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("resource", sa.String(50), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_permissions_resource", "permissions", ["resource"])
    op.create_unique_constraint(
        "uq_permissions_resource_action", "permissions", ["resource", "action"]
    )

    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "permission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "assigned_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])

    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("before_state", postgresql.JSONB, nullable=True),
        sa.Column("after_state", postgresql.JSONB, nullable=True),
        sa.Column("ip_address", postgresql.INET, nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_audit_log_action", "audit_log", ["action"])
    op.create_index("ix_audit_log_resource_type", "audit_log", ["resource_type"])
    op.create_index("ix_audit_log_resource_id", "audit_log", ["resource_id"])

    # ------------------------------------------------------------------ #
    # 2. Seed system roles and permissions (idempotent)                    #
    # ------------------------------------------------------------------ #

    op.execute(sa.text("""
        INSERT INTO roles (id, name, display_name, description, is_system)
        VALUES
            (gen_random_uuid(), 'super_admin', 'Super Administrator', 'Full access to everything', true),
            (gen_random_uuid(), 'admin',       'Administrator',       'Manages content, users, and org settings', true),
            (gen_random_uuid(), 'support',     'Support',             'Read-only access plus limited write', true),
            (gen_random_uuid(), 'finance',     'Finance',             'Billing and subscription access', true),
            (gen_random_uuid(), 'viewer',      'Viewer',              'Read-only access', true)
        ON CONFLICT (name) DO NOTHING
    """))

    op.execute(sa.text("""
        INSERT INTO permissions (id, resource, action, description)
        VALUES
            (gen_random_uuid(), 'users',     'create',  'Create new users'),
            (gen_random_uuid(), 'users',     'read',    'View user profiles'),
            (gen_random_uuid(), 'users',     'update',  'Edit user profiles'),
            (gen_random_uuid(), 'users',     'delete',  'Delete/deactivate users'),
            (gen_random_uuid(), 'cases',     'create',  'Create legal cases'),
            (gen_random_uuid(), 'cases',     'read',    'View cases'),
            (gen_random_uuid(), 'cases',     'update',  'Update case data'),
            (gen_random_uuid(), 'cases',     'delete',  'Delete cases'),
            (gen_random_uuid(), 'documents', 'create',  'Upload documents'),
            (gen_random_uuid(), 'documents', 'read',    'View/download documents'),
            (gen_random_uuid(), 'documents', 'update',  'Edit document metadata'),
            (gen_random_uuid(), 'documents', 'delete',  'Delete documents'),
            (gen_random_uuid(), 'billing',   'read',    'View billing info'),
            (gen_random_uuid(), 'billing',   'update',  'Update billing/payment'),
            (gen_random_uuid(), 'reports',   'read',    'View reports'),
            (gen_random_uuid(), 'reports',   'export',  'Export reports'),
            (gen_random_uuid(), 'settings',  'read',    'View system settings'),
            (gen_random_uuid(), 'settings',  'update',  'Update system settings'),
            (gen_random_uuid(), 'audit_log', 'read',    'View audit log')
        ON CONFLICT (resource, action) DO NOTHING
    """))

    # Map every permission in the matrix to the right role
    op.execute(sa.text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE (r.name, p.resource, p.action) IN (
            -- super_admin: all 19
            ('super_admin','users','create'),   ('super_admin','users','read'),
            ('super_admin','users','update'),   ('super_admin','users','delete'),
            ('super_admin','cases','create'),   ('super_admin','cases','read'),
            ('super_admin','cases','update'),   ('super_admin','cases','delete'),
            ('super_admin','documents','create'),('super_admin','documents','read'),
            ('super_admin','documents','update'),('super_admin','documents','delete'),
            ('super_admin','billing','read'),   ('super_admin','billing','update'),
            ('super_admin','reports','read'),   ('super_admin','reports','export'),
            ('super_admin','settings','read'),  ('super_admin','settings','update'),
            ('super_admin','audit_log','read'),
            -- admin: 17
            ('admin','users','create'),   ('admin','users','read'),
            ('admin','users','update'),   ('admin','users','delete'),
            ('admin','cases','create'),   ('admin','cases','read'),
            ('admin','cases','update'),   ('admin','cases','delete'),
            ('admin','documents','create'),('admin','documents','read'),
            ('admin','documents','update'),('admin','documents','delete'),
            ('admin','billing','read'),
            ('admin','reports','read'),   ('admin','reports','export'),
            ('admin','settings','read'),
            ('admin','audit_log','read'),
            -- support: 5
            ('support','users','read'), ('support','cases','read'),
            ('support','documents','read'), ('support','reports','read'),
            ('support','settings','read'),
            -- finance: 6
            ('finance','users','read'), ('finance','cases','read'),
            ('finance','documents','read'),
            ('finance','billing','read'), ('finance','billing','update'),
            ('finance','reports','read'),
            -- viewer: 4
            ('viewer','users','read'), ('viewer','cases','read'),
            ('viewer','documents','read'), ('viewer','reports','read')
        )
        ON CONFLICT DO NOTHING
    """))

    # ------------------------------------------------------------------ #
    # 3. Data migration: is_admin=true → super_admin role                 #
    # ------------------------------------------------------------------ #

    op.execute(sa.text("""
        INSERT INTO user_roles (user_id, role_id, assigned_at)
        SELECT u.id, r.id, now()
        FROM users u, roles r
        WHERE u.is_admin = true
          AND r.name = 'super_admin'
        ON CONFLICT DO NOTHING
    """))


def downgrade() -> None:
    op.drop_index("ix_audit_log_resource_id", table_name="audit_log")
    op.drop_index("ix_audit_log_resource_type", table_name="audit_log")
    op.drop_index("ix_audit_log_action", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_user_roles_user_id", table_name="user_roles")
    op.drop_table("user_roles")

    op.drop_table("role_permissions")

    op.drop_constraint("uq_permissions_resource_action", "permissions", type_="unique")
    op.drop_index("ix_permissions_resource", table_name="permissions")
    op.drop_table("permissions")

    op.drop_index("uq_roles_name", table_name="roles")
    op.drop_table("roles")
