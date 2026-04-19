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
    """Plans response includes the canonical plan IDs: free, pro, studio.

    Post plan-model-refactor (Sprint 2): legacy 'starter'/'professional' IDs
    were renamed to pro/studio; 'free' stays.
    """
    res = await client.get("/api/billing/plans")
    data = res.json()
    assert isinstance(data, dict)
    assert "free" in data
    assert "pro" in data
    assert "studio" in data


async def test_list_plans_count(client: AsyncClient):
    """There are at least 3 billing plans."""
    res = await client.get("/api/billing/plans")
    plans = res.json()
    assert len(plans) >= 3


async def test_plan_has_required_fields(client: AsyncClient):
    """Each plan has daily_limit, description, areas, multi_user.

    Post fix-usage-limit-schema (Sprint 1): weekly/monthly caps replaced by
    a unified daily_limit. -1 signals unlimited for pro/studio.
    """
    res = await client.get("/api/billing/plans")
    for plan_name, plan_data in res.json().items():
        assert "daily_limit" in plan_data, f"Plan {plan_name} missing daily_limit"
        assert "description" in plan_data, f"Plan {plan_name} missing description"
        assert "areas" in plan_data, f"Plan {plan_name} missing areas"
        assert "multi_user" in plan_data, f"Plan {plan_name} missing multi_user"


async def test_free_plan_has_lower_limit_than_studio(client: AsyncClient):
    """Free daily cap (10) is stricter than studio (-1 = unlimited)."""
    res = await client.get("/api/billing/plans")
    plans = res.json()
    free_limit = plans["free"]["daily_limit"]
    studio_limit = plans["studio"]["daily_limit"]
    # studio is unlimited (-1) — treat as "greater than any finite cap"
    assert studio_limit == -1 or free_limit < studio_limit
    assert free_limit == 10  # canonical per BETA_HARD_LIMITS


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
# /api/billing/webhook/mp  (payment-hardening replaced the single-webhook
# endpoint with provider-specific routes: /webhook/mp and /webhook/culqi)
# ---------------------------------------------------------------------------


async def test_mp_webhook_returns_400_on_missing_event_id(client: AsyncClient):
    """Webhooks are always active; payload without 'id' field returns 400 (AC12).

    Updated: webhooks no longer gate on provider configuration. They process all
    requests and return 400 when required fields (event_id) are missing.
    """
    res = await client.post(
        "/api/billing/webhook/mp",
        content=b'{"type": "payment"}',
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 400


async def test_culqi_webhook_returns_400_on_empty_body(client: AsyncClient):
    """Webhooks are always active; empty/missing 'id' returns 400 (AC12).

    Updated: webhooks no longer gate on provider configuration.
    """
    res = await client.post(
        "/api/billing/webhook/culqi",
        content=b"{}",
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 400


async def test_legacy_webhook_path_is_gone(client: AsyncClient):
    """The pre-payment-hardening single endpoint /api/billing/webhook must 404.

    Kept as a regression guard: if someone re-adds a catch-all webhook, the
    HMAC-specific guards on /webhook/mp and /webhook/culqi lose their meaning.
    """
    res = await client.post("/api/billing/webhook", content=b"{}")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# /api/billing/{org_id}/subscribe
# ---------------------------------------------------------------------------


async def test_subscribe_invalid_plan_returns_400(auth_client: AsyncClient):
    """Subscribing to an unknown plan returns 400 (or 503 when no provider configured).

    The checkout endpoint validates the plan before creating a session.
    In environments without a payment provider, the 503 check fires first;
    in configured environments the plan check fires and returns 400.
    """
    create_res = await auth_client.post(
        "/api/organizations/",
        json={"name": "Sub Test Org", "slug": _unique_slug()},
    )
    org_id = create_res.json()["id"]

    res = await auth_client.post(
        f"/api/billing/{org_id}/checkout",
        json={"plan": "nonexistent_plan"},
    )
    # 400 when provider is configured (plan validation), 503 when not (provider check first)
    assert res.status_code in (400, 503), res.text


async def test_subscribe_valid_plan(auth_client: AsyncClient):
    """Checkout endpoint accepts a canonical plan and returns checkout_url or 503 (no provider)."""
    create_res = await auth_client.post(
        "/api/organizations/",
        json={"name": "Sub Upgrade Org", "slug": _unique_slug()},
    )
    assert create_res.status_code == 201
    org_id = create_res.json()["id"]

    res = await auth_client.post(
        f"/api/billing/{org_id}/checkout",
        json={"plan": "pro"},
    )
    # 200 + checkout_url when provider configured; 503 when not (dev/test environment)
    assert res.status_code in (200, 503), res.text
    if res.status_code == 200:
        data = res.json()
        assert "checkout_url" in data
        assert "provider" in data
