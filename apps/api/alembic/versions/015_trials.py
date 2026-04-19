"""Add trials table.

Revision ID: 015_trials
Revises: 014_invoices
Create Date: 2026-04-19
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "015_trials"
down_revision = "014_invoices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("plan_code", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        # Card
        sa.Column("card_added_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider", sa.String(10), nullable=True),
        sa.Column("provider_customer_id", sa.String(200), nullable=True),
        sa.Column("provider_card_token", sa.String(200), nullable=True),
        # Outcome
        sa.Column("charged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("charge_failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("charge_failure_reason", sa.String(500), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        # Cancel / downgrade
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "canceled_by_user",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("downgraded_at", sa.DateTime(timezone=True), nullable=True),
        # FK to subscription (set on auto-charge success)
        sa.Column(
            "subscription_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subscriptions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Row timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Constraints
        sa.UniqueConstraint("user_id", "plan_code", name="uq_trials_user_plan"),
        sa.CheckConstraint("ends_at > started_at", name="ck_trials_ends_after_start"),
        sa.CheckConstraint(
            "status IN ('active','charged','charge_failed','downgraded',"
            "'canceled_pending','canceled')",
            name="ck_trials_status",
        ),
        sa.CheckConstraint(
            "plan_code IN ('pro','studio')",
            name="ck_trials_plan_code",
        ),
        sa.CheckConstraint(
            "provider IS NULL OR provider IN ('culqi','mp')",
            name="ck_trials_provider",
        ),
    )

    op.create_index("ix_trials_user_id", "trials", ["user_id"])
    op.create_index("idx_trials_status_ends_at", "trials", ["status", "ends_at"])
    op.create_index(
        "uix_trials_user_active",
        "trials",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "idx_trials_charge_failed_retry",
        "trials",
        ["status", "charge_failed_at"],
        postgresql_where=sa.text("status = 'charge_failed'"),
    )


def downgrade() -> None:
    op.drop_index("idx_trials_charge_failed_retry", table_name="trials")
    op.drop_index("uix_trials_user_active", table_name="trials")
    op.drop_index("idx_trials_status_ends_at", table_name="trials")
    op.drop_index("ix_trials_user_id", table_name="trials")
    op.drop_table("trials")
