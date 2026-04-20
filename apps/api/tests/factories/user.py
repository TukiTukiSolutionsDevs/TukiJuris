"""User factory — creates users via POST /api/auth/register."""
from __future__ import annotations

import uuid

from httpx import AsyncClient


async def make_user(
    client: AsyncClient,
    *,
    plan: str = "free",  # noqa: ARG001 — accepted for API compat, plan set by subscription service
    is_admin: bool = False,  # noqa: ARG001 — accepted for API compat, set via DB outside factory
) -> dict:
    """Register a fresh test user and return auth context.

    Returns: {email, password, access_token, refresh_token}

    plan and is_admin are accepted for call-site symmetry; promotion requires
    separate service-layer calls outside this factory's scope.
    """
    email = f"user-{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPassword123!"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert res.status_code in (200, 201), f"make_user failed: {res.status_code} {res.text}"
    data = res.json()
    return {
        "email": email,
        "password": password,
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token"),
    }
