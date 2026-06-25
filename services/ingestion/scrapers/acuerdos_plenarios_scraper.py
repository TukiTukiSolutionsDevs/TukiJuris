"""
Scraper: Acuerdos Plenarios de la Corte Suprema (Materia Penal).

Fuente oficial: Portal del Centro de Investigaciones Judiciales (CIJ) del
Poder Judicial del Perú, bajo la sección Jurisprudencia Sistematizada:

    https://www.pj.gob.pe/wps/wcm/connect/cij-juris/.../as_acuerdos_plenarios/
        as_AcuerdosPlenariosenMateriaPenal/
            as_AcuerdosPlenarios{YYYY}/                  (años regulares)
            as_AcuerdosPlenos{YYYY}/                     (variante de naming)
            as_AcuerdosPlenosExtraordinarios{YYYY}/      (plenos extraordinarios)

Estructura de cada página de año:
    Tabla HTML con filas `<tr class="tabla">`. Cada fila tiene:
        - Celda título: "Acuerdo Plenario N°XX-YYYY/CJ-116" (o /CIJ-116)
        - Celda tema/sumilla
        - Celda fecha publicación
        - Celda con enlace al PDF

PDFs viven en `/wps/wcm/connect/<uuid>/<filename>.pdf?MOD=AJPERES&CACHEID=...`
y se sirven sin captcha.

Materias adicionales (Constitucional, Laboral, Laboral Previsional) tienen
landing pages publicadas pero sin acuerdos cargados aún (verificado 2026-06-24).
Se ignoran por ahora; el scraper acepta materias adicionales de forma
parametrizada para cuando publiquen contenido.

Mapeo TukiJuris
---------------
    area       = "penal"  (todos los acuerdos plenarios publicados son penales)
    hierarchy  = "administrativo"  (jurisprudencia vinculante de la Corte Suprema)
    type       = "acuerdo_plenario"
    source     = "acuerdos_plenarios"
    number     = "AP <num>-<year>/<CJ|CIJ>-116"
"""

from __future__ import annotations

import asyncio
import logging
import re
from urllib.parse import urljoin

from services.ingestion.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://www.pj.gob.pe"
SECTION_PATH = (
    "/wps/wcm/connect/cij-juris/s_cij_jurisprudencia_nuevo/"
    "as_jurisprudencia_sistematizada/as_acuerdos_plenarios/"
)


# ──────────────────────────────────────────────────────────────────────────
# Sub-páginas conocidas (Materia Penal) — verificadas 2026-06-24
# ──────────────────────────────────────────────────────────────────────────
# Cada tupla = (materia_slug, year_slug). El scraper también puede
# autodescubrir sub-páginas leyendo la landing de la materia.

PENAL_YEARS: tuple[str, ...] = (
    "as_AcuerdosPlenos2019",
    "as_AcuerdosPlenos2017",
    "as_AcuerdosPlenosExtraordinarios2016",
    "as_AcuerdosPlenarios2015",
    "as_AcuerdosPlenosExtraordinarios2012",
    "as_AcuerdosPlenarios2012",
    "as_AcuerdosPlenarios2011",
    "as_AcuerdosPlenarios2010",
    "as_AcuerdosPlenarios2009",
    "as_AcuerdosPlenarios2008",
    "as_AcuerdosPlenarios2007",
    "as_AcuerdosPlenarios2006",
    "as_AcuerdosPlenarios2005",
)

MATERIAS: tuple[tuple[str, str], ...] = (
    ("as_AcuerdosPlenariosenMateriaPenal", "penal"),
    # Las materias siguientes están vacías al 2026-06-24 pero se mantienen
    # configuradas para que el scraper se autoexpanda cuando publiquen:
    ("as_AcuerdosPlenariosenMateriaConstitucional", "constitucional"),
    ("as_AcuerdosPlenariosenMateriaLaboralPrevisional", "laboral"),
    ("as_AcuerdosPlenariosenMateriaLaboral", "laboral"),
)


# ──────────────────────────────────────────────────────────────────────────
# Parsers
# ──────────────────────────────────────────────────────────────────────────

