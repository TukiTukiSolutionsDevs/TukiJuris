"""Tests — internal trial tick endpoint (TD.3).

Direct handler calls (no real DB needed). The tick logic is tested via mocked
trial_svc and db, exercising each dispatch branch.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_internal_trials_routes.py -v
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.trial import RETRY_WINDOW_HOURS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _async_cm():
    """Returns an async context manager that yields None — mirrors db.begin()."""
    @asynccontextmanager
    async def _cm():
        yield None
    return _cm()


def _mock_db(trials: list = None) -> AsyncMock:
    """AsyncMock DB that returns the given trials on execute().scalars().all()."""
    db = AsyncMock()
    # db.begin() must return a FRESH CM on each call (context managers are single-use).
    db.begin = MagicMock(side_effect=lambda: _async_cm())

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = trials or []
    db.execute = AsyncMock(return_value=mock_result)
    db.commit = AsyncMock()
    return db


def _mock_svc(db) -> MagicMock:
    svc = MagicMock()
    svc.db = db
    svc.mark_canceled = AsyncMock()
    svc.mark_downgraded = AsyncMock()
    svc.mark_charged = AsyncMock()
    svc.mark_charge_failed = AsyncMock()
    svc.culqi = MagicMock()
    svc.mp = MagicMock()
    return svc


def _mock_email() -> MagicMock:
    email = MagicMock()
    email.send_trial_email = AsyncMock()
    return email


def _make_trial(
    status: str = "active",
    plan_code: str = "pro",
    card_added_at=None,
    charge_failed_at=None,
    days_remaining: int = 14,
    ends_at=None,
    provider: str | None = None,
    provider_card_token: str | None = None,
    provider_customer_id: str | None = None,
) -> MagicMock:
    t = MagicMock()
    t.id = uuid.uuid4()
    t.user_id = uuid.uuid4()
    t.plan_code = plan_code
    t.status = status
    t.ends_at = ends_at or (
        datetime.now(UTC) - timedelta(hours=1) if days_remaining == 0
        else datetime.now(UTC) + timedelta(days=days_remaining)
    )
    t.card_added_at = card_added_at
    t.charge_failed_at = charge_failed_at
    t.days_remaining = days_remaining
    t.provider = provider
    t.provider_customer_id = provider_customer_id
    t.provider_card_token = provider_card_token
    t.retry_count = 0
    return t


# ---------------------------------------------------------------------------
# Token guard tests (via AsyncClient)
# ---------------------------------------------------------------------------


class TestTokenGuard:
    @pytest.mark.asyncio
    async def test_missing_token_returns_401(self, client):
        res = await client.post("/api/internal/trials/tick")
        assert res.status_code in (401, 422)  # 422 if header missing entirely

    @pytest.mark.asyncio
    async def test_wrong_token_returns_401(self, client):
        res = await client.post(
            "/api/internal/trials/tick",
            headers={"x-internal-token": "wrong-token"},
        )
        assert res.status_code == 401
        assert res.json()["detail"] == "invalid_internal_token"


# ---------------------------------------------------------------------------
# Tick dispatch logic (direct handler calls)
# ---------------------------------------------------------------------------


class TestTrialTickDispatch:
    @pytest.mark.asyncio
    async def test_empty_trial_list_returns_zero_result(self):
        """No trials → result with all zeros."""
        from app.jobs.trial_jobs import run_trial_tick as trial_tick

        db = _mock_db(trials=[])
        svc = _mock_svc(db)
        email = _mock_email()

        result = await trial_tick(db=db, trial_svc=svc, email=email)

        assert result.processed == 0
        assert result.canceled == 0
        assert result.downgraded == 0
        assert result.charged == 0
        assert result.errors == 0

    @pytest.mark.asyncio
    async def test_canceled_pending_expired_calls_mark_canceled(self):
        """canceled_pending + expired → mark_canceled + email."""
        from app.jobs.trial_jobs import run_trial_tick as trial_tick

        trial = _make_trial(
            status="canceled_pending",
            days_remaining=0,
            ends_at=datetime.now(UTC) - timedelta(hours=2),
        )
        db = _mock_db(trials=[trial])
        svc = _mock_svc(db)
        email = _mock_email()

        result = await trial_tick(db=db, trial_svc=svc, email=email)

        assert result.processed == 1
        assert result.canceled == 1
        svc.mark_canceled.assert_called_once_with(trial.id)
        email.send_trial_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_active_expired_no_card_calls_mark_downgraded(self):
        """active + expired + no card → mark_downgraded + email."""
        from app.jobs.trial_jobs import run_trial_tick as trial_tick

        trial = _make_trial(
            status="active",
            days_remaining=0,
            ends_at=datetime.now(UTC) - timedelta(hours=2),
            card_added_at=None,
        )
        db = _mock_db(trials=[trial])
        svc = _mock_svc(db)
        email = _mock_email()

        result = await trial_tick(db=db, trial_svc=svc, email=email)

        assert result.processed == 1
        assert result.downgraded == 1
        svc.mark_downgraded.assert_called_once_with(trial.id)

    @pytest.mark.asyncio
    async def test_active_expired_with_card_submits_charge(self):
        """active + expired + has card → adapter.charge_stored_card called."""
        from app.jobs.trial_jobs import run_trial_tick as trial_tick

        charge_mock = MagicMock()
        charge_mock.success = True
        charge_mock.provider_charge_id = "chr_test_123"

        trial = _make_trial(
            status="active",
            days_remaining=0,
            ends_at=datetime.now(UTC) - timedelta(hours=2),
            card_added_at=datetime.now(UTC) - timedelta(days=5),
            provider="culqi",
            provider_card_token="tok_test_abc",
            provider_customer_id="cus_test_xyz",
        )
        db = _mock_db(trials=[trial])
        svc = _mock_svc(db)
        svc.culqi.charge_stored_card = AsyncMock(return_value=charge_mock)
        email = _mock_email()

        with patch("app.services.plan_service.PlanService.get_price_cents", return_value=9900):
            result = await trial_tick(db=db, trial_svc=svc, email=email)

        assert result.processed == 1
        assert result.charged == 1
        svc.culqi.charge_stored_card.assert_called_once()

    @pytest.mark.asyncio
    async def test_active_expired_charge_fails_calls_mark_charge_failed(self):
        """active + expired + has card + charge fails → mark_charge_failed."""
        from app.jobs.trial_jobs import run_trial_tick as trial_tick

        charge_mock = MagicMock()
        charge_mock.success = False
        charge_mock.error_code = "card_declined"
        charge_mock.error_message = "Insufficient funds"

        trial = _make_trial(
            status="active",
            days_remaining=0,
            ends_at=datetime.now(UTC) - timedelta(hours=2),
            card_added_at=datetime.now(UTC) - timedelta(days=5),
            provider="culqi",
            provider_card_token="tok_test_abc",
            provider_customer_id="cus_test_xyz",
        )
        db = _mock_db(trials=[trial])
        svc = _mock_svc(db)
        svc.culqi.charge_stored_card = AsyncMock(return_value=charge_mock)
        email = _mock_email()

        with patch("app.services.plan_service.PlanService.get_price_cents", return_value=9900):
            result = await trial_tick(db=db, trial_svc=svc, email=email)

        assert result.charge_failed == 1
        svc.mark_charge_failed.assert_called_once()

    @pytest.mark.asyncio
    async def test_charge_failed_window_expired_downgrades(self):
        """charge_failed + 72h window expired → mark_downgraded."""
        from app.jobs.trial_jobs import run_trial_tick as trial_tick

        trial = _make_trial(
            status="charge_failed",
            charge_failed_at=datetime.now(UTC) - timedelta(hours=RETRY_WINDOW_HOURS + 1),
        )
        db = _mock_db(trials=[trial])
        svc = _mock_svc(db)
        email = _mock_email()

        result = await trial_tick(db=db, trial_svc=svc, email=email)

        assert result.downgraded == 1
        svc.mark_downgraded.assert_called_once_with(trial.id)

    @pytest.mark.asyncio
    async def test_charge_failed_window_open_skips_downgrade(self):
        """charge_failed + within 72h window → no action taken."""
        from app.jobs.trial_jobs import run_trial_tick as trial_tick

        trial = _make_trial(
            status="charge_failed",
            charge_failed_at=datetime.now(UTC) - timedelta(hours=10),
        )
        db = _mock_db(trials=[trial])
        svc = _mock_svc(db)
        email = _mock_email()

        result = await trial_tick(db=db, trial_svc=svc, email=email)

        assert result.downgraded == 0
        svc.mark_downgraded.assert_not_called()

    @pytest.mark.asyncio
    async def test_active_expiring_soon_sends_reminder_email(self):
        """active + 3 days remaining → reminder email, no DB mutation."""
        from app.jobs.trial_jobs import run_trial_tick as trial_tick

        trial = _make_trial(status="active", days_remaining=2)
        db = _mock_db(trials=[trial])
        svc = _mock_svc(db)
        email = _mock_email()

        result = await trial_tick(db=db, trial_svc=svc, email=email)

        assert result.errors == 0
        svc.mark_downgraded.assert_not_called()
        email.send_trial_email.assert_called_once()
        call_kwargs = email.send_trial_email.call_args
        assert call_kwargs[0][0] == "trial.reminder_3d"

    @pytest.mark.asyncio
    async def test_error_in_one_trial_increments_errors_continues(self):
        """Exception in one trial → errors += 1, other trials still processed."""
        from app.jobs.trial_jobs import run_trial_tick as trial_tick

        # First trial will raise
        bad_trial = _make_trial(
            status="canceled_pending",
            days_remaining=0,
            ends_at=datetime.now(UTC) - timedelta(hours=2),
        )
        # Second trial will succeed
        good_trial = _make_trial(
            status="active",
            days_remaining=0,
            ends_at=datetime.now(UTC) - timedelta(hours=2),
            card_added_at=None,
        )

        db = _mock_db(trials=[bad_trial, good_trial])
        svc = _mock_svc(db)
        svc.mark_canceled.side_effect = Exception("DB exploded")
        email = _mock_email()

        result = await trial_tick(db=db, trial_svc=svc, email=email)

        assert result.errors == 1
        assert result.downgraded == 1  # good_trial still processed
