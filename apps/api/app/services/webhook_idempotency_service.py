"""
Webhook idempotency service — DB-backed at-most-once processing.

Pattern: INSERT + flush → catch IntegrityError (unique violation on
(provider, event_id)) → rollback → SELECT existing row.

This avoids the TOCTOU race that a pre-check SELECT would have:
  - Pre-check: two concurrent requests both see "no row", both INSERT → duplicate.
  - Flush/catch: DB constraint is the arbiter; only one INSERT wins.

Usage:
    svc = WebhookIdempotencyService(db)
    is_new, row = await svc.record_and_check(provider, event_id, event_type, payload_hash)
    if not is_new:
        return {"status": "duplicate_ignored"}
    # ... do business work ...
    await svc.update_response(row, http_status=200, response_body='{"status":"ok"}')
    await db.commit()
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import ProcessedWebhookEvent

logger = logging.getLogger(__name__)


class WebhookIdempotencyService:
    """Encapsulates deduplification logic for incoming payment webhooks."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record_and_check(
        self,
        provider: str,
        event_id: str,
        event_type: str | None,
        payload_hash: str | None,
    ) -> tuple[bool, ProcessedWebhookEvent]:
        """
        Attempt to record a new webhook event.

        Returns:
            (True, new_row)      — event is new; caller must execute business logic.
            (False, existing_row) — duplicate; caller must return duplicate_ignored.

        The caller is responsible for calling `update_response` after business
        logic completes, and for `db.commit()`.
        """
        row = ProcessedWebhookEvent(
            provider=provider,
            event_id=event_id,
            event_type=event_type,
            payload_hash=payload_hash,
        )
        self.db.add(row)

        try:
            await self.db.flush()
            logger.debug(
                "webhook.idempotency: new event provider=%s event_id=%s",
                provider,
                event_id,
            )
            return True, row

        except IntegrityError:
            # Unique constraint on (provider, event_id) fired — this is a replay.
            await self.db.rollback()
            logger.info(
                "webhook.idempotency: duplicate event provider=%s event_id=%s — skipping",
                provider,
                event_id,
            )
            result = await self.db.execute(
                select(ProcessedWebhookEvent).where(
                    ProcessedWebhookEvent.provider == provider,
                    ProcessedWebhookEvent.event_id == event_id,
                )
            )
            existing = result.scalar_one()
            return False, existing

    async def update_response(
        self,
        row: ProcessedWebhookEvent,
        http_status: int,
        response_body: str,
    ) -> None:
        """
        Persist the HTTP response that was sent for this event.

        Call AFTER business logic succeeds and BEFORE db.commit().
        Stored for provider replay debugging — not used as a dedupe key.
        """
        row.http_status = http_status
        row.response_body = response_body
