"""admin_saas_panel indexes

Adds a composite index on refresh_tokens(user_id, created_at DESC) to support
the last_active subquery in the admin users list. Uses CONCURRENTLY to avoid
locking the hot refresh_tokens table during deployment.

Revision ID: 010_admin_saas_panel_indexes
Revises: 009_backfill_is_admin_from_rbac
Create Date: 2026-04-19
"""

from alembic import op

revision = "010_admin_saas_panel_indexes"
down_revision = "009_backfill_is_admin_from_rbac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CONCURRENTLY avoids a full table lock on the hot refresh_tokens table.
    # Requires autocommit — cannot run inside a transaction block.
    with op.get_context().autocommit_block():
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
            "ix_refresh_tokens_user_id_created_at_desc "
            "ON refresh_tokens (user_id, created_at DESC)"
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            "DROP INDEX CONCURRENTLY IF EXISTS "
            "ix_refresh_tokens_user_id_created_at_desc"
        )
