"""Integration tests — POST /api/auth/logout-all (complementary edge cases).

Complements tests/integration/test_logout_all.py which covers the primary
AC11/AC12 contract (204, DB revoke, Redis denylist, audit log, cookies cleared).

This file covers edge cases NOT present in the primary file:
- Idempotent: calling logout-all twice returns 204 on both calls.
- Cross-user isolation: logout-all for user A does NOT revoke user B's sessions.

Requirements: live PostgreSQL + Redis (docker-compose up, alembic upgrade head).

Run:
    docker exec tukijuris-api-1 pytest tests/integration/test_auth_logout_all.py -v
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


async def _register(client: AsyncClient, suffix: str = "") -> tuple[str, str]:
    """Register a fresh user. Returns (access_token, email)."""
    tag = suffix or uuid.uuid4().hex[:8]
    email = f"la2-{tag}@test.com"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "LogoutAll2!", "full_name": "LA2 Tester"},
    )
    assert res.status_code in (200, 201), f"Register failed: {res.status_code} {res.text}"
    return res.json()["access_token"], email


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestLogoutAllEdgeCases:
    """Complementary edge-case coverage for POST /api/auth/logout-all."""

    async def test_logout_all_is_idempotent(self, http_client: AsyncClient):
        """Calling logout-all twice in a row returns 204 on both calls.

        After the first call there are no active sessions. The second call
        must not crash (empty revoke set is a valid no-op).
        """
        access_token, _ = await _register(http_client)

        # First call — revokes the active session
        res1 = await http_client.post(
            "/api/auth/logout-all",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert res1.status_code == 204, f"First logout-all returned {res1.status_code}"

        # Second call — no active sessions remain; must still return 204
        res2 = await http_client.post(
            "/api/auth/logout-all",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert res2.status_code == 204, (
            f"Second logout-all (idempotent, 0 sessions) returned {res2.status_code}"
        )

    async def test_logout_all_does_not_affect_other_user_sessions(
        self, http_client: AsyncClient
    ):
        """User A's logout-all must NOT revoke user B's refresh tokens.

        Uses two independent AsyncClient instances to prevent cookie cross-pollution.
        User B's /refresh must succeed after user A performs logout-all.
        """
        # Register user A on the shared client
        token_a, _ = await _register(http_client, suffix=f"a{uuid.uuid4().hex[:6]}")

        # Register user B on a completely separate client
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client_b:
            token_b, _ = await _register(client_b, suffix=f"b{uuid.uuid4().hex[:6]}")
            refresh_b_before = client_b.cookies.get("refresh_token", "")
            assert refresh_b_before, "User B must have a refresh cookie"

            # User A performs logout-all
            res = await http_client.post(
                "/api/auth/logout-all",
                headers={"Authorization": f"Bearer {token_a}"},
            )
            assert res.status_code == 204

            # User B's refresh token must still be valid
            res_b = await client_b.post("/api/auth/refresh")
            assert res_b.status_code == 200, (
                f"User B's session was affected by user A's logout-all "
                f"(got {res_b.status_code})"
            )
            assert "access_token" in res_b.json()
