"""add_password_updated_at_to_users

Revision ID: 016_add_password_updated_at
Revises: 015_trials
Create Date: 2026-04-22

"""

from alembic import op
import sqlalchemy as sa

revision = "016_add_password_updated_at"
down_revision = "015_trials"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("password_updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "password_updated_at")
