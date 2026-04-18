"""Unit route tests for refresh token endpoints (T-9.0 RED).

All tests in this file are RED until T-9.1 implements the route handlers:
  - /auth/refresh, /auth/logout, /auth/logout-all, /auth/sessions → 404 (don't exist yet)

Will be GREEN after T-9.1.

Uses FastAPI dependency_overrides to avoid real DB/Redis connections.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import (
    ExpiredRefreshToken,
    InvalidRefreshToken,
    ReuseDetected,
    RevokedRefreshToken,
)
from app.main import app
from app.services.refresh_token_service import SessionDTO, TokenPair

# ---------------------------------------------------------------------------
# Shared mock constants
# ---------------------------------------------------------------------------

FAKE_ACCESS = "eyJhbGciOiJIUzI1NiJ9.fake.access"
FAKE_REFRESH = "eyJhbGciOiJIUzI1NiJ9.fake.refresh"
FAKE_PAIR = TokenPair(access_token=FAKE_ACCESS, refresh_token=FAKE_REFRESH)

MOCK_USER_ID = uuid.uuid4()


class _MockUser:
    id = MOCK_USER_ID
    email = "user@test.com"
    full_name = "Test User"
    is_active = True
    plan = "free"
    hashed_password = "hashed"
    is_admin = False
    auth_provider = "email"
    avatar_url = None
    default_org_id = None
    created_at = datetime.now(UTC)


MOCK_USER = _MockUser()


def _make_service(pair: TokenPair = FAKE_PAIR, sessions: list | None = None) -> AsyncMock:
    svc = AsyncMock()
    svc.issue_pair.return_value = pair
    svc.rotate.return_value = pair
    svc.revoke.return_value = None
    svc.revoke_all.return_value = 2
    svc.list_sessions.return_value = sessions if sessions is not None else [
        SessionDTO(
            jti=str(uuid.uuid4()),
            family_id=str(uuid.uuid4()),
            created_at=datetime.now(UTC) - timedelta(hours=2),
            expires_at=datetime.now(UTC) + timedelta(days=29),
        )
    ]
    return svc


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def rf_client():
    """Client with get_refresh_service + get_current_user overridden (no DB/Redis)."""
    from app.api.deps import get_current_user, get_refresh_service

    svc = _make_service()
    app.dependency_overrides[get_refresh_service] = lambda: svc
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac, svc

    app.dependency_overrides.pop(get_refresh_service, None)
    app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# POST /api/auth/refresh
# ---------------------------------------------------------------------------


async def test_refresh_happy_path(rf_client):
    """POST /auth/refresh with valid token → 200 {access_token, refresh_token, token_type}."""
    ac, svc = rf_client
    res = await ac.post(
        "/api/auth/refresh",
        json={"refresh_token": FAKE_REFRESH},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["access_token"] == FAKE_ACCESS
    assert data["refresh_token"] == FAKE_REFRESH
    assert data["token_type"] == "bearer"
    svc.rotate.assert_awaited_once()


async def test_refresh_missing_body_returns_422():
    """POST /auth/refresh with empty body → 422 (missing refresh_token field)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.post("/api/auth/refresh", json={})
    assert res.status_code == 422


@pytest.mark.parametrize(
    "exc_class,error_code",
    [
        (InvalidRefreshToken, "invalid_refresh_token"),
        (ExpiredRefreshToken, "expired_refresh_token"),
        (RevokedRefreshToken, "revoked_refresh_token"),
        (ReuseDetected, "reuse_detected"),
    ],
)
async def test_refresh_auth_errors_return_401_with_error_code(exc_class, error_code):
    """POST /auth/refresh with bad token → 401 {detail, error_code}."""
    from app.api.deps import get_current_user, get_refresh_service

    svc = AsyncMock()
    svc.rotate.side_effect = exc_class()
    app.dependency_overrides[get_refresh_service] = lambda: svc
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            res = await ac.post(
                "/api/auth/refresh",
                json={"refresh_token": FAKE_REFRESH},
            )
        assert res.status_code == 401
        body = res.json()
        assert "detail" in body
        assert body.get("error_code") == error_code
    finally:
        app.dependency_overrides.pop(get_refresh_service, None)
        app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# POST /api/auth/logout
# ---------------------------------------------------------------------------


async def test_logout_returns_204(rf_client):
    """POST /auth/logout with refresh_token → 204 No Content."""
    ac, svc = rf_client
    res = await ac.post(
        "/api/auth/logout",
        json={"refresh_token": FAKE_REFRESH},
    )
    assert res.status_code == 204
    svc.revoke.assert_awaited_once_with(FAKE_REFRESH)


async def test_logout_without_token_still_returns_204(rf_client):
    """POST /auth/logout without refresh_token → 204 (idempotent)."""
    ac, svc = rf_client
    res = await ac.post("/api/auth/logout", json={})
    assert res.status_code == 204


async def test_logout_requires_auth():
    """POST /auth/logout without Bearer → 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.post(
            "/api/auth/logout",
            json={"refresh_token": FAKE_REFRESH},
        )
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/auth/logout-all
# ---------------------------------------------------------------------------


async def test_logout_all_returns_revoked_count(rf_client):
    """POST /auth/logout-all → 200 {revoked: N}."""
    ac, svc = rf_client
    svc.revoke_all.return_value = 3
    res = await ac.post("/api/auth/logout-all")
    assert res.status_code == 200
    body = res.json()
    assert body["revoked"] == 3
    svc.revoke_all.assert_awaited_once_with(MOCK_USER.id)


async def test_logout_all_requires_auth():
    """POST /auth/logout-all without Bearer → 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.post("/api/auth/logout-all")
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/auth/sessions
# ---------------------------------------------------------------------------


async def test_sessions_returns_session_list(rf_client):
    """GET /auth/sessions → 200 [{jti, family_id, created_at, expires_at}]."""
    ac, svc = rf_client
    res = await ac.get("/api/auth/sessions")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 1
    session = data[0]
    assert "jti" in session
    assert "family_id" in session
    assert "created_at" in session
    assert "expires_at" in session
    svc.list_sessions.assert_awaited_once_with(MOCK_USER.id)


async def test_sessions_empty_list(rf_client):
    """GET /auth/sessions with no active sessions → 200 []."""
    ac, svc = rf_client
    svc.list_sessions.return_value = []
    res = await ac.get("/api/auth/sessions")
    assert res.status_code == 200
    assert res.json() == []


async def test_sessions_requires_auth():
    """GET /auth/sessions without Bearer → 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.get("/api/auth/sessions")
    assert res.status_code == 401
