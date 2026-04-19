"""add_onboarding_completed

Adds onboarding_completed boolean column to the users table.
Backfills all existing users to TRUE so they skip the onboarding wizard
on their next login (principle of least astonishment — productive users
must not be sent back to onboarding after a deploy).

Revision ID: 011_add_onboarding_completed
Revises: 010_admin_saas_panel_indexes
Create Date: 2026-04-19
"""

import sqlalchemy as sa
from alembic import op

revision = "011_add_onboarding_completed"
down_revision = "010_admin_saas_panel_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add column with a server_default so the NOT NULL constraint is satisfied
    # for existing rows during the ALTER TABLE.
    op.add_column(
        "users",
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    # Backfill: all pre-existing users are already onboarded.
    op.execute("UPDATE users SET onboarding_completed = TRUE")
    # Drop the server_default — application layer controls future inserts.
    op.alter_column("users", "onboarding_completed", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "onboarding_completed")
