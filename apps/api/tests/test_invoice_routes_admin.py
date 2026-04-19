"""Admin invoice route unit tests.

GET   /api/admin/invoices           (AC18, AC19)
GET   /api/admin/invoices/{id}      (AC18, AC19)
PATCH /api/admin/invoices/{id}      (AC12, AC13, AC14)

Strategy: call route handler functions directly with mocked deps —
same pattern as tests/unit/test_rbac_routes.py. No HTTP layer needed.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_invoice_routes_admin.py -v
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.invoice import InvoiceAdminPatchRequest
from app.services.invoice_service import InvoiceStateError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(is_admin: bool = True) -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.is_admin = is_admin
    return user


def _make_invoice(**kwargs) -> MagicMock:
    inv = MagicMock()
    inv.id = kwargs.get("id", uuid.uuid4())
    inv.org_id = kwargs.get("org_id", uuid.uuid4())
    inv.subscription_id = None
    inv.provider = "culqi"
    inv.provider_charge_id = f"chr_{uuid.uuid4().hex[:10]}"
    inv.status = kwargs.get("status", "paid")
    inv.currency = "PEN"
    inv.base_amount = Decimal("70.00")
    inv.seats_count = 0
    inv.seat_amount = Decimal("0.00")
    inv.subtotal_amount = Decimal("70.00")
    inv.tax_amount = Decimal("12.60")
    inv.total_amount = Decimal("82.60")
    inv.plan = "pro"
    inv.paid_at = datetime.now(UTC)
    inv.failed_at = None
    inv.refunded_at = kwargs.get("refunded_at", None)
    inv.voided_at = kwargs.get("voided_at", None)
    inv.refund_reason = None
    inv.void_reason = None
    inv.provider_event_id = None
    inv.created_at = datetime.now(UTC)
    inv.updated_at = datetime.now(UTC)
    return inv


def _mock_svc(**kwargs) -> MagicMock:
    svc = MagicMock()
    svc.list_for_admin = AsyncMock(
        return_value=kwargs.get("list_return", ([], 0))
    )
    svc.get_for_admin = AsyncMock(return_value=kwargs.get("get_return", None))
    svc.mark_refunded = AsyncMock(side_effect=kwargs.get("refund_side_effect", None))
    svc.mark_voided = AsyncMock(side_effect=kwargs.get("void_side_effect", None))
    if "refunded_invoice" in kwargs:
        svc.mark_refunded.return_value = kwargs["refunded_invoice"]
        svc.mark_refunded.side_effect = None
    if "voided_invoice" in kwargs:
        svc.mark_voided.return_value = kwargs["voided_invoice"]
        svc.mark_voided.side_effect = None
    return svc


# ---------------------------------------------------------------------------
# _ensure_admin guard
# ---------------------------------------------------------------------------


class TestEnsureAdmin:
    async def test_non_admin_user_raises_403(self):
        from app.api.routes.admin_invoices import list_invoices_admin

        non_admin = _make_user(is_admin=False)
        svc = _mock_svc(list_return=([], 0))

        with pytest.raises(HTTPException) as exc_info:
            await list_invoices_admin(
                page=1,
                per_page=20,
                invoice_status=None,
                org_id=None,
                user=non_admin,
                svc=svc,
                _rl=None,
            )
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "admin_required"


# ---------------------------------------------------------------------------
# GET /admin/invoices
# ---------------------------------------------------------------------------


class TestListInvoicesAdmin:
    async def test_empty_list(self):
        from app.api.routes.admin_invoices import list_invoices_admin

        svc = _mock_svc(list_return=([], 0))
        result = await list_invoices_admin(
            page=1, per_page=20, invoice_status=None, org_id=None,
            user=_make_user(), svc=svc, _rl=None,
        )
        assert result.total == 0
        assert result.items == []
        assert result.page == 1
        assert result.per_page == 20

    async def test_returns_items(self):
        from app.api.routes.admin_invoices import list_invoices_admin

        inv = _make_invoice()
        svc = _mock_svc(list_return=([inv], 1))
        result = await list_invoices_admin(
            page=1, per_page=20, invoice_status=None, org_id=None,
            user=_make_user(), svc=svc, _rl=None,
        )
        assert result.total == 1
        assert len(result.items) == 1
        svc.list_for_admin.assert_called_once_with(
            page=1, per_page=20, status=None, org_id=None,
        )

    async def test_status_filter_forwarded(self):
        from app.api.routes.admin_invoices import list_invoices_admin

        svc = _mock_svc(list_return=([], 0))
        await list_invoices_admin(
            page=1, per_page=5, invoice_status="paid", org_id=None,
            user=_make_user(), svc=svc, _rl=None,
        )
        svc.list_for_admin.assert_called_once_with(
            page=1, per_page=5, status="paid", org_id=None,
        )

    async def test_org_id_filter_forwarded(self):
        from app.api.routes.admin_invoices import list_invoices_admin

        oid = uuid.uuid4()
        svc = _mock_svc(list_return=([], 0))
        await list_invoices_admin(
            page=1, per_page=20, invoice_status=None, org_id=oid,
            user=_make_user(), svc=svc, _rl=None,
        )
        svc.list_for_admin.assert_called_once_with(
            page=1, per_page=20, status=None, org_id=oid,
        )


# ---------------------------------------------------------------------------
# GET /admin/invoices/{invoice_id}
# ---------------------------------------------------------------------------


class TestGetInvoiceAdmin:
    async def test_returns_invoice(self):
        from app.api.routes.admin_invoices import get_invoice_admin

        inv_id = uuid.uuid4()
        inv = _make_invoice(id=inv_id)
        svc = _mock_svc(get_return=inv)
        result = await get_invoice_admin(
            invoice_id=inv_id, user=_make_user(), svc=svc, _rl=None,
        )
        assert result.id == inv_id
        svc.get_for_admin.assert_called_once_with(invoice_id=inv_id)

    async def test_not_found_raises_404(self):
        from app.api.routes.admin_invoices import get_invoice_admin

        svc = _mock_svc(get_return=None)
        with pytest.raises(HTTPException) as exc_info:
            await get_invoice_admin(
                invoice_id=uuid.uuid4(), user=_make_user(), svc=svc, _rl=None,
            )
        assert exc_info.value.status_code == 404

    async def test_non_admin_raises_403(self):
        from app.api.routes.admin_invoices import get_invoice_admin

        svc = _mock_svc(get_return=_make_invoice())
        with pytest.raises(HTTPException) as exc_info:
            await get_invoice_admin(
                invoice_id=uuid.uuid4(),
                user=_make_user(is_admin=False),
                svc=svc,
                _rl=None,
            )
        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /admin/invoices/{invoice_id}
# ---------------------------------------------------------------------------


class TestPatchInvoiceAdmin:
    async def test_refund_action(self):
        from app.api.routes.admin_invoices import patch_invoice_admin

        inv = _make_invoice(status="paid")
        refunded = _make_invoice(status="refunded", refunded_at=datetime.now(UTC))
        svc = _mock_svc(get_return=inv, refunded_invoice=refunded)
        db = AsyncMock()
        body = InvoiceAdminPatchRequest(action="refund", reason="Customer request")

        result = await patch_invoice_admin(
            invoice_id=inv.id, body=body,
            user=_make_user(), db=db, svc=svc, _rl=None,
        )
        assert result.status == "refunded"
        svc.mark_refunded.assert_called_once_with(
            invoice=inv, reason="Customer request", actor_id=svc.mark_refunded.call_args.kwargs["actor_id"],
        )
        db.commit.assert_called_once()

    async def test_void_action(self):
        from app.api.routes.admin_invoices import patch_invoice_admin

        inv = _make_invoice(status="paid")
        voided = _make_invoice(status="voided", voided_at=datetime.now(UTC))
        svc = _mock_svc(get_return=inv, voided_invoice=voided)
        db = AsyncMock()
        body = InvoiceAdminPatchRequest(action="void", reason="Duplicate charge")

        result = await patch_invoice_admin(
            invoice_id=inv.id, body=body,
            user=_make_user(), db=db, svc=svc, _rl=None,
        )
        assert result.status == "voided"
        db.commit.assert_called_once()

    async def test_state_error_returns_409(self):
        from app.api.routes.admin_invoices import patch_invoice_admin

        inv = _make_invoice(status="refunded")
        svc = _mock_svc(
            get_return=inv,
            refund_side_effect=InvoiceStateError("already refunded"),
        )
        db = AsyncMock()
        body = InvoiceAdminPatchRequest(action="refund")

        with pytest.raises(HTTPException) as exc_info:
            await patch_invoice_admin(
                invoice_id=inv.id, body=body,
                user=_make_user(), db=db, svc=svc, _rl=None,
            )
        assert exc_info.value.status_code == 409
        db.commit.assert_not_called()

    async def test_not_found_raises_404_before_action(self):
        from app.api.routes.admin_invoices import patch_invoice_admin

        svc = _mock_svc(get_return=None)
        db = AsyncMock()
        body = InvoiceAdminPatchRequest(action="refund")

        with pytest.raises(HTTPException) as exc_info:
            await patch_invoice_admin(
                invoice_id=uuid.uuid4(), body=body,
                user=_make_user(), db=db, svc=svc, _rl=None,
            )
        assert exc_info.value.status_code == 404
        svc.mark_refunded.assert_not_called()
        db.commit.assert_not_called()

    async def test_non_admin_raises_403(self):
        from app.api.routes.admin_invoices import patch_invoice_admin

        svc = _mock_svc(get_return=_make_invoice())
        db = AsyncMock()
        body = InvoiceAdminPatchRequest(action="refund")

        with pytest.raises(HTTPException) as exc_info:
            await patch_invoice_admin(
                invoice_id=uuid.uuid4(), body=body,
                user=_make_user(is_admin=False),
                db=db, svc=svc, _rl=None,
            )
        assert exc_info.value.status_code == 403
        db.commit.assert_not_called()
