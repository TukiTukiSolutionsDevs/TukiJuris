"""Unit tests for RateLimitGuard factory (Phase 8 — fix-rate-limit-architecture).

Tests the guard behaviour in isolation by mocking rate_limiter.check_rate_limit.
No real Redis, no real DB required.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.deps import RateLimitBucket, RateLimitGuard
from app.core.rate_limiter import READ_LIMIT_PER_MIN, get_write_limit_for_plan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(plan: str = "free", is_admin: bool = False):
    u = MagicMock()
    u.id = "user-test-123"
    u.plan = plan
    u.is_admin = is_admin
    return u


def _allowed(limit: int = 600) -> dict:
    return {
        "allowed": True,
        "limit": limit,
        "remaining": limit - 1,
        "reset_at": int(time.time()) + 60,
    }


def _denied(limit: int = 30) -> dict:
    return {
        "allowed": False,
        "limit": limit,
        "remaining": 0,
        "reset_at": int(time.time()) + 60,
    }


def _make_app(bucket: RateLimitBucket, mock_user) -> FastAPI:
    """Return a minimal FastAPI app with a single guarded GET /test route."""
    from app.api.deps import get_optional_user

    app = FastAPI()
    guard = RateLimitGuard(bucket)

    @app.get("/test")
    async def endpoint(_rl=Depends(guard)):
        return {"ok": True}

    app.dependency_overrides[get_optional_user] = lambda: mock_user
    return app


# ---------------------------------------------------------------------------
# Admin bypass
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_bypass_skips_redis_call():
    """Admin users are passed through without touching Redis, regardless of bucket."""
    admin = _make_user(is_admin=True)
    app = _make_app(RateLimitBucket.WRITE, admin)

    with patch(
        "app.core.rate_limiter.rate_limiter.check_rate_limit",
        new=AsyncMock(),
    ) as mock_rl:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/test")

    assert res.status_code == 200
    mock_rl.assert_not_called()


# ---------------------------------------------------------------------------
# READ bucket — flat limit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_read_bucket_uses_flat_limit():
    """READ bucket always applies READ_LIMIT_PER_MIN (600), regardless of plan."""
    user = _make_user(plan="free")
    app = _make_app(RateLimitBucket.READ, user)

    captured: dict = {}

    async def fake_check(key: str, max_requests: int, window: int) -> dict:
        captured["max_requests"] = max_requests
        return _allowed(limit=max_requests)

    with patch("app.core.rate_limiter.rate_limiter.check_rate_limit", side_effect=fake_check):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/test")

    assert res.status_code == 200
    assert captured["max_requests"] == READ_LIMIT_PER_MIN


# ---------------------------------------------------------------------------
# WRITE bucket — per-plan limits
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("plan", ["free", "pro", "studio"])
async def test_write_bucket_uses_plan_limit(plan: str):
    """WRITE bucket applies the per-plan limit from RATE_LIMIT_TIERS."""
    user = _make_user(plan=plan)
    app = _make_app(RateLimitBucket.WRITE, user)

    expected = get_write_limit_for_plan(plan)
    captured: dict = {}

    async def fake_check(key: str, max_requests: int, window: int) -> dict:
        captured["max_requests"] = max_requests
        return _allowed(limit=max_requests)

    with patch("app.core.rate_limiter.rate_limiter.check_rate_limit", side_effect=fake_check):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/test")

    assert res.status_code == 200
    assert captured["max_requests"] == expected


@pytest.mark.asyncio
async def test_anonymous_write_uses_free_limit():
    """Anonymous users get the 'free' WRITE limit."""
    app = _make_app(RateLimitBucket.WRITE, None)  # None = anonymous

    expected = get_write_limit_for_plan("free")
    captured: dict = {}

    async def fake_check(key: str, max_requests: int, window: int) -> dict:
        captured["max_requests"] = max_requests
        return _allowed(limit=max_requests)

    with patch("app.core.rate_limiter.rate_limiter.check_rate_limit", side_effect=fake_check):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/test")

    assert res.status_code == 200
    assert captured["max_requests"] == expected


# ---------------------------------------------------------------------------
# Key strategy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_authenticated_keyed_by_user_id():
    """Authenticated requests use key ``rl:{bucket}:user:{user_id}``."""
    user = _make_user(plan="free")
    user.id = "user-abc-999"
    app = _make_app(RateLimitBucket.READ, user)

    captured: dict = {}

    async def fake_check(key: str, max_requests: int, window: int) -> dict:
        captured["key"] = key
        return _allowed()

    with patch("app.core.rate_limiter.rate_limiter.check_rate_limit", side_effect=fake_check):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            await ac.get("/test")

    assert captured["key"] == "rl:read:user:user-abc-999"


@pytest.mark.asyncio
async def test_anonymous_keyed_by_ip():
    """Anonymous requests use key ``rl:{bucket}:ip:{client_ip}``."""
    app = _make_app(RateLimitBucket.READ, None)

    captured: dict = {}

    async def fake_check(key: str, max_requests: int, window: int) -> dict:
        captured["key"] = key
        return _allowed()

    with patch("app.core.rate_limiter.rate_limiter.check_rate_limit", side_effect=fake_check):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            await ac.get("/test")

    assert "key" in captured
    assert captured["key"].startswith("rl:read:ip:")


# ---------------------------------------------------------------------------
# 429 response contract
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_exceeded_limit_returns_429():
    """When the limit is exceeded the guard raises HTTP 429."""
    user = _make_user(plan="free")
    app = _make_app(RateLimitBucket.WRITE, user)

    with patch(
        "app.core.rate_limiter.rate_limiter.check_rate_limit",
        new=AsyncMock(return_value=_denied(limit=30)),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/test")

    assert res.status_code == 429


@pytest.mark.asyncio
async def test_429_body_has_required_fields():
    """429 response body includes error, bucket, limit, remaining, reset_at, retry_after."""
    user = _make_user(plan="free")
    app = _make_app(RateLimitBucket.WRITE, user)

    with patch(
        "app.core.rate_limiter.rate_limiter.check_rate_limit",
        new=AsyncMock(return_value=_denied(limit=30)),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/test")

    assert res.status_code == 429
    detail = res.json()["detail"]
    # Spec §5 shape: error_code + bucket + limit + used + retry_after_seconds.
    # reset_at lives in the X-RateLimit-Reset header, not the body.
    assert detail["error_code"] == "rate_limit_exceeded"
    assert detail["bucket"] == "write"
    assert detail["limit"] == 30
    assert detail["used"] == 30  # limit - remaining
    assert "retry_after_seconds" in detail


@pytest.mark.asyncio
async def test_429_response_has_ratelimit_headers():
    """429 response includes X-RateLimit-* and Retry-After headers."""
    user = _make_user(plan="free")
    app = _make_app(RateLimitBucket.WRITE, user)

    with patch(
        "app.core.rate_limiter.rate_limiter.check_rate_limit",
        new=AsyncMock(return_value=_denied(limit=30)),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/test")

    assert "x-ratelimit-limit" in res.headers
    assert res.headers["x-ratelimit-remaining"] == "0"
    assert "x-ratelimit-reset" in res.headers
    assert "retry-after" in res.headers


# ---------------------------------------------------------------------------
# Fail-open semantics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_redis_error_allows_request():
    """When Redis raises an exception the guard fails open (200, no 429)."""
    user = _make_user(plan="free")
    app = _make_app(RateLimitBucket.READ, user)

    async def explode(*args, **kwargs):
        raise ConnectionError("Redis is down")

    with patch("app.core.rate_limiter.rate_limiter.check_rate_limit", side_effect=explode):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/test")

    assert res.status_code == 200


# ---------------------------------------------------------------------------
# RateLimitBucket enum values
# ---------------------------------------------------------------------------


def test_bucket_enum_values():
    assert RateLimitBucket.READ.value == "read"
    assert RateLimitBucket.WRITE.value == "write"


def test_write_limit_fallback_to_free():
    """Unknown plan falls back to the 'free' tier limit."""
    free_limit = get_write_limit_for_plan("free")
    unknown_limit = get_write_limit_for_plan("unknown_plan")
    assert unknown_limit == free_limit
