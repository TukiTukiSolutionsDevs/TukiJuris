"""
Document Ingestion Pipeline — loads legal documents into PostgreSQL + pgvector.

Usage (from project root):
    docker exec agente-derecho-api-1 python -m services.ingestion.ingest

Or locally:
    python -m services.ingestion.ingest
    python -m services.ingestion.ingest --db-url postgresql://user:pass@host:5432/db
"""

import argparse
import asyncio
import logging
import os
import sys
import uuid
from collections import defaultdict
from pathlib import Path

import asyncpg

# Add project root to path so we can import seeders
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# --- Original seeders ---
from services.ingestion.seeders.constitucion import CONSTITUCION_ARTICLES
from services.ingestion.seeders.codigo_laboral import LABORAL_ARTICLES
from services.ingestion.seeders.codigo_civil import CIVIL_ARTICLES
from services.ingestion.seeders.codigo_civil_ext import CIVIL_EXT_ARTICLES
from services.ingestion.seeders.codigo_penal import PENAL_ARTICLES
from services.ingestion.seeders.codigo_penal_ext import PENAL_EXT_ARTICLES
from services.ingestion.seeders.codigo_tributario import TRIBUTARIO_ARTICLES
from services.ingestion.seeders.derecho_procesal import (
    PROCESAL_CIVIL_ARTICLES,
    PROCESAL_PENAL_ARTICLES,
)
from services.ingestion.seeders.derecho_admin_corp import (
    ADMINISTRATIVO_ARTICLES,
    CORPORATIVO_ARTICLES,
)
from services.ingestion.seeders.derecho_registral_competencia_compliance import (
    REGISTRAL_ARTICLES,
    COMPETENCIA_ARTICLES,
    COMPLIANCE_ARTICLES,
)
from services.ingestion.seeders.comercio_exterior import (
    COMERCIO_EXT_ARTICLES as COMERCIO_EXTERIOR_ARTICLES,
)

# --- Sprint 12: Extended seeders ---
from services.ingestion.seeders.derecho_registral_ext import REGISTRAL_EXT_ARTICLES
from services.ingestion.seeders.comercio_exterior_ext import (
    COMERCIO_EXT_ARTICLES as COMERCIO_EXT_ARTICLES_SPRINT12,
)
from services.ingestion.seeders.derecho_administrativo_ext import ADMINISTRATIVO_EXT_ARTICLES
from services.ingestion.seeders.derecho_corporativo_ext import CORPORATIVO_EXT_ARTICLES
from services.ingestion.seeders.derecho_tributario_ext import TRIBUTARIO_EXT_ARTICLES
from services.ingestion.seeders.derecho_laboral_ext import LABORAL_EXT_ARTICLES

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_DB_URL = os.environ.get(
    "DATABASE_URL_SYNC",
    "postgresql://postgres:postgres@localhost:5432/agente_derecho",
)


