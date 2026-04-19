"""
Tests for authentication endpoints.

POST /api/auth/register — create account, receive JWT
POST /api/auth/login    — get JWT with valid credentials

All tests use unique UUIDs in emails to guarantee isolation even when
the DB persists across runs.
"""

import uuid

import pytest
from httpx import AsyncClient


def _unique_email() -> str:
    """Generate a unique email address for test isolation."""
    return f"test-{uuid.uuid4().hex[:12]}@example.com"


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


async def test_register_success(client: AsyncClient):
    """Valid registration returns 201 with access_token in body and refresh_token as httpOnly cookie.

    Post-Sprint-1 (fix-auth-tokens): refresh_token lives in an httpOnly cookie,
    NOT the response body. The pair contract is: access_token in body, refresh
    token in `refresh_token` cookie (path=/api/auth) + `tk_session` (path=/).
    """
    res = await client.post(
        "/api/auth/register",
        json={
            "email": _unique_email(),
            "password": "SecurePass123!",
            "full_name": "Integration Test User",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 10
    # Refresh token lives in an httpOnly cookie now (Sprint 1 fix-auth-tokens).
    assert "refresh_token" in res.cookies


async def test_register_returns_valid_jwt(client: AsyncClient):
    """The access token returned by register is a well-formed JWT (3 dot-separated parts)."""
    res = await client.post(
        "/api/auth/register",
        json={
            "email": _unique_email(),
            "password": "SecurePass123!",
            "full_name": "JWT Check",
        },
    )
    assert res.status_code == 201
    data = res.json()
    token = data["access_token"]
    parts = token.split(".")
    assert len(parts) == 3, "access_token must have 3 dot-separated parts (header.payload.signature)"


async def test_register_duplicate_email_returns_409(client: AsyncClient):
    """Registering the same email twice returns 409."""
    email = _unique_email()
    payload = {"email": email, "password": "SecurePass123!", "full_name": "Dup User"}

    first = await client.post("/api/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/auth/register", json=payload)
    assert second.status_code == 409
    assert "already" in second.json()["detail"].lower()


async def test_register_without_full_name(client: AsyncClient):
    """full_name is optional — registration succeeds without it."""
    res = await client.post(
        "/api/auth/register",
        json={"email": _unique_email(), "password": "SecurePass123!"},
    )
    assert res.status_code == 201
    assert "access_token" in res.json()


async def test_register_invalid_email_format_returns_422(client: AsyncClient):
    """Invalid email format is rejected with 422 Unprocessable Entity."""
    res = await client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "SecurePass123!"},
    )
    assert res.status_code == 422


async def test_register_missing_email_returns_422(client: AsyncClient):
    """Missing email field returns 422."""
    res = await client.post(
        "/api/auth/register",
        json={"password": "SecurePass123!", "full_name": "No Email"},
    )
    assert res.status_code == 422


async def test_register_missing_password_returns_422(client: AsyncClient):
    """Missing password field returns 422."""
    res = await client.post(
        "/api/auth/register",
        json={"email": _unique_email(), "full_name": "No Password"},
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


async def test_login_success(client: AsyncClient):
    """Valid login returns 200 with access_token in body and refresh_token as httpOnly cookie."""
    email = _unique_email()
    password = "LoginTest456!"

    await client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )

    res = await client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # Refresh token lives in an httpOnly cookie now (Sprint 1 fix-auth-tokens).
    assert "refresh_token" in res.cookies


async def test_login_wrong_password_returns_401(client: AsyncClient):
    """Login with wrong password returns 401."""
    email = _unique_email()

    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "CorrectPass789!"},
    )

    res = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "WrongPassword"},
    )
    assert res.status_code == 401
    assert "credentials" in res.json()["detail"].lower()


async def test_login_nonexistent_email_returns_401(client: AsyncClient):
    """Login with an email that was never registered returns 401."""
    res = await client.post(
        "/api/auth/login",
        json={"email": f"ghost-{uuid.uuid4().hex}@nowhere.com", "password": "Irrelevant1!"},
    )
    assert res.status_code == 401


async def test_login_invalid_email_format_returns_422(client: AsyncClient):
    """Login with malformed email returns 422."""
    res = await client.post(
        "/api/auth/login",
        json={"email": "not-an-email", "password": "SomePass123!"},
    )
    assert res.status_code == 422


async def test_login_missing_fields_returns_422(client: AsyncClient):
    """Login with empty body returns 422."""
    res = await client.post("/api/auth/login", json={})
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Token usability
# ---------------------------------------------------------------------------


async def test_token_can_authenticate_conversations_endpoint(client: AsyncClient):
    """
    A token obtained from login can be used on a protected endpoint.
    We use GET /api/conversations/ which requires auth and returns 200
    (empty list is fine — it means the token is valid).
    """
    email = _unique_email()
    password = "TokenTest123!"

    await client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )

    login_res = await client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["access_token"]

    protected_res = await client.get(
        "/api/conversations/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert protected_res.status_code == 200


async def test_no_token_returns_401_on_protected_endpoint(client: AsyncClient):
    """Requests to protected endpoints without a token return 401 or 403."""
    res = await client.get("/api/conversations/")
    assert res.status_code in (401, 403)
