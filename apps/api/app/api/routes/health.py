"""Health check endpoints — liveness, readiness, and knowledge base stats."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter(
    tags=["health"],
    responses={503: {"description": "Service unavailable"}},
)


@router.get(
    "/health",
    summary="Liveness check",
    description="Basic liveness probe. Returns `ok` if the API process is running. Used by load balancers and container orchestrators.",
    response_description="Service status string",
    responses={200: {"description": "API is alive"}},
)
async def health_check():
    """Basic health check."""
    return {"status": "ok", "service": "agente-derecho-api"}


@router.get(
    "/health/db",
    summary="Database connectivity check",
    description="Verifies that the API can reach the PostgreSQL database. Returns `error` with detail if the connection fails.",
    response_description="Database connection status",
    responses={
        200: {"description": "Database is reachable"},
        503: {"description": "Database connection failed"},
    },
)
async def health_db(db: AsyncSession = Depends(get_db)):
    """Database connectivity check."""
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


@router.get(
    "/health/ready",
    summary="Full readiness check",
    description=(
        "Deep readiness probe. Checks PostgreSQL connectivity AND the pgvector extension "
        "required for semantic search. Returns `degraded` if any subsystem is unhealthy. "
        "Use this endpoint for Kubernetes readiness probes."
    ),
    response_description="Status of each subsystem (database, pgvector)",
    responses={
        200: {"description": "All systems ready (status=ok) or partially degraded (status=degraded)"},
    },
)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Full readiness check — DB + pgvector."""
    checks = {}

    # Database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    # pgvector extension
    try:
        result = await db.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'"))
        version = result.scalar()
        checks["pgvector"] = f"ok (v{version})" if version else "not installed"
    except Exception:
        checks["pgvector"] = "error"

    all_ok = all(v.startswith("ok") for v in checks.values())
    return {"status": "ok" if all_ok else "degraded", "checks": checks}


@router.get(
    "/health/metrics",
    summary="Runtime metrics",
    description=(
        "Returns in-process counters: total requests, error rate, average latency, "
        "and request count by endpoint. Backed by an in-memory store — resets on restart."
    ),
    response_description="Aggregated runtime metrics",
    responses={200: {"description": "Metrics snapshot"}},
)
async def system_metrics():
    """Runtime metrics — request counts, latency, errors."""
    from app.core.monitoring import metrics

    return {"status": "ok", "metrics": metrics.get_stats()}


@router.get(
    "/health/knowledge",
    summary="Knowledge base statistics",
    description=(
        "Returns the number of indexed legal documents and text chunks, broken down by "
        "area of law. Useful to verify the RAG knowledge base is populated before querying."
    ),
    response_description="Document and chunk counts by legal area",
    responses={
        200: {"description": "Knowledge base stats"},
        503: {"description": "Could not connect to the vector database"},
    },
)
async def knowledge_stats():
    """Knowledge base statistics — documents and chunks by area."""
    from app.services.rag import rag_service

    try:
        stats = await rag_service.get_stats()
        return {"status": "ok", **stats}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get(
    "/health/cache",
    summary="Redis cache statistics",
    description=(
        "Returns Redis memory usage and total cached key count. "
        "Useful for verifying the cache layer is healthy and monitoring memory consumption."
    ),
    response_description="Cache memory stats and key count",
    responses={
        200: {"description": "Cache is reachable (status=ok) or unavailable (status=error)"},
    },
)
async def cache_stats():
    """Redis cache statistics — memory usage and key count."""
    from app.core.cache import cache

    try:
        r = await cache._get_redis()
        info = await r.info("memory")
        keys = await r.dbsize()
        return {
            "status": "ok",
            "keys": keys,
            "memory_used": info.get("used_memory_human", "?"),
            "memory_peak": info.get("used_memory_peak_human", "?"),
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