# A single content row in the table
_ROW_RE = re.compile(
    r'<tr[^>]*class="tabla"[^>]*>(?P<row>.*?)</tr>',
    re.DOTALL | re.IGNORECASE,
)

# Title cell — captures something like "Acuerdo Plenario N°09-2019/CIJ-116"
_TITLE_RE = re.compile(
    r'Acuerdo\s+Plenari?o?s?\s*'
    r'N\s*[°º&deg;]+\s*'
    r'(?P<num>\d+)\s*-\s*(?P<year>\d{4})'
    r'\s*/\s*(?P<court>CJ|CIJ)\s*-\s*(?P<chamber>\d+)',
    re.IGNORECASE,
)

# Sometimes the table header reads "XI PLENO SUPREMO PENAL - ACUERDO PLENARIO..."
_PLENO_PREFIX_RE = re.compile(
    r'([IVX]+\s+PLENO\s+(?:JURISDICCIONAL\s+)?SUPREMO\s+[A-ZÁÉÍÓÚÑ ]+)',
    re.IGNORECASE,
)

# PDF link inside the row
_PDF_RE = re.compile(
    r'href="(?P<pdf>[^"]+\.pdf[^"]*)"',
    re.IGNORECASE,
)

# Year discovery in materia landing pages
_YEAR_LINK_RE = re.compile(
    r'(as_AcuerdosPlen(?:os|arios)(?:Extraordinarios)?\d{4})',
)

# Plain text cell content extractor
_TAGS_RE = re.compile(r"<[^>]+>")
_HTML_ENTITY_RE = re.compile(r"&([a-z]+|#\d+);", re.IGNORECASE)


_ENTITY_MAP = {
    "nbsp": " ",
    "amp": "&",
    "deg": "°",
    "ordm": "º",
    "aacute": "á",
    "eacute": "é",
    "iacute": "í",
    "oacute": "ó",
    "uacute": "ú",
    "ntilde": "ñ",
    "Ntilde": "Ñ",
    "lt": "<",
    "gt": ">",
    "quot": '"',
}


def _decode_entities(s: str) -> str:
    def replace(match: re.Match) -> str:
        ent = match.group(1)
        if ent.startswith("#"):
            try:
                return chr(int(ent[1:]))
            except ValueError:
                return match.group(0)
        return _ENTITY_MAP.get(ent, match.group(0))

    return _HTML_ENTITY_RE.sub(replace, s)


def _strip_html(s: str) -> str:
    txt = _decode_entities(_TAGS_RE.sub(" ", s))
    return re.sub(r"\s+", " ", txt).strip()


def _extract_cells(row_html: str) -> list[str]:
    """Returns the visible text of each <td> in the row, in order."""
    return [
        _strip_html(m)
        for m in re.findall(
            r"<td[^>]*>(.*?)</td>", row_html, flags=re.DOTALL | re.IGNORECASE
        )
    ]


# ──────────────────────────────────────────────────────────────────────────
# Scraper
# ──────────────────────────────────────────────────────────────────────────

