"""Trial lifecycle routes — user-facing endpoints.

All endpoints (except GET /trials/current) return 503 when TRIALS_ENABLED=false.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import RateLimitBucket, RateLimitGuard, get_current_user, get_trial_service
from app.config import settings
from app.models.user import User
from app.schemas.trials import AddCardRequest, StartTrialRequest, TrialResponse
from app.services.trial_service import TrialService

router = APIRouter(prefix="/trials", tags=["trials"])


def _guard_trials_enabled() -> None:
    if not settings.trials_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="trials_not_enabled",
        )


# ---------------------------------------------------------------------------
# GET /api/trials/current
# ---------------------------------------------------------------------------


@router.get("/current", response_model=TrialResponse | None)
async def get_current_trial(
    current_user: User = Depends(get_current_user),
    trial_svc: TrialService = Depends(get_trial_service),
) -> object:
    """Return the most recent trial for the authenticated user, or null."""
    return await trial_svc.get_current(current_user.id)


# ---------------------------------------------------------------------------
# POST /api/trials
# ---------------------------------------------------------------------------


@router.post("", response_model=TrialResponse, status_code=status.HTTP_201_CREATED)
async def start_trial(
    body: StartTrialRequest,
    current_user: User = Depends(get_current_user),
    trial_svc: TrialService = Depends(get_trial_service),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> object:
    """Start a 14-day free trial for the given plan."""
    _guard_trials_enabled()
    return await trial_svc.start_trial(current_user.id, body.plan_code)


# ---------------------------------------------------------------------------
# POST /api/trials/{trial_id}/add-card
# ---------------------------------------------------------------------------


@router.post("/{trial_id}/add-card", response_model=TrialResponse)
async def add_card(
    trial_id: uuid.UUID,
    body: AddCardRequest,
    current_user: User = Depends(get_current_user),
    trial_svc: TrialService = Depends(get_trial_service),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> object:
    """Add a payment card to an active trial (triggers auto-charge at end of trial)."""
    _guard_trials_enabled()
    return await trial_svc.add_card(
        trial_id,
        current_user.id,
        body.provider,
        body.token_id,
        body.customer_info,
    )


# ---------------------------------------------------------------------------
# DELETE /api/trials/{trial_id}
# ---------------------------------------------------------------------------


@router.delete("/{trial_id}", response_model=TrialResponse)
async def cancel_trial(
    trial_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    trial_svc: TrialService = Depends(get_trial_service),
) -> object:
    """Cancel an active trial (transitions to canceled_pending until trial end)."""
    _guard_trials_enabled()
    return await trial_svc.cancel(trial_id, current_user.id)


# ---------------------------------------------------------------------------
# POST /api/trials/{trial_id}/retry-charge
# ---------------------------------------------------------------------------


@router.post("/{trial_id}/retry-charge", response_model=TrialResponse)
async def retry_charge(
    trial_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    trial_svc: TrialService = Depends(get_trial_service),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> object:
    """User-initiated retry of a failed trial charge (72-hour retry window)."""
    _guard_trials_enabled()
    return await trial_svc.retry_charge(trial_id, current_user.id)
