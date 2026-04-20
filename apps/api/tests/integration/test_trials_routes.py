"""Integration tests — trials route feature-flag guard (billing.int.002).

Verifies POST /api/trials/{trial_id}/retry-charge returns 503 when
TRIALS_ENABLED=False (the default in non-prod environments).

Requirements: live PostgreSQL + Redis (docker-compose up).

Run:
    docker exec tukijuris-api-1 pytest tests/integration/test_trials_routes.py -v
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _register(client: AsyncClient) -> str:
    """Register a unique user and return its access token."""
    email = f"trials-{uuid.uuid4().hex[:8]}@test.com"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "TestPass123!", "full_name": "Trials Tester"},
    )
    assert res.status_code in (200, 201), f"Register failed: {res.status_code} {res.text}"
    return res.json()["access_token"]


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


# ---------------------------------------------------------------------------
# billing.int.002 — retry-charge disabled when TRIALS_ENABLED=False
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestTrialsRetryChargeDisabled:
    """billing.int.002 — retry-charge returns 503 when TRIALS_ENABLED=False."""

    async def test_retry_charge_returns_503_when_trials_disabled(self, http_client: AsyncClient):
        """
        Default config has trials_enabled=False.
        POST /api/trials/{any_id}/retry-charge must return 503.
        """
        token = await _register(http_client)
        fake_trial_id = str(uuid.uuid4())

        res = await http_client.post(
            f"/api/trials/{fake_trial_id}/retry-charge",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 503, (
            f"Expected 503 (trials disabled), got {res.status_code}: {res.text}"
        )

    async def test_retry_charge_unauthenticated_returns_401_or_503(self, http_client: AsyncClient):
        """
        Without a token, auth check fires before the trials guard.
        Accept either 401 (auth rejected) or 503 (guard fires first).
        """
        fake_trial_id = str(uuid.uuid4())
        res = await http_client.post(f"/api/trials/{fake_trial_id}/retry-charge")
        assert res.status_code in (401, 503), (
            f"Expected 401 or 503, got {res.status_code}: {res.text}"
        )
