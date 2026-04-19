"""
Usage tracking service — query counting, plan limits, and usage stats.

Uses asyncpg directly (same pattern as RAGService) for raw UPSERT
queries that need ON CONFLICT handling not available via ORM easily.
"""

import logging
import uuid
from calendar import monthrange
from datetime import UTC, datetime, timedelta
from datetime import date as _date
from typing import TypedDict

import asyncpg

from app.config import settings
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

_DB_URL = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

# ── Tier limits — internal to UsageService ───────────────────────────────────
#
# Per-tier daily limits for model-tier enforcement.
# Canonical plan config (queries_day, byok_enabled) lives in app/config/plans.py.
# This dict ONLY holds tier_limits_day data — it is NOT a general plan registry.
#
# Tier mapping: 1=base, 2=standard, 3=premium, 4=ultra
# -1 = unlimited within tier,  0 = tier not available for this plan.
_TIER_LIMITS_DAY: dict[str, dict[int, int]] = {
    "free":   {1: 8, 2: 2, 3: 0, 4: 0},
    "pro":    {1: -1, 2: -1, 3: 3, 4: 0},
    "studio": {1: -1, 2: -1, 3: 15, 4: 3},
}


class DailyLimitResult(TypedDict):
    allowed: bool
    used_today: int
    limit: int  # -1 means unlimited
    remaining: int  # -1 if unlimited
    plan: str
    reset_at: datetime  # next UTC midnight


