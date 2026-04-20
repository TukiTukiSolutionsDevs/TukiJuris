"""
Webhook idempotency service — DB-backed at-most-once processing.

Pattern: CHECK-FIRST SELECT → INSERT if absent → flush (canonical per SA gotcha #2).

Why check-first (not flush+catch+rollback)?
  - Webhook retries arrive SERIALLY from providers (Culqi/MP wait for 2xx before retrying).
  - flush+catch+rollback breaks composability with `async with db.begin()` (two-phase commit
    canonical). An inner rollback poisons the outer transaction context manager, causing
    `InvalidRequestError: Can't operate on closed transaction` on subsequent ops.
  - See: `tukijuris/sqlalchemy-async-gotchas` #2, `tukijuris/webhook-two-phase-commit`.

TOCTOU consideration:
  - Pre-check SELECT *could* race against a truly-concurrent INSERT (two webhooks arriving
    in the same instant from different processes). If that happens, the flush raises
    IntegrityError and the outer `async with db.begin()` rolls back. The provider retries,
    and on retry the SELECT finds the row → returns (False, existing). Zero duplicates.

Usage:
    svc = WebhookIdempotencyService(db)
    async with db.begin():
        is_new, row = await svc.record_and_check(provider, event_id, event_type, payload_hash)
        if not is_new:
            return {"status": "duplicate_ignored"}  # outer CM commits no-op
        # ... do business work ...
        await svc.update_response(row, http_status=200, response_body='{"status":"ok"}')
    # outer CM commits
"""

from __future__ import annotations

import logging

from sqlalchemy import select
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

        Safe to call inside `async with db.begin()` — uses check-first SELECT, no
        internal rollback. If a truly-concurrent race causes flush to raise
        IntegrityError, the exception bubbles up and the outer CM rolls back; the
        provider retry will see the existing row on next delivery.
        """
        # Check-first SELECT (canonical — avoids begin_nested / rollback poisoning)
        result = await self.db.execute(
            select(ProcessedWebhookEvent).where(
                ProcessedWebhookEvent.provider == provider,
                ProcessedWebhookEvent.event_id == event_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            logger.info(
                "webhook.idempotency: duplicate event provider=%s event_id=%s — skipping",
                provider,
                event_id,
            )
            return False, existing

        # Not seen before — INSERT. Any concurrent-race IntegrityError bubbles up
        # to the outer `async with db.begin()` (caller contract).
        row = ProcessedWebhookEvent(
            provider=provider,
            event_id=event_id,
            event_type=event_type,
            payload_hash=payload_hash,
        )
        self.db.add(row)
        await self.db.flush()
        logger.debug(
            "webhook.idempotency: new event provider=%s event_id=%s",
            provider,
            event_id,
        )
        return True, row

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
