"""Integration tests — OAuth state parameter tampering rejection.

The state JWT is verified BEFORE any OAuth provider communication, so these
tests return 401 regardless of whether Google/Microsoft OAuth is configured.

Covers:
- Tampered (garbage) state string → 401
- Expired but validly-signed state JWT → 401
- JWT signed with wrong secret → 401
Both Google and Microsoft callback endpoints are covered.

Run:
    docker exec tukijuris-api-1 pytest tests/integration/test_auth_oauth_state.py -v
"""

import time

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt as jose_jwt

from app.config import settings
from app.main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# State token factories
# ---------------------------------------------------------------------------


def _tampered_state() -> str:
    """A random string that is not a valid signed JWT."""
    return "tampered.notavalidjwt.state"


def _expired_state() -> str:
    """A validly-signed state JWT whose exp is 1 hour in the past."""
    payload = {
        "returnto": "/chat",
        "exp": int(time.time()) - 3600,
        "iat": int(time.time()) - 7200,
    }
    return jose_jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _wrong_signature_state() -> str:
    """A structurally valid JWT signed with a different secret — signature mismatch."""
    payload = {
        "returnto": "/chat",
        "exp": int(time.time()) + 600,
        "iat": int(time.time()),
    }
    return jose_jwt.encode(payload, "completely-wrong-secret", algorithm=settings.jwt_algorithm)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestOAuthStateTampering:
    """OAuth callback endpoints reject tampered, expired, and wrong-signature state tokens."""

    async def test_google_callback_tampered_state_returns_401(self, http_client: AsyncClient):
        """Garbage state string → Google callback returns 401 before touching OAuth."""
        res = await http_client.post(
            "/api/auth/oauth/google/callback",
            json={"code": "any-code", "state": _tampered_state()},
        )
        assert res.status_code == 401, (
            f"Expected 401 for tampered state, got {res.status_code}: {res.text}"
        )
        detail = res.json().get("detail", "").lower()
        assert "state" in detail or "invalid" in detail or "expired" in detail, (
            f"Detail does not mention state/invalid/expired: {detail}"
        )

    async def test_microsoft_callback_tampered_state_returns_401(self, http_client: AsyncClient):
        """Garbage state string → Microsoft callback returns 401 before touching OAuth."""
        res = await http_client.post(
            "/api/auth/oauth/microsoft/callback",
            json={"code": "any-code", "state": _tampered_state()},
        )
        assert res.status_code == 401, (
            f"Expected 401 for tampered state, got {res.status_code}: {res.text}"
        )

    async def test_google_callback_expired_state_returns_401(self, http_client: AsyncClient):
        """Expired but validly-signed state JWT → Google callback returns 401."""
        res = await http_client.post(
            "/api/auth/oauth/google/callback",
            json={"code": "any-code", "state": _expired_state()},
        )
        assert res.status_code == 401, (
            f"Expected 401 for expired state, got {res.status_code}: {res.text}"
        )

    async def test_microsoft_callback_expired_state_returns_401(self, http_client: AsyncClient):
        """Expired but validly-signed state JWT → Microsoft callback returns 401."""
        res = await http_client.post(
            "/api/auth/oauth/microsoft/callback",
            json={"code": "any-code", "state": _expired_state()},
        )
        assert res.status_code == 401, (
            f"Expected 401 for expired state, got {res.status_code}: {res.text}"
        )

    async def test_google_callback_wrong_signature_returns_401(self, http_client: AsyncClient):
        """Valid JWT structure but wrong signing secret → Google callback returns 401."""
        res = await http_client.post(
            "/api/auth/oauth/google/callback",
            json={"code": "any-code", "state": _wrong_signature_state()},
        )
        assert res.status_code == 401, (
            f"Expected 401 for wrong-signature state, got {res.status_code}: {res.text}"
        )
