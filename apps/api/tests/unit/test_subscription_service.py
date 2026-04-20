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


# ---------------------------------------------------------------------------
# billing.unit.003 — _handle_subscription_deleted downgrades org to free
# billing.unit.004 — _handle_payment_failed triggers notification (xfail)
# ---------------------------------------------------------------------------


class TestHandleSubscriptionDeletedDowngrade:
    """billing.unit.003 — subscription.deleted event reverts org plan to free."""

    @pytest.mark.asyncio
    async def test_subscription_deleted_sets_org_plan_free(self):
        from unittest.mock import MagicMock
        from app.api.routes.billing import _handle_subscription_deleted
        from app.models.organization import Organization

        org_id = uuid.uuid4()

        sub = _make_sub(org_id, payment_subscription_id="sub_del_001", plan="pro")
        sub.status = "active"

        org = Organization()
        org.id = org_id
        org.plan = "pro"
        org.payment_subscription_id = "sub_del_001"
        org.plan_queries_limit = -1
        org.plan_models_allowed = ["*"]

        db = _make_db()
        db.flush = AsyncMock()
        db.scalar = AsyncMock(return_value=False)  # no BYOK keys

        sub_result = MagicMock()
        sub_result.scalar_one_or_none.return_value = sub

        org_result = MagicMock()
        org_result.scalar_one_or_none.return_value = org

        members_result = MagicMock()
        members_result.scalars.return_value = []

        db.execute = AsyncMock(side_effect=[sub_result, org_result, members_result])

        await _handle_subscription_deleted(
            {"subscription_id": "sub_del_001", "org_id": str(org_id), "status": "cancelled", "provider": "culqi"},
            db,
        )

        assert sub.status == "canceled", f"Expected 'canceled', got '{sub.status}'"
        assert org.plan == "free", f"Expected 'free', got '{org.plan}'"
        assert org.payment_subscription_id is None
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscription_deleted_missing_sub_returns_gracefully(self):
        """No subscription found → exits without error or flush."""
        from unittest.mock import MagicMock
        from app.api.routes.billing import _handle_subscription_deleted

        db = _make_db()
        db.flush = AsyncMock()

        no_result = MagicMock()
        no_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=no_result)

        await _handle_subscription_deleted(
            {"subscription_id": "nonexistent", "org_id": "", "status": "cancelled", "provider": "culqi"},
            db,
        )
        db.flush.assert_not_called()


@pytest.mark.xfail(
    reason=(
        "_handle_payment_failed only marks subscription past_due. "
        "It does NOT call notification_service with failure reason. "
        "Owner notification on payment failure is not yet implemented — deferred billing gap."
    ),
    strict=False,
)
@pytest.mark.asyncio
async def test_handle_payment_failed_notification_triggered():
    """billing.unit.004 — xfail: payment failure should notify the org owner (not yet implemented)."""
    # Desired: _handle_payment_failed calls notification_service.create with failure reason.
    # Actual: only sets subscription.status = "past_due". No notification fired.
    raise AssertionError(
        "_handle_payment_failed does not call notification_service. "
        "Implement owner notification to resolve this xfail."
    )
