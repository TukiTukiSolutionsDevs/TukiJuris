"""Add seat pricing columns to organizations and price_cents to subscriptions.

Nullability rationale:
  - organizations.base_seats_included / seat_price_cents / base_price_cents:
    nullable because free/pro orgs have no seat pricing. Enforcing NOT NULL
    would require synthetic defaults that misrepresent the org's tier.
  - subscriptions.price_cents: NOT NULL, server_default=0 during fill,
    then server_default dropped so future inserts must set it explicitly.

Revision ID: 008_org_seat_pricing
Revises: 007_rename_plan_values
Create Date: 2026-04-18
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic
revision: str = "008_org_seat_pricing"
down_revision: str = "007_rename_plan_values"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── organizations — seat pricing fields ────────────────────────────────
    op.add_column(
        "organizations",
        sa.Column("base_seats_included", sa.Integer(), nullable=True),
    )
    op.add_column(
        "organizations",
        sa.Column("seat_price_cents", sa.Integer(), nullable=True),
    )
    op.add_column(
        "organizations",
        sa.Column("base_price_cents", sa.Integer(), nullable=True),
    )

    # ── subscriptions — standardise price in integer cents ─────────────────
    # Add with server_default so existing rows get 0 (not NULL).
    op.add_column(
        "subscriptions",
        sa.Column(
            "price_cents",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    # Drop server_default so future inserts must be explicit.
    op.alter_column("subscriptions", "price_cents", server_default=None)


def downgrade() -> None:
    op.drop_column("subscriptions", "price_cents")
    op.drop_column("organizations", "base_price_cents")
    op.drop_column("organizations", "seat_price_cents")
    op.drop_column("organizations", "base_seats_included")
