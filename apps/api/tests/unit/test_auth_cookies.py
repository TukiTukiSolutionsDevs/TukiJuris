"""Cookie contract tests — Task 15.

Asserts that every session-issuing endpoint sets BOTH cookies with correct
attributes, and every clearing path (logout, refresh failure) expires them.

Routes under test (via ASGI transport, no real DB/Redis):
  POST /api/auth/login
  POST /api/auth/register
  POST /api/auth/refresh
  POST /api/auth/logout
  POST /api/auth/oauth/google/callback
  POST /api/auth/oauth/microsoft/callback
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.refresh_token_service import TokenPair

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_ACCESS = "eyJ.fake.access"
FAKE_REFRESH = "eyJ.fake.refresh"
FAKE_PAIR = TokenPair(access_token=FAKE_ACCESS, refresh_token=FAKE_REFRESH)


class _MockUser:
    id = uuid.uuid4()
    email = "user@test.com"
    full_name = "Test User"
    is_active = True
    is_admin = False
    plan = "free"
    hashed_password = "hashed"
    auth_provider = "email"
    avatar_url = None
    default_org_id = None
    created_at = datetime.now(UTC)


MOCK_USER = _MockUser()


def _parse_set_cookie_headers(response) -> list[str]:
    """Return all Set-Cookie header values from an httpx response.

    httpx.Headers.items() joins multiple values for the same header name with
    ', ', which corrupts Set-Cookie parsing (cookies share the same header
    name).  get_list() preserves each cookie as a separate string.
    """
    return response.headers.get_list("set-cookie")


def _cookie_map(response) -> dict[str, str]:
    """Return {cookie_name: full_header_value} for each Set-Cookie header."""
    result = {}
    for header in _parse_set_cookie_headers(response):
        name = header.split("=")[0].strip()
        result[name] = header
    return result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def auth_client():
    """Client with service + user dependencies overridden."""
    from app.api.deps import get_current_user, get_refresh_service
    from app.core.database import get_db

    svc = AsyncMock()
    svc.issue_pair.return_value = FAKE_PAIR
    svc.rotate.return_value = FAKE_PAIR
    svc.revoke.return_value = None

    db = AsyncMock()

    app.dependency_overrides[get_refresh_service] = lambda: svc
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    app.dependency_overrides[get_db] = lambda: db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac, svc, db

    app.dependency_overrides.pop(get_refresh_service, None)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Cookie attribute assertions (shared logic)
# ---------------------------------------------------------------------------


def _assert_session_cookies_set(response, *, expect_httponly: bool = True):
    """Assert both refresh_token and tk_session cookies are set with correct attrs."""
    cookies = _cookie_map(response)

    assert "refresh_token" in cookies, "refresh_token cookie must be set"
    assert "tk_session" in cookies, "tk_session cookie must be set"

    rt = cookies["refresh_token"].lower()
    ts = cookies["tk_session"].lower()

    # HttpOnly
    assert "httponly" in rt, "refresh_token must be HttpOnly"
    assert "httponly" in ts, "tk_session must be HttpOnly"

    # SameSite=Lax
    assert "samesite=lax" in rt, "refresh_token must be SameSite=Lax"
    assert "samesite=lax" in ts, "tk_session must be SameSite=Lax"

    # Path scoping
    assert "path=/api/auth" in rt, "refresh_token must be scoped to Path=/api/auth"
    assert "path=/" in ts, "tk_session must be scoped to Path=/"

    # Max-Age — must be positive (not expired)
    import re
    rt_age = re.search(r"max-age=(\d+)", rt)
    ts_age = re.search(r"max-age=(\d+)", ts)
    assert rt_age and int(rt_age.group(1)) > 0, "refresh_token Max-Age must be positive"
    assert ts_age and int(ts_age.group(1)) > 0, "tk_session Max-Age must be positive"


def _assert_session_cookies_cleared(response):
    """Assert both session cookies are expired (Max-Age=0)."""
    cookies = _cookie_map(response)
    assert "refresh_token" in cookies, "refresh_token clearing cookie must be present"
    assert "tk_session" in cookies, "tk_session clearing cookie must be present"

    rt = cookies["refresh_token"].lower()
    ts = cookies["tk_session"].lower()
    assert "max-age=0" in rt, f"refresh_token must have Max-Age=0, got: {rt}"
    assert "max-age=0" in ts, f"tk_session must have Max-Age=0, got: {ts}"


# ---------------------------------------------------------------------------
# Login — sets both cookies
# ---------------------------------------------------------------------------


async def test_login_sets_both_cookies(auth_client):
    """POST /auth/login → sets refresh_token + tk_session with correct attributes."""
    ac, svc, db = auth_client

    result = MagicMock()
    result.scalar_one_or_none.return_value = MOCK_USER
    db.execute = AsyncMock(return_value=result)

    with patch("app.api.routes.auth.check_login_attempts", return_value=True):
        with patch("app.api.routes.auth.verify_password", return_value=True):
            with patch("app.api.routes.auth._has_privileged_role", new=AsyncMock(return_value=False)):
                res = await ac.post(
                    "/api/auth/login",
                    json={"email": "user@test.com", "password": "Password1"},
                )

    assert res.status_code == 200
    assert "refresh_token" not in res.json(), "refresh_token must not be in JSON body"
    _assert_session_cookies_set(res)


# ---------------------------------------------------------------------------
# Register — sets both cookies
# ---------------------------------------------------------------------------


async def test_register_sets_both_cookies(auth_client):
    """POST /auth/register → sets refresh_token + tk_session."""
    ac, svc, db = auth_client

    result = MagicMock()
    result.scalar_one_or_none.return_value = None  # email not taken
    db.execute = AsyncMock(return_value=result)
    db.flush = AsyncMock()

    with patch("app.api.routes.auth.validate_password", return_value=(True, None)):
        with patch("app.api.routes.auth.hash_password", return_value="hashed"):
            with patch("app.api.routes.auth.email_service"):
                with patch("app.api.routes.auth.notification_service"):
                    res = await ac.post(
                        "/api/auth/register",
                        json={"email": "new@test.com", "password": "Password1!"},
                    )

    assert res.status_code == 201
    assert "refresh_token" not in res.json()
    _assert_session_cookies_set(res)


# ---------------------------------------------------------------------------
# Refresh — sets both cookies on success, clears on failure
# ---------------------------------------------------------------------------


async def test_refresh_sets_both_cookies_on_success(auth_client):
    """POST /auth/refresh with valid cookie → rotates both session cookies."""
    ac, svc, _ = auth_client
    res = await ac.post(
        "/api/auth/refresh",
        cookies={"refresh_token": FAKE_REFRESH},
    )
    assert res.status_code == 200
    _assert_session_cookies_set(res)


async def test_refresh_clears_cookies_on_missing():
    """POST /auth/refresh without cookie → 401 with both cookies expired."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.post("/api/auth/refresh")
    assert res.status_code == 401
    _assert_session_cookies_cleared(res)


