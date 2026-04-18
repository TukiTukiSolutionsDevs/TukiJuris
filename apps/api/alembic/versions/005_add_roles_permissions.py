"""Add roles:read and roles:write permissions and assign to admin roles.

Revision ID: 005_add_roles_permissions
Revises: 004_add_rbac
Create Date: 2026-04-16
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_add_roles_permissions"
down_revision: Union[str, None] = "004_add_rbac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Insert new permissions (idempotent)
    op.execute(sa.text("""
        INSERT INTO permissions (id, resource, action, description)
        VALUES
            (gen_random_uuid(), 'roles', 'read',  'View roles and their permission assignments'),
            (gen_random_uuid(), 'roles', 'write', 'Assign or revoke roles from users')
        ON CONFLICT (resource, action) DO NOTHING
    """))

    # Assign roles:read and roles:write to super_admin and admin
    op.execute(sa.text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE (r.name, p.resource, p.action) IN (
            ('super_admin', 'roles', 'read'),
            ('super_admin', 'roles', 'write'),
            ('admin',       'roles', 'read'),
            ('admin',       'roles', 'write')
        )
        ON CONFLICT DO NOTHING
    """))


def downgrade() -> None:
    # Remove role_permissions rows for roles:read and roles:write
    op.execute(sa.text("""
        DELETE FROM role_permissions
        WHERE permission_id IN (
            SELECT id FROM permissions
            WHERE resource = 'roles' AND action IN ('read', 'write')
        )
    """))

    # Remove the permissions themselves
    op.execute(sa.text("""
        DELETE FROM permissions
        WHERE resource = 'roles' AND action IN ('read', 'write')
    """))
