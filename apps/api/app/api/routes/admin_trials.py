"""Admin trial management routes.

Endpoints:
  GET   /admin/trials           — paginated list with optional filters
  PATCH /admin/trials/{id}      — state transition (force_downgrade, extend_days, etc.)

Defense-in-depth: require_permission enforces RBAC; _ensure_admin enforces is_admin=True.
Both guards must pass (mirrors admin_invoices.py pattern).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_trial_service
from app.models.user import User
from app.rbac.dependencies import require_permission
from app.schemas.trials import (
    AdminTrialFilters,
    AdminTrialListResponse,
    AdminTrialPatch,
    TrialResponse,
)
from app.services.trial_service import TrialService

router = APIRouter(prefix="/admin", tags=["admin-trials"])

# Module-level singletons so tests can override via app.dependency_overrides.
# Each call to require_permission() returns a NEW closure, so we must capture
# them once and reuse the same object everywhere — including in test overrides.
_billing_read = require_permission("billing:read")
_billing_update = require_permission("billing:update")


def _ensure_admin(user: User) -> None:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_required")


# ---------------------------------------------------------------------------
# GET /api/admin/trials
# ---------------------------------------------------------------------------


@router.get("/trials", response_model=AdminTrialListResponse)
async def list_trials_admin(
    status_filter: str | None = Query(default=None, alias="status"),
    plan_code: str | None = Query(default=None),
    expiring_in_days: int | None = Query(default=None, ge=0, le=30),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user: User = Depends(_billing_read),
    trial_svc: TrialService = Depends(get_trial_service),
) -> AdminTrialListResponse:
    """Paginated list of all trials with optional filters."""
    _ensure_admin(user)
    filters = AdminTrialFilters(
        status=status_filter,
        plan_code=plan_code,
        expiring_in_days=expiring_in_days,
        page=page,
        per_page=per_page,
    )
    items, total = await trial_svc.admin_list(filters)
    return AdminTrialListResponse(items=items, total=total, page=page, per_page=per_page)


# ---------------------------------------------------------------------------
# PATCH /api/admin/trials/{trial_id}
# ---------------------------------------------------------------------------


@router.patch("/trials/{trial_id}", response_model=TrialResponse)
async def patch_trial_admin(
    trial_id: uuid.UUID,
    body: AdminTrialPatch,
    user: User = Depends(_billing_update),
    trial_svc: TrialService = Depends(get_trial_service),
) -> object:
    """Admin-initiated trial state transition."""
    _ensure_admin(user)
    return await trial_svc.admin_patch(trial_id, user.id, body)
