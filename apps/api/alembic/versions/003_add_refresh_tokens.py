"""Add refresh_tokens table.

Stores one row per issued refresh token: hash, family, expiry, revocation.
Access tokens are stateless; only refresh tokens are persisted.

Revision ID: 003_add_refresh_tokens
Revises: 002_add_user_sso_fields
Create Date: 2026-04-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_add_refresh_tokens"
down_revision: Union[str, None] = "002_add_user_sso_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # jti: JWT ID — unique per token, used for fast lookup and revocation
        sa.Column("jti", sa.String(36), nullable=False),
        # user_id: CASCADE delete — revoking a user clears all their tokens
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        # family_id: rotation theft-detection — all tokens from one login share a family
        sa.Column("family_id", sa.String(36), nullable=False),
        # token_hash: SHA-256 of the raw token — raw token is never stored
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # FK: user_id → users.id — named for clean downgrade
    op.create_foreign_key(
        "fk_refresh_tokens_user_id",
        "refresh_tokens",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Unique index on jti — O(1) token lookup and revocation
    op.create_index("uq_refresh_tokens_jti", "refresh_tokens", ["jti"], unique=True)
    # Non-unique index on user_id — list/revoke all tokens for a user
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    # Non-unique index on family_id — theft-detection family scan
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"])


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index("uq_refresh_tokens_jti", table_name="refresh_tokens")
    op.drop_constraint("fk_refresh_tokens_user_id", "refresh_tokens", type_="foreignkey")
    op.drop_table("refresh_tokens")
