"""
Local Embedding Generation — multilingual-e5-large (1024-dim).

Genera embeddings localmente con sentence-transformers, sin depender de
proveedores externos (Google/OpenAI/Groq).

Modelo:    intfloat/multilingual-e5-large
Dim:       1024  — coincide con la columna `embedding vector(1024)`
Idiomas:   100+ (incluye español rioplatense/peruano)
Licencia:  MIT (compatible con SaaS comercial)

Convención del modelo e5 (importante para retrieval correcto):
    - Pasajes  → prefijar con  "passage: "
    - Queries  → prefijar con  "query: "
La inserción aquí trata cada chunk como pasaje. El servicio RAG en runtime
debe agregar el prefijo "query: " al embebido de la consulta.

Uso (desde la raíz del proyecto, con la BD accesible localmente):
    python -m services.ingestion.generate_embeddings_local

Dentro del container:
    docker exec tukijuris-api-1 python -m services.ingestion.generate_embeddings_local
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ───────── Configuration ─────────
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/agente_derecho",
).replace("postgresql+asyncpg://", "postgresql://")

MODEL_NAME = os.getenv("LOCAL_EMBEDDING_MODEL", "intfloat/multilingual-e5-large")
TARGET_DIM = 1024
BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "32"))
DEVICE = os.getenv("EMBED_DEVICE", "")  # "", "cpu", "cuda", "mps"

PASSAGE_PREFIX = "passage: "


# ───────── Schema migration ─────────
HYBRID_SEARCH_PATCH_1024 = """
CREATE OR REPLACE FUNCTION hybrid_search(
    query_text   TEXT,
    query_emb    vector(1024),
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


async def _ensure_column_and_index(conn: asyncpg.Connection) -> None:
    """Make sure embedding column is vector(1024) and HNSW index exists."""
    typmod = await conn.fetchval(
        """
        SELECT atttypmod
        FROM pg_attribute
        WHERE attrelid = 'document_chunks'::regclass
          AND attname = 'embedding'
          AND NOT attisdropped
        """
    )
    if typmod and typmod != TARGET_DIM:
        logger.info(f"Migrating embedding column from dim={typmod} to dim={TARGET_DIM}")
        await conn.execute("UPDATE document_chunks SET embedding = NULL")
        await conn.execute(
            f"ALTER TABLE document_chunks "
            f"ALTER COLUMN embedding TYPE vector({TARGET_DIM}) "
            f"USING NULL::vector({TARGET_DIM})"
        )
        await conn.execute("DROP INDEX IF EXISTS idx_chunks_embedding")
    else:
        logger.info(f"Embedding column already at dim={TARGET_DIM}")


async def _ensure_hnsw_index(conn: asyncpg.Connection) -> None:
    exists = await conn.fetchval(
        "SELECT 1 FROM pg_indexes WHERE indexname = 'idx_chunks_embedding'"
    )
    if exists:
        logger.info("HNSW index already exists")
        return
    logger.info("Creating HNSW index (may take a few minutes on large corpora)...")
    await conn.execute(
        "CREATE INDEX idx_chunks_embedding ON document_chunks "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 200)"
    )
    logger.info("HNSW index created")


# ───────── Model loader ─────────
# Soporta dos backends:
#   - fastembed (ONNX, ~50 MB instal, sin torch) — preferido por velocidad de install
#   - sentence-transformers (torch, ~2 GB instal, soporta GPU/MPS) — fallback
# Auto-detect: usa fastembed si está disponible, si no cae a sentence-transformers.
_model_cache: dict[str, object] = {}
_backend: str = ""


def _detect_backend() -> str:
    global _backend
    if _backend:
        return _backend
    try:
        import fastembed  # type: ignore  # noqa: F401
        _backend = "fastembed"
    except ImportError:
        try:
            import sentence_transformers  # type: ignore  # noqa: F401
            _backend = "sentence_transformers"
        except ImportError as e:
            raise EnvironmentError(
                "Ningún backend de embeddings está instalado. "
                "Instala uno de: `pip install fastembed` (recomendado) o "
                "`pip install sentence-transformers` (pesado, pero soporta MPS/GPU)."
            ) from e
    return _backend


