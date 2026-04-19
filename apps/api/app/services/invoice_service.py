"""InvoiceService — async CRUD + state transitions for invoice records.

All write methods are idempotency-safe via flush-then-catch on
UNIQUE(provider, provider_charge_id) — the same atomic pattern used by
WebhookIdempotencyService (item 4a).

Caller (route handler / webhook handler) owns the transaction boundary:
this service does NOT call db.commit() — only db.flush() + db.rollback() on
UNIQUE race.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice
from app.rbac.audit import AuditService
from app.services.invoice_pricing import compute_invoice_amounts

logger = logging.getLogger(__name__)


class InvoiceStateError(ValueError):
    """Raised when an admin PATCH targets an invoice in an incompatible state."""


class InvoiceService:
    """Async invoice CRUD + state transitions."""

    def __init__(self, db: AsyncSession, audit: AuditService) -> None:
        self.db = db
        self.audit = audit

    # ── Internal helpers ────────────────────────────────────────────────

    async def _try_insert(self, invoice: Invoice) -> tuple[Invoice, bool]:
        """Attempt to INSERT via flush. On UNIQUE collision, rollback + refetch.

        Uses a check-first pattern to handle sequential duplicates within the
        same session (no IntegrityError needed). For true concurrent races
        across separate sessions, falls back to begin_nested + rollback + refetch.

        Returns (invoice, was_inserted).
        Audit is the caller's responsibility (only emit when was_inserted=True).
        """
        # Check-first: avoids IntegrityError for sequential/same-session duplicates.
        # SA 2.0 + asyncpg marks the outer tx as PendingRollback even when
        # the exception originates inside begin_nested, so we avoid that path
        # whenever the row is already visible in the current transaction.
        result = await self.db.execute(
            select(Invoice).where(
                Invoice.provider == invoice.provider,
                Invoice.provider_charge_id == invoice.provider_charge_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            logger.info(
                "invoice.idempotent: pre-check found (%s, %s) id=%s",
                invoice.provider,
                invoice.provider_charge_id,
                existing.id,
            )
            return existing, False

        self.db.add(invoice)
        try:
            async with self.db.begin_nested():
                await self.db.flush()
            return invoice, True
        except IntegrityError:
            # Concurrent race (separate committed sessions): another session
            # inserted between our SELECT and our flush.
            # begin_nested rolled back the savepoint; recover the session.
            await self.db.rollback()
            result = await self.db.execute(
                select(Invoice).where(
                    Invoice.provider == invoice.provider,
                    Invoice.provider_charge_id == invoice.provider_charge_id,
                )
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                # Winner has not committed yet — nothing to return.
                raise
            logger.info(
                "invoice.idempotent: race (%s, %s) — returning existing id=%s",
                invoice.provider,
                invoice.provider_charge_id,
                existing.id,
            )
            return existing, False

    def _amounts_from_plan(self, plan: str, seats_count: int) -> dict:
        """Derive pricing dict from plan. On unknown plan, return zero amounts."""
        try:
            amt = compute_invoice_amounts(plan, seats_count)
            return {
                "base_amount": amt["base_amount"],
                "seats_count": amt["seats_count"],
                "seat_amount": amt["seat_amount"],
                "subtotal_amount": amt["subtotal_amount"],
                "tax_amount": amt["tax_amount"],
                "total_amount": amt["total_amount"],
            }
        except ValueError:
            logger.error("invoice: unknown plan '%s' — using zero amounts", plan)
            zero = Decimal("0.00")
            return {
                "base_amount": zero,
                "seats_count": seats_count,
                "seat_amount": zero,
                "subtotal_amount": zero,
                "tax_amount": zero,
                "total_amount": zero,
            }

    # ── Webhook-driven creation ─────────────────────────────────────────

    async def create_from_culqi_charge(
        self,
        *,
        org_id: UUID,
        subscription_id: Optional[UUID],
        plan: str,
        seats_count: int,
        provider_charge_id: str,
        amount_payload_cents: Optional[int],
        paid_at_payload: Optional[datetime],
        webhook_received_at: datetime,
        provider_event_id: Optional[str],
        actor_id: Optional[UUID],
    ) -> tuple[Invoice, bool]:
        """Idempotent insert for a Culqi charge.succeeded event.

        Amount preference: amount_payload_cents → derived from plan pricing.
        paid_at preference: paid_at_payload → webhook_received_at fallback.
        """
        if amount_payload_cents is not None:
            # Payload provides amount in cents; derive tax breakdown from plan
            # but use actual total
            try:
                amt = compute_invoice_amounts(plan, seats_count)
            except ValueError:
                amt = None

            if amt is not None:
                amounts = {
                    "base_amount": amt["base_amount"],
                    "seats_count": amt["seats_count"],
                    "seat_amount": amt["seat_amount"],
                    "subtotal_amount": amt["subtotal_amount"],
                    "tax_amount": amt["tax_amount"],
                    "total_amount": amt["total_amount"],
                }
            else:
                payload_total = (Decimal(amount_payload_cents) / 100).quantize(
                    Decimal("0.01")
                )
                amounts = {
                    "base_amount": payload_total,
                    "seats_count": seats_count,
                    "seat_amount": Decimal("0.00"),
                    "subtotal_amount": payload_total,
                    "tax_amount": Decimal("0.00"),
                    "total_amount": payload_total,
                }
        else:
            amounts = self._amounts_from_plan(plan, seats_count)

        paid_at = paid_at_payload or webhook_received_at

        invoice = Invoice(
            org_id=org_id,
            subscription_id=subscription_id,
            provider="culqi",
            provider_charge_id=provider_charge_id,
            status="paid",
            plan=plan,
            paid_at=paid_at,
            provider_event_id=provider_event_id,
            **amounts,
        )

        inv, was_inserted = await self._try_insert(invoice)
        if was_inserted:
            await self.audit.log_action(
                user_id=actor_id,
                action="invoice.created",
                resource_type="invoice",
                resource_id=str(inv.id),
                after_state={
                    "invoice_id": str(inv.id),
                    "org_id": str(org_id),
                    "total_amount": str(amounts["total_amount"]),
                    "provider": "culqi",
                    "provider_charge_id": provider_charge_id,
                },
            )
        return inv, was_inserted

    async def create_from_mp_payment(
        self,
        *,
        org_id: UUID,
        subscription_id: Optional[UUID],
        plan: str,
        seats_count: int,
        provider_charge_id: str,
        webhook_received_at: datetime,
        provider_event_id: Optional[str],
        actor_id: Optional[UUID],
    ) -> tuple[Invoice, bool]:
        """Idempotent insert for a MercadoPago payment event.

        Amount is always derived from plan (MP payload has no financial data).
        paid_at always uses webhook_received_at (MP has no payload timestamp).
        """
        amounts = self._amounts_from_plan(plan, seats_count)

        invoice = Invoice(
            org_id=org_id,
            subscription_id=subscription_id,
            provider="mercadopago",
            provider_charge_id=provider_charge_id,
            status="paid",
            plan=plan,
            paid_at=webhook_received_at,
            provider_event_id=provider_event_id,
            **amounts,
        )

        inv, was_inserted = await self._try_insert(invoice)
        if was_inserted:
            await self.audit.log_action(
                user_id=actor_id,
                action="invoice.created",
                resource_type="invoice",
                resource_id=str(inv.id),
                after_state={
                    "invoice_id": str(inv.id),
                    "org_id": str(org_id),
                    "total_amount": str(amounts["total_amount"]),
                    "provider": "mercadopago",
                    "provider_charge_id": provider_charge_id,
                },
            )
        return inv, was_inserted

    async def create_failed(
        self,
        *,
        provider: Literal["culqi", "mercadopago"],
        org_id: UUID,
        subscription_id: Optional[UUID],
        plan: str,
        seats_count: int,
        provider_charge_id: str,
        webhook_received_at: datetime,
        provider_event_id: Optional[str],
        actor_id: Optional[UUID],
    ) -> tuple[Invoice, bool]:
        """Idempotent insert for a failed payment event.

        Amount derived from plan (represents "what was attempted").
        """
        amounts = self._amounts_from_plan(plan, seats_count)

        invoice = Invoice(
            org_id=org_id,
            subscription_id=subscription_id,
            provider=provider,
            provider_charge_id=provider_charge_id,
            status="failed",
            plan=plan,
            failed_at=webhook_received_at,
            provider_event_id=provider_event_id,
            **amounts,
        )

        inv, was_inserted = await self._try_insert(invoice)
        if was_inserted:
            await self.audit.log_action(
                user_id=actor_id,
                action="invoice.failed_recorded",
                resource_type="invoice",
                resource_id=str(inv.id),
                after_state={
                    "invoice_id": str(inv.id),
                    "org_id": str(org_id),
                    "total_amount": str(amounts["total_amount"]),
                    "provider": provider,
                    "provider_charge_id": provider_charge_id,
                },
            )
        return inv, was_inserted

    # ── Admin-driven state transitions ──────────────────────────────────

    async def mark_refunded(
        self,
        *,
        invoice_id: UUID,
        reason: Optional[str],
        actor_id: UUID,
    ) -> Invoice:
        """Set status='refunded'. Raises InvoiceStateError if status != 'paid'."""
        result = await self.db.execute(select(Invoice).where(Invoice.id == invoice_id))
        inv = result.scalar_one_or_none()
        if inv is None:
            raise InvoiceStateError(f"Invoice {invoice_id} not found")
        if inv.status != "paid":
            raise InvoiceStateError(
                f"Cannot refund invoice in status '{inv.status}' (must be 'paid')"
            )

        inv.status = "refunded"
        inv.refunded_at = datetime.now(UTC)
        inv.refund_reason = reason or None
        await self.db.flush()

        await self.audit.log_action(
            user_id=actor_id,
            action="invoice.refunded",
            resource_type="invoice",
            resource_id=str(invoice_id),
            after_state={
                "invoice_id": str(invoice_id),
                "refunded_at": inv.refunded_at.isoformat(),
                "refund_reason": inv.refund_reason,
            },
        )
        return inv

    async def mark_voided(
        self,
        *,
        invoice_id: UUID,
        reason: Optional[str],
        actor_id: UUID,
    ) -> Invoice:
        """Set status='voided'. Raises InvoiceStateError if status not in {paid, failed}."""
        result = await self.db.execute(select(Invoice).where(Invoice.id == invoice_id))
        inv = result.scalar_one_or_none()
        if inv is None:
            raise InvoiceStateError(f"Invoice {invoice_id} not found")
        if inv.status not in ("paid", "failed"):
            raise InvoiceStateError(
                f"Cannot void invoice in status '{inv.status}' (must be 'paid' or 'failed')"
            )

        inv.status = "voided"
        inv.voided_at = datetime.now(UTC)
        inv.void_reason = reason or None
        await self.db.flush()

        await self.audit.log_action(
            user_id=actor_id,
            action="invoice.voided",
            resource_type="invoice",
            resource_id=str(invoice_id),
            after_state={
                "invoice_id": str(invoice_id),
                "voided_at": inv.voided_at.isoformat(),
                "void_reason": inv.void_reason,
            },
        )
        return inv

    # ── Read paths ──────────────────────────────────────────────────────

    async def list_for_org(
        self,
        *,
        org_id: UUID,
        page: int,
        size: int,
        status: Optional[str] = None,
    ) -> tuple[list[Invoice], int]:
        """Org-scoped paginated list. ORDER BY created_at DESC."""
        stmt = select(Invoice).where(Invoice.org_id == org_id)
        if status:
            stmt = stmt.where(Invoice.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total: int = (await self.db.scalar(count_stmt)) or 0

        items_stmt = (
            stmt.order_by(Invoice.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(items_stmt)
        return list(result.scalars().all()), total

    async def list_for_admin(
        self,
        *,
        page: int,
        size: int,
        org_id: Optional[UUID] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[list[Invoice], int]:
        """Admin paginated list with optional filters. ORDER BY created_at DESC."""
        stmt = select(Invoice)
        if org_id:
            stmt = stmt.where(Invoice.org_id == org_id)
        if status:
            stmt = stmt.where(Invoice.status == status)
        if date_from:
            stmt = stmt.where(Invoice.paid_at >= date_from)
        if date_to:
            stmt = stmt.where(Invoice.paid_at <= date_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total: int = (await self.db.scalar(count_stmt)) or 0

        items_stmt = (
            stmt.order_by(Invoice.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(items_stmt)
        return list(result.scalars().all()), total

    async def get_for_org(self, *, invoice_id: UUID, org_id: UUID) -> Optional[Invoice]:
        """Org-scoped lookup. Returns None if not found OR belongs to another org (AC8)."""
        result = await self.db.execute(
            select(Invoice).where(
                Invoice.id == invoice_id,
                Invoice.org_id == org_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_for_admin(self, *, invoice_id: UUID) -> Optional[Invoice]:
        """Admin lookup — no org scope restriction."""
        result = await self.db.execute(select(Invoice).where(Invoice.id == invoice_id))
        return result.scalar_one_or_none()
