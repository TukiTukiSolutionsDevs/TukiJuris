"""Batch E tests — webhook integration + admin revenue from invoices.

Tests:
  TestRevenueFromInvoices   — AdminMetricsService.compute_revenue() prefers invoices
  TestWebhookInvoiceCreation — billing.py webhook handlers call InvoiceService

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_invoice_batch_e.py -v
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.admin_metrics_service import AdminMetricsService
from app.services.plan_service import PlanService


# ---------------------------------------------------------------------------
# Helpers shared with test_admin_metrics_service.py
# ---------------------------------------------------------------------------


def _exec_mock(*row_lists):
    db = AsyncMock()
    side_effects = []
    for rows in row_lists:
        result = MagicMock()
        result.mappings.return_value.fetchall.return_value = rows
        side_effects.append(result)
    db.execute.side_effect = side_effects
    return db


# ---------------------------------------------------------------------------
# Revenue from invoices (AdminMetricsService)
# ---------------------------------------------------------------------------


class TestRevenueFromInvoices:
    async def test_uses_invoices_when_paid_invoices_exist(self):
        """When invoices table has paid rows, source='invoices'."""
        invoice_rows = [
            {"plan": "pro", "org_count": 2, "revenue_cents": 16520},  # 2×S/82.60
        ]
        # First execute = invoices query (has rows → use it, skip canonical)
        db = _exec_mock(invoice_rows)

        service = AdminMetricsService(db=db, plan_service=PlanService())
        snapshot = await service.compute_revenue()

        assert snapshot.source == "invoices"
        assert snapshot.mrr_cents == 16520
        assert snapshot.arr_cents == 16520 * 12
        assert len(snapshot.breakdown) == 1
        assert snapshot.breakdown[0].plan == "pro"
        assert snapshot.breakdown[0].org_count == 2
        assert snapshot.breakdown[0].revenue_cents == 16520

    async def test_empty_period_returns_zero_not_canonical_fallback(self):
        """When no paid invoices match, returns S/0 with source='invoices' — no fallback."""
        db = _exec_mock([])  # invoices query returns empty rows

        service = AdminMetricsService(db=db, plan_service=PlanService())
        snapshot = await service.compute_revenue()

        assert snapshot.source == "invoices"
        assert snapshot.mrr_cents == 0
        assert snapshot.arr_cents == 0
        assert snapshot.breakdown == []

    async def test_source_always_invoices_regardless_of_data(self):
        """source='invoices' always — locked-scope decision 7 hard swap."""
        invoice_rows = [
            {"plan": "pro", "org_count": 1, "revenue_cents": 8260},
        ]
        db = _exec_mock(invoice_rows)

        service = AdminMetricsService(db=db, plan_service=PlanService())
        snapshot = await service.compute_revenue()

        assert snapshot.source == "invoices"

    async def test_date_filter_params_passed_through(self):
        """date_from / date_to are accepted and don't crash (SQL mocked)."""
        from datetime import UTC, datetime

        invoice_rows = [
            {"plan": "studio", "org_count": 1, "revenue_cents": 35282},
        ]
        db = _exec_mock(invoice_rows)

        service = AdminMetricsService(db=db, plan_service=PlanService())
        snapshot = await service.compute_revenue(
            date_from=datetime(2026, 1, 1, tzinfo=UTC),
            date_to=datetime(2026, 1, 31, tzinfo=UTC),
        )

        assert snapshot.source == "invoices"
        assert snapshot.mrr_cents == 35282

    async def test_invoice_revenue_multi_plan_breakdown(self):
        """Mixed invoice plans sum correctly."""
        invoice_rows = [
            {"plan": "pro", "org_count": 1, "revenue_cents": 8260},
            {"plan": "studio", "org_count": 1, "revenue_cents": 35282},
        ]
        db = _exec_mock(invoice_rows)

        service = AdminMetricsService(db=db, plan_service=PlanService())
        snapshot = await service.compute_revenue()

        assert snapshot.source == "invoices"
        assert snapshot.mrr_cents == 8260 + 35282
        assert snapshot.arr_cents == snapshot.mrr_cents * 12
        assert len(snapshot.breakdown) == 2

    async def test_invoice_revenue_display_names_resolved(self):
        """display_name is resolved from PLANS config, not raw plan key."""
        invoice_rows = [
            {"plan": "pro", "org_count": 1, "revenue_cents": 8260},
        ]
        db = _exec_mock(invoice_rows)

        service = AdminMetricsService(db=db, plan_service=PlanService())
        snapshot = await service.compute_revenue()

        assert snapshot.breakdown[0].display_name == "Profesional"

    async def test_invoice_revenue_unknown_plan_uses_raw_name(self):
        """Unknown plan key falls back to raw name for display."""
        invoice_rows = [
            {"plan": "enterprise", "org_count": 1, "revenue_cents": 99900},
        ]
        db = _exec_mock(invoice_rows)

        service = AdminMetricsService(db=db, plan_service=PlanService())
        snapshot = await service.compute_revenue()

        assert snapshot.breakdown[0].plan == "enterprise"
        assert snapshot.breakdown[0].display_name == "enterprise"


# ---------------------------------------------------------------------------
# Webhook invoice creation (billing.py handlers)
# ---------------------------------------------------------------------------


