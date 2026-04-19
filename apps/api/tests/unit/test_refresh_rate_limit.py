"""T-10.0 RED: Rate limiting on /auth/refresh endpoint.

RED until T-10.1 adds refresh_rate_limit() dependency to rate_limiter.py
and wires it to the /auth/refresh route.

Tests:
  - Dependency raises 429 when per-IP refresh bucket is exhausted.
  - Dependency does not raise when bucket has capacity.
  - Fail-open: no exception propagated when Redis is unavailable.
  - Bucket key is refresh-specific (not the global login/IP key).
  - Limit is exactly 10 req/min (window=60s).
  - Integration: 429 propagated through the full route stack.
  - Does not touch the login rate-limit bucket.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Unit tests — dependency function tested directly (no HTTP stack)
# ---------------------------------------------------------------------------


async def test_refresh_rate_limit_dep_raises_429_when_denied():
    """refresh_rate_limit dependency raises HTTP 429 when bucket is exhausted."""
    from app.core.rate_limiter import refresh_rate_limit, rate_limiter  # RED if not implemented

    mock_request = MagicMock()
    mock_request.client.host = "10.0.0.1"

    with patch.object(
        rate_limiter,
        "check_rate_limit",
        new=AsyncMock(
            return_value={
                "allowed": False,
                "remaining": 0,
                "limit": 10,
                "reset_at": 9_999_999_999,
            }
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await refresh_rate_limit(mock_request)

    assert exc_info.value.status_code == 429


async def test_refresh_rate_limit_dep_does_not_raise_when_allowed():
    """refresh_rate_limit dependency does NOT raise when bucket has capacity."""
    from app.core.rate_limiter import refresh_rate_limit, rate_limiter

    mock_request = MagicMock()
    mock_request.client.host = "10.0.0.2"

    with patch.object(
        rate_limiter,
        "check_rate_limit",
        new=AsyncMock(
            return_value={
                "allowed": True,
                "remaining": 9,
                "limit": 10,
                "reset_at": 9_999_999_999,
            }
        ),
    ):
        await refresh_rate_limit(mock_request)  # must not raise


async def test_refresh_rate_limit_fail_open_on_redis_error():
    """refresh_rate_limit allows the request through when Redis raises (fail-open)."""
    from app.core.rate_limiter import refresh_rate_limit, rate_limiter

    mock_request = MagicMock()
    mock_request.client.host = "10.0.0.3"

    with patch.object(
        rate_limiter,
        "check_rate_limit",
        new=AsyncMock(side_effect=ConnectionError("Redis down")),
    ):
        # Must NOT raise — fail-open: Redis outage must not block refresh
        await refresh_rate_limit(mock_request)


async def test_refresh_rate_limit_uses_refresh_specific_key():
    """refresh_rate_limit calls check_rate_limit with a refresh-specific bucket key."""
    from app.core.rate_limiter import refresh_rate_limit, rate_limiter

    mock_request = MagicMock()
    mock_request.client.host = "10.0.0.4"

    captured_keys: list[str] = []

    async def capture(key: str, max_requests: int, window_seconds: int) -> dict:
        captured_keys.append(key)
        return {"allowed": True, "remaining": 9, "limit": 10, "reset_at": 9_999_999_999}

    with patch.object(rate_limiter, "check_rate_limit", new=capture):
        await refresh_rate_limit(mock_request)

    assert len(captured_keys) == 1, f"Expected exactly 1 rate-limit call, got: {captured_keys}"
    assert "refresh" in captured_keys[0], (
        f"Expected refresh-specific bucket key, got: {captured_keys[0]}"
    )
    # Must NOT be the same as the global anonymous IP bucket
    assert captured_keys[0] != f"ip:{mock_request.client.host}", (
        "refresh_rate_limit must use a separate bucket from the global IP limiter"
    )


async def test_refresh_rate_limit_max_is_ten_per_minute():
    """refresh_rate_limit enforces exactly 10 req/min (window=60s)."""
    from app.core.rate_limiter import refresh_rate_limit, rate_limiter

    mock_request = MagicMock()
    mock_request.client.host = "10.0.0.5"

    captured: list[tuple[int, int]] = []

    async def capture(key: str, max_requests: int, window_seconds: int) -> dict:
        captured.append((max_requests, window_seconds))
        return {"allowed": True, "remaining": 9, "limit": 10, "reset_at": 9_999_999_999}

    with patch.object(rate_limiter, "check_rate_limit", new=capture):
        await refresh_rate_limit(mock_request)

    assert len(captured) == 1
    max_req, window = captured[0]
    assert max_req == 10, f"Expected limit=10, got {max_req}"
    assert window == 60, f"Expected window=60s, got {window}"


async def test_refresh_rate_limit_does_not_touch_login_bucket():
    """refresh_rate_limit must not write to the login rate-limit bucket."""
    from app.core.rate_limiter import refresh_rate_limit, rate_limiter

    mock_request = MagicMock()
    mock_request.client.host = "10.0.0.6"

    captured_keys: list[str] = []

    async def capture(key: str, max_requests: int, window_seconds: int) -> dict:
        captured_keys.append(key)
        return {"allowed": True, "remaining": 9, "limit": 10, "reset_at": 9_999_999_999}

    with patch.object(rate_limiter, "check_rate_limit", new=capture):
        await refresh_rate_limit(mock_request)

    login_key = f"login:ip:{mock_request.client.host}"
    assert login_key not in captured_keys, (
        f"refresh_rate_limit must not touch the login bucket, but found: {captured_keys}"
    )


# ---------------------------------------------------------------------------
# Integration test — 429 propagated through the full ASGI stack
# ---------------------------------------------------------------------------


async def test_refresh_route_returns_429_when_specific_bucket_is_full():
    """POST /auth/refresh → 429 when refresh bucket is full (global bucket still OK).

    Uses a selective mock: global middleware IP bucket is allowed; only the
    refresh-specific bucket ("refresh:ip:...") is denied.
    """
    from httpx import ASGITransport, AsyncClient

    from app.api.deps import get_refresh_service
    from app.core.rate_limiter import rate_limiter
    from app.main import app
    from app.services.refresh_token_service import TokenPair

    fake_pair = TokenPair(access_token="acc", refresh_token="ref")
    svc = AsyncMock()
    svc.rotate.return_value = fake_pair
    app.dependency_overrides[get_refresh_service] = lambda: svc

    async def selective_deny(key: str, max_requests: int, window_seconds: int) -> dict:
        if "refresh:" in key:
            return {"allowed": False, "remaining": 0, "limit": 10, "reset_at": 9_999_999_999}
        return {"allowed": True, "remaining": 9, "limit": 10, "reset_at": 9_999_999_999}

    try:
        with patch.object(rate_limiter, "check_rate_limit", new=selective_deny):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                res = await ac.post(
                    "/api/auth/refresh",
                    cookies={"refresh_token": "old.token.here"},
                )
        assert res.status_code == 429
    finally:
        app.dependency_overrides.pop(get_refresh_service, None)
