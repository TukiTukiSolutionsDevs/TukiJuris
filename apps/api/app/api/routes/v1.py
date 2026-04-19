"""
Public API v1 — versioned endpoints for external developer integrations.

Authentication: JWT Bearer token OR API key (X-API-Key header or Bearer ak_...).
All endpoints enforce scope checks for API key auth.

Base path: /api/v1
"""

import time
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import LEGAL_AREAS, legal_orchestrator
from app.api.deps import RateLimitBucket, RateLimitGuard, get_authenticated_user, get_db
from app.models.api_key import APIKey
from app.models.user import User
from app.services.llm_adapter import llm_service
from app.services.rag import rag_service

router = APIRouter(
    prefix="/v1",
    tags=["public-api-v1"],
    responses={
        401: {"description": "Authentication required — provide a valid JWT or API key"},
        403: {"description": "API key does not have the required scope for this endpoint"},
        429: {"description": "Rate limit exceeded — see X-RateLimit-Limit response header"},
        502: {"description": "AI processing error — upstream LLM or vector DB failure"},
    },
)


# ---------------------------------------------------------------------------
# Scope helper
# ---------------------------------------------------------------------------

_SCOPE_ERROR = {
    "query": "This API key does not have the 'query' scope",
    "search": "This API key does not have the 'search' scope",
    "analyze": "This API key does not have the 'analyze' scope",
    "documents": "This API key does not have the 'documents' scope",
}


async def _check_scope(request: Request, db: AsyncSession, required_scope: str) -> None:
    """
    If the request is authenticated via API key, verify the key has the required scope.
    JWT-authenticated requests always pass (scopes are not checked on JWT).
    """
    api_key_str = request.headers.get("X-API-Key", "").strip()
    if not api_key_str:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer ak_"):
            api_key_str = auth[len("Bearer "):]

    if not api_key_str:
        return  # JWT path — no scope check

    import hashlib

    key_hash = hashlib.sha256(api_key_str.encode()).hexdigest()
    result = await db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
    api_key_obj = result.scalar_one_or_none()

    if api_key_obj and required_scope not in (api_key_obj.scopes or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_SCOPE_ERROR.get(required_scope, f"Missing scope: {required_scope}"),
        )


def _rate_limit_headers(rate_limit: int) -> dict[str, str]:
    return {
        "X-RateLimit-Limit": str(rate_limit),
        "X-RateLimit-Window": "60s",
    }


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class V1QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    legal_area: str | None = Field(None, description="Optional area hint (e.g. 'penal')")
    model: str | None = Field(None, description="LLM model override")


class V1CitationItem(BaseModel):
    document: str
    article: str | None
    content: str
    score: float | None = None


class V1QueryResponse(BaseModel):
    answer: str
    citations: list[V1CitationItem]
    area_detected: str
    agent_used: str
    model_used: str
    tokens_used: int | None
    latency_ms: int


class V1SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    area: str | None = None
    limit: int = Field(10, ge=1, le=50)


class V1SearchResult(BaseModel):
    content: str
    document: str
    article: str | None
    score: float
    legal_area: str


class V1SearchResponse(BaseModel):
    results: list[V1SearchResult]
    total: int
    query: str


class V1AnalyzeRequest(BaseModel):
    case_description: str = Field(..., min_length=10, max_length=5000)
    areas: list[str] | None = None


class V1AnalyzeResponse(BaseModel):
    areas_detected: list[str]
    analysis: str
    model_used: str
    latency_ms: int


class V1AreaInfo(BaseModel):
    id: str
    name: str
    chunks: int


class V1AreasResponse(BaseModel):
    areas: list[V1AreaInfo]


class V1DocumentItem(BaseModel):
    id: uuid.UUID
    title: str
    document_number: str | None
    legal_area: str | None
    chunk_count: int | None = None


class V1DocumentsResponse(BaseModel):
    documents: list[V1DocumentItem]
    total: int


class V1UsageResponse(BaseModel):
    queries_today: int
    queries_month: int
    plan: str
    # BYOK: No monthly query limits — platform charges for access, not queries.
    # Consumption depends on the user's own provider plan/quota.
    note: str
    # API key metadata
    limit_per_minute: int
    key_name: str | None


# Pretty names for legal areas
_AREA_NAMES: dict[str, str] = {
    "civil": "Derecho Civil",
    "penal": "Derecho Penal",
    "laboral": "Derecho Laboral",
    "tributario": "Derecho Tributario",
    "constitucional": "Derecho Constitucional",
    "administrativo": "Derecho Administrativo",
    "corporativo": "Derecho Corporativo",
    "registral": "Derecho Registral",
    "competencia": "Competencia y Propiedad Intelectual",
    "compliance": "Compliance",
    "comercio_exterior": "Comercio Exterior",
}


