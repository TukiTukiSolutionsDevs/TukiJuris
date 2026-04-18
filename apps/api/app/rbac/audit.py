"""AuditService — write and query AuditLog records.

Provides:
  - log_action(...)  → writes one AuditLog row, flushes immediately
  - query_log(...)   → paginated query with optional filters
"""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.rbac.models import AuditLog


class AuditService:
    """Handles writing and querying the audit_log table."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def log_action(
        self,
        user_id: uuid.UUID | None,
        action: str,
        resource_type: str | None,
        resource_id: str | None = None,
        before_state: dict | None = None,
        after_state: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Create and flush one AuditLog record.

        Does NOT commit — the caller's transaction owns the commit boundary.
        Use BackgroundTasks at the route layer if you want non-blocking writes.
        """
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._db.add(entry)
        await self._db.flush()
        return entry

    async def query_log(
        self,
        page: int,
        page_size: int,
        filters: dict,
    ) -> tuple[list[AuditLog], int]:
        """Return a paginated page of AuditLog rows plus the total count.

        Supported filter keys:
          user_id       (uuid.UUID)  — exact match
          action        (str)        — exact match
          resource_type (str)        — exact match
          date_from     (datetime)   — inclusive lower bound on created_at
          date_to       (datetime)   — inclusive upper bound on created_at
        """
        conditions = []

        if user_id := filters.get("user_id"):
            conditions.append(AuditLog.user_id == user_id)
        if action := filters.get("action"):
            conditions.append(AuditLog.action == action)
        if resource_type := filters.get("resource_type"):
            conditions.append(AuditLog.resource_type == resource_type)
        if date_from := filters.get("date_from"):
            conditions.append(AuditLog.created_at >= date_from)
        if date_to := filters.get("date_to"):
            conditions.append(AuditLog.created_at <= date_to)

        # COUNT query
        count_stmt = select(func.count()).select_from(AuditLog)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        count_result = await self._db.execute(count_stmt)
        total: int = count_result.scalar() or 0

        # ROWS query
        offset = (page - 1) * page_size
        rows_stmt = (
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        if conditions:
            rows_stmt = rows_stmt.where(*conditions)
        rows_result = await self._db.execute(rows_stmt)
        items = rows_result.scalars().all()

        return list(items), total
