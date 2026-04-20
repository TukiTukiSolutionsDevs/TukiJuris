"""Organization factory — creates orgs and manages membership via the HTTP surface."""
from __future__ import annotations

import uuid

from httpx import AsyncClient


async def make_org(
    client: AsyncClient,
    *,
    name: str | None = None,
) -> dict:
    """Create an organization. The client must be authenticated (Bearer token set).

    Returns: {org_id, name}
    """
    name = name or f"Test Org {uuid.uuid4().hex[:6]}"
    res = await client.post("/api/organizations/", json={"name": name})
    assert res.status_code == 201, f"make_org failed: {res.status_code} {res.text}"
    data = res.json()
    return {"org_id": data["id"], "name": data["name"]}


async def add_member(
    client: AsyncClient,
    *,
    org_id: str,
    email: str,
    role: str = "member",
) -> dict:
    """Invite a user to an org. The client must be owner or admin.

    Returns the membership response dict.
    """
    res = await client.post(
        f"/api/organizations/{org_id}/invite",
        json={"email": email, "role": role},
    )
    assert res.status_code == 201, f"add_member failed: {res.status_code} {res.text}"
    return res.json()
