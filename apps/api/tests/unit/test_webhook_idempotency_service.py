"""Unit tests for WebhookIdempotencyService (AC1, AC2, AC3, AC4, AC14).

Service uses CHECK-FIRST SELECT pattern (canonical per SA 2.0 gotcha #2):
  1. SELECT existing row — if found, return (False, existing) → no rollback, no flush
  2. If no row, INSERT + flush — the caller's `async with db.begin()` handles rollback
     on rare concurrent race (provider retries will see the row on next delivery)

All DB interactions are mocked — no live PostgreSQL required.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/unit/test_webhook_idempotency_service.py -v
"""

from unittest.mock import AsyncMock, MagicMock

from app.models.subscription import ProcessedWebhookEvent
from app.services.webhook_idempotency_service import WebhookIdempotencyService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(db: AsyncMock) -> WebhookIdempotencyService:
    return WebhookIdempotencyService(db)


def _make_db(existing: ProcessedWebhookEvent | None = None) -> AsyncMock:
    """Async mock of SQLAlchemy AsyncSession.

    Configure `existing` to simulate duplicate (check-first SELECT returns a row).
    Leave `existing=None` for the new-event path (SELECT returns no rows).
    """
    db = AsyncMock()
    db.add = MagicMock()  # synchronous call
    db.flush = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing
    db.execute = AsyncMock(return_value=mock_result)
    return db


def _make_existing_row(
    provider: str = "culqi",
    event_id: str = "evt_001",
    http_status: int = 200,
    response_body: str = '{"status":"ok"}',
) -> ProcessedWebhookEvent:
    row = ProcessedWebhookEvent()
    row.provider = provider
    row.event_id = event_id
    row.http_status = http_status
    row.response_body = response_body
    return row


# ---------------------------------------------------------------------------
# New event: happy path (AC1, AC3) — check-first SELECT returns None → INSERT
# ---------------------------------------------------------------------------


class TestRecordAndCheckNewEvent:
    async def test_new_event_returns_true_and_row(self):
        """A fresh event_id must return (True, row) after successful flush."""
        db = _make_db(existing=None)  # check-first SELECT returns None
        svc = _make_service(db)

        is_new, row = await svc.record_and_check(
            provider="culqi",
            event_id="evt_new_001",
            event_type="charge.succeeded",
            payload_hash="abc123",
        )

        assert is_new is True
        assert row is not None
        assert row.provider == "culqi"
        assert row.event_id == "evt_new_001"
        assert row.event_type == "charge.succeeded"
        assert row.payload_hash == "abc123"
        db.execute.assert_awaited_once()  # check-first SELECT
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    async def test_new_mp_event_returns_true(self):
        """MercadoPago new event must behave identically to Culqi."""
        db = _make_db(existing=None)
        svc = _make_service(db)

        is_new, row = await svc.record_and_check(
            provider="mercadopago",
            event_id="mp_evt_001",
            event_type="payment",
            payload_hash="def456",
        )

        assert is_new is True
        assert row.provider == "mercadopago"


# ---------------------------------------------------------------------------
# Duplicate event: check-first SELECT returns existing row (AC2, AC4, AC14)
# ---------------------------------------------------------------------------


class TestRecordAndCheckDuplicate:
    async def test_duplicate_returns_existing_without_flush(self):
        """When check-first SELECT finds a row, return (False, existing) with no INSERT."""
        existing = _make_existing_row()
        db = _make_db(existing=existing)
        svc = _make_service(db)

        is_new, row = await svc.record_and_check(
            provider="culqi",
            event_id="evt_001",
            event_type="charge.succeeded",
            payload_hash="abc",
        )

        assert is_new is False
        assert row is existing
        db.execute.assert_awaited_once()  # SELECT only — no INSERT path
        db.add.assert_not_called()
        db.flush.assert_not_awaited()

    async def test_duplicate_does_not_add_row(self):
        """On duplicate, db.add must NOT be called (no INSERT attempted)."""
        existing = _make_existing_row()
        db = _make_db(existing=existing)
        svc = _make_service(db)

        await svc.record_and_check("culqi", "evt_001", None, "hash")

        assert db.add.call_count == 0
        assert db.flush.await_count == 0

    async def test_duplicate_returns_none_response_when_not_cached(self):
        """Duplicate with no cached response_body still returns (False, row)."""
        existing = _make_existing_row(http_status=None, response_body=None)
        db = _make_db(existing=existing)
        svc = _make_service(db)

        is_new, row = await svc.record_and_check("culqi", "evt_001", None, "hash")

        assert is_new is False
        assert row.response_body is None


# ---------------------------------------------------------------------------
# update_response persistence
# ---------------------------------------------------------------------------


class TestUpdateResponse:
    async def test_update_response_sets_status_and_body(self):
        """update_response must set http_status and response_body on the row."""
        db = _make_db()
        svc = _make_service(db)

        row = ProcessedWebhookEvent()
        row.http_status = None
        row.response_body = None

        await svc.update_response(row, http_status=200, response_body='{"status":"ok"}')

        assert row.http_status == 200
        assert row.response_body == '{"status":"ok"}'

    async def test_update_response_marks_failure(self):
        """update_response should accept non-2xx status codes."""
        db = _make_db()
        svc = _make_service(db)

        row = ProcessedWebhookEvent()
        await svc.update_response(row, http_status=500, response_body="error")

        assert row.http_status == 500
        assert row.response_body == "error"
