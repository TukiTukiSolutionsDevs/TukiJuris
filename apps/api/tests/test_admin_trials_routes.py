"""Tests — admin trial management routes (TD.2).

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_admin_trials_routes.py -v
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from fastapi import HTTPException
from app.api.deps import get_trial_service, require_admin
from app.api.routes.admin_trials import _billing_read, _billing_update
from app.services.trial_service import TrialError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_admin_user() -> MagicMock:
    u = MagicMock()
    u.id = uuid.uuid4()
    u.is_admin = True
    u.email = "admin@test.com"
    return u


def _make_regular_user() -> MagicMock:
    u = MagicMock()
    u.id = uuid.uuid4()
    u.is_admin = False
    u.email = "user@test.com"
    return u


def _make_trial(status: str = "active", plan_code: str = "pro") -> MagicMock:
    t = MagicMock()
    t.id = uuid.uuid4()
    t.user_id = uuid.uuid4()
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
    svc.admin_list = AsyncMock(return_value=([], 0))
    svc.admin_patch = AsyncMock()
    return svc


@pytest_asyncio.fixture
async def admin_client():
    """Client with admin user and mocked trial service."""
    user = _make_admin_user()
    svc = _make_svc()

    app.dependency_overrides[_billing_read] = lambda: user
    app.dependency_overrides[_billing_update] = lambda: user
    app.dependency_overrides[require_admin] = lambda: user
    app.dependency_overrides[get_trial_service] = lambda: svc

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac, user, svc

    app.dependency_overrides.pop(_billing_read, None)
    app.dependency_overrides.pop(_billing_update, None)
    app.dependency_overrides.pop(require_admin, None)
    app.dependency_overrides.pop(get_trial_service, None)


@pytest_asyncio.fixture
async def non_admin_client():
    """Client with non-admin user and mocked trial service."""
    user = _make_regular_user()
    svc = _make_svc()

    def _raise_admin_required():
        raise HTTPException(status_code=403, detail="admin_required")

    app.dependency_overrides[_billing_read] = lambda: user
    app.dependency_overrides[_billing_update] = lambda: user
    app.dependency_overrides[require_admin] = _raise_admin_required
    app.dependency_overrides[get_trial_service] = lambda: svc

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac, user, svc

    app.dependency_overrides.pop(_billing_read, None)
    app.dependency_overrides.pop(_billing_update, None)
    app.dependency_overrides.pop(require_admin, None)
    app.dependency_overrides.pop(get_trial_service, None)


# ---------------------------------------------------------------------------
# GET /api/admin/trials
# ---------------------------------------------------------------------------


class TestListTrialsAdmin:
    @pytest.mark.asyncio
    async def test_non_admin_returns_403(self, non_admin_client):
        ac, user, svc = non_admin_client

        res = await ac.get("/api/admin/trials")

        assert res.status_code == 403
        assert res.json()["detail"] == "admin_required"

    @pytest.mark.asyncio
    async def test_empty_list_returns_paginated_response(self, admin_client):
        ac, user, svc = admin_client
        svc.admin_list.return_value = ([], 0)

        res = await ac.get("/api/admin/trials")

        assert res.status_code == 200
        data = res.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 20

    @pytest.mark.asyncio
    async def test_returns_trials_with_filters(self, admin_client):
        ac, user, svc = admin_client
        trials = [_make_trial(status="active"), _make_trial(status="active")]
        svc.admin_list.return_value = (trials, 2)

        res = await ac.get("/api/admin/trials?status=active&plan_code=pro&page=1&per_page=10")

        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

        # Verify filters were passed to service
        call_args = svc.admin_list.call_args[0][0]
        assert call_args.status == "active"
        assert call_args.plan_code == "pro"
        assert call_args.per_page == 10

    @pytest.mark.asyncio
    async def test_expiring_in_days_filter(self, admin_client):
        ac, user, svc = admin_client
        svc.admin_list.return_value = ([], 0)

        res = await ac.get("/api/admin/trials?expiring_in_days=3")

        assert res.status_code == 200
        call_args = svc.admin_list.call_args[0][0]
        assert call_args.expiring_in_days == 3


# ---------------------------------------------------------------------------
# PATCH /api/admin/trials/{trial_id}
# ---------------------------------------------------------------------------


class TestPatchTrialAdmin:
    @pytest.mark.asyncio
    async def test_non_admin_returns_403(self, non_admin_client):
        ac, user, svc = non_admin_client
        trial_id = uuid.uuid4()

        res = await ac.patch(
            f"/api/admin/trials/{trial_id}",
            json={"action": "force_downgrade", "reason": "test reason"},
        )

        assert res.status_code == 403

    @pytest.mark.asyncio
    async def test_force_downgrade_success(self, admin_client):
        ac, user, svc = admin_client
        trial = _make_trial(status="downgraded")
        svc.admin_patch.return_value = trial

        res = await ac.patch(
            f"/api/admin/trials/{trial.id}",
            json={"action": "force_downgrade", "reason": "No card added after 3 days"},
        )

        assert res.status_code == 200
        assert res.json()["status"] == "downgraded"
        svc.admin_patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_extend_days_success(self, admin_client):
        ac, user, svc = admin_client
        trial = _make_trial()
        svc.admin_patch.return_value = trial

        res = await ac.patch(
            f"/api/admin/trials/{trial.id}",
            json={"action": "extend_days", "extend_days": 7, "reason": "Support exception"},
        )

        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_unknown_action_returns_422(self, admin_client):
        ac, user, svc = admin_client
        trial_id = uuid.uuid4()

        res = await ac.patch(
            f"/api/admin/trials/{trial_id}",
            json={"action": "unknown_action", "reason": "test reason"},
        )

        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_reason_too_short_returns_422(self, admin_client):
        ac, user, svc = admin_client
        trial_id = uuid.uuid4()

        res = await ac.patch(
            f"/api/admin/trials/{trial_id}",
            json={"action": "force_downgrade", "reason": "x"},
        )

        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_trial_not_found_returns_404(self, admin_client):
        ac, user, svc = admin_client
        trial_id = uuid.uuid4()
        svc.admin_patch.side_effect = TrialError(404, "Trial not found")

        res = await ac.patch(
            f"/api/admin/trials/{trial_id}",
            json={"action": "force_cancel", "reason": "Administrative action"},
        )

        assert res.status_code == 404
