"""Integration tests — GET /api/auth/me entitlements.

Verifies that the /me endpoint returns the correct plan and entitlements
array for free, pro, and studio users, honouring BETA_MODE.

Requirements:
  - Live PostgreSQL + Redis (docker-compose up)
  - Migration 007 + 008 applied (alembic upgrade head)

Run with:
  cd apps/api && python -m pytest tests/integration/test_me_endpoint.py -v -m integration

Skipped automatically if DB is unreachable.
"""

import uuid
from unittest.mock import patch

import pytest
import pytest_asyncio
import asyncpg
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _db_connect() -> asyncpg.Connection:
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    return await asyncpg.connect(db_url)


async def _register_user(client: AsyncClient) -> tuple[str, str]:
    """Register a unique user. Returns (access_token, email)."""
    email = f"me-{uuid.uuid4().hex[:8]}@test.com"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "TestPass123!", "full_name": "Me Tester"},
    )
    assert res.status_code in (200, 201), f"Register failed: {res.status_code} {res.text}"
    return res.json()["access_token"], email


async def _set_user_plan(email: str, plan: str) -> None:
    """Directly update user plan in DB by email."""
    try:
        conn = await _db_connect()
    except Exception as exc:
        pytest.skip(f"DB unreachable: {exc}")
    try:
        await conn.execute("UPDATE users SET plan = $1 WHERE email = $2", plan, email)
    finally:
        await conn.close()


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.integration
class TestMeEndpointEntitlements:
    """Verify /me returns correct plan and entitlements per user plan."""

    async def test_free_user_gets_chat_only_no_beta(self, http_client: AsyncClient):
        """Free user with BETA_MODE=False gets only chat entitlement."""
        token, email = await _register_user(http_client)
        await _set_user_plan(email, "free")

        with patch.object(settings, "beta_mode", False):
            res = await http_client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["plan"] == "free"
        assert data["entitlements"] == ["chat"]

    async def test_free_user_beta_excludes_byok(self, http_client: AsyncClient):
        """Free user with BETA_MODE=True gets all features EXCEPT byok_enabled."""
        token, email = await _register_user(http_client)
        await _set_user_plan(email, "free")

        with patch.object(settings, "beta_mode", True):
            res = await http_client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["plan"] == "free"
        assert "byok_enabled" not in data["entitlements"]
        assert "chat" in data["entitlements"]

    async def test_pro_user_has_byok_no_team_seats(self, http_client: AsyncClient):
        """Pro user without beta has byok_enabled but not team_seats."""
        token, email = await _register_user(http_client)
        await _set_user_plan(email, "pro")

        with patch.object(settings, "beta_mode", False):
            res = await http_client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["plan"] == "pro"
        assert "byok_enabled" in data["entitlements"]
        assert "team_seats" not in data["entitlements"]

    async def test_studio_user_has_all_features(self, http_client: AsyncClient):
        """Studio user has all feature keys in entitlements."""
        token, email = await _register_user(http_client)
        await _set_user_plan(email, "studio")

        with patch.object(settings, "beta_mode", False):
            res = await http_client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["plan"] == "studio"
        expected_features = {
            "chat",
            "pdf_export",
            "file_upload",
            "byok_enabled",
            "team_seats",
            "priority_support",
        }
        assert expected_features.issubset(set(data["entitlements"])), (
            f"Missing features: {expected_features - set(data['entitlements'])}"
        )

    async def test_me_response_shape(self, http_client: AsyncClient):
        """Response must contain id, email, full_name, plan, entitlements, is_admin."""
        token, _email = await _register_user(http_client)

        res = await http_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert res.status_code == 200
        data = res.json()
        required_keys = {"id", "email", "full_name", "plan", "entitlements", "is_admin"}
        assert required_keys.issubset(data.keys()), (
            f"Missing keys: {required_keys - set(data.keys())}"
        )
        assert isinstance(data["entitlements"], list)

    async def test_unauthenticated_me_returns_401(self, http_client: AsyncClient):
        """GET /me without token must return 401."""
        res = await http_client.get("/api/auth/me")
        assert res.status_code == 401

    async def test_entitlements_are_sorted(self, http_client: AsyncClient):
        """Entitlements list must be sorted (deterministic for frontend caching)."""
        token, email = await _register_user(http_client)
        await _set_user_plan(email, "studio")

        res = await http_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert res.status_code == 200
        entitlements = res.json()["entitlements"]
        assert entitlements == sorted(entitlements), (
            f"Entitlements not sorted: {entitlements}"
        )
