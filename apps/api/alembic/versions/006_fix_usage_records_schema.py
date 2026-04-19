"""Fix usage_records schema — replace month VARCHAR with day DATE, nullable org.

This is a DESTRUCTIVE forward-only migration. Existing usage data is discarded
(acceptable per spec §6 — beta has no active usage tracking history).

Rollout order (operator responsibility):
  1. pg_dump <db> > backup_pre_006.sql   # BACKUP FIRST
  2. docker compose stop api
  3. alembic upgrade head                 # this migration
  4. docker compose start api
  5. smoke: POST /api/chat/query with a free-plan user — expect 200, not 500

Revision ID: 006_fix_usage_records_schema
Revises: 005_add_roles_permissions
Create Date: 2026-04-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "006_fix_usage_records_schema"
down_revision: Union[str, None] = "005_add_roles_permissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Destructive: drop old table and all its constraints/indexes with it.
    # The old schema had VARCHAR(7) month, NOT NULL organization_id, and
    # column names queries_used/tokens_used — all replaced below.
    op.drop_table("usage_records")

    op.create_table(
        "usage_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,  # NULL for free-tier users without an org
        ),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("query_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_foreign_key(
        "fk_usage_records_user_id",
        "usage_records",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_usage_records_organization_id",
        "usage_records",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Individual column indexes
    op.create_index("ix_usage_records_user_id", "usage_records", ["user_id"])
    op.create_index("ix_usage_records_organization_id", "usage_records", ["organization_id"])
    op.create_index("ix_usage_records_day", "usage_records", ["day"])

    # Composite unique index — guarantees one row per (user, day)
    op.create_index(
        "uq_usage_records_user_day",
        "usage_records",
        ["user_id", "day"],
        unique=True,
    )

    # Composite index for org-level monthly aggregation (check_limit / get_usage)
    op.create_index(
        "ix_usage_records_org_day",
        "usage_records",
        ["organization_id", "day"],
    )


def downgrade() -> None:
    # Forward-only: the old VARCHAR(7) month schema cannot be reconstructed
    # from daily rows without data loss (multiple days per month collapse).
    # Per spec §6, rollback path is "restore from pre-migration backup", not
    # "alembic downgrade".
    raise NotImplementedError(
        "006_fix_usage_records_schema is forward-only. "
        "Restore from a pre-migration backup (backup_pre_006.sql) to roll back."
    )
