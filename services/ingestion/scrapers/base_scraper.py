"""
Base scraper with common functionality for legal document scraping.

All scrapers inherit from BaseScraper and implement the scrape() method.
The ingest() and run() methods are shared across all scrapers.
"""

import abc
import asyncio
import logging
import uuid
from datetime import datetime, UTC

import asyncpg
import httpx


class BaseScraper(abc.ABC):
    """Abstract base class for all legal document scrapers."""

    def __init__(self, db_url: str, name: str):
        self.db_url = db_url
        self.name = name
        self.logger = logging.getLogger(f"scraper.{name}")
        self.client = httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": "AgenteDerecho/1.0 (Legal Research Bot; contact@agentederecho.pe)"
            },
        )

    @abc.abstractmethod
    async def scrape(self) -> list[dict]:
        """
        Scrape and return a list of document dicts.

        Each dict must contain:
            - title (str): Full document title
            - type (str): Document type (ley, decreto_supremo, sentencia, resolucion)
            - number (str): Unique document identifier (used as document_number in DB)
            - area (str): Legal area (laboral, penal, civil, tributario, etc.)
            - hierarchy (str): Normative hierarchy level (constitucional, legal, reglamentario)
            - source (str): Source name (e.g. "elperuano.pe", "tc.gob.pe")
            - source_url (str): URL where the document was found or originated
            - chunks (list[dict]): List of content chunks, each with:
                - content (str): Chunk text
                - article_number (str, optional): Article reference
                - section_path (str, optional): Section path for navigation
        """
        ...

    async def ingest(self, docs: list[dict]) -> dict:
        """
        Ingest scraped documents into the database.

        Idempotent: checks document_number before inserting.
        Returns counts of inserted docs, chunks, and skipped docs.
        """
        conn = await asyncpg.connect(self.db_url)
        inserted_docs = 0
        inserted_chunks = 0
        skipped = 0

        try:
            for doc in docs:
                # Idempotency check — skip if document_number already exists
                existing = await conn.fetchval(
                    "SELECT id FROM documents WHERE document_number = $1",
                    doc["number"],
                )
                if existing:
                    self.logger.debug(f"Skipping existing document: {doc['number']}")
                    skipped += 1
                    continue

                doc_id = uuid.uuid4()
                await conn.execute(
                    """
                    INSERT INTO documents (
                        id, title, document_type, document_number,
                        legal_area, hierarchy, source, source_url, is_active
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, true)
                    """,
                    doc_id,
                    doc["title"],
                    doc["type"],
                    doc["number"],
                    doc["area"],
                    doc.get("hierarchy", "legal"),
                    doc["source"],
                    doc["source_url"],
                )

                for i, chunk in enumerate(doc.get("chunks", [])):
                    chunk_id = uuid.uuid4()
                    content = chunk.get("content", "")
                    await conn.execute(
                        """
                        INSERT INTO document_chunks (
                            id, document_id, chunk_index, content,
                            legal_area, article_number, section_path, token_count
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                        chunk_id,
                        doc_id,
                        i,
                        content,
                        doc["area"],
                        chunk.get("article_number", ""),
                        chunk.get("section_path", f"{doc['source']} > {doc['title']}"),
                        len(content.split()),
                    )
                    inserted_chunks += 1

                inserted_docs += 1
                self.logger.info(
                    f"  [{self.name}] Inserted: {doc['number']} ({doc['area']})"
                )

            return {
                "docs": inserted_docs,
                "chunks": inserted_chunks,
                "skipped": skipped,
            }

        finally:
            await conn.close()

    async def run(self) -> dict:
        """Full pipeline: scrape then ingest. Returns combined stats."""
        self.logger.info(f"Starting scraper: {self.name}")
        try:
            docs = await self.scrape()
            self.logger.info(f"[{self.name}] Scraped {len(docs)} documents")
            result = await self.ingest(docs)
            self.logger.info(
                f"[{self.name}] Done — docs={result['docs']}, "
                f"chunks={result['chunks']}, skipped={result['skipped']}"
            )
            return result
        except Exception as exc:
            self.logger.error(f"[{self.name}] Scraper failed: {exc}", exc_info=True)
            return {"docs": 0, "chunks": 0, "skipped": 0, "error": str(exc)}
        finally:
            await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
