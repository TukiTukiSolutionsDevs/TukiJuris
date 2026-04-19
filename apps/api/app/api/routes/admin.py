"""Admin endpoints — system stats, user management, activity log, knowledge base."""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RateLimitBucket, RateLimitGuard, get_db
from app.models.user import User
from app.rbac.audit import AuditService
from app.rbac.dependencies import require_permission
from app.rbac.schemas import AuditLogEntry, AuditLogPage
from app.api.routes.admin_saas import _ensure_admin

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# GET /api/admin/stats
# ---------------------------------------------------------------------------

@router.get("/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("reports:read")),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> dict[str, Any]:
    """System overview: user counts, document KB stats, query activity."""
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    # --- scalar counts ---
    total_users = await db.scalar(text("SELECT COUNT(*) FROM users"))
    total_organizations = await db.scalar(text("SELECT COUNT(*) FROM organizations"))
    total_conversations = await db.scalar(text("SELECT COUNT(*) FROM conversations"))
    total_messages = await db.scalar(text("SELECT COUNT(*) FROM messages"))
    total_chunks = await db.scalar(text("SELECT COUNT(*) FROM document_chunks"))
    total_documents = await db.scalar(text("SELECT COUNT(*) FROM documents"))

    queries_today_result = await db.execute(
        text(
            "SELECT COUNT(*) FROM messages "
            "WHERE role = 'user' AND created_at >= :since"
        ),
        {"since": today_start},
    )
    queries_today = queries_today_result.scalar() or 0

    # --- chunks by area ---
    chunks_by_area_result = await db.execute(
        text(
            "SELECT legal_area, COUNT(*) AS cnt "
            "FROM document_chunks "
            "GROUP BY legal_area "
            "ORDER BY cnt DESC"
        )
    )
    chunks_by_area = {row.legal_area: row.cnt for row in chunks_by_area_result.fetchall()}

    # --- users by plan ---
    users_by_plan_result = await db.execute(
        text(
            "SELECT plan, COUNT(*) AS cnt "
            "FROM users "
            "GROUP BY plan "
            "ORDER BY cnt DESC"
        )
    )
    users_by_plan = {row.plan: row.cnt for row in users_by_plan_result.fetchall()}

    return {
        "total_users": total_users or 0,
        "total_organizations": total_organizations or 0,
        "total_conversations": total_conversations or 0,
        "total_messages": total_messages or 0,
        "queries_today": queries_today,
        "total_chunks": total_chunks or 0,
        "total_documents": total_documents or 0,
        "chunks_by_area": chunks_by_area,
        "users_by_plan": users_by_plan,
    }


# ---------------------------------------------------------------------------
# GET /api/admin/users
# ---------------------------------------------------------------------------

@router.get("/users")
async def admin_users(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Filter by email substring"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("users:read")),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> dict[str, Any]:
    """Paginated user list with organisation name and query count this month."""
    _ensure_admin(user)
    offset = (page - 1) * per_page

    # Build WHERE clause for optional email search
    where = "WHERE 1=1"
    params: dict[str, Any] = {"limit": per_page, "offset": offset}

    if search:
        where += " AND u.email ILIKE :search"
        params["search"] = f"%{search}%"

    month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    params["month_start"] = month_start

    # Total count (for pagination metadata)
    count_sql = f"SELECT COUNT(*) FROM users u {where}"
    total_result = await db.execute(text(count_sql), params)
    total = total_result.scalar() or 0

    # User rows + org name + query count this month + last_active + byok_count (admin-saas-panel)
    rows_sql = f"""
        SELECT
            u.id,
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
        {where}
        ORDER BY u.created_at DESC
        LIMIT :limit OFFSET :offset
    """
    rows_result = await db.execute(text(rows_sql), params)
    users = []
    for row in rows_result.mappings().fetchall():
        users.append({
            "id": str(row["id"]),
            "email": row["email"],
            "full_name": row["full_name"],
            "is_active": row["is_active"],
            "is_admin": row["is_admin"],
            "plan": row["plan"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "org_name": row["org_name"],
            "queries_this_month": row["queries_this_month"],
            "last_active": row["last_active"].isoformat() if row["last_active"] else None,
            "byok_count": int(row["byok_count"] or 0),
        })

    return {
        "users": users,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


# ---------------------------------------------------------------------------
# GET /api/admin/activity
# ---------------------------------------------------------------------------

@router.get("/activity")
async def admin_activity(
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    area: str | None = Query(None, description="Filter by legal area"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("reports:read")),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> dict[str, Any]:
    """Recent message activity log: user, area, agent, model, latency, timestamp."""
    where = "WHERE m.role = 'assistant'"
    params: dict[str, Any] = {"limit": limit}

    if area:
        where += " AND m.legal_area = :area"
        params["area"] = area

    sql = f"""
        SELECT
            u.email         AS user_email,
            m.legal_area,
            m.agent_used,
            m.model,
            m.latency_ms,
            m.created_at
        FROM messages m
        JOIN conversations c ON c.id = m.conversation_id
        JOIN users u ON u.id = c.user_id
        {where}
        ORDER BY m.created_at DESC
        LIMIT :limit
    """
    result = await db.execute(text(sql), params)
    rows = result.mappings().fetchall()

    activity = [
        {
            "user_email": row["user_email"],
            "legal_area": row["legal_area"],
            "agent_used": row["agent_used"],
            "model": row["model"],
            "latency_ms": row["latency_ms"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
        for row in rows
    ]

    return {"activity": activity, "count": len(activity)}


# ---------------------------------------------------------------------------
# GET /api/admin/knowledge
# ---------------------------------------------------------------------------

@router.get("/knowledge")
async def admin_knowledge(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("reports:read")),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> dict[str, Any]:
    """Detailed knowledge base stats: chunks by area, doc breakdown, embedding coverage."""

    # Chunks + documents per area
    area_stats_result = await db.execute(
        text(
            """
            SELECT
                dc.legal_area,
                COUNT(dc.id)       AS chunk_count,
                COUNT(DISTINCT dc.document_id) AS doc_count
            FROM document_chunks dc
            GROUP BY dc.legal_area
            ORDER BY chunk_count DESC
            """
        )
    )
    areas: list[dict] = []
    for row in area_stats_result.mappings().fetchall():
        areas.append({
            "area": row["legal_area"],
            "chunk_count": row["chunk_count"],
            "doc_count": row["doc_count"],
        })

    # Document breakdown: id, title, area, chunk count, most recent chunk
    doc_breakdown_result = await db.execute(
        text(
            """
            SELECT
                d.id,
                d.title,
                d.legal_area,
                d.document_number,
                d.created_at,
                COUNT(dc.id) AS chunk_count
            FROM documents d
            LEFT JOIN document_chunks dc ON dc.document_id = d.id
            GROUP BY d.id, d.title, d.legal_area, d.document_number, d.created_at
            ORDER BY d.created_at DESC
            """
        )
    )
    documents: list[dict] = []
    for row in doc_breakdown_result.mappings().fetchall():
        documents.append({
            "id": str(row["id"]),
            "title": row["title"],
            "legal_area": row["legal_area"],
            "document_number": row["document_number"],
            "chunk_count": row["chunk_count"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        })

    # Embedding coverage: how many chunks have a non-null embedding vector
    total_chunks = await db.scalar(text("SELECT COUNT(*) FROM document_chunks"))
    embedded_chunks = await db.scalar(
        text("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL")
    )
    total_chunks = total_chunks or 0
    embedded_chunks = embedded_chunks or 0
    coverage_pct = round(embedded_chunks / total_chunks * 100, 1) if total_chunks > 0 else 0.0

    return {
        "chunks_by_area": areas,
        "documents": documents,
        "embedding_coverage": {
            "total_chunks": total_chunks,
            "embedded_chunks": embedded_chunks,
            "coverage_pct": coverage_pct,
        },
    }


# ---------------------------------------------------------------------------
# GET /api/admin/audit-log
# ---------------------------------------------------------------------------


@router.get("/audit-log")
async def admin_audit_log(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user_id: uuid.UUID | None = Query(None, description="Filter by actor user ID"),
    action: str | None = Query(None, description="Filter by action (e.g. role.assign)"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    date_from: datetime | None = Query(None, description="Lower bound on created_at (inclusive)"),
    date_to: datetime | None = Query(None, description="Upper bound on created_at (inclusive)"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("audit_log:read")),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> AuditLogPage:
    """Paginated audit log. Requires audit_log:read permission."""
    audit_svc = AuditService(db=db)

    filters = {
        k: v
        for k, v in {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "date_from": date_from,
            "date_to": date_to,
        }.items()
        if v is not None
    }

    items, total = await audit_svc.query_log(
        page=page,
        page_size=page_size,
        filters=filters,
    )

    return AuditLogPage(
        items=[AuditLogEntry.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
