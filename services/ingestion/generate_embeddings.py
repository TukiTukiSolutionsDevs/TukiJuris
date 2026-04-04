"""
Embedding Generation Script — populates the `embedding` column in `document_chunks`.

Reads all chunks with `embedding IS NULL` and generates embeddings using:
  - Primary:  Google text-embedding-004  (768-dim) via google.generativeai
  - Fallback: OpenAI text-embedding-3-small (1536-dim)

Before generating embeddings, migrates the DB column to the correct dimensions.

Usage (from project root):
    docker exec agente-derecho-api-1 python -m services.ingestion.generate_embeddings

Or locally (needs DB accessible at localhost:5432):
    python -m services.ingestion.generate_embeddings
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

import asyncpg

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/agente_derecho",
).replace("postgresql+asyncpg://", "postgresql://")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

GOOGLE_MODEL = "models/text-embedding-004"
GOOGLE_DIM = 768

OPENAI_MODEL = "text-embedding-3-small"
OPENAI_DIM = 1536

BATCH_SIZE = 20        # chunks per batch (respect rate limits)
SLEEP_BETWEEN_BATCHES = 1.0  # seconds


# ──────────────────────────────────────────────
# Migration SQL
# ──────────────────────────────────────────────
MIGRATION_GOOGLE = """
ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(768)
    USING embedding::text::vector(768);
DROP INDEX IF EXISTS idx_chunks_embedding;
CREATE INDEX idx_chunks_embedding
    ON document_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);