class TestWebhookInvoiceCreation:
    """Unit tests for billing.py webhook invoice integration.

    Call the handler functions directly with mocked deps — same pattern
    as test_rbac_routes.py.
    """

    def _base_culqi_payload(self, event_type: str, charge_id: str) -> dict:
        return {
            "id": f"evt_{uuid.uuid4().hex[:10]}",
            "type": event_type,
            "data": {
                "id": charge_id,
                "amount": 8260,  # cents
                "metadata": {
                    "org_id": str(uuid.uuid4()),
                    "plan": "pro",
                    "seats_count": 0,
                },
            },
            "metadata": {
                "org_id": str(uuid.uuid4()),
                "plan": "pro",
                "seats_count": 0,
            },
        }

    async def test_culqi_charge_succeeded_calls_create_from_culqi_charge(self):
        from app.api.routes.billing import culqi_webhook
        import json
        from fastapi import Request

        charge_id = f"chr_{uuid.uuid4().hex[:10]}"
        org_id = str(uuid.uuid4())
        event_id = f"evt_{uuid.uuid4().hex[:10]}"
        payload = {
            "id": event_id,
            "type": "charge.succeeded",
            "data": {"id": charge_id, "amount": 8260, "metadata": {"org_id": org_id, "plan": "pro"}},
            "metadata": {"org_id": org_id, "plan": "pro"},
        }
        raw = json.dumps(payload).encode()

        request = MagicMock()
        request.body = AsyncMock(return_value=raw)
        request.headers = {}

        db = AsyncMock()
        audit = MagicMock()
        audit.log_action = AsyncMock()

        idem = MagicMock()
        idem.record_and_check = AsyncMock(return_value=(True, MagicMock()))
        idem.update_response = AsyncMock()

        inv_svc = MagicMock()
        inv_svc.create_from_culqi_charge = AsyncMock(return_value=(MagicMock(), True))

        with patch("app.config.settings") as mock_settings:
            mock_settings.culqi_webhook_secret = None  # skip HMAC

            # Patch _handle_checkout_completed to avoid DB work
            with patch("app.api.routes.billing._handle_checkout_completed", new=AsyncMock()):
                result = await culqi_webhook(
                    request=request,
                    db=db,
                    audit=audit,
                    idem=idem,
                    inv_svc=inv_svc,
                )

        assert result == {"status": "ok"}
        inv_svc.create_from_culqi_charge.assert_called_once()
        call_kwargs = inv_svc.create_from_culqi_charge.call_args.kwargs
        assert call_kwargs["provider_charge_id"] == charge_id
        assert call_kwargs["plan"] == "pro"
        assert call_kwargs["provider_event_id"] == event_id

    async def test_culqi_charge_failed_calls_create_failed(self):
        from app.api.routes.billing import culqi_webhook
        import json

        charge_id = f"chr_{uuid.uuid4().hex[:10]}"
        org_id = str(uuid.uuid4())
        event_id = f"evt_{uuid.uuid4().hex[:10]}"
        payload = {
            "id": event_id,
            "type": "charge.failed",
            "data": {"id": charge_id, "metadata": {"org_id": org_id, "plan": "pro"}},
            "metadata": {"org_id": org_id, "plan": "pro"},
        }
        raw = json.dumps(payload).encode()

        request = MagicMock()
        request.body = AsyncMock(return_value=raw)
        request.headers = {}

        db = AsyncMock()
        audit = MagicMock()
        audit.log_action = AsyncMock()
        idem = MagicMock()
        idem.record_and_check = AsyncMock(return_value=(True, MagicMock()))
        idem.update_response = AsyncMock()

        inv_svc = MagicMock()
        inv_svc.create_failed = AsyncMock(return_value=(MagicMock(), True))

        with patch("app.config.settings") as mock_settings:
            mock_settings.culqi_webhook_secret = None

            with patch("app.api.routes.billing._handle_payment_failed", new=AsyncMock()):
                result = await culqi_webhook(
                    request=request,
                    db=db,
                    audit=audit,
                    idem=idem,
                    inv_svc=inv_svc,
                )

        assert result == {"status": "ok"}
        inv_svc.create_failed.assert_called_once()
        call_kwargs = inv_svc.create_failed.call_args.kwargs
        assert call_kwargs["provider"] == "culqi"
        assert call_kwargs["provider_charge_id"] == charge_id

    async def test_invoice_creation_failure_does_not_break_webhook(self):
        """Invoice creation error is logged but webhook still returns ok."""
        from app.api.routes.billing import culqi_webhook
        import json

        org_id = str(uuid.uuid4())
        event_id = f"evt_{uuid.uuid4().hex[:10]}"
        payload = {
            "id": event_id,
            "type": "charge.succeeded",
            "data": {"id": f"chr_{uuid.uuid4().hex[:10]}", "metadata": {"org_id": org_id, "plan": "pro"}},
            "metadata": {"org_id": org_id, "plan": "pro"},
        }
        raw = json.dumps(payload).encode()

        request = MagicMock()
        request.body = AsyncMock(return_value=raw)
        request.headers = {}

        db = AsyncMock()
        audit = MagicMock()
        audit.log_action = AsyncMock()
        idem = MagicMock()
        idem.record_and_check = AsyncMock(return_value=(True, MagicMock()))
        idem.update_response = AsyncMock()

        inv_svc = MagicMock()
        inv_svc.create_from_culqi_charge = AsyncMock(side_effect=RuntimeError("DB exploded"))

        with patch("app.config.settings") as mock_settings:
            mock_settings.culqi_webhook_secret = None

            with patch("app.api.routes.billing._handle_checkout_completed", new=AsyncMock()):
                result = await culqi_webhook(
                    request=request,
                    db=db,
                    audit=audit,
                    idem=idem,
                    inv_svc=inv_svc,
                )

        # Webhook must still succeed despite invoice creation failure
        assert result == {"status": "ok"}
