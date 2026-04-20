"""Advanced search routes — full-text search with filters, suggestions, saved searches, history."""

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RateLimitBucket, RateLimitGuard, get_current_user, get_db, get_optional_user
from app.core.validators import _VALID_LEGAL_AREAS
from app.models.search import SavedSearch, SearchHistory
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

# ---------------------------------------------------------------------------
# Whitelists — prevent SQL injection in dynamic ORDER BY / filter clauses
# ---------------------------------------------------------------------------

_VALID_SORT_OPTIONS: frozenset[str] = frozenset(
    {"relevance", "date_desc", "date_asc"}
)

_VALID_DOCUMENT_TYPES: frozenset[str] = frozenset(
    {
        "ley",
        "decreto_supremo",
        "decreto_legislativo",
        "resolucion",
        "resolucion_ministerial",
        "sentencia",
        "casacion",
        "constitucion",
        "reglamento",
    }
)

_VALID_HIERARCHY: frozenset[str] = frozenset(
    {"constitucional", "legal", "reglamentario"}
)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class SearchFilters(BaseModel):
    areas: list[str] | None = None
    document_types: list[str] | None = None
    date_from: str | None = None
    date_to: str | None = None
    hierarchy: str | None = None
    source: str | None = None


class AdvancedSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    filters: SearchFilters | None = None
    sort: str = Field(default="relevance")
    page: int = Field(default=1, ge=1, le=1000)
    per_page: int = Field(default=20, ge=1, le=100)


class SearchResultItem(BaseModel):
    id: str
    document_id: str
    title: str
    document_type: str
    document_number: str | None
    legal_area: str
    hierarchy: str | None
    source: str
    publication_date: str | None
    snippet: str
    score: float


class PaginatedSearchResponse(BaseModel):
    results: list[SearchResultItem]
    total: int
    page: int
    per_page: int
    total_pages: int
    query: str


class SavedSearchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    query: str = Field(..., min_length=1, max_length=500)
    filters: SearchFilters | None = None


class SavedSearchResponse(BaseModel):
    id: str
    name: str
    query: str
    filters: dict | None
    created_at: str


class SearchHistoryItem(BaseModel):
    id: str
    query: str
    filters: dict | None
    results_count: int
    created_at: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_filters(filters: SearchFilters | None) -> None:
    """Raise 422 if any filter value falls outside the allowed whitelists."""
    if not filters:
        return

    if filters.areas:
        for area in filters.areas:
            if area not in _VALID_LEGAL_AREAS:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Area legal invalida: '{area}'",
                )

    if filters.document_types:
        for dt in filters.document_types:
            if dt not in _VALID_DOCUMENT_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Tipo de documento invalido: '{dt}'",
                )

    if filters.hierarchy and filters.hierarchy not in _VALID_HIERARCHY:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Jerarquia invalida: '{filters.hierarchy}'",
        )

    if filters.date_from and filters.date_to and filters.date_from > filters.date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La fecha de fin no puede ser anterior a la fecha de inicio",
        )


