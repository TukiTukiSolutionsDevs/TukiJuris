"""Migration 015 — trials table smoke test.

Verifies that after migration 015 is applied the table exists with:
  - All expected columns.
  - UNIQUE constraint on (user_id, plan_code).
  - Partial UNIQUE index on user_id WHERE status = 'active'.
  - CHECK constraints on status, plan_code, provider, and ends_at > started_at.
  - Required indexes.
  - ORM Trial model is importable.

Requirements: live PostgreSQL (docker-compose up, alembic upgrade head).
Skipped automatically if the DB is unreachable.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_migration_015.py -v
"""

from __future__ import annotations

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
class TestMigration015:
    """Verify migration 015 creates the trials table correctly."""

    async def test_table_exists(self):
        conn = await _db_connect()
        try:
            row = await conn.fetchrow(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'trials'
                """
            )
        finally:
            await conn.close()
        assert row is not None, "Table 'trials' not found. Run: alembic upgrade head"

    async def test_expected_columns_exist(self):
        expected = {
            "id", "user_id", "plan_code", "status",
            "started_at", "ends_at",
            "card_added_at", "provider", "provider_customer_id", "provider_card_token",
            "charged_at", "charge_failed_at", "charge_failure_reason", "retry_count",
            "canceled_at", "canceled_by_user", "downgraded_at",
            "subscription_id",
            "created_at", "updated_at",
        }
        conn = await _db_connect()
        try:
            rows = await conn.fetch(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'trials'"
            )
        finally:
            await conn.close()
        actual = {r["column_name"] for r in rows}
        missing = expected - actual
        assert not missing, f"Missing columns: {missing}"

    async def test_unique_constraint_user_plan(self):
        """UNIQUE(user_id, plan_code) must exist."""
        conn = await _db_connect()
        try:
            row = await conn.fetchrow(
                """
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name = 'trials'
                  AND constraint_type = 'UNIQUE'
                  AND constraint_name = 'uq_trials_user_plan'
                """
            )
        finally:
            await conn.close()
        assert row is not None, "UNIQUE constraint uq_trials_user_plan not found"

    async def test_partial_unique_index_user_active(self):
        """Partial unique index uix_trials_user_active must exist."""
        conn = await _db_connect()
        try:
            row = await conn.fetchrow(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'trials'
                  AND indexname = 'uix_trials_user_active'
                """
            )
        finally:
            await conn.close()
        assert row is not None, "Partial unique index uix_trials_user_active not found"

    async def test_partial_unique_enforces_single_active_trial_per_user(self):
        """Only one active trial per user_id is allowed (partial UNIQUE)."""
        conn = await _db_connect()
        try:
            user_id = await conn.fetchval("SELECT id FROM users LIMIT 1")
            if user_id is None:
                pytest.skip("No users in DB")

            now = "NOW()"
            ends = "NOW() + INTERVAL '14 days'"

            async with conn.transaction():
                await conn.execute(
                    f"""
                    INSERT INTO trials
                      (id, user_id, plan_code, status, started_at, ends_at, created_at, updated_at)
                    VALUES
                      (gen_random_uuid(), $1, 'pro', 'active', {now}, {ends}, {now}, {now})
                    """,
                    user_id,
                )
                with pytest.raises(asyncpg.UniqueViolationError):
                    await conn.execute(
                        f"""
                        INSERT INTO trials
                          (id, user_id, plan_code, status, started_at, ends_at, created_at, updated_at)
                        VALUES
                          (gen_random_uuid(), $1, 'studio', 'active', {now}, {ends}, {now}, {now})
                        """,
                        user_id,
                    )
                raise Exception("rollback")
        except Exception as exc:
            if "rollback" not in str(exc):
                raise
        finally:
            await conn.close()

    async def test_check_constraint_rejects_invalid_status(self):
        conn = await _db_connect()
        try:
            with pytest.raises(asyncpg.CheckViolationError):
                await conn.execute(
                    """
                    INSERT INTO trials
                      (id, user_id, plan_code, status, started_at, ends_at, created_at, updated_at)
                    VALUES
                      (gen_random_uuid(), gen_random_uuid(), 'pro', 'bogus_status',
                       NOW(), NOW() + INTERVAL '14 days', NOW(), NOW())
                    """
                )
        finally:
            await conn.close()

    async def test_check_constraint_rejects_invalid_plan_code(self):
        conn = await _db_connect()
        try:
            with pytest.raises(asyncpg.CheckViolationError):
                await conn.execute(
                    """
                    INSERT INTO trials
                      (id, user_id, plan_code, status, started_at, ends_at, created_at, updated_at)
                    VALUES
                      (gen_random_uuid(), gen_random_uuid(), 'enterprise', 'active',
                       NOW(), NOW() + INTERVAL '14 days', NOW(), NOW())
                    """
                )
        finally:
            await conn.close()

    async def test_check_constraint_rejects_invalid_provider(self):
        conn = await _db_connect()
        try:
            user_id = await conn.fetchval("SELECT id FROM users LIMIT 1")
            if user_id is None:
                pytest.skip("No users in DB")
            with pytest.raises(asyncpg.CheckViolationError):
                await conn.execute(
                    """
                    INSERT INTO trials
                      (id, user_id, plan_code, status, provider, started_at, ends_at, created_at, updated_at)
                    VALUES
                      (gen_random_uuid(), $1, 'pro', 'active', 'stripe',
                       NOW(), NOW() + INTERVAL '14 days', NOW(), NOW())
                    """,
                    user_id,
                )
        finally:
            await conn.close()

    async def test_check_constraint_rejects_ends_before_starts(self):
        conn = await _db_connect()
        try:
            with pytest.raises(asyncpg.CheckViolationError):
                await conn.execute(
                    """
                    INSERT INTO trials
                      (id, user_id, plan_code, status, started_at, ends_at, created_at, updated_at)
                    VALUES
                      (gen_random_uuid(), gen_random_uuid(), 'pro', 'active',
                       NOW() + INTERVAL '14 days', NOW(), NOW(), NOW())
                    """
                )
        finally:
            await conn.close()

    async def test_indexes_exist(self):
        """Required indexes must exist."""
        expected = {
            "ix_trials_user_id",
            "idx_trials_status_ends_at",
            "uix_trials_user_active",
            "idx_trials_charge_failed_retry",
        }
        conn = await _db_connect()
        try:
            rows = await conn.fetch(
                "SELECT indexname FROM pg_indexes WHERE tablename = 'trials'"
            )
        finally:
            await conn.close()
        actual = {r["indexname"] for r in rows}
        missing = expected - actual
        assert not missing, f"Missing indexes: {missing}"

    def test_orm_trial_model_importable(self):
        """Trial ORM model must import cleanly."""
        from app.models.trial import Trial, TRIAL_DURATION_DAYS, RETRY_WINDOW_HOURS

        assert Trial.__tablename__ == "trials"
        assert TRIAL_DURATION_DAYS == 14
        assert RETRY_WINDOW_HOURS == 72

    def test_orm_trial_init_defaults(self):
        """Trial.__init__ sets all defaults without DB access (SA gotcha #1)."""
        import uuid
        from app.models.trial import Trial

        user_id = uuid.uuid4()
        t = Trial(user_id=user_id, plan_code="pro")

        assert t.status == "active"
        assert t.canceled_by_user is False
        assert t.retry_count == 0
        assert t.started_at is not None
        assert t.ends_at is not None
        assert (t.ends_at - t.started_at).days == 14
        assert t.created_at is not None
        assert t.updated_at is not None

    def test_orm_trial_days_remaining(self):
        """days_remaining hybrid property returns correct value."""
        import uuid
        from datetime import UTC, datetime, timedelta
        from app.models.trial import Trial

        user_id = uuid.uuid4()
        now = datetime.now(UTC)
        t = Trial(
            user_id=user_id,
            plan_code="studio",
            started_at=now,
            ends_at=now + timedelta(days=5),
        )
        assert t.days_remaining == 5

    def test_schemas_importable(self):
        """All trial schemas must import cleanly."""
        from app.schemas.trials import (
            StartTrialRequest,
            AddCardRequest,
            AdminTrialPatch,
            AdminTrialFilters,
            TrialResponse,
            AdminTrialListResponse,
            TrialTickResult,
            CustomerInfo,
        )
        assert StartTrialRequest.model_fields["plan_code"] is not None
