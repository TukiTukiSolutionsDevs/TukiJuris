"""Integration tests — GET /api/admin/users/{user_id}/roles.

Spec IDs: admin-rbac.int.006
Layer: integration

Tests the new GET endpoint that returns roles currently assigned to a user.
Covers: happy path (200), missing permission (403), unknown user (404).

Run: docker exec tukijuris-api-1 pytest apps/api/tests/integration/test_admin_user_roles_get.py -v
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
# DB helpers — mirrors test_rbac_admin.py pattern
# ---------------------------------------------------------------------------


async def _db_connect() -> asyncpg.Connection:
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    return await asyncpg.connect(db_url)


async def _register(client: AsyncClient, prefix: str = "get-roles") -> tuple[str, str]:
    """Register a fresh test user; return (access_token, email)."""
    email = f"{prefix}-{uuid.uuid4().hex[:8]}@test.com"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "TestPass123!", "full_name": "Roles Tester"},
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


async def _assign_role_direct(user_id: uuid.UUID, role_id: uuid.UUID) -> None:
    """Directly seed a user_role row without going through the API."""
    conn = await _db_connect()
    try:
        await conn.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            user_id,
            role_id,
        )
    finally:
        await conn.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def admin_client():
    """Authenticated super_admin client (has roles:read + roles:write permissions)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        token, email = await _register(ac, prefix="get-roles-actor")
        await _make_super_admin(email)
        ac.headers["Authorization"] = f"Bearer {token}"
        yield ac


@pytest_asyncio.fixture
async def unprivileged_client():
    """Authenticated client with NO roles:read permission."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        token, _ = await _register(ac, prefix="get-roles-unpriv")
        ac.headers["Authorization"] = f"Bearer {token}"
        yield ac


@pytest_asyncio.fixture
async def target_user_email_and_id() -> tuple[str, uuid.UUID]:
    """Register a fresh target user and return (email, DB UUID)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        _, email = await _register(ac, prefix="get-roles-target")
    uid = await _fetch_user_id(email)
    return email, uid


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


class TestGetUserRolesHappyPath:
    """admin-rbac.int.006 — GET /api/admin/users/{user_id}/roles happy path."""

    async def test_returns_empty_list_for_user_with_no_roles(
        self,
        admin_client: AsyncClient,
        target_user_email_and_id: tuple[str, uuid.UUID],
    ):
        """User with no assigned roles returns 200 with empty list."""
        _, target_id = target_user_email_and_id
        res = await admin_client.get(f"/api/admin/users/{target_id}/roles")
        assert res.status_code == 200, res.text
        body = res.json()
        assert isinstance(body, list)

    async def test_returns_assigned_roles(
        self,
        admin_client: AsyncClient,
        target_user_email_and_id: tuple[str, uuid.UUID],
        support_role_id: uuid.UUID,
    ):
        """User with an assigned role returns that role in the list."""
        _, target_id = target_user_email_and_id
        # Seed the role directly
        await _assign_role_direct(target_id, support_role_id)

        res = await admin_client.get(f"/api/admin/users/{target_id}/roles")
        assert res.status_code == 200, res.text
        body = res.json()
        assert isinstance(body, list)
        role_ids = [r["id"] for r in body]
        assert str(support_role_id) in role_ids

    async def test_response_shape_matches_role_response_schema(
        self,
        admin_client: AsyncClient,
        target_user_email_and_id: tuple[str, uuid.UUID],
        support_role_id: uuid.UUID,
    ):
        """Each item in the response has id, name, display_name, description, is_system."""
        _, target_id = target_user_email_and_id
        await _assign_role_direct(target_id, support_role_id)

        res = await admin_client.get(f"/api/admin/users/{target_id}/roles")
        assert res.status_code == 200, res.text
        body = res.json()
        assert len(body) >= 1
        role = body[0]
        for field in ("id", "name", "display_name", "is_system"):
            assert field in role, f"Missing field '{field}' in response"


class TestGetUserRolesPermission:
    """admin-rbac.int.006 — GET /api/admin/users/{user_id}/roles permission gate."""

    async def test_returns_403_without_roles_read(
        self,
        unprivileged_client: AsyncClient,
        target_user_email_and_id: tuple[str, uuid.UUID],
    ):
        """User without roles:read permission receives 403."""
        _, target_id = target_user_email_and_id
        res = await unprivileged_client.get(f"/api/admin/users/{target_id}/roles")
        assert res.status_code == 403, res.text


class TestGetUserRolesNotFound:
    """admin-rbac.int.006 — GET /api/admin/users/{user_id}/roles unknown user."""

    async def test_returns_404_for_unknown_user(
        self,
        admin_client: AsyncClient,
    ):
        """Non-existent user_id returns 404."""
        phantom_id = uuid.uuid4()
        res = await admin_client.get(f"/api/admin/users/{phantom_id}/roles")
        assert res.status_code == 404, res.text