def _get_model():
    if "m" in _model_cache:
        return _model_cache["m"]
    backend = _detect_backend()
    logger.info(f"Backend de embeddings: {backend}")

    if backend == "fastembed":
        from fastembed import TextEmbedding  # type: ignore

        logger.info(f"Cargando modelo {MODEL_NAME} (ONNX/fastembed)...")
        model = TextEmbedding(model_name=MODEL_NAME, cache_dir="/root/.cache/huggingface")
        _model_cache["m"] = model
        logger.info("Modelo fastembed listo")
        return model

    # sentence_transformers fallback
    from sentence_transformers import SentenceTransformer  # type: ignore

    kwargs = {}
    if DEVICE:
        kwargs["device"] = DEVICE
    logger.info(f"Cargando modelo {MODEL_NAME} (sentence-transformers, device={DEVICE or 'auto'})...")
    model = SentenceTransformer(MODEL_NAME, **kwargs)
    _model_cache["m"] = model
    logger.info(f"Modelo cargado — dim={model.get_sentence_embedding_dimension()}")
    return model


def _embed_batch(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    backend = _detect_backend()
    prefixed = [PASSAGE_PREFIX + (t or "") for t in texts]

    if backend == "fastembed":
        # fastembed.embed() devuelve un generador de np.ndarray (ya normalizadas).
        vecs = list(model.embed(prefixed))  # type: ignore[attr-defined]
        return [v.tolist() for v in vecs]

    # sentence-transformers
    vecs = model.encode(  # type: ignore[union-attr]
        prefixed,
        batch_size=BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return [v.tolist() for v in vecs]


# ───────── Main pipeline ─────────

async def generate_embeddings() -> None:
    logger.info(f"Connecting to DB: {DB_URL.split('@')[-1]}")
    conn = await asyncpg.connect(DB_URL)

    try:
        await _ensure_column_and_index(conn)

        total_pending = await conn.fetchval(
            "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NULL"
        )
        total_all = await conn.fetchval("SELECT COUNT(*) FROM document_chunks")
        logger.info(f"Chunks to embed: {total_pending} / {total_all}")

        if total_pending == 0:
            logger.info("Nothing to embed.")
            await _ensure_hnsw_index(conn)
            await conn.execute(HYBRID_SEARCH_PATCH_1024)
            logger.info("hybrid_search() function patched for vector(1024)")
            return

        processed = 0
        start = time.time()

        while True:
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
            vectors = _embed_batch(texts)

            async with conn.transaction():
                for cid, vec in zip(ids, vectors):
                    vec_str = "[" + ",".join(f"{v:.6f}" for v in vec) + "]"
                    await conn.execute(
                        "UPDATE document_chunks SET embedding = $1 WHERE id = $2",
                        vec_str,
                        cid,
                    )

            processed += len(rows)
            elapsed = time.time() - start
            rate = processed / max(elapsed, 1e-6)
            remaining = total_pending - processed
            eta_sec = remaining / max(rate, 1e-6)
            logger.info(
                f"Progress {processed}/{total_pending} "
                f"({processed * 100.0 / total_pending:.1f}%) | "
                f"{rate:.1f} ch/s | ETA {eta_sec:.0f}s"
            )

        # Post-fill housekeeping
        await _ensure_hnsw_index(conn)
        await conn.execute(HYBRID_SEARCH_PATCH_1024)
        logger.info("hybrid_search() function patched for vector(1024)")

        total_time = time.time() - start
        logger.info("=" * 55)
        logger.info(f"Done — {processed} embeddings in {total_time:.1f}s")
        logger.info(f"Model : {MODEL_NAME}  Dim: {TARGET_DIM}")
        logger.info("=" * 55)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(generate_embeddings())
