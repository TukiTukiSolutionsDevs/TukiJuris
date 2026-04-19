"""Integration tests — OAuth returnto threading (authorize → callback round-trip).

Uses ASGITransport to exercise real FastAPI routing. External HTTP calls
(_exchange_google_code, _exchange_microsoft_code, _upsert_sso_user, service.issue_pair)
are patched so no real network or DB is needed.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/unit/test_oauth_returnto_integration.py -v
"""

import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt as jose_jwt

from app.api.deps import get_refresh_service
from app.config import settings
from app.core.database import get_db
from app.core.security import OAUTH_STATE_TYPE, create_oauth_state_jwt
from app.main import app

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

GOOGLE_PROFILE = {
    "id": "g-integration-user",
    "email": "integration@example.com",
    "name": "Integration User",
    "picture": None,
}

MICROSOFT_PROFILE = {
    "id": "ms-integration-user",
    "email": "integration@example.com",
    "name": "Integration User",
    "picture": None,
}


def make_user(is_admin: bool = False) -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "integration@example.com"
    user.is_active = True
    user.is_admin = is_admin
    return user


def make_token_pair():
    from app.services.refresh_token_service import TokenPair

    return TokenPair(
        access_token="integration_access_token",
        refresh_token="integration_refresh_token",
        expires_in=900,
    )


_GOOGLE_SETTINGS = {
    "google_oauth_client_id": "fake_google_id",
    "google_oauth_client_secret": "fake_google_secret",
}
_MICROSOFT_SETTINGS = {
    "microsoft_oauth_client_id": "fake_ms_id",
    "microsoft_oauth_client_secret": "fake_ms_secret",
    "microsoft_oauth_tenant_id": "fake_tenant",
}


def _make_override_service(user: MagicMock):
    """Build a mock RefreshTokenService whose issue_pair returns a fixed TokenPair."""
    svc = AsyncMock()
    svc.issue_pair.return_value = make_token_pair()
    return svc


# ---------------------------------------------------------------------------
# Parametrized fixtures
# ---------------------------------------------------------------------------

PROVIDER_PARAMS = [
    pytest.param(
        "google",
        "/api/auth/oauth/google/authorize",
        "/api/auth/oauth/google/callback",
        GOOGLE_PROFILE,
        "_exchange_google_code",
        _GOOGLE_SETTINGS,
        id="google",
    ),
    pytest.param(
        "microsoft",
        "/api/auth/oauth/microsoft/authorize",
        "/api/auth/oauth/microsoft/callback",
        MICROSOFT_PROFILE,
        "_exchange_microsoft_code",
        _MICROSOFT_SETTINGS,
        id="microsoft",
    ),
]


# ---------------------------------------------------------------------------
# Helper: run a full authorize→callback round-trip via ASGITransport
# ---------------------------------------------------------------------------


async def _run_round_trip(
    returnto: str | None,
    profile: dict,
    exchange_fn: str,
    oauth_settings: dict,
    authorize_url: str,
    callback_url: str,
    user: MagicMock,
) -> dict:
    """
    1. GET authorize?returnto=<returnto> → extract state JWT from provider URL
    2. POST callback {code, state} → return {status, body}

    Uses app.dependency_overrides to inject mock DB session and service so
    no real PostgreSQL connection is needed.
    """
    mock_svc = _make_override_service(user)

    # Override FastAPI DI — must be cleaned up after the request
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    app.dependency_overrides[get_refresh_service] = lambda: mock_svc
    try:
        with patch.multiple("app.api.routes.oauth.settings", **oauth_settings):
            with patch(f"app.api.routes.oauth.{exchange_fn}", new=AsyncMock(return_value=profile)):
                with patch("app.api.routes.oauth._upsert_sso_user", new=AsyncMock(return_value=user)):
                    with patch("app.api.routes.oauth._set_session_cookies"):
                        async with AsyncClient(
                            transport=ASGITransport(app=app),
                            base_url="http://test",
                        ) as client:
                            # Step 1: authorize
                            auth_url = authorize_url
                            if returnto:
                                auth_url = f"{authorize_url}?returnto={returnto}"
                            auth_res = await client.get(auth_url)
                            assert auth_res.status_code == 200, f"Authorize failed: {auth_res.text}"
                            state_in_url = parse_qs(urlparse(auth_res.json()["url"]).query)["state"][0]

                            # Step 2: callback
                            cb_res = await client.post(
                                callback_url,
                                json={"code": "test-code", "state": state_in_url},
                            )
                            return {"status": cb_res.status_code, "body": cb_res.json()}
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_refresh_service, None)


