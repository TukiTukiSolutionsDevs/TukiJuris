"""Organization factory — creates orgs and manages membership via the HTTP surface."""
from __future__ import annotations

import re
import uuid

from httpx import AsyncClient


def _slugify(name: str) -> str:
    """Convert a display name to a URL-safe slug (lowercase, hyphens only)."""
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


async def make_org(
    client: AsyncClient,
    *,
    name: str | None = None,
    slug: str | None = None,
) -> dict:
    """Create an organization. The client must be authenticated (Bearer token set).

    Returns: {org_id, name, slug}

    A slug is generated automatically from the name + a random suffix when not
    provided, satisfying the OrgCreate schema requirement for a URL-safe slug.
    """
    name = name or f"Test Org {uuid.uuid4().hex[:6]}"
    if slug is None:
        base = _slugify(name)
        slug = f"{base}-{uuid.uuid4().hex[:6]}"
    res = await client.post("/api/organizations/", json={"name": name, "slug": slug})
    assert res.status_code == 201, f"make_org failed: {res.status_code} {res.text}"
    data = res.json()
    return {"org_id": data["id"], "name": data["name"], "slug": data["slug"]}


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
