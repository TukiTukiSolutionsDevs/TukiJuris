"""Invoice factory — direct SA insert for billing state tests.

Uses direct DB insert because invoices are created via payment webhooks in
production and cannot be reached through the HTTP surface in tests.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice


async def make_invoice(
    db: AsyncSession,
    *,
    org_id: str,
    plan: str = "pro",
    status: str = "paid",
    total_amount: float = 100.00,
    provider: str = "culqi",
) -> Invoice:
    """Insert an Invoice row in the given status.

    Use only when the desired state cannot be reached via HTTP (e.g. refunded).
    Returns the flushed Invoice instance — caller must commit the session.
    """
    now = datetime.now(UTC)
    paid_at = now if status == "paid" else None
    failed_at = now if status == "failed" else None
    refunded_at = now if status == "refunded" else None

    invoice = Invoice(
        id=uuid.uuid4(),
        org_id=uuid.UUID(org_id),
        provider=provider,
        provider_charge_id=f"test-charge-{uuid.uuid4().hex[:12]}",
        status=status,
        currency="PEN",
        base_amount=total_amount,
        seats_count=0,
        seat_amount=0.0,
        subtotal_amount=total_amount,
        tax_amount=0.0,
        total_amount=total_amount,
        plan=plan,
        paid_at=paid_at,
        failed_at=failed_at,
        refunded_at=refunded_at,
    )
    db.add(invoice)
    await db.flush()
    return invoice
