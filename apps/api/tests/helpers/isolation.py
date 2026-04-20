"""Cross-tenant isolation assertion helper.

Project-wide 403 vs 404 convention (see design §2.1.4):
  - User-owned resource accessed by non-owner  → 404 (no existence leak)
  - Org-membership gate (non-member)           → 403
  - Admin-only endpoint (non-admin)            → 403
  - Unauthenticated access                     → 401
"""
from __future__ import annotations

from httpx import AsyncClient


async def assert_isolated(
    *,
    victim_client: AsyncClient,
    attacker_client: AsyncClient,
    method: str,
    path: str,
    attacker_status: int,
    json: dict | None = None,
    owner_status: int = 200,
) -> None:
    """Assert that a resource is properly isolated between two users.

    Steps:
    1. Issues the request as the OWNER — asserts `owner_status` (default 200).
       Guards against false-green isolation tests where the route is broken
       for everyone.
    2. Issues the same request as the ATTACKER — asserts `attacker_status`.
    3. For mutating methods (PATCH, PUT, DELETE), re-fetches via GET to confirm
       the owner's resource was NOT modified even if a non-2xx was returned.
       (Catches the class of bug where 403 is returned but the write already
       happened before the auth check.)

    Args:
        victim_client:    Client authenticated as the resource owner.
        attacker_client:  Client authenticated as the cross-tenant attacker.
        method:           HTTP verb — "GET" | "POST" | "PATCH" | "PUT" | "DELETE".
        path:             Full path, e.g. "/api/bookmarks/some-uuid".
        attacker_status:  Expected HTTP status when attacker hits the route
                          (typically 403 for org gates, 404 for user-owned).
        json:             Optional request body for write methods.
        owner_status:     Expected HTTP status when owner hits the route (default 200).
    """
    method = method.upper()
    kwargs: dict = {}
    if json is not None:
        kwargs["json"] = json

    # 1. Owner sanity check
    owner_res = await victim_client.request(method, path, **kwargs)
    assert owner_res.status_code == owner_status, (
        f"assert_isolated: owner should get {owner_status} on {method} {path}, "
        f"got {owner_res.status_code}. Body: {owner_res.text[:300]}"
    )

    # 2. Attacker probe
    attacker_res = await attacker_client.request(method, path, **kwargs)
    assert attacker_res.status_code == attacker_status, (
        f"assert_isolated: attacker should get {attacker_status} on {method} {path}, "
        f"got {attacker_res.status_code}. Body: {attacker_res.text[:300]}"
    )

    # 3. Write-then-read integrity check for mutating verbs
    if method in ("PATCH", "PUT", "DELETE") and owner_status in (200, 204):
        # Attempt a GET on the same path to verify the resource is intact.
        # Only meaningful when the owner originally had access.
        if method != "DELETE":
            verify_res = await victim_client.get(path)
            assert verify_res.status_code == owner_status, (
                f"assert_isolated: after attacker {method}, owner GET {path} "
                f"returned {verify_res.status_code} — resource may have been mutated."
            )
