"""Unit tests for WebhookIdempotencyService (AC1, AC2, AC3, AC4, AC14).

All DB interactions are mocked — no live PostgreSQL required.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/unit/test_webhook_idempotency_service.py -v
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.subscription import ProcessedWebhookEvent
from app.services.webhook_idempotency_service import WebhookIdempotencyService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(db: AsyncMock) -> WebhookIdempotencyService:
    return WebhookIdempotencyService(db)


def _make_db() -> AsyncMock:
    """Async mock of SQLAlchemy AsyncSession."""
    db = AsyncMock()
    db.add = MagicMock()  # synchronous call
    db.flush = AsyncMock()
    db.rollback = AsyncMock()
    db.execute = AsyncMock()
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
# T2.1 — New event: happy path (AC1, AC3)
# ---------------------------------------------------------------------------


class TestRecordAndCheckNewEvent:
    async def test_new_event_returns_true_and_row(self):
        """A fresh event_id must return (True, row) after successful flush."""
        db = _make_db()
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
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    async def test_new_mp_event_returns_true(self):
        """MercadoPago new event must behave identically to Culqi."""
        db = _make_db()
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
# T2.1 — Duplicate event: IntegrityError path (AC2, AC4, AC14)
# ---------------------------------------------------------------------------


class TestRecordAndCheckDuplicate:
    async def test_duplicate_triggers_rollback_and_returns_existing(self):
        """On IntegrityError (unique violation), rollback + return existing row."""
        db = _make_db()
        db.flush = AsyncMock(
            side_effect=IntegrityError(
                statement="INSERT", params={}, orig=Exception("unique violation")
            )
        )

        existing = _make_existing_row()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = existing
        db.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(db)

        is_new, row = await svc.record_and_check(
            provider="culqi",
            event_id="evt_001",
            event_type="charge.succeeded",
            payload_hash="abc",
        )

        assert is_new is False
        assert row is existing
        db.rollback.assert_awaited_once()
        db.execute.assert_awaited_once()  # SELECT for existing row

    async def test_duplicate_does_not_re_add_row(self):
        """On duplicate, db.add must NOT be called a second time."""
        db = _make_db()
        db.flush = AsyncMock(
            side_effect=IntegrityError("INSERT", {}, Exception("dup"))
        )
        existing = _make_existing_row()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = existing
        db.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(db)
        await svc.record_and_check("culqi", "evt_001", None, "hash")

        # add is called once for the initial INSERT attempt, then NOT again
        assert db.add.call_count == 1

    async def test_duplicate_returns_none_response_when_not_cached(self):
        """Duplicate with no cached response_body still returns (False, row)."""
        db = _make_db()
        db.flush = AsyncMock(
            side_effect=IntegrityError("INSERT", {}, Exception("dup"))
        )
        existing = _make_existing_row(http_status=None, response_body=None)
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = existing
        db.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(db)
        is_new, row = await svc.record_and_check("culqi", "evt_001", None, "hash")

        assert is_new is False
        assert row.response_body is None


# ---------------------------------------------------------------------------
# T2.1 — update_response persistence
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
