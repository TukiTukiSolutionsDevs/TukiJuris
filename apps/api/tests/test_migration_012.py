"""Migration 012 — onboarding_completed server_default smoke test.

Verifies that users.onboarding_completed has column_default = 'false'
after migration 012 is applied.

Requirements: live PostgreSQL (docker-compose up, alembic upgrade head).
Skipped automatically if the DB is unreachable.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_migration_012.py -v
"""

import asyncpg
import pytest

from app.config import settings


async def _db_connect() -> asyncpg.Connection:
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    try:
        return await asyncpg.connect(db_url)
    except Exception as exc:
        pytest.skip(f"DB unreachable: {exc}")


@pytest.mark.integration
class TestMigration012:
    """Verify migration 012 restores server_default false on onboarding_completed."""

    async def test_column_has_server_default_false(self):
        """onboarding_completed must have column_default = 'false' after migration 012."""
        conn = await _db_connect()
        try:
            row = await conn.fetchrow(
                """
                SELECT column_default
                FROM information_schema.columns
                WHERE table_name = 'users'
                  AND column_name = 'onboarding_completed'
                """
            )
        finally:
            await conn.close()

        assert row is not None, "Column 'onboarding_completed' not found in users table"
        assert row["column_default"] == "false", (
            f"Expected column_default 'false', got {row['column_default']!r}. "
            "Migration 012 may not have been applied — run: alembic upgrade head"
        )
