"""
Scraper: Tribunal Fiscal — Resoluciones de Observancia Obligatoria (RTF OO).

Fuente: Colección institucional del MEF publicada en gob.pe:
    https://www.gob.pe/institucion/mef/normas-legales/tipos/88-resolucion-del-tribunal-fiscal

Nota sobre cobertura
--------------------
El sitio oficial del MEF (mef.gob.pe/.../jurisprudencia/...) está protegido
por Imperva + hCaptcha y bloquea automation. Sin embargo el MEF publica sus
RTFs de Observancia Obligatoria también en gob.pe bajo el tipo 88, que es
HTML estático limpio sin captcha. Esa colección es un subconjunto curado de
los RTFs más relevantes (jurisprudencia vinculante).

Para acceder al corpus completo histórico del MEF se requeriría Playwright
con resolución manual del captcha — fuera de scope para este MVP.

Estructura del scrape
---------------------
Lista (sheet=N) → ficha por norma. Cada ficha contiene:
    - Título: "Resolución del Tribunal Fiscal N.° <num>-<sala>-<año>"
    - Sumilla: <meta name="description"> con el extracto jurídico
    - PDF descargable: cdn.www.gob.pe/uploads/document/file/<id>/<file>.pdf
    - Fecha de publicación: "DD de <mes> de YYYY"

Mapeo TukiJuris
---------------
    area = "tributario"
    hierarchy = "administrativo"  (jurisprudencia administrativa vinculante)
    type = "resolucion_tribunal_fiscal"
    source = "tribunal_fiscal"
    number = "RTF <num>-<sala>-<año>"  (idempotency key)
"""

from __future__ import annotations

import asyncio
import logging
import re

from services.ingestion.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://www.gob.pe"
LIST_PATH = "/institucion/mef/normas-legales/tipos/88-resolucion-del-tribunal-fiscal"


# ──────────────────────────────────────────────────────────────────────────
# Regex parsers (no bs4 dependency; tolerant to minor layout changes)
# ──────────────────────────────────────────────────────────────────────────

# Detail link pattern: /institucion/mef/normas-legales/<numeric-id>-<slug>
_DETAIL_LINK_RE = re.compile(
    r'/institucion/mef/normas-legales/(?P<id>\d+)-(?P<slug>[\w\-]+)',
)

# Title pattern in list cards
_RTF_TITLE_RE = re.compile(
    r'Resoluci[oó]n del Tribunal Fiscal\s+N\.?\s*[°º]?\s*([\w\-]+)',
    re.IGNORECASE,
)

# Date in list page text: "23 de abril de 2026"
_DATE_RE = re.compile(
    r'(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
    re.IGNORECASE,
)

# PDF on cdn.www.gob.pe
_PDF_RE = re.compile(
    r'(https://cdn\.www\.gob\.pe/uploads/document/file/\d+/[^"\'\s<>]+\.[Pp][Dd][Ff])',
)

# Meta description (sumilla) on detail page
_META_DESC_RE = re.compile(
    r'<meta\s+content="([^"]+)"\s+name="description"',
)


