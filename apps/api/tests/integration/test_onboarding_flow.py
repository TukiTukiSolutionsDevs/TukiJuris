"""Integration tests — POST /api/auth/me/onboarding + GET /api/auth/me flag.

Covers:
  - AC6: POST /me/onboarding flips flag to TRUE and returns 204.
  - AC6: Idempotent — calling twice still returns 204, no error.
  - AC6: Requires auth — 401 without token.
  - AC15: /me includes onboarding_completed field after flag flip.
  - Audit log entry is written on first call (not on idempotent repeat).

Requirements: live PostgreSQL + Redis (docker-compose up, alembic upgrade head 011).
Skipped automatically if the DB is unreachable.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/integration/test_onboarding_flow.py -v
"""

import uuid

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _db_connect() -> asyncpg.Connection:
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    try:
        return await asyncpg.connect(db_url)
    except Exception as exc:
        pytest.skip(f"DB unreachable: {exc}")


async def _register(client: AsyncClient) -> tuple[str, str]:
    """Register a unique user. Returns (access_token, email)."""
    email = f"ob-{uuid.uuid4().hex[:8]}@test.com"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "OnboardPass1!", "full_name": "Onboard Tester"},
    )
    assert res.status_code in (200, 201), f"Register failed: {res.status_code} {res.text}"
    return res.json()["access_token"], email


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestMeOnboardingEndpoint:
    """POST /api/auth/me/onboarding acceptance criteria."""

    async def test_me_includes_onboarding_completed_false_for_new_user(
        self, http_client: AsyncClient
    ):
        """GET /me must return onboarding_completed=false for newly registered user."""
        token, _ = await _register(http_client)
        res = await http_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "onboarding_completed" in data, "/me missing onboarding_completed field"
        assert data["onboarding_completed"] is False

    async def test_post_me_onboarding_returns_204(self, http_client: AsyncClient):
        """POST /me/onboarding with valid auth must return 204."""
        token, _ = await _register(http_client)
        res = await http_client.post(
            "/api/auth/me/onboarding",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 204, f"Expected 204, got {res.status_code}: {res.text}"

    async def test_post_me_onboarding_sets_flag_true_in_db(self, http_client: AsyncClient):
        """After POST /me/onboarding, onboarding_completed must be TRUE in DB."""
        token, email = await _register(http_client)

        # Confirm it starts as FALSE
        conn = await _db_connect()
        try:
            before = await conn.fetchval(
                "SELECT onboarding_completed FROM users WHERE email = $1", email
            )
        finally:
            await conn.close()
        assert before is False

        # Call the endpoint
        res = await http_client.post(
            "/api/auth/me/onboarding",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 204

        # Confirm it's now TRUE
        conn = await _db_connect()
        try:
            after = await conn.fetchval(
                "SELECT onboarding_completed FROM users WHERE email = $1", email
            )
        finally:
            await conn.close()
        assert after is True

    async def test_post_me_onboarding_is_idempotent(self, http_client: AsyncClient):
        """Calling POST /me/onboarding twice must return 204 both times (no error)."""
        token, _ = await _register(http_client)

        for _ in range(2):
            res = await http_client.post(
                "/api/auth/me/onboarding",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert res.status_code == 204, (
                f"Idempotent call failed: {res.status_code} {res.text}"
            )

    async def test_post_me_onboarding_requires_auth(self, http_client: AsyncClient):
        """POST /me/onboarding without token must return 401."""
        res = await http_client.post("/api/auth/me/onboarding")
        assert res.status_code == 401

    async def test_me_reflects_completed_flag_after_endpoint_call(
        self, http_client: AsyncClient
    ):
        """GET /me after POST /me/onboarding must return onboarding_completed=true."""
        token, _ = await _register(http_client)

        # Flip the flag
        await http_client.post(
            "/api/auth/me/onboarding",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Fetch /me
        res = await http_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["onboarding_completed"] is True

    async def test_post_me_onboarding_writes_audit_log(self, http_client: AsyncClient):
        """POST /me/onboarding must write an audit_log entry with action=auth.onboarding_completed."""
        token, email = await _register(http_client)

        # Get user_id
        conn = await _db_connect()
        try:
            user_id = await conn.fetchval("SELECT id FROM users WHERE email = $1", email)
        finally:
            await conn.close()

        # Call endpoint
        res = await http_client.post(
            "/api/auth/me/onboarding",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 204

        # Check audit log
        conn = await _db_connect()
        try:
            audit_row = await conn.fetchrow(
                """
                SELECT action, resource_type, resource_id
                FROM audit_log
                WHERE user_id = $1 AND action = 'auth.onboarding_completed'
                ORDER BY created_at DESC LIMIT 1
                """,
                user_id,
            )
        finally:
            await conn.close()

        assert audit_row is not None, "No audit_log entry for auth.onboarding_completed"
        assert audit_row["action"] == "auth.onboarding_completed"

    async def test_post_me_onboarding_idempotent_no_duplicate_audit(
        self, http_client: AsyncClient
    ):
        """Idempotent second call must NOT emit a second audit log entry."""
        token, email = await _register(http_client)

        conn = await _db_connect()
        try:
            user_id = await conn.fetchval("SELECT id FROM users WHERE email = $1", email)
        finally:
            await conn.close()

        # Call twice
        for _ in range(2):
            await http_client.post(
                "/api/auth/me/onboarding",
                headers={"Authorization": f"Bearer {token}"},
            )

        conn = await _db_connect()
        try:
            count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM audit_log
                WHERE user_id = $1 AND action = 'auth.onboarding_completed'
                """,
                user_id,
            )
        finally:
            await conn.close()

        assert count == 1, f"Expected 1 audit entry, got {count} (idempotency broken)"
