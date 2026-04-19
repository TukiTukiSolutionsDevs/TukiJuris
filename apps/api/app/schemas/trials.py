"""Pydantic v2 schemas for the trials API."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Nested ────────────────────────────────────────────────────────────────


class CustomerInfo(BaseModel):
    """Customer details forwarded to the payment provider."""

    email: EmailStr
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    phone_number: Optional[str] = Field(default=None, max_length=20)


# ── Request bodies ────────────────────────────────────────────────────────


class StartTrialRequest(BaseModel):
    plan_code: Literal["pro", "studio"]


class AddCardRequest(BaseModel):
    provider: Literal["culqi", "mp"]
    token_id: str = Field(min_length=4, max_length=200)
    customer_info: CustomerInfo


class AdminTrialPatch(BaseModel):
    action: Literal["force_downgrade", "extend_days", "force_cancel", "force_charge"]
    extend_days: Optional[int] = Field(default=None, ge=1, le=30)
    reason: str = Field(min_length=4, max_length=500)


class AdminTrialFilters(BaseModel):
    status: Optional[str] = None
    plan_code: Optional[str] = None
    expiring_in_days: Optional[int] = Field(default=None, ge=0, le=30)
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


# ── Response schemas ──────────────────────────────────────────────────────


class TrialResponse(BaseModel):
    """Full trial representation returned to end users and admins."""

    id: uuid.UUID
    user_id: uuid.UUID
    plan_code: Literal["pro", "studio"]
    status: Literal[
        "active",
        "charged",
        "charge_failed",
        "downgraded",
        "canceled_pending",
        "canceled",
    ]
    started_at: datetime
    ends_at: datetime
    days_remaining: int

    # Card
    card_added_at: Optional[datetime] = None
    provider: Optional[Literal["culqi", "mp"]] = None

    # Outcome
    charged_at: Optional[datetime] = None
    charge_failed_at: Optional[datetime] = None
    charge_failure_reason: Optional[str] = None
    retry_count: int = 0

    # Cancel / downgrade
    canceled_at: Optional[datetime] = None
    canceled_by_user: bool = False
    downgraded_at: Optional[datetime] = None

    subscription_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)


class AdminTrialListResponse(BaseModel):
    items: list[TrialResponse]
    total: int
    page: int
    per_page: int


class TrialTickResult(BaseModel):
    """Summary returned by POST /internal/trials/tick."""

    processed: int = 0
    charged: int = 0
    downgraded: int = 0
    canceled: int = 0
    charge_failed: int = 0
    errors: int = 0
