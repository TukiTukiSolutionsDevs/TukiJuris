"""Integration tests — POST /api/auth/logout-all with Redis denylist.

Covers:
  - AC11: logout-all revokes all active JTIs in DB and writes each to Redis denylist.
  - AC11: Response is 204 (not 200 + JSON body).
  - AC11: Audit log entry written.
  - AC12: /refresh with a denylisted JTI is rejected (fast-path, no DB needed).
  - Cookies cleared on logout-all.

Requirements: live PostgreSQL + Redis (docker-compose up, alembic upgrade head 011).
Skipped automatically if DB or Redis is unreachable.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/integration/test_logout_all.py -v
"""

import uuid

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt as jose_jwt
from redis import asyncio as aioredis

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


async def _redis_connect():
    try:
        r = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        await r.ping()
        return r
    except Exception as exc:
        pytest.skip(f"Redis unreachable: {exc}")


async def _register_and_issue_sessions(
    client: AsyncClient, n_extra: int = 2
) -> tuple[str, str, list[str]]:
    """Register a user, issue n_extra additional refresh tokens by calling /refresh.

    Returns (access_token, email, list_of_jtis).
    """
    email = f"la-{uuid.uuid4().hex[:8]}@test.com"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "LogoutAll1!", "full_name": "LogoutAll Tester"},
    )
    assert res.status_code in (200, 201), f"Register failed: {res.status_code} {res.text}"
    access_token = res.json()["access_token"]

    # Collect JTIs — start with the one from registration
    jtis: list[str] = []
    refresh_cookie = client.cookies.get("refresh_token", "")
    if refresh_cookie:
        payload = jose_jwt.decode(
            refresh_cookie,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": False},
        )
        jtis.append(payload["jti"])

    # Issue n_extra more sessions by calling /refresh
    for _ in range(n_extra):
        res = await client.post("/api/auth/refresh")
        assert res.status_code == 200, f"Refresh failed: {res.status_code}"
        new_access = res.json()["access_token"]
        new_refresh = client.cookies.get("refresh_token", "")
        if new_refresh:
            payload = jose_jwt.decode(
                new_refresh,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
                options={"verify_exp": False},
            )
            jtis.append(payload["jti"])
        access_token = new_access  # keep latest valid access token

    return access_token, email, jtis


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
class TestLogoutAllRedisDenylist:
    """POST /api/auth/logout-all — Redis denylist + audit AC11/AC12."""

    async def test_logout_all_returns_204(self, http_client: AsyncClient):
        """logout-all must return 204 No Content (not 200 with JSON body)."""
        access_token, _, _ = await _register_and_issue_sessions(http_client, n_extra=1)
        res = await http_client.post(
            "/api/auth/logout-all",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert res.status_code == 204, (
            f"Expected 204, got {res.status_code}: {res.text}"
        )

    async def test_logout_all_requires_auth(self, http_client: AsyncClient):
        """logout-all without token must return 401."""
        res = await http_client.post("/api/auth/logout-all")
        assert res.status_code == 401

    async def test_logout_all_revokes_all_jtis_in_db(self, http_client: AsyncClient):
        """AC11: All active JTIs must be marked revoked_at IS NOT NULL in DB."""
        access_token, email, jtis = await _register_and_issue_sessions(http_client, n_extra=2)
        assert len(jtis) >= 1, "Expected at least 1 JTI"

        res = await http_client.post(
            "/api/auth/logout-all",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert res.status_code == 204

        conn = await _db_connect()
        try:
            for jti in jtis:
                revoked_at = await conn.fetchval(
                    "SELECT revoked_at FROM refresh_tokens WHERE jti = $1", jti
                )
                assert revoked_at is not None, f"JTI {jti} not revoked in DB"
        finally:
            await conn.close()

    async def test_logout_all_populates_redis_denylist(self, http_client: AsyncClient):
        """AC11: Each revoked JTI must be present in Redis denylist with a TTL."""
        access_token, email, jtis = await _register_and_issue_sessions(http_client, n_extra=2)
        assert len(jtis) >= 1

        res = await http_client.post(
            "/api/auth/logout-all",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert res.status_code == 204

        redis = await _redis_connect()
        try:
            for jti in jtis:
                key = f"{settings.redis_key_prefix}denylist:{jti}"
                exists = await redis.exists(key)
                assert exists, f"Redis denylist key missing for JTI {jti} (key={key})"
                ttl = await redis.ttl(key)
                assert ttl > 0, f"Redis TTL is {ttl} for JTI {jti} — must be positive"
        finally:
            await redis.aclose()

    async def test_logout_all_refresh_rejected_via_redis_fast_path(
        self, http_client: AsyncClient
    ):
        """AC12: /refresh with a denylisted token must return 401 (Redis fast-path)."""
        access_token, _, _ = await _register_and_issue_sessions(http_client, n_extra=0)
        # Store the current refresh cookie before logout-all
        refresh_before = http_client.cookies.get("refresh_token", "")
        assert refresh_before, "No refresh cookie to test with"

        # logout-all
        res = await http_client.post(
            "/api/auth/logout-all",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert res.status_code == 204

        # Attempt to refresh with the old (now denylisted) cookie
        http_client.cookies.set("refresh_token", refresh_before)
        res = await http_client.post("/api/auth/refresh")
        assert res.status_code == 401, (
            f"Expected 401 for denylisted refresh token, got {res.status_code}"
        )

    async def test_logout_all_clears_cookies(self, http_client: AsyncClient):
        """logout-all must clear both session cookies."""
        access_token, _, _ = await _register_and_issue_sessions(http_client, n_extra=0)
        res = await http_client.post(
            "/api/auth/logout-all",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert res.status_code == 204
        set_cookie_headers = res.headers.get_list("set-cookie")
        refresh_cleared = any("refresh_token" in h for h in set_cookie_headers)
        session_cleared = any("tk_session" in h for h in set_cookie_headers)
        assert refresh_cleared, "refresh_token cookie not cleared"
        assert session_cleared, "tk_session cookie not cleared"

    async def test_logout_all_emits_audit_log(self, http_client: AsyncClient):
        """AC11: auth.logout_all audit entry must be written."""
        access_token, email, _ = await _register_and_issue_sessions(http_client, n_extra=0)

        conn = await _db_connect()
        try:
            user_id = await conn.fetchval("SELECT id FROM users WHERE email = $1", email)
        finally:
            await conn.close()

        res = await http_client.post(
            "/api/auth/logout-all",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert res.status_code == 204

        conn = await _db_connect()
        try:
            audit_row = await conn.fetchrow(
                """
                SELECT action FROM audit_log
                WHERE user_id = $1 AND action = 'auth.logout_all'
                ORDER BY created_at DESC LIMIT 1
                """,
                user_id,
            )
        finally:
            await conn.close()

        assert audit_row is not None, "No audit_log entry for auth.logout_all"
