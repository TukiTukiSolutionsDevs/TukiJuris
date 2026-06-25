"""Split daily quota into normal and reasoning pools.

Adds `reasoning_count` to `usage_records` so we can track and cap reasoning
queries (models that use thinking/reasoning_effort) separately from normal
queries. Free tier: 4 normal + 1 reasoning per day.

Revision ID: 019_reasoning_quota
Revises: 018_platform_llm_keys
Create Date: 2026-05-04
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "019_reasoning_quota"
down_revision: Union[str, None] = "018_platform_llm_keys"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE usage_records ADD COLUMN IF NOT EXISTS reasoning_count INTEGER NOT NULL DEFAULT 0"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE usage_records DROP COLUMN IF EXISTS reasoning_count")
