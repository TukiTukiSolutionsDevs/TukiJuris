"""auth.unit.001 — GET /api/auth/sessions returns correct shape.

Spec: auth.unit.001 — test_auth_sessions_list_shape
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestAuthSessions:
    async def test_auth_sessions_list_shape(self, auth_client: AsyncClient) -> None:
        """GET /api/auth/sessions returns 200 with a list of session objects.

        The list must contain at least the current session (registered by the
        auth_client fixture). Each entry must have the fields documented in
        the SessionResponse schema.
        """
        res = await auth_client.get("/api/auth/sessions")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

        data = res.json()
        assert isinstance(data, list), "Response should be a list of sessions"
        assert len(data) >= 1, "At least the current session should be present"

        # Validate shape of the first session — SessionResponse schema
        # (apps/api/app/api/routes/auth.py:93)
        session = data[0]
        for field in ("jti", "family_id", "created_at", "expires_at"):
            assert field in session, (
                f"SessionResponse missing field '{field}'. Got keys: {list(session.keys())}"
            )
