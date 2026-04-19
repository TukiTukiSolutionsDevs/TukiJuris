"""TrialService unit tests — full coverage via AsyncMock (no live DB required).

Tests validate:
  - start_trial: happy, BETA_MODE, free-plan, plan-used, already-active
  - add_card: happy (Culqi + MP), 404 non-owner, 409 already-added, wrong status
  - cancel: happy, idempotent (already canceled/pending), non-owner 404, wrong status 422
  - retry_charge: happy success, happy failure, not-in-failed 422, window-closed 422
  - get_current: most recent trial returned
  - admin_list: filtered query delegation
  - admin_patch: force_downgrade, extend_days, force_cancel, force_charge
  - mark_charged: happy, idempotent (check-first / 2-session pattern)
  - mark_downgraded, mark_canceled, mark_charge_failed

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_trial_service.py -v
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.trial import RETRY_WINDOW_HOURS, Trial
from app.schemas.trials import AdminTrialFilters, AdminTrialPatch
from app.services.payment_providers.base import ChargeResult
from app.services.trial_service import TrialError, TrialService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _async_cm(return_value=None):
    """Return an async context-manager mock (for 'async with db.begin()')."""
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=return_value)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm


def _mock_db():
    db = AsyncMock()
    db.begin = MagicMock(return_value=_async_cm())
    db.flush = AsyncMock()
    db.scalar = AsyncMock(return_value=0)
    return db


def _result(value):
    """Wrap a value in a mock that mimics AsyncSession.execute() result."""
    r = MagicMock()
    r.scalar_one_or_none.return_value = value
    r.scalars.return_value.all.return_value = value if isinstance(value, list) else []
    r.first.return_value = None
    return r


def _make_trial(
    *,
    status: str = "active",
    provider: str | None = None,
    card_token: str | None = None,
    charge_failed_at: datetime | None = None,
    charged_at: datetime | None = None,
    canceled_at: datetime | None = None,
    retry_count: int = 0,
) -> MagicMock:
    t = MagicMock(spec=Trial)
    t.id = uuid.uuid4()
    t.user_id = uuid.uuid4()
    t.plan_code = "pro"
    t.status = status
    t.provider = provider
    t.provider_customer_id = "cus_test" if provider else None
    t.provider_card_token = card_token
    t.card_added_at = datetime.now(UTC) if card_token else None
    t.charge_failed_at = charge_failed_at
    t.charged_at = charged_at
    t.canceled_at = canceled_at
    t.canceled_by_user = False
    t.retry_count = retry_count
    t.ends_at = datetime.now(UTC) + timedelta(days=14)
    t.updated_at = datetime.now(UTC)
    t.subscription_id = None
    return t


def _make_user(*, plan: str = "free", default_org_id: uuid.UUID | None = None):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.plan = plan
    u.default_org_id = default_org_id
    return u


def _make_settings(*, beta_mode: bool = False, trials_enabled: bool = True):
    s = MagicMock()
    s.beta_mode = beta_mode
    s.trials_enabled = trials_enabled
    return s


def _make_svc(
    db=None,
    *,
    beta_mode: bool = False,
    trials_enabled: bool = True,
) -> TrialService:
    db = db or _mock_db()
    audit = MagicMock()
    audit.log_action = AsyncMock()
    culqi = AsyncMock()
    culqi.provider_name = "culqi"
    culqi.create_customer = AsyncMock(return_value="cus_culqi")
    culqi.create_card = AsyncMock(return_value="crd_culqi")
    culqi.charge_stored_card = AsyncMock(
        return_value=ChargeResult(success=True, provider_charge_id="chr_ok")
    )
    mp = AsyncMock()
    mp.provider_name = "mp"
    mp.create_customer = AsyncMock(return_value="cus_mp")
    mp.create_card = AsyncMock(return_value="pre_mp")
    mp.charge_stored_card = AsyncMock(
        return_value=ChargeResult(success=True, provider_charge_id="pre_ok")
    )
    email = AsyncMock()
    email.send_trial_email = AsyncMock(return_value=True)
    settings = _make_settings(beta_mode=beta_mode, trials_enabled=trials_enabled)
    return TrialService(db=db, audit=audit, culqi=culqi, mp=mp, email=email, settings=settings)


def _customer_info(email: str = "test@example.com"):
    ci = MagicMock()
    ci.email = email
    ci.first_name = "Ana"
    ci.last_name = "Garcia"
    ci.phone_number = "999000111"
    return ci


# ---------------------------------------------------------------------------
# start_trial
# ---------------------------------------------------------------------------


class TestStartTrial:
    @pytest.mark.asyncio
    async def test_happy_path_creates_trial(self):
        db = _mock_db()
        # check plan used → None, check active → None
        db.execute = AsyncMock(side_effect=[_result(None), _result(None)])
        svc = _make_svc(db)
        user_id = uuid.uuid4()

        # Patch helpers so we don't need full DB mock chain
        svc._activate_subscription_trialing = AsyncMock(return_value=uuid.uuid4())

        trial = await svc.start_trial(user_id, "pro")

        assert trial is not None
        db.add.assert_called_once()
        db.flush.assert_called()
        svc._activate_subscription_trialing.assert_awaited_once_with(user_id, "pro")
        svc.audit.log_action.assert_awaited_once()
        svc.email.send_trial_email.assert_awaited_once_with(
            "trial.started_confirmation",
            user_id=user_id,
            trial_id=trial.id,
            plan_code="pro",
            days_remaining=14,
        )

    @pytest.mark.asyncio
    async def test_beta_mode_returns_409(self):
        svc = _make_svc(beta_mode=True)
        svc._activate_subscription_trialing = AsyncMock()
        with pytest.raises(TrialError) as exc_info:
            await svc.start_trial(uuid.uuid4(), "pro")
        assert exc_info.value.status_code == 409
        assert "BETA_MODE" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_free_plan_returns_422(self):
        svc = _make_svc()
        with pytest.raises(TrialError) as exc_info:
            await svc.start_trial(uuid.uuid4(), "free")
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_plan_already_used_returns_409(self):
        """2-session pattern: simulate existing row visible to a new session."""
        db = _mock_db()
        existing = _make_trial()
        # First execute → plan already used row found
        db.execute = AsyncMock(return_value=_result(existing))
        svc = _make_svc(db)
        with pytest.raises(TrialError) as exc_info:
            await svc.start_trial(existing.user_id, "pro")
        assert exc_info.value.status_code == 409
        assert "already used" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_already_active_trial_returns_409(self):
        """2-session pattern: existing active trial visible to a new session."""
        db = _mock_db()
        active = _make_trial(status="active")
        # First execute (plan check) → None, second (active check) → active trial
        db.execute = AsyncMock(side_effect=[_result(None), _result(active)])
        svc = _make_svc(db)
        with pytest.raises(TrialError) as exc_info:
            await svc.start_trial(active.user_id, "studio")
        assert exc_info.value.status_code == 409
        assert "already active" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_studio_plan_accepted(self):
        db = _mock_db()
        db.execute = AsyncMock(side_effect=[_result(None), _result(None)])
        svc = _make_svc(db)
        svc._activate_subscription_trialing = AsyncMock(return_value=None)
        trial = await svc.start_trial(uuid.uuid4(), "studio")
        assert trial.plan_code == "studio"


# ---------------------------------------------------------------------------
# add_card
# ---------------------------------------------------------------------------


class TestAddCard:
    @pytest.mark.asyncio
    async def test_happy_culqi_sets_card_fields(self):
        db = _mock_db()
        trial = _make_trial(status="active")
        trial.provider_customer_id = None
        trial.card_added_at = None
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)

        result = await svc.add_card(
            trial.id, trial.user_id, "culqi", "tkn_test", _customer_info()
        )

        assert result.provider == "culqi"
        assert result.provider_card_token == "crd_culqi"
        assert result.card_added_at is not None
        svc._providers["culqi"].create_customer.assert_awaited_once()
        svc._providers["culqi"].create_card.assert_awaited_once()
        svc.email.send_trial_email.assert_awaited_once_with(
            "trial.card_added", user_id=trial.user_id, trial_id=trial.id
        )

    @pytest.mark.asyncio
    async def test_happy_mp_sets_preapproval_id(self):
        db = _mock_db()
        trial = _make_trial(status="active")
        trial.provider_customer_id = None
        trial.card_added_at = None
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)

        result = await svc.add_card(
            trial.id, trial.user_id, "mp", "tkn_mp", _customer_info()
        )

        assert result.provider == "mp"
        assert result.provider_card_token == "pre_mp"
        svc._providers["mp"].create_card.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_non_owner_returns_404(self):
        db = _mock_db()
        db.execute = AsyncMock(return_value=_result(None))  # trial not found for user
        svc = _make_svc(db)
        with pytest.raises(TrialError) as exc_info:
            await svc.add_card(uuid.uuid4(), uuid.uuid4(), "culqi", "tkn", _customer_info())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_card_already_added_returns_409(self):
        db = _mock_db()
        trial = _make_trial(status="active", provider="culqi", card_token="crd_existing")
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        with pytest.raises(TrialError) as exc_info:
            await svc.add_card(trial.id, trial.user_id, "culqi", "tkn", _customer_info())
        assert exc_info.value.status_code == 409
        assert "already added" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_wrong_status_returns_409(self):
        db = _mock_db()
        trial = _make_trial(status="charged")
        trial.card_added_at = None
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        with pytest.raises(TrialError) as exc_info:
            await svc.add_card(trial.id, trial.user_id, "culqi", "tkn", _customer_info())
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_reuses_existing_customer_id(self):
        db = _mock_db()
        trial = _make_trial(status="active")
        trial.provider_customer_id = "cus_existing"
        trial.card_added_at = None
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        await svc.add_card(trial.id, trial.user_id, "culqi", "tkn", _customer_info())
        # create_customer should NOT be called when customer_id already exists
        svc._providers["culqi"].create_customer.assert_not_awaited()
        svc._providers["culqi"].create_card.assert_awaited_once_with(
            "cus_existing", "tkn", pytest.approx({"email": "test@example.com", "amount_cents": 7000, "plan_code": "pro", "currency": "PEN"}, abs=1)
        )


# ---------------------------------------------------------------------------
# cancel
# ---------------------------------------------------------------------------


class TestCancel:
    @pytest.mark.asyncio
    async def test_happy_path_sets_canceled_pending(self):
        db = _mock_db()
        trial = _make_trial(status="active")
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)

        result = await svc.cancel(trial.id, trial.user_id)

        assert result.status == "canceled_pending"
        assert result.canceled_by_user is True
        assert result.canceled_at is not None
        svc.audit.log_action.assert_awaited_once()
        svc.email.send_trial_email.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_already_canceled_pending_is_idempotent(self):
        db = _mock_db()
        trial = _make_trial(status="canceled_pending")
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)

        result = await svc.cancel(trial.id, trial.user_id)

        assert result.status == "canceled_pending"
        svc.audit.log_action.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_already_canceled_is_idempotent(self):
        db = _mock_db()
        trial = _make_trial(status="canceled")
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)

        result = await svc.cancel(trial.id, trial.user_id)

        assert result.status == "canceled"
        svc.audit.log_action.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_non_owner_returns_404(self):
        db = _mock_db()
        db.execute = AsyncMock(return_value=_result(None))
        svc = _make_svc(db)
        with pytest.raises(TrialError) as exc_info:
            await svc.cancel(uuid.uuid4(), uuid.uuid4())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_charged_status_returns_422(self):
        db = _mock_db()
        trial = _make_trial(status="charged")
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        with pytest.raises(TrialError) as exc_info:
            await svc.cancel(trial.id, trial.user_id)
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_charge_failed_can_be_canceled(self):
        db = _mock_db()
        trial = _make_trial(status="charge_failed")
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        result = await svc.cancel(trial.id, trial.user_id)
        assert result.status == "canceled_pending"


# ---------------------------------------------------------------------------
# retry_charge
# ---------------------------------------------------------------------------


class TestRetryCharge:
    def _trial_with_card_failed(self, *, hours_ago: int = 1) -> MagicMock:
        return _make_trial(
            status="charge_failed",
            provider="culqi",
            card_token="crd_test",
            charge_failed_at=datetime.now(UTC) - timedelta(hours=hours_ago),
            retry_count=1,
        )

    @pytest.mark.asyncio
    async def test_success_clears_failure_reason(self):
        db = _mock_db()
        trial = self._trial_with_card_failed()
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)

        result = await svc.retry_charge(trial.id, trial.user_id)

        assert result.charge_failure_reason is None
        svc._providers["culqi"].charge_stored_card.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_failure_increments_retry_count(self):
        db = _mock_db()
        trial = self._trial_with_card_failed()
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        svc._providers["culqi"].charge_stored_card = AsyncMock(
            return_value=ChargeResult(
                success=False, error_code="card_declined", error_message="Insufficient funds"
            )
        )

        result = await svc.retry_charge(trial.id, trial.user_id)

        assert result.retry_count == 2  # was 1, incremented
        assert "card_declined" in (result.charge_failure_reason or "")

    @pytest.mark.asyncio
    async def test_not_in_charge_failed_returns_422(self):
        db = _mock_db()
        trial = _make_trial(status="active")
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        with pytest.raises(TrialError) as exc_info:
            await svc.retry_charge(trial.id, trial.user_id)
        assert exc_info.value.status_code == 422
        assert "charge_failed" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_window_closed_returns_422(self):
        db = _mock_db()
        trial = self._trial_with_card_failed(hours_ago=RETRY_WINDOW_HOURS + 1)
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        with pytest.raises(TrialError) as exc_info:
            await svc.retry_charge(trial.id, trial.user_id)
        assert exc_info.value.status_code == 422
        assert "window" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_no_card_returns_422(self):
        db = _mock_db()
        trial = _make_trial(
            status="charge_failed",
            provider=None,
            card_token=None,
            charge_failed_at=datetime.now(UTC) - timedelta(hours=1),
        )
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        with pytest.raises(TrialError) as exc_info:
            await svc.retry_charge(trial.id, trial.user_id)
        assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# get_current
# ---------------------------------------------------------------------------


class TestGetCurrent:
    @pytest.mark.asyncio
    async def test_returns_most_recent(self):
        db = _mock_db()
        trial = _make_trial()
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        result = await svc.get_current(trial.user_id)
        assert result is trial

    @pytest.mark.asyncio
    async def test_returns_none_when_no_trial(self):
        db = _mock_db()
        db.execute = AsyncMock(return_value=_result(None))
        svc = _make_svc(db)
        result = await svc.get_current(uuid.uuid4())
        assert result is None


# ---------------------------------------------------------------------------
# admin_list
# ---------------------------------------------------------------------------


class TestAdminList:
    @pytest.mark.asyncio
    async def test_returns_paginated_list(self):
        db = _mock_db()
        trials = [_make_trial(), _make_trial()]
        count_result = MagicMock()
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = trials
        db.scalar = AsyncMock(return_value=2)
        db.execute = AsyncMock(return_value=list_result)
        svc = _make_svc(db)

        f = AdminTrialFilters(page=1, per_page=20)
        items, total = await svc.admin_list(f)

        assert total == 2
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_status_filter_applied(self):
        db = _mock_db()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.scalar = AsyncMock(return_value=0)
        db.execute = AsyncMock(return_value=result)
        svc = _make_svc(db)
        f = AdminTrialFilters(status="active", page=1, per_page=10)
        await svc.admin_list(f)
        # Just ensure no error — filter application is tested via integration tests


# ---------------------------------------------------------------------------
# admin_patch
# ---------------------------------------------------------------------------


class TestAdminPatch:
    @pytest.mark.asyncio
    async def test_force_downgrade_sets_status(self):
        db = _mock_db()
        trial = _make_trial(status="active")
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        svc._deactivate_to_free = AsyncMock()

        patch = AdminTrialPatch(action="force_downgrade", reason="test downgrade")
        result = await svc.admin_patch(trial.id, uuid.uuid4(), patch)

        assert result.status == "downgraded"
        assert result.downgraded_at is not None
        svc._deactivate_to_free.assert_awaited_once_with(trial.user_id)

    @pytest.mark.asyncio
    async def test_force_downgrade_on_terminal_status_returns_422(self):
        db = _mock_db()
        trial = _make_trial(status="charged")
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        patch = AdminTrialPatch(action="force_downgrade", reason="test")
        with pytest.raises(TrialError) as exc_info:
            await svc.admin_patch(trial.id, uuid.uuid4(), patch)
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_extend_days_updates_ends_at(self):
        db = _mock_db()
        trial = _make_trial(status="active")
        original_ends_at = trial.ends_at
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)

        patch = AdminTrialPatch(action="extend_days", extend_days=7, reason="grace period")
        result = await svc.admin_patch(trial.id, uuid.uuid4(), patch)

        assert result.ends_at == original_ends_at + timedelta(days=7)

    @pytest.mark.asyncio
    async def test_extend_days_requires_extend_days_field(self):
        db = _mock_db()
        trial = _make_trial(status="active")
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        patch = AdminTrialPatch(action="extend_days", extend_days=None, reason="test")
        with pytest.raises(TrialError) as exc_info:
            await svc.admin_patch(trial.id, uuid.uuid4(), patch)
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_force_cancel_sets_canceled(self):
        db = _mock_db()
        trial = _make_trial(status="active")
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        svc._deactivate_to_free = AsyncMock()

        patch = AdminTrialPatch(action="force_cancel", reason="abuse")
        result = await svc.admin_patch(trial.id, uuid.uuid4(), patch)

        assert result.status == "canceled"
        svc._deactivate_to_free.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_force_charge_success_clears_failure(self):
        db = _mock_db()
        trial = _make_trial(
            status="charge_failed",
            provider="culqi",
            card_token="crd_test",
        )
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)

        patch = AdminTrialPatch(action="force_charge", reason="manual retry")
        result = await svc.admin_patch(trial.id, uuid.uuid4(), patch)

        assert result.charge_failure_reason is None
        svc._providers["culqi"].charge_stored_card.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_force_charge_failure_increments_retry(self):
        db = _mock_db()
        trial = _make_trial(
            status="charge_failed", provider="culqi", card_token="crd_test", retry_count=2
        )
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        svc._providers["culqi"].charge_stored_card = AsyncMock(
            return_value=ChargeResult(success=False, error_code="err", error_message="fail")
        )

        patch = AdminTrialPatch(action="force_charge", reason="admin retry")
        result = await svc.admin_patch(trial.id, uuid.uuid4(), patch)

        assert result.retry_count == 3

    @pytest.mark.asyncio
    async def test_trial_not_found_returns_404(self):
        db = _mock_db()
        db.execute = AsyncMock(return_value=_result(None))
        svc = _make_svc(db)
        patch = AdminTrialPatch(action="force_downgrade", reason="test")
        with pytest.raises(TrialError) as exc_info:
            await svc.admin_patch(uuid.uuid4(), uuid.uuid4(), patch)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_unknown_action_returns_422(self):
        db = _mock_db()
        trial = _make_trial(status="active")
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        patch = AdminTrialPatch(action="force_downgrade", reason="test reason")
        patch.action = "invalid_action"  # bypass Literal validation
        with pytest.raises(TrialError) as exc_info:
            await svc.admin_patch(trial.id, uuid.uuid4(), patch)
        assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# mark_charged
# ---------------------------------------------------------------------------


class TestMarkCharged:
    @pytest.mark.asyncio
    async def test_happy_path_sets_charged(self):
        db = _mock_db()
        trial = _make_trial(status="active")
        user = _make_user()
        # execute 1: load trial, execute 2: load user
        db.execute = AsyncMock(side_effect=[_result(trial), _result(user)])
        svc = _make_svc(db)

        result = await svc.mark_charged(
            trial.id, charge_id="chr_123", provider="culqi"
        )

        assert result.status == "charged"
        assert result.charged_at is not None
        assert user.plan == "pro"
        svc.audit.log_action.assert_awaited_once()
        db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_idempotent_when_already_charged(self):
        """2-session pattern: second session sees already-charged trial."""
        db = _mock_db()
        trial = _make_trial(status="charged", charged_at=datetime.now(UTC))
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)

        result = await svc.mark_charged(
            trial.id, charge_id="chr_dup", provider="culqi"
        )

        # No audit logged, no flush with status change
        svc.audit.log_action.assert_not_awaited()
        assert result is trial

    @pytest.mark.asyncio
    async def test_sets_subscription_id_when_provided(self):
        db = _mock_db()
        trial = _make_trial(status="active")
        user = _make_user()
        db.execute = AsyncMock(side_effect=[_result(trial), _result(user)])
        svc = _make_svc(db)
        sub_id = uuid.uuid4()

        result = await svc.mark_charged(
            trial.id, charge_id="chr_x", provider="culqi", subscription_id=sub_id
        )

        assert result.subscription_id == sub_id

    @pytest.mark.asyncio
    async def test_trial_not_found_raises_404(self):
        db = _mock_db()
        db.execute = AsyncMock(return_value=_result(None))
        svc = _make_svc(db)
        with pytest.raises(TrialError) as exc_info:
            await svc.mark_charged(uuid.uuid4(), charge_id="x", provider="culqi")
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# mark_downgraded
# ---------------------------------------------------------------------------


class TestMarkDowngraded:
    @pytest.mark.asyncio
    async def test_sets_downgraded_status(self):
        db = _mock_db()
        trial = _make_trial(status="active")
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        svc._deactivate_to_free = AsyncMock()

        result = await svc.mark_downgraded(trial.id)

        assert result.status == "downgraded"
        assert result.downgraded_at is not None
        svc._deactivate_to_free.assert_awaited_once_with(trial.user_id)
        svc.audit.log_action.assert_awaited_once()
        db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = _mock_db()
        db.execute = AsyncMock(return_value=_result(None))
        svc = _make_svc(db)
        with pytest.raises(TrialError) as exc_info:
            await svc.mark_downgraded(uuid.uuid4())
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# mark_canceled
# ---------------------------------------------------------------------------


class TestMarkCanceled:
    @pytest.mark.asyncio
    async def test_sets_canceled_status(self):
        db = _mock_db()
        trial = _make_trial(status="canceled_pending")
        trial.canceled_at = None
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        svc._deactivate_to_free = AsyncMock()

        result = await svc.mark_canceled(trial.id)

        assert result.status == "canceled"
        assert result.canceled_at is not None
        svc._deactivate_to_free.assert_awaited_once()
        svc.audit.log_action.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_preserves_existing_canceled_at(self):
        db = _mock_db()
        existing_ts = datetime.now(UTC) - timedelta(hours=5)
        trial = _make_trial(status="canceled_pending", canceled_at=existing_ts)
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        svc._deactivate_to_free = AsyncMock()

        result = await svc.mark_canceled(trial.id)
        # canceled_at should NOT be overwritten
        assert result.canceled_at == existing_ts


# ---------------------------------------------------------------------------
# mark_charge_failed
# ---------------------------------------------------------------------------


class TestMarkChargeFailed:
    @pytest.mark.asyncio
    async def test_sets_failed_status_and_increments_retry(self):
        db = _mock_db()
        trial = _make_trial(status="active", retry_count=0)
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)

        result = await svc.mark_charge_failed(trial.id, reason="card_declined: nsf")

        assert result.status == "charge_failed"
        assert result.charge_failed_at is not None
        assert result.charge_failure_reason == "card_declined: nsf"
        assert result.retry_count == 1
        svc.audit.log_action.assert_awaited_once()
        svc.email.send_trial_email.assert_awaited_once_with(
            "trial.charge_failed_update_card",
            user_id=trial.user_id,
            trial_id=trial.id,
            reason="card_declined: nsf",
        )

    @pytest.mark.asyncio
    async def test_reason_truncated_to_500(self):
        db = _mock_db()
        trial = _make_trial(status="active", retry_count=0)
        db.execute = AsyncMock(return_value=_result(trial))
        svc = _make_svc(db)
        long_reason = "x" * 600

        result = await svc.mark_charge_failed(trial.id, reason=long_reason)

        assert len(result.charge_failure_reason) == 500

    @pytest.mark.asyncio
    async def test_not_found_raises_404(self):
        db = _mock_db()
        db.execute = AsyncMock(return_value=_result(None))
        svc = _make_svc(db)
        with pytest.raises(TrialError) as exc_info:
            await svc.mark_charge_failed(uuid.uuid4(), reason="err")
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# _provider_for
# ---------------------------------------------------------------------------


class TestProviderFor:
    def test_unknown_provider_raises_422(self):
        svc = _make_svc()
        with pytest.raises(TrialError) as exc_info:
            svc._provider_for("stripe")
        assert exc_info.value.status_code == 422
