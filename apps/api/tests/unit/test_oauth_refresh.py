"""Unit tests — OAuth SSO authorize + callback routes (stateless JWT state, no Redis)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import Response

from app.api.routes.oauth import OAuthCallbackRequest, OAuthCallbackResponse
from app.core.security import create_oauth_state_jwt, verify_oauth_state_jwt


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def make_user(user_id: uuid.UUID | None = None, is_admin: bool = False) -> MagicMock:
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.email = "sso@example.com"
    user.is_active = True
    user.is_admin = is_admin
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
# TokenResponse schema — backward-compat (unchanged)
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
# OAuthCallbackResponse schema
# ---------------------------------------------------------------------------


class TestOAuthCallbackResponseSchema:
    def test_has_returnto_field(self):
        resp = OAuthCallbackResponse(access_token="at", returnto="/chat")
        assert resp.returnto == "/chat"

    def test_returnto_is_required(self):
        with pytest.raises(Exception):
            OAuthCallbackResponse(access_token="at")  # missing returnto


# ---------------------------------------------------------------------------
# Google authorize — returns JSON {url} with JWT state embedded
# ---------------------------------------------------------------------------


class TestGoogleAuthorize:
    async def test_returns_url_with_state_jwt(self):
        from app.api.routes.oauth import google_authorize

        with patch.multiple("app.api.routes.oauth.settings", **_GOOGLE_SETTINGS):
            result = await google_authorize(returnto=None)

        parsed = urlparse(result.url)
        params = parse_qs(parsed.query)
        state_token = params["state"][0]
        oauth_state = verify_oauth_state_jwt(state_token)
        assert oauth_state.returnto is None

    async def test_returnto_embedded_in_state_jwt(self):
        from app.api.routes.oauth import google_authorize

        with patch.multiple("app.api.routes.oauth.settings", **_GOOGLE_SETTINGS):
            result = await google_authorize(returnto="/admin/invoices")

        params = parse_qs(urlparse(result.url).query)
        state = verify_oauth_state_jwt(params["state"][0])
        assert state.returnto == "/admin/invoices"

    async def test_invalid_returnto_silently_becomes_none(self):
        from app.api.routes.oauth import google_authorize

        with patch.multiple("app.api.routes.oauth.settings", **_GOOGLE_SETTINGS):
            result = await google_authorize(returnto="//evil.com/steal")

        params = parse_qs(urlparse(result.url).query)
        state = verify_oauth_state_jwt(params["state"][0])
        assert state.returnto is None

    async def test_invalid_returnto_logs_warning(self, caplog):
        from app.api.routes.oauth import google_authorize
        import logging

        with patch.multiple("app.api.routes.oauth.settings", **_GOOGLE_SETTINGS):
            with caplog.at_level(logging.WARNING, logger="app.api.routes.oauth"):
                await google_authorize(returnto="//evil.com")

        assert any("invalid returnto rejected" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# Microsoft authorize
# ---------------------------------------------------------------------------


class TestMicrosoftAuthorize:
    async def test_returns_url_with_state_jwt(self):
        from app.api.routes.oauth import microsoft_authorize

        with patch.multiple("app.api.routes.oauth.settings", **_MICROSOFT_SETTINGS):
            result = await microsoft_authorize(returnto=None)

        params = parse_qs(urlparse(result.url).query)
        state = verify_oauth_state_jwt(params["state"][0])
        assert state.returnto is None

    async def test_returnto_embedded_in_state_jwt(self):
        from app.api.routes.oauth import microsoft_authorize

        with patch.multiple("app.api.routes.oauth.settings", **_MICROSOFT_SETTINGS):
            result = await microsoft_authorize(returnto="/billing")

        params = parse_qs(urlparse(result.url).query)
        state = verify_oauth_state_jwt(params["state"][0])
        assert state.returnto == "/billing"


# ---------------------------------------------------------------------------
# Google callback — JWT state, returns OAuthCallbackResponse with returnto
# ---------------------------------------------------------------------------


class TestGoogleCallback:
    async def test_returns_access_token_and_returnto(self):
        from app.api.routes.oauth import google_callback

        state = create_oauth_state_jwt(returnto="/admin/invoices")
        body = OAuthCallbackRequest(code="gcode", state=state)
        user = make_user()
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair()

        with patch.multiple("app.api.routes.oauth.settings", **_GOOGLE_SETTINGS):
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
        assert result.returnto == "/admin/invoices"

    async def test_falls_back_to_chat_for_regular_user(self):
        from app.api.routes.oauth import google_callback

        state = create_oauth_state_jwt(returnto=None)
        body = OAuthCallbackRequest(code="gcode", state=state)
        user = make_user(is_admin=False)
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair()

        with patch.multiple("app.api.routes.oauth.settings", **_GOOGLE_SETTINGS):
            with patch("app.api.routes.oauth._exchange_google_code", new=AsyncMock(return_value=GOOGLE_PROFILE)):
                with patch("app.api.routes.oauth._upsert_sso_user", new=AsyncMock(return_value=user)):
                    result = await google_callback(
                        body=body,
                        request=make_request(),
                        response=Response(),
                        db=AsyncMock(),
                        service=service,
                    )

        assert result.returnto == "/chat"

    async def test_falls_back_to_admin_for_admin_user(self):
        from app.api.routes.oauth import google_callback

        state = create_oauth_state_jwt(returnto=None)
        body = OAuthCallbackRequest(code="gcode", state=state)
        user = make_user(is_admin=True)
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair()

        with patch.multiple("app.api.routes.oauth.settings", **_GOOGLE_SETTINGS):
            with patch("app.api.routes.oauth._exchange_google_code", new=AsyncMock(return_value=GOOGLE_PROFILE)):
                with patch("app.api.routes.oauth._upsert_sso_user", new=AsyncMock(return_value=user)):
                    result = await google_callback(
                        body=body,
                        request=make_request(),
                        response=Response(),
                        db=AsyncMock(),
                        service=service,
                    )

        assert result.returnto == "/admin"

    async def test_rejects_expired_state_with_401(self):
        from datetime import UTC, datetime, timedelta

        from app.api.routes.oauth import google_callback
        from jose import jwt as jose_jwt
        from app.config import settings as app_settings
        from app.core.security import OAUTH_STATE_TYPE

        now = datetime.now(UTC)
        payload = {
            "type": OAUTH_STATE_TYPE,
            "nonce": "a" * 32,
            "returnto": None,
            "iat": int((now - timedelta(seconds=700)).timestamp()),
            "exp": int((now - timedelta(seconds=100)).timestamp()),
        }
        expired_state = jose_jwt.encode(payload, app_settings.jwt_secret, algorithm=app_settings.jwt_algorithm)
        body = OAuthCallbackRequest(code="gcode", state=expired_state)

        from fastapi import HTTPException

        with patch.multiple("app.api.routes.oauth.settings", **_GOOGLE_SETTINGS):
            with pytest.raises(HTTPException) as exc_info:
                await google_callback(
                    body=body,
                    request=make_request(),
                    response=Response(),
                    db=AsyncMock(),
                    service=AsyncMock(),
                )

        assert exc_info.value.status_code == 401

    async def test_rejects_tampered_state_with_401(self):
        from app.api.routes.oauth import google_callback
        from fastapi import HTTPException

        good_state = create_oauth_state_jwt(returnto=None)
        parts = good_state.split(".")
        parts[-1] = parts[-1][:-4] + "XXXX"
        tampered = ".".join(parts)
        body = OAuthCallbackRequest(code="gcode", state=tampered)

        with patch.multiple("app.api.routes.oauth.settings", **_GOOGLE_SETTINGS):
            with pytest.raises(HTTPException) as exc_info:
                await google_callback(
                    body=body,
                    request=make_request(),
                    response=Response(),
                    db=AsyncMock(),
                    service=AsyncMock(),
                )

        assert exc_info.value.status_code == 401

    async def test_sets_session_cookies(self):
        from app.api.routes.oauth import google_callback

        state = create_oauth_state_jwt(returnto=None)
        body = OAuthCallbackRequest(code="gcode", state=state)
        user = make_user()
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair()
        mock_response = MagicMock()

        with patch.multiple("app.api.routes.oauth.settings", **_GOOGLE_SETTINGS):
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

    async def test_issue_pair_receives_user_and_device_info(self):
        from app.api.routes.oauth import google_callback

        state = create_oauth_state_jwt(returnto=None)
        body = OAuthCallbackRequest(code="gcode", state=state)
        user = make_user()
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair()
        req = make_request(ip="10.0.0.1")

        with patch.multiple("app.api.routes.oauth.settings", **_GOOGLE_SETTINGS):
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
# Microsoft callback — mirrors Google
# ---------------------------------------------------------------------------


class TestMicrosoftCallback:
    async def test_returns_access_token_and_returnto(self):
        from app.api.routes.oauth import microsoft_callback

        state = create_oauth_state_jwt(returnto="/billing")
        body = OAuthCallbackRequest(code="mscode", state=state)
        user = make_user()
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair()

        with patch.multiple("app.api.routes.oauth.settings", **_MICROSOFT_SETTINGS):
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
        assert result.returnto == "/billing"

    async def test_falls_back_to_chat_for_regular_user(self):
        from app.api.routes.oauth import microsoft_callback

        state = create_oauth_state_jwt(returnto=None)
        body = OAuthCallbackRequest(code="mscode", state=state)
        user = make_user(is_admin=False)
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair()

        with patch.multiple("app.api.routes.oauth.settings", **_MICROSOFT_SETTINGS):
            with patch("app.api.routes.oauth._exchange_microsoft_code", new=AsyncMock(return_value=MICROSOFT_PROFILE)):
                with patch("app.api.routes.oauth._upsert_sso_user", new=AsyncMock(return_value=user)):
                    result = await microsoft_callback(
                        body=body,
                        request=make_request(),
                        response=Response(),
                        db=AsyncMock(),
                        service=service,
                    )

        assert result.returnto == "/chat"

    async def test_falls_back_to_admin_for_admin_user(self):
        from app.api.routes.oauth import microsoft_callback

        state = create_oauth_state_jwt(returnto=None)
        body = OAuthCallbackRequest(code="mscode", state=state)
        user = make_user(is_admin=True)
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair()

        with patch.multiple("app.api.routes.oauth.settings", **_MICROSOFT_SETTINGS):
            with patch("app.api.routes.oauth._exchange_microsoft_code", new=AsyncMock(return_value=MICROSOFT_PROFILE)):
                with patch("app.api.routes.oauth._upsert_sso_user", new=AsyncMock(return_value=user)):
                    result = await microsoft_callback(
                        body=body,
                        request=make_request(),
                        response=Response(),
                        db=AsyncMock(),
                        service=service,
                    )

        assert result.returnto == "/admin"

    async def test_rejects_expired_state_with_401(self):
        from datetime import UTC, datetime, timedelta

        from app.api.routes.oauth import microsoft_callback
        from fastapi import HTTPException
        from jose import jwt as jose_jwt
        from app.config import settings as app_settings
        from app.core.security import OAUTH_STATE_TYPE

        now = datetime.now(UTC)
        payload = {
            "type": OAUTH_STATE_TYPE,
            "nonce": "a" * 32,
            "returnto": None,
            "iat": int((now - timedelta(seconds=700)).timestamp()),
            "exp": int((now - timedelta(seconds=100)).timestamp()),
        }
        expired_state = jose_jwt.encode(payload, app_settings.jwt_secret, algorithm=app_settings.jwt_algorithm)
        body = OAuthCallbackRequest(code="mscode", state=expired_state)

        with patch.multiple("app.api.routes.oauth.settings", **_MICROSOFT_SETTINGS):
            with pytest.raises(HTTPException) as exc_info:
                await microsoft_callback(
                    body=body,
                    request=make_request(),
                    response=Response(),
                    db=AsyncMock(),
                    service=AsyncMock(),
                )

        assert exc_info.value.status_code == 401

    async def test_rejects_tampered_state_with_401(self):
        from app.api.routes.oauth import microsoft_callback
        from fastapi import HTTPException

        good_state = create_oauth_state_jwt(returnto=None)
        parts = good_state.split(".")
        parts[-1] = parts[-1][:-4] + "XXXX"
        tampered = ".".join(parts)
        body = OAuthCallbackRequest(code="mscode", state=tampered)

        with patch.multiple("app.api.routes.oauth.settings", **_MICROSOFT_SETTINGS):
            with pytest.raises(HTTPException) as exc_info:
                await microsoft_callback(
                    body=body,
                    request=make_request(),
                    response=Response(),
                    db=AsyncMock(),
                    service=AsyncMock(),
                )

        assert exc_info.value.status_code == 401

    async def test_sets_session_cookies(self):
        from app.api.routes.oauth import microsoft_callback

        state = create_oauth_state_jwt(returnto=None)
        body = OAuthCallbackRequest(code="mscode", state=state)
        user = make_user()
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair()
        mock_response = MagicMock()

        with patch.multiple("app.api.routes.oauth.settings", **_MICROSOFT_SETTINGS):
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
