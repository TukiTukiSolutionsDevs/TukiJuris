"""AdminMetricsService — revenue aggregation, BYOK listing, extended user listing.

All methods take an injected AsyncSession + PlanService so they are testable
in isolation without spinning up the full app.

Deviations from design (discovered during Batch A):
- Organization.plan (not plan_code), Organization.is_active (not subscription_status)
- user_llm_keys.updated_at is the source column; API exposes it as last_rotation_at
- DB is named agente_derecho — no model changes required, just noted
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.plans import PLANS
from app.services.plan_service import PlanService  # retained for __init__ signature


# ---------------------------------------------------------------------------
# Internal DTOs (service layer — no HTTP framework concerns)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RevenueBreakdownItem:
    plan: str
    display_name: str
    org_count: int
    revenue_cents: int


@dataclass(frozen=True)
class RevenueSnapshot:
    source: str
    mrr_cents: int
    arr_cents: int
    breakdown: list[RevenueBreakdownItem]


@dataclass(frozen=True)
class BYOKItem:
    user_id: str
    user_email: str
    provider: str
    is_active: bool
    api_key_hint: str
    last_rotation_at: datetime | None


@dataclass(frozen=True)
class UserListItemInternal:
    id: str
    email: str
    full_name: str | None
    is_active: bool
    is_admin: bool
    plan: str
    created_at: datetime
    org_name: str | None
    queries_this_month: int
    last_active: datetime | None
    byok_count: int


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class AdminMetricsService:
    def __init__(self, db: AsyncSession, plan_service: PlanService) -> None:
        self._db = db
        self._plan_service = plan_service

    # ── Revenue ──────────────────────────────────────────────────────────

    async def compute_revenue(
        self,
        date_from: "datetime | None" = None,
        date_to: "datetime | None" = None,
    ) -> RevenueSnapshot:
        """Compute MRR/ARR from paid invoices (HARD SWAP — no canonical fallback).

        Source is always "invoices". When no paid invoices match the date range
        the result is an honest S/0 snapshot rather than a fallback to canonical
        prices. This honours locked-scope decision 7.

        Args:
            date_from: lower bound on paid_at (inclusive). None = no lower bound.
            date_to:   upper bound on paid_at (inclusive). None = no upper bound.
        """
        date_filters = ""
        params: dict = {}
        if date_from is not None:
            date_filters += " AND paid_at >= :date_from"
            params["date_from"] = date_from
        if date_to is not None:
            date_filters += " AND paid_at <= :date_to"
            params["date_to"] = date_to

        sql = text(
            f"""
            SELECT
                plan,
                COUNT(DISTINCT org_id) AS org_count,
                ROUND(SUM(total_amount) * 100)::bigint AS revenue_cents
            FROM invoices
            WHERE status = 'paid'{date_filters}
            GROUP BY plan
            """
        )
        result = await self._db.execute(sql, params)
        rows = result.mappings().fetchall()

        breakdown: list[RevenueBreakdownItem] = []
        mrr_cents = 0
        for row in rows:
            plan = str(row["plan"])
            revenue_cents = int(row["revenue_cents"] or 0)
            org_count = int(row["org_count"] or 0)
            display_name = PLANS[plan].display_name if plan in PLANS else plan
            breakdown.append(
                RevenueBreakdownItem(
                    plan=plan,
                    display_name=display_name,
                    org_count=org_count,
                    revenue_cents=revenue_cents,
                )
            )
            mrr_cents += revenue_cents

        return RevenueSnapshot(
            source="invoices",
            mrr_cents=mrr_cents,
            arr_cents=mrr_cents * 12,
            breakdown=breakdown,
        )

    # ── BYOK ─────────────────────────────────────────────────────────────

    async def list_byok(
        self,
        page: int,
        per_page: int,
        provider: str | None,
    ) -> tuple[list[BYOKItem], int]:
        """Return paginated BYOK configurations. Never includes encrypted material.

        Note: user_llm_keys.updated_at is exposed as last_rotation_at in the API shape.
        """
        offset = (page - 1) * per_page
        provider_filter = "" if provider is None else "AND k.provider = :provider"
        params: dict = {"limit": per_page, "offset": offset}
        count_params: dict = {}
        if provider is not None:
            params["provider"] = provider
            count_params["provider"] = provider

        items_sql = text(
            f"""
            SELECT
                k.user_id::text,
                u.email         AS user_email,
                k.provider,
                k.is_active,
                k.api_key_hint,
                k.updated_at    AS last_rotation_at
            FROM user_llm_keys k
            JOIN users u ON u.id = k.user_id
            WHERE true {provider_filter}
            ORDER BY k.updated_at DESC NULLS LAST, k.created_at DESC
            LIMIT :limit OFFSET :offset
            """
        )
        count_sql = text(
            f"""
            SELECT COUNT(*)
            FROM user_llm_keys k
            WHERE true {provider_filter}
            """
        )

        rows_result = await self._db.execute(items_sql, params)
        rows = rows_result.mappings().fetchall()

        total = int(await self._db.scalar(count_sql, count_params) or 0)

        items = [
            BYOKItem(
                user_id=row["user_id"],
                user_email=row["user_email"],
                provider=row["provider"],
                is_active=row["is_active"],
                api_key_hint=row["api_key_hint"],
                last_rotation_at=row["last_rotation_at"],
            )
            for row in rows
        ]
        return items, total

    # ── Extended user list ────────────────────────────────────────────────

    async def list_users_extended(
        self,
        page: int,
        per_page: int,
        q: str | None,
    ) -> tuple[list[UserListItemInternal], int]:
        """Paginated user list enriched with last_active and byok_count."""
        offset = (page - 1) * per_page
        month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        search_val = f"%{q}%" if q else None
        search_filter = "" if search_val is None else "AND u.email ILIKE :search"
        params: dict = {
            "limit": per_page,
            "offset": offset,
            "month_start": month_start,
        }
        count_params: dict = {}
        if search_val is not None:
            params["search"] = search_val
            count_params["search"] = search_val

        rows_sql = text(
            f"""
            SELECT
                u.id::text,
                u.email,
                u.full_name,
                u.is_active,
                u.is_admin,
                u.plan,
                u.created_at,
                o.name AS org_name,
                COALESCE(mq.query_count, 0) AS queries_this_month,
                (
                    SELECT MAX(rt.created_at)
                    FROM refresh_tokens rt
                    WHERE rt.user_id = u.id
                ) AS last_active,
                (
                    SELECT COUNT(*)
                    FROM user_llm_keys k
                    WHERE k.user_id = u.id AND k.is_active = true
                ) AS byok_count
            FROM users u
            LEFT JOIN organizations o ON o.id = u.default_org_id
            LEFT JOIN (
                SELECT c.user_id, COUNT(m.id) AS query_count
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                WHERE m.role = 'user' AND m.created_at >= :month_start
                GROUP BY c.user_id
            ) mq ON mq.user_id = u.id
            WHERE true {search_filter}
            ORDER BY u.created_at DESC
            LIMIT :limit OFFSET :offset
            """
        )
        count_sql = text(
            f"""
            SELECT COUNT(*)
            FROM users u
            WHERE true {search_filter}
            """
        )

        rows_result = await self._db.execute(rows_sql, params)
        rows = rows_result.mappings().fetchall()

        total = int(await self._db.scalar(count_sql, count_params) or 0)

        items = [
            UserListItemInternal(
                id=row["id"],
                email=row["email"],
                full_name=row["full_name"],
                is_active=row["is_active"],
                is_admin=row["is_admin"],
                plan=row["plan"],
                created_at=row["created_at"],
                org_name=row["org_name"],
                queries_this_month=int(row["queries_this_month"] or 0),
                last_active=row["last_active"],
                byok_count=int(row["byok_count"] or 0),
            )
            for row in rows
        ]
        return items, total
