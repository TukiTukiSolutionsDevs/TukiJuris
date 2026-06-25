"""Persist case-analysis state per conversation.

Revision ID: 021_conversation_case_state
Revises: 020_indexes_and_sunat_prep
Create Date: 2026-06-25

Background
----------
The case-analysis flow (intake → investigation → analysis) keeps a
`case_state` dict across turns: phase, accumulated facts, pending questions,
turn count, area hint. Until this migration that state lived only in the
client's React state — refreshing the page or reopening from /historial
lost it, forcing users to start over.

This migration adds a JSONB column on `conversations` so the API can save
the latest case_state on every turn and restore it when /analizar reopens
a past conversation.

The column is NULLABLE so legacy conversations (created before this flow)
remain valid; the orchestrator treats a missing case_state as "start a
fresh intake".
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = "021_conversation_case_state"
down_revision = "020_indexes_and_sunat_prep"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("case_state", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversations", "case_state")
