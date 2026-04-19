"""User invoice route tests.

GET /api/billing/{org_id}/invoices        — list (AC18, AC19)
GET /api/billing/{org_id}/invoices/{id}   — detail (AC18, AC19)

Strategy: real org via POST /api/organizations/, mock InvoiceService via
dependency_overrides — keeps route tests decoupled from service internals.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_invoice_routes_user.py -v
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.api.deps import get_invoice_service
from app.main import app
from app.services.invoice_service import InvoiceService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_invoice(**kwargs) -> MagicMock:
    """Build a mock Invoice ORM object that serializes cleanly via InvoiceOut."""
    inv = MagicMock()
    inv.id = kwargs.get("id", uuid.uuid4())
    inv.org_id = kwargs.get("org_id", uuid.uuid4())
    inv.subscription_id = kwargs.get("subscription_id", None)
    inv.provider = kwargs.get("provider", "culqi")
    inv.provider_charge_id = kwargs.get("provider_charge_id", f"chr_{uuid.uuid4().hex[:10]}")
    inv.status = kwargs.get("status", "paid")
    inv.currency = kwargs.get("currency", "PEN")
    inv.base_amount = kwargs.get("base_amount", Decimal("70.00"))
    inv.seats_count = kwargs.get("seats_count", 0)
    inv.seat_amount = kwargs.get("seat_amount", Decimal("0.00"))
    inv.subtotal_amount = kwargs.get("subtotal_amount", Decimal("70.00"))
    inv.tax_amount = kwargs.get("tax_amount", Decimal("12.60"))
    inv.total_amount = kwargs.get("total_amount", Decimal("82.60"))
    inv.plan = kwargs.get("plan", "pro")
    inv.paid_at = kwargs.get("paid_at", datetime.now(UTC))
    inv.failed_at = kwargs.get("failed_at", None)
    inv.refunded_at = kwargs.get("refunded_at", None)
    inv.voided_at = kwargs.get("voided_at", None)
    inv.refund_reason = kwargs.get("refund_reason", None)
    inv.void_reason = kwargs.get("void_reason", None)
    inv.provider_event_id = kwargs.get("provider_event_id", None)
    inv.created_at = kwargs.get("created_at", datetime.now(UTC))
    inv.updated_at = kwargs.get("updated_at", datetime.now(UTC))
    return inv


def _mock_svc(list_return=None, get_return=None) -> InvoiceService:
    svc = MagicMock(spec=InvoiceService)
    svc.list_for_org = AsyncMock(return_value=list_return or ([], 0))
    svc.get_for_org = AsyncMock(return_value=get_return)
    return svc


def _unique_slug() -> str:
    return f"inv-user-{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def org_id(auth_client: AsyncClient) -> str:
    """Create a real org for the auth user and return its id."""
    res = await auth_client.post(
        "/api/organizations/",
        json={"name": "Invoice User Test Org", "slug": _unique_slug()},
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


# ---------------------------------------------------------------------------
# Auth guard tests
# ---------------------------------------------------------------------------


async def test_list_invoices_unauthenticated_returns_401(client: AsyncClient):
    res = await client.get(f"/api/billing/{uuid.uuid4()}/invoices")
    assert res.status_code in (401, 403)


async def test_list_invoices_non_member_returns_403(auth_client: AsyncClient):
    """Non-member org_id returns 403 regardless of invoice data."""
    svc = _mock_svc(list_return=([], 0))
    app.dependency_overrides[get_invoice_service] = lambda: svc
    try:
        res = await auth_client.get(f"/api/billing/{uuid.uuid4()}/invoices")
        assert res.status_code == 403
    finally:
        app.dependency_overrides.pop(get_invoice_service, None)


async def test_get_invoice_unauthenticated_returns_401(client: AsyncClient):
    res = await client.get(f"/api/billing/{uuid.uuid4()}/invoices/{uuid.uuid4()}")
    assert res.status_code in (401, 403)


# ---------------------------------------------------------------------------
# List invoices
# ---------------------------------------------------------------------------


async def test_list_invoices_empty(auth_client: AsyncClient, org_id: str):
    svc = _mock_svc(list_return=([], 0))
    app.dependency_overrides[get_invoice_service] = lambda: svc
    try:
        res = await auth_client.get(f"/api/billing/{org_id}/invoices")
        assert res.status_code == 200
        data = res.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 20
    finally:
        app.dependency_overrides.pop(get_invoice_service, None)


async def test_list_invoices_returns_items(auth_client: AsyncClient, org_id: str):
    inv = _make_invoice(org_id=uuid.UUID(org_id))
    svc = _mock_svc(list_return=([inv], 1))
    app.dependency_overrides[get_invoice_service] = lambda: svc
    try:
        res = await auth_client.get(f"/api/billing/{org_id}/invoices")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "paid"
        assert data["items"][0]["provider"] == "culqi"
    finally:
        app.dependency_overrides.pop(get_invoice_service, None)


async def test_list_invoices_pagination_params(auth_client: AsyncClient, org_id: str):
    svc = _mock_svc(list_return=([], 0))
    app.dependency_overrides[get_invoice_service] = lambda: svc
    try:
        res = await auth_client.get(
            f"/api/billing/{org_id}/invoices?page=2&per_page=5"
        )
        assert res.status_code == 200
        data = res.json()
        assert data["page"] == 2
        assert data["per_page"] == 5
        svc.list_for_org.assert_called_once_with(
            org_id=uuid.UUID(org_id), page=2, per_page=5, status=None
        )
    finally:
        app.dependency_overrides.pop(get_invoice_service, None)


async def test_list_invoices_status_filter(auth_client: AsyncClient, org_id: str):
    svc = _mock_svc(list_return=([], 0))
    app.dependency_overrides[get_invoice_service] = lambda: svc
    try:
        res = await auth_client.get(
            f"/api/billing/{org_id}/invoices?status=paid"
        )
        assert res.status_code == 200
        svc.list_for_org.assert_called_once_with(
            org_id=uuid.UUID(org_id), page=1, per_page=20, status="paid"
        )
    finally:
        app.dependency_overrides.pop(get_invoice_service, None)


# ---------------------------------------------------------------------------
# Get single invoice
# ---------------------------------------------------------------------------


async def test_get_invoice_returns_200(auth_client: AsyncClient, org_id: str):
    inv_id = uuid.uuid4()
    inv = _make_invoice(id=inv_id, org_id=uuid.UUID(org_id))
    svc = _mock_svc(get_return=inv)
    app.dependency_overrides[get_invoice_service] = lambda: svc
    try:
        res = await auth_client.get(f"/api/billing/{org_id}/invoices/{inv_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == str(inv_id)
        assert data["status"] == "paid"
    finally:
        app.dependency_overrides.pop(get_invoice_service, None)


async def test_get_invoice_not_found_returns_404(auth_client: AsyncClient, org_id: str):
    svc = _mock_svc(get_return=None)
    app.dependency_overrides[get_invoice_service] = lambda: svc
    try:
        res = await auth_client.get(
            f"/api/billing/{org_id}/invoices/{uuid.uuid4()}"
        )
        assert res.status_code == 404
    finally:
        app.dependency_overrides.pop(get_invoice_service, None)


async def test_get_invoice_non_member_returns_403(auth_client: AsyncClient):
    """Invoice detail for org user is not a member of returns 403."""
    svc = _mock_svc(get_return=_make_invoice())
    app.dependency_overrides[get_invoice_service] = lambda: svc
    try:
        res = await auth_client.get(
            f"/api/billing/{uuid.uuid4()}/invoices/{uuid.uuid4()}"
        )
        assert res.status_code == 403
    finally:
        app.dependency_overrides.pop(get_invoice_service, None)
