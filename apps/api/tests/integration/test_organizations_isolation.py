"""Organizations cross-tenant isolation and role-enforcement tests.

Spec: openspec/changes/backend-saas-test-coverage/specs/organizations.md §3
Design: §2.1.4 — org-membership gates return 403 (not 404).

orgs.int.001 — test_org_remove_member
orgs.int.002 — test_org_member_cannot_update_org
orgs.int.003 — test_org_owner_self_removal_rejected
orgs.int.004 — test_org_cross_tenant_read_403
"""
from __future__ import annotations

import pytest

from tests.factories.org import add_member


# ---------------------------------------------------------------------------
# Cross-tenant isolation — org-membership gate → 403
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_org_cross_tenant_read_403(tenant_pair):
    """orgs.int.004 — Non-member cannot GET another org's details."""
    org_a_id = tenant_pair.org_a["org_id"]
    res = await tenant_pair.client_b.get(f"/api/organizations/{org_a_id}")
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"


@pytest.mark.asyncio
async def test_org_cross_tenant_list_members_403(tenant_pair):
    """Non-member cannot list members of another org."""
    org_a_id = tenant_pair.org_a["org_id"]
    res = await tenant_pair.client_b.get(f"/api/organizations/{org_a_id}/members")
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"


@pytest.mark.asyncio
async def test_org_cross_tenant_invite_403(tenant_pair):
    """Non-member cannot invite users into another org."""
    org_a_id = tenant_pair.org_a["org_id"]
    res = await tenant_pair.client_b.post(
        f"/api/organizations/{org_a_id}/invite",
        json={"email": "outsider@example.com", "role": "member"},
    )
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"


@pytest.mark.asyncio
async def test_org_cross_tenant_remove_member_403(tenant_pair):
    """Non-member cannot remove members from another org.

    The role check fires before the target-member lookup, so any UUID suffices
    for the path parameter — the route returns 403 immediately.
    """
    import uuid

    org_a_id = tenant_pair.org_a["org_id"]
    random_uid = str(uuid.uuid4())
    res = await tenant_pair.client_b.delete(
        f"/api/organizations/{org_a_id}/members/{random_uid}"
    )
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"


# ---------------------------------------------------------------------------
# Role enforcement within the same org
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_org_member_cannot_update_org(tenant_pair):
    """orgs.int.002 — A standard member (not owner/admin) cannot update org settings.

    Setup: invite owner_b into org_a as 'member', then attempt PUT as owner_b.
    The route requires owner or admin role — member role yields 403.
    """
    org_a_id = tenant_pair.org_a["org_id"]
    owner_b_email = tenant_pair.owner_b["email"]

    # Invite user_b into org_a as a plain member
    await add_member(
        tenant_pair.client_a,
        org_id=org_a_id,
        email=owner_b_email,
        role="member",
    )

    # user_b IS now a member of org_a, but only with 'member' role → PUT must 403
    res = await tenant_pair.client_b.put(
        f"/api/organizations/{org_a_id}",
        json={"name": "Injected Name"},
    )
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"


# ---------------------------------------------------------------------------
# Member lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_org_remove_member(tenant_pair):
    """orgs.int.001 — Org owner can remove a member via DELETE; member disappears from list."""
    org_a_id = tenant_pair.org_a["org_id"]
    owner_b_email = tenant_pair.owner_b["email"]

    # Invite owner_b into org_a as a plain member
    membership = await add_member(
        tenant_pair.client_a,
        org_id=org_a_id,
        email=owner_b_email,
        role="member",
    )
    member_user_id = str(membership["user_id"])

    # Owner A removes user B
    res = await tenant_pair.client_a.delete(
        f"/api/organizations/{org_a_id}/members/{member_user_id}"
    )
    assert res.status_code == 204, f"Expected 204, got {res.status_code}: {res.text}"

    # Verify user B is no longer listed
    members_res = await tenant_pair.client_a.get(f"/api/organizations/{org_a_id}/members")
    assert members_res.status_code == 200
    listed_ids = [m["user_id"] for m in members_res.json()]
    assert member_user_id not in listed_ids, "Removed member still appears in members list"


@pytest.mark.asyncio
async def test_org_owner_self_removal_rejected(tenant_pair):
    """orgs.int.003 — Sole org owner cannot remove themselves.

    The members endpoint returns the owner's membership row; we use it to obtain
    the owner's user_id without an explicit /me endpoint.
    """
    org_a_id = tenant_pair.org_a["org_id"]

    # Resolve owner A's user_id via the members list
    members_res = await tenant_pair.client_a.get(f"/api/organizations/{org_a_id}/members")
    assert members_res.status_code == 200
    members = members_res.json()
    assert len(members) == 1, "Expected only the owner in a freshly created org"
    owner_a_user_id = members[0]["user_id"]

    # Sole owner tries to delete themselves → must be rejected
    res = await tenant_pair.client_a.delete(
        f"/api/organizations/{org_a_id}/members/{owner_a_user_id}"
    )
    assert res.status_code in (400, 403), (
        f"Expected 400 or 403 for sole-owner self-removal, got {res.status_code}: {res.text}"
    )
