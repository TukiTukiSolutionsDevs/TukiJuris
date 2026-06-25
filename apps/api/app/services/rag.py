"""
RAG Service — Retrieval-Augmented Generation for legal documents.

Uses hybrid search (BM25 full-text + vector similarity) to find
the most relevant legal chunks for a given query.

Search strategy (in order of preference):
  1. Hybrid search  — combines BM25 + cosine similarity (best recall+precision)
  2. Vector search  — pure cosine similarity via HNSW index
  3. BM25 search    — PostgreSQL ts_rank full-text (fallback / no embeddings)
"""

import asyncio
import logging
import time
from typing import Optional

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)

# Direct asyncpg URL (not async SQLAlchemy — faster for raw queries)
_DB_URL = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

# ──────────────────────────────────────────────────────────────────────────────
# Embedding client — lazy-init, module-level singleton
# ──────────────────────────────────────────────────────────────────────────────
_genai_configured: bool = False
_openai_client = None


async def _resolve_provider_key(provider: str) -> str:
    """Return the platform key for a provider.

    Reads first from the encrypted `platform_llm_keys` table (operator-managed
    via /admin?tab=claves). Falls back to the legacy settings field — which is
    expected to be empty in modern deployments. Returns "" if neither has a
    key, so callers can short-circuit cleanly.
    """
    from app.core.database import async_session_factory
    from app.services.platform_llm_key_service import get_platform_key

    try:
        async with async_session_factory() as db:
            key = await get_platform_key(provider, db)
            if key:
                return key
    except Exception as e:  # noqa: BLE001
        logger.warning("rag.platform_key_read_failed: provider=%s error=%s", provider, e)

    # Legacy env fallback. In current deployments settings.<provider>_api_key
    # is always "" — kept here only for backward compat with dev-time overrides.
    legacy = getattr(settings, f"{provider}_api_key", "") or ""
    return legacy


async def _configure_genai_async() -> bool:
    """Configure Google genai once. Returns True on success."""
    global _genai_configured
    if _genai_configured:
        return True
    google_key = await _resolve_provider_key("google")
    if not google_key:
        return False
    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=google_key)
        _genai_configured = True
        return True
    except ImportError:
        logger.warning("google-generativeai package not installed — vector search unavailable")
        return False


async def _get_openai_client_async():
    """Lazy-init OpenAI client (fallback embeddings). Returns None if unavailable.

    NOTE: We pass `base_url="https://api.openai.com/v1"` explicitly so that any
    `OPENAI_BASE_URL` env override (e.g. the codex-proxy at :5050, which doesn't
    implement /v1/embeddings) is ignored for the embedding path. We also set
    `max_retries=0` and a tight timeout so that a misconfigured key fails fast
    and the caller falls back to BM25 search instead of hanging the pipeline.
    """
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    openai_key = await _resolve_provider_key("openai")
    if not openai_key:
        return None
    try:
        from openai import AsyncOpenAI  # type: ignore

        _openai_client = AsyncOpenAI(
            api_key=openai_key,
            base_url="https://api.openai.com/v1",
            max_retries=0,
            timeout=10.0,
        )
        return _openai_client
    except ImportError:
        logger.warning("openai package not installed — OpenAI fallback unavailable")
        return None


