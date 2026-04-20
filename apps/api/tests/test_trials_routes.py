"""Tests — trials user-facing routes (TD.1).

All tests mock get_current_user and get_trial_service via app.dependency_overrides
so no real DB is needed.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_trials_routes.py -v
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.api.deps import get_current_user, get_trial_service
from app.models.user import User
from app.services.trial_service import TrialError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(is_admin: bool = False) -> User:
    u = MagicMock(spec=User)
    u.id = uuid.uuid4()
    u.email = "test@test.com"
    u.is_admin = is_admin
    return u


def _make_trial(
    status: str = "active",
    plan_code: str = "pro",
    user_id: uuid.UUID | None = None,
) -> MagicMock:
    t = MagicMock()
    t.id = uuid.uuid4()
    t.user_id = user_id or uuid.uuid4()
    t.plan_code = plan_code
    t.status = status
    t.started_at = datetime.now(UTC)
    t.ends_at = datetime.now(UTC) + timedelta(days=14)
    t.days_remaining = 14
    t.card_added_at = None
    t.provider = None
    t.charged_at = None
    t.charge_failed_at = None
    t.charge_failure_reason = None
    t.retry_count = 0
    t.canceled_at = None
    t.canceled_by_user = False
    t.downgraded_at = None
    t.subscription_id = None
    return t


def _make_svc() -> MagicMock:
    svc = MagicMock()
    svc.get_current = AsyncMock(return_value=None)
    svc.start_trial = AsyncMock()
    svc.add_card = AsyncMock()
    svc.cancel = AsyncMock()
    svc.retry_charge = AsyncMock()
    return svc


def _make_provider_error(code: str = "invalid_token", message: str = "Invalid card token") -> object:
    from app.services.payment_providers.base import ProviderError
    return ProviderError(code=code, message=message)


@pytest_asyncio.fixture
async def client_with_overrides():
    """Client with mocked get_current_user and get_trial_service."""
    user = _make_user()
    svc = _make_svc()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_trial_service] = lambda: svc

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac, user, svc

    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_trial_service, None)


# ---------------------------------------------------------------------------
# GET /api/trials/me  (spec AC22)
# ---------------------------------------------------------------------------


class TestGetCurrentTrial:
    @pytest.mark.asyncio
    async def test_returns_null_when_no_trial(self, client_with_overrides):
        ac, user, svc = client_with_overrides
        svc.get_current.return_value = None

        res = await ac.get("/api/trials/me")

        assert res.status_code == 200
        assert res.json() is None

    @pytest.mark.asyncio
    async def test_returns_trial_when_exists(self, client_with_overrides):
        ac, user, svc = client_with_overrides
        trial = _make_trial(user_id=user.id)
        svc.get_current.return_value = trial

        res = await ac.get("/api/trials/me")

        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "active"
        assert data["plan_code"] == "pro"

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, client):
        res = await client.get("/api/trials/me")
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/trials/start  (spec AC1–AC5)
# ---------------------------------------------------------------------------


class TestStartTrial:
    @pytest.mark.asyncio
    async def test_returns_503_when_trials_disabled(self, client_with_overrides):
        ac, user, svc = client_with_overrides

        with patch("app.api.routes.trials.settings") as mock_settings:
            mock_settings.trials_enabled = False
            res = await ac.post("/api/trials/start", json={"plan_code": "pro"})

        assert res.status_code == 503
        assert res.json()["detail"] == "trials_not_enabled"

    @pytest.mark.asyncio
    async def test_starts_trial_successfully(self, client_with_overrides):
        ac, user, svc = client_with_overrides
        trial = _make_trial(user_id=user.id)
        svc.start_trial.return_value = trial

        with patch("app.api.routes.trials.settings") as mock_settings:
            mock_settings.trials_enabled = True
            res = await ac.post("/api/trials/start", json={"plan_code": "pro"})

        assert res.status_code == 201
        svc.start_trial.assert_called_once_with(user.id, "pro")

    @pytest.mark.asyncio
    async def test_returns_409_when_trial_exists(self, client_with_overrides):
        ac, user, svc = client_with_overrides
        svc.start_trial.side_effect = TrialError(409, "Trial already active for this user")

        with patch("app.api.routes.trials.settings") as mock_settings:
            mock_settings.trials_enabled = True
            res = await ac.post("/api/trials/start", json={"plan_code": "pro"})

        assert res.status_code == 409

    @pytest.mark.asyncio
    async def test_invalid_plan_code_returns_422(self, client_with_overrides):
        ac, user, svc = client_with_overrides

        with patch("app.api.routes.trials.settings") as mock_settings:
            mock_settings.trials_enabled = True
            res = await ac.post("/api/trials/start", json={"plan_code": "free"})

        assert res.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/trials/add-card  (spec AC6–AC9)
# ---------------------------------------------------------------------------

_ADD_CARD_BODY = {
    "provider": "culqi",
    "token_id": "tok_test_abc123",
    "customer_info": {
        "email": "user@test.com",
        "first_name": "Ana",
        "last_name": "Torres",
    },
}


class TestAddCard:
    @pytest.mark.asyncio
    async def test_add_card_success(self, client_with_overrides):
        ac, user, svc = client_with_overrides
        trial = _make_trial(user_id=user.id)
        trial.card_added_at = datetime.now(UTC)
        trial.provider = "culqi"
        svc.get_current.return_value = trial
        svc.add_card.return_value = trial

        with patch("app.api.routes.trials.settings") as mock_settings:
            mock_settings.trials_enabled = True
            res = await ac.post("/api/trials/add-card", json=_ADD_CARD_BODY)

        assert res.status_code == 200
        svc.add_card.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_card_no_active_trial_returns_404(self, client_with_overrides):
        ac, user, svc = client_with_overrides
        svc.get_current.return_value = None

        with patch("app.api.routes.trials.settings") as mock_settings:
            mock_settings.trials_enabled = True
            res = await ac.post("/api/trials/add-card", json=_ADD_CARD_BODY)

        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_add_card_already_added_returns_409(self, client_with_overrides):
        ac, user, svc = client_with_overrides
        trial = _make_trial(user_id=user.id)
        svc.get_current.return_value = trial
        svc.add_card.side_effect = TrialError(409, "Card already added to this trial")

        with patch("app.api.routes.trials.settings") as mock_settings:
            mock_settings.trials_enabled = True
            res = await ac.post("/api/trials/add-card", json=_ADD_CARD_BODY)

        assert res.status_code == 409

    @pytest.mark.asyncio
    async def test_invalid_token_returns_400(self, client_with_overrides):
        """AC8 — invalid payment token must return 400, not 500."""
        ac, user, svc = client_with_overrides
        trial = _make_trial(user_id=user.id)
        svc.get_current.return_value = trial
        svc.add_card.side_effect = TrialError(400, "Invalid card token")

        with patch("app.api.routes.trials.settings") as mock_settings:
            mock_settings.trials_enabled = True
            res = await ac.post("/api/trials/add-card", json=_ADD_CARD_BODY)

        assert res.status_code == 400
        assert "token" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# POST /api/trials/{trial_id}/cancel  (spec AC10–AC12)
# ---------------------------------------------------------------------------


class TestCancelTrial:
    @pytest.mark.asyncio
    async def test_cancel_success(self, client_with_overrides):
        ac, user, svc = client_with_overrides
        trial = _make_trial(status="canceled_pending", user_id=user.id)
        svc.cancel.return_value = trial

        with patch("app.api.routes.trials.settings") as mock_settings:
            mock_settings.trials_enabled = True
            res = await ac.post(f"/api/trials/{trial.id}/cancel")

        assert res.status_code == 200
        assert res.json()["status"] == "canceled_pending"

    @pytest.mark.asyncio
    async def test_cancel_wrong_status_returns_422(self, client_with_overrides):
        ac, user, svc = client_with_overrides
        trial_id = uuid.uuid4()
        svc.cancel.side_effect = TrialError(422, "Cannot cancel trial in status 'charged'")

        with patch("app.api.routes.trials.settings") as mock_settings:
            mock_settings.trials_enabled = True
            res = await ac.post(f"/api/trials/{trial_id}/cancel")

        assert res.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/trials/{trial_id}/retry-charge
# ---------------------------------------------------------------------------


class TestRetryCharge:
    @pytest.mark.asyncio
    async def test_retry_charge_success(self, client_with_overrides):
        ac, user, svc = client_with_overrides
        trial = _make_trial(status="charge_failed", user_id=user.id)
        svc.retry_charge.return_value = trial

        with patch("app.api.routes.trials.settings") as mock_settings:
            mock_settings.trials_enabled = True
            res = await ac.post(f"/api/trials/{trial.id}/retry-charge")

        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_retry_charge_window_closed_returns_422(self, client_with_overrides):
        ac, user, svc = client_with_overrides
        trial_id = uuid.uuid4()
        svc.retry_charge.side_effect = TrialError(422, "Retry window has closed")

        with patch("app.api.routes.trials.settings") as mock_settings:
            mock_settings.trials_enabled = True
            res = await ac.post(f"/api/trials/{trial_id}/retry-charge")

        assert res.status_code == 422
