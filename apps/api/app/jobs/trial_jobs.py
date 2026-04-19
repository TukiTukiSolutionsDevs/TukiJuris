"""Trial lifecycle scheduler job.

Contains the reusable ``run_trial_tick`` function shared between:
  - POST /internal/trials/tick  (externally triggered, token-gated)
  - APScheduler hourly job      (in-process, see app/scheduler.py)

The ``scheduled_trial_tick`` coroutine is the APScheduler entry point: it
creates its own DB session and service instances (no request context available
in a scheduled job).
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trial import RETRY_WINDOW_HOURS, Trial
from app.schemas.trials import TrialTickResult
from app.services.email_service import EmailService
from app.services.plan_service import PlanService
from app.services.trial_service import TrialService

logger = logging.getLogger(__name__)


async def run_trial_tick(
    db: AsyncSession,
    trial_svc: TrialService,
    email: EmailService,
) -> TrialTickResult:
    """Run one lifecycle tick over all non-terminal trials.

    SA session pattern (see internal_trials.py for detailed comments):
      1. SELECT all actionable trials → snapshot → await db.commit()
      2. Per-trial mutations inside async with db.begin()
      3. HTTP charges OUTSIDE db.begin() (R-D3)
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
        }
        for t in rows
    ]

    # ── Step 3: End implicit read transaction ─────────────────────────────────
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

            if t_status == "canceled_pending" and expired:
                async with db.begin():
                    await trial_svc.mark_canceled(trial_id)
                result.canceled += 1
                await email.send_trial_email(
                    "trial.canceled_confirmation",
                    user_id=user_id,
                    trial_id=trial_id,
                )

            elif t_status == "active" and expired and card_added_at is None:
                async with db.begin():
                    await trial_svc.mark_downgraded(trial_id)
                result.downgraded += 1
                await email.send_trial_email(
                    "trial.downgraded_no_card",
                    user_id=user_id,
                    trial_id=trial_id,
                )

            elif t_status == "active" and expired and card_added_at is not None:
                if provider is None or provider_card_token is None:
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


async def scheduled_trial_tick() -> None:
    """APScheduler entry point — creates its own DB session and services.

    This runs outside any HTTP request context, so we can't use FastAPI's
    dependency injection. We create the session and services manually.
    """
    from app.api.deps import get_culqi_adapter, get_mp_adapter
    from app.config import settings
    from app.core.database import async_session_factory
    from app.rbac.audit import AuditService
    from app.services.email_service import email_service
    from app.services.trial_service import TrialService

    logger.info("trial.scheduler: starting tick")
    async with async_session_factory() as session:
        try:
            audit = AuditService(session)
            trial_svc = TrialService(
                db=session,
                audit=audit,
                culqi=get_culqi_adapter(),
                mp=get_mp_adapter(),
                email=email_service,
                settings=settings,
            )
            result = await run_trial_tick(session, trial_svc, email_service)
            logger.info(
                "trial.scheduler: tick complete processed=%d charged=%d "
                "downgraded=%d canceled=%d failed=%d errors=%d",
                result.processed,
                result.charged,
                result.downgraded,
                result.canceled,
                result.charge_failed,
                result.errors,
            )
        except Exception:
            logger.exception("trial.scheduler: tick failed")
            await session.rollback()
