"""
Tests for billing endpoints.

GET  /api/billing/plans            — public, no auth required
GET  /api/billing/{org_id}/usage   — requires auth + org membership
POST /api/billing/webhook          — public webhook placeholder
POST /api/billing/{org_id}/subscribe — requires owner role
"""

import uuid

import pytest
from httpx import AsyncClient


def _unique_slug() -> str:
    return f"billing-org-{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# /api/billing/plans
# ---------------------------------------------------------------------------


async def test_list_plans_returns_200(client: AsyncClient):
    """GET /api/billing/plans returns 200 without auth."""
    res = await client.get("/api/billing/plans")
    assert res.status_code == 200


async def test_list_plans_has_expected_plan_keys(client: AsyncClient):
    """Plans response includes at least 'free', 'starter', 'professional'."""
    res = await client.get("/api/billing/plans")
    data = res.json()
    assert isinstance(data, dict)
    assert "free" in data
    assert "starter" in data
    assert "professional" in data


async def test_list_plans_count(client: AsyncClient):
    """There are at least 3 billing plans."""
    res = await client.get("/api/billing/plans")
    plans = res.json()
    assert len(plans) >= 3


async def test_plan_has_required_fields(client: AsyncClient):
    """Each plan has queries_month, models, areas, multi_user."""
    res = await client.get("/api/billing/plans")
    for plan_name, plan_data in res.json().items():
        assert "queries_month" in plan_data, f"Plan {plan_name} missing queries_month"
        assert "models" in plan_data, f"Plan {plan_name} missing models"
        assert "areas" in plan_data, f"Plan {plan_name} missing areas"
        assert "multi_user" in plan_data, f"Plan {plan_name} missing multi_user"


async def test_free_plan_has_lower_limit_than_professional(client: AsyncClient):
    """The free plan has fewer monthly queries than the professional plan."""
    res = await client.get("/api/billing/plans")
    plans = res.json()
    assert plans["free"]["queries_month"] < plans["professional"]["queries_month"]


# ---------------------------------------------------------------------------
# /api/billing/{org_id}/usage
# ---------------------------------------------------------------------------


async def test_get_usage_without_auth_returns_401(client: AsyncClient):
    """GET usage without token returns 401."""
    fake_id = uuid.uuid4()
    res = await client.get(f"/api/billing/{fake_id}/usage")
    assert res.status_code in (401, 403)


async def test_get_usage_nonexistent_org_returns_error(auth_client: AsyncClient):
    """GET usage for an org the user is not a member of returns 403 or 404."""
    fake_id = uuid.uuid4()
    res = await auth_client.get(f"/api/billing/{fake_id}/usage")
    assert res.status_code in (403, 404)


async def test_get_usage_for_own_org(auth_client: AsyncClient):
    """GET usage for an org the user owns returns 200 with usage data."""
    create_res = await auth_client.post(
        "/api/organizations/",
        json={"name": "Billing Test Org", "slug": _unique_slug()},
    )
    assert create_res.status_code == 201
    org_id = create_res.json()["id"]

    usage_res = await auth_client.get(f"/api/billing/{org_id}/usage")
    assert usage_res.status_code == 200
    data = usage_res.json()
    assert "org_id" in data
    assert "total_queries" in data


# ---------------------------------------------------------------------------
# /api/billing/webhook
# ---------------------------------------------------------------------------


async def test_webhook_returns_200(client: AsyncClient):
    """POST /api/billing/webhook returns 200 regardless of payload."""
    res = await client.post(
        "/api/billing/webhook",
        content=b'{"type": "checkout.session.completed"}',
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 200


async def test_webhook_acknowledges_receipt(client: AsyncClient):
    """Webhook response body contains a received confirmation."""
    res = await client.post("/api/billing/webhook", content=b"{}")
    assert res.status_code == 200
    data = res.json()
    assert data.get("received") is True


async def test_webhook_empty_body_returns_200(client: AsyncClient):
    """Webhook with completely empty body still returns 200 (fail-safe)."""
    res = await client.post("/api/billing/webhook", content=b"")
    assert res.status_code == 200


# ---------------------------------------------------------------------------
# /api/billing/{org_id}/subscribe
# ---------------------------------------------------------------------------


async def test_subscribe_invalid_plan_returns_400(auth_client: AsyncClient):
    """Subscribing to an unknown plan returns 400."""
    create_res = await auth_client.post(
        "/api/organizations/",
        json={"name": "Sub Test Org", "slug": _unique_slug()},
    )
    org_id = create_res.json()["id"]

    res = await auth_client.post(
        f"/api/billing/{org_id}/subscribe",
        json={"plan": "nonexistent_plan"},
    )
    assert res.status_code == 400


async def test_subscribe_valid_plan(auth_client: AsyncClient):
    """Owner can upgrade their org to the starter plan."""
    create_res = await auth_client.post(
        "/api/organizations/",
        json={"name": "Sub Upgrade Org", "slug": _unique_slug()},
    )
    assert create_res.status_code == 201
    org_id = create_res.json()["id"]

    res = await auth_client.post(
        f"/api/billing/{org_id}/subscribe",
        json={"plan": "starter"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["plan"] == "starter"
    assert data["status"] == "active"
