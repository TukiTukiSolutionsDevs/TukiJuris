"""Rename plan values: base -> pro, enterprise -> studio.

Schema verification (task 01): users.plan, organizations.plan, subscriptions.plan
are all String(50) / VARCHAR(50) — confirmed via ORM models. Plain UPDATE path used.

If you ever encounter a native Postgres ENUM for this column, use the alt-path:
    op.execute("ALTER TYPE plan_enum RENAME VALUE 'base' TO 'pro';")
    op.execute("ALTER TYPE plan_enum RENAME VALUE 'enterprise' TO 'studio';")
Requires Postgres >= 10 and a maintenance window (no active transactions on the type).

DEPLOY ORDER (operator responsibility — non-negotiable):
    1. pg_dump <db> > backup_pre_007.sql          # BACKUP FIRST
    2. Deploy new code (reads pro/studio, tolerates legacy during window)
    3. docker compose stop api
    4. alembic upgrade head                        # applies 007 then 008
    5. docker compose start api
    6. Smoke test: free user sees 10/day cap; pro sees BYOK; studio sees seats.

Revision ID: 007_rename_plan_values
Revises: 006_fix_usage_records_schema
Create Date: 2026-04-18
"""

from alembic import op

# revision identifiers, used by Alembic
revision: str = "007_rename_plan_values"
down_revision: str = "006_fix_usage_records_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────
    op.execute("UPDATE users SET plan = 'pro' WHERE plan = 'base';")
    op.execute("UPDATE users SET plan = 'studio' WHERE plan = 'enterprise';")

    # ── organizations ──────────────────────────────────────────────────────
    op.execute("UPDATE organizations SET plan = 'pro' WHERE plan = 'base';")
    op.execute("UPDATE organizations SET plan = 'studio' WHERE plan = 'enterprise';")

    # ── subscriptions ──────────────────────────────────────────────────────
    op.execute("UPDATE subscriptions SET plan = 'pro' WHERE plan = 'base';")
    op.execute("UPDATE subscriptions SET plan = 'studio' WHERE plan = 'enterprise';")


def downgrade() -> None:
    # This migration is FORWARD-ONLY per proposal §Risks.
    # Reason: renaming back would re-introduce legacy IDs that new code no
    # longer handles. Restore from pre-migration backup instead.
    raise NotImplementedError(
        "007_rename_plan_values is forward-only. "
        "Restore from backup_pre_007.sql to roll back."
    )
