"""Unit route tests for refresh token endpoints — cookie-based contract.

Covers:
  - POST /auth/refresh  — reads refresh_token from Cookie, returns access token only.
  - POST /auth/logout   — reads refresh_token from Cookie, clears both session cookies.
  - POST /auth/logout-all
  - GET  /auth/sessions

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
    from unittest.mock import AsyncMock, MagicMock

    from app.api.deps import get_audit_service, get_current_user, get_denylist, get_refresh_service

    svc = _make_service()
    # Stub audit service so FK violations against test-only user IDs don't poison the session
    audit_stub = AsyncMock()
    # Stub denylist so Redis is not required for unit tests
    denylist_stub = MagicMock()
    denylist_stub.add = AsyncMock()

    app.dependency_overrides[get_refresh_service] = lambda: svc
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    app.dependency_overrides[get_audit_service] = lambda: audit_stub
    app.dependency_overrides[get_denylist] = lambda: denylist_stub

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac, svc

    app.dependency_overrides.pop(get_refresh_service, None)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_audit_service, None)
    app.dependency_overrides.pop(get_denylist, None)


# ---------------------------------------------------------------------------
# POST /api/auth/refresh — cookie-based contract
# ---------------------------------------------------------------------------


async def test_refresh_happy_path(rf_client):
    """POST /auth/refresh with cookie → 200 {access_token, token_type}, no refresh_token in body."""
    ac, svc = rf_client
    res = await ac.post(
        "/api/auth/refresh",
        cookies={"refresh_token": FAKE_REFRESH},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["access_token"] == FAKE_ACCESS
    assert data["token_type"] == "bearer"
    assert "refresh_token" not in data, "refresh_token must NOT appear in JSON body"
    svc.rotate.assert_awaited_once()


async def test_refresh_sets_both_cookies_on_success(rf_client):
    """Successful refresh sets refresh_token and tk_session cookies."""
    ac, svc = rf_client
    res = await ac.post(
        "/api/auth/refresh",
        cookies={"refresh_token": FAKE_REFRESH},
    )
    assert res.status_code == 200
    set_cookie_headers = res.headers.get_list("set-cookie") if hasattr(res.headers, "get_list") else [
        v for k, v in res.headers.items() if k.lower() == "set-cookie"
    ]
    cookie_names = [h.split("=")[0].strip() for h in set_cookie_headers]
    assert "refresh_token" in cookie_names, "refresh_token cookie must be set on success"
    assert "tk_session" in cookie_names, "tk_session cookie must be set on success"


async def test_refresh_missing_cookie_returns_401():
    """POST /auth/refresh without cookie → 401 missing_refresh_token."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.post("/api/auth/refresh")
    assert res.status_code == 401
    assert res.json().get("error_code") == "missing_refresh_token"


async def test_refresh_clears_cookies_on_missing_token():
    """POST /auth/refresh without cookie → response expires both session cookies."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.post("/api/auth/refresh")
    set_cookie = " ".join(
        v for k, v in res.headers.items() if k.lower() == "set-cookie"
    )
    assert "Max-Age=0" in set_cookie or "max-age=0" in set_cookie.lower()


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
    """POST /auth/refresh with bad cookie → 401 {detail, error_code} + cookies cleared."""
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
                cookies={"refresh_token": FAKE_REFRESH},
            )
        assert res.status_code == 401
        body = res.json()
        assert "detail" in body
        assert body.get("error_code") == error_code
        # Cookies must be cleared on auth failure
        set_cookie = " ".join(
            v for k, v in res.headers.items() if k.lower() == "set-cookie"
        )
        assert "Max-Age=0" in set_cookie or "max-age=0" in set_cookie.lower()
    finally:
        app.dependency_overrides.pop(get_refresh_service, None)
        app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# POST /api/auth/logout — cookie-based contract
# ---------------------------------------------------------------------------


async def test_logout_returns_204(rf_client):
    """POST /auth/logout with cookie → 204 No Content, token revoked."""
    ac, svc = rf_client
    res = await ac.post(
        "/api/auth/logout",
        cookies={"refresh_token": FAKE_REFRESH},
    )
    assert res.status_code == 204
    svc.revoke.assert_awaited_once_with(FAKE_REFRESH)


async def test_logout_clears_both_cookies(rf_client):
    """POST /auth/logout → both refresh_token and tk_session cookies are expired."""
    ac, svc = rf_client
    res = await ac.post(
        "/api/auth/logout",
        cookies={"refresh_token": FAKE_REFRESH},
    )
    assert res.status_code == 204
    set_cookie = " ".join(
        v for k, v in res.headers.items() if k.lower() == "set-cookie"
    )
    assert "Max-Age=0" in set_cookie or "max-age=0" in set_cookie.lower()


async def test_logout_without_cookie_still_returns_204(rf_client):
    """POST /auth/logout without cookie → 204 (idempotent, no revoke call)."""
    ac, svc = rf_client
    res = await ac.post("/api/auth/logout")
    assert res.status_code == 204
    svc.revoke.assert_not_awaited()


async def test_logout_without_bearer_returns_204():
    """POST /auth/logout without Bearer → 204 (graceful, no revoke call).

    Design change (fix-session-flow): logout is now intentionally unauthenticated.
    A missing/invalid cookie results in a no-op 204 rather than 401, so clients
    can always clear their local state even after token expiry.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.post("/api/auth/logout")
    assert res.status_code == 204


# ---------------------------------------------------------------------------
# POST /api/auth/logout-all
# ---------------------------------------------------------------------------


async def test_logout_all_returns_204(rf_client):
    """POST /auth/logout-all → 204 No Content (all sessions revoked).

    Design change (fix-session-flow): logout-all now returns 204 instead of
    200 + JSON body, consistent with the single-device logout endpoint.
    """
    ac, svc = rf_client
    svc.revoke_all.return_value = 3
    res = await ac.post("/api/auth/logout-all")
    assert res.status_code == 204
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
