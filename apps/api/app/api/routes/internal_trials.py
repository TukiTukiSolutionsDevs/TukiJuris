"""Internal trial lifecycle tick endpoint.

POST /internal/trials/tick — protected by X-Internal-Token header.

Runs one lifecycle pass over all non-terminal trials:
  - active + expired + no card     → mark_downgraded (free plan)
  - active + expired + has card    → charge adapter (HTTP outside tx), mark_charge_failed on failure
  - canceled_pending + expired     → mark_canceled
  - charge_failed + window closed  → mark_downgraded
  - active + expiring ≤3 days      → send reminder email (stub)

Idempotent: safe to call multiple times; each mark_* method is idempotent.

NOTE: Batch E refactors the scheduling logic into app/jobs/trial_jobs.py with APScheduler.
      This endpoint will remain as the externally callable trigger.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_email_service, get_trial_service
from app.config import settings
from app.core.database import get_db
from app.models.trial import RETRY_WINDOW_HOURS, Trial
from app.schemas.trials import TrialTickResult
from app.services.email_service import EmailService
from app.services.plan_service import PlanService
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

    SA pattern:
      1. Load all actionable trials (autobegin implicit tx).
      2. Snapshot needed fields into plain dicts (survive commit).
      3. Commit the read transaction (expire_on_commit=False keeps dicts intact).
      4. For each trial, run mutation inside its own async with db.begin() block.
      5. HTTP adapter calls happen OUTSIDE db.begin() (R-D3: no idle-in-transaction).
    """
    result = TrialTickResult()
    now = datetime.now(UTC)

    # ── Step 1+2: Load and snapshot ──────────────────────────────────────────
    rows = list(
        (
            await db.execute(
                select(Trial).where(
                    Trial.status.in_(["active", "charge_failed", "canceled_pending"])
                )
            )
        )
        .scalars()
        .all()
    )

    # Snapshot all fields we need BEFORE committing the read tx.
    # expire_on_commit=False on the session means objects stay valid,
    # but we snapshot explicitly to make intent clear.
    snapshots: list[dict[str, Any]] = [
        {
            "id": t.id,
            "user_id": t.user_id,
            "status": t.status,
            "ends_at": t.ends_at,
            "card_added_at": t.card_added_at,
            "charge_failed_at": t.charge_failed_at,
            "days_remaining": t.days_remaining,
            "provider": t.provider,
            "provider_customer_id": t.provider_customer_id,
            "provider_card_token": t.provider_card_token,
            "plan_code": t.plan_code,
            "retry_count": t.retry_count,
        }
        for t in rows
    ]

    # ── Step 3: End the read transaction ─────────────────────────────────────
    await db.commit()

    # ── Step 4+5: Per-trial processing ───────────────────────────────────────
    for snap in snapshots:
        trial_id: uuid.UUID = snap["id"]
        user_id: uuid.UUID = snap["user_id"]
        t_status: str = snap["status"]
        ends_at: datetime = snap["ends_at"]
        card_added_at = snap["card_added_at"]
        charge_failed_at = snap["charge_failed_at"]
        days_remaining: int = snap["days_remaining"]
        provider: str | None = snap["provider"]
        provider_customer_id: str | None = snap["provider_customer_id"]
        provider_card_token: str | None = snap["provider_card_token"]
        plan_code: str = snap["plan_code"]

        result.processed += 1

        try:
            expired = ends_at <= now

            # ── canceled_pending + expired → finalize cancellation ────────
            if t_status == "canceled_pending" and expired:
                async with db.begin():
                    await trial_svc.mark_canceled(trial_id)
                result.canceled += 1
                await email.send_trial_email(
                    "trial.canceled_confirmation",
                    user_id=user_id,
                    trial_id=trial_id,
                )

            # ── active + expired + no card → downgrade to free ────────────
            elif t_status == "active" and expired and card_added_at is None:
                async with db.begin():
                    await trial_svc.mark_downgraded(trial_id)
                result.downgraded += 1
                await email.send_trial_email(
                    "trial.downgraded_no_card",
                    user_id=user_id,
                    trial_id=trial_id,
                )

            # ── active + expired + has card → attempt charge ───────────────
            elif t_status == "active" and expired and card_added_at is not None:
                if provider is None or provider_card_token is None:
                    # Card partially added — treat as no-card path
                    async with db.begin():
                        await trial_svc.mark_downgraded(trial_id)
                    result.downgraded += 1
                else:
                    # HTTP charge OUTSIDE db.begin() (R-D3: avoid idle-in-transaction)
                    idem_key = f"{trial_id}:scheduler:{int(now.timestamp() // 3600)}"
                    adapter = trial_svc.culqi if provider == "culqi" else trial_svc.mp
                    amount_cents = PlanService.get_price_cents(plan_code, seat_count=1)

                    charge_result = await adapter.charge_stored_card(
                        customer_id=provider_customer_id or "",
                        card_id=provider_card_token,
                        amount_cents=amount_cents,
                        currency="PEN",
                        metadata={
                            "trial_id": str(trial_id),
                            "user_id": str(user_id),
                            "plan_code": plan_code,
                        },
                        idempotency_key=idem_key,
                    )

                    if charge_result.success:
                        # Webhook will call mark_charged when provider confirms.
                        result.charged += 1
                        logger.info(
                            "trial.tick: charge submitted trial_id=%s charge_id=%s",
                            trial_id,
                            charge_result.provider_charge_id,
                        )
                    else:
                        async with db.begin():
                            await trial_svc.mark_charge_failed(
                                trial_id,
                                reason=(
                                    f"{charge_result.error_code}: "
                                    f"{charge_result.error_message}"
                                ),
                            )
                        result.charge_failed += 1

            # ── charge_failed + retry window closed → downgrade ───────────
            elif t_status == "charge_failed":
                window_expired = charge_failed_at is not None and (
                    now - charge_failed_at > timedelta(hours=RETRY_WINDOW_HOURS)
                )
                if window_expired:
                    async with db.begin():
                        await trial_svc.mark_downgraded(trial_id)
                    result.downgraded += 1
                    await email.send_trial_email(
                        "trial.downgraded_no_card",
                        user_id=user_id,
                        trial_id=trial_id,
                    )

            # ── active + expiring soon → reminder email ───────────────────
            elif t_status == "active" and 0 < days_remaining <= 3:
                await email.send_trial_email(
                    "trial.reminder_3d",
                    user_id=user_id,
                    trial_id=trial_id,
                    days_remaining=days_remaining,
                )

        except Exception:
            logger.exception("trial.tick: unhandled error for trial_id=%s", trial_id)
            result.errors += 1

    return result