def _build_search_query(
    query_text: str,
    filters: SearchFilters | None,
    sort: str,
    page: int,
    per_page: int,
) -> tuple[str, str, dict[str, Any]]:
    """Build the parameterized advanced search SQL.

    Returns (results_sql, count_sql, params_dict).
    All dynamic values go through bind parameters — no f-string interpolation
    of user-supplied data into the query string.
    """
    params: dict[str, Any] = {"query": query_text}

    # Base SELECT — rank by BM25 / ts_rank when sort=relevance
    select_clause = """
        SELECT
            dc.id            AS chunk_id,
            dc.document_id,
            d.title,
            d.document_type,
            d.document_number,
            d.legal_area,
            d.hierarchy,
            d.source,
            d.publication_date,
            dc.content       AS snippet,
            ts_rank(
                to_tsvector('spanish', dc.content),
                plainto_tsquery('spanish', :query)
            )                AS score
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE d.is_active = TRUE
          AND to_tsvector('spanish', dc.content)
              @@ plainto_tsquery('spanish', :query)
    """

    # Dynamic WHERE clauses — values go through bind params, names go
    # through the whitelist-validated frozensets above.
    extra_where: list[str] = []

    if filters:
        if filters.areas:
            # Already whitelist-validated — safe to build IN clause with
            # positional placeholders.
            placeholders = ", ".join(
                f":area_{i}" for i in range(len(filters.areas))
            )
            extra_where.append(f"d.legal_area IN ({placeholders})")
            for i, area in enumerate(filters.areas):
                params[f"area_{i}"] = area

        if filters.document_types:
            placeholders = ", ".join(
                f":dtype_{i}" for i in range(len(filters.document_types))
            )
            extra_where.append(f"d.document_type IN ({placeholders})")
            for i, dt in enumerate(filters.document_types):
                params[f"dtype_{i}"] = dt

        if filters.date_from:
            extra_where.append("d.publication_date >= :date_from")
            params["date_from"] = filters.date_from

        if filters.date_to:
            extra_where.append("d.publication_date <= :date_to")
            params["date_to"] = filters.date_to

        if filters.hierarchy:
            extra_where.append("d.hierarchy = :hierarchy")
            params["hierarchy"] = filters.hierarchy

        if filters.source:
            extra_where.append("d.source ILIKE :source")
            params["source"] = f"%{filters.source}%"

    if extra_where:
        select_clause += "\n  AND " + "\n  AND ".join(extra_where)

    # ORDER BY — value is whitelist-validated before reaching here
    if sort == "date_desc":
        order_clause = "ORDER BY d.publication_date DESC NULLS LAST, score DESC"
    elif sort == "date_asc":
        order_clause = "ORDER BY d.publication_date ASC NULLS LAST, score DESC"
    else:
        order_clause = "ORDER BY score DESC"

    offset = (page - 1) * per_page
    params["limit"] = per_page
    params["offset"] = offset

    full_sql = f"{select_clause}\n{order_clause}\nLIMIT :limit OFFSET :offset"

    # Count query (reuse same WHERE, strip pagination)
    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE d.is_active = TRUE
          AND to_tsvector('spanish', dc.content)
              @@ plainto_tsquery('spanish', :query)
    """
    if extra_where:
        count_sql += "\n  AND " + "\n  AND ".join(extra_where)

    return full_sql, count_sql, params


async def _log_search_history(
    db_factory: Any,
    user_id: uuid.UUID,
    query: str,
    filters: SearchFilters | None,
    results_count: int,
) -> None:
    """Fire-and-forget — saves a search event to history without blocking."""
    try:
        from app.core.database import async_session_factory

        async with async_session_factory() as session:
            entry = SearchHistory(
                user_id=user_id,
                query=query,
                filters=filters.model_dump(exclude_none=True) if filters else None,
                results_count=results_count,
            )
            session.add(entry)
            await session.commit()
    except Exception:
        # History logging must never fail a search request
        logger.warning("Failed to log search history", exc_info=True)


# ---------------------------------------------------------------------------
# POST /api/search/advanced
# ---------------------------------------------------------------------------


@router.post(
    "/advanced",
    response_model=PaginatedSearchResponse,
    summary="Advanced search with filters",
    description=(
        "Full-text search over the legal knowledge base with optional filters "
        "for area, document type, date range, hierarchy, and source. "
        "Supports pagination and three sort modes: relevance, date_desc, date_asc."
    ),
)
async def advanced_search(
    body: AdvancedSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> PaginatedSearchResponse:
    # Validate sort option (whitelist)
    if body.sort not in _VALID_SORT_OPTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Opcion de orden invalida: '{body.sort}'",
        )

    # Validate all filter values against whitelists
    _validate_filters(body.filters)

    # Build parameterized SQL
    full_sql, count_sql, params = _build_search_query(
        query_text=body.query,
        filters=body.filters,
        sort=body.sort,
        page=body.page,
        per_page=body.per_page,
    )

    # Execute count query
    count_result = await db.execute(text(count_sql), params)
    total_row = count_result.fetchone()
    total = int(total_row.total) if total_row else 0

    # Execute main query
    rows_result = await db.execute(text(full_sql), params)
    rows = rows_result.fetchall()

    results = [
        SearchResultItem(
            id=str(row.chunk_id),
            document_id=str(row.document_id),
            title=row.title,
            document_type=row.document_type,
            document_number=row.document_number,
            legal_area=row.legal_area,
            hierarchy=row.hierarchy,
            source=row.source,
            publication_date=(
                row.publication_date.isoformat() if row.publication_date else None
            ),
            snippet=(
                row.snippet[:500] + "..." if len(row.snippet) > 500 else row.snippet
            ),
            score=float(row.score),
        )
        for row in rows
    ]

    # Fire-and-forget history log for authenticated users
    if current_user:
        asyncio.create_task(
            _log_search_history(
                db_factory=None,
                user_id=current_user.id,
                query=body.query,
                filters=body.filters,
                results_count=total,
            )
        )

    total_pages = max(1, -(-total // body.per_page))  # ceiling division

    return PaginatedSearchResponse(
        results=results,
        total=total,
        page=body.page,
        per_page=body.per_page,
        total_pages=total_pages,
        query=body.query,
    )


# ---------------------------------------------------------------------------
# GET /api/search/suggestions
# ---------------------------------------------------------------------------


@router.get(
    "/suggestions",
    summary="Auto-suggest search terms",
    description=(
        "Returns up to `limit` suggestions based on recent search history "
        "and document titles matching the prefix query."
    ),
)
async def search_suggestions(
    q: str = Query(..., min_length=1, max_length=200, description="Prefix to suggest from"),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> dict[str, list[str]]:
    suggestions: list[str] = []
    seen: set[str] = set()

    # 1. User's own recent history (fast, personalized)
    if current_user:
        history_sql = text(
            """
            SELECT DISTINCT query
            FROM search_history
            WHERE user_id = :user_id
              AND query ILIKE :prefix
            ORDER BY MAX(created_at) DESC
            LIMIT :limit
            """
        )
        # GROUP BY needed for MAX — rewrite
        history_sql = text(
            """
            SELECT query
            FROM (
                SELECT query, MAX(created_at) AS last_used
                FROM search_history
                WHERE user_id = :user_id
                  AND query ILIKE :prefix
                GROUP BY query
            ) sub
            ORDER BY last_used DESC
            LIMIT :limit
            """
        )
        rows = await db.execute(
            history_sql,
            {"user_id": current_user.id, "prefix": f"{q}%", "limit": limit},
        )
        for row in rows.fetchall():
            if row.query not in seen:
                suggestions.append(row.query)
                seen.add(row.query)

    # 2. Global popular searches from history (fills remaining slots)
    remaining = limit - len(suggestions)
    if remaining > 0:
        global_sql = text(
            """
            SELECT query
            FROM (
                SELECT query, COUNT(*) AS freq
                FROM search_history
                WHERE query ILIKE :prefix
                GROUP BY query
            ) sub
            ORDER BY freq DESC
            LIMIT :limit
            """
        )
        rows = await db.execute(global_sql, {"prefix": f"{q}%", "limit": remaining * 2})
        for row in rows.fetchall():
            if row.query not in seen and len(suggestions) < limit:
                suggestions.append(row.query)
                seen.add(row.query)

    # 3. Document titles (fills any remaining slots)
    remaining = limit - len(suggestions)
    if remaining > 0:
        titles_sql = text(
            """
            SELECT DISTINCT title
            FROM documents
            WHERE title ILIKE :prefix
              AND is_active = TRUE
            ORDER BY title
            LIMIT :limit
            """
        )
        rows = await db.execute(titles_sql, {"prefix": f"{q}%", "limit": remaining})
        for row in rows.fetchall():
            if row.title not in seen and len(suggestions) < limit:
                suggestions.append(row.title)
                seen.add(row.title)

    return {"suggestions": suggestions[:limit]}


# ---------------------------------------------------------------------------
# POST /api/search/saved
# ---------------------------------------------------------------------------


@router.post(
    "/saved",
    response_model=SavedSearchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a search",
)
async def save_search(
    body: SavedSearchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> SavedSearchResponse:
    _validate_filters(body.filters)

    saved = SavedSearch(
        user_id=current_user.id,
        name=body.name,
        query=body.query,
        filters=body.filters.model_dump(exclude_none=True) if body.filters else None,
    )
    db.add(saved)
    await db.flush()

    return SavedSearchResponse(
        id=str(saved.id),
        name=saved.name,
        query=saved.query,
        filters=saved.filters,
        created_at=saved.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# GET /api/search/saved
# ---------------------------------------------------------------------------


@router.get(
    "/saved",
    response_model=list[SavedSearchResponse],
    summary="List saved searches",
)
async def list_saved_searches(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> list[SavedSearchResponse]:
    result = await db.execute(
        select(SavedSearch)
        .where(SavedSearch.user_id == current_user.id)
        .order_by(SavedSearch.created_at.desc())
        .limit(50)
    )
    items = result.scalars().all()

    return [
        SavedSearchResponse(
            id=str(s.id),
            name=s.name,
            query=s.query,
            filters=s.filters,
            created_at=s.created_at.isoformat(),
        )
        for s in items
    ]


# ---------------------------------------------------------------------------
# DELETE /api/search/saved/{id}
# ---------------------------------------------------------------------------


@router.delete(
    "/saved/{saved_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a saved search",
)
async def delete_saved_search(
    saved_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> None:
    result = await db.execute(
        select(SavedSearch).where(
            SavedSearch.id == saved_id,
            SavedSearch.user_id == current_user.id,
        )
    )
    saved = result.scalar_one_or_none()
    if not saved:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Busqueda no encontrada")

    await db.delete(saved)


# ---------------------------------------------------------------------------
# GET /api/search/history
# ---------------------------------------------------------------------------


@router.get(
    "/history",
    response_model=list[SearchHistoryItem],
    summary="Recent search history",
    description="Returns the last 20 searches for the authenticated user.",
)
async def search_history(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> list[SearchHistoryItem]:
    result = await db.execute(
        select(SearchHistory)
        .where(SearchHistory.user_id == current_user.id)
        .order_by(SearchHistory.created_at.desc())
        .limit(limit)
    )
    items = result.scalars().all()

    return [
        SearchHistoryItem(
            id=str(h.id),
            query=h.query,
            filters=h.filters,
            results_count=h.results_count,
            created_at=h.created_at.isoformat(),
        )
        for h in items
    ]