DOCUMENT_DEFINITIONS = [
    # =========================================================================
    # CONSTITUCIONAL
    # =========================================================================
    {
        "title": "Constitucion Politica del Peru de 1993",
        "document_type": "constitucion",
        "document_number": "Constitucion 1993",
        "legal_area": "constitucional",
        "hierarchy": "constitucional",
        "source": "tc.gob.pe",
        "source_url": "https://www.tc.gob.pe/wp-content/uploads/2018/10/Compendio_Normativo.pdf",
        "articles": CONSTITUCION_ARTICLES,
    },

    # =========================================================================
    # LABORAL — original
    # =========================================================================
    {
        "title": "TUO del DL 728 - Ley de Productividad y Competitividad Laboral (DS 003-97-TR)",
        "document_type": "decreto_supremo",
        "document_number": "DS 003-97-TR",
        "legal_area": "laboral",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": [a for a in LABORAL_ARTICLES if a["article"].startswith(("1", "2", "3"))],
    },
    {
        "title": "TUO del DL 650 - Ley de Compensacion por Tiempo de Servicios (DS 001-97-TR)",
        "document_type": "decreto_supremo",
        "document_number": "DS 001-97-TR",
        "legal_area": "laboral",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": [a for a in LABORAL_ARTICLES if a["article"].startswith("CTS")],
    },
    {
        "title": "Ley 27735 - Ley que regula el otorgamiento de Gratificaciones",
        "document_type": "ley",
        "document_number": "Ley 27735",
        "legal_area": "laboral",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": [a for a in LABORAL_ARTICLES if a["article"].startswith("GRAT")],
    },
    {
        "title": "DL 713 - Descansos Remunerados (Vacaciones)",
        "document_type": "decreto_legislativo",
        "document_number": "DL 713",
        "legal_area": "laboral",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": [a for a in LABORAL_ARTICLES if a["article"].startswith("VAC")],
    },

    # =========================================================================
    # LABORAL — Sprint 12 extension
    # =========================================================================
    {
        "title": "Derecho Laboral — Extension: SST, Colectivo, Teletrabajo, Tercerizacion",
        "document_type": "compilacion",
        "document_number": "LABORAL-EXT-2024",
        "legal_area": "laboral",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": LABORAL_EXT_ARTICLES,
    },

    # =========================================================================
    # CIVIL — original
    # =========================================================================
    {
        "title": "Codigo Civil Peruano (DL 295, 1984) — Articulos principales",
        "document_type": "codigo",
        "document_number": "DL 295 - Codigo Civil",
        "legal_area": "civil",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": CIVIL_ARTICLES,
    },
    {
        "title": "Codigo Civil — Extension: Familia, Sucesiones, Arrendamiento, Garantias",
        "document_type": "codigo",
        "document_number": "DL 295 - Codigo Civil EXT",
        "legal_area": "civil",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": CIVIL_EXT_ARTICLES,
    },

    # =========================================================================
    # PENAL — original
    # =========================================================================
    {
        "title": "Codigo Penal Peruano (DL 635) — Articulos principales",
        "document_type": "codigo",
        "document_number": "DL 635 - Codigo Penal",
        "legal_area": "penal",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": PENAL_ARTICLES,
    },
    {
        "title": "Codigo Penal — Extension: Delitos frecuentes y fe publica",
        "document_type": "codigo",
        "document_number": "DL 635 - Codigo Penal EXT",
        "legal_area": "penal",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": PENAL_EXT_ARTICLES,
    },

    # =========================================================================
    # TRIBUTARIO — original
    # =========================================================================
    {
        "title": "Codigo Tributario y normas SUNAT/IR/IGV",
        "document_type": "codigo",
        "document_number": "DS 133-2013-EF - Codigo Tributario",
        "legal_area": "tributario",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": TRIBUTARIO_ARTICLES,
    },

    # =========================================================================
    # TRIBUTARIO — Sprint 12 extension
    # =========================================================================
    {
        "title": "Derecho Tributario — Extension: Codigo, IR, IGV, procedimientos SUNAT",
        "document_type": "compilacion",
        "document_number": "TRIBUTARIO-EXT-2024",
        "legal_area": "tributario",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": TRIBUTARIO_EXT_ARTICLES,
    },

    # =========================================================================
    # PROCESAL
    # =========================================================================
    {
        "title": "Codigo Procesal Civil — Vias procedimentales principales",
        "document_type": "codigo",
        "document_number": "DL 768 - CPC",
        "legal_area": "procesal",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": PROCESAL_CIVIL_ARTICLES,
    },
    {
        "title": "Nuevo Codigo Procesal Penal — Proceso comun y principios",
        "document_type": "codigo",
        "document_number": "DL 957 - NCPP",
        "legal_area": "procesal",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": PROCESAL_PENAL_ARTICLES,
    },

    # =========================================================================
    # ADMINISTRATIVO — original
    # =========================================================================
    {
        "title": "TUO LPAG (DS 004-2019-JUS) — Ley del Procedimiento Administrativo General",
        "document_type": "ley",
        "document_number": "Ley 27444 TUO - LPAG",
        "legal_area": "administrativo",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": ADMINISTRATIVO_ARTICLES,
    },

    # =========================================================================
    # ADMINISTRATIVO — Sprint 12 extension
    # =========================================================================
    {
        "title": "Derecho Administrativo — Extension: principios, acto, silencio, sancionador",
        "document_type": "compilacion",
        "document_number": "ADMINISTRATIVO-EXT-2024",
        "legal_area": "administrativo",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": ADMINISTRATIVO_EXT_ARTICLES,
    },

    # =========================================================================
    # CORPORATIVO — original
    # =========================================================================
    {
        "title": "LGS (Ley 26887) — Ley General de Sociedades",
        "document_type": "ley",
        "document_number": "Ley 26887 - LGS",
        "legal_area": "corporativo",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": CORPORATIVO_ARTICLES,
    },

    # =========================================================================
    # CORPORATIVO — Sprint 12 extension
    # =========================================================================
    {
        "title": "Derecho Corporativo — Extension: tipos sociales, organos, M&A, MYPES",
        "document_type": "compilacion",
        "document_number": "CORPORATIVO-EXT-2024",
        "legal_area": "corporativo",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": CORPORATIVO_EXT_ARTICLES,
    },

    # =========================================================================
    # REGISTRAL — original
    # =========================================================================
    {
        "title": "Registral — SUNARP, inscripciones, procedimiento registral",
        "document_type": "compilacion",
        "document_number": "SUNARP - Registral Base",
        "legal_area": "registral",
        "hierarchy": "legal",
        "source": "sunarp.gob.pe",
        "source_url": "https://www.sunarp.gob.pe",
        "articles": REGISTRAL_ARTICLES,
    },

    # =========================================================================
    # REGISTRAL — Sprint 12 extension
    # =========================================================================
    {
        "title": "Derecho Registral — Extension: RGRP, predios, sociedades, vehiculos",
        "document_type": "compilacion",
        "document_number": "REGISTRAL-EXT-2024",
        "legal_area": "registral",
        "hierarchy": "legal",
        "source": "sunarp.gob.pe",
        "source_url": "https://www.sunarp.gob.pe",
        "articles": REGISTRAL_EXT_ARTICLES,
    },

    # =========================================================================
    # COMPETENCIA / INDECOPI
    # =========================================================================
    {
        "title": "Competencia e INDECOPI — PI, publicidad, proteccion al consumidor",
        "document_type": "compilacion",
        "document_number": "INDECOPI - Competencia Base",
        "legal_area": "competencia",
        "hierarchy": "legal",
        "source": "indecopi.gob.pe",
        "source_url": "https://www.indecopi.gob.pe",
        "articles": COMPETENCIA_ARTICLES,
    },

    # =========================================================================
    # COMPLIANCE
    # =========================================================================
    {
        "title": "Compliance — PLAFT, FCPA, ISO 37001, gobierno corporativo",
        "document_type": "compilacion",
        "document_number": "COMPLIANCE-BASE",
        "legal_area": "compliance",
        "hierarchy": "legal",
        "source": "spij",
        "source_url": "https://spijweb.minjus.gob.pe",
        "articles": COMPLIANCE_ARTICLES,
    },

    # =========================================================================
    # COMERCIO EXTERIOR — original
    # =========================================================================
    {
        "title": "Comercio Exterior — Aduanas, TLC, MINCETUR",
        "document_type": "compilacion",
        "document_number": "DL 1053 - LGA Base",
        "legal_area": "comercio_exterior",
        "hierarchy": "legal",
        "source": "sunat.gob.pe",
        "source_url": "https://www.sunat.gob.pe",
        "articles": COMERCIO_EXTERIOR_ARTICLES,
    },

    # =========================================================================
    # COMERCIO EXTERIOR — Sprint 12 extension
    # =========================================================================
    {
        "title": "Comercio Exterior — Extension: regimenes, TLCs, INTA, infracciones",
        "document_type": "compilacion",
        "document_number": "COMERCIO-EXT-2024",
        "legal_area": "comercio_exterior",
        "hierarchy": "legal",
        "source": "sunat.gob.pe",
        "source_url": "https://www.sunat.gob.pe",
        "articles": COMERCIO_EXT_ARTICLES_SPRINT12,
    },
]


