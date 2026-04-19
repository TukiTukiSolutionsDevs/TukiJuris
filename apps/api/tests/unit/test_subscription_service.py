"""Unit tests for subscription upsert service (AC10).

Verifies that upsert_subscription_for_checkout is idempotent:
  - First call creates a Subscription row.
  - Second call with the same (org_id, provider, subscription_id) updates
    the existing row instead of creating a duplicate.

All DB interactions are mocked — no live PostgreSQL required.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/unit/test_subscription_service.py -v
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.subscription import Subscription
from app.services.subscription_service import upsert_subscription_for_checkout


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db() -> AsyncMock:
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.execute = AsyncMock()
    db.scalar = AsyncMock()
    return db


def _make_sub(
    org_id: uuid.UUID,
    provider: str = "culqi",
    payment_subscription_id: str = "sub_001",
    plan: str = "pro",
    status: str = "active",
) -> Subscription:
    sub = Subscription()
    sub.id = uuid.uuid4()
    sub.organization_id = org_id
    sub.payment_provider = provider
    sub.payment_subscription_id = payment_subscription_id
    sub.plan = plan
    sub.status = status
    sub.created_at = datetime.now(UTC)
    sub.updated_at = datetime.now(UTC)
    return sub


# ---------------------------------------------------------------------------
# AC10 — upsert is idempotent
# ---------------------------------------------------------------------------


class TestUpsertSubscriptionForCheckout:
    async def test_first_call_creates_new_subscription(self):
        """When no existing sub exists, a new Subscription is created."""
        db = _make_db()
        db.scalar = AsyncMock(return_value=None)  # no existing row

        org_id = uuid.uuid4()
        result = await upsert_subscription_for_checkout(
            db=db,
            org_id=org_id,
            provider="culqi",
            provider_subscription_id="sub_001",
            plan="pro",
            status="active",
        )

        db.add.assert_called_once()
        added_sub = db.add.call_args[0][0]
        assert isinstance(added_sub, Subscription)
        assert added_sub.organization_id == org_id
        assert added_sub.payment_provider == "culqi"
        assert added_sub.payment_subscription_id == "sub_001"
        assert added_sub.plan == "pro"
        assert added_sub.status == "active"

    async def test_second_call_updates_existing_subscription(self):
        """When a sub with the same (org, provider, sub_id) exists, update it — no duplicate."""
        db = _make_db()
        org_id = uuid.uuid4()
        existing = _make_sub(org_id, status="canceled")  # previously canceled
        db.scalar = AsyncMock(return_value=existing)

        result = await upsert_subscription_for_checkout(
            db=db,
            org_id=org_id,
            provider="culqi",
            provider_subscription_id="sub_001",
            plan="pro",
            status="active",
        )

        # Must NOT create a new row
        db.add.assert_not_called()
        # Must update the existing row
        assert result is existing
        assert result.status == "active"
        assert result.plan == "pro"

    async def test_mp_provider_creates_sub(self):
        """MercadoPago variant creates sub identically."""
        db = _make_db()
        db.scalar = AsyncMock(return_value=None)
        org_id = uuid.uuid4()

        result = await upsert_subscription_for_checkout(
            db=db,
            org_id=org_id,
            provider="mercadopago",
            provider_subscription_id="mp_sub_001",
            plan="studio",
            status="active",
        )

        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.payment_provider == "mercadopago"
        assert added.plan == "studio"

    async def test_returns_existing_sub_on_update(self):
        """Return value is the existing subscription object when updating."""
        db = _make_db()
        org_id = uuid.uuid4()
        existing = _make_sub(org_id)
        db.scalar = AsyncMock(return_value=existing)

        result = await upsert_subscription_for_checkout(
            db=db,
            org_id=org_id,
            provider="culqi",
            provider_subscription_id="sub_001",
            plan="pro",
            status="active",
        )

        assert result is existing

    async def test_none_subscription_id_still_creates_row(self):
        """When provider_subscription_id is None/empty (one-time payment), create a new row."""
        db = _make_db()
        db.scalar = AsyncMock(return_value=None)
        org_id = uuid.uuid4()

        result = await upsert_subscription_for_checkout(
            db=db,
            org_id=org_id,
            provider="culqi",
            provider_subscription_id=None,
            plan="pro",
            status="active",
        )

        db.add.assert_called_once()
