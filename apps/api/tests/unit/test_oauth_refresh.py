"""Unit tests — OAuth SSO callbacks set refresh-token cookie, return access token only."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Response

from app.api.routes.oauth import OAuthCallbackRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_user(user_id: uuid.UUID | None = None) -> MagicMock:
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.email = "sso@example.com"
    user.is_active = True
    user.is_admin = False
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
# TokenResponse schema — refresh_token removed from JSON body
# ---------------------------------------------------------------------------


class TestTokenResponseSchema:
    def test_has_access_token_field(self):
        from app.api.routes.oauth import TokenResponse

        resp = TokenResponse(access_token="at")
        assert resp.access_token == "at"
        assert resp.token_type == "bearer"

    def test_has_expires_in_field(self):
        from app.api.routes.oauth import TokenResponse

        resp = TokenResponse(access_token="at", expires_in=900)
        assert resp.expires_in == 900

    def test_default_expires_in_is_900(self):
        from app.api.routes.oauth import TokenResponse

        resp = TokenResponse(access_token="at")
        assert resp.expires_in == 900

    def test_no_refresh_token_in_body(self):
        """refresh_token must NOT appear in OAuth JSON response body."""
        from app.api.routes.oauth import TokenResponse

        resp = TokenResponse(access_token="at")
        assert not hasattr(resp, "refresh_token") or "refresh_token" not in resp.model_fields


# ---------------------------------------------------------------------------
# Google callback — returns access token, sets cookie
# ---------------------------------------------------------------------------


class TestGoogleCallbackReturnsTokenPair:
    async def test_returns_access_token(self):
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
                            response=Response(),
                            db=AsyncMock(),
                            service=service,
                        )

        assert result.access_token == "access_tok_sso"
        assert not hasattr(result, "refresh_token") or "refresh_token" not in result.model_fields

    async def test_sets_session_cookies(self):
        """Google callback must call _set_session_cookies with the refresh token."""
        from app.api.routes.oauth import google_callback

        body = OAuthCallbackRequest(code="gcode", state="valid_state")
        user = make_user()
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair()
        mock_response = MagicMock()

        with patch.multiple("app.api.routes.oauth.settings", **_GOOGLE_SETTINGS):
            with patch("app.api.routes.oauth._get_redis", new=AsyncMock(return_value=make_redis_mock())):
                with patch("app.api.routes.oauth._exchange_google_code", new=AsyncMock(return_value=GOOGLE_PROFILE)):
                    with patch("app.api.routes.oauth._upsert_sso_user", new=AsyncMock(return_value=user)):
                        with patch("app.api.routes.oauth._set_session_cookies") as mock_set:
                            await google_callback(
                                body=body,
                                request=make_request(),
                                response=mock_response,
                                db=AsyncMock(),
                                service=service,
                            )

        mock_set.assert_called_once_with(mock_response, "refresh_tok_sso")

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
                        await google_callback(
                            body=body,
                            request=make_request(),
                            response=Response(),
                            db=AsyncMock(),
                            service=service,
                        )

        service.issue_pair.assert_called_once()

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
                            response=Response(),
                            db=AsyncMock(),
                            service=service,
                        )

        call_args = service.issue_pair.call_args
        assert call_args.args[0] is user
        assert call_args.args[1]["ip_address"] == "10.0.0.1"


# ---------------------------------------------------------------------------
# Microsoft callback — returns access token, sets cookie
# ---------------------------------------------------------------------------


class TestMicrosoftCallbackReturnsTokenPair:
    async def test_returns_access_token(self):
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
                            response=Response(),
                            db=AsyncMock(),
                            service=service,
                        )

        assert result.access_token == "access_tok_sso"
        assert not hasattr(result, "refresh_token") or "refresh_token" not in result.model_fields

    async def test_sets_session_cookies(self):
        """Microsoft callback must call _set_session_cookies with the refresh token."""
        from app.api.routes.oauth import microsoft_callback

        body = OAuthCallbackRequest(code="mscode", state="valid_state")
        user = make_user()
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair()
        mock_response = MagicMock()

        with patch.multiple("app.api.routes.oauth.settings", **_MICROSOFT_SETTINGS):
            with patch("app.api.routes.oauth._get_redis", new=AsyncMock(return_value=make_redis_mock())):
                with patch("app.api.routes.oauth._exchange_microsoft_code", new=AsyncMock(return_value=MICROSOFT_PROFILE)):
                    with patch("app.api.routes.oauth._upsert_sso_user", new=AsyncMock(return_value=user)):
                        with patch("app.api.routes.oauth._set_session_cookies") as mock_set:
                            await microsoft_callback(
                                body=body,
                                request=make_request(),
                                response=mock_response,
                                db=AsyncMock(),
                                service=service,
                            )

        mock_set.assert_called_once_with(mock_response, "refresh_tok_sso")

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
                        await microsoft_callback(
                            body=body,
                            request=make_request(),
                            response=Response(),
                            db=AsyncMock(),
                            service=service,
                        )

        service.issue_pair.assert_called_once()
