"""auth.unit.002 — PUT /api/auth/me rejects invalid data with HTTP 422.

Spec: auth.unit.002 — test_profile_update_validation_rejected
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestAuthMeValidation:
    async def test_profile_update_validation_rejected(self, auth_client: AsyncClient) -> None:
        """PUT /api/auth/me with an invalid default_org_id (non-UUID) must return 422.

        UpdateProfileBody exposes default_org_id: uuid.UUID | None. Sending a
        non-UUID string triggers Pydantic validation and FastAPI returns 422
        Unprocessable Entity.
        """
        res = await auth_client.put(
            "/api/auth/me",
            json={"default_org_id": "this-is-not-a-uuid"},
        )
        assert res.status_code == 422, (
            f"Expected 422 for invalid default_org_id, got {res.status_code}: {res.text}"
        )
        error_body = res.json()
        # FastAPI/Pydantic v2 returns {"detail": [...]} on validation failure
        assert "detail" in error_body, f"422 response missing 'detail' field: {error_body}"
