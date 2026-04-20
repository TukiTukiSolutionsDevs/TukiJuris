"""Developer API key factory — creates keys via POST /api/keys/."""
from __future__ import annotations

import uuid

from httpx import AsyncClient

VALID_SCOPES = {"query", "search", "analyze", "documents"}


async def make_api_key(
    auth_client: AsyncClient,
    *,
    name: str | None = None,
    scopes: list[str] | None = None,
) -> dict:
    """Create a developer API key via the HTTP surface.

    Returns: {key_id, raw_token, scopes}
    raw_token is only returned at creation time — store it immediately.
    """
    if scopes is None:
        scopes = ["query", "search"]
    name = name or f"test-key-{uuid.uuid4().hex[:6]}"
    res = await auth_client.post(
        "/api/keys/",
        json={"name": name, "scopes": scopes},
    )
    assert res.status_code == 201, f"make_api_key failed: {res.status_code} {res.text}"
    data = res.json()
    # APIKeyCreated extends APIKeyResponse; raw key is in "key" field
    raw_token = data.get("key") or data.get("raw_key") or data.get("full_key")
    return {
        "key_id": data["id"],
        "raw_token": raw_token,
        "scopes": data.get("scopes", scopes),
        "prefix": data.get("prefix"),
    }
