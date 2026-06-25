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
    # Idempotent: the legacy `infrastructure/sql/migration_004_sso.sql` may
    # have already added these columns when pgdata was first initialised.
    # Using IF NOT EXISTS keeps this revision safe to apply on either a
    # fresh DB (no SQL bootstrap) or a legacy DB (SQL bootstrap already ran).
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(50) NOT NULL DEFAULT 'local'"
    )
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider_id VARCHAR(255)"
    )
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT"
    )
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}'::jsonb"
    )


def downgrade() -> None:
    op.drop_column("users", "preferences")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "auth_provider_id")
    op.drop_column("users", "auth_provider")