class UsageService:
    """Tracks per-org/per-user query and token usage against plan limits."""

    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        """Lazy-init connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(_DB_URL, min_size=1, max_size=5)
        return self._pool

    # ── Write path ───────────────────────────────────────────────────────────

    async def track_query(
        self,
        org_id: uuid.UUID | None,
        user_id: uuid.UUID,
        tokens: int = 0,
    ) -> None:
        """Increment daily usage for a user.

        Delegates entirely to increment_daily_usage — the old monthly INSERT
        block is gone (that table column no longer exists).
        org_id may be None for free-tier users without an organisation.
        """
        await self.increment_daily_usage(user_id, org_id, query_count=1, token_count=tokens)
        logger.debug(
            "UsageService.track_query: org=%s user=%s tokens=%d",
            org_id,
            user_id,
            tokens,
        )

        # Fire-and-forget: check org thresholds and send usage alert if needed.
        if org_id is not None:
            try:
                limit_info = await self.check_limit(org_id)
                await notification_service.usage_alert(
                    org_id=org_id,
                    used=limit_info["used"],
                    limit=limit_info["limit"],
                )
            except Exception as exc:
                logger.warning(
                    "UsageService.track_query: alert check failed for org %s: %s", org_id, exc
                )

    async def increment_daily_usage(
        self,
        user_id: uuid.UUID,
        org_id: uuid.UUID | None,
        query_count: int = 1,
        token_count: int = 0,
    ) -> None:
        """Upsert today's usage row.  Safe when org_id is None (free-tier users).

        Uses ON CONFLICT (user_id, day) to atomically create-or-increment.
        No SELECT FOR UPDATE — a +1 overshoot on concurrent requests is
        accepted per spec §9 AC4.  Redis counters deferred to future sprint.
        """
        today = datetime.now(UTC).date()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO usage_records
                    (id, user_id, organization_id, day, query_count, token_count,
                     created_at, updated_at)
                VALUES
                    (gen_random_uuid(), $1, $2, $3, $4, $5, NOW(), NOW())
                ON CONFLICT (user_id, day) DO UPDATE SET
                    query_count     = usage_records.query_count     + EXCLUDED.query_count,
                    token_count     = usage_records.token_count     + EXCLUDED.token_count,
                    organization_id = COALESCE(
                        usage_records.organization_id, EXCLUDED.organization_id
                    ),
                    updated_at = NOW()
                """,
                user_id,
                org_id,
                today,
                query_count,
                token_count,
            )

    # ── Read path ────────────────────────────────────────────────────────────

    async def check_daily_limit(self, user_id: uuid.UUID, plan: str) -> DailyLimitResult:
        """Check today's UTC usage against plan daily cap.

        Reads usage_records only — never the messages table (spec §2).
        Returns DailyLimitResult with allowed/remaining/reset_at/plan.

        Daily cap is sourced from PlanService (canonical config/plans.py).
        Free tier cap (10/day) is ALWAYS enforced regardless of BETA_MODE.
        """
        from app.services.plan_service import PlanService

        try:
            daily_limit = PlanService.queries_day_for(plan)
        except ValueError:
            # Unknown plan string — treat as free (safe default: 10/day).
            daily_limit = 10
        now = datetime.now(UTC)
        reset_at = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        if daily_limit == -1:
            return {
                "allowed": True,
                "used_today": 0,
                "limit": -1,
                "remaining": -1,
                "plan": plan,
                "reset_at": reset_at,
            }

        today = now.date()  # native datetime.date — passed as DATE to asyncpg

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT query_count FROM usage_records
                WHERE user_id = $1 AND day = $2
                """,
                user_id,
                today,
            )

        used_today = int(row["query_count"]) if row else 0
        remaining = max(0, daily_limit - used_today)

        return {
            "allowed": used_today < daily_limit,
            "used_today": used_today,
            "limit": daily_limit,
            "remaining": remaining,
            "plan": plan,
            "reset_at": reset_at,
        }

    async def check_limit(self, org_id: uuid.UUID) -> dict:
        """Check whether the org is within its plan's monthly query limit.

        Aggregates daily rows within the current calendar month.
        Returns: allowed (bool), used (int), limit (int, -1 = unlimited), plan (str).
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    o.plan,
                    o.plan_queries_limit,
                    COALESCE(SUM(ur.query_count), 0) AS total_queries
                FROM organizations o
                LEFT JOIN usage_records ur
                    ON ur.organization_id = o.id
                   AND ur.day >= date_trunc('month', CURRENT_DATE)::date
                   AND ur.day <  (date_trunc('month', CURRENT_DATE)
                                  + interval '1 month')::date
                WHERE o.id = $1
                GROUP BY o.plan, o.plan_queries_limit
                """,
                org_id,
            )

        if not row:
            logger.warning("UsageService.check_limit: org %s not found", org_id)
            return {"allowed": False, "used": 0, "limit": 0, "plan": "unknown"}

        plan = row["plan"]
        limit = row["plan_queries_limit"]
        used = int(row["total_queries"])
        allowed = limit == -1 or used < limit

        return {"allowed": allowed, "used": used, "limit": limit, "plan": plan}

    async def get_usage(self, org_id: uuid.UUID, month: str | None = None) -> dict:
        """Return usage stats for an org, optionally filtered to a specific month
        (YYYY-MM format).  Defaults to the current UTC month.

        Aggregates daily rows that fall within the month bounds.
        """
        if month:
            year, mon = int(month[:4]), int(month[5:7])
            _, last_day = monthrange(year, mon)
            start = _date(year, mon, 1)
            end = _date(year, mon, last_day)
            target_month = month
        else:
            today = datetime.now(UTC).date()
            _, last_day = monthrange(today.year, today.month)
            start = today.replace(day=1)
            end = today.replace(day=last_day)
            target_month = today.strftime("%Y-%m")

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    ur.user_id,
                    SUM(ur.query_count) AS queries_used,
                    SUM(ur.token_count) AS tokens_used
                FROM usage_records ur
                WHERE ur.organization_id = $1
                  AND ur.day BETWEEN $2 AND $3
                GROUP BY ur.user_id
                ORDER BY queries_used DESC
                """,
                org_id,
                start,
                end,
            )

        total_queries = sum(int(r["queries_used"]) for r in rows)
        total_tokens = sum(int(r["tokens_used"]) for r in rows)

        return {
            "org_id": str(org_id),
            "month": target_month,
            "total_queries": total_queries,
            "total_tokens": total_tokens,
            "by_user": [
                {
                    "user_id": str(r["user_id"]),
                    "queries_used": int(r["queries_used"]),
                    "tokens_used": int(r["tokens_used"]),
                }
                for r in rows
            ],
        }

    async def get_plan_limits(self, plan: str) -> dict:
        """Return tier limit definition for a plan (usage-service internal data only)."""
        return {"tier_limits_day": _TIER_LIMITS_DAY.get(plan, _TIER_LIMITS_DAY["pro"])}

    async def check_tier_limit(self, user_id: uuid.UUID, plan: str, model_id: str) -> dict:
        """Check tier-specific daily limit.

        All plans now enforce tier limits on a daily basis (unified in
        fix-usage-limit-schema — free plan migrated from weekly to daily tiers).

        Returns allowed, tier, used, limit, remaining, period.
        """
        from app.services.llm_adapter import MODEL_TIERS, get_model_tier

        tier = get_model_tier(model_id)
        plan_config = _TIER_LIMITS_DAY.get(plan, _TIER_LIMITS_DAY["free"])

        # Unified to daily period for all plans (was weekly for free plan).
        tier_limits = plan_config
        period = "day"
        period_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        tier_limit = tier_limits.get(tier, 0)
        if tier_limit == -1:
            return {"allowed": True, "tier": tier, "used": 0, "limit": -1, "period": period}
        if tier_limit == 0:
            return {"allowed": False, "tier": tier, "used": 0, "limit": 0, "period": period}

        tier_models = [mid for mid, t in MODEL_TIERS.items() if t == tier]
        if not tier_models:
            return {
                "allowed": True,
                "tier": tier,
                "used": 0,
                "limit": tier_limit,
                "period": period,
            }

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT COUNT(m.id) as total FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                WHERE c.user_id = $1 AND m.role = 'assistant'
                  AND m.model = ANY($2) AND m.created_at >= $3
                """,
                user_id,
                tier_models,
                period_start,
            )
        used = int(row["total"]) if row else 0
        return {
            "allowed": used < tier_limit,
            "tier": tier,
            "used": used,
            "limit": tier_limit,
            "remaining": max(0, tier_limit - used),
            "period": period,
        }


# Singleton — mirrors rag_service pattern
usage_service = UsageService()
