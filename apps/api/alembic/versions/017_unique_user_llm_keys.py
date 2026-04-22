"""add unique constraint on user_llm_keys (user_id, provider)

Revision ID: 017_unique_user_llm_keys
Revises: 016_add_password_updated_at
Create Date: 2026-04-22
"""

from alembic import op

revision = "017_unique_user_llm_keys"
down_revision = "016_add_password_updated_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Deduplicate: keep the most-recent row per (user_id, provider), delete older ones.
    # get_user_key_for_provider() already returns most-recent, so behavior is preserved.
    op.execute(
        """
        DELETE FROM user_llm_keys
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY user_id, provider
                           ORDER BY created_at DESC, id DESC
                       ) AS rn
                FROM user_llm_keys
            ) ranked
            WHERE ranked.rn > 1
        )
        """
    )
    op.create_unique_constraint(
        "uq_user_llm_keys_user_provider",
        "user_llm_keys",
        ["user_id", "provider"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_user_llm_keys_user_provider", "user_llm_keys", type_="unique")
