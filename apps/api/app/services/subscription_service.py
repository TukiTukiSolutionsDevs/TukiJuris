"""
Subscription service — idempotent subscription management.

Provides upsert semantics for checkout-completed events so that webhook
retries do not create duplicate Subscription rows.

Key design decision: query-first-then-create (NOT INSERT + catch).
Reason: subscription IDs come from the provider (Culqi/MP) and are stable —
we can reliably identify an existing row by (org_id, provider, sub_id).
The TOCTOU concern that applies to idempotency table inserts does NOT apply
here because the outer webhook handler already prevents duplicate execution
via the ProcessedWebhookEvent unique index.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription

logger = logging.getLogger(__name__)


async def upsert_subscription_for_checkout(
    db: AsyncSession,
    org_id: uuid.UUID,
    provider: str,
    provider_subscription_id: str | None,
    plan: str,
    status: str = "active",
) -> Subscription:
    """
    Create or update a Subscription for a completed checkout.

    Lookup key: (organization_id, payment_provider, payment_subscription_id).
    When provider_subscription_id is None/empty, always creates a new row
    (one-time payments that have no stable subscription ID).

    Returns the existing or newly created Subscription.
    """
    existing: Subscription | None = None

    if provider_subscription_id:
        existing = await db.scalar(
            select(Subscription).where(
                Subscription.organization_id == org_id,
                Subscription.payment_provider == provider,
                Subscription.payment_subscription_id == provider_subscription_id,
            )
        )

    if existing is not None:
        # Idempotent update — same event replayed, just re-affirm the state.
        logger.info(
            "subscription.upsert: updating existing sub id=%s org=%s provider=%s",
            existing.id,
            org_id,
            provider,
        )
        existing.plan = plan
        existing.status = status
        return existing

    # No matching row — create a new subscription.
    now = datetime.now(UTC)
    new_sub = Subscription(
        organization_id=org_id,
        plan=plan,
        status=status,
        payment_subscription_id=provider_subscription_id or None,
        payment_plan_id=plan,
        payment_provider=provider,
        current_period_start=now,
        current_period_end=None,
    )
    db.add(new_sub)
    logger.info(
        "subscription.upsert: created new sub org=%s provider=%s plan=%s",
        org_id,
        provider,
        plan,
    )
    return new_sub
