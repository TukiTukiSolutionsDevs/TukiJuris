"""Migration 013 — processed_webhook_events smoke test (AC13).

Verifies that after migration 013 is applied the table exists with:
  - All expected columns (id, provider, event_id, event_type, payload_hash,
    processed_at, http_status, response_body).
  - A UNIQUE index on (provider, event_id).
  - A CHECK constraint that rejects unknown providers.

Requirements: live PostgreSQL (docker-compose up, alembic upgrade head).
Skipped automatically if the DB is unreachable.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_migration_013.py -v
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
class TestMigration013:
    """Verify migration 013 creates processed_webhook_events correctly."""

    async def test_table_exists(self):
        """processed_webhook_events table must exist after migration 013."""
        conn = await _db_connect()
        try:
            row = await conn.fetchrow(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'processed_webhook_events'
                """
            )
        finally:
            await conn.close()
        assert row is not None, (
            "Table 'processed_webhook_events' not found. "
            "Run: alembic upgrade head"
        )

    async def test_expected_columns_exist(self):
        """All spec-required columns must be present."""
        expected_columns = {
            "id",
            "provider",
            "event_id",
            "event_type",
            "payload_hash",
            "processed_at",
            "http_status",
            "response_body",
        }
        conn = await _db_connect()
        try:
            rows = await conn.fetch(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'processed_webhook_events'
                """
            )
        finally:
            await conn.close()

        actual_columns = {row["column_name"] for row in rows}
        missing = expected_columns - actual_columns
        assert not missing, f"Missing columns: {missing}"

    async def test_unique_index_on_provider_event_id(self):
        """UNIQUE index ux_processed_webhook_events_provider_event_id must exist."""
        conn = await _db_connect()
        try:
            row = await conn.fetchrow(
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'processed_webhook_events'
                  AND indexname = 'ux_processed_webhook_events_provider_event_id'
                """
            )
        finally:
            await conn.close()

        assert row is not None, (
            "Unique index 'ux_processed_webhook_events_provider_event_id' not found."
        )
        assert "UNIQUE" in row["indexdef"].upper(), (
            f"Index exists but is not UNIQUE: {row['indexdef']}"
        )

    async def test_check_constraint_rejects_unknown_provider(self):
        """CHECK constraint must reject providers outside ('culqi','mercadopago')."""
        conn = await _db_connect()
        try:
            with pytest.raises(asyncpg.CheckViolationError):
                await conn.execute(
                    """
                    INSERT INTO processed_webhook_events (provider, event_id)
                    VALUES ('stripe', 'evt_test_invalid_provider')
                    """
                )
        finally:
            await conn.close()

    async def test_valid_providers_accepted(self):
        """Both 'culqi' and 'mercadopago' must be accepted by the CHECK constraint."""
        conn = await _db_connect()
        try:
            # Use a transaction so we don't leave test rows behind
            async with conn.transaction():
                await conn.execute(
                    """
                    INSERT INTO processed_webhook_events (provider, event_id, event_type)
                    VALUES ('culqi', 'mig_test_culqi_001', 'charge.succeeded'),
                           ('mercadopago', 'mig_test_mp_001', 'payment')
                    """
                )
                # Confirm rows exist within the transaction
                count = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM processed_webhook_events
                    WHERE event_id IN ('mig_test_culqi_001', 'mig_test_mp_001')
                    """
                )
                assert count == 2, f"Expected 2 test rows, got {count}"
                raise Exception("rollback")  # force rollback to clean up
        except Exception as exc:
            if "rollback" not in str(exc):
                raise
        finally:
            await conn.close()
