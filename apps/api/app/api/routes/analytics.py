"""Analytics endpoints — org-level usage metrics for owners and admins."""

import csv
import io
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_org_role
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _assert_org_access(
    org_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> None:
    """Raise 403 unless the current user is owner or admin of the org."""
    await require_org_role(current_user, org_id, "admin", db)


def _date_range(days: int) -> tuple[datetime, datetime]:
    now = datetime.now(UTC)
    start = now - timedelta(days=days)
    return start, now


# ---------------------------------------------------------------------------
# GET /api/analytics/{org_id}/overview
# ---------------------------------------------------------------------------


@router.get("/{org_id}/overview")
async def analytics_overview(
    org_id: uuid.UUID,
    days: int = Query(30, ge=1, le=365, description="Look-back window in days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Org analytics overview: query volumes, trends, top areas/models, latency, satisfaction."""
    await _assert_org_access(org_id, current_user, db)

    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    window_start = now - timedelta(days=days)

    # Base params shared across several queries
    base_params: dict[str, Any] = {"org_id": org_id}

    # --- scalar counts ---
    queries_today: int = (
        await db.scalar(
            text(
                """
                SELECT COUNT(m.id)
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                JOIN users u ON u.id = c.user_id
                JOIN org_memberships om ON om.user_id = u.id
                WHERE om.organization_id = :org_id
                  AND om.is_active = TRUE
                  AND m.role = 'user'
                  AND m.created_at >= :since
                """
            ),
            {**base_params, "since": today_start},
        )
        or 0
    )

    queries_yesterday: int = (
        await db.scalar(
            text(
                """
                SELECT COUNT(m.id)
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                JOIN users u ON u.id = c.user_id
                JOIN org_memberships om ON om.user_id = u.id
                WHERE om.organization_id = :org_id
                  AND om.is_active = TRUE
                  AND m.role = 'user'
                  AND m.created_at >= :day_start
                  AND m.created_at < :today_start
                """
            ),
            {
                **base_params,
                "day_start": today_start - timedelta(days=1),
                "today_start": today_start,
            },
        )
        or 0
    )

    queries_week: int = (
        await db.scalar(
            text(
                """
                SELECT COUNT(m.id)
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                JOIN users u ON u.id = c.user_id
                JOIN org_memberships om ON om.user_id = u.id
                WHERE om.organization_id = :org_id
                  AND om.is_active = TRUE
                  AND m.role = 'user'
                  AND m.created_at >= :since
                """
            ),
            {**base_params, "since": week_start},
        )
        or 0
    )

    queries_month: int = (
        await db.scalar(
            text(
                """
                SELECT COUNT(m.id)
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                JOIN users u ON u.id = c.user_id
                JOIN org_memberships om ON om.user_id = u.id
                WHERE om.organization_id = :org_id
                  AND om.is_active = TRUE
                  AND m.role = 'user'
                  AND m.created_at >= :since
                """
            ),
            {**base_params, "since": month_start},
        )
        or 0
    )

    # --- daily trend (last `days` days) ---
    trend_result = await db.execute(
        text(
            """
            SELECT
                DATE(m.created_at AT TIME ZONE 'UTC') AS day,
                COUNT(m.id) AS cnt
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            JOIN users u ON u.id = c.user_id
            JOIN org_memberships om ON om.user_id = u.id
            WHERE om.organization_id = :org_id
              AND om.is_active = TRUE
              AND m.role = 'user'
              AND m.created_at >= :since
            GROUP BY day
            ORDER BY day
            """
        ),
        {**base_params, "since": window_start},
    )
    queries_trend = [
        {"date": str(row.day), "count": row.cnt}
        for row in trend_result.fetchall()
    ]

    # --- top legal areas (from assistant messages which carry area metadata) ---
    areas_result = await db.execute(
        text(
            """
            SELECT
                m.legal_area   AS area,
                COUNT(m.id)    AS cnt
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            JOIN users u ON u.id = c.user_id
            JOIN org_memberships om ON om.user_id = u.id
            WHERE om.organization_id = :org_id
              AND om.is_active = TRUE
              AND m.role = 'assistant'
              AND m.legal_area IS NOT NULL
              AND m.created_at >= :since
            GROUP BY m.legal_area
            ORDER BY cnt DESC
            LIMIT 10
            """
        ),
        {**base_params, "since": window_start},
    )
    top_areas = [
        {"area": row.area, "count": row.cnt}
        for row in areas_result.fetchall()
    ]

    # --- top models ---
    models_result = await db.execute(
        text(
            """
            SELECT
                m.model        AS model,
                COUNT(m.id)    AS cnt
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            JOIN users u ON u.id = c.user_id
            JOIN org_memberships om ON om.user_id = u.id
            WHERE om.organization_id = :org_id
              AND om.is_active = TRUE
              AND m.role = 'assistant'
              AND m.model IS NOT NULL
              AND m.created_at >= :since
            GROUP BY m.model
            ORDER BY cnt DESC
            """
        ),
        {**base_params, "since": window_start},
    )
    top_models = [
        {"model": row.model, "count": row.cnt}
        for row in models_result.fetchall()
    ]

    # --- average latency ---
    avg_latency: float = (
        await db.scalar(
            text(
                """
                SELECT AVG(m.latency_ms)
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                JOIN users u ON u.id = c.user_id
                JOIN org_memberships om ON om.user_id = u.id
                WHERE om.organization_id = :org_id
                  AND om.is_active = TRUE
                  AND m.role = 'assistant'
                  AND m.latency_ms IS NOT NULL
                  AND m.created_at >= :since
                """
            ),
            {**base_params, "since": window_start},
        )
        or 0.0
    )

    # --- satisfaction from Message.feedback field ---
    total_fb: int = (
        await db.scalar(
            text(
                """
                SELECT COUNT(m.id)
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                JOIN users u ON u.id = c.user_id
                JOIN org_memberships om ON om.user_id = u.id
                WHERE om.organization_id = :org_id
                  AND om.is_active = TRUE
                  AND m.feedback IS NOT NULL
                  AND m.created_at >= :since
                """
            ),
            {**base_params, "since": window_start},
        )
        or 0
    )
    positive_fb: int = (
        await db.scalar(
            text(
                """
                SELECT COUNT(m.id)
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                JOIN users u ON u.id = c.user_id
                JOIN org_memberships om ON om.user_id = u.id
                WHERE om.organization_id = :org_id
                  AND om.is_active = TRUE
                  AND m.feedback = 'thumbs_up'
                  AND m.created_at >= :since
                """
            ),
            {**base_params, "since": window_start},
        )
        or 0
    )
    satisfaction_rate = round(positive_fb / total_fb * 100, 1) if total_fb > 0 else 0.0

    # --- active users ---
    active_users: int = (
        await db.scalar(
            text(
                """
                SELECT COUNT(DISTINCT c.user_id)
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                JOIN users u ON u.id = c.user_id
                JOIN org_memberships om ON om.user_id = u.id
                WHERE om.organization_id = :org_id
                  AND om.is_active = TRUE
                  AND m.role = 'user'
                  AND m.created_at >= :since
                """
            ),
            {**base_params, "since": window_start},
        )
        or 0
    )

    # compute day-over-day change
    today_vs_yesterday_pct: float = 0.0
    if queries_yesterday > 0:
        today_vs_yesterday_pct = round(
            (queries_today - queries_yesterday) / queries_yesterday * 100, 1
        )

    return {
        "queries_today": queries_today,
        "queries_today_vs_yesterday_pct": today_vs_yesterday_pct,
        "queries_week": queries_week,
        "queries_month": queries_month,
        "queries_trend": queries_trend,
        "top_areas": top_areas,
        "top_models": top_models,
        "avg_latency_ms": round(float(avg_latency), 1),
        "satisfaction_rate": satisfaction_rate,
        "active_users": active_users,
    }


# ---------------------------------------------------------------------------
# GET /api/analytics/{org_id}/queries
# ---------------------------------------------------------------------------


@router.get("/{org_id}/queries")
async def analytics_queries(
    org_id: uuid.UUID,
    start: date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end: date | None = Query(None, description="End date (YYYY-MM-DD)"),
    area: str | None = Query(None, description="Filter by legal area"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Paginated query log for the organisation with optional date/area filters."""
    await _assert_org_access(org_id, current_user, db)

    offset = (page - 1) * per_page
    where_clauses = [
        "om.organization_id = :org_id",
        "om.is_active = TRUE",
        "m.role = 'assistant'",
    ]
    params: dict[str, Any] = {"org_id": org_id, "limit": per_page, "offset": offset}

    if start:
        where_clauses.append("m.created_at >= :start_dt")
        params["start_dt"] = datetime(start.year, start.month, start.day, tzinfo=UTC)
    if end:
        # include full end day
        end_dt = datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=UTC)
        where_clauses.append("m.created_at <= :end_dt")
        params["end_dt"] = end_dt
    if area:
        where_clauses.append("m.legal_area = :area")
        params["area"] = area

    where_sql = " AND ".join(where_clauses)

    count_result = await db.scalar(
        text(
            f"""
            SELECT COUNT(m.id)
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            JOIN users u ON u.id = c.user_id
            JOIN org_memberships om ON om.user_id = u.id
            WHERE {where_sql}
            """
        ),
        params,
    )
    total: int = count_result or 0

    rows_result = await db.execute(
        text(
            f"""
            SELECT
                m.id,
                m.created_at,
                u.email         AS user_email,
                m.legal_area,
                m.agent_used,
                m.model,
                m.latency_ms
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            JOIN users u ON u.id = c.user_id
            JOIN org_memberships om ON om.user_id = u.id
            WHERE {where_sql}
            ORDER BY m.created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    )

    queries = [
        {
            "id": str(row.id),
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "user_email": row.user_email,
            "legal_area": row.legal_area,
            "agent_used": row.agent_used,
            "model": row.model,
            "latency_ms": row.latency_ms,
        }
        for row in rows_result.mappings().fetchall()
    ]

    return {
        "queries": queries,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


# ---------------------------------------------------------------------------
# GET /api/analytics/{org_id}/areas
# ---------------------------------------------------------------------------


@router.get("/{org_id}/areas")
async def analytics_areas(
    org_id: uuid.UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Detailed usage breakdown per legal area with 7-day trend comparison."""
    await _assert_org_access(org_id, current_user, db)

    window_start = datetime.now(UTC) - timedelta(days=days)
    prev_start = window_start - timedelta(days=days)
    params: dict[str, Any] = {"org_id": org_id}

    current_result = await db.execute(
        text(
            """
            SELECT
                m.legal_area   AS area,
                COUNT(m.id)    AS cnt,
                AVG(m.latency_ms) AS avg_latency
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            JOIN users u ON u.id = c.user_id
            JOIN org_memberships om ON om.user_id = u.id
            WHERE om.organization_id = :org_id
              AND om.is_active = TRUE
              AND m.role = 'assistant'
              AND m.legal_area IS NOT NULL
              AND m.created_at >= :since
            GROUP BY m.legal_area
            ORDER BY cnt DESC
            """
        ),
        {**params, "since": window_start},
    )
    current_data = {row.area: {"count": row.cnt, "avg_latency": row.avg_latency}
                    for row in current_result.fetchall()}

    prev_result = await db.execute(
        text(
            """
            SELECT
                m.legal_area AS area,
                COUNT(m.id) AS cnt
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            JOIN users u ON u.id = c.user_id
            JOIN org_memberships om ON om.user_id = u.id
            WHERE om.organization_id = :org_id
              AND om.is_active = TRUE
              AND m.role = 'assistant'
              AND m.legal_area IS NOT NULL
              AND m.created_at >= :prev_start
              AND m.created_at < :window_start
            GROUP BY m.legal_area
            """
        ),
        {**params, "prev_start": prev_start, "window_start": window_start},
    )
    prev_data = {row.area: row.cnt for row in prev_result.fetchall()}

    total_current = sum(d["count"] for d in current_data.values()) or 1

    areas = []
    for area, data in current_data.items():
        prev_count = prev_data.get(area, 0)
        change_pct = (
            round((data["count"] - prev_count) / prev_count * 100, 1)
            if prev_count > 0
            else None
        )
        areas.append(
            {
                "area": area,
                "count": data["count"],
                "percentage": round(data["count"] / total_current * 100, 1),
                "avg_latency_ms": round(float(data["avg_latency"] or 0), 1),
                "prev_period_count": prev_count,
                "change_pct": change_pct,
                "trend": (
                    "up" if change_pct and change_pct > 0
                    else "down" if change_pct and change_pct < 0
                    else "stable"
                ),
            }
        )

    return {"areas": areas, "window_days": days}


# ---------------------------------------------------------------------------
# GET /api/analytics/{org_id}/models
# ---------------------------------------------------------------------------


@router.get("/{org_id}/models")
async def analytics_models(
    org_id: uuid.UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Model usage breakdown: query count and average latency per model."""
    await _assert_org_access(org_id, current_user, db)

    window_start = datetime.now(UTC) - timedelta(days=days)

    result = await db.execute(
        text(
            """
            SELECT
                m.model,
                COUNT(m.id)       AS cnt,
                AVG(m.latency_ms) AS avg_latency,
                MIN(m.latency_ms) AS min_latency,
                MAX(m.latency_ms) AS max_latency
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            JOIN users u ON u.id = c.user_id
            JOIN org_memberships om ON om.user_id = u.id
            WHERE om.organization_id = :org_id
              AND om.is_active = TRUE
              AND m.role = 'assistant'
              AND m.model IS NOT NULL
              AND m.created_at >= :since
            GROUP BY m.model
            ORDER BY cnt DESC
            """
        ),
        {"org_id": org_id, "since": window_start},
    )

    rows = result.fetchall()
    total_queries = sum(r.cnt for r in rows) or 1

    models = [
        {
            "model": row.model,
            "count": row.cnt,
            "percentage": round(row.cnt / total_queries * 100, 1),
            "avg_latency_ms": round(float(row.avg_latency or 0), 1),
            "min_latency_ms": row.min_latency,
            "max_latency_ms": row.max_latency,
        }
        for row in rows
    ]

    return {"models": models, "window_days": days}


# ---------------------------------------------------------------------------
# GET /api/analytics/{org_id}/costs
# ---------------------------------------------------------------------------

# Cost per 1K tokens (USD)
_MODEL_COST_PER_1K: dict[str, float] = {
    "gpt-4o": 0.005,
    "gpt-4o-mini": 0.00015,
    "claude-3-5-sonnet": 0.003,
    "claude-3-haiku": 0.00025,
    "gemini-1.5-pro": 0.00125,
}


def _estimate_cost(model: str, tokens: int) -> float:
    """Return estimated USD cost for the given model and token count."""
    # Try exact match first, then partial prefix match
    rate = _MODEL_COST_PER_1K.get(model)
    if rate is None:
        for key, val in _MODEL_COST_PER_1K.items():
            if key in model or model in key:
                rate = val
                break
    if rate is None:
        rate = 0.002  # conservative default for unknown models
    return round((tokens / 1000) * rate, 6)


@router.get("/{org_id}/costs")
async def analytics_costs(
    org_id: uuid.UUID,
    days: int = Query(30, ge=1, le=365, description="Look-back window in days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Cost breakdown by model based on tokens_used."""
    await _assert_org_access(org_id, current_user, db)

    window_start = datetime.now(UTC) - timedelta(days=days)

    result = await db.execute(
        text(
            """
            SELECT
                m.model,
                COALESCE(SUM(m.tokens_used), 0)   AS total_tokens,
                COUNT(m.id)                        AS query_count,
                COALESCE(AVG(m.tokens_used), 0)    AS avg_tokens
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            JOIN users u ON u.id = c.user_id
            JOIN org_memberships om ON om.user_id = u.id
            WHERE om.organization_id = :org_id
              AND om.is_active = TRUE
              AND m.role = 'assistant'
              AND m.model IS NOT NULL
              AND m.created_at >= :since
            GROUP BY m.model
            ORDER BY total_tokens DESC
            """
        ),
        {"org_id": org_id, "since": window_start},
    )

    rows = result.fetchall()

    models_data = []
    total_cost_usd = 0.0

    for row in rows:
        model_name: str = row.model
        total_tokens: int = int(row.total_tokens)
        query_count: int = int(row.query_count)
        avg_tokens: float = float(row.avg_tokens)

        estimated_cost = _estimate_cost(model_name, total_tokens)
        total_cost_usd += estimated_cost

        models_data.append(
            {
                "model": model_name,
                "total_tokens": total_tokens,
                "estimated_cost_usd": estimated_cost,
                "query_count": query_count,
                "avg_tokens_per_query": round(avg_tokens, 1),
            }
        )

    return {
        "models": models_data,
        "total_cost_usd": round(total_cost_usd, 6),
        "window_days": days,
    }


# ---------------------------------------------------------------------------
# GET /api/analytics/{org_id}/top-queries
# ---------------------------------------------------------------------------


@router.get("/{org_id}/top-queries")
async def analytics_top_queries(
    org_id: uuid.UUID,
    days: int = Query(30, ge=1, le=365, description="Look-back window in days"),
    limit: int = Query(10, ge=1, le=100, description="Max number of patterns to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Most frequent query patterns — grouped by first 100 chars normalised."""
    await _assert_org_access(org_id, current_user, db)

    window_start = datetime.now(UTC) - timedelta(days=days)

    result = await db.execute(
        text(
            """
            SELECT
                LOWER(TRIM(LEFT(m.content, 100)))          AS query_preview,
                COUNT(m.id)                                 AS cnt,
                ARRAY_AGG(DISTINCT ass.legal_area)
                    FILTER (WHERE ass.legal_area IS NOT NULL) AS legal_areas,
                MAX(m.created_at)                           AS last_asked
            FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            JOIN users u ON u.id = c.user_id
            JOIN org_memberships om ON om.user_id = u.id
            -- join to assistant reply in same conversation to get legal_area
            LEFT JOIN LATERAL (
                SELECT a.legal_area
                FROM messages a
                WHERE a.conversation_id = m.conversation_id
                  AND a.role = 'assistant'
                  AND a.created_at > m.created_at
                ORDER BY a.created_at
                LIMIT 1
            ) ass ON TRUE
            WHERE om.organization_id = :org_id
              AND om.is_active = TRUE
              AND m.role = 'user'
              AND m.content IS NOT NULL
              AND m.created_at >= :since
            GROUP BY query_preview
            ORDER BY cnt DESC
            LIMIT :limit
            """
        ),
        {"org_id": org_id, "since": window_start, "limit": limit},
    )

    rows = result.fetchall()

    queries = [
        {
            "query_preview": row.query_preview,
            "count": int(row.cnt),
            "legal_areas": [a for a in (row.legal_areas or []) if a] or [],
            "last_asked": row.last_asked.isoformat() if row.last_asked else None,
        }
        for row in rows
    ]

    return {"queries": queries, "window_days": days}


# ---------------------------------------------------------------------------
# GET /api/analytics/{org_id}/export
# ---------------------------------------------------------------------------


@router.get("/{org_id}/export")
async def analytics_export(
    org_id: uuid.UUID,
    days: int = Query(30, ge=1, le=365, description="Look-back window in days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Export analytics as CSV (date, user_email, query_preview, legal_area,
    agent_used, model, latency_ms, tokens_used)."""
    await _assert_org_access(org_id, current_user, db)

    window_start = datetime.now(UTC) - timedelta(days=days)

    result = await db.execute(
        text(
            """
            SELECT
                ass.created_at,
                u.email            AS user_email,
                LEFT(usr_m.content, 200) AS query_preview,
                ass.legal_area,
                ass.agent_used,
                ass.model,
                ass.latency_ms,
                ass.tokens_used
            FROM messages ass
            JOIN conversations c ON c.id = ass.conversation_id
            JOIN users u ON u.id = c.user_id
            JOIN org_memberships om ON om.user_id = u.id
            -- get the user message that preceded this assistant reply
            LEFT JOIN LATERAL (
                SELECT m2.content
                FROM messages m2
                WHERE m2.conversation_id = ass.conversation_id
                  AND m2.role = 'user'
                  AND m2.created_at < ass.created_at
                ORDER BY m2.created_at DESC
                LIMIT 1
            ) usr_m ON TRUE
            WHERE om.organization_id = :org_id
              AND om.is_active = TRUE
              AND ass.role = 'assistant'
              AND ass.created_at >= :since
            ORDER BY ass.created_at DESC
            """
        ),
        {"org_id": org_id, "since": window_start},
    )

    rows = result.fetchall()

    # Build CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["date", "user_email", "query_preview", "legal_area", "agent_used", "model",
         "latency_ms", "tokens_used"]
    )
    for row in rows:
        writer.writerow(
            [
                row.created_at.isoformat() if row.created_at else "",
                row.user_email or "",
                (row.query_preview or "").replace("\n", " ").replace("\r", " "),
                row.legal_area or "",
                row.agent_used or "",
                row.model or "",
                row.latency_ms if row.latency_ms is not None else "",
                row.tokens_used if row.tokens_used is not None else "",
            ]
        )

    csv_bytes = output.getvalue().encode("utf-8-sig")  # utf-8-sig for Excel compat
    today_str = date.today().isoformat()
    filename = f"tukijuris-analytics-{org_id}-{today_str}.csv"

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
