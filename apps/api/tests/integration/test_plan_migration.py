"""Integration tests — migration 007 plan rename.

Verifies that after running alembic upgrade head the database contains
no rows with legacy plan values (base, enterprise) in the three
affected tables: users, organizations, subscriptions.

Requirements:
  - Live PostgreSQL (docker-compose up)
  - Migration 007 applied (alembic upgrade head)

Run with:
  cd apps/api && python -m pytest tests/integration/test_plan_migration.py -v -m integration

Skipped automatically if DB is unreachable.
"""

import pytest
import pytest_asyncio
import asyncpg

from app.config import settings


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _connect() -> asyncpg.Connection:
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    return await asyncpg.connect(db_url)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def db():
    """Raw asyncpg connection — skips test if DB is unreachable."""
    try:
        conn = await _connect()
    except Exception as exc:
        pytest.skip(f"DB unreachable: {exc}")
    yield conn
    await conn.close()


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.integration
class TestPlanMigration007:
    """Verify migration 007 renamed all legacy plan values."""

    async def test_no_base_plan_in_users(self, db: asyncpg.Connection):
        """users.plan must contain no rows with value 'base'."""
        count = await db.fetchval(
            "SELECT COUNT(*) FROM users WHERE plan = 'base'"
        )
        assert count == 0, f"Found {count} users still on legacy plan 'base'"

    async def test_no_enterprise_plan_in_users(self, db: asyncpg.Connection):
        """users.plan must contain no rows with value 'enterprise'."""
        count = await db.fetchval(
            "SELECT COUNT(*) FROM users WHERE plan = 'enterprise'"
        )
        assert count == 0, f"Found {count} users still on legacy plan 'enterprise'"

    async def test_valid_plan_values_in_users(self, db: asyncpg.Connection):
        """users.plan must only contain canonical values: free, pro, studio."""
        rows = await db.fetch(
            "SELECT DISTINCT plan FROM users WHERE plan NOT IN ('free', 'pro', 'studio')"
        )
        unexpected = [r["plan"] for r in rows]
        assert unexpected == [], f"Unexpected plan values in users: {unexpected}"

    async def test_no_base_plan_in_organizations(self, db: asyncpg.Connection):
        """organizations.plan must contain no rows with value 'base'."""
        count = await db.fetchval(
            "SELECT COUNT(*) FROM organizations WHERE plan = 'base'"
        )
        assert count == 0, f"Found {count} organizations still on legacy plan 'base'"

    async def test_no_enterprise_plan_in_organizations(self, db: asyncpg.Connection):
        """organizations.plan must contain no rows with value 'enterprise'."""
        count = await db.fetchval(
            "SELECT COUNT(*) FROM organizations WHERE plan = 'enterprise'"
        )
        assert count == 0, f"Found {count} organizations still on legacy plan 'enterprise'"

    async def test_no_base_plan_in_subscriptions(self, db: asyncpg.Connection):
        """subscriptions.plan must contain no rows with value 'base'."""
        count = await db.fetchval(
            "SELECT COUNT(*) FROM subscriptions WHERE plan = 'base'"
        )
        assert count == 0, f"Found {count} subscriptions still on legacy plan 'base'"

    async def test_no_enterprise_plan_in_subscriptions(self, db: asyncpg.Connection):
        """subscriptions.plan must contain no rows with value 'enterprise'."""
        count = await db.fetchval(
            "SELECT COUNT(*) FROM subscriptions WHERE plan = 'enterprise'"
        )
        assert count == 0, f"Found {count} subscriptions still on legacy plan 'enterprise'"

    async def test_migration_007_is_recorded(self, db: asyncpg.Connection):
        """Migration 007_rename_plan_values must be an ancestor of the current Alembic head.

        Walks the revision chain from the live DB head to base using Alembic's
        ScriptDirectory. Resilient to future migrations: passes as long as 007
        is in the linear chain, regardless of what the current head revision is.
        """
        import os
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        head = await db.fetchval("SELECT version_num FROM alembic_version LIMIT 1")
        assert head is not None, "No Alembic version recorded — run: alembic upgrade head"

        api_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cfg = Config(os.path.join(api_root, "alembic.ini"))
        script = ScriptDirectory.from_config(cfg)
        chain = {rev.revision for rev in script.iterate_revisions(head, "base")}

        assert "007_rename_plan_values" in chain, (
            f"Migration 007_rename_plan_values is not an ancestor of current head ({head}). "
            "Run: alembic upgrade head"
        )

    async def test_migration_008_is_recorded(self, db: asyncpg.Connection):
        """Migration 008_org_seat_pricing must be an ancestor of the current Alembic head.

        Walks the revision chain from the live DB head to base using Alembic's
        ScriptDirectory. Resilient to future migrations: passes as long as 008
        is in the linear chain, regardless of what the current head revision is.
        """
        import os
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        head = await db.fetchval("SELECT version_num FROM alembic_version LIMIT 1")
        assert head is not None, "No Alembic version recorded — run: alembic upgrade head"

        api_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cfg = Config(os.path.join(api_root, "alembic.ini"))
        script = ScriptDirectory.from_config(cfg)
        chain = {rev.revision for rev in script.iterate_revisions(head, "base")}

        assert "008_org_seat_pricing" in chain, (
            f"Migration 008_org_seat_pricing is not an ancestor of current head ({head}). "
            "Run: alembic upgrade head"
        )

    async def test_organizations_has_seat_pricing_columns(self, db: asyncpg.Connection):
        """Migration 008 must have added base_seats_included, seat_price_cents, base_price_cents."""
        rows = await db.fetch(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'organizations'
              AND column_name IN (
                  'base_seats_included', 'seat_price_cents', 'base_price_cents'
              )
            """
        )
        found = {r["column_name"] for r in rows}
        expected = {"base_seats_included", "seat_price_cents", "base_price_cents"}
        assert found == expected, f"Missing columns: {expected - found}"

    async def test_subscriptions_has_price_cents_column(self, db: asyncpg.Connection):
        """Migration 008 must have added price_cents to subscriptions."""
        row = await db.fetchrow(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'subscriptions'
              AND column_name = 'price_cents'
            """
        )
        assert row is not None, "subscriptions.price_cents column not found after migration 008"
