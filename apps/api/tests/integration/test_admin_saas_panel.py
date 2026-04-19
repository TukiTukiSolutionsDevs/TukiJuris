"""Integration tests — admin-saas-panel endpoints.

Covers ACs 1-8:
  AC1 — GET /api/admin/revenue returns MRR/ARR/breakdown
  AC2 — billing:read required for /revenue; users:read required for /byok
  AC3 — is_admin=False → 403 on all admin endpoints (defense-in-depth)
  AC4 — users list has last_active + byok_count
  AC5 — BYOK list has provider/is_active/api_key_hint/last_rotation_at, NO key material
  AC6 — revenue response has source="canonical_prices"
  AC7 — pagination params validated (422 on bad page/per_page)
  AC8 — last_active reflects latest refresh_token.created_at

Run: docker exec tukijuris-api-1 python -m pytest tests/integration/test_admin_saas_panel.py -v
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


async def _db_connect() -> asyncpg.Connection:
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    return await asyncpg.connect(db_url)


async def _register(client: AsyncClient) -> tuple[str, str]:
    """Register a fresh user and return (access_token, email)."""
    email = f"saas-{uuid.uuid4().hex[:8]}@test.com"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "TestPass123!", "full_name": "Admin Tester"},
    )
    assert res.status_code in (200, 201), f"Register failed: {res.status_code} {res.text}"
    return res.json()["access_token"], email


async def _make_admin(email: str, role_name: str = "super_admin") -> None:
    """Set is_admin=true and assign a role to the user by email."""
    try:
        conn = await _db_connect()
    except Exception as exc:
        pytest.skip(f"DB unreachable: {exc}")
    try:
        user_id = await conn.fetchval("SELECT id FROM users WHERE email = $1", email)
        role_id = await conn.fetchval("SELECT id FROM roles WHERE name = $1", role_name)
        if role_id is None:
            pytest.skip(f"Role '{role_name}' not seeded — run alembic upgrade head")
        await conn.execute(
            "UPDATE users SET is_admin = true WHERE id = $1",
            user_id,
        )
        await conn.execute(
            """
            INSERT INTO user_roles (user_id, role_id)
            VALUES ($1, $2)
            ON CONFLICT (user_id, role_id) DO NOTHING
            """,
            user_id,
            role_id,
        )
    finally:
        await conn.close()


async def _make_non_admin(email: str) -> None:
    """Ensure user has is_admin=false (default, but explicit for clarity)."""
    try:
        conn = await _db_connect()
    except Exception as exc:
        pytest.skip(f"DB unreachable: {exc}")
    try:
        await conn.execute("UPDATE users SET is_admin = false WHERE email = $1", email)
    finally:
        await conn.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def super_admin_client(client: AsyncClient):
    """Authenticated client for an admin user with super_admin role."""
    token, email = await _register(client)
    await _make_admin(email, role_name="super_admin")
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture
async def support_client(client: AsyncClient):
    """Admin with support role: has users:read but NOT billing:read."""
    token, email = await _register(client)
    await _make_admin(email, role_name="support")
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture
async def non_admin_client(client: AsyncClient):
    """Regular user with super_admin role but is_admin=false (defense-in-depth test)."""
    token, email = await _register(client)
    await _make_non_admin(email)
    # Assign super_admin role so RBAC passes but is_admin guard fires
    conn = None
    try:
        conn = await _db_connect()
    except Exception as exc:
        pytest.skip(f"DB unreachable: {exc}")
    try:
        user_id = await conn.fetchval("SELECT id FROM users WHERE email = $1", email)
        role_id = await conn.fetchval("SELECT id FROM roles WHERE name = 'super_admin'")
        await conn.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            user_id,
            role_id,
        )
    finally:
        if conn:
            await conn.close()
    client.headers["Authorization"] = f"Bearer {token}"
    return client


# ---------------------------------------------------------------------------
# AC1 + AC6 — GET /api/admin/revenue
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revenue_returns_200_and_source_flag(super_admin_client: AsyncClient):
    """AC1 + AC6: revenue endpoint returns 200 with source=invoices (hard swap — no canonical fallback)."""
    res = await super_admin_client.get("/api/admin/revenue")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["source"] == "invoices"
    assert "mrr_cents" in data
    assert "arr_cents" in data
    assert "breakdown" in data
    assert data["arr_cents"] == data["mrr_cents"] * 12


# ---------------------------------------------------------------------------
# AC2 — permission guard
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revenue_forbidden_without_billing_read(support_client: AsyncClient):
    """AC2: admin with support role (no billing:read) gets 403 on /revenue."""
    res = await support_client.get("/api/admin/revenue")
    assert res.status_code == 403, res.text


@pytest.mark.asyncio
async def test_byok_allowed_with_users_read(support_client: AsyncClient):
    """AC2: support role has users:read → /byok returns 200."""
    res = await support_client.get("/api/admin/byok")
    assert res.status_code == 200, res.text


# ---------------------------------------------------------------------------
# AC3 — is_admin defense-in-depth
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revenue_forbidden_for_non_admin(non_admin_client: AsyncClient):
    """AC3: user with is_admin=False gets 403 even if RBAC permits billing:read."""
    res = await non_admin_client.get("/api/admin/revenue")
    assert res.status_code == 403, res.text


@pytest.mark.asyncio
async def test_byok_forbidden_for_non_admin(non_admin_client: AsyncClient):
    """AC3: user with is_admin=False gets 403 on /byok."""
    res = await non_admin_client.get("/api/admin/byok")
    assert res.status_code == 403, res.text


# ---------------------------------------------------------------------------
# AC5 — BYOK list: no key material
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_byok_list_shape_no_key_material(super_admin_client: AsyncClient):
    """AC5: /byok response has correct shape and no encrypted key material."""
    res = await super_admin_client.get("/api/admin/byok")
    assert res.status_code == 200, res.text
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    for item in data["items"]:
        assert "api_key_encrypted" not in item
        assert "api_key_hint" in item
        assert "provider" in item
        assert "is_active" in item
        assert "last_rotation_at" in item


# ---------------------------------------------------------------------------
# AC4 + AC8 — users list extended
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_users_list_has_last_active_and_byok_count(super_admin_client: AsyncClient):
    """AC4 + AC8: /admin/users response items include last_active and byok_count."""
    res = await super_admin_client.get("/api/admin/users?page=1&per_page=5")
    assert res.status_code == 200, res.text
    data = res.json()
    assert "users" in data
    for user in data["users"]:
        assert "last_active" in user
        assert "byok_count" in user
        assert isinstance(user["byok_count"], int)


# ---------------------------------------------------------------------------
# AC7 — pagination validation (422)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_users_list_rejects_invalid_page(super_admin_client: AsyncClient):
    """AC7: page < 1 → 422 Unprocessable Entity."""
    res = await super_admin_client.get("/api/admin/users?page=0")
    assert res.status_code == 422, res.text


@pytest.mark.asyncio
async def test_users_list_rejects_per_page_over_100(super_admin_client: AsyncClient):
    """AC7: per_page > 100 → 422 Unprocessable Entity."""
    res = await super_admin_client.get("/api/admin/users?per_page=200")
    assert res.status_code == 422, res.text


@pytest.mark.asyncio
async def test_byok_rejects_invalid_page(super_admin_client: AsyncClient):
    """AC7: page < 1 → 422 on /byok."""
    res = await super_admin_client.get("/api/admin/byok?page=0")
    assert res.status_code == 422, res.text


# ---------------------------------------------------------------------------
# Unauthenticated
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revenue_unauthenticated(client: AsyncClient):
    """401 with no token."""
    res = await client.get("/api/admin/revenue")
    assert res.status_code == 401, res.text


@pytest.mark.asyncio
async def test_byok_unauthenticated(client: AsyncClient):
    """401 with no token."""
    res = await client.get("/api/admin/byok")
    assert res.status_code == 401, res.text


# ---------------------------------------------------------------------------
# AC8 — last_active picks latest of multiple refresh tokens
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_last_active_picks_latest_of_multiple_refresh_tokens(
    super_admin_client: AsyncClient,
    client: AsyncClient,
) -> None:
    """AC8: last_active == MAX(refresh_token.created_at) when a user has many tokens."""
    # Register a fresh target user
    _, email = await _register(client)

    now = datetime.now(UTC)
    t_old = now - timedelta(days=3)
    t_mid = now - timedelta(days=1)
    t_recent = now - timedelta(hours=1)
    expires = now + timedelta(days=30)

    try:
        conn = await _db_connect()
    except Exception as exc:
        pytest.skip(f"DB unreachable: {exc}")
    try:
        user_id = await conn.fetchval("SELECT id FROM users WHERE email = $1", email)
        # Remove any tokens created during registration so the set is fully controlled
        await conn.execute("DELETE FROM refresh_tokens WHERE user_id = $1", user_id)
        for ts in [t_old, t_mid, t_recent]:
            await conn.execute(
                """
                INSERT INTO refresh_tokens
                    (user_id, jti, family_id, token_hash, expires_at, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                user_id,
                uuid.uuid4().hex,
                uuid.uuid4().hex,
                uuid.uuid4().hex,
                expires,
                ts,
            )
    finally:
        await conn.close()

    res = await super_admin_client.get(
        f"/api/admin/users?search={email}&per_page=1"
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert len(data["users"]) == 1, f"Expected 1 user, got {len(data['users'])}"

    last_active_str = data["users"][0]["last_active"]
    assert last_active_str is not None, "last_active must not be None after inserting tokens"

    last_active_dt = datetime.fromisoformat(last_active_str)
    if last_active_dt.tzinfo is None:
        last_active_dt = last_active_dt.replace(tzinfo=UTC)

    diff = abs((last_active_dt - t_recent).total_seconds())
    assert diff < 2, (
        f"last_active should equal the most recent token (~{t_recent}), "
        f"got {last_active_dt} (diff={diff:.2f}s)"
    )
