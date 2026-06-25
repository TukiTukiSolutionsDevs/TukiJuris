"""
Scraper: gob.pe — Plataforma Digital Única del Estado Peruano.

Cubre la fuente dominante de normativa peruana (~70% de fuentes oficiales):
    https://www.gob.pe/institucion/<slug>/normas-legales?sheet=N

Un solo scraper parametrizado por (institucion_slug, legal_area, hierarchy)
extrae listados de normas de múltiples entidades públicas:
    - SUNAT, INDECOPI, ANPD, SBS, SMV, OSCE, MINAM, OEFA, OSINERGMIN,
      OSIPTEL, MTC, MINSA, DIGEMID, SUSALUD, SUNAFIL, SUNARP, SERVIR,
      OECE (Tribunal Contrataciones), MINJUS, MEF, MINTRA, etc.

Cada listado expone tarjetas con: tipo de norma, número, fecha publicación,
sumilla y URL al detalle (que a su vez contiene PDF descargable).

Para el MVP indexamos el sumario + metadata. La extracción de texto completo
desde PDF se hace en un paso posterior (servicio OCR/PDF).
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from urllib.parse import urljoin

from services.ingestion.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://www.gob.pe"


@dataclass(frozen=True)
class GobPeSource:
    """Definition of a gob.pe institutional collection to scrape."""

    slug: str           # institution slug used in URL (e.g. "sunat", "anpd", "osce")
    legal_area: str     # mapped TukiJuris legal area
    source_label: str   # human-readable source name
    hierarchy: str = "legal"  # constitucional | legal | reglamentario | administrativo
    max_sheets: int = 3       # pages to crawl per source on each run (conservative default)


# ──────────────────────────────────────────────────────────────────────────
# Source catalog — top-priority institutions by area
# ──────────────────────────────────────────────────────────────────────────
GOB_PE_SOURCES: list[GobPeSource] = [
    # Tributario
    GobPeSource("sunat", "tributario", "SUNAT", "reglamentario", 5),
    GobPeSource("mef", "tributario", "MEF", "reglamentario", 3),
    # Datos personales
    GobPeSource("anpd", "datos_personales", "ANPD", "administrativo", 4),
    # Financiero / MV / Seguros
    GobPeSource("sbs", "financiero", "SBS", "reglamentario", 4),
    GobPeSource("smv", "mercado_valores", "SMV", "reglamentario", 3),
    # Contrataciones Estado
    GobPeSource("osce", "contrataciones_estado", "OSCE", "reglamentario", 5),
    GobPeSource("oece", "contrataciones_estado", "OECE - Tribunal Contrataciones", "administrativo", 4),
    # Ambiental
    GobPeSource("minam", "ambiental", "MINAM", "reglamentario", 4),
    GobPeSource("oefa", "ambiental", "OEFA", "administrativo", 4),
    # Sectoriales
    GobPeSource("osinergmin", "hidrocarburos", "OSINERGMIN", "reglamentario", 4),
    GobPeSource("osiptel", "telecom", "OSIPTEL", "reglamentario", 3),
    GobPeSource("mtc", "transporte", "MTC", "reglamentario", 3),
    GobPeSource("minsa", "salud", "MINSA", "reglamentario", 3),
    GobPeSource("susalud", "salud", "SUSALUD", "administrativo", 3),
    # Laboral
    GobPeSource("sunafil", "laboral", "SUNAFIL", "administrativo", 3),
    GobPeSource("mtpe", "laboral", "MTPE", "reglamentario", 3),
    # Registral
    GobPeSource("sunarp", "registral", "SUNARP", "reglamentario", 3),
    # Servicio civil
    GobPeSource("servir", "administrativo", "SERVIR", "administrativo", 3),
    # Competencia / Consumidor / PI
    GobPeSource("indecopi", "consumidor", "INDECOPI", "administrativo", 4),
]


# ──────────────────────────────────────────────────────────────────────────
# HTML parsing — tolerant regex (no bs4 dependency required)
# ──────────────────────────────────────────────────────────────────────────

# gob.pe normas-legales cards look roughly like:
#   <article ...>
#     <a href="/institucion/<slug>/normas-legales/<NN>-<title-slug>">
#       <h3>...title...</h3>
#     </a>
#     <p>Tipo: ...  Fecha: ...  Sumilla: ...</p>
#   </article>
# We parse with conservative regex to stay resilient to minor layout changes.

_CARD_RE = re.compile(
    r'<a[^>]+href="(?P<href>/institucion/[^/"]+/normas-legales/[^"#?]+)"[^>]*>'
    r'(?P<inner>.*?)</a>',
    re.DOTALL | re.IGNORECASE,
)
_TITLE_RE = re.compile(r"<h[1-4][^>]*>(?P<title>.*?)</h[1-4]>", re.DOTALL | re.IGNORECASE)
_TAGS_RE = re.compile(r"<[^>]+>")


def _strip_html(s: str) -> str:
    return re.sub(r"\s+", " ", _TAGS_RE.sub(" ", s)).strip()


_DOC_TYPE_HINTS: tuple[tuple[str, str], ...] = (
    ("decreto supremo", "decreto_supremo"),
    ("decreto legislativo", "decreto_legislativo"),
    ("decreto de urgencia", "decreto_urgencia"),
    ("resolución de superintendencia", "resolucion_superintendencia"),
    ("resolución ministerial", "resolucion_ministerial"),
    ("resolución directoral", "resolucion_directoral"),
    ("resolución de consejo directivo", "resolucion_consejo"),
    ("resolución administrativa", "resolucion_administrativa"),
    ("resolución", "resolucion"),
    ("ley n", "ley"),
    ("ley ", "ley"),
    ("circular", "circular"),
    ("directiva", "directiva"),
    ("opinión", "opinion"),
)


def _detect_doc_type(title: str) -> str:
    low = title.lower()
    for needle, label in _DOC_TYPE_HINTS:
        if needle in low:
            return label
    return "norma"


_NUMBER_RE = re.compile(
    r"(?:N[°º\.]?\s*)?(\d{1,5}-\d{2,4}(?:-[A-Z0-9/]+)?|\d{4,6})",
    re.IGNORECASE,
)


def _extract_document_number(title: str, source_label: str) -> str:
    match = _NUMBER_RE.search(title)
    base = match.group(1) if match else title[:60].strip()
    return f"{source_label} - {base}"


# ──────────────────────────────────────────────────────────────────────────
# Scraper
# ──────────────────────────────────────────────────────────────────────────

class GobPeScraper(BaseScraper):
    """Generic scraper for gob.pe institutional `normas-legales` collections."""

    def __init__(self, db_url: str, sources: list[GobPeSource] | None = None) -> None:
        super().__init__(db_url=db_url, name="gob_pe")
        self.sources = sources or GOB_PE_SOURCES

    async def scrape(self) -> list[dict]:
        docs: list[dict] = []
        for src in self.sources:
            try:
                docs.extend(await self._scrape_source(src))
            except Exception as exc:
                self.logger.warning(f"[{src.slug}] scrape failed: {exc}")
            await asyncio.sleep(0.5)  # be polite between institutions
        return docs

    async def _scrape_source(self, src: GobPeSource) -> list[dict]:
        out: list[dict] = []
        seen_urls: set[str] = set()
        for sheet in range(1, src.max_sheets + 1):
            url = f"{BASE_URL}/institucion/{src.slug}/normas-legales?sheet={sheet}"
            html = await self._fetch(url)
            if not html:
                break
            cards = list(_CARD_RE.finditer(html))
            if not cards:
                # No more results — stop paginating
                break

            new_in_page = 0
            for m in cards:
                href = m.group("href")
                inner = m.group("inner")
                detail_url = urljoin(BASE_URL, href)
                if detail_url in seen_urls:
                    continue
                seen_urls.add(detail_url)

                title_match = _TITLE_RE.search(inner)
                title_text = _strip_html(
                    title_match.group("title") if title_match else inner
                )
                if not title_text or len(title_text) < 8:
                    continue

                doc_type = _detect_doc_type(title_text)
                doc_number = _extract_document_number(title_text, src.source_label)

                # Single chunk per norma: title is the searchable summary
                # Full PDF text extraction is a separate downstream pipeline.
                chunk_content = (
                    f"{title_text}\n\n"
                    f"Entidad emisora: {src.source_label}.\n"
                    f"Tipo: {doc_type.replace('_', ' ').title()}.\n"
                    f"Fuente oficial: {detail_url}"
                )

                out.append({
                    "title": title_text[:1000],
                    "type": doc_type,
                    "number": doc_number,
                    "area": src.legal_area,
                    "hierarchy": src.hierarchy,
                    "source": f"gob.pe/{src.slug}",
                    "source_url": detail_url,
                    "chunks": [{
                        "content": chunk_content,
                        "article_number": "",
                        "section_path": f"{src.source_label} > Normas Legales",
                    }],
                })
                new_in_page += 1

            self.logger.info(
                f"[{src.slug}] sheet={sheet} cards={len(cards)} new={new_in_page}"
            )
            if new_in_page == 0:
                break
            await asyncio.sleep(0.3)
        return out

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

    scraper = GobPeScraper(db_url=db_url)
    result = asyncio.run(scraper.run())
    print(result)
    sys.exit(0 if "error" not in result else 1)
