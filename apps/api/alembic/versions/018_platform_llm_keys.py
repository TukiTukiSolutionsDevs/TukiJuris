"""Add platform_llm_keys table — operator-owned provider keys.

These keys back the free/pro tiers when a user has no BYOK. They are
distinct from user_llm_keys by design: cross-tenant key reuse is
forbidden, so platform keys live in their own table with a unique
constraint on `provider` (one operator key per provider).

Revision ID: 018_platform_llm_keys
Revises: 017_unique_user_llm_keys
Create Date: 2026-05-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "018_platform_llm_keys"
down_revision: Union[str, None] = "017_unique_user_llm_keys"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "platform_llm_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(50), nullable=False, unique=True),
        sa.Column("api_key_encrypted", sa.Text(), nullable=False),
        sa.Column("api_key_hint", sa.String(20), nullable=False),
        sa.Column("label", sa.String(200), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_platform_llm_keys_provider", "platform_llm_keys", ["provider"], unique=False
    )

    # Seed permission for managing platform keys.
    # The RBAC schema (migration 004/005) uses (resource, action) as the
    # composite key — see the unique constraint `uq_permissions_resource_action`.
    # The frontend exposes this as `platform_keys:write`.
    op.execute(
        """
        INSERT INTO permissions (id, resource, action, description, created_at)
        VALUES (gen_random_uuid(), 'platform_keys', 'write',
                'Manage platform-owned LLM provider keys (admin only)', now())
        ON CONFLICT (resource, action) DO NOTHING
        """
    )

    # Grant the new permission to super_admin and admin system roles.
    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r
        CROSS JOIN permissions p
        WHERE r.name IN ('super_admin', 'admin')
          AND p.resource = 'platform_keys'
          AND p.action = 'write'
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM role_permissions
        WHERE permission_id IN (
            SELECT id FROM permissions
            WHERE resource = 'platform_keys' AND action = 'write'
        )
        """
    )
    op.execute(
        "DELETE FROM permissions WHERE resource = 'platform_keys' AND action = 'write'"
    )
    op.drop_index("ix_platform_llm_keys_provider", table_name="platform_llm_keys")
    op.drop_table("platform_llm_keys")
