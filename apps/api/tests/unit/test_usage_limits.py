"""Unit tests for UsageService — fix-usage-limit-schema.

All external deps (asyncpg pool) are mocked.
No Docker required — runs with: python -m pytest tests/unit/test_usage_limits.py -v
"""

import inspect
import re
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.services.usage as usage_mod
from app.config.plans import PLANS
from app.services.plan_service import PlanService
from app.services.usage import UsageService, _TIER_LIMITS_DAY


# ── Source inspection helpers ─────────────────────────────────────────────────


def _code_only(src: str) -> str:
    """Strip docstrings and inline comments so inspect assertions hit code only."""
    src = re.sub(r'""".*?"""', "", src, flags=re.DOTALL)
    src = re.sub(r"'''.*?'''", "", src, flags=re.DOTALL)
    src = re.sub(r"#[^\n]*", "", src)
    return src


# ── Pool fixture helper ───────────────────────────────────────────────────────


def make_fake_pool(conn: AsyncMock) -> MagicMock:
    """Return a fake asyncpg pool whose acquire() yields the given connection."""
    pool = MagicMock()

    @asynccontextmanager
    async def _acquire():
        yield conn

    pool.acquire = _acquire
    return pool


# ── Plan limits config (task 05) ─────────────────────────────────────────────


class TestPlanLimitsConfig:
    """Plan config assertions — post plan-model-refactor.

    PLAN_LIMITS was removed (Sprint 2 C1). Canonical sources now:
    - Daily query caps: PlanService.queries_day_for() → app/config/plans.py PLANS
    - Tier limits: _TIER_LIMITS_DAY (module-internal to app/services/usage.py)
    """

    def test_free_queries_day_is_ten(self):
        assert PlanService.queries_day_for("free") == 10

    def test_free_tier_limits_day_shape(self):
        assert _TIER_LIMITS_DAY["free"] == {1: 8, 2: 2, 3: 0, 4: 0}

    def test_plan_ids_are_free_pro_studio(self):
        """Plan IDs updated to free/pro/studio — plan-model-refactor Sprint 2 complete."""
        assert set(PLANS.keys()) == {"free", "pro", "studio"}

    def test_tier_limits_only_has_canonical_plans(self):
        """Internal tier-limits dict must track the same plan set as PLANS."""
        assert set(_TIER_LIMITS_DAY.keys()) == {"free", "pro", "studio"}

    def test_pro_queries_day_is_unlimited(self):
        assert PlanService.queries_day_for("pro") == -1

    def test_studio_queries_day_is_unlimited(self):
        assert PlanService.queries_day_for("studio") == -1

    def test_no_weekly_concept_anywhere(self):
        """Weekly quotas are gone repo-wide (fix-usage-limit-schema). _TIER_LIMITS_DAY
        must not expose any weekly shape, and usage.py must not reference it."""
        import inspect

        src = inspect.getsource(usage_mod)
        assert "tier_limits_week" not in src, (
            "tier_limits_week must not exist — weekly quotas were removed "
            "in fix-usage-limit-schema."
        )
        assert "queries_week" not in src, (
            "queries_week must not exist — daily-only quota per spec §2."
        )


# ── check_daily_limit — boundary matrix (task 07) ────────────────────────────


