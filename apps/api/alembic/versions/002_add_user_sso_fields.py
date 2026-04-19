"""Add SSO and preferences fields to users table.

Columns: auth_provider, auth_provider_id, avatar_url, preferences.

Revision ID: 002_add_user_sso_fields
Revises: 001_baseline
Create Date: 2026-04-08
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_add_user_sso_fields"
down_revision: Union[str, None] = "001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("auth_provider", sa.String(50), server_default="local", nullable=False))
    op.add_column("users", sa.Column("auth_provider_id", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("preferences", postgresql.JSONB(), server_default="{}", nullable=True))


def downgrade() -> None:
    op.drop_column("users", "preferences")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "auth_provider_id")
    op.drop_column("users", "auth_provider")
