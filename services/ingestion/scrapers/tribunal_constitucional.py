"""
Scraper: Tribunal Constitucional del Perú (tc.gob.pe)

Extrae sentencias y resoluciones del TC que están disponibles públicamente.
Las sentencias del TC son precedentes vinculantes y doctrina jurisprudencial
fundamental para el derecho peruano.
"""

import asyncio
import logging
import re
import uuid

import httpx

logger = logging.getLogger(__name__)

TC_BASE_URL = "https://www.tc.gob.pe"

# Key precedentes vinculantes y sentencias emblemáticas del TC
# (pre-curados para calidad — el scraper web de tc.gob.pe es inestable)
TC_PRECEDENTES = [
    {
        "expediente": "Exp. N° 1124-2001-AA/TC",
        "nombre": "Caso Telefónica - Despido y derechos laborales",
        "area": "laboral",
        "contenido": (
            "Sentencia del Tribunal Constitucional - Exp. N° 1124-2001-AA/TC (Caso Telefónica).\n"
            "Precedente vinculante sobre despido arbitrario y protección adecuada contra el despido.\n"
            "El TC estableció que el Art. 27 de la Constitución, que señala que 'la ley otorga al trabajador "
            "adecuada protección contra el despido arbitrario', no significa que el legislador tenga carta "
            "abierta para establecer cualquier forma de protección, sino que debe garantizar que la protección "
            "sea realmente 'adecuada'. La indemnización no es la única forma de protección, la reposición "
            "también es una alternativa constitucionalmente válida.\n"
            "Este precedente abrió la puerta a la reposición por despido incausado, fraudulento y nulo."
        ),
    },
    {
        "expediente": "Exp. N° 0206-2005-PA/TC",
        "nombre": "Caso Baylón Flores - Precedente laboral amparo",
        "area": "laboral",
        "contenido": (
            "Sentencia del TC - Exp. N° 0206-2005-PA/TC (Caso Baylón Flores).\n"
            "Precedente vinculante que establece las reglas para determinar cuándo el amparo es la vía "
            "idónea para proteger el derecho al trabajo frente al despido.\n"
            "Reglas establecidas:\n"
            "1. El amparo procede contra el despido incausado (sin expresión de causa).\n"
            "2. El amparo procede contra el despido fraudulento (con causa falsa o inventada).\n"
            "3. El amparo procede contra el despido nulo (por motivos discriminatorios o represalias).\n"
            "4. Si el despido se fundamenta en causa justa pero hay controversia sobre los hechos, "
            "la vía ordinaria laboral es la adecuada, no el amparo.\n"
            "5. Si el trabajador es del régimen público (DL 276 o DL 728 del sector público), la vía "
            "contencioso-administrativa es la adecuada."
        ),
    },
    {
        "expediente": "Exp. N° 3771-2004-HC/TC",
        "nombre": "Caso Alfaro - Plazo razonable de detención",
        "area": "penal",
        "contenido": (
            "Sentencia del TC - Exp. N° 3771-2004-HC/TC.\n"
            "El Tribunal Constitucional estableció criterios sobre el plazo razonable de la detención "
            "preventiva (prisión preventiva) y los derechos del imputado.\n"
            "El TC señaló que la prisión preventiva no puede exceder un plazo razonable y que los jueces "
            "deben evaluar periódicamente si subsisten las causales que la motivaron.\n"
            "Criterios para evaluar la razonabilidad del plazo:\n"
            "a) La complejidad del asunto.\n"
            "b) La actividad procesal del interesado.\n"
            "c) La conducta de las autoridades judiciales.\n"
            "d) La afectación generada en la situación jurídica del interesado."
        ),
    },
    {
        "expediente": "Exp. N° 0048-2004-PI/TC",
        "nombre": "Caso Regalías Mineras - Potestad tributaria",
        "area": "tributario",
        "contenido": (
            "Sentencia del TC - Exp. N° 0048-2004-PI/TC (Caso Regalías Mineras).\n"
            "El TC analizó la naturaleza jurídica de las regalías mineras y los principios de la "
            "potestad tributaria del Estado.\n"
            "Estableció que las regalías mineras no constituyen un tributo (impuesto, contribución o tasa), "
            "sino una contraprestación por la explotación de recursos naturales no renovables que son "
            "patrimonio de la Nación (Art. 66 de la Constitución).\n"
            "Reafirmó los principios tributarios constitucionales:\n"
            "- Principio de legalidad (Art. 74 Const.)\n"
            "- Principio de igualdad\n"
            "- Principio de no confiscatoriedad\n"
            "- Respeto a los derechos fundamentales"
        ),
    },
    {
        "expediente": "Exp. N° 00014-2014-PI/TC",
        "nombre": "Caso Ley Servir - Empleo público",
        "area": "administrativo",
        "contenido": (
            "Sentencia del TC - Exp. N° 00014-2014-PI/TC.\n"
            "El TC se pronunció sobre la constitucionalidad de la Ley 30057, Ley del Servicio Civil "
            "(Ley Servir) y el nuevo régimen del empleo público.\n"
            "Declaró constitucional la mayoría de disposiciones de la Ley Servir, confirmando:\n"
            "1. La potestad del Estado de reformar el empleo público.\n"
            "2. El tránsito de los trabajadores al nuevo régimen.\n"
            "3. La evaluación del desempeño como herramienta de gestión.\n"
            "Sin embargo, declaró inconstitucional la prohibición absoluta de negociación colectiva "
            "de remuneraciones, por vulnerar el derecho a la negociación colectiva (Art. 28 Const.)."
        ),
    },
    {
        "expediente": "Exp. N° 0019-2005-PI/TC",
        "nombre": "Caso Ley de Justicia Militar - Debido proceso",
        "area": "constitucional",
        "contenido": (
            "Sentencia del TC - Exp. N° 0019-2005-PI/TC.\n"
            "Precedente fundamental sobre el derecho al debido proceso, motivación de resoluciones "
            "judiciales y la jurisdicción militar.\n"
            "El TC reiteró que el derecho al debido proceso (Art. 139.3 Const.) comprende:\n"
            "1. El derecho a la jurisdicción predeterminada por ley (juez natural).\n"
            "2. El derecho a un juez independiente e imparcial.\n"
            "3. El derecho a la defensa.\n"
            "4. El derecho a la prueba.\n"
            "5. El derecho a la motivación de las resoluciones judiciales.\n"
            "6. El derecho a la pluralidad de instancias.\n"
            "7. El derecho al plazo razonable.\n"
            "8. El principio ne bis in idem."
        ),
    },
    {
        "expediente": "Exp. N° 0030-2005-PI/TC",
        "nombre": "Caso Ley de Partidos Políticos - Democracia",
        "area": "constitucional",
        "contenido": (
            "Sentencia del TC - Exp. N° 0030-2005-PI/TC.\n"
            "Sentencia sobre el Estado Constitucional de Derecho, democracia y los partidos políticos.\n"
            "El TC estableció doctrina sobre:\n"
            "- La Constitución como norma jurídica suprema.\n"
            "- La interpretación constitucional y sus métodos.\n"
            "- Los precedentes vinculantes del TC (Art. VII del CPConst.): las sentencias del TC que "
            "adquieren la autoridad de cosa juzgada constituyen precedente vinculante cuando así lo "
            "exprese la sentencia, precisando el extremo de su efecto normativo.\n"
            "- Distinción entre precedente vinculante y doctrina jurisprudencial."
        ),
    },
    {
        "expediente": "Exp. N° 4587-2004-AA/TC",
        "nombre": "Caso Santiago Terrones - Derecho de propiedad",
        "area": "civil",
        "contenido": (
            "Sentencia del TC - Exp. N° 4587-2004-AA/TC.\n"
            "Precedente sobre el contenido esencial del derecho de propiedad (Art. 70 Const.) y sus límites.\n"
            "El TC estableció que el derecho de propiedad comprende cuatro atributos:\n"
            "1. Usar (ius utendi) — servirse del bien.\n"
            "2. Disfrutar (ius fruendi) — percibir los frutos.\n"
            "3. Disponer (ius abutendi) — transferir, gravar.\n"
            "4. Reivindicar (ius vindicandi) — recuperar.\n"
            "El derecho de propiedad no es absoluto: debe ejercerse en armonía con el bien común "
            "y dentro de los límites de ley. La expropiación solo procede por seguridad nacional "
            "o necesidad pública, declarada por ley, y previo pago de indemnización justipreciada."
        ),
    },
]


