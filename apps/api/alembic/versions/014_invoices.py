"""Add invoices table.

Revision ID: 014_invoices
Revises: 013_webhook_dedupe
Create Date: 2026-04-19
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "014_invoices"
down_revision = "013_webhook_dedupe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
        ),
        sa.Column(
            "subscription_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subscriptions.id"),
            nullable=True,
        ),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("provider_charge_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="PEN"),
        sa.Column("base_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("seats_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("seat_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("subtotal_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("plan", sa.String(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refund_reason", sa.Text(), nullable=True),
        sa.Column("void_reason", sa.Text(), nullable=True),
        sa.Column("provider_event_id", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("provider", "provider_charge_id", name="uq_invoices_provider_charge"),
        sa.CheckConstraint(
            "provider IN ('culqi','mercadopago')",
            name="ck_invoices_provider",
        ),
        sa.CheckConstraint(
            "status IN ('pending','paid','failed','refunded','voided')",
            name="ck_invoices_status",
        ),
        sa.CheckConstraint(
            "currency = 'PEN'",
            name="ck_invoices_currency",
        ),
    )
    op.create_index("ix_invoices_org_created", "invoices", ["org_id", sa.text("created_at DESC")])
    op.create_index("ix_invoices_status_paid", "invoices", ["status", "paid_at"])
    op.create_index("ix_invoices_provider_event", "invoices", ["provider_event_id"])


def downgrade() -> None:
    op.drop_index("ix_invoices_provider_event", table_name="invoices")
    op.drop_index("ix_invoices_status_paid", table_name="invoices")
    op.drop_index("ix_invoices_org_created", table_name="invoices")
    op.drop_table("invoices")
