"""Unit tests — OAuth SSO callbacks return refresh token pair (RED: T5.7)."""

import uuid
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.routes.oauth import OAuthCallbackRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_user(user_id: uuid.UUID | None = None) -> MagicMock:
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.email = "sso@example.com"
    user.is_active = True
    return user


def make_request(ip: str = "127.0.0.1") -> MagicMock:
    req = MagicMock()
    req.client.host = ip
    req.headers.get.return_value = "Mozilla/5.0"
    return req


def make_token_pair():
    from app.services.refresh_token_service import TokenPair

    return TokenPair(
        access_token="access_tok_sso",
        refresh_token="refresh_tok_sso",
        expires_in=900,
    )


def make_redis_mock(state_valid: bool = True) -> AsyncMock:
    redis = AsyncMock()
    redis.get = AsyncMock(return_value="1" if state_valid else None)
    redis.delete = AsyncMock()
    return redis


GOOGLE_PROFILE = {
    "id": "google123",
    "email": "sso@example.com",
    "name": "Test User",
    "picture": None,
}

MICROSOFT_PROFILE = {
    "id": "ms123",
    "email": "sso@example.com",
    "name": "Test User",
    "picture": None,
}

# Patch helpers — fake OAuth credentials so the 503 guard doesn't fire
_GOOGLE_SETTINGS = {
    "google_oauth_client_id": "fake_google_id",
    "google_oauth_client_secret": "fake_google_secret",
}
_MICROSOFT_SETTINGS = {
    "microsoft_oauth_client_id": "fake_ms_id",
    "microsoft_oauth_client_secret": "fake_ms_secret",
    "microsoft_oauth_tenant_id": "fake_tenant",
}


# ---------------------------------------------------------------------------
# T5.7 — TokenResponse schema includes refresh_token
# ---------------------------------------------------------------------------


class TestTokenResponseSchema:
    def test_has_refresh_token_field(self):
        from app.api.routes.oauth import TokenResponse

        resp = TokenResponse(access_token="at", refresh_token="rt")
        assert resp.refresh_token == "rt"
        assert resp.token_type == "bearer"

    def test_has_expires_in_field(self):
        from app.api.routes.oauth import TokenResponse

        resp = TokenResponse(access_token="at", refresh_token="rt", expires_in=900)
        assert resp.expires_in == 900

    def test_default_expires_in_is_900(self):
        from app.api.routes.oauth import TokenResponse

        resp = TokenResponse(access_token="at", refresh_token="rt")
        assert resp.expires_in == 900


# ---------------------------------------------------------------------------
# T5.7 — Google callback returns token pair
# ---------------------------------------------------------------------------


class TestGoogleCallbackReturnsTokenPair:
    async def test_returns_access_and_refresh_token(self):
        from app.api.routes.oauth import google_callback

        body = OAuthCallbackRequest(code="gcode", state="valid_state")
        user = make_user()
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair()

        with patch.multiple("app.api.routes.oauth.settings", **_GOOGLE_SETTINGS):
            with patch("app.api.routes.oauth._get_redis", new=AsyncMock(return_value=make_redis_mock())):
                with patch("app.api.routes.oauth._exchange_google_code", new=AsyncMock(return_value=GOOGLE_PROFILE)):
                    with patch("app.api.routes.oauth._upsert_sso_user", new=AsyncMock(return_value=user)):
                        result = await google_callback(
                            body=body,
                            request=make_request(),
                            db=AsyncMock(),
                            service=service,
                        )

        assert result.access_token == "access_tok_sso"
        assert result.refresh_token == "refresh_tok_sso"

    async def test_calls_issue_pair_not_create_access_token(self):
        from app.api.routes.oauth import google_callback

        body = OAuthCallbackRequest(code="gcode", state="valid_state")
        user = make_user()
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair()

        with patch.multiple("app.api.routes.oauth.settings", **_GOOGLE_SETTINGS):
            with patch("app.api.routes.oauth._get_redis", new=AsyncMock(return_value=make_redis_mock())):
                with patch("app.api.routes.oauth._exchange_google_code", new=AsyncMock(return_value=GOOGLE_PROFILE)):
                    with patch("app.api.routes.oauth._upsert_sso_user", new=AsyncMock(return_value=user)):
                        with patch("app.api.routes.oauth.create_access_token") as mock_create:
                            await google_callback(
                                body=body,
                                request=make_request(),
                                db=AsyncMock(),
                                service=service,
                            )

        service.issue_pair.assert_called_once()
        mock_create.assert_not_called()

    async def test_issue_pair_receives_user_and_device_info(self):
        from app.api.routes.oauth import google_callback

        body = OAuthCallbackRequest(code="gcode", state="valid_state")
        user = make_user()
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair()
        req = make_request(ip="10.0.0.1")

        with patch.multiple("app.api.routes.oauth.settings", **_GOOGLE_SETTINGS):
            with patch("app.api.routes.oauth._get_redis", new=AsyncMock(return_value=make_redis_mock())):
                with patch("app.api.routes.oauth._exchange_google_code", new=AsyncMock(return_value=GOOGLE_PROFILE)):
                    with patch("app.api.routes.oauth._upsert_sso_user", new=AsyncMock(return_value=user)):
                        await google_callback(
                            body=body,
                            request=req,
                            db=AsyncMock(),
                            service=service,
                        )

        call_args = service.issue_pair.call_args
        assert call_args.args[0] is user
        assert call_args.args[1]["ip_address"] == "10.0.0.1"


# ---------------------------------------------------------------------------
# T5.7 — Microsoft callback returns token pair
# ---------------------------------------------------------------------------


class TestMicrosoftCallbackReturnsTokenPair:
    async def test_returns_access_and_refresh_token(self):
        from app.api.routes.oauth import microsoft_callback

        body = OAuthCallbackRequest(code="mscode", state="valid_state")
        user = make_user()
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair()

        with patch.multiple("app.api.routes.oauth.settings", **_MICROSOFT_SETTINGS):
            with patch("app.api.routes.oauth._get_redis", new=AsyncMock(return_value=make_redis_mock())):
                with patch("app.api.routes.oauth._exchange_microsoft_code", new=AsyncMock(return_value=MICROSOFT_PROFILE)):
                    with patch("app.api.routes.oauth._upsert_sso_user", new=AsyncMock(return_value=user)):
                        result = await microsoft_callback(
                            body=body,
                            request=make_request(),
                            db=AsyncMock(),
                            service=service,
                        )

        assert result.access_token == "access_tok_sso"
        assert result.refresh_token == "refresh_tok_sso"

    async def test_calls_issue_pair_not_create_access_token(self):
        from app.api.routes.oauth import microsoft_callback

        body = OAuthCallbackRequest(code="mscode", state="valid_state")
        user = make_user()
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair()

        with patch.multiple("app.api.routes.oauth.settings", **_MICROSOFT_SETTINGS):
            with patch("app.api.routes.oauth._get_redis", new=AsyncMock(return_value=make_redis_mock())):
                with patch("app.api.routes.oauth._exchange_microsoft_code", new=AsyncMock(return_value=MICROSOFT_PROFILE)):
                    with patch("app.api.routes.oauth._upsert_sso_user", new=AsyncMock(return_value=user)):
                        with patch("app.api.routes.oauth.create_access_token") as mock_create:
                            await microsoft_callback(
                                body=body,
                                request=make_request(),
                                db=AsyncMock(),
                                service=service,
                            )

        service.issue_pair.assert_called_once()
        mock_create.assert_not_called()
