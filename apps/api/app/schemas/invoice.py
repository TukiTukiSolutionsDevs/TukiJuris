"""Pydantic schemas for invoice endpoints (user + admin).

Shape:
  InvoiceOut — full invoice representation for both /me/invoices and /admin/invoices.
  InvoiceListResponse — paginated list wrapper.
  InvoiceAdminPatchRequest — admin PATCH body for refund/void.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class InvoiceOut(BaseModel):
    """Full invoice read-model returned by both user and admin endpoints."""

    id: UUID
    org_id: UUID
    subscription_id: Optional[UUID] = None
    provider: str
    provider_charge_id: str
    status: str
    currency: str
    base_amount: Decimal
    seats_count: int
    seat_amount: Decimal
    subtotal_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    plan: str
    paid_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    voided_at: Optional[datetime] = None
    refund_reason: Optional[str] = None
    void_reason: Optional[str] = None
    provider_event_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    """Paginated list of invoices."""

    items: list[InvoiceOut]
    total: int
    page: int
    per_page: int


class InvoiceAdminPatchRequest(BaseModel):
    """Body for admin PATCH /admin/invoices/{id}."""

    action: str = Field(
        description="Allowed values: 'refund', 'void'",
        pattern="^(refund|void)$",
    )
    reason: Optional[str] = Field(default=None, max_length=512)
