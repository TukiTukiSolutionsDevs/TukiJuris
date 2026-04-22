"""Integration tests — refresh token reuse detection (family invalidation).

Covers the reuse detection contract documented in AGENTS.md:
- Rotating a refresh token invalidates the old (gen-0) token.
- Presenting a revoked (rotated-away) token triggers full-family revocation.
- After family kill, even the newest valid token in the family is rejected.
- Passing an access token (type='access') to /refresh is rejected (auth.int.002).

Requirements: live PostgreSQL + Redis (docker-compose up, alembic upgrade head).

Run:
    docker exec tukijuris-api-1 pytest tests/integration/test_auth_refresh_reuse.py -v
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _register(client: AsyncClient) -> tuple[str, str]:
    """Register a fresh user. Returns (access_token, email)."""
    email = f"reuse-{uuid.uuid4().hex[:8]}@test.com"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "ReuseTest1!", "full_name": "Reuse Tester"},
    )
    assert res.status_code in (200, 201), f"Register failed: {res.status_code} {res.text}"
    return res.json()["access_token"], email


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestRefreshTokenReuseDetection:
    """Refresh token reuse detection and family invalidation edge cases."""

    async def test_rotated_token_is_rejected(self, http_client: AsyncClient):
        """After rotation, re-presenting the gen-0 token must return 401.

        Flow: register → capture gen-0 cookie → rotate to gen-1 → present gen-0 → 401.
        """
        await _register(http_client)

        gen0_cookie = http_client.cookies.get("refresh_token", "")
        assert gen0_cookie, "No refresh cookie after register"

        # Rotate: gen-0 → gen-1
        res = await http_client.post("/api/auth/refresh")
        assert res.status_code == 200, f"First rotation failed: {res.status_code}"

        # Present gen-0 again — must be rejected
        http_client.cookies.set("refresh_token", gen0_cookie)
        res = await http_client.post("/api/auth/refresh")
        assert res.status_code == 401, (
            f"Expected 401 for rotated-away token, got {res.status_code}"
        )

    async def test_reuse_detection_kills_entire_family(self, http_client: AsyncClient):
        """Reusing a revoked token triggers family kill; gen-1 is also rejected afterwards.

        Flow: register → gen-0 → rotate to gen-1 → reuse gen-0 (kills family) →
              present gen-1 → 401 (family is dead).
        """
        await _register(http_client)

        gen0_cookie = http_client.cookies.get("refresh_token", "")
        assert gen0_cookie, "No refresh cookie after register"

        # Rotate: gen-0 → gen-1
        res = await http_client.post("/api/auth/refresh")
        assert res.status_code == 200, f"Rotation to gen-1 failed: {res.status_code}"
        gen1_cookie = http_client.cookies.get("refresh_token", "")
        assert gen1_cookie, "No gen-1 refresh cookie"

        # Trigger reuse: present gen-0 → 401 + family killed
        http_client.cookies.set("refresh_token", gen0_cookie)
        res = await http_client.post("/api/auth/refresh")
        assert res.status_code == 401, (
            f"Reuse of gen-0 must return 401, got {res.status_code}"
        )

        # gen-1 should also be dead — entire family was revoked
        http_client.cookies.set("refresh_token", gen1_cookie)
        res = await http_client.post("/api/auth/refresh")
        assert res.status_code == 401, (
            f"gen-1 must be rejected after family kill, got {res.status_code}"
        )

    async def test_valid_rotation_chain_succeeds(self, http_client: AsyncClient):
        """Multiple sequential rotations succeed as long as only the latest token is used.

        Sanity check: reuse detection must NOT break normal usage.
        """
        await _register(http_client)

        for i in range(3):
            res = await http_client.post("/api/auth/refresh")
            assert res.status_code == 200, f"Rotation #{i + 1} failed: {res.status_code}"
            assert "access_token" in res.json(), f"No access_token after rotation #{i + 1}"

    async def test_access_token_type_rejected_at_refresh_endpoint(
        self, http_client: AsyncClient
    ):
        """Presenting an access token (type='access') to /refresh returns 401.

        Spec: auth.int.002 — token type claim is enforced.
        """
        access_token, _ = await _register(http_client)

        # Inject the access JWT as if it were the refresh cookie
        http_client.cookies.set("refresh_token", access_token)
        res = await http_client.post("/api/auth/refresh")
        assert res.status_code == 401, (
            f"Access token must be rejected at /refresh (wrong type), got {res.status_code}"
        )
