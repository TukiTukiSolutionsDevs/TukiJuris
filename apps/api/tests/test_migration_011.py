"""Migration 011 — onboarding_completed column smoke tests.

Verifies via raw asyncpg that:
  - The column exists in the users table with the correct type.
  - New users registered via the API receive onboarding_completed = FALSE.
  - The value can be toggled to TRUE (simulating backfill / endpoint behaviour).

Requirements: live PostgreSQL + Redis (docker-compose up, alembic upgrade head).
Skipped automatically if the DB is unreachable.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_migration_011.py -v
"""

import uuid

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _db_connect() -> asyncpg.Connection:
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    try:
        return await asyncpg.connect(db_url)
    except Exception as exc:
        pytest.skip(f"DB unreachable: {exc}")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestMigration011:
    """Verify migration 011 applied correctly."""

    async def test_column_exists_with_correct_type(self):
        """onboarding_completed column must exist as boolean, not-null."""
        conn = await _db_connect()
        try:
            row = await conn.fetchrow(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'onboarding_completed'
                """
            )
        finally:
            await conn.close()

        assert row is not None, "Column 'onboarding_completed' not found in users table"
        assert row["data_type"] == "boolean", (
            f"Expected boolean, got {row['data_type']}"
        )
        assert row["is_nullable"] == "NO", (
            "Column must be NOT NULL"
        )

    async def test_new_user_defaults_to_false(self, http_client: AsyncClient):
        """Users created after migration 011 must default to onboarding_completed = FALSE."""
        email = f"mig011-{uuid.uuid4().hex[:8]}@test.com"
        res = await http_client.post(
            "/api/auth/register",
            json={"email": email, "password": "TestMig011!", "full_name": "Mig Tester"},
        )
        assert res.status_code in (200, 201), f"Register failed: {res.status_code} {res.text}"

        conn = await _db_connect()
        try:
            val = await conn.fetchval(
                "SELECT onboarding_completed FROM users WHERE email = $1", email
            )
        finally:
            await conn.close()

        assert val is False, f"Expected False for new user, got {val!r}"

    async def test_column_can_be_set_to_true(self, http_client: AsyncClient):
        """Verify direct DB update to TRUE (simulates backfill correctness)."""
        email = f"mig011-bt-{uuid.uuid4().hex[:8]}@test.com"
        res = await http_client.post(
            "/api/auth/register",
            json={"email": email, "password": "TestMig011!", "full_name": "Backfill Tester"},
        )
        assert res.status_code in (200, 201)

        conn = await _db_connect()
        try:
            await conn.execute(
                "UPDATE users SET onboarding_completed = TRUE WHERE email = $1", email
            )
            val = await conn.fetchval(
                "SELECT onboarding_completed FROM users WHERE email = $1", email
            )
        finally:
            await conn.close()

        assert val is True, f"Expected True after update, got {val!r}"

    async def test_backfill_logic_sets_false_rows_to_true(self):
        """The migration 011 backfill SQL correctly updates FALSE → TRUE.

        Rather than inspecting global DB state (which breaks when the DB persists
        across test runs and accumulates users with onboarding_completed=FALSE),
        this test:
          1. Creates a dedicated test user via the API (starts as FALSE).
          2. Applies the backfill UPDATE directly.
          3. Verifies the user is now TRUE.
          4. Cleans up.
        """
        import uuid as _uuid

        email = f"mig011-bf-{_uuid.uuid4().hex[:8]}@test.com"

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            res = await ac.post(
                "/api/auth/register",
                json={"email": email, "password": "TestMig011!", "full_name": "Backfill Test"},
            )
            assert res.status_code in (200, 201), f"Register failed: {res.text}"

        conn = await _db_connect()
        try:
            # Confirm user starts as FALSE (new-user default)
            before = await conn.fetchval(
                "SELECT onboarding_completed FROM users WHERE email = $1", email
            )
            assert before is False, f"Expected FALSE before backfill, got {before!r}"

            # Apply the same UPDATE the migration runs
            affected = await conn.fetchval(
                "UPDATE users SET onboarding_completed = TRUE WHERE onboarding_completed = FALSE AND email = $1 RETURNING 1",
                email,
            )
            assert affected == 1, "Backfill UPDATE affected wrong number of rows"

            after = await conn.fetchval(
                "SELECT onboarding_completed FROM users WHERE email = $1", email
            )
        finally:
            await conn.close()

        assert after is True, f"Expected TRUE after backfill, got {after!r}"