# ---------------------------------------------------------------------------
# Test: end-to-end happy path — returnto threads through
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "provider,authorize_url,callback_url,profile,exchange_fn,oauth_settings",
    PROVIDER_PARAMS,
)
async def test_end_to_end_returnto_threads_through(
    provider, authorize_url, callback_url, profile, exchange_fn, oauth_settings
):
    """authorize with ?returnto=/admin/invoices → callback returns returnto=/admin/invoices."""
    user = make_user(is_admin=False)
    result = await _run_round_trip(
        returnto="/admin/invoices",
        profile=profile,
        exchange_fn=exchange_fn,
        oauth_settings=oauth_settings,
        authorize_url=authorize_url,
        callback_url=callback_url,
        user=user,
    )
    assert result["status"] == 200
    assert result["body"]["returnto"] == "/admin/invoices"


# ---------------------------------------------------------------------------
# Test: missing returnto → role-based fallback
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "provider,authorize_url,callback_url,profile,exchange_fn,oauth_settings",
    PROVIDER_PARAMS,
)
async def test_end_to_end_fallback_regular_user(
    provider, authorize_url, callback_url, profile, exchange_fn, oauth_settings
):
    """authorize without returnto → callback returns /chat for regular user."""
    user = make_user(is_admin=False)
    result = await _run_round_trip(
        returnto=None,
        profile=profile,
        exchange_fn=exchange_fn,
        oauth_settings=oauth_settings,
        authorize_url=authorize_url,
        callback_url=callback_url,
        user=user,
    )
    assert result["status"] == 200
    assert result["body"]["returnto"] == "/chat"


@pytest.mark.parametrize(
    "provider,authorize_url,callback_url,profile,exchange_fn,oauth_settings",
    PROVIDER_PARAMS,
)
async def test_end_to_end_fallback_admin_user(
    provider, authorize_url, callback_url, profile, exchange_fn, oauth_settings
):
    """authorize without returnto → callback returns /admin for admin user."""
    user = make_user(is_admin=True)
    result = await _run_round_trip(
        returnto=None,
        profile=profile,
        exchange_fn=exchange_fn,
        oauth_settings=oauth_settings,
        authorize_url=authorize_url,
        callback_url=callback_url,
        user=user,
    )
    assert result["status"] == 200
    assert result["body"]["returnto"] == "/admin"


# ---------------------------------------------------------------------------
# Test: invalid returnto at authorize → state JWT has returnto=None → fallback
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "provider,authorize_url,callback_url,profile,exchange_fn,oauth_settings",
    PROVIDER_PARAMS,
)
async def test_invalid_returnto_at_init_falls_back(
    provider, authorize_url, callback_url, profile, exchange_fn, oauth_settings
):
    """authorize with invalid returnto (//evil.com) → state JWT returnto=None → /chat fallback."""
    user = make_user(is_admin=False)
    result = await _run_round_trip(
        returnto="//evil.com/steal",
        profile=profile,
        exchange_fn=exchange_fn,
        oauth_settings=oauth_settings,
        authorize_url=authorize_url,
        callback_url=callback_url,
        user=user,
    )
    assert result["status"] == 200
    assert result["body"]["returnto"] == "/chat"


# ---------------------------------------------------------------------------
# Test: tampered state JWT → 401
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "provider,authorize_url,callback_url,profile,exchange_fn,oauth_settings",
    PROVIDER_PARAMS,
)
async def test_tampered_state_returns_401(
    provider, authorize_url, callback_url, profile, exchange_fn, oauth_settings
):
    """A tampered state JWT must be rejected with HTTP 401."""
    good_state = create_oauth_state_jwt(returnto=None)
    parts = good_state.split(".")
    parts[-1] = parts[-1][:-4] + "XXXX"
    tampered = ".".join(parts)

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    app.dependency_overrides[get_refresh_service] = lambda: AsyncMock()
    try:
        with patch.multiple("app.api.routes.oauth.settings", **oauth_settings):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                res = await client.post(
                    callback_url,
                    json={"code": "test-code", "state": tampered},
                )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_refresh_service, None)

    assert res.status_code == 401


# ---------------------------------------------------------------------------
# Test: expired state JWT → 401
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "provider,authorize_url,callback_url,profile,exchange_fn,oauth_settings",
    PROVIDER_PARAMS,
)
async def test_expired_state_returns_401(
    provider, authorize_url, callback_url, profile, exchange_fn, oauth_settings
):
    """An expired state JWT must be rejected with HTTP 401."""
    now = datetime.now(UTC)
    payload = {
        "type": OAUTH_STATE_TYPE,
        "nonce": "a" * 32,
        "returnto": None,
        "iat": int((now - timedelta(seconds=700)).timestamp()),
        "exp": int((now - timedelta(seconds=100)).timestamp()),
    }
    expired_state = jose_jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    app.dependency_overrides[get_db] = lambda: AsyncMock()
    app.dependency_overrides[get_refresh_service] = lambda: AsyncMock()
    try:
        with patch.multiple("app.api.routes.oauth.settings", **oauth_settings):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                res = await client.post(
                    callback_url,
                    json={"code": "test-code", "state": expired_state},
                )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_refresh_service, None)

    assert res.status_code == 401
