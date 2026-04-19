"""webhook_idempotency_dedupe_table

Adds `processed_webhook_events` table used for at-most-once processing
of Culqi and MercadoPago webhooks.

Schema:
  - BIGSERIAL primary key
  - provider  TEXT NOT NULL   CHECK (provider IN ('culqi','mercadopago'))
  - event_id  TEXT NOT NULL
  - UNIQUE (provider, event_id)  -- the idempotency key
  - event_type, payload_hash (SHA-256 of raw body) for forensics
  - http_status, response_body for provider replay debugging
  - processed_at TIMESTAMPTZ server default now()

Revision ID: 013_webhook_dedupe
Revises: 012_onboarding_server_default
Create Date: 2026-04-19
"""

import sqlalchemy as sa
from alembic import op

revision = "013_webhook_dedupe"
down_revision = "012_onboarding_server_default"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "processed_webhook_events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("provider", sa.String, nullable=False),
        sa.Column("event_id", sa.String, nullable=False),
        sa.Column("event_type", sa.String, nullable=True),
        sa.Column("payload_hash", sa.String, nullable=True),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("http_status", sa.Integer, nullable=True),
        sa.Column("response_body", sa.Text, nullable=True),
        sa.CheckConstraint(
            "provider IN ('culqi','mercadopago')",
            name="ck_webhook_provider",
        ),
    )
    op.create_index(
        "ux_processed_webhook_events_provider_event_id",
        "processed_webhook_events",
        ["provider", "event_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ux_processed_webhook_events_provider_event_id",
        table_name="processed_webhook_events",
    )
    op.drop_table("processed_webhook_events")
