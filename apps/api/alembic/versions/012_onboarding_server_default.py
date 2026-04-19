"""add_onboarding_completed_server_default

Restores the DB-level DEFAULT false on users.onboarding_completed.

Migration 011 added the column with server_default=sa.false() to satisfy
NOT NULL during ADD COLUMN, then explicitly dropped that server_default
after the backfill. As a result, raw SQL inserts (data fixtures, scripts,
external tools) fail with NOT NULL violations unless they explicitly set
the column.

This migration re-applies the server_default so that every insert path
is safe without requiring application-layer intervention.

Revision ID: 012_onboarding_server_default
Revises: 011_add_onboarding_completed
Create Date: 2026-04-19
"""

import sqlalchemy as sa
from alembic import op

revision = "012_onboarding_server_default"
down_revision = "011_add_onboarding_completed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "onboarding_completed",
        server_default=sa.false(),
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "onboarding_completed",
        server_default=None,
    )
