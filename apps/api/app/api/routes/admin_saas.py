"""Admin SaaS panel routes — revenue metrics and BYOK monitoring.

Separate from admin.py (infra/system) to keep RBAC scoping clean:
  - billing:read  → /revenue
  - users:read    → /byok

Defense-in-depth: require_permission enforces RBAC AND _ensure_admin enforces
User.is_admin = True. Both guards must pass.

Audit: every successful request emits an AuditService.log_action entry.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RateLimitBucket, RateLimitGuard, get_db
from app.models.user import User
from app.rbac.audit import AuditService
from app.rbac.dependencies import require_permission
from app.schemas.admin import BYOKListItem, BYOKListResponse, RevenueResponse
from app.services.admin_metrics_service import AdminMetricsService
from app.services.plan_service import PlanService

router = APIRouter(prefix="/admin", tags=["admin-saas"])


# ---------------------------------------------------------------------------
# Guard helper
# ---------------------------------------------------------------------------


def _ensure_admin(user: User) -> None:
    """Defense-in-depth: RBAC permission is necessary but not sufficient.

    An attacker who manages to bypass RBAC still can't reach admin data
    unless the user row itself has is_admin=True.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin_required",
        )


# ---------------------------------------------------------------------------
# GET /api/admin/revenue
# ---------------------------------------------------------------------------


@router.get(
    "/revenue",
    response_model=RevenueResponse,
    summary="Revenue snapshot — MRR/ARR with per-plan breakdown",
)
async def get_revenue(
    user: User = Depends(require_permission("billing:read")),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> RevenueResponse:
    """Compute MRR/ARR from canonical plan prices.

    Requires: billing:read permission AND is_admin=True.
    """
    _ensure_admin(user)

    service = AdminMetricsService(db=db, plan_service=PlanService())
    snapshot = await service.compute_revenue()

    await AuditService(db=db).log_action(
        user_id=user.id,
        action="admin.revenue.read",
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
    user: User = Depends(require_permission("users:read")),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> BYOKListResponse:
    """List BYOK configurations across all users.

    Requires: users:read permission AND is_admin=True.
    Returns api_key_hint only — never the encrypted key material.
    """
    _ensure_admin(user)

    service = AdminMetricsService(db=db, plan_service=PlanService())
    items, total = await service.list_byok(page=page, per_page=per_page, provider=provider)

    await AuditService(db=db).log_action(
        user_id=user.id,
        action="admin.byok.list",
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
