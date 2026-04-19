"""Subscription and usage tracking models — billing skeleton."""

import uuid
from datetime import UTC, datetime
from datetime import date as _date

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan: Mapped[str] = mapped_column(String(50), nullable=False)  # free, pro, studio
    status: Mapped[str] = mapped_column(
        String(50), default="active"
    )  # active, canceled, past_due, trialing

    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Billing — price in PEN integer cents (0 for free; set on paid plan activation).
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Payment provider references
    payment_subscription_id: Mapped[str | None] = mapped_column(String(100))
    payment_plan_id: Mapped[str | None] = mapped_column(String(100))
    payment_provider: Mapped[str | None] = mapped_column(String(50))  # "mercadopago" or "culqi"

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    organization = relationship("Organization", back_populates="subscriptions")


class UsageRecord(Base):
    """Daily per-user query/token usage. One row per (user_id, day).

    `organization_id` is nullable to track free-tier users without an org.
    Unique constraint on (user_id, day) enables clean upsert via ON CONFLICT.
    asyncpg handles writes directly — ORM is read-only reference for migrations.
    """

    __tablename__ = "usage_records"

    __table_args__ = (
        UniqueConstraint("user_id", "day", name="uq_usage_records_user_day"),
        Index("ix_usage_records_user_day", "user_id", "day"),
        Index("ix_usage_records_org_day", "organization_id", "day"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    day: Mapped[_date] = mapped_column(Date, nullable=False, index=True)
    query_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class ProcessedWebhookEvent(Base):
    """
    DB-backed idempotency record for payment webhooks.

    One row per (provider, event_id) pair.  The UNIQUE constraint on that
    pair is the dedupe key — INSERT + flush triggers IntegrityError on replay,
    allowing the handler to skip re-processing without a TOCTOU race window.

    `payload_hash` (SHA-256 of raw body) and `response_body` are stored for
    forensic/replay auditing only; they are NOT used as dedupe keys.
    """

    __tablename__ = "processed_webhook_events"

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "event_id",
            name="ux_processed_webhook_events_provider_event_id",
        ),
        CheckConstraint(
            "provider IN ('culqi','mercadopago')",
            name="ck_webhook_provider",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    event_id: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str | None] = mapped_column(String, nullable=True)
    payload_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