class TestCheckDailyLimitBoundaries:
    @pytest.mark.parametrize(
        "used, expected_allowed, expected_remaining",
        [
            (0, True, 10),
            (9, True, 1),
            (10, False, 0),
            (11, False, 0),
        ],
    )
    async def test_boundary(self, used, expected_allowed, expected_remaining):
        svc = UsageService()
        fake_conn = AsyncMock()
        fake_conn.fetchrow = AsyncMock(return_value={"query_count": used})
        pool = make_fake_pool(fake_conn)

        with patch.object(svc, "_get_pool", new=AsyncMock(return_value=pool)):
            result = await svc.check_daily_limit(uuid.uuid4(), "free")

        assert result["allowed"] is expected_allowed
        assert result["remaining"] == expected_remaining
        assert result["limit"] == 10
        assert result["plan"] == "free"

    async def test_no_row_returns_zero_used_and_allowed(self):
        """When no usage row exists for today, used_today=0 and allowed=True."""
        svc = UsageService()
        fake_conn = AsyncMock()
        fake_conn.fetchrow = AsyncMock(return_value=None)
        pool = make_fake_pool(fake_conn)

        with patch.object(svc, "_get_pool", new=AsyncMock(return_value=pool)):
            result = await svc.check_daily_limit(uuid.uuid4(), "free")

        assert result["allowed"] is True
        assert result["used_today"] == 0
        assert result["remaining"] == 10

    async def test_result_includes_plan_key(self):
        svc = UsageService()
        fake_conn = AsyncMock()
        fake_conn.fetchrow = AsyncMock(return_value={"query_count": 3})
        pool = make_fake_pool(fake_conn)

        with patch.object(svc, "_get_pool", new=AsyncMock(return_value=pool)):
            result = await svc.check_daily_limit(uuid.uuid4(), "pro")

        assert result["plan"] == "pro"
        assert result["limit"] == -1  # pro is unlimited

    async def test_result_includes_reset_at(self):
        svc = UsageService()
        fake_conn = AsyncMock()
        fake_conn.fetchrow = AsyncMock(return_value={"query_count": 0})
        pool = make_fake_pool(fake_conn)

        with patch.object(svc, "_get_pool", new=AsyncMock(return_value=pool)):
            result = await svc.check_daily_limit(uuid.uuid4(), "free")

        assert "reset_at" in result
        assert result["reset_at"].tzinfo is not None  # timezone-aware


# ── reset_at correctness (task 07) ───────────────────────────────────────────


