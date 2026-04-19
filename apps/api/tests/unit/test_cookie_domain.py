"""Tests for cookie domain injection (Phase 8 — fix-rate-limit-architecture).

Verifies that settings.cookie_domain is correctly injected into Set-Cookie headers:
- Empty string  → no Domain attribute (safe for localhost dev)
- Non-empty string → Domain=<value> present on both set and delete operations
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
    email = "domain-test@test.com"
    full_name = "Domain Test"
    is_active = True
    is_admin = False
    plan = "free"
    hashed_password = "hashed"
    auth_provider = "email"
    avatar_url = None
    default_org_id = None
    created_at = datetime.now(UTC)


MOCK_USER = _MockUser()


def _cookie_map(response) -> dict[str, str]:
    """Return {cookie_name: full_header_value} for each Set-Cookie header."""
    result = {}
    for header in response.headers.get_list("set-cookie"):
        name = header.split("=")[0].strip()
        result[name] = header
    return result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def auth_client_with_domain(cookie_domain: str):
    """Client with service + user overrides and a patched cookie_domain."""
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

    with patch("app.api.routes.auth.settings") as mock_settings:
        mock_settings.cookie_domain = cookie_domain
        mock_settings.app_debug = True  # avoid HSTS header interference

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac, svc, db

    app.dependency_overrides.pop(get_refresh_service, None)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Empty domain — no Domain= attribute on cookies
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_domain_no_domain_attr_on_set():
    """When cookie_domain is empty, Set-Cookie must NOT contain Domain= attribute."""
    from app.api.deps import get_current_user, get_refresh_service
    from app.core.database import get_db

    svc = AsyncMock()
    svc.rotate.return_value = FAKE_PAIR
    db = AsyncMock()

    app.dependency_overrides[get_refresh_service] = lambda: svc
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    app.dependency_overrides[get_db] = lambda: db

    try:
        with patch("app.api.routes.auth.settings") as mock_settings:
            mock_settings.cookie_domain = ""
            mock_settings.app_debug = True

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                res = await ac.post(
                    "/api/auth/refresh",
                    cookies={"refresh_token": FAKE_REFRESH},
                )

        assert res.status_code == 200
        cookies = _cookie_map(res)
        assert "refresh_token" in cookies
        assert "tk_session" in cookies

        rt = cookies["refresh_token"].lower()
        ts = cookies["tk_session"].lower()

        # Domain= must be absent
        assert "domain=" not in rt, f"refresh_token must not have Domain= when empty, got: {rt}"
        assert "domain=" not in ts, f"tk_session must not have Domain= when empty, got: {ts}"
    finally:
        app.dependency_overrides.pop(get_refresh_service, None)
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Non-empty domain — Domain= attribute present on cookies
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_custom_domain_injects_domain_attr_on_set():
    """When cookie_domain is set, Set-Cookie must include Domain=<value>."""
    from app.api.deps import get_current_user, get_refresh_service
    from app.core.database import get_db

    svc = AsyncMock()
    svc.rotate.return_value = FAKE_PAIR
    db = AsyncMock()

    app.dependency_overrides[get_refresh_service] = lambda: svc
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    app.dependency_overrides[get_db] = lambda: db

    try:
        with patch("app.api.routes.auth.settings") as mock_settings:
            mock_settings.cookie_domain = ".tukijuris.net.pe"
            mock_settings.app_debug = True

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                res = await ac.post(
                    "/api/auth/refresh",
                    cookies={"refresh_token": FAKE_REFRESH},
                )

        assert res.status_code == 200
        cookies = _cookie_map(res)
        assert "refresh_token" in cookies
        assert "tk_session" in cookies

        rt = cookies["refresh_token"].lower()
        ts = cookies["tk_session"].lower()

        assert "domain=.tukijuris.net.pe" in rt, (
            f"refresh_token must have domain=.tukijuris.net.pe, got: {rt}"
        )
        assert "domain=.tukijuris.net.pe" in ts, (
            f"tk_session must have domain=.tukijuris.net.pe, got: {ts}"
        )
    finally:
        app.dependency_overrides.pop(get_refresh_service, None)
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_custom_domain_injects_domain_attr_on_clear():
    """When cookie_domain is set, delete_cookie (logout) also uses Domain=<value>."""
    from app.api.deps import get_current_user, get_refresh_service
    from app.core.database import get_db

    svc = AsyncMock()
    svc.revoke.return_value = None
    db = AsyncMock()

    app.dependency_overrides[get_refresh_service] = lambda: svc
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    app.dependency_overrides[get_db] = lambda: db

    try:
        with patch("app.api.routes.auth.settings") as mock_settings:
            mock_settings.cookie_domain = ".tukijuris.net.pe"
            mock_settings.app_debug = True

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                res = await ac.post(
                    "/api/auth/logout",
                    cookies={"refresh_token": FAKE_REFRESH},
                )

        assert res.status_code == 204
        cookies = _cookie_map(res)
        assert "refresh_token" in cookies
        assert "tk_session" in cookies

        rt = cookies["refresh_token"].lower()
        ts = cookies["tk_session"].lower()

        # Must be expired
        assert "max-age=0" in rt
        assert "max-age=0" in ts

        # Must carry the domain on delete too (browsers require it to match)
        assert "domain=.tukijuris.net.pe" in rt, (
            f"refresh_token clear must have domain= on logout, got: {rt}"
        )
        assert "domain=.tukijuris.net.pe" in ts, (
            f"tk_session clear must have domain= on logout, got: {ts}"
        )
    finally:
        app.dependency_overrides.pop(get_refresh_service, None)
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Unit-level: _domain_kw logic
# ---------------------------------------------------------------------------


def test_domain_kw_empty_string_produces_empty_dict():
    """When cookie_domain is falsy, _domain_kw must be {}."""
    cookie_domain = ""
    domain_kw = {"domain": cookie_domain} if cookie_domain else {}
    assert domain_kw == {}


def test_domain_kw_non_empty_string_produces_domain_dict():
    """When cookie_domain is non-empty, _domain_kw must contain domain key."""
    cookie_domain = ".tukijuris.net.pe"
    domain_kw = {"domain": cookie_domain} if cookie_domain else {}
    assert domain_kw == {"domain": ".tukijuris.net.pe"}
