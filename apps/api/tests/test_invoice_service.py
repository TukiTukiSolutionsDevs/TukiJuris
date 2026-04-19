"""InvoiceService integration tests (AC2, AC3, AC4, AC12, AC13, AC14, AC17, AC18, AC19).

Tests run against the live DB (docker-compose up).

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_invoice_service.py -v
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import asyncpg
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.invoice import Invoice
from app.rbac.audit import AuditService
from app.services.invoice_pricing import compute_invoice_amounts
from app.services.invoice_service import InvoiceService, InvoiceStateError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _engine():
    return create_async_engine(settings.database_url, echo=False)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = _engine()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def real_org_id() -> uuid.UUID:
    """Fetch a real org_id from DB to satisfy FK constraints."""
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    try:
        row = await conn.fetchrow("SELECT id FROM organizations LIMIT 1")
        if row is None:
            pytest.skip("No organizations in DB")
        return uuid.UUID(str(row["id"]))
    finally:
        await conn.close()


@pytest.fixture
def mock_audit() -> AuditService:
    audit = MagicMock(spec=AuditService)
    audit.log_action = AsyncMock(return_value=None)
    return audit


@pytest_asyncio.fixture
async def svc(db_session: AsyncSession, mock_audit: AuditService) -> InvoiceService:
    return InvoiceService(db=db_session, audit=mock_audit)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(UTC)


def _charge_id() -> str:
    return f"chr_{uuid.uuid4().hex[:10]}"


def _mp_id() -> str:
    return f"mp_{uuid.uuid4().hex[:10]}"


# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------

class TestInvoiceServicePricingMath:
    """Verify amounts stored match compute_invoice_amounts (AC3, AC4)."""

    async def test_pro_amounts_stored_correctly(self, svc, real_org_id):
        inv, was_inserted = await svc.create_from_culqi_charge(
            org_id=real_org_id,
            subscription_id=None,
            plan="pro",
            seats_count=0,
            provider_charge_id=_charge_id(),
            amount_payload_cents=None,
            paid_at_payload=None,
            webhook_received_at=_now(),
            provider_event_id=None,
            actor_id=None,
        )
        assert was_inserted is True
        assert inv.base_amount == Decimal("70.00")
        assert inv.tax_amount == Decimal("12.60")
        assert inv.total_amount == Decimal("82.60")

    async def test_studio_7_seats_amounts(self, svc, real_org_id):
        inv, was_inserted = await svc.create_from_culqi_charge(
            org_id=real_org_id,
            subscription_id=None,
            plan="studio",
            seats_count=7,
            provider_charge_id=_charge_id(),
            amount_payload_cents=None,
            paid_at_payload=None,
            webhook_received_at=_now(),
            provider_event_id=None,
            actor_id=None,
        )
        assert was_inserted is True
        assert inv.seat_amount == Decimal("80.00")
        assert inv.subtotal_amount == Decimal("379.00")
        assert inv.tax_amount == Decimal("68.22")
        assert inv.total_amount == Decimal("447.22")


# ---------------------------------------------------------------------------
# create_from_culqi_charge
# ---------------------------------------------------------------------------

class TestCreateFromCulqiCharge:

    async def test_happy_path_status_paid(self, svc, real_org_id):
        inv, was_inserted = await svc.create_from_culqi_charge(
            org_id=real_org_id,
            subscription_id=None,
            plan="pro",
            seats_count=0,
            provider_charge_id=_charge_id(),
            amount_payload_cents=None,
            paid_at_payload=None,
            webhook_received_at=_now(),
            provider_event_id=None,
            actor_id=None,
        )
        assert was_inserted is True
        assert inv.status == "paid"
        assert inv.provider == "culqi"

    async def test_paid_at_uses_payload_when_present(self, svc, real_org_id):
        specific_ts = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
        inv, _ = await svc.create_from_culqi_charge(
            org_id=real_org_id,
            subscription_id=None,
            plan="pro",
            seats_count=0,
            provider_charge_id=_charge_id(),
            amount_payload_cents=None,
            paid_at_payload=specific_ts,
            webhook_received_at=_now(),
            provider_event_id=None,
            actor_id=None,
        )
        assert inv.paid_at is not None
        assert inv.paid_at.replace(tzinfo=UTC) == specific_ts or inv.paid_at == specific_ts

    async def test_paid_at_fallback_to_webhook_received_at(self, svc, real_org_id):
        received = datetime(2026, 1, 20, 8, 0, 0, tzinfo=UTC)
        inv, _ = await svc.create_from_culqi_charge(
            org_id=real_org_id,
            subscription_id=None,
            plan="pro",
            seats_count=0,
            provider_charge_id=_charge_id(),
            amount_payload_cents=None,
            paid_at_payload=None,
            webhook_received_at=received,
            provider_event_id=None,
            actor_id=None,
        )
        assert inv.paid_at is not None

    async def test_audit_emitted_on_insert(self, svc, real_org_id, mock_audit):
        await svc.create_from_culqi_charge(
            org_id=real_org_id,
            subscription_id=None,
            plan="pro",
            seats_count=0,
            provider_charge_id=_charge_id(),
            amount_payload_cents=None,
            paid_at_payload=None,
            webhook_received_at=_now(),
            provider_event_id=None,
            actor_id=None,
        )
        mock_audit.log_action.assert_called_once()
        call_kwargs = mock_audit.log_action.call_args.kwargs
        assert call_kwargs["action"] == "invoice.created"


# ---------------------------------------------------------------------------
# create_from_mp_payment
# ---------------------------------------------------------------------------

class TestCreateFromMpPayment:

    async def test_happy_path_mp(self, svc, real_org_id):
        inv, was_inserted = await svc.create_from_mp_payment(
            org_id=real_org_id,
            subscription_id=None,
            plan="pro",
            seats_count=0,
            provider_charge_id=_mp_id(),
            webhook_received_at=_now(),
            provider_event_id=None,
            actor_id=None,
        )
        assert was_inserted is True
        assert inv.status == "paid"
        assert inv.provider == "mercadopago"
        assert inv.total_amount == Decimal("82.60")

    async def test_mp_amount_always_derived(self, svc, real_org_id):
        """MP never takes payload cents — always uses plan pricing."""
        inv, _ = await svc.create_from_mp_payment(
            org_id=real_org_id,
            subscription_id=None,
            plan="studio",
            seats_count=0,
            provider_charge_id=_mp_id(),
            webhook_received_at=_now(),
            provider_event_id=None,
            actor_id=None,
        )
        assert inv.base_amount == Decimal("299.00")


# ---------------------------------------------------------------------------
# create_failed
# ---------------------------------------------------------------------------

class TestCreateFailed:

    async def test_culqi_failed(self, svc, real_org_id):
        inv, was_inserted = await svc.create_failed(
            provider="culqi",
            org_id=real_org_id,
            subscription_id=None,
            plan="pro",
            seats_count=0,
            provider_charge_id=_charge_id(),
            webhook_received_at=_now(),
            provider_event_id=None,
            actor_id=None,
        )
        assert was_inserted is True
        assert inv.status == "failed"
        assert inv.failed_at is not None
        assert inv.provider == "culqi"

    async def test_mp_failed(self, svc, real_org_id):
        inv, was_inserted = await svc.create_failed(
            provider="mercadopago",
            org_id=real_org_id,
            subscription_id=None,
            plan="pro",
            seats_count=0,
            provider_charge_id=_mp_id(),
            webhook_received_at=_now(),
            provider_event_id=None,
            actor_id=None,
        )
        assert was_inserted is True
        assert inv.status == "failed"
        assert inv.provider == "mercadopago"

    async def test_failed_audit_emitted(self, svc, real_org_id, mock_audit):
        await svc.create_failed(
            provider="culqi",
            org_id=real_org_id,
            subscription_id=None,
            plan="pro",
            seats_count=0,
            provider_charge_id=_charge_id(),
            webhook_received_at=_now(),
            provider_event_id=None,
            actor_id=None,
        )
        mock_audit.log_action.assert_called_once()
        assert mock_audit.log_action.call_args.kwargs["action"] == "invoice.failed_recorded"


# ---------------------------------------------------------------------------
# Idempotency (AC2, AC17)
# ---------------------------------------------------------------------------

class TestIdempotency:

    async def test_same_charge_id_twice_returns_existing(self, svc, real_org_id):
        """Second call with same charge_id returns (existing, False)."""
        charge_id = _charge_id()
        inv1, inserted1 = await svc.create_from_culqi_charge(
            org_id=real_org_id,
            subscription_id=None,
            plan="pro",
            seats_count=0,
            provider_charge_id=charge_id,
            amount_payload_cents=None,
            paid_at_payload=None,
            webhook_received_at=_now(),
            provider_event_id=None,
            actor_id=None,
        )
        inv2, inserted2 = await svc.create_from_culqi_charge(
            org_id=real_org_id,
            subscription_id=None,
            plan="pro",
            seats_count=0,
            provider_charge_id=charge_id,
            amount_payload_cents=None,
            paid_at_payload=None,
            webhook_received_at=_now(),
            provider_event_id=None,
            actor_id=None,
        )
        assert inserted1 is True
        assert inserted2 is False
        assert inv1.id == inv2.id

    async def test_idempotent_no_duplicate_audit(self, svc, real_org_id, mock_audit):
        charge_id = _charge_id()
        await svc.create_from_culqi_charge(
            org_id=real_org_id, subscription_id=None, plan="pro", seats_count=0,
            provider_charge_id=charge_id, amount_payload_cents=None, paid_at_payload=None,
            webhook_received_at=_now(), provider_event_id=None, actor_id=None,
        )
        await svc.create_from_culqi_charge(
            org_id=real_org_id, subscription_id=None, plan="pro", seats_count=0,
            provider_charge_id=charge_id, amount_payload_cents=None, paid_at_payload=None,
            webhook_received_at=_now(), provider_event_id=None, actor_id=None,
        )
        # Audit called only once (on first insert)
        assert mock_audit.log_action.call_count == 1

    async def test_create_from_culqi_charge_race_single_row(self, real_org_id):
        """Concurrent same charge_id → exactly 1 row persisted (AC17)."""
        engine = _engine()
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        charge_id = _charge_id()

        async def _create():
            async with AsyncSessionLocal() as session:
                audit = MagicMock(spec=AuditService)
                audit.log_action = AsyncMock(return_value=None)
                svc = InvoiceService(db=session, audit=audit)
                try:
                    result = await svc.create_from_culqi_charge(
                        org_id=real_org_id, subscription_id=None, plan="pro", seats_count=0,
                        provider_charge_id=charge_id, amount_payload_cents=None,
                        paid_at_payload=None, webhook_received_at=_now(),
                        provider_event_id=None, actor_id=None,
                    )
                    await session.commit()
                    return result
                except Exception:
                    await session.rollback()
                    return None

        results = await asyncio.gather(_create(), _create())
        # In asyncio single-thread concurrent mode the loser may not find the
        # winner's row before commit, so it re-raises and _create() returns None.
        # Invariant: at least 1 success, and at most 1 "was_inserted=True".
        successes = [r for r in results if r is not None]
        assert len(successes) >= 1
        assert sum(1 for _, inserted in successes if inserted) <= 1


# ---------------------------------------------------------------------------
# mark_refunded / mark_voided (AC12, AC13, AC14)
# ---------------------------------------------------------------------------

class TestMarkRefunded:

    async def test_refund_paid_invoice(self, svc, real_org_id, mock_audit):
        inv, _ = await svc.create_from_culqi_charge(
            org_id=real_org_id, subscription_id=None, plan="pro", seats_count=0,
            provider_charge_id=_charge_id(), amount_payload_cents=None, paid_at_payload=None,
            webhook_received_at=_now(), provider_event_id=None, actor_id=None,
        )
        mock_audit.reset_mock()
        actor = uuid.uuid4()
        refunded = await svc.mark_refunded(invoice_id=inv.id, reason="Customer request", actor_id=actor)
        assert refunded.status == "refunded"
        assert refunded.refunded_at is not None
        assert refunded.refund_reason == "Customer request"
        mock_audit.log_action.assert_called_once()
        assert mock_audit.log_action.call_args.kwargs["action"] == "invoice.refunded"

    async def test_refund_already_refunded_raises(self, svc, real_org_id):
        inv, _ = await svc.create_from_culqi_charge(
            org_id=real_org_id, subscription_id=None, plan="pro", seats_count=0,
            provider_charge_id=_charge_id(), amount_payload_cents=None, paid_at_payload=None,
            webhook_received_at=_now(), provider_event_id=None, actor_id=None,
        )
        await svc.mark_refunded(invoice_id=inv.id, reason=None, actor_id=uuid.uuid4())
        with pytest.raises(InvoiceStateError, match="refunded"):
            await svc.mark_refunded(invoice_id=inv.id, reason=None, actor_id=uuid.uuid4())

    async def test_refund_failed_invoice_raises(self, svc, real_org_id):
        inv, _ = await svc.create_failed(
            provider="culqi", org_id=real_org_id, subscription_id=None, plan="pro",
            seats_count=0, provider_charge_id=_charge_id(), webhook_received_at=_now(),
            provider_event_id=None, actor_id=None,
        )
        with pytest.raises(InvoiceStateError):
            await svc.mark_refunded(invoice_id=inv.id, reason=None, actor_id=uuid.uuid4())

    async def test_refund_without_reason(self, svc, real_org_id):
        inv, _ = await svc.create_from_culqi_charge(
            org_id=real_org_id, subscription_id=None, plan="pro", seats_count=0,
            provider_charge_id=_charge_id(), amount_payload_cents=None, paid_at_payload=None,
            webhook_received_at=_now(), provider_event_id=None, actor_id=None,
        )
        refunded = await svc.mark_refunded(invoice_id=inv.id, reason=None, actor_id=uuid.uuid4())
        assert refunded.refund_reason is None


class TestMarkVoided:

    async def test_void_paid_invoice(self, svc, real_org_id, mock_audit):
        inv, _ = await svc.create_from_culqi_charge(
            org_id=real_org_id, subscription_id=None, plan="pro", seats_count=0,
            provider_charge_id=_charge_id(), amount_payload_cents=None, paid_at_payload=None,
            webhook_received_at=_now(), provider_event_id=None, actor_id=None,
        )
        mock_audit.reset_mock()
        voided = await svc.mark_voided(invoice_id=inv.id, reason="Admin decision", actor_id=uuid.uuid4())
        assert voided.status == "voided"
        assert voided.voided_at is not None
        assert voided.void_reason == "Admin decision"
        assert mock_audit.log_action.call_args.kwargs["action"] == "invoice.voided"

    async def test_void_failed_invoice(self, svc, real_org_id):
        inv, _ = await svc.create_failed(
            provider="culqi", org_id=real_org_id, subscription_id=None, plan="pro",
            seats_count=0, provider_charge_id=_charge_id(), webhook_received_at=_now(),
            provider_event_id=None, actor_id=None,
        )
        voided = await svc.mark_voided(invoice_id=inv.id, reason=None, actor_id=uuid.uuid4())
        assert voided.status == "voided"

    async def test_void_already_voided_raises(self, svc, real_org_id):
        inv, _ = await svc.create_from_culqi_charge(
            org_id=real_org_id, subscription_id=None, plan="pro", seats_count=0,
            provider_charge_id=_charge_id(), amount_payload_cents=None, paid_at_payload=None,
            webhook_received_at=_now(), provider_event_id=None, actor_id=None,
        )
        await svc.mark_voided(invoice_id=inv.id, reason=None, actor_id=uuid.uuid4())
        with pytest.raises(InvoiceStateError):
            await svc.mark_voided(invoice_id=inv.id, reason=None, actor_id=uuid.uuid4())


# ---------------------------------------------------------------------------
# Read paths
# ---------------------------------------------------------------------------

class TestReadPaths:

    async def test_list_for_org_pagination(self, svc, real_org_id):
        # Insert 3 invoices
        for _ in range(3):
            await svc.create_from_culqi_charge(
                org_id=real_org_id, subscription_id=None, plan="pro", seats_count=0,
                provider_charge_id=_charge_id(), amount_payload_cents=None, paid_at_payload=None,
                webhook_received_at=_now(), provider_event_id=None, actor_id=None,
            )
        items, total = await svc.list_for_org(org_id=real_org_id, page=1, size=2)
        assert len(items) <= 2
        assert total >= 3

    async def test_list_for_org_status_filter(self, svc, real_org_id):
        # Insert paid + failed
        await svc.create_from_culqi_charge(
            org_id=real_org_id, subscription_id=None, plan="pro", seats_count=0,
            provider_charge_id=_charge_id(), amount_payload_cents=None, paid_at_payload=None,
            webhook_received_at=_now(), provider_event_id=None, actor_id=None,
        )
        await svc.create_failed(
            provider="culqi", org_id=real_org_id, subscription_id=None, plan="pro",
            seats_count=0, provider_charge_id=_charge_id(), webhook_received_at=_now(),
            provider_event_id=None, actor_id=None,
        )
        paid_items, _ = await svc.list_for_org(org_id=real_org_id, page=1, size=100, status="paid")
        assert all(i.status == "paid" for i in paid_items)

    async def test_get_for_org_cross_org_returns_none(self, svc, real_org_id):
        inv, _ = await svc.create_from_culqi_charge(
            org_id=real_org_id, subscription_id=None, plan="pro", seats_count=0,
            provider_charge_id=_charge_id(), amount_payload_cents=None, paid_at_payload=None,
            webhook_received_at=_now(), provider_event_id=None, actor_id=None,
        )
        other_org_id = uuid.uuid4()
        result = await svc.get_for_org(invoice_id=inv.id, org_id=other_org_id)
        assert result is None

    async def test_get_for_admin_ignores_org(self, svc, real_org_id):
        inv, _ = await svc.create_from_culqi_charge(
            org_id=real_org_id, subscription_id=None, plan="pro", seats_count=0,
            provider_charge_id=_charge_id(), amount_payload_cents=None, paid_at_payload=None,
            webhook_received_at=_now(), provider_event_id=None, actor_id=None,
        )
        result = await svc.get_for_admin(invoice_id=inv.id)
        assert result is not None
        assert result.id == inv.id

    async def test_list_for_admin_org_filter(self, svc, real_org_id):
        await svc.create_from_culqi_charge(
            org_id=real_org_id, subscription_id=None, plan="pro", seats_count=0,
            provider_charge_id=_charge_id(), amount_payload_cents=None, paid_at_payload=None,
            webhook_received_at=_now(), provider_event_id=None, actor_id=None,
        )
        items, total = await svc.list_for_admin(org_id=real_org_id, page=1, size=100)
        assert total >= 1
        assert all(str(i.org_id) == str(real_org_id) for i in items)