# ---------------------------------------------------------------------------
# POST /v1/query
# ---------------------------------------------------------------------------


@router.post(
    "/query",
    response_model=V1QueryResponse,
    summary="Legal query",
    description=(
        "Submit a legal question to the AI orchestrator. The system automatically classifies "
        "the question by area of law (civil, penal, laboral, etc.), retrieves relevant context "
        "from the knowledge base using hybrid BM25 + semantic search, and generates an answer "
        "with citations to the original legal texts.\n\n"
        "**Authentication**: JWT Bearer token or API key with `query` scope.\n\n"
        "**Latency**: typically 2–8 seconds depending on the selected model and query complexity.\n\n"
        "**Example request body**:\n"
        "```json\n"
        '{"query": "Requisitos para un despido justificado en Peru"}\n'
        "```"
    ),
    response_description="AI-generated legal answer with citations, detected area, and metadata",
    responses={
        200: {"description": "Successful query — answer with citations returned"},
        401: {"description": "Authentication required"},
        403: {"description": "API key missing `query` scope"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "AI processing error"},
    },
)
async def v1_query(
    body: V1QueryRequest,
    request: Request,
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """
    Submit a legal query and receive a cited answer.

    Requires scope: **query**
    """
    await _check_scope(request, db, "query")
    start = time.time()

    try:
        result = await legal_orchestrator.process_query(
            query=body.query,
            model=body.model,
            legal_area_hint=body.legal_area,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI processing error: {exc}",
        )

    latency_ms = int((time.time() - start) * 1000)

    raw_citations = result.get("citations") or []
    citations = [
        V1CitationItem(
            document=c.get("document", ""),
            article=c.get("article"),
            content=c.get("content", ""),
            score=c.get("score"),
        )
        for c in raw_citations
    ]

    return V1QueryResponse(
        answer=result["response"],
        citations=citations,
        area_detected=result.get("legal_area", "unknown"),
        agent_used=result.get("agent_used", "unknown"),
        model_used=result.get("model_used", "unknown"),
        tokens_used=result.get("tokens_used"),
        latency_ms=latency_ms,
    )


# ---------------------------------------------------------------------------
# POST /v1/search
# ---------------------------------------------------------------------------


@router.post(
    "/search",
    response_model=V1SearchResponse,
    summary="Search the legal knowledge base",
    description=(
        "Perform a hybrid BM25 + semantic search over the indexed Peruvian legal corpus. "
        "Returns ranked document chunks with relevance scores. Use this endpoint when you "
        "need raw search results rather than a generated answer — for example, to build "
        "your own legal research UI or to pre-fetch context before calling `/v1/query`.\n\n"
        "**Authentication**: JWT Bearer token or API key with `search` scope.\n\n"
        "**Tip**: Pass `area` to constrain results to a single area of law and improve precision."
    ),
    response_description="Ranked list of matching document chunks with source information",
    responses={
        200: {"description": "Search results returned"},
        401: {"description": "Authentication required"},
        403: {"description": "API key missing `search` scope"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def v1_search(
    body: V1SearchRequest,
    request: Request,
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
):
    """
    Search the legal knowledge base and return ranked chunks.

    Requires scope: **search**
    """
    await _check_scope(request, db, "search")

    results = await rag_service.search_hybrid(
        query=body.query,
        legal_area=body.area,
        limit=body.limit,
    )

    items = [
        V1SearchResult(
            content=r["content"],
            document=r.get("document_title", ""),
            article=r.get("article_number"),
            score=float(r.get("hybrid_score") or r.get("bm25_score") or r.get("score") or 0.0),
            legal_area=r.get("legal_area", ""),
        )
        for r in results
    ]

    return V1SearchResponse(results=items, total=len(items), query=body.query)


# ---------------------------------------------------------------------------
# POST /v1/analyze
# ---------------------------------------------------------------------------


@router.post(
    "/analyze",
    response_model=V1AnalyzeResponse,
    summary="Analyze a legal case",
    description=(
        "Submit a description of a legal case or situation and receive a structured analysis. "
        "The system retrieves applicable regulations from the knowledge base, identifies "
        "all relevant areas of law, and produces a structured analysis covering: "
        "applicable regulations, rights and obligations, potential legal courses of action, "
        "relevant deadlines, and a general recommendation.\n\n"
        "**Authentication**: JWT Bearer token or API key with `analyze` scope.\n\n"
        "**Latency**: typically 4–12 seconds — this endpoint runs a more thorough retrieval "
        "pipeline than `/v1/query`.\n\n"
        "**Tip**: Provide a detailed `case_description` (100+ words) for better analysis quality."
    ),
    response_description="Structured legal analysis with detected areas, normativa, and recommendations",
    responses={
        200: {"description": "Analysis generated"},
        401: {"description": "Authentication required"},
        403: {"description": "API key missing `analyze` scope"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "AI processing error"},
    },
)
async def v1_analyze(
    body: V1AnalyzeRequest,
    request: Request,
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """
    Analyze a legal case description across multiple areas.

    Requires scope: **analyze**
    """
    await _check_scope(request, db, "analyze")
    start = time.time()

    # Retrieve relevant context
    context_results = await rag_service.search_bm25(
        query=body.case_description, limit=10
    )

    areas_detected: list[str] = []
    context_parts: list[str] = []
    for r in context_results:
        area = r.get("legal_area", "")
        if area and area not in areas_detected:
            areas_detected.append(area)
        src = f"[{r.get('document_title', '')}] {r['content']}"
        context_parts.append(src)

    # Filter by requested areas
    if body.areas:
        areas_detected = [a for a in areas_detected if a in body.areas] or areas_detected

    context_str = "\n\n---\n\n".join(context_parts[:8])

    analysis_prompt = (
        f"Eres un analista jurídico experto en derecho peruano. "
        f"Analiza el siguiente caso:\n\n{body.case_description}\n\n"
        f"NORMATIVA RELEVANTE:\n{context_str}\n\n"
        f"Proporciona un análisis estructurado con: áreas del derecho involucradas, "
        f"normativa aplicable, derechos y obligaciones, posibles vías legales, "
        f"plazos importantes, y recomendación general."
    )

    try:
        llm_result = await llm_service.completion(
            messages=[
                {"role": "system", "content": "Eres un analista jurídico peruano experto."},
                {"role": "user", "content": analysis_prompt},
            ]
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI processing error: {exc}",
        )

    latency_ms = int((time.time() - start) * 1000)

    return V1AnalyzeResponse(
        areas_detected=areas_detected,
        analysis=llm_result.get("content", ""),
        model_used=llm_result.get("model", "unknown"),
        latency_ms=latency_ms,
    )


# ---------------------------------------------------------------------------
# GET /v1/areas
# ---------------------------------------------------------------------------


@router.get(
    "/areas",
    response_model=V1AreasResponse,
    summary="List legal areas",
    description=(
        "Returns all 11 areas of Peruvian law available in the knowledge base. "
        "Use the `id` field as the `legal_area` parameter in `/v1/query` and `/v1/search` "
        "to constrain processing to a specific domain.\n\n"
        "**Authentication**: JWT Bearer token or any valid API key (no specific scope required)."
    ),
    response_description="List of legal area identifiers with display names",
    responses={
        200: {"description": "List of available legal areas"},
        401: {"description": "Authentication required"},
    },
)
async def v1_areas(
    current_user: User = Depends(get_authenticated_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
):
    """List all available legal areas in the knowledge base."""
    # Descriptions sourced from /chat/agents — kept in sync with the orchestrator
    _AREA_DESCRIPTIONS: dict[str, str] = {
        "civil": "Código Civil, CPC, Familia, Sucesiones, Contratos, Obligaciones",
        "penal": "Código Penal, NCPP, Ejecución Penal",
        "laboral": "LPCL, Seguridad y Salud, Relaciones Colectivas",
        "tributario": "Código Tributario, IR, IGV, SUNAT",
        "constitucional": "Constitución 1993, Procesos Constitucionales, TC",
        "administrativo": "LPAG, Contrataciones del Estado",
        "corporativo": "LGS, Mercado de Valores, MYPE",
        "registral": "SUNARP, Registros Públicos",
        "competencia": "INDECOPI, Marcas, Patentes, Consumidor",
        "compliance": "Datos Personales, Anticorrupción, Lavado de Activos",
        "comercio_exterior": "Aduanas, TLC, MINCETUR",
    }
    areas = [
        V1AreaInfo(
            id=area,
            name=_AREA_NAMES.get(area, area.title()),
            chunks=0,  # chunk count available via /v1/documents endpoint
        )
        for area in LEGAL_AREAS
    ]
    # Attach descriptions to the response as additional context
    # (V1AreaInfo doesn't have a description field — extend the dict response instead)
    return {
        "areas": [
            {
                "id": a.id,
                "name": a.name,
                "description": _AREA_DESCRIPTIONS.get(a.id, ""),
                "chunks": a.chunks,
            }
            for a in areas
        ]
    }


# ---------------------------------------------------------------------------
# GET /v1/documents
# ---------------------------------------------------------------------------


@router.get(
    "/documents",
    response_model=V1DocumentsResponse,
    summary="List indexed legal documents",
    description=(
        "Browse the catalog of legal documents indexed in the knowledge base. "
        "Returns document metadata including title, document number, legal area, "
        "and the number of indexed text chunks. Supports pagination via `limit` and `offset`.\n\n"
        "**Authentication**: JWT Bearer token or API key with `documents` scope.\n\n"
        "**Tip**: Use `GET /api/v1/areas` to get valid area identifiers for the `area` filter."
    ),
    response_description="Paginated list of documents with metadata",
    responses={
        200: {"description": "Document list returned"},
        401: {"description": "Authentication required"},
        403: {"description": "API key missing `documents` scope"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def v1_documents(
    request: Request,
    area: str | None = Query(None, description="Filter by legal area"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
):
    """
    List documents in the knowledge base.

    Requires scope: **documents**
    """
    await _check_scope(request, db, "documents")

    # Use raw asyncpg via rag_service for consistent access pattern
    pool = await rag_service._get_pool()

    async with pool.acquire() as conn:
        if area:
            rows = await conn.fetch(
                """
                SELECT d.id, d.title, d.document_number, d.legal_area,
                       COUNT(dc.id)::int AS chunk_count
                FROM documents d
                LEFT JOIN document_chunks dc ON dc.document_id = d.id
                WHERE d.legal_area = $1
                GROUP BY d.id
                ORDER BY d.title
                LIMIT $2 OFFSET $3
                """,
                area,
                limit,
                offset,
            )
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM documents WHERE legal_area = $1", area
            )
        else:
            rows = await conn.fetch(
                """
                SELECT d.id, d.title, d.document_number, d.legal_area,
                       COUNT(dc.id)::int AS chunk_count
                FROM documents d
                LEFT JOIN document_chunks dc ON dc.document_id = d.id
                GROUP BY d.id
                ORDER BY d.title
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
            total = await conn.fetchval("SELECT COUNT(*) FROM documents")

    docs = [
        V1DocumentItem(
            id=r["id"],
            title=r["title"],
            document_number=r.get("document_number"),
            legal_area=r.get("legal_area"),
            chunk_count=r.get("chunk_count"),
        )
        for r in rows
    ]

    return V1DocumentsResponse(documents=docs, total=int(total or 0))


# ---------------------------------------------------------------------------
# GET /v1/usage
# ---------------------------------------------------------------------------


@router.get(
    "/usage",
    response_model=V1UsageResponse,
    summary="API key usage stats",
    description=(
        "Returns usage counters for the API key used in the current request. "
        "Includes query counts for today and the current month, the rate limit "
        "configured for the key, and the key's display name.\n\n"
        "When authenticated via JWT (no API key), returns zeroed counters with "
        "the account's plan rate limit.\n\n"
        "**Authentication**: JWT Bearer token or any valid API key."
    ),
    response_description="Usage counters and rate limit for the current API key or user",
    responses={
        200: {"description": "Usage stats returned"},
        401: {"description": "Authentication required"},
    },
)
async def v1_usage(
    request: Request,
    current_user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
):
    """
    Return usage stats for the current user (or API key).

    Counts user queries for today and the current month from the messages table.
    """
    import hashlib

    api_key_str = request.headers.get("X-API-Key", "").strip()
    if not api_key_str:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer ak_"):
            api_key_str = auth[len("Bearer "):]

    key_obj: APIKey | None = None
    if api_key_str and api_key_str.startswith("ak_"):
        key_hash = hashlib.sha256(api_key_str.encode()).hexdigest()
        result = await db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
        key_obj = result.scalar_one_or_none()

    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Count user's queries today
    queries_today = await db.scalar(
        text("""
            SELECT COUNT(m.id) FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            WHERE c.user_id = :uid AND m.role = 'user' AND m.created_at >= :since
        """),
        {"uid": current_user.id, "since": today_start},
    ) or 0

    # Count user's queries this month
    queries_month = await db.scalar(
        text("""
            SELECT COUNT(m.id) FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            WHERE c.user_id = :uid AND m.role = 'user' AND m.created_at >= :since
        """),
        {"uid": current_user.id, "since": month_start},
    ) or 0

    return V1UsageResponse(
        queries_today=int(queries_today),
        queries_month=int(queries_month),
        plan=current_user.plan,
        # BYOK: TukiJuris does not limit queries — platform charges for access only.
        # Token/cost consumption depends on the user's own API key and provider plan.
        note=(
            "TukiJuris cobra por acceso a la plataforma, no por consultas. "
            "El consumo de modelos y costos depende de tu proveedor y tu propia API key."
        ),
        limit_per_minute=key_obj.rate_limit_per_minute if key_obj else 60,
        key_name=key_obj.name if key_obj else None,
    )