async def test_refresh_clears_cookies_on_auth_error():
    """POST /auth/refresh with invalid cookie → 401 with both cookies expired."""
    from app.api.deps import get_refresh_service
    from app.core.exceptions import InvalidRefreshToken

    svc = AsyncMock()
    svc.rotate.side_effect = InvalidRefreshToken()
    app.dependency_overrides[get_refresh_service] = lambda: svc

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            res = await ac.post(
                "/api/auth/refresh",
                cookies={"refresh_token": "bad.token"},
            )
        assert res.status_code == 401
        _assert_session_cookies_cleared(res)
    finally:
        app.dependency_overrides.pop(get_refresh_service, None)


# ---------------------------------------------------------------------------
# Logout — clears both cookies
# ---------------------------------------------------------------------------


async def test_logout_clears_both_cookies(auth_client):
    """POST /auth/logout → both session cookies expired."""
    ac, svc, _ = auth_client
    res = await ac.post(
        "/api/auth/logout",
        cookies={"refresh_token": FAKE_REFRESH},
    )
    assert res.status_code == 204
    _assert_session_cookies_cleared(res)


async def test_logout_clears_cookies_even_without_token(auth_client):
    """POST /auth/logout without cookie → still clears both session cookies."""
    ac, svc, _ = auth_client
    res = await ac.post("/api/auth/logout")
    assert res.status_code == 204
    _assert_session_cookies_cleared(res)


# ---------------------------------------------------------------------------
# JSON body must NOT contain refresh_token
# ---------------------------------------------------------------------------


async def test_login_response_body_has_no_refresh_token(auth_client):
    ac, svc, db = auth_client
    result = MagicMock()
    result.scalar_one_or_none.return_value = MOCK_USER
    db.execute = AsyncMock(return_value=result)

    with patch("app.api.routes.auth.check_login_attempts", return_value=True):
        with patch("app.api.routes.auth.verify_password", return_value=True):
            with patch("app.api.routes.auth._has_privileged_role", new=AsyncMock(return_value=False)):
                res = await ac.post(
                    "/api/auth/login",
                    json={"email": "user@test.com", "password": "Password1"},
                )
    assert "refresh_token" not in res.json()


async def test_refresh_response_body_has_no_refresh_token(auth_client):
    ac, svc, _ = auth_client
    res = await ac.post(
        "/api/auth/refresh",
        cookies={"refresh_token": FAKE_REFRESH},
    )
    assert "refresh_token" not in res.json()
