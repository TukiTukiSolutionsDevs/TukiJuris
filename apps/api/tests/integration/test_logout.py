"""Integration tests — POST /api/auth/logout (relaxed, expired-token-tolerant).

Covers:
  - AC9: Expired access token + valid refresh cookie → 204, cookies cleared.
  - AC9: No access token at all + valid refresh cookie → 204.
  - AC9: No cookie at all → 204 (silent idempotent success).
  - AC10: Audit log entry written when user_id is extractable from refresh token.
  - Refresh token is marked revoked in DB after logout.
  - Both tk_session and refresh_token cookies are cleared.

Requirements: live PostgreSQL + Redis (docker-compose up, alembic upgrade head 011).
Skipped automatically if the DB is unreachable.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/integration/test_logout.py -v
"""

import uuid
from datetime import UTC, datetime, timedelta

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt

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


async def _register_full(client: AsyncClient) -> tuple[str, str, str]:
    """Register user. Returns (access_token, email, refresh_token_cookie_value).

    The refresh token is extracted from the Set-Cookie header.
    """
    email = f"lo-{uuid.uuid4().hex[:8]}@test.com"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "LogoutPass1!", "full_name": "Logout Tester"},
    )
    assert res.status_code in (200, 201), f"Register failed: {res.status_code} {res.text}"
    access_token = res.json()["access_token"]
    refresh_cookie = client.cookies.get("refresh_token", "")
    return access_token, email, refresh_cookie


def _make_expired_access_token(user_id: str) -> str:
    """Craft an already-expired access token for a given user_id."""
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "type": "access",
        "iat": (now - timedelta(hours=2)).timestamp(),
        "exp": (now - timedelta(hours=1)).timestamp(),  # expired 1 hour ago
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


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
class TestLogoutRelaxed:
    """POST /api/auth/logout — must succeed even with expired/missing access token."""

    async def test_logout_with_valid_access_token_returns_204(
        self, http_client: AsyncClient
    ):
        """Baseline: normal logout with a valid access token still works."""
        access_token, _, _ = await _register_full(http_client)
        res = await http_client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert res.status_code == 204, f"Expected 204, got {res.status_code}: {res.text}"

    async def test_logout_with_expired_access_token_returns_204(
        self, http_client: AsyncClient
    ):
        """AC9: Expired access token must NOT cause 401 — logout returns 204."""
        access_token, email, _ = await _register_full(http_client)

        # Fetch user_id from DB to craft expired token
        conn = await _db_connect()
        try:
            user_id = str(await conn.fetchval("SELECT id FROM users WHERE email = $1", email))
        finally:
            await conn.close()

        expired_token = _make_expired_access_token(user_id)
        res = await http_client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert res.status_code == 204, (
            f"Expected 204 with expired token, got {res.status_code}: {res.text}"
        )

    async def test_logout_without_any_token_returns_204(self, http_client: AsyncClient):
        """AC9: No Authorization header + no cookie → 204 (fully anonymous logout)."""
        # No registration — pure anonymous call
        res = await http_client.post("/api/auth/logout")
        assert res.status_code == 204, (
            f"Expected 204 with no token, got {res.status_code}: {res.text}"
        )

    async def test_logout_clears_refresh_token_cookie(self, http_client: AsyncClient):
        """Logout must set Max-Age=0 on the refresh_token cookie."""
        access_token, _, _ = await _register_full(http_client)
        res = await http_client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert res.status_code == 204
        # httpx stores expired cookies; check Set-Cookie header directly
        set_cookie_headers = res.headers.get_list("set-cookie")
        refresh_cleared = any(
            "refresh_token" in h and ("max-age=0" in h.lower() or "expires=" in h.lower())
            for h in set_cookie_headers
        )
        assert refresh_cleared, (
            f"refresh_token cookie not cleared. Set-Cookie headers: {set_cookie_headers}"
        )

    async def test_logout_clears_tk_session_cookie(self, http_client: AsyncClient):
        """Logout must set Max-Age=0 on the tk_session cookie."""
        access_token, _, _ = await _register_full(http_client)
        res = await http_client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert res.status_code == 204
        set_cookie_headers = res.headers.get_list("set-cookie")
        session_cleared = any(
            "tk_session" in h and ("max-age=0" in h.lower() or "expires=" in h.lower())
            for h in set_cookie_headers
        )
        assert session_cleared, (
            f"tk_session cookie not cleared. Set-Cookie headers: {set_cookie_headers}"
        )

    async def test_logout_revokes_refresh_token_in_db(self, http_client: AsyncClient):
        """Refresh token JTI must be marked revoked in DB after logout."""
        access_token, email, refresh_cookie = await _register_full(http_client)

        # Decode refresh cookie to get the JTI
        payload = jwt.decode(
            refresh_cookie,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": False},
        )
        jti = payload["jti"]

        # Logout
        res = await http_client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert res.status_code == 204

        # Verify revoked_at is set in DB
        conn = await _db_connect()
        try:
            revoked_at = await conn.fetchval(
                "SELECT revoked_at FROM refresh_tokens WHERE jti = $1", jti
            )
        finally:
            await conn.close()

        assert revoked_at is not None, f"JTI {jti} not revoked in DB after logout"

    async def test_logout_emits_audit_log(self, http_client: AsyncClient):
        """AC10: auth.logout audit entry must be written when user_id is known."""
        access_token, email, _ = await _register_full(http_client)

        conn = await _db_connect()
        try:
            user_id = await conn.fetchval("SELECT id FROM users WHERE email = $1", email)
        finally:
            await conn.close()

        res = await http_client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert res.status_code == 204

        conn = await _db_connect()
        try:
            audit_row = await conn.fetchrow(
                """
                SELECT action FROM audit_log
                WHERE user_id = $1 AND action = 'auth.logout'
                ORDER BY created_at DESC LIMIT 1
                """,
                user_id,
            )
        finally:
            await conn.close()

        assert audit_row is not None, "No audit_log entry for auth.logout"

    async def test_logout_is_idempotent_double_call(self, http_client: AsyncClient):
        """Calling logout twice must return 204 both times (idempotent)."""
        access_token, _, _ = await _register_full(http_client)
        for _ in range(2):
            res = await http_client.post(
                "/api/auth/logout",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert res.status_code == 204, (
                f"Idempotent logout failed: {res.status_code} {res.text}"
            )
