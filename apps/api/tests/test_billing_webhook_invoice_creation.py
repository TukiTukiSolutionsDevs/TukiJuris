"""Tests — billing.py webhook invoice creation for MP payment.created/updated (C3)
and Culqi charge.refunded audit stub (C4).

These are unit tests: billing route handlers are called directly with mocked
deps (same pattern as test_invoice_batch_e.py::TestWebhookInvoiceCreation).
No live DB required.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_billing_webhook_invoice_creation.py -v
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mp_payload(event_type: str, status: str = "", plan: str = "pro") -> bytes:
    org_id = str(uuid.uuid4())
    payment_id = f"pay_{uuid.uuid4().hex[:10]}"
    return json.dumps({
        "id": f"evt_{uuid.uuid4().hex[:10]}",
        "type": event_type,
        "status": status,
        "data": {"id": payment_id, "status": status},
        "metadata": {"org_id": org_id, "plan": plan, "seats_count": 0},
    }).encode()


def _culqi_payload(event_type: str, charge_id: str | None = None) -> bytes:
    org_id = str(uuid.uuid4())
    cid = charge_id or f"chr_{uuid.uuid4().hex[:10]}"
    return json.dumps({
        "id": f"evt_{uuid.uuid4().hex[:10]}",
        "type": event_type,
        "data": {"id": cid, "metadata": {"org_id": org_id, "plan": "pro", "seats_count": 0}},
        "metadata": {"org_id": org_id, "plan": "pro", "seats_count": 0},
    }).encode()


def _make_request(raw: bytes) -> MagicMock:
    req = MagicMock()
    req.body = AsyncMock(return_value=raw)
    req.headers = {}
    return req


def _make_idem(is_new: bool = True) -> MagicMock:
    idem = MagicMock()
    idem.record_and_check = AsyncMock(return_value=(is_new, MagicMock()))
    idem.update_response = AsyncMock()
    return idem


def _mock_db() -> AsyncMock:
    """AsyncMock DB with begin() and begin_nested() properly returning async context managers.

    SQLAlchemy's begin() / begin_nested() are sync calls that return an async CM.
    Plain AsyncMock() makes them return a coroutine which breaks 'async with'.
    """
    db = AsyncMock()
    db.begin = MagicMock(return_value=AsyncMock())
    db.begin_nested = MagicMock(return_value=AsyncMock())
    return db


# ---------------------------------------------------------------------------
# C3 — MP payment.created creates invoice
# ---------------------------------------------------------------------------


class TestMPPaymentCreated:
    async def test_payment_created_calls_create_from_mp_payment(self):
        """payment.created → create_from_mp_payment is called."""
        from app.api.routes.billing import mercadopago_webhook

        raw = _mp_payload("payment.created")
        db = _mock_db()
        audit = MagicMock()
        audit.log_action = AsyncMock()
        idem = _make_idem()
        inv_svc = MagicMock()
        inv_svc.create_from_mp_payment = AsyncMock(return_value=(MagicMock(), True))

        with patch("app.config.settings") as mock_settings:
            mock_settings.mp_webhook_secret = None

            result = await mercadopago_webhook(
                request=_make_request(raw),
                db=db,
                audit=audit,
                idem=idem,
                inv_svc=inv_svc,
            )

        assert result == {"status": "ok"}
        inv_svc.create_from_mp_payment.assert_called_once()
        call_kwargs = inv_svc.create_from_mp_payment.call_args.kwargs
        assert call_kwargs["plan"] == "pro"

    async def test_payment_updated_approved_creates_invoice(self):
        """payment.updated with status=approved → create_from_mp_payment is called."""
        from app.api.routes.billing import mercadopago_webhook

        raw = _mp_payload("payment.updated", status="approved")
        db = _mock_db()
        audit = MagicMock()
        audit.log_action = AsyncMock()
        idem = _make_idem()
        inv_svc = MagicMock()
        inv_svc.create_from_mp_payment = AsyncMock(return_value=(MagicMock(), True))

        with patch("app.config.settings") as mock_settings:
            mock_settings.mp_webhook_secret = None

            result = await mercadopago_webhook(
                request=_make_request(raw),
                db=db,
                audit=audit,
                idem=idem,
                inv_svc=inv_svc,
            )

        assert result == {"status": "ok"}
        inv_svc.create_from_mp_payment.assert_called_once()

    async def test_payment_updated_pending_does_not_create_invoice(self):
        """payment.updated with status=pending → no invoice created."""
        from app.api.routes.billing import mercadopago_webhook

        raw = _mp_payload("payment.updated", status="pending")
        db = _mock_db()
        audit = MagicMock()
        audit.log_action = AsyncMock()
        idem = _make_idem()
        inv_svc = MagicMock()
        inv_svc.create_from_mp_payment = AsyncMock(return_value=(MagicMock(), True))

        with patch("app.config.settings") as mock_settings:
            mock_settings.mp_webhook_secret = None

            result = await mercadopago_webhook(
                request=_make_request(raw),
                db=db,
                audit=audit,
                idem=idem,
                inv_svc=inv_svc,
            )

        assert result == {"status": "ok"}
        inv_svc.create_from_mp_payment.assert_not_called()

    async def test_payment_failed_calls_create_failed(self):
        """payment.failed → create_failed(provider='mercadopago') is called."""
        from app.api.routes.billing import mercadopago_webhook

        raw = _mp_payload("payment.failed")
        db = _mock_db()
        audit = MagicMock()
        audit.log_action = AsyncMock()
        idem = _make_idem()
        inv_svc = MagicMock()
        inv_svc.create_failed = AsyncMock(return_value=(MagicMock(), True))

        with patch("app.config.settings") as mock_settings:
            mock_settings.mp_webhook_secret = None

            result = await mercadopago_webhook(
                request=_make_request(raw),
                db=db,
                audit=audit,
                idem=idem,
                inv_svc=inv_svc,
            )

        assert result == {"status": "ok"}
        inv_svc.create_failed.assert_called_once()
        call_kwargs = inv_svc.create_failed.call_args.kwargs
        assert call_kwargs["provider"] == "mercadopago"

    async def test_invoice_creation_failure_does_not_break_mp_webhook(self):
        """Invoice creation exception must not break MP webhook response."""
        from app.api.routes.billing import mercadopago_webhook

        raw = _mp_payload("payment.created")
        db = _mock_db()
        audit = MagicMock()
        audit.log_action = AsyncMock()
        idem = _make_idem()
        inv_svc = MagicMock()
        inv_svc.create_from_mp_payment = AsyncMock(side_effect=RuntimeError("DB failure"))

        with patch("app.config.settings") as mock_settings:
            mock_settings.mp_webhook_secret = None

            result = await mercadopago_webhook(
                request=_make_request(raw),
                db=db,
                audit=audit,
                idem=idem,
                inv_svc=inv_svc,
            )

        assert result == {"status": "ok"}


# ---------------------------------------------------------------------------
# C4 — Culqi charge.refunded emits audit
# ---------------------------------------------------------------------------


class TestCulqiChargeRefunded:
    async def test_charge_refunded_emits_audit_action(self):
        """charge.refunded → audit.log_action called with webhook.refund_received_unprocessed."""
        from app.api.routes.billing import culqi_webhook

        raw = _culqi_payload("charge.refunded")
        db = _mock_db()
        audit = MagicMock()
        audit.log_action = AsyncMock()
        idem = _make_idem()
        inv_svc = MagicMock()

        with patch("app.config.settings") as mock_settings:
            mock_settings.culqi_webhook_secret = None

            result = await culqi_webhook(
                request=_make_request(raw),
                db=db,
                audit=audit,
                idem=idem,
                inv_svc=inv_svc,
            )

        assert result == {"status": "ok"}
        audit.log_action.assert_called()
        # Verify the refund audit action was emitted
        actions = [
            call.kwargs.get("action") or (call.args[1] if len(call.args) > 1 else None)
            for call in audit.log_action.call_args_list
        ]
        assert "webhook.refund_received_unprocessed" in actions, (
            f"Expected 'webhook.refund_received_unprocessed' in audit actions, got: {actions}"
        )

    async def test_charge_refunded_returns_200(self):
        """charge.refunded webhook returns 200 ok (stub, not a hard failure)."""
        from app.api.routes.billing import culqi_webhook

        raw = _culqi_payload("charge.refunded")
        db = _mock_db()
        audit = MagicMock()
        audit.log_action = AsyncMock()
        idem = _make_idem()
        inv_svc = MagicMock()

        with patch("app.config.settings") as mock_settings:
            mock_settings.culqi_webhook_secret = None

            result = await culqi_webhook(
                request=_make_request(raw),
                db=db,
                audit=audit,
                idem=idem,
                inv_svc=inv_svc,
            )

        assert result == {"status": "ok"}
