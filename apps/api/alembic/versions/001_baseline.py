"""Baseline — represents the schema from init.sql + manual migrations.

This is a no-op migration that marks the starting point for Alembic.
All existing tables were created by init.sql and migration_002/003/004.

Revision ID: 001_baseline
Revises: None
Create Date: 2026-04-03
"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op: tables already exist from init.sql
    # This revision marks the baseline for future Alembic-managed migrations.
    pass


def downgrade() -> None:
    # Cannot downgrade past baseline — init.sql owns this schema.
    pass
