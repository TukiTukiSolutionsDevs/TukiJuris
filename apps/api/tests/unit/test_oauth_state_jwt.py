"""Unit tests for OAuth state JWT helpers (create_oauth_state_jwt / verify_oauth_state_jwt)."""

import base64
import json
from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from app.config import settings
from app.core.security import (
    OAUTH_STATE_MAX_AGE_SECONDS,
    OAUTH_STATE_TYPE,
    InvalidStateTokenError,
    OAuthState,
    create_oauth_state_jwt,
    verify_oauth_state_jwt,
)


# ---------------------------------------------------------------------------
# create_oauth_state_jwt
# ---------------------------------------------------------------------------


def test_sign_creates_expected_claims():
    """Payload must contain all required claim keys with correct shapes."""
    token = create_oauth_state_jwt(returnto="/admin/invoices")
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

    assert payload["type"] == OAUTH_STATE_TYPE
    nonce = payload["nonce"]
    assert isinstance(nonce, str) and len(nonce) == 32
    assert payload["returnto"] == "/admin/invoices"
    assert isinstance(payload["iat"], (int, float))
    assert isinstance(payload["exp"], (int, float))
    assert payload["exp"] == pytest.approx(payload["iat"] + OAUTH_STATE_MAX_AGE_SECONDS, abs=2)


def test_sign_generates_unique_nonces():
    """Two consecutive calls must produce different nonce values."""
    t1 = create_oauth_state_jwt(returnto=None)
    t2 = create_oauth_state_jwt(returnto=None)
    p1 = jwt.decode(t1, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    p2 = jwt.decode(t2, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert p1["nonce"] != p2["nonce"]


def test_sign_none_returnto_encoded():
    """returnto=None must be stored in the payload (not omitted) and decoded as None."""
    token = create_oauth_state_jwt(returnto=None)
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert "returnto" in payload
    assert payload["returnto"] is None


# ---------------------------------------------------------------------------
# verify_oauth_state_jwt — happy path
# ---------------------------------------------------------------------------


def test_verify_roundtrip_returns_oauth_state():
    """Round-trip: create then verify returns OAuthState with correct fields."""
    token = create_oauth_state_jwt(returnto="/chat")
    state = verify_oauth_state_jwt(token)

    assert isinstance(state, OAuthState)
    assert state.returnto == "/chat"
    assert isinstance(state.nonce, str) and len(state.nonce) == 32
    assert isinstance(state.iat, int)
    assert isinstance(state.exp, int)


def test_verify_accepts_none_returnto():
    """OAuthState.returnto is None when create was called with returnto=None."""
    token = create_oauth_state_jwt(returnto=None)
    state = verify_oauth_state_jwt(token)
    assert state.returnto is None


# ---------------------------------------------------------------------------
# verify_oauth_state_jwt — error paths
# ---------------------------------------------------------------------------


def test_verify_rejects_expired_token():
    """A token whose exp is in the past raises InvalidStateTokenError."""
    now = datetime.now(UTC)
    payload = {
        "type": OAUTH_STATE_TYPE,
        "nonce": "a" * 32,
        "returnto": None,
        "iat": int((now - timedelta(seconds=700)).timestamp()),
        "exp": int((now - timedelta(seconds=100)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    with pytest.raises(InvalidStateTokenError):
        verify_oauth_state_jwt(token)


def test_verify_rejects_bad_signature():
    """A token with a tampered signature raises InvalidStateTokenError."""
    token = create_oauth_state_jwt(returnto=None)
    # Replace last 4 chars of the signature segment with garbage
    parts = token.split(".")
    parts[-1] = parts[-1][:-4] + "XXXX"
    tampered = ".".join(parts)

    with pytest.raises(InvalidStateTokenError):
        verify_oauth_state_jwt(tampered)


def test_verify_rejects_wrong_type_claim():
    """A JWT with type != 'oauth_state' raises InvalidStateTokenError."""
    now = datetime.now(UTC)
    payload = {
        "type": "access",  # wrong type — access-token confusion attack
        "nonce": "a" * 32,
        "returnto": None,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=600)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    with pytest.raises(InvalidStateTokenError):
        verify_oauth_state_jwt(token)


def test_verify_rejects_missing_nonce():
    """A JWT without a nonce claim raises InvalidStateTokenError."""
    now = datetime.now(UTC)
    payload = {
        "type": OAUTH_STATE_TYPE,
        # intentionally omitting "nonce"
        "returnto": None,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=600)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    with pytest.raises(InvalidStateTokenError):
        verify_oauth_state_jwt(token)


def test_verify_rejects_malformed_token():
    """An entirely malformed string raises InvalidStateTokenError."""
    with pytest.raises(InvalidStateTokenError):
        verify_oauth_state_jwt("not.a.jwt")


def test_verify_rejects_empty_string():
    """An empty string raises InvalidStateTokenError."""
    with pytest.raises(InvalidStateTokenError):
        verify_oauth_state_jwt("")


def test_verify_rejects_alg_none_attack():
    """A raw unsigned JWT (alg=none) must be rejected by python-jose."""
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "none", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()

    now = int(datetime.now(UTC).timestamp())
    body_data = {
        "type": OAUTH_STATE_TYPE,
        "nonce": "a" * 32,
        "returnto": None,
        "iat": now,
        "exp": now + 600,
    }
    body = base64.urlsafe_b64encode(
        json.dumps(body_data).encode()
    ).rstrip(b"=").decode()

    # alg=none token: header.payload. (empty signature)
    token = f"{header}.{body}."

    with pytest.raises(InvalidStateTokenError):
        verify_oauth_state_jwt(token)