def _strip_html(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


# ──────────────────────────────────────────────────────────────────────────
# Scraper
# ──────────────────────────────────────────────────────────────────────────

class TribunalFiscalScraper(BaseScraper):
    """Scraper for RTFs de Observancia Obligatoria publicados en gob.pe/mef."""

    def __init__(self, db_url: str, max_sheets: int = 5) -> None:
        super().__init__(db_url=db_url, name="tribunal_fiscal")
        self.max_sheets = max_sheets

    async def scrape(self) -> list[dict]:
        docs: list[dict] = []
        seen_ids: set[str] = set()

        for sheet in range(1, self.max_sheets + 1):
            url = f"{BASE_URL}{LIST_PATH}?sheet={sheet}"
            html = await self._fetch(url)
            if not html:
                break

            entries = self._parse_list_page(html)
            if not entries:
                self.logger.info(f"sheet={sheet} no entries — stopping pagination")
                break

            new_in_page = 0
            for entry in entries:
                if entry["id"] in seen_ids:
                    continue
                seen_ids.add(entry["id"])

                # Enrich with sumilla from detail page
                sumilla = await self._fetch_sumilla(entry["detail_url"])

                doc = self._build_document(entry, sumilla)
                if doc:
                    docs.append(doc)
                    new_in_page += 1

                await asyncio.sleep(0.2)  # be polite to gob.pe

            self.logger.info(
                f"sheet={sheet} entries={len(entries)} new={new_in_page}"
            )
            if new_in_page == 0:
                break
            await asyncio.sleep(0.4)

        return docs

    def _parse_list_page(self, html: str) -> list[dict]:
        """
        Walks the HTML linearly, grouping consecutive (detail_link, pdf_link, date)
        triples per RTF card. The gob.pe normas-legales list always renders cards
        in stable order: title link → "Leer más" link → publication date → PDF link.
        """
        # Collect every detail href occurrence and every PDF/date in HTML order.
        # We iterate detail-link matches and for each, find the next PDF + date
        # that appears AFTER it in the HTML.
        detail_matches = list(_DETAIL_LINK_RE.finditer(html))
        pdf_matches = list(_PDF_RE.finditer(html))
        date_matches = list(_DATE_RE.finditer(html))

        seen_detail_ids: set[str] = set()
        entries: list[dict] = []

        for dm in detail_matches:
            detail_id = dm.group("id")
            if detail_id in seen_detail_ids:
                continue  # title + "Leer más" both link to the same detail page
            seen_detail_ids.add(detail_id)

            # Find next PDF and next date that appear after this card's start
            pos = dm.end()
            next_pdf = next((p.group(1) for p in pdf_matches if p.start() >= pos), None)
            next_date = next((d.group(1) for d in date_matches if d.start() >= pos), None)

            entries.append({
                "id": detail_id,
                "slug": dm.group("slug"),
                "detail_url": f"{BASE_URL}/institucion/mef/normas-legales/{detail_id}-{dm.group('slug')}",
                "pdf_url": next_pdf or "",
                "date": next_date or "",
            })

        return entries

    async def _fetch_sumilla(self, detail_url: str) -> str:
        """Fetch the detail page and extract the sumilla from <meta name=description>."""
        html = await self._fetch(detail_url)
        if not html:
            return ""
        m = _META_DESC_RE.search(html)
        if not m:
            return ""
        sumilla = m.group(1).strip()
        # Sumillas end with "..." in meta description — keep as-is, it's natural
        return sumilla

    def _build_document(self, entry: dict, sumilla: str) -> dict | None:
        slug = entry["slug"]

        # Try to extract a clean RTF number from the slug
        # Slug examples: "02077-q-2014", "06561-1-2007", "0001-2025"
        rtf_number = slug.upper()

        title = f"Resolución del Tribunal Fiscal N.° {rtf_number}"
        document_number = f"RTF {rtf_number}"

        content_parts = [title]
        if sumilla:
            content_parts.append(f"Sumilla: {sumilla}")
        if entry.get("date"):
            content_parts.append(f"Fecha de publicación: {entry['date']}")
        content_parts.append(
            "Órgano emisor: Tribunal Fiscal del Ministerio de Economía y Finanzas (MEF). "
            "Jurisprudencia tributaria de observancia obligatoria."
        )
        if entry.get("pdf_url"):
            content_parts.append(f"PDF oficial: {entry['pdf_url']}")
        content_parts.append(f"Ficha gob.pe: {entry['detail_url']}")

        chunk_content = "\n\n".join(content_parts)

        return {
            "title": title,
            "type": "resolucion_tribunal_fiscal",
            "number": document_number,
            "area": "tributario",
            "hierarchy": "administrativo",
            "source": "tribunal_fiscal",
            "source_url": entry["detail_url"],
            "chunks": [{
                "content": chunk_content,
                "article_number": "",
                "section_path": f"Tribunal Fiscal > RTF {rtf_number}",
            }],
        }

    async def _fetch(self, url: str) -> str | None:
        try:
            r = await self.client.get(url)
            if r.status_code != 200:
                self.logger.debug(f"GET {url} -> {r.status_code}")
                return None
            return r.text
        except Exception as exc:
            self.logger.debug(f"GET {url} failed: {exc}")
            return None


# ──────────────────────────────────────────────────────────────────────────
# CLI entrypoint
# ──────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    db_url = os.environ.get(
        "DATABASE_URL_SYNC",
        "postgresql://postgres:postgres@localhost:5432/agente_derecho",
    ).replace("postgresql+asyncpg://", "postgresql://")

    scraper = TribunalFiscalScraper(db_url=db_url)
    result = asyncio.run(scraper.run())
    print(result)
    sys.exit(0 if "error" not in result else 1)