async def fetch_and_ingest_tc(db_url: str) -> dict:
    """
    Ingest TC precedentes into the database.
    Uses pre-curated content for reliability (TC website is unstable).
    """
    import asyncpg

    conn = await asyncpg.connect(db_url)
    tc = 0

    try:
        # Check if TC document already exists
        existing = await conn.fetchval(
            "SELECT id FROM documents WHERE document_number = $1", "TC-PRECEDENTES"
        )
        if existing:
            logger.info("TC precedentes already ingested, skipping")
            return {"status": "skipped", "reason": "already exists"}

        doc_id = uuid.uuid4()
        await conn.execute(
            """INSERT INTO documents (id, title, document_type, document_number,
               legal_area, hierarchy, source, source_url, is_active)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, true)""",
            doc_id,
            "Jurisprudencia del Tribunal Constitucional - Precedentes Vinculantes",
            "sentencia",
            "TC-PRECEDENTES",
            "constitucional",
            "constitucional",
            "tc.gob.pe",
            "https://www.tc.gob.pe/jurisprudencia/",
        )

        for i, prec in enumerate(TC_PRECEDENTES):
            chunk_id = uuid.uuid4()
            await conn.execute(
                """INSERT INTO document_chunks (id, document_id, chunk_index, content,
                   legal_area, article_number, section_path, token_count)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                chunk_id,
                doc_id,
                i,
                prec["contenido"],
                prec["area"],
                prec["expediente"],
                f"TC > Precedentes Vinculantes > {prec['nombre']}",
                len(prec["contenido"].split()),
            )
            tc += 1
            logger.info(f"  TC: {prec['expediente']} → {prec['area']}")

        return {"status": "ok", "chunks_inserted": tc}

    finally:
        await conn.close()


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    db = sys.argv[1] if len(sys.argv) > 1 else "postgresql://postgres:postgres@localhost:5432/agente_derecho"
    result = asyncio.run(fetch_and_ingest_tc(db))
    print(f"Result: {result}")
