"""
Usage tracking service — query counting, plan limits, and usage stats.

Uses asyncpg directly (same pattern as RAGService) for raw UPSERT
queries that need ON CONFLICT handling not available via ORM easily.
"""

import logging
import uuid
from datetime import UTC, datetime

import asyncpg

from app.config import settings
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

_DB_URL = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

# Plan limits table — single source of truth.
#
# BYOK Model: TukiJuris does NOT resell AI model usage.
# Plans are for PLATFORM ACCESS only — not for queries or model access.
# Users bring their own API keys → no model restrictions.
#
# queries_day: daily question limit (-1 = unlimited, 0 = no access)
# queries_month: -1 = unlimited for all plans (kept for backward compat — daily is the real limit)
# models:        ["*"] = all models available (user's own key determines access)
# areas:         all 11 legal areas available on all plans
PLAN_LIMITS: dict[str, dict] = {
    "free": {
        "queries_day": 10,        # 10 consultas/día con modelos gratuitos de la plataforma
        "queries_month": -1,      # Kept for backward compat
        "models": ["gemini/gemini-2.5-flash", "groq/llama-3.3-70b-versatile", "groq/llama-3.1-8b-instant"],
        "areas": 11,
        "multi_user": False,
        "description": "Acceso gratuito. 10 consultas/día con modelos incluidos.",
    },
    "base": {
        "queries_day": 100,
        "queries_month": -1,      # Kept for backward compat (daily is the real limit)
        "models": ["*"],
        "areas": 11,
        "multi_user": False,
        "description": "Acceso completo. 100 consultas/día. Soporte prioritario.",
    },
    "enterprise": {
        "queries_day": -1,        # Unlimited
        "queries_month": -1,
        "models": ["*"],
        "areas": 11,
        "multi_user": True,
        "description": "Acceso ilimitado. Soporte dedicado. Integraciones API.",
    },
}