async def ingest_all(db_url: str) -> None:
    """Main ingestion pipeline."""
    logger.info("Connecting to database...")
    conn = await asyncpg.connect(db_url)

    try:
        total_docs = 0
        total_chunks = 0
        chunks_by_area: dict[str, int] = defaultdict(int)

        for doc_def in DOCUMENT_DEFINITIONS:
            articles = doc_def.pop("articles")
            if not articles:
                logger.warning(f"  No articles for: {doc_def['document_number']} — skipping")
                continue

            # Idempotent: skip if document already ingested
            existing = await conn.fetchval(
                "SELECT id FROM documents WHERE document_number = $1",
                doc_def["document_number"],
            )
            if existing:
                logger.info(f"  Skip (exists): {doc_def['document_number']}")
                # Still count existing chunks for the summary
                area_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM document_chunks WHERE document_id = $1",
                    existing,
                )
                chunks_by_area[doc_def["legal_area"]] += area_count or 0
                continue

            # Insert document record
            doc_id = uuid.uuid4()
            await conn.execute(
                """
                INSERT INTO documents (id, title, document_type, document_number, legal_area,
                                       hierarchy, source, source_url, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, true)
                """,
                doc_id,
                doc_def["title"],
                doc_def["document_type"],
                doc_def["document_number"],
                doc_def["legal_area"],
                doc_def["hierarchy"],
                doc_def["source"],
                doc_def.get("source_url"),
            )
            total_docs += 1
            logger.info(f"  Inserted document: {doc_def['title']}")

            # Insert chunks (articles)
            chunk_count = 0
            for idx, article in enumerate(articles):
                chunk_id = uuid.uuid4()
                content = article["content"]
                token_count = int(len(content.split()) * 1.3)  # rough token estimate

                await conn.execute(
                    """
                    INSERT INTO document_chunks
                        (id, document_id, chunk_index, content, legal_area,
                         article_number, section_path, token_count)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    chunk_id,
                    doc_id,
                    idx,
                    content,
                    doc_def["legal_area"],
                    article["article"],
                    article["section_path"],
                    token_count,
                )
                chunk_count += 1
                total_chunks += 1

            chunks_by_area[doc_def["legal_area"]] += chunk_count
            logger.info(f"    -> {chunk_count} chunks inserted for area '{doc_def['legal_area']}'")

        # Summary
        total_in_db = await conn.fetchval("SELECT COUNT(*) FROM document_chunks")
        docs_in_db = await conn.fetchval("SELECT COUNT(*) FROM documents")

        logger.info("")
        logger.info("=" * 60)
        logger.info(f"Ingestion complete — {total_docs} documents, {total_chunks} new chunks")
        logger.info(f"Database totals  — {docs_in_db} documents, {total_in_db} chunks")
        logger.info("")
        logger.info("Chunks by area (this run):")
        for area, count in sorted(chunks_by_area.items()):
            logger.info(f"  {area:<30} {count:>5} chunks")
        logger.info("=" * 60)

    finally:
        await conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest legal documents into PostgreSQL + pgvector"
    )
    parser.add_argument(
        "--db-url",
        default=DEFAULT_DB_URL,
        help=f"PostgreSQL connection URL (default: {DEFAULT_DB_URL})",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(ingest_all(args.db_url))
