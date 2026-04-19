"""Pydantic schemas for the admin-saas-panel endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Revenue
# ---------------------------------------------------------------------------


class RevenueBreakdownItem(BaseModel):
    plan: str
    display_name: str
    org_count: int
    revenue_cents: int


class RevenueResponse(BaseModel):
    source: str = Field(description="'canonical_prices' or 'invoices'")
    mrr_cents: int
    arr_cents: int
    breakdown: list[RevenueBreakdownItem]


# ---------------------------------------------------------------------------
# BYOK
# ---------------------------------------------------------------------------


class BYOKListItem(BaseModel):
    user_id: str
    user_email: str
    provider: str
    is_active: bool
    api_key_hint: str
    last_rotation_at: datetime | None


class BYOKListResponse(BaseModel):
    items: list[BYOKListItem]
    total: int
    page: int
    per_page: int


# ---------------------------------------------------------------------------
# Users (extended — additive on top of existing admin.py shape)
# ---------------------------------------------------------------------------


class UserListItem(BaseModel):
    id: str
    email: str
    full_name: str | None
    is_active: bool
    is_admin: bool
    plan: str
    created_at: datetime
    org_name: str | None
    queries_this_month: int
    last_active: datetime | None = None  # NEW: latest refresh_token.created_at
    byok_count: int = 0                  # NEW: count of active user_llm_keys


class UserListResponse(BaseModel):
    users: list[UserListItem]
    total: int
    page: int
    per_page: int
