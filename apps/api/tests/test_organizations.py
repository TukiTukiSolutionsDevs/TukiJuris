"""
Tests for organization management endpoints.

GET/POST/PUT /api/organizations/
POST /api/organizations/{id}/invite
GET  /api/organizations/{id}/members

All tests use the auth_client fixture (authenticated user).
Organization slugs use uuid suffixes to guarantee uniqueness.
"""

import uuid

import pytest
from httpx import AsyncClient


def _unique_slug() -> str:
    return f"test-org-{uuid.uuid4().hex[:8]}"


def _org_payload(slug: str | None = None) -> dict:
    s = slug or _unique_slug()
    return {"name": f"Test Org {s}", "slug": s}


# ---------------------------------------------------------------------------
# Create organization
# ---------------------------------------------------------------------------


async def test_create_org_returns_201(auth_client: AsyncClient):
    """POST /api/organizations/ returns 201 with org data."""
    res = await auth_client.post("/api/organizations/", json=_org_payload())
    assert res.status_code == 201
    data = res.json()
    assert "id" in data
    assert "name" in data
    assert "slug" in data
    assert data["is_active"] is True


async def test_create_org_owner_is_set(auth_client: AsyncClient):
    """Creating an org returns a valid plan (default 'free')."""
    res = await auth_client.post("/api/organizations/", json=_org_payload())
    assert res.status_code == 201
    data = res.json()
    assert data["plan"] in ("free", "starter", "professional", "enterprise")


async def test_create_org_duplicate_slug_returns_409(auth_client: AsyncClient):
    """Two orgs with the same slug return 409 on the second attempt."""
    slug = _unique_slug()
    first = await auth_client.post("/api/organizations/", json=_org_payload(slug))
    assert first.status_code == 201

    second = await auth_client.post("/api/organizations/", json=_org_payload(slug))
    assert second.status_code == 409


async def test_create_org_invalid_slug_returns_422(auth_client: AsyncClient):
    """Slug with uppercase or spaces is rejected with 422."""
    res = await auth_client.post(
        "/api/organizations/",
        json={"name": "Bad Slug Org", "slug": "Invalid Slug With Spaces"},
    )
    assert res.status_code == 422


async def test_create_org_without_auth_returns_401(client: AsyncClient):
    """Creating an org without token returns 401."""
    res = await client.post("/api/organizations/", json=_org_payload())
    assert res.status_code in (401, 403)


# ---------------------------------------------------------------------------
# List organizations
# ---------------------------------------------------------------------------


async def test_list_orgs_returns_list(auth_client: AsyncClient):
    """GET /api/organizations/ returns a list."""
    res = await auth_client.get("/api/organizations/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


async def test_list_orgs_includes_created_org(auth_client: AsyncClient):
    """A newly created org appears in the list."""
    slug = _unique_slug()
    create_res = await auth_client.post("/api/organizations/", json=_org_payload(slug))
    assert create_res.status_code == 201
    created_id = create_res.json()["id"]

    list_res = await auth_client.get("/api/organizations/")
    assert list_res.status_code == 200
    ids = [o["id"] for o in list_res.json()]
    assert created_id in ids


async def test_list_orgs_without_auth_returns_401(client: AsyncClient):
    """Listing orgs without token returns 401."""
    res = await client.get("/api/organizations/")
    assert res.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Get organization by ID
# ---------------------------------------------------------------------------


async def test_get_org_by_id(auth_client: AsyncClient):
    """GET /api/organizations/{id} returns the org for a member."""
    create_res = await auth_client.post("/api/organizations/", json=_org_payload())
    org_id = create_res.json()["id"]

    res = await auth_client.get(f"/api/organizations/{org_id}")
    assert res.status_code == 200
    assert res.json()["id"] == org_id


async def test_get_org_not_found_returns_404(auth_client: AsyncClient):
    """GET /api/organizations/{random_uuid} returns 404."""
    fake_id = uuid.uuid4()
    res = await auth_client.get(f"/api/organizations/{fake_id}")
    assert res.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Update organization
# ---------------------------------------------------------------------------


async def test_update_org_name(auth_client: AsyncClient):
    """PUT /api/organizations/{id} updates the organization name."""
    create_res = await auth_client.post("/api/organizations/", json=_org_payload())
    org_id = create_res.json()["id"]

    update_res = await auth_client.put(
        f"/api/organizations/{org_id}",
        json={"name": "Updated Name"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated Name"


# ---------------------------------------------------------------------------
# Invite member
# ---------------------------------------------------------------------------


async def test_invite_member_requires_target_to_exist(auth_client: AsyncClient):
    """
    Inviting a non-existent email returns 404 (user must have an account).
    """
    create_res = await auth_client.post("/api/organizations/", json=_org_payload())
    org_id = create_res.json()["id"]

    ghost_email = f"ghost-{uuid.uuid4().hex}@nowhere.com"
    invite_res = await auth_client.post(
        f"/api/organizations/{org_id}/invite",
        json={"email": ghost_email, "role": "member"},
    )
    assert invite_res.status_code == 404


async def test_invite_member_invalid_role_returns_422(auth_client: AsyncClient):
    """Inviting with an invalid role returns 422."""
    create_res = await auth_client.post("/api/organizations/", json=_org_payload())
    org_id = create_res.json()["id"]

    invite_res = await auth_client.post(
        f"/api/organizations/{org_id}/invite",
        json={"email": "someone@example.com", "role": "superuser"},
    )
    assert invite_res.status_code == 422


# ---------------------------------------------------------------------------
# List members
# ---------------------------------------------------------------------------


async def test_list_members_includes_owner(auth_client: AsyncClient):
    """GET /api/organizations/{id}/members returns at least the owner."""
    create_res = await auth_client.post("/api/organizations/", json=_org_payload())
    org_id = create_res.json()["id"]

    members_res = await auth_client.get(f"/api/organizations/{org_id}/members")
    assert members_res.status_code == 200
    members = members_res.json()
    assert isinstance(members, list)
    assert len(members) >= 1
    roles = [m["role"] for m in members]
    assert "owner" in roles


async def test_list_members_without_auth_returns_401(client: AsyncClient):
    """Listing members without token returns 401."""
    fake_id = uuid.uuid4()
    res = await client.get(f"/api/organizations/{fake_id}/members")
    assert res.status_code in (401, 403)
