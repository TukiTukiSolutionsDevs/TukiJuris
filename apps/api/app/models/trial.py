"""Trial ORM model — 14-day trial lifecycle for Pro and Studio plans."""

from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime, timedelta
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

TRIAL_DURATION_DAYS = 14
RETRY_WINDOW_HOURS = 72

VALID_STATUSES = (
    "active",
    "charged",
    "charge_failed",
    "downgraded",
    "canceled_pending",
    "canceled",
)
VALID_PLAN_CODES = ("pro", "studio")
VALID_PROVIDERS = ("culqi", "mp")


class Trial(Base):
    """Persistent record of a user's trial for a given plan."""

    __tablename__ = "trials"

    __table_args__ = (
        UniqueConstraint("user_id", "plan_code", name="uq_trials_user_plan"),
        # Partial UNIQUE: at most 1 active trial per user.
        # UniqueConstraint does NOT support postgresql_where in SA 2.0;
        # must be Index with unique=True + postgresql_where.
        Index(
            "uix_trials_user_active",
            "user_id",
            unique=True,
            postgresql_where="status = 'active'",
        ),
        Index("idx_trials_status_ends_at", "status", "ends_at"),
        Index(
            "idx_trials_charge_failed_retry",
            "status",
            "charge_failed_at",
            postgresql_where="status = 'charge_failed'",
        ),
        CheckConstraint("ends_at > started_at", name="ck_trials_ends_after_start"),
        CheckConstraint(
            "status IN ('active','charged','charge_failed','downgraded',"
            "'canceled_pending','canceled')",
            name="ck_trials_status",
        ),
        CheckConstraint("plan_code IN ('pro','studio')", name="ck_trials_plan_code"),
        CheckConstraint(
            "provider IS NULL OR provider IN ('culqi','mp')",
            name="ck_trials_provider",
        ),
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
    plan_code: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Card details (set when user calls POST /api/trials/add-card)
    card_added_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    provider: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    provider_customer_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    provider_card_token: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Charge outcome
    charged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    charge_failed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    charge_failure_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Cancel / downgrade
    canceled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    canceled_by_user: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    downgraded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # FK to subscription (set on auto-charge success via webhook Phase 1)
    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    user = relationship("User", back_populates="trials")
    subscription = relationship("Subscription", foreign_keys=[subscription_id])

    def __init__(self, **kw: object) -> None:
        """Set Python-side defaults before SA processes kwargs.

        SA 2.0 column-level defaults only fire at INSERT flush, not at
        object construction. Explicit setdefault here ensures tests and
        service code can read these fields before any DB flush.
        """
        now = datetime.now(UTC)
        kw.setdefault("id", uuid.uuid4())
        kw.setdefault("created_at", now)
        kw.setdefault("updated_at", now)
        kw.setdefault("started_at", now)
        kw.setdefault("ends_at", now + timedelta(days=TRIAL_DURATION_DAYS))
        kw.setdefault("status", "active")
        kw.setdefault("canceled_by_user", False)
        kw.setdefault("retry_count", 0)
        super().__init__(**kw)

    def __repr__(self) -> str:
        return (
            f"<Trial id={self.id} user={self.user_id} "
            f"plan={self.plan_code} status={self.status} ends={self.ends_at}>"
        )

    # ── Hybrid properties (read-only domain queries) ──────────────────────

    @hybrid_property
    def days_remaining(self) -> int:
        """Days until trial ends, ceiling-rounded, clamped to 0.

        Uses ceil(total_seconds / 86400) so that 4d 23h 59m shows as 5 days
        (user-friendly, avoids timedelta.days floor truncation off-by-one).
        """
        if self.ends_at is None:
            return 0
        delta = self.ends_at - datetime.now(UTC)
        total_seconds = delta.total_seconds()
        if total_seconds <= 0:
            return 0
        return math.ceil(total_seconds / 86400)

    @hybrid_property
    def is_expiring_soon(self) -> bool:
        """True when <= 3 days remain and trial is still active."""
        return self.status == "active" and 0 <= self.days_remaining <= 3

    @hybrid_property
    def can_charge(self) -> bool:
        """Eligible for scheduler auto-charge path (has card, not yet charged)."""
        return (
            self.status == "active"
            and self.card_added_at is not None
            and self.charged_at is None
        )
