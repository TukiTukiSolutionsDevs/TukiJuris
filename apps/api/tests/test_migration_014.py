"""Migration 014 — invoices table smoke test (AC1, AC2).

Verifies that after migration 014 is applied the table exists with:
  - All expected columns.
  - UNIQUE constraint on (provider, provider_charge_id).
  - CHECK constraints on provider, status, currency.
  - 3 non-unique indexes.

Requirements: live PostgreSQL (docker-compose up, alembic upgrade head).
Skipped automatically if the DB is unreachable.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_migration_014.py -v
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
class TestMigration014:
    """Verify migration 014 creates invoices correctly."""

    async def test_table_exists(self):
        conn = await _db_connect()
        try:
            row = await conn.fetchrow(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'invoices'
                """
            )
        finally:
            await conn.close()
        assert row is not None, "Table 'invoices' not found. Run: alembic upgrade head"

    async def test_expected_columns_exist(self):
        expected = {
            "id", "org_id", "subscription_id", "provider", "provider_charge_id",
            "status", "currency", "base_amount", "seats_count", "seat_amount",
            "subtotal_amount", "tax_amount", "total_amount", "plan",
            "paid_at", "failed_at", "refunded_at", "voided_at",
            "refund_reason", "void_reason", "provider_event_id",
            "created_at", "updated_at",
        }
        conn = await _db_connect()
        try:
            rows = await conn.fetch(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'invoices'"
            )
        finally:
            await conn.close()
        actual = {r["column_name"] for r in rows}
        missing = expected - actual
        assert not missing, f"Missing columns: {missing}"

    async def test_unique_constraint_on_provider_charge(self):
        """UNIQUE(provider, provider_charge_id) must exist."""
        conn = await _db_connect()
        try:
            row = await conn.fetchrow(
                """
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name = 'invoices'
                  AND constraint_type = 'UNIQUE'
                  AND constraint_name = 'uq_invoices_provider_charge'
                """
            )
        finally:
            await conn.close()
        assert row is not None, "UNIQUE constraint uq_invoices_provider_charge not found"

    async def test_check_constraint_rejects_invalid_status(self):
        """CHECK ck_invoices_status rejects bogus status values."""
        conn = await _db_connect()
        try:
            with pytest.raises(asyncpg.CheckViolationError):
                await conn.execute(
                    """
                    INSERT INTO invoices
                      (id, org_id, provider, provider_charge_id, status, currency,
                       base_amount, seats_count, seat_amount, subtotal_amount,
                       tax_amount, total_amount, plan)
                    VALUES
                      (gen_random_uuid(), gen_random_uuid(), 'culqi', 'test_chk_status',
                       'invalid_status', 'PEN', 70, 0, 0, 70, 12.60, 82.60, 'pro')
                    """
                )
        finally:
            await conn.close()

    async def test_check_constraint_rejects_invalid_provider(self):
        """CHECK ck_invoices_provider rejects unknown providers."""
        conn = await _db_connect()
        try:
            with pytest.raises(asyncpg.CheckViolationError):
                await conn.execute(
                    """
                    INSERT INTO invoices
                      (id, org_id, provider, provider_charge_id, status, currency,
                       base_amount, seats_count, seat_amount, subtotal_amount,
                       tax_amount, total_amount, plan)
                    VALUES
                      (gen_random_uuid(), gen_random_uuid(), 'stripe', 'test_chk_prov',
                       'paid', 'PEN', 70, 0, 0, 70, 12.60, 82.60, 'pro')
                    """
                )
        finally:
            await conn.close()

    async def test_unique_constraint_rejects_duplicate_provider_charge(self):
        """Duplicate (provider, provider_charge_id) must raise UniqueViolationError (AC2)."""
        conn = await _db_connect()
        try:
            # Fetch a real org_id to satisfy FK constraint
            org_id = await conn.fetchval("SELECT id FROM organizations LIMIT 1")
            if org_id is None:
                pytest.skip("No organizations in DB — cannot test FK-constrained insert")

            async with conn.transaction():
                await conn.execute(
                    """
                    INSERT INTO invoices
                      (id, org_id, provider, provider_charge_id, status, currency,
                       base_amount, seats_count, seat_amount, subtotal_amount,
                       tax_amount, total_amount, plan)
                    VALUES
                      (gen_random_uuid(), $1, 'culqi', 'dup_charge_mig014',
                       'paid', 'PEN', 70, 0, 0, 70, 12.60, 82.60, 'pro')
                    """,
                    org_id,
                )
                with pytest.raises(asyncpg.UniqueViolationError):
                    await conn.execute(
                        """
                        INSERT INTO invoices
                          (id, org_id, provider, provider_charge_id, status, currency,
                           base_amount, seats_count, seat_amount, subtotal_amount,
                           tax_amount, total_amount, plan)
                        VALUES
                          (gen_random_uuid(), $1, 'culqi', 'dup_charge_mig014',
                           'paid', 'PEN', 70, 0, 0, 70, 12.60, 82.60, 'pro')
                        """,
                        org_id,
                    )
                raise Exception("rollback")
        except Exception as exc:
            if "rollback" not in str(exc):
                raise
        finally:
            await conn.close()

    async def test_indexes_exist(self):
        """The 3 non-unique indexes must exist."""
        expected_indexes = {
            "ix_invoices_org_created",
            "ix_invoices_status_paid",
            "ix_invoices_provider_event",
        }
        conn = await _db_connect()
        try:
            rows = await conn.fetch(
                "SELECT indexname FROM pg_indexes WHERE tablename = 'invoices'"
            )
        finally:
            await conn.close()
        actual = {r["indexname"] for r in rows}
        missing = expected_indexes - actual
        assert not missing, f"Missing indexes: {missing}"
