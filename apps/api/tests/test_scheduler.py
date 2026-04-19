"""Tests — APScheduler integration (Batch E).

Tests:
  - start_scheduler registers trial_tick job when both flags enabled
  - start_scheduler skips when SCHEDULER_ENABLED=false
  - start_scheduler skips trial_tick when TRIALS_ENABLED=false
  - stop_scheduler shuts down a running scheduler

All tests reset the scheduler singleton to avoid cross-test interference.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_scheduler.py -v
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _reset_scheduler():
    """Reset the module-level _scheduler singleton to None."""
    import app.scheduler as sched_mod
    sched_mod._scheduler = None


class TestStartScheduler:
    @pytest.mark.asyncio
    async def test_starts_with_trial_tick_when_both_enabled(self):
        """SCHEDULER_ENABLED=true + TRIALS_ENABLED=true → scheduler starts with job."""
        _reset_scheduler()

        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        with patch("app.scheduler.AsyncIOScheduler", return_value=mock_scheduler), \
             patch("app.scheduler.settings") as mock_settings:
            mock_settings.scheduler_enabled = True
            mock_settings.trials_enabled = True

            from app.scheduler import start_scheduler
            await start_scheduler()

        mock_scheduler.add_job.assert_called_once()
        call_kwargs = mock_scheduler.add_job.call_args
        assert call_kwargs[1]["id"] == "trial_tick"
        assert call_kwargs[1]["trigger"] == "interval"
        mock_scheduler.start.assert_called_once()

        _reset_scheduler()

    @pytest.mark.asyncio
    async def test_does_not_start_when_scheduler_disabled(self):
        """SCHEDULER_ENABLED=false → scheduler not started at all."""
        _reset_scheduler()

        mock_scheduler = MagicMock()

        with patch("app.scheduler.AsyncIOScheduler", return_value=mock_scheduler), \
             patch("app.scheduler.settings") as mock_settings:
            mock_settings.scheduler_enabled = False
            mock_settings.trials_enabled = True

            from app.scheduler import start_scheduler
            await start_scheduler()

        mock_scheduler.start.assert_not_called()
        mock_scheduler.add_job.assert_not_called()

        _reset_scheduler()

    @pytest.mark.asyncio
    async def test_starts_without_trial_tick_when_trials_disabled(self):
        """SCHEDULER_ENABLED=true + TRIALS_ENABLED=false → scheduler starts but no job added."""
        _reset_scheduler()

        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        with patch("app.scheduler.AsyncIOScheduler", return_value=mock_scheduler), \
             patch("app.scheduler.settings") as mock_settings:
            mock_settings.scheduler_enabled = True
            mock_settings.trials_enabled = False

            from app.scheduler import start_scheduler
            await start_scheduler()

        mock_scheduler.start.assert_called_once()
        mock_scheduler.add_job.assert_not_called()

        _reset_scheduler()


class TestStopScheduler:
    def test_stops_running_scheduler(self):
        """stop_scheduler calls shutdown on running scheduler."""
        _reset_scheduler()

        mock_scheduler = MagicMock()
        mock_scheduler.running = True

        import app.scheduler as sched_mod
        sched_mod._scheduler = mock_scheduler

        from app.scheduler import stop_scheduler
        stop_scheduler()

        mock_scheduler.shutdown.assert_called_once_with(wait=False)
        assert sched_mod._scheduler is None

    def test_stop_is_noop_when_not_running(self):
        """stop_scheduler is safe to call when scheduler is None."""
        _reset_scheduler()

        from app.scheduler import stop_scheduler
        stop_scheduler()  # should not raise

        import app.scheduler as sched_mod
        assert sched_mod._scheduler is None

    def test_stop_is_noop_when_scheduler_not_running(self):
        """stop_scheduler skips shutdown if scheduler exists but not running."""
        _reset_scheduler()

        mock_scheduler = MagicMock()
        mock_scheduler.running = False

        import app.scheduler as sched_mod
        sched_mod._scheduler = mock_scheduler

        from app.scheduler import stop_scheduler
        stop_scheduler()

        mock_scheduler.shutdown.assert_not_called()
