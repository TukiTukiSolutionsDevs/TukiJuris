"""Admin SaaS panel routes — revenue metrics and BYOK monitoring.

Separate from admin.py (infra/system) to keep RBAC scoping clean:
  - billing:read  → /revenue
  - users:read    → /byok

Defense-in-depth: require_permission enforces RBAC AND require_admin enforces
User.is_admin = True. Both guards must pass.

Audit: every successful request emits an AuditService.log_action entry.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RateLimitBucket, RateLimitGuard, get_db, require_admin
from app.models.user import User
from app.rbac.audit import AuditService
from app.rbac.dependencies import require_permission
from app.schemas.admin import BYOKListItem, BYOKListResponse, RevenueResponse
from app.services.admin_metrics_service import AdminMetricsService
from app.services.plan_service import PlanService

router = APIRouter(prefix="/admin", tags=["admin-saas"])


# ---------------------------------------------------------------------------
# GET /api/admin/revenue
# ---------------------------------------------------------------------------


@router.get(
    "/revenue",
    response_model=RevenueResponse,
    summary="Revenue snapshot — MRR/ARR with per-plan breakdown",
)
async def get_revenue(
    date_from: Optional[datetime] = Query(default=None, description="Filter paid_at >= date_from (ISO 8601)"),
    date_to: Optional[datetime] = Query(default=None, description="Filter paid_at <= date_to (ISO 8601)"),
    user: User = Depends(require_admin),
    _perm: User = Depends(require_permission("billing:read")),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> RevenueResponse:
    """Compute MRR/ARR from paid invoices (hard swap — no canonical fallback).

    Requires: billing:read permission AND is_admin=True.
    Optionally filter by date range using date_from / date_to (ISO 8601 datetime).
    """

    service = AdminMetricsService(db=db, plan_service=PlanService())
    snapshot = await service.compute_revenue(date_from=date_from, date_to=date_to)

    await AuditService(db=db).log_action(
        user_id=user.id,
        action="admin.revenue.viewed",
        resource_type="revenue",
    )

    return RevenueResponse(
        source=snapshot.source,
        mrr_cents=snapshot.mrr_cents,
        arr_cents=snapshot.arr_cents,
        breakdown=[
            {  # type: ignore[arg-type]
                "plan": item.plan,
                "display_name": item.display_name,
                "org_count": item.org_count,
                "revenue_cents": item.revenue_cents,
            }
            for item in snapshot.breakdown
        ],
    )


# ---------------------------------------------------------------------------
# GET /api/admin/byok
# ---------------------------------------------------------------------------


@router.get(
    "/byok",
    response_model=BYOKListResponse,
    summary="Paginated BYOK key configurations — no encrypted material returned",
)
async def list_byok(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    provider: str | None = Query(None, description="Filter by provider (e.g. openai)"),
    user: User = Depends(require_admin),
    _perm: User = Depends(require_permission("users:read")),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> BYOKListResponse:
    """List BYOK configurations across all users.

    Requires: users:read permission AND is_admin=True.
    Returns api_key_hint only — never the encrypted key material.
    """

    service = AdminMetricsService(db=db, plan_service=PlanService())
    items, total = await service.list_byok(page=page, per_page=per_page, provider=provider)

    await AuditService(db=db).log_action(
        user_id=user.id,
        action="admin.byok.listed",
        resource_type="byok",
    )

    return BYOKListResponse(
        items=[
            BYOKListItem(
                user_id=item.user_id,
                user_email=item.user_email,
                provider=item.provider,
                is_active=item.is_active,
                api_key_hint=item.api_key_hint,
                last_rotation_at=item.last_rotation_at,
            )
            for item in items
        ],
        total=total,
        page=page,
        per_page=per_page,
    )