class RAGService:
    """Retrieves relevant legal context from the knowledge base."""

    def __init__(self):
        self._pool: asyncpg.Pool | None = None
        # Cache for has_embeddings() — avoids a DB round-trip on every request
        self._embeddings_cache: Optional[bool] = None
        self._embeddings_cache_at: float = 0.0
        self._embeddings_cache_ttl: float = 300.0  # 5 minutes

    # ──────────────────────────────────────────
    # Infrastructure
    # ──────────────────────────────────────────

    async def _get_pool(self) -> asyncpg.Pool:
        """Lazy-init connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(_DB_URL, min_size=2, max_size=10)
        return self._pool

    # ──────────────────────────────────────────
    # Embedding generation
    # ──────────────────────────────────────────

    async def _generate_embedding(self, text: str) -> Optional[list[float]]:
        """
        Generate a single embedding vector for *text*.

        Tries Google text-embedding-004 first (768-dim).
        Falls back to OpenAI text-embedding-3-small (1536-dim).
        Returns None if no provider is available or an error occurs.
        """
        # ── Google (primary) ──────────────────────────────────────────────
        # Provider preference is taken from settings.embedding_provider; key
        # availability is decided inside _configure_genai_async (DB first,
        # legacy env after).
        if settings.embedding_provider == "google":
            if await _configure_genai_async():
                try:
                    import google.generativeai as genai  # type: ignore

                    # embed_content is synchronous — run in executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        lambda: genai.embed_content(
                            model=f"models/{settings.embedding_model}",
                            content=text,
                        ),
                    )
                    return result["embedding"]
                except Exception as exc:
                    logger.warning(f"Google embedding failed: {exc} — trying OpenAI fallback")

        # ── OpenAI (fallback) ─────────────────────────────────────────────
        client = await _get_openai_client_async()
        if client is not None:
            try:
                response = await client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text,
                )
                return response.data[0].embedding
            except Exception as exc:
                logger.warning(f"OpenAI embedding failed: {exc}")

        return None

    # ──────────────────────────────────────────
    # has_embeddings cache
    # ──────────────────────────────────────────

    async def has_embeddings(self) -> bool:
        """
        Returns True if at least one chunk in `document_chunks` has a non-NULL embedding.
        Result is cached for 5 minutes to avoid repeated DB queries.
        """
        now = time.monotonic()
        if (
            self._embeddings_cache is not None
            and now - self._embeddings_cache_at < self._embeddings_cache_ttl
        ):
            return self._embeddings_cache

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            exists: bool = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM document_chunks WHERE embedding IS NOT NULL)"
            )
        self._embeddings_cache = bool(exists)
        self._embeddings_cache_at = now
        return self._embeddings_cache

    # ──────────────────────────────────────────
    # BM25 search
    # ──────────────────────────────────────────

    async def search_bm25(
        self,
        query: str,
        legal_area: str | None = None,
        limit: int = 8,
    ) -> list[dict]:
        """
        BM25 full-text search over document chunks.
        Uses PostgreSQL's built-in ts_rank with Spanish configuration.
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            if legal_area:
                rows = await conn.fetch(
                    """
                    SELECT
                        dc.id, dc.document_id, dc.content, dc.legal_area,
                        dc.article_number, dc.section_path,
                        d.title AS document_title,
                        d.document_number,
                        ts_rank_cd(
                            to_tsvector('spanish', dc.content),
                            plainto_tsquery('spanish', $1)
                        ) AS score
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE dc.legal_area = $2
                      AND to_tsvector('spanish', dc.content) @@ plainto_tsquery('spanish', $1)
                    ORDER BY score DESC
                    LIMIT $3
                    """,
                    query,
                    legal_area,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT
                        dc.id, dc.document_id, dc.content, dc.legal_area,
                        dc.article_number, dc.section_path,
                        d.title AS document_title,
                        d.document_number,
                        ts_rank_cd(
                            to_tsvector('spanish', dc.content),
                            plainto_tsquery('spanish', $1)
                        ) AS score
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE to_tsvector('spanish', dc.content) @@ plainto_tsquery('spanish', $1)
                    ORDER BY score DESC
                    LIMIT $2
                    """,
                    query,
                    limit,
                )

            return [dict(r) for r in rows]

    # ──────────────────────────────────────────
    # Vector search
    # ──────────────────────────────────────────

    async def search_vector(
        self,
        query: str,
        legal_area: str | None = None,
        limit: int = 8,
    ) -> list[dict]:
        """
        Vector similarity search using cosine distance via the HNSW index.

        Embeds *query* at call time then queries `document_chunks` ordered by
        `embedding <=> query_vector` (cosine distance — lower is better).

        Returns an empty list if embedding generation fails.
        """
        embedding = await self._generate_embedding(query)
        if embedding is None:
            logger.warning("search_vector: embedding generation failed — returning empty results")
            return []

        vector_str = "[" + ",".join(map(str, embedding)) + "]"
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            if legal_area:
                rows = await conn.fetch(
                    """
                    SELECT
                        dc.id, dc.content, dc.legal_area, dc.article_number,
                        dc.section_path, d.title AS document_title,
                        d.document_number,
                        (1.0 - (dc.embedding <=> $1::vector))::float AS score
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE dc.legal_area = $2
                      AND dc.embedding IS NOT NULL
                    ORDER BY dc.embedding <=> $1::vector
                    LIMIT $3
                    """,
                    vector_str,
                    legal_area,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT
                        dc.id, dc.content, dc.legal_area, dc.article_number,
                        dc.section_path, d.title AS document_title,
                        d.document_number,
                        (1.0 - (dc.embedding <=> $1::vector))::float AS score
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE dc.embedding IS NOT NULL
                    ORDER BY dc.embedding <=> $1::vector
                    LIMIT $2
                    """,
                    vector_str,
                    limit,
                )

        return [dict(r) for r in rows]

    # ──────────────────────────────────────────
    # Hybrid search
    # ──────────────────────────────────────────

    async def search_hybrid(
        self,
        query: str,
        legal_area: str | None = None,
        limit: int = 8,
        bm25_weight: float = 0.4,
        vec_weight: float = 0.6,
    ) -> list[dict]:
        """
        Hybrid search combining BM25 and vector similarity.

        Calls the `hybrid_search()` PostgreSQL function (defined in init.sql / migration).
        Falls back to BM25 if embedding generation fails.

        Args:
            query:       Natural language query string.
            legal_area:  Optional filter (e.g. "laboral", "constitucional").
            limit:       Maximum number of results to return.
            bm25_weight: Weight for BM25 component (default 0.4).
            vec_weight:  Weight for vector component (default 0.6).

        Returns:
            List of result dicts with keys: id, content, legal_area, article_number,
            section_path, document_title, document_number, bm25_score, vec_score, hybrid_score.
        """
        embedding = await self._generate_embedding(query)
        if embedding is None:
            logger.warning("search_hybrid: embedding unavailable — falling back to BM25")
            return await self.search_bm25(query, legal_area=legal_area, limit=limit)

        vector_str = "[" + ",".join(map(str, embedding)) + "]"
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            try:
                rows = await conn.fetch(
                    "SELECT * FROM hybrid_search($1, $2::vector, $3, $4, $5, $6)",
                    query,
                    vector_str,
                    legal_area,
                    limit,
                    bm25_weight,
                    vec_weight,
                )
                return [dict(r) for r in rows]
            except asyncpg.exceptions.UndefinedFunctionError:
                logger.warning(
                    "hybrid_search() function not found in DB — falling back to BM25. "
                    "Run generate_embeddings.py to create the function."
                )
                return await self.search_bm25(query, legal_area=legal_area, limit=limit)
            except Exception as exc:
                logger.error(f"search_hybrid DB error: {exc} — falling back to BM25")
                return await self.search_bm25(query, legal_area=legal_area, limit=limit)

    # ──────────────────────────────────────────
    # Main retrieval
    # ──────────────────────────────────────────

    async def retrieve(
        self,
        query: str,
        legal_area: str | None = None,
        limit: int = 6,
    ) -> str:
        """
        Main retrieval method — returns a formatted context string
        ready to inject into the LLM prompt.

        Search strategy:
          1. If embeddings exist AND we have an API key → hybrid search
          2. Otherwise → BM25 (safe fallback, always works)

        Reranking (optional, controlled by settings.reranking_enabled):
          - Over-retrieve up to settings.reranking_candidates candidates
          - Rerank using RerankerService (LLM or TF-IDF fallback)
          - Return top `limit` results after reranking
          - If reranking fails for any reason, falls back to original order

        Caching (Redis, TTL = cache_rag_ttl):
          - Cache key includes query[:100], legal_area, and limit to avoid stale results
          - Cache failures are non-critical — app degrades gracefully to a direct DB query
        """
        from app.core.cache import cache
        from app.services.reranker import reranker_service

        # Check cache before hitting the DB + embedding API
        cache_key = cache._make_key("rag", query[:100], legal_area, limit)
        cached = await cache.get(cache_key)
        if cached is not None:
            logger.info("RAG: Cache hit for query='%s'", query[:40])
            return cached

        # Determine how many candidates to fetch.
        # When reranking is enabled we over-retrieve, then rerank down to `limit`.
        fetch_limit = (
            max(settings.reranking_candidates, limit)
            if settings.reranking_enabled
            else limit
        )

        # Decide which search method to use. Hybrid search needs an embedding
        # provider key — try DB-backed platform keys first (operator-managed),
        # fall back to legacy settings (typically empty).
        google_key = await _resolve_provider_key("google")
        openai_key = await _resolve_provider_key("openai")
        use_hybrid = bool(google_key or openai_key) and await self.has_embeddings()

        if use_hybrid:
            results = await self.search_hybrid(query, legal_area=legal_area, limit=fetch_limit)
            method = "hybrid"
        else:
            results = await self.search_bm25(query, legal_area=legal_area, limit=fetch_limit)
            method = "bm25"

        if not results:
            logger.info(
                f"RAG [{method}]: No results for query='{query[:80]}' area={legal_area}"
            )
            return ""

        # Rerank when we have more results than the requested limit
        if settings.reranking_enabled and len(results) > limit:
            try:
                results = await reranker_service.rerank(query, results, top_k=limit)
                method = f"{method}+rerank"
            except Exception as exc:
                logger.warning(
                    f"RAG Reranker: reranking failed, using original order: {exc}"
                )
                results = results[:limit]
        else:
            results = results[:limit]

        logger.info(
            f"RAG [{method}]: Found {len(results)} chunks "
            f"for query='{query[:80]}' area={legal_area}"
        )

        # Format results as context for the LLM
        context_parts = []
        for i, r in enumerate(results, 1):
            source_label = f"{r['document_title']} ({r['document_number']})"
            article_label = f"Art. {r['article_number']}" if r["article_number"] else ""
            section = r["section_path"] or ""

            header = f"[Fuente {i}] {source_label}"
            if article_label:
                header += f" — {article_label}"
            if section:
                header += f" | {section}"

            context_parts.append(f"{header}\n{r['content']}")

        context_result = "\n\n---\n\n".join(context_parts)

        # Store in cache — TTL uses dedicated RAG setting (10 min by default)
        # Legal content changes infrequently, so a longer TTL is safe here
        if context_result:
            await cache.set(cache_key, context_result, ttl_seconds=settings.cache_rag_ttl)

        return context_result

    # ──────────────────────────────────────────
    # Stats
    # ──────────────────────────────────────────

    async def get_stats(self) -> dict:
        """
        Knowledge base statistics — rich breakdown for the /buscar UI and
        operational dashboards.

        Returns counts of:
            - total documents and chunks
            - embedding coverage (chunks with embedding / total)
            - chunks by legal_area, hierarchy, source, document_type
            - distinct sources and document_types (lists for filter UIs)
            - last 5 most recently ingested document titles
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            total_docs = await conn.fetchval("SELECT COUNT(*) FROM documents")
            total_chunks = await conn.fetchval("SELECT COUNT(*) FROM document_chunks")
            embedded_chunks = await conn.fetchval(
                "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL"
            )

            areas = await conn.fetch(
                "SELECT legal_area, COUNT(*) as c FROM document_chunks "
                "GROUP BY legal_area ORDER BY c DESC"
            )
            docs_by_hierarchy = await conn.fetch(
                "SELECT COALESCE(hierarchy, 'sin_clasificar') AS hierarchy, COUNT(*) AS c "
                "FROM documents GROUP BY 1 ORDER BY c DESC"
            )
            docs_by_source = await conn.fetch(
                "SELECT source, COUNT(*) AS c FROM documents "
                "GROUP BY source ORDER BY c DESC"
            )
            docs_by_type = await conn.fetch(
                "SELECT document_type, COUNT(*) AS c FROM documents "
                "GROUP BY document_type ORDER BY c DESC"
            )
            recent = await conn.fetch(
                "SELECT title, document_number, legal_area, source, created_at "
                "FROM documents ORDER BY created_at DESC NULLS LAST LIMIT 5"
            )

            return {
                "total_documents": total_docs or 0,
                "total_chunks": total_chunks or 0,
                "embedded_chunks": embedded_chunks or 0,
                "embedding_coverage": (
                    round((embedded_chunks or 0) / total_chunks * 100, 1)
                    if total_chunks
                    else 0
                ),
                "areas_count": len(areas),
                "chunks_by_area": {r["legal_area"]: r["c"] for r in areas},
                "docs_by_hierarchy": {r["hierarchy"]: r["c"] for r in docs_by_hierarchy},
                "docs_by_source": {r["source"]: r["c"] for r in docs_by_source},
                "docs_by_type": {r["document_type"]: r["c"] for r in docs_by_type},
                "sources": [r["source"] for r in docs_by_source],
                "document_types": [r["document_type"] for r in docs_by_type],
                "recent_documents": [
                    {
                        "title": r["title"],
                        "document_number": r["document_number"],
                        "legal_area": r["legal_area"],
                        "source": r["source"],
                        "created_at": (
                            r["created_at"].isoformat() if r["created_at"] else None
                        ),
                    }
                    for r in recent
                ],
            }


# Singleton
rag_service = RAGService()