"""

MIGRATION_OPENAI = """
-- column stays vector(1536) — no migration needed for OpenAI
"""

HYBRID_SEARCH_PATCH_768 = """
CREATE OR REPLACE FUNCTION hybrid_search(
    query_text   TEXT,
    query_emb    vector(768),
    area_filter  TEXT    DEFAULT NULL,
    result_limit INT     DEFAULT 8,
    bm25_weight  FLOAT   DEFAULT 0.4,
    vec_weight   FLOAT   DEFAULT 0.6
)
RETURNS TABLE (
    id              UUID,
    content         TEXT,
    legal_area      TEXT,
    article_number  TEXT,
    section_path    TEXT,
    document_title  TEXT,
    document_number TEXT,
    bm25_score      FLOAT,
    vec_score       FLOAT,
    hybrid_score    FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH bm25 AS (
        SELECT
            dc.id,
            ts_rank_cd(
                to_tsvector('spanish', dc.content),
                plainto_tsquery('spanish', query_text)
            )::FLOAT AS score
        FROM document_chunks dc
        WHERE
            (area_filter IS NULL OR dc.legal_area = area_filter)
            AND to_tsvector('spanish', dc.content) @@ plainto_tsquery('spanish', query_text)
    ),
    vec AS (
        SELECT
            dc.id,
            (1.0 - (dc.embedding <=> query_emb))::FLOAT AS score
        FROM document_chunks dc
        WHERE
            (area_filter IS NULL OR dc.legal_area = area_filter)
            AND dc.embedding IS NOT NULL
        ORDER BY dc.embedding <=> query_emb
        LIMIT result_limit * 3
    ),
    combined AS (
        SELECT
            dc.id,
            dc.content,
            dc.legal_area,
            dc.article_number,
            dc.section_path,
            d.title  AS document_title,
            d.document_number,
            COALESCE(b.score, 0.0) AS bm25_score,
            COALESCE(v.score, 0.0) AS vec_score,
            (COALESCE(b.score, 0.0) * bm25_weight
             + COALESCE(v.score, 0.0) * vec_weight) AS hybrid_score
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        LEFT JOIN bm25 b ON b.id = dc.id
        LEFT JOIN vec  v ON v.id = dc.id
        WHERE b.id IS NOT NULL OR v.id IS NOT NULL
    )
    SELECT *
    FROM combined
    ORDER BY hybrid_score DESC
    LIMIT result_limit;
END;
$$;
"""


# ──────────────────────────────────────────────
# Embedding providers
# ──────────────────────────────────────────────

def _embed_google(texts: list[str]) -> list[list[float]]:
    """Generate embeddings using Google text-embedding-004 (768-dim)."""
    import google.generativeai as genai  # type: ignore

    genai.configure(api_key=GOOGLE_API_KEY)
    embeddings: list[list[float]] = []
    for text in texts:
        result = genai.embed_content(
            model=GOOGLE_MODEL,
            content=text,
        )
        embeddings.append(result["embedding"])
    return embeddings


def _embed_openai(texts: list[str]) -> list[list[float]]:
    """Generate embeddings using OpenAI text-embedding-3-small (1536-dim)."""
    from openai import OpenAI  # type: ignore

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(
        model=OPENAI_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


def detect_provider() -> tuple[str, int]:
    """
    Returns (provider_name, embedding_dim) based on available API keys.
    Preference: Google → OpenAI → raise.
    """
    if GOOGLE_API_KEY:
        logger.info("Using Google text-embedding-004 (768-dim)")
        return "google", GOOGLE_DIM
    if OPENAI_API_KEY:
        logger.info("Using OpenAI text-embedding-3-small (1536-dim)")
        return "openai", OPENAI_DIM
    raise EnvironmentError(
        "No embedding API key found. "
        "Set GOOGLE_API_KEY or OPENAI_API_KEY environment variables."
    )


def embed_batch(provider: str, texts: list[str]) -> list[list[float]]:
    """Dispatch to the correct embedding provider."""
    if provider == "google":
        return _embed_google(texts)
    if provider == "openai":
        return _embed_openai(texts)
    raise ValueError(f"Unknown provider: {provider}")


# ──────────────────────────────────────────────
# Migration helpers
# ──────────────────────────────────────────────

async def _get_current_embedding_dim(conn: asyncpg.Connection) -> Optional[int]:
    """
    Returns the current dimension of the embedding column,
    or None if the column doesn't exist / has no type info.
    """
    row = await conn.fetchrow(
        """
        SELECT atttypmod
        FROM pg_attribute
        WHERE attrelid = 'document_chunks'::regclass
          AND attname = 'embedding'
          AND attnum > 0
          AND NOT attisdropped
        """
    )
    if row is None:
        return None
    # atttypmod for vector type encodes dimension as (dim + 1) * 8? No — pgvector
    # stores it differently. Instead just check with a simpler approach:
    # atttypmod == -1 means no modifier (unconstrained); otherwise it's dim+1 * 4
    # Actually for pgvector, atttypmod = dim directly when set. Let's query typmod.
    typmod = row["atttypmod"]
    if typmod == -1:
        return None
    return typmod  # pgvector stores dim directly in atttypmod


async def run_migration(conn: asyncpg.Connection, provider: str, target_dim: int) -> None:
    """
    Alters embedding column to the target dimension if needed,
    re-creates the HNSW index, and patches the hybrid_search function.
    """
    current_dim = await _get_current_embedding_dim(conn)
    logger.info(f"Current embedding column dim: {current_dim}, target: {target_dim}")

    if current_dim != target_dim:
        logger.info(f"Migrating embedding column from dim={current_dim} to dim={target_dim}...")
        # Drop nullify all existing (incompatible) embeddings before ALTER TYPE
        await conn.execute("UPDATE document_chunks SET embedding = NULL")
        await conn.execute(f"""
            ALTER TABLE document_chunks
                ALTER COLUMN embedding TYPE vector({target_dim})
                USING NULL::vector({target_dim})
        """)
        logger.info(f"Column altered to vector({target_dim})")

        # Drop and recreate HNSW index
        await conn.execute("DROP INDEX IF EXISTS idx_chunks_embedding")
        await conn.execute(f"""
            CREATE INDEX idx_chunks_embedding
                ON document_chunks
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 200)
        """)
        logger.info("HNSW index recreated")
    else:
        logger.info("Column dimension already correct — skipping ALTER TABLE")

    # Always patch hybrid_search to match current dimension
    if target_dim == GOOGLE_DIM:
        await conn.execute(HYBRID_SEARCH_PATCH_768)
        logger.info("hybrid_search() function updated for 768-dim vectors")
    else:
        logger.info("Using OpenAI dim (1536) — hybrid_search function not patched")


# ──────────────────────────────────────────────
# Main pipeline
# ──────────────────────────────────────────────

async def generate_embeddings() -> None:
    """Main pipeline: connects, migrates schema, batches, embeds, updates."""
    provider, dim = detect_provider()

    logger.info(f"Connecting to DB: {DB_URL.split('@')[-1]}")  # hide credentials
    conn = await asyncpg.connect(DB_URL)

    try:
        # ── Schema migration ────────────────────────────────────────────────
        await run_migration(conn, provider, dim)

        # ── Count pending chunks ────────────────────────────────────────────
        total_pending: int = await conn.fetchval(
            "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NULL"
        )
        if total_pending == 0:
            logger.info("✅ All chunks already have embeddings. Nothing to do.")
            return

        total_all: int = await conn.fetchval("SELECT COUNT(*) FROM document_chunks")
        logger.info(f"Chunks to embed: {total_pending} / {total_all}")

        # ── Batch processing ────────────────────────────────────────────────
        processed = 0
        start_time = time.time()

        while True:
            # Fetch next batch
            rows = await conn.fetch(
                """
                SELECT id, content
                FROM document_chunks
                WHERE embedding IS NULL
                ORDER BY id
                LIMIT $1
                """,
                BATCH_SIZE,
            )
            if not rows:
                break

            ids = [r["id"] for r in rows]
            texts = [r["content"] for r in rows]

            # Generate embeddings
            try:
                vectors = embed_batch(provider, texts)
            except Exception as exc:
                logger.error(f"Embedding API error: {exc}")
                logger.error("Aborting — check API key and rate limits.")
                raise

            # Persist to DB inside a transaction
            async with conn.transaction():
                for chunk_id, vector in zip(ids, vectors):
                    vector_str = "[" + ",".join(map(str, vector)) + "]"
                    await conn.execute(
                        "UPDATE document_chunks SET embedding = $1 WHERE id = $2",
                        vector_str,
                        chunk_id,
                    )

            processed += len(rows)
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            remaining = total_pending - processed
            eta_sec = remaining / rate if rate > 0 else 0

            logger.info(
                f"  Progress: {processed}/{total_pending} chunks "
                f"({processed / total_pending * 100:.1f}%) "
                f"| {rate:.1f} chunks/s "
                f"| ETA: {eta_sec:.0f}s"
            )

            # Respect rate limits
            if remaining > 0:
                time.sleep(SLEEP_BETWEEN_BATCHES)

        elapsed_total = time.time() - start_time
        logger.info(f"\n{'='*55}")
        logger.info(f"✅ Done! {processed} embeddings generated in {elapsed_total:.1f}s")
        logger.info(f"   Provider : {provider}")
        logger.info(f"   Model    : {GOOGLE_MODEL if provider == 'google' else OPENAI_MODEL}")
        logger.info(f"   Dim      : {dim}")
        logger.info(f"{'='*55}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(generate_embeddings())
