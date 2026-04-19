"""Internal trial lifecycle tick endpoint.

POST /internal/trials/tick — protected by X-Internal-Token header.

Thin HTTP wrapper around ``run_trial_tick`` from ``app.jobs.trial_jobs``.
The same function is called by the APScheduler hourly job (see app/scheduler.py).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_email_service, get_trial_service
from app.config import settings
from app.core.database import get_db
from app.jobs.trial_jobs import run_trial_tick
from app.schemas.trials import TrialTickResult
from app.services.email_service import EmailService
from app.services.trial_service import TrialService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["internal"])


# ---------------------------------------------------------------------------
# Token guard
# ---------------------------------------------------------------------------


def _verify_internal_token(x_internal_token: str = Header(...)) -> None:
    """Reject requests missing or mismatching the shared internal secret."""
    if x_internal_token != settings.internal_tick_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_internal_token",
        )


# ---------------------------------------------------------------------------
# POST /internal/trials/tick
# ---------------------------------------------------------------------------


@router.post(
    "/trials/tick",
    response_model=TrialTickResult,
    dependencies=[Depends(_verify_internal_token)],
)
async def trial_tick(
    db: AsyncSession = Depends(get_db),
    trial_svc: TrialService = Depends(get_trial_service),
    email: EmailService = Depends(get_email_service),
) -> TrialTickResult:
    """Run one lifecycle tick for all trials that need action.

    Delegates to ``run_trial_tick`` — same function used by the APScheduler
    hourly job, ensuring parity between scheduled and manually triggered ticks.
    """
    return await run_trial_tick(db, trial_svc, email)
