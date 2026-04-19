"""APScheduler integration for TukiJuris.

Manages an in-process ``AsyncIOScheduler`` that runs the trial lifecycle tick
hourly. Only one instance should schedule jobs — set SCHEDULER_ENABLED=false
on secondary API containers (see docs/scheduler-runbook.md).

Usage (from lifespan)::

    from app.scheduler import start_scheduler, stop_scheduler

    @asynccontextmanager
    async def lifespan(app):
        await start_scheduler()
        yield
        await stop_scheduler()
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Return the global scheduler singleton, creating it if needed."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")
    return _scheduler


async def start_scheduler() -> None:
    """Configure and start the scheduler.

    Guards:
      - SCHEDULER_ENABLED=false → skip (multi-instance safety)
      - TRIALS_ENABLED=false → skip trial tick job
    """
    if not settings.scheduler_enabled:
        logger.info("scheduler: SCHEDULER_ENABLED=false — not starting")
        return

    scheduler = get_scheduler()

    if settings.trials_enabled:
        from app.jobs.trial_jobs import scheduled_trial_tick

        scheduler.add_job(
            scheduled_trial_tick,
            trigger="interval",
            hours=1,
            id="trial_tick",
            replace_existing=True,
            misfire_grace_time=300,  # tolerate up to 5 min late fires
        )
        logger.info("scheduler: registered trial_tick job (hourly)")
    else:
        logger.info("scheduler: TRIALS_ENABLED=false — trial tick not registered")

    scheduler.start()
    logger.info("scheduler: started")


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler (sync — called from lifespan teardown)."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("scheduler: stopped")
    _scheduler = None
