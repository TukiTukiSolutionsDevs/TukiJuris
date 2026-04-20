"""Integration tests — RBAC admin assign/revoke role lifecycle.

Spec IDs: admin-rbac.int.004, admin-rbac.int.005
Layer: integration

Full lifecycle: assign a role to a user via POST /api/admin/users/{id}/roles,
verify the permissions endpoint returns the role's permissions (200), then
revoke via DELETE and assert 204.

Run: docker exec tukijuris-api-1 pytest apps/api/tests/integration/test_rbac_admin.py -v
"""
from __future__ import annotations

import uuid

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app


# ---------------------------------------------------------------------------
# DB helpers — mirrors test_admin_saas_panel.py pattern
# ---------------------------------------------------------------------------


async def _db_connect() -> asyncpg.Connection:
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    return await asyncpg.connect(db_url)


async def _register(client: AsyncClient, prefix: str = "rbac") -> tuple[str, str]:
    """Register a fresh test user; return (access_token, email)."""
    email = f"{prefix}-{uuid.uuid4().hex[:8]}@test.com"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "TestPass123!", "full_name": "RBAC Tester"},
    )
    assert res.status_code in (200, 201), f"Register failed: {res.status_code} {res.text}"
    return res.json()["access_token"], email


async def _make_super_admin(email: str) -> None:
    """Grant is_admin=True and assign the super_admin role by email."""
    try:
        conn = await _db_connect()
    except Exception as exc:
        pytest.skip(f"DB unreachable: {exc}")
    try:
        user_id = await conn.fetchval("SELECT id FROM users WHERE email = $1", email)
        role_id = await conn.fetchval("SELECT id FROM roles WHERE name = 'super_admin'")
        if role_id is None:
            pytest.skip("'super_admin' role not seeded — run alembic upgrade head")
        await conn.execute("UPDATE users SET is_admin = true WHERE id = $1", user_id)
        await conn.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            user_id,
            role_id,
        )
    finally:
        await conn.close()


async def _fetch_user_id(email: str) -> uuid.UUID:
    conn = await _db_connect()
    try:
        return await conn.fetchval("SELECT id FROM users WHERE email = $1", email)
    finally:
        await conn.close()


async def _fetch_role_id(name: str) -> uuid.UUID | None:
    conn = await _db_connect()
    try:
        return await conn.fetchval("SELECT id FROM roles WHERE name = $1", name)
    finally:
        await conn.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def admin_client():
    """Authenticated super_admin client (has roles:read + roles:write permissions)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        token, email = await _register(ac, prefix="rbac-actor")
        await _make_super_admin(email)
        ac.headers["Authorization"] = f"Bearer {token}"
        yield ac


@pytest_asyncio.fixture
async def target_user_id() -> uuid.UUID:
    """Register a fresh target user and return their DB UUID."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        _, email = await _register(ac, prefix="rbac-target")
    return await _fetch_user_id(email)


@pytest_asyncio.fixture
async def support_role_id() -> uuid.UUID:
    """Return the UUID of the 'support' system role (assumed seeded)."""
    role_id = await _fetch_role_id("support")
    if role_id is None:
        pytest.skip("'support' role not seeded — run alembic upgrade head")
    return role_id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRBACAssignRoleIntegration:
    """admin-rbac.int.004 — assign role lifecycle."""

    async def test_rbac_assign_role_integration(
        self,
        admin_client: AsyncClient,
        target_user_id: uuid.UUID,
        support_role_id: uuid.UUID,
    ):
        """Assign support role; assert 201 + role_id in response; verify permissions endpoint."""
        # --- Assign ---
        res = await admin_client.post(
            f"/api/admin/users/{target_user_id}/roles",
            json={"role_id": str(support_role_id)},
        )
        assert res.status_code == 201, res.text
        body = res.json()
        assert body["role_id"] == str(support_role_id)
        assert "assigned_at" in body

        # --- Verify permissions endpoint returns the role's granted powers ---
        perms_res = await admin_client.get(f"/api/admin/roles/{support_role_id}/permissions")
        assert perms_res.status_code == 200, perms_res.text
        perms = perms_res.json()
        assert isinstance(perms, list)
        assert len(perms) > 0, "support role must have at least one seeded permission"


class TestRBACRevokeRoleIntegration:
    """admin-rbac.int.005 — revoke role lifecycle."""

    async def test_rbac_revoke_role_integration(
        self,
        admin_client: AsyncClient,
        target_user_id: uuid.UUID,
        support_role_id: uuid.UUID,
    ):
        """Assign support role to target, then revoke — DELETE returns 204."""
        # Setup: assign first
        assign_res = await admin_client.post(
            f"/api/admin/users/{target_user_id}/roles",
            json={"role_id": str(support_role_id)},
        )
        assert assign_res.status_code == 201, f"Setup assign failed: {assign_res.text}"

        # Revoke
        revoke_res = await admin_client.delete(
            f"/api/admin/users/{target_user_id}/roles/{support_role_id}",
        )
        assert revoke_res.status_code == 204, revoke_res.text
