"""Saved search factory — direct SA insert for documents-search spec tests."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search import SavedSearch


async def make_saved_search(
    db: AsyncSession,
    *,
    user_id: str,
    query: str = "test legal query",
    filters: dict | None = None,
) -> SavedSearch:
    """Insert a SavedSearch row for a user.

    Returns the flushed SavedSearch instance — caller must commit the session.
    """
    search = SavedSearch(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
        query=query,
        filters=filters or {},
    )
    db.add(search)
    await db.flush()
    return search
