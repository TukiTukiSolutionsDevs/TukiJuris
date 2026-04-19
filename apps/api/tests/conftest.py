"""
Test configuration and shared fixtures for Agente Derecho API.

All tests are integration tests that exercise the real FastAPI app via
ASGITransport (no real HTTP server needed). Tests that touch the database
require PostgreSQL to be running — they will gracefully fail with a clear
error if the DB is not available, rather than silently passing.
"""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


# ---------------------------------------------------------------------------
# Redis rate-limit bucket reset (autouse)
#
# Many tests hit rate-limited endpoints (e.g. /api/auth/refresh at 10/60s per IP).
# Without flushing the Redis bucket between tests, later tests in the same
# session fail with 429. This fixture clears every `tukijuris:ratelimit:*`
# key before each test. Fail-open: if Redis is unreachable, the fixture is a no-op.
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def _reset_rate_limit_buckets():
    """Flush Redis rate-limit keys before each test to keep tests independent.

    Reuses the app's own `rate_limiter` singleton so we hit the exact same
    Redis DB/connection the production code uses. Key pattern is `ratelimit:*`
    — see app/core/rate_limiter.py line 60.
    """
    try:
        from app.core.rate_limiter import rate_limiter

        r = await rate_limiter._get_redis()
        async for key in r.scan_iter(match="ratelimit:*"):
            await r.delete(key)
    except Exception:
        # Redis unavailable — fine for pure-unit tests that don't touch it.
        pass
    yield


# ---------------------------------------------------------------------------
# Event loop — single loop for the entire session (avoids loop-reuse errors)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop():
    """Provide a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# HTTP clients
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Unauthenticated async HTTP client wired to the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    """
    Authenticated client.

    Registers a unique test user on each test run and sets the
    Authorization header so subsequent requests are authenticated.
    Falls back to login if the email already exists (409).
    """
    email = f"test-{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPassword123!"

    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    if res.status_code == 409:
        res = await client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )

    data = res.json()
    assert "access_token" in data, f"Auth setup failed: {res.status_code} {data}"
    client.headers["Authorization"] = f"Bearer {data['access_token']}"
    return client


# ---------------------------------------------------------------------------
# Refresh token fixtures — G6 (T-6.0 + T-6.1)
# ---------------------------------------------------------------------------


@pytest.fixture
def test_family() -> str:
    """A fresh family_id UUID string per test."""
    return str(uuid.uuid4())


@pytest.fixture
def refresh_token_factory():
    """Factory that builds in-memory RefreshToken instances (not persisted)."""
    from app.models.refresh_token import RefreshToken

    def factory(
        user_id: uuid.UUID | None = None,
        family_id: str | None = None,
        token_hash: str | None = None,
        revoked_at: datetime | None = None,
        expires_at: datetime | None = None,
    ) -> RefreshToken:
        now = datetime.now(UTC)
        return RefreshToken(
            id=uuid.uuid4(),
            jti=str(uuid.uuid4()),
            user_id=user_id or uuid.uuid4(),
            family_id=family_id or str(uuid.uuid4()),
            token_hash=token_hash or "a" * 64,
            expires_at=expires_at or now + timedelta(days=30),
            revoked_at=revoked_at,
            created_at=now,
        )

    return factory


@pytest.fixture
def expired_refresh_token(refresh_token_factory):
    """A RefreshToken whose expires_at is in the past."""
    past = datetime.now(UTC) - timedelta(days=1)
    return refresh_token_factory(expires_at=past)


@pytest.fixture
def revoked_refresh_token(refresh_token_factory):
    """A RefreshToken with revoked_at set."""
    return refresh_token_factory(revoked_at=datetime.now(UTC))


@pytest.fixture
def redis_denylist():
    """TokenDenylist backed by an AsyncMock Redis — no real Redis required."""
    from app.core.token_denylist import TokenDenylist

    mock_redis = AsyncMock()
    mock_redis.exists.return_value = 0
    return TokenDenylist(mock_redis, prefix="test:deny:")


@pytest_asyncio.fixture
async def auth_client_with_pair(client: AsyncClient):
    """Authenticated client yielding (client, access_token, refresh_token | None).

    Forward-compatible: refresh_token is None until G9 wires the login endpoint
    to return a pair. Once it does, this fixture exposes it automatically.
    Does NOT replace auth_client — existing tests are unaffected.
    """
    email = f"test-{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPassword123!"

    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    if res.status_code == 409:
        res = await client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )

    data = res.json()
    assert "access_token" in data, f"Auth setup failed: {res.status_code} {data}"
    access_token = data["access_token"]
    refresh_token = data.get("refresh_token")  # None until G9 is implemented

    client.headers["Authorization"] = f"Bearer {access_token}"
    yield client, access_token, refresh_token
