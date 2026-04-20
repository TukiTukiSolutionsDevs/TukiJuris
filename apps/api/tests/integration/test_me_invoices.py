"""Integration tests — invoice access control (billing.int.001).

Verifies GET /api/billing/{org_id}/invoices enforces org membership:
  - Non-member → 403
  - Owner → 200
  - Unauthenticated → 401

Requirements: live PostgreSQL + Redis (docker-compose up), alembic upgrade head.

Run:
    docker exec tukijuris-api-1 pytest tests/integration/test_me_invoices.py -v
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _register(client: AsyncClient, tag: str = "") -> tuple[str, str]:
    """Register a unique user. Returns (access_token, email)."""
    email = f"inv-{tag}-{uuid.uuid4().hex[:8]}@test.com"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "TestPass123!", "full_name": "Invoice Tester"},
    )
    assert res.status_code in (200, 201), f"Register failed: {res.status_code} {res.text}"
    return res.json()["access_token"], email


async def _create_org(client: AsyncClient, token: str) -> str:
    """Create an org for the authenticated user. Returns org_id str."""
    suffix = uuid.uuid4().hex[:8]
    res = await client.post(
        "/api/organizations/",
        json={"name": f"TestOrg-{suffix}", "slug": f"testorg-{suffix}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code in (200, 201), f"Org creation failed: {res.status_code} {res.text}"
    return res.json()["id"]


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


# ---------------------------------------------------------------------------
# billing.int.001 — access control
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestMeInvoicesAccessControl:
    """billing.int.001 — GET /billing/{org_id}/invoices enforces membership."""

    async def test_non_member_gets_403(self, http_client: AsyncClient):
        """User B cannot list invoices for User A's org."""
        token_a, _ = await _register(http_client, "a")
        token_b, _ = await _register(http_client, "b")
        org_id = await _create_org(http_client, token_a)

        res = await http_client.get(
            f"/api/billing/{org_id}/invoices",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"

    async def test_owner_gets_200_empty_list(self, http_client: AsyncClient):
        """Org owner can list invoices — empty list is a valid 200 response."""
        token, _ = await _register(http_client, "owner")
        org_id = await _create_org(http_client, token)

        res = await http_client.get(
            f"/api/billing/{org_id}/invoices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        body = res.json()
        assert "items" in body
        assert "total" in body
        assert isinstance(body["items"], list)

    async def test_unauthenticated_gets_401(self, http_client: AsyncClient):
        """No token → 401 before membership check."""
        fake_org = str(uuid.uuid4())
        res = await http_client.get(f"/api/billing/{fake_org}/invoices")
        assert res.status_code == 401, f"Expected 401, got {res.status_code}"
