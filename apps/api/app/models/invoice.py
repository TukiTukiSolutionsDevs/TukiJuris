"""Invoice ORM model — one row per payment attempt from Culqi or MercadoPago."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Invoice(Base):
    """Persistent record of a payment charge — one invoice per provider charge_id."""

    __tablename__ = "invoices"

    __table_args__ = (
        UniqueConstraint("provider", "provider_charge_id", name="uq_invoices_provider_charge"),
        CheckConstraint(
            "provider IN ('culqi','mercadopago')",
            name="ck_invoices_provider",
        ),
        CheckConstraint(
            "status IN ('pending','paid','failed','refunded','voided')",
            name="ck_invoices_status",
        ),
        CheckConstraint(
            "currency = 'PEN'",
            name="ck_invoices_currency",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=False
    )
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=True
    )
    provider: Mapped[str] = mapped_column(String, nullable=False)
    provider_charge_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")

    # Pricing breakdown
    base_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    seats_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    seat_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    subtotal_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Plan snapshot
    plan: Mapped[str] = mapped_column(String, nullable=False)

    # Event timestamps (nullable — set when the status is reached)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Optional metadata
    refund_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    void_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_event_id: Mapped[str | None] = mapped_column(String, nullable=True)

    # Row timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def __init__(self, **kwargs: object) -> None:
        """Set Python-side defaults before SA processes kwargs.

        SA 2.0 column-level defaults are applied at INSERT time, not at
        object construction. We set them here so unit tests and code that
        reads attributes before flush see sensible values.
        """
        from decimal import Decimal as _D

        kwargs.setdefault("id", uuid.uuid4())
        kwargs.setdefault("status", "pending")
        kwargs.setdefault("currency", "PEN")
        kwargs.setdefault("seats_count", 0)
        kwargs.setdefault("seat_amount", _D("0.00"))
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return (
            f"<Invoice id={self.id} provider={self.provider} "
            f"charge={self.provider_charge_id} status={self.status} "
            f"total={self.total_amount}>"
        )