class AcuerdosPlenariosScraper(BaseScraper):
    """Scraper for Acuerdos Plenarios de la Corte Suprema."""

    def __init__(
        self,
        db_url: str,
        materias: tuple[tuple[str, str], ...] = MATERIAS,
        autodiscover_years: bool = True,
    ) -> None:
        super().__init__(db_url=db_url, name="acuerdos_plenarios")
        self.materias = materias
        self.autodiscover_years = autodiscover_years

    async def scrape(self) -> list[dict]:
        docs: list[dict] = []
        seen_numbers: set[str] = set()

        for materia_slug, area in self.materias:
            years = await self._discover_years(materia_slug)
            if not years:
                self.logger.info(f"[{materia_slug}] sin años con contenido")
                continue

            for year_slug in years:
                url = f"{BASE_URL}{SECTION_PATH}{materia_slug}/{year_slug}/"
                html = await self._fetch(url)
                if not html:
                    continue

                rows = self._parse_year_page(html)
                new_in_page = 0
                for row in rows:
                    if not row["pdf_url"]:
                        # No PDF available for this row — skip; we'll see the
                        # same row again if/when PDF gets published.
                        continue
                    if row["number"] in seen_numbers:
                        continue
                    seen_numbers.add(row["number"])

                    docs.append(self._build_document(row, area, url))
                    new_in_page += 1

                self.logger.info(
                    f"[{materia_slug}/{year_slug}] rows={len(rows)} con_pdf={new_in_page}"
                )
                await asyncio.sleep(0.3)

        return docs

    async def _discover_years(self, materia_slug: str) -> list[str]:
        """Crawl the materia landing page to find available year sub-paths."""
        if not self.autodiscover_years and materia_slug.endswith("MateriaPenal"):
            return list(PENAL_YEARS)

        landing_url = f"{BASE_URL}{SECTION_PATH}{materia_slug}/"
        html = await self._fetch(landing_url)
        if not html:
            return []

        discovered = list(dict.fromkeys(_YEAR_LINK_RE.findall(html)))
        # When auto-discovery yields nothing for Penal, fall back to known set
        if not discovered and materia_slug.endswith("MateriaPenal"):
            return list(PENAL_YEARS)
        return discovered

    def _parse_year_page(self, html: str) -> list[dict]:
        out: list[dict] = []
        for m in _ROW_RE.finditer(html):
            row_html = m.group("row")
            title_match = _TITLE_RE.search(_decode_entities(row_html))
            if not title_match:
                continue

            num = title_match.group("num").lstrip("0") or "0"
            year = title_match.group("year")
            court = title_match.group("court").upper()
            chamber = title_match.group("chamber")
            document_number = f"AP {int(num):02d}-{year}/{court}-{chamber}"

            cells = _extract_cells(row_html)
            # Heuristics: typically 4 cells (title, topic, date, pdf_icon)
            topic = ""
            date = ""
            if len(cells) >= 4:
                # cells[0] contains title text; topic is next; date follows
                topic = cells[1] if len(cells) > 1 else ""
                date = cells[2] if len(cells) > 2 else ""
            elif len(cells) == 3:
                topic = cells[1]
                date = cells[2]

            # Look for Pleno prefix in the title cell (informational)
            pleno_match = _PLENO_PREFIX_RE.search(cells[0]) if cells else None
            pleno_prefix = pleno_match.group(1).strip() if pleno_match else ""

            pdf_match = _PDF_RE.search(row_html)
            pdf_path = pdf_match.group("pdf") if pdf_match else ""
            pdf_url = urljoin(BASE_URL, pdf_path) if pdf_path else ""

            out.append({
                "number": document_number,
                "title_raw": f"Acuerdo Plenario N°{num.zfill(2)}-{year}/{court}-{chamber}",
                "topic": topic,
                "date": date,
                "pdf_url": pdf_url,
                "pleno_prefix": pleno_prefix,
            })
        return out

    def _build_document(self, row: dict, area: str, source_url: str) -> dict:
        topic = row["topic"] or "(sin tema registrado)"
        title = f"{row['title_raw']} — {topic}"[:1000]

        content_parts = [row["title_raw"]]
        if row["pleno_prefix"]:
            content_parts.append(row["pleno_prefix"])
        content_parts.append(f"Tema: {topic}")
        if row["date"]:
            content_parts.append(f"Fecha de publicación: {row['date']}")
        content_parts.append(
            "Órgano emisor: Salas Penales Permanente y Transitorias de la "
            "Corte Suprema de Justicia de la República. "
            "Jurisprudencia vinculante (acuerdo plenario)."
        )
        if row["pdf_url"]:
            content_parts.append(f"PDF oficial: {row['pdf_url']}")
        content_parts.append(f"Listado año: {source_url}")

        chunk_content = "\n\n".join(content_parts)

        return {
            "title": title,
            "type": "acuerdo_plenario",
            "number": row["number"],
            "area": area,
            "hierarchy": "administrativo",
            "source": "acuerdos_plenarios",
            "source_url": row["pdf_url"] or source_url,
            "chunks": [{
                "content": chunk_content,
                "article_number": "",
                "section_path": f"Acuerdos Plenarios > {row['number']}",
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

    scraper = AcuerdosPlenariosScraper(db_url=db_url)
    result = asyncio.run(scraper.run())
    print(result)
    sys.exit(0 if "error" not in result else 1)