class UsageService:
    """Tracks per-org/per-user query and token usage against plan limits."""

    def __init__(self):
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        """Lazy-init connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(_DB_URL, min_size=1, max_size=5)
        return self._pool

    def _current_month(self) -> str:
        """Return current month in YYYY-MM format."""
        return datetime.now(UTC).strftime("%Y-%m")

    async def track_query(
        self,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        tokens: int = 0,
    ) -> None:
        """
        Increment query count (and optionally token count) for the
        org/user/month combination.  Uses INSERT ... ON CONFLICT DO UPDATE
        so the first call creates the row and subsequent calls increment.
        """
        month = self._current_month()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO usage_records (
                    id, organization_id, user_id, month,
                    queries_used, tokens_used, created_at
                )
                VALUES (
                    gen_random_uuid(), $1, $2, $3,
                    1, $4, NOW()
                )
                ON CONFLICT (organization_id, user_id, month)
                DO UPDATE SET
                    queries_used = usage_records.queries_used + 1,
                    tokens_used  = usage_records.tokens_used  + EXCLUDED.tokens_used
                """,
                org_id,
                user_id,
                month,
                tokens,
            )
            logger.debug(
                "UsageService.track_query: org=%s user=%s month=%s tokens=%d",
                org_id,
                user_id,
                month,
                tokens,
            )

        # Also track daily usage for plan limit enforcement
        await self.increment_daily_usage(user_id, org_id)

        # Fire-and-forget: check thresholds and send usage alert if needed.
        # We do this outside the connection block so it opens a fresh session.
        try:
            limit_info = await self.check_limit(org_id)
            await notification_service.usage_alert(
                org_id=org_id,
                used=limit_info["used"],
                limit=limit_info["limit"],
            )
        except Exception as exc:
            logger.warning("UsageService.track_query: alert check failed for org %s: %s", org_id, exc)

    async def check_limit(self, org_id: uuid.UUID) -> dict:
        """
        Check whether the org is within its plan's monthly query limit.

        Returns a dict with:
          - allowed  (bool)   — True if the org can make another query
          - used     (int)    — total queries this month across all members
          - limit    (int)    — -1 means unlimited
          - plan     (str)
        """
        month = self._current_month()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            # Fetch org plan + aggregate usage in one round-trip
            row = await conn.fetchrow(
                """
                SELECT
                    o.plan,
                    o.plan_queries_limit,
                    COALESCE(SUM(ur.queries_used), 0) AS total_queries
                FROM organizations o
                LEFT JOIN usage_records ur
                    ON ur.organization_id = o.id
                    AND ur.month = $2
                WHERE o.id = $1
                GROUP BY o.plan, o.plan_queries_limit
                """,
                org_id,
                month,
            )

        if not row:
            logger.warning("UsageService.check_limit: org %s not found", org_id)
            return {"allowed": False, "used": 0, "limit": 0, "plan": "unknown"}

        plan = row["plan"]
        limit = row["plan_queries_limit"]
        used = int(row["total_queries"])

        # -1 on the column also means unlimited (set for enterprise)
        allowed = limit == -1 or used < limit

        return {"allowed": allowed, "used": used, "limit": limit, "plan": plan}

    async def get_usage(self, org_id: uuid.UUID, month: str | None = None) -> dict:
        """
        Return usage stats for an org, optionally filtered to a specific month.
        If month is None, defaults to the current month.
        """
        target_month = month or self._current_month()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    ur.user_id,
                    ur.month,
                    ur.queries_used,
                    ur.tokens_used
                FROM usage_records ur
                WHERE ur.organization_id = $1
                  AND ur.month = $2
                ORDER BY ur.queries_used DESC
                """,
                org_id,
                target_month,
            )

        total_queries = sum(r["queries_used"] for r in rows)
        total_tokens = sum(r["tokens_used"] for r in rows)

        return {
            "org_id": str(org_id),
            "month": target_month,
            "total_queries": total_queries,
            "total_tokens": total_tokens,
            "by_user": [
                {
                    "user_id": str(r["user_id"]),
                    "queries_used": r["queries_used"],
                    "tokens_used": r["tokens_used"],
                }
                for r in rows
            ],
        }

    async def get_plan_limits(self, plan: str) -> dict:
        """Return the limit definition for a plan tier."""
        return PLAN_LIMITS.get(plan, PLAN_LIMITS["base"])

    async def check_daily_limit(self, user_id: uuid.UUID, plan: str) -> dict:
        """Check if user has exceeded their daily query limit.

        Returns dict with:
            allowed: bool
            used_today: int
            daily_limit: int
            remaining: int
        """
        daily_limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"]).get("queries_day", 0)

        # Unlimited plans
        if daily_limit == -1:
            return {"allowed": True, "used_today": 0, "daily_limit": -1, "remaining": -1}

        today = datetime.now(UTC).strftime("%Y-%m-%d")

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT COALESCE(SUM(queries_used), 0) as total
                FROM usage_records
                WHERE user_id = $1
                  AND month = $2
                """,
                user_id,
                today,
            )

        used_today = int(row["total"]) if row else 0
        remaining = max(0, daily_limit - used_today)

        return {
            "allowed": used_today < daily_limit,
            "used_today": used_today,
            "daily_limit": daily_limit,
            "remaining": remaining,
        }

    async def increment_daily_usage(self, user_id: uuid.UUID, org_id: uuid.UUID) -> None:
        """Increment the daily usage counter for a user."""
        today = datetime.now(UTC).strftime("%Y-%m-%d")

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO usage_records (id, organization_id, user_id, month, queries_used, tokens_used, created_at)
                VALUES (gen_random_uuid(), $1, $2, $3, 1, 0, NOW())
                ON CONFLICT (organization_id, user_id, month)
                DO UPDATE SET queries_used = usage_records.queries_used + 1
                """,
                org_id,
                user_id,
                today,
            )


# Singleton — mirrors rag_service pattern
usage_service = UsageService()