class TestResetAt:
    async def test_reset_at_is_next_utc_midnight(self):
        svc = UsageService()
        fake_conn = AsyncMock()
        fake_conn.fetchrow = AsyncMock(return_value={"query_count": 5})
        pool = make_fake_pool(fake_conn)

        fixed_now = datetime(2026, 4, 19, 14, 30, 0, tzinfo=timezone.utc)
        expected_reset = datetime(2026, 4, 20, 0, 0, 0, tzinfo=timezone.utc)

        with patch.object(svc, "_get_pool", new=AsyncMock(return_value=pool)):
            with patch("app.services.usage.datetime") as mock_dt:
                mock_dt.now = MagicMock(return_value=fixed_now)
                result = await svc.check_daily_limit(uuid.uuid4(), "free")

        assert result["reset_at"] == expected_reset

    async def test_reset_at_crosses_month_boundary(self):
        """April 30 23:59 UTC → reset_at is May 1 00:00 UTC."""
        svc = UsageService()
        fake_conn = AsyncMock()
        fake_conn.fetchrow = AsyncMock(return_value={"query_count": 2})
        pool = make_fake_pool(fake_conn)

        fixed_now = datetime(2026, 4, 30, 23, 59, 0, tzinfo=timezone.utc)
        expected_reset = datetime(2026, 5, 1, 0, 0, 0, tzinfo=timezone.utc)

        with patch.object(svc, "_get_pool", new=AsyncMock(return_value=pool)):
            with patch("app.services.usage.datetime") as mock_dt:
                mock_dt.now = MagicMock(return_value=fixed_now)
                result = await svc.check_daily_limit(uuid.uuid4(), "free")

        assert result["reset_at"] == expected_reset

    async def test_reset_at_crosses_year_boundary(self):
        """Dec 31 23:59 UTC → reset_at is Jan 1 00:00 UTC."""
        svc = UsageService()
        fake_conn = AsyncMock()
        fake_conn.fetchrow = AsyncMock(return_value={"query_count": 1})
        pool = make_fake_pool(fake_conn)

        fixed_now = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        expected_reset = datetime(2027, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        with patch.object(svc, "_get_pool", new=AsyncMock(return_value=pool)):
            with patch("app.services.usage.datetime") as mock_dt:
                mock_dt.now = MagicMock(return_value=fixed_now)
                result = await svc.check_daily_limit(uuid.uuid4(), "free")

        assert result["reset_at"] == expected_reset


# ── increment_daily_usage — null org + upsert (task 08) ──────────────────────


class TestIncrementNullOrg:
    async def test_org_id_none_does_not_raise(self):
        """free-tier user without an org (org_id=None) must not raise."""
        svc = UsageService()
        fake_conn = AsyncMock()
        fake_conn.execute = AsyncMock()
        pool = make_fake_pool(fake_conn)

        with patch.object(svc, "_get_pool", new=AsyncMock(return_value=pool)):
            await svc.increment_daily_usage(uuid.uuid4(), None, 1, 0)

        # $2 positional arg to conn.execute is org_id — must be None
        call_args = fake_conn.execute.await_args.args
        assert call_args[2] is None

    async def test_execute_called_once_per_increment(self):
        """One upsert per increment_daily_usage call."""
        svc = UsageService()
        fake_conn = AsyncMock()
        fake_conn.execute = AsyncMock()
        pool = make_fake_pool(fake_conn)

        with patch.object(svc, "_get_pool", new=AsyncMock(return_value=pool)):
            await svc.increment_daily_usage(uuid.uuid4(), uuid.uuid4(), 1, 100)

        fake_conn.execute.assert_awaited_once()

    async def test_correct_counts_passed_to_execute(self):
        """query_count and token_count are forwarded as $4 and $5."""
        svc = UsageService()
        fake_conn = AsyncMock()
        fake_conn.execute = AsyncMock()
        pool = make_fake_pool(fake_conn)

        user_id = uuid.uuid4()
        org_id = uuid.uuid4()

        with patch.object(svc, "_get_pool", new=AsyncMock(return_value=pool)):
            await svc.increment_daily_usage(user_id, org_id, query_count=2, token_count=500)

        call_args = fake_conn.execute.await_args.args
        # SQL string is args[0]; positional params: $1=user_id, $2=org_id, $3=today,
        # $4=query_count, $5=token_count
        assert call_args[1] == user_id
        assert call_args[2] == org_id
        assert call_args[4] == 2
        assert call_args[5] == 500


# ── Concurrency contract (task 16) ───────────────────────────────────────────


class TestConcurrencyContract:
    """Comment-as-contract: no transactional guarantee against +1 overshoot.

    Two concurrent requests at used=9 may both pass the pre-check and both
    succeed, incrementing the counter to 11.  This is ACCEPTED for the beta
    phase (spec §9 AC4, design R3).  No Redis counter or SELECT FOR UPDATE used.

    If a future change introduces transactional enforcement, UPDATE THESE TESTS.
    """

    def test_increment_does_not_use_select_for_update(self):
        src = _code_only(inspect.getsource(UsageService.increment_daily_usage))
        assert "FOR UPDATE" not in src.upper(), (
            "increment_daily_usage must NOT use SELECT FOR UPDATE — "
            "+1 overshoot is documented and accepted (spec §9 AC4)."
        )

    def test_increment_does_not_use_redis(self):
        src = _code_only(inspect.getsource(UsageService.increment_daily_usage))
        assert "redis" not in src.lower(), (
            "increment_daily_usage must NOT use Redis counters — "
            "atomic enforcement is deferred to a future sprint (design R3)."
        )

    def test_check_daily_limit_does_not_query_messages_table(self):
        """Quota reads usage_records only — never the messages table (spec §2)."""
        src = _code_only(inspect.getsource(UsageService.check_daily_limit))
        assert "messages" not in src.lower(), (
            "check_daily_limit must NOT query the messages table — "
            "quota reads usage_records only per spec §2."
        )

    def test_no_check_weekly_limit_method(self):
        """check_weekly_limit must be removed — daily-only quota per spec §2."""
        assert not hasattr(UsageService, "check_weekly_limit"), (
            "check_weekly_limit was not deleted. "
            "Spec §2 mandates daily-only quota; weekly checker must be gone."
        )

    def test_no_current_month_helper(self):
        """_current_month helper must be removed — no month column exists anymore."""
        assert not hasattr(UsageService, "_current_month"), (
            "_current_month helper was not deleted. "
            "The month VARCHAR column is gone; this helper is dead code."
        )
