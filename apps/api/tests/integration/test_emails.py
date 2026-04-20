"""Integration tests — password-reset email flow (sub-batch D.4b).

Spec IDs:
  notifications.unit.009  test_email_password_reset_request_flow
  notifications.unit.010  test_email_password_reset_confirm_flow  [XFAIL — no token blacklist]

Routes exercised:
  POST /api/auth/password-reset         → 202
  POST /api/auth/password-reset/confirm → 200 | 400

Token invalidation is JWT-only with no server-side blacklist — a second use of
the same reset token succeeds. test_010 is XFAIL(strict=True) until a
token-denylist for password-reset JWTs is implemented.

Run:
  docker exec tukijuris-api-1 pytest tests/integration/test_emails.py -v --tb=short
"""
from __future__ import annotations

import re
import uuid

import pytest
from httpx import AsyncClient

from app.config import settings
from app.services.email_service import email_service
from tests.mocks.email import MockEmailProvider


# ---------------------------------------------------------------------------
# notifications.unit.009 — request flow sends email
# ---------------------------------------------------------------------------


async def test_email_password_reset_request_flow(client: AsyncClient, monkeypatch) -> None:
    """Spec: notifications.unit.009

    POST /api/auth/password-reset → 202 + mock provider captures the reset email.
    """
    mock = MockEmailProvider()
    monkeypatch.setattr(email_service, "_provider", mock)
    monkeypatch.setattr(settings, "email_enabled", True)

    email = f"reset-{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "TestPassword123!", "full_name": "Reset User"},
    )

    res = await client.post("/api/auth/password-reset", json={"email": email})
    assert res.status_code == 202, f"Expected 202, got {res.status_code}: {res.text[:200]}"

    assert mock.last_sent is not None, "Mock provider captured no outbound email"
    subj = mock.last_sent.subject.lower()
    assert "contrasena" in subj or "reset" in subj, f"Unexpected subject: {mock.last_sent.subject!r}"


# ---------------------------------------------------------------------------
# notifications.unit.010 — confirm flow + token reuse rejected
# ---------------------------------------------------------------------------


@pytest.mark.xfail(strict=True, reason="No reset-token denylist — same JWT accepted on reuse")
async def test_email_password_reset_confirm_flow(client: AsyncClient, monkeypatch) -> None:
    """Spec: notifications.unit.010

    Confirm reset → password changed + new credentials work for login.
    Second use of same token → 400 (XFAIL: token blacklist not implemented).
    """
    mock = MockEmailProvider()
    monkeypatch.setattr(email_service, "_provider", mock)
    monkeypatch.setattr(settings, "email_enabled", True)

    email = f"confirm-{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/auth/register",
        json={"email": email, "password": "TestPassword123!", "full_name": "Confirm User"},
    )
    await client.post("/api/auth/password-reset", json={"email": email})
    assert mock.last_sent is not None, "No reset email captured"

    token_match = re.search(r"token=([^\"&\s<]+)", mock.last_sent.html)
    assert token_match, "Token not found in reset email HTML"
    token = token_match.group(1)

    res = await client.post(
        "/api/auth/password-reset/confirm",
        json={"token": token, "new_password": "NewPassword456!"},
    )
    assert res.status_code == 200, f"Confirm failed: {res.status_code} {res.text[:200]}"

    login = await client.post(
        "/api/auth/login", json={"email": email, "password": "NewPassword456!"}
    )
    assert login.status_code == 200, "New password does not work for login"

    # Token reuse — should be 400 but returns 200 (no blacklist) → xfail fires here
    res2 = await client.post(
        "/api/auth/password-reset/confirm",
        json={"token": token, "new_password": "AnotherPass789!"},
    )
    assert res2.status_code == 400, f"Expected 400 on token reuse, got {res2.status_code}"
