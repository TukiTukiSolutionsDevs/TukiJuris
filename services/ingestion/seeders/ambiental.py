"""
Seed: Derecho Ambiental Peruano.

Núcleo normativo:
    - Ley 28611 (2005) — Ley General del Ambiente (LGA).
    - Ley 27446 (2001) — Ley del SEIA (Sistema Nacional de Evaluación de Impacto Ambiental).
    - DS 019-2009-MINAM — Reglamento Ley del SEIA.
    - Ley 29338 (2009) — Ley de Recursos Hídricos.
    - Ley 29763 (2011) — Ley Forestal y de Fauna Silvestre.
    - Ley 29325 (2009) — SINEFA / crea OEFA.
    - Ley 28245 (2004) — Ley Marco del SNGA.
    - DL 1278 (2016) — Ley de Gestión Integral de Residuos Sólidos.

Cada chunk resume institución o regla con cita exacta del articulado base.
"""

AMBIENTAL_ARTICLES = [
    # ── Ley General del Ambiente ─────────────────────────────────────────
    {
        "article": "I-LGA",
        "section_path": "Ley 28611 > Título Preliminar > Art. I",
        "content": (
            "Artículo I del Título Preliminar.- Derecho y deber fundamental (Ley 28611).\n"
            "Toda persona tiene el derecho irrenunciable a vivir en un ambiente saludable, "
            "equilibrado y adecuado para el pleno desarrollo de la vida, y el deber de "
            "contribuir a una efectiva gestión ambiental y de proteger el ambiente, así como "
            "sus componentes, asegurando particularmente la salud de las personas en forma "
            "individual y colectiva, la conservación de la diversidad biológica, el "
            "aprovechamiento sostenible de los recursos naturales y el desarrollo sostenible "
            "del país."
        ),
    },
    {
        "article": "VI-LGA",
        "section_path": "Ley 28611 > Título Preliminar > Art. VI",
        "content": (
            "Artículo VI del Título Preliminar.- Principio de prevención (Ley 28611).\n"
            "La gestión ambiental tiene como objetivos prioritarios prevenir, vigilar y evitar "
            "la degradación ambiental. Cuando no sea posible eliminar las causas que la "
            "generan, se adoptan las medidas de mitigación, recuperación, restauración o "
            "eventual compensación, que correspondan."
        ),
    },
    {
        "article": "VII-LGA",
        "section_path": "Ley 28611 > Título Preliminar > Art. VII",
        "content": (
            "Artículo VII del Título Preliminar.- Principio precautorio (Ley 28611).\n"
            "Cuando haya peligro de daño grave o irreversible, la falta de certeza absoluta no "
            "debe utilizarse como razón para postergar la adopción de medidas eficaces y "
            "eficientes para impedir la degradación del ambiente."
        ),
    },
    {
        "article": "VIII-LGA",
        "section_path": "Ley 28611 > Título Preliminar > Art. VIII",
        "content": (
            "Artículo VIII del Título Preliminar.- Principio de internalización de costos (Ley 28611).\n"
            "Toda persona natural o jurídica, pública o privada, debe asumir el costo de los "
            "riesgos o daños que genere sobre el ambiente. El costo de las acciones de "
            "prevención, vigilancia, restauración, rehabilitación, reparación y compensación "
            "ambiental se rige por el principio de internalización de costos — principio "
            "'el que contamina paga'."
        ),
    },
    {
        "article": "IX-LGA",
        "section_path": "Ley 28611 > Título Preliminar > Art. IX",
        "content": (
            "Artículo IX del Título Preliminar.- Principio de responsabilidad ambiental (Ley 28611).\n"
            "El causante de la degradación del ambiente y de sus componentes, sea una persona "
            "natural o jurídica, pública o privada, está obligado a adoptar inexcusablemente "
            "las medidas para su restauración, rehabilitación o reparación según corresponda "
            "o, cuando ello no sea posible, a compensar en términos ambientales los daños "
            "generados, sin perjuicio de otras responsabilidades administrativas, civiles o "
            "penales a que hubiera lugar."
        ),
    },
    {
        "article": "24-LGA",
        "section_path": "Ley 28611 > Capítulo 3 > Art. 24-27 SEIA",
        "content": (
            "Artículos 24-27.- Sistema Nacional de Evaluación de Impacto Ambiental — SEIA (Ley 28611).\n"
            "Toda actividad humana que implique construcciones, obras, servicios y otras "
            "actividades, así como las políticas, planes y programas públicos susceptibles de "
            "causar impactos ambientales de carácter significativo, está sujeta al SEIA.\n\n"
            "Categorías de instrumentos:\n"
            "- Cat. I: Declaración de Impacto Ambiental (DIA) — impactos leves.\n"
            "- Cat. II: Estudio de Impacto Ambiental Semidetallado (EIA-sd) — impactos moderados.\n"
            "- Cat. III: Estudio de Impacto Ambiental Detallado (EIA-d) — impactos significativos.\n\n"
            "Sin certificación ambiental aprobada NO se autoriza el inicio de actividades.\n\n"
            "Autoridad técnica: SENACE (Servicio Nacional de Certificación Ambiental para las "
            "Inversiones Sostenibles) para proyectos sujetos a EIA-d; sectores para los demás."
        ),
    },
    # ── Ley del SEIA ─────────────────────────────────────────────────────
    {
        "article": "1-SEIA",
        "section_path": "Ley 27446 > Art. 1",
        "content": (
            "Artículo 1.- Objeto (Ley 27446 — Ley del SEIA).\n"
            "Se crea el Sistema Nacional de Evaluación del Impacto Ambiental (SEIA), como un "
            "sistema único y coordinado de identificación, prevención, supervisión, control y "
            "corrección anticipada de los impactos ambientales negativos derivados de las "
            "acciones humanas expresadas por medio del proyecto de inversión.\n\n"
            "También establece un proceso uniforme que comprende los requerimientos, etapas y "
            "alcances de las evaluaciones del impacto ambiental de proyectos de inversión."
        ),
    },
    {
        "article": "6-SEIA",
        "section_path": "Ley 27446 > Art. 6",
        "content": (
            "Artículo 6.- Procedimiento para la certificación ambiental (Ley 27446).\n"
            "El procedimiento consta de:\n"
            "1. Clasificación del proyecto en una de las tres categorías (I, II o III).\n"
            "2. Aprobación de los términos de referencia para el EIA cuando corresponda.\n"
            "3. Elaboración del estudio ambiental por el titular del proyecto a través de "
            "consultoras inscritas en el Registro Nacional de Consultoras Ambientales.\n"
            "4. Mecanismos de participación ciudadana (audiencias públicas, talleres, "
            "consulta previa cuando aplique).\n"
            "5. Evaluación del estudio por la autoridad competente.\n"
            "6. Resolución que otorga o deniega la certificación ambiental.\n"
            "7. Seguimiento, fiscalización y control durante la operación."
        ),
    },
    # ── Recursos Hídricos ────────────────────────────────────────────────
    {
        "article": "1-LRH",
        "section_path": "Ley 29338 > Art. 1-2",
        "content": (
            "Artículos 1-2.- Disposiciones generales (Ley 29338 — Ley de Recursos Hídricos).\n"
            "El agua es un recurso natural renovable, indispensable para la vida, vulnerable y "
            "estratégico para el desarrollo sostenible, el mantenimiento de los sistemas y "
            "ciclos naturales que la sustentan, y la seguridad de la Nación.\n\n"
            "El agua constituye PATRIMONIO DE LA NACIÓN. El dominio sobre ella es inalienable "
            "e imprescriptible. No hay propiedad privada sobre el agua. Su uso requiere "
            "AUTORIZACIÓN, PERMISO o LICENCIA otorgada por la Autoridad Nacional del Agua (ANA)."
        ),
    },
    {
        "article": "44-LRH",
        "section_path": "Ley 29338 > Art. 44-58 Usos",
        "content": (
            "Artículos 44-58.- Usos del agua (Ley 29338).\n"
            "ORDEN DE PRELACIÓN (preferencia por escasez):\n"
            "1. Uso primario — directo y para necesidades humanas.\n"
            "2. Uso poblacional — consumo humano colectivo, saneamiento.\n"
            "3. Uso productivo — agrario, acuícola, energético, industrial, minero, recreativo, "
            "turístico, transporte.\n\n"
            "Derechos de uso del agua:\n"
            "- LICENCIA: derecho permanente para uso productivo, oneroso, transferible.\n"
            "- PERMISO: derecho temporal para usos productivos eventuales.\n"
            "- AUTORIZACIÓN: para usos transitorios (estudios, construcción de obras).\n\n"
            "RETRIBUCIÓN ECONÓMICA: todo uso productivo paga retribución a la ANA, conforme a "
            "valores fijados por DS anual del MINAGRI."
        ),
    },
    # ── Ley Forestal y Fauna Silvestre ───────────────────────────────────
    {
        "article": "1-LFFS",
        "section_path": "Ley 29763 > Disposiciones generales",
        "content": (
            "Artículos 1-3.- Disposiciones generales (Ley 29763 — Ley Forestal y de Fauna Silvestre).\n"
            "Patrimonio Forestal de la Nación: comprende los recursos forestales y de fauna "
            "silvestre, mantenidos en su fuente, los servicios ecosistémicos, las áreas que "
            "los contienen, los ecosistemas frágiles y los recursos hidrobiológicos en aguas "
            "continentales y los espacios para la fauna silvestre.\n\n"
            "Autoridad: SERFOR (Servicio Nacional Forestal y de Fauna Silvestre).\n"
            "Aprovechamiento sujeto a TÍTULO HABILITANTE: concesiones forestales con fines "
            "maderables o no maderables, permisos, autorizaciones."
        ),
    },
    # ── OEFA / SINEFA ────────────────────────────────────────────────────
    {
        "article": "1-SINEFA",
        "section_path": "Ley 29325 > Art. 1-11 — OEFA",
        "content": (
            "Artículos 1-11.- SINEFA y OEFA (Ley 29325).\n"
            "Crea el Sistema Nacional de Evaluación y Fiscalización Ambiental (SINEFA) con el "
            "Organismo de Evaluación y Fiscalización Ambiental (OEFA) como ente RECTOR.\n\n"
            "Funciones OEFA:\n"
            "1. Función evaluadora: monitoreo, vigilancia y caracterización ambiental.\n"
            "2. Función supervisora directa: verificación del cumplimiento normativo.\n"
            "3. Función fiscalizadora y sancionadora: imposición de sanciones y medidas correctivas.\n"
            "4. Función normativa: emisión de normas técnicas en su ámbito.\n"
            "5. Función de aplicación de incentivos: registro de buenas prácticas.\n\n"
            "Sectores bajo competencia OEFA: minería (gran y mediana), hidrocarburos, "
            "electricidad, pesquería industrial, industria manufacturera y otros que se le "
            "transfieren progresivamente desde sectores."
        ),
    },
    {
        "article": "17-SINEFA",
        "section_path": "Ley 29325 > Art. 17-22 — Sanciones",
        "content": (
            "Artículos 17-22.- Régimen sancionador OEFA (Ley 29325 + RCD 045-2013-OEFA/CD).\n"
            "Infracciones clasificadas en LEVE, GRAVE y MUY GRAVE según matriz de "
            "tipificación específica por sector.\n\n"
            "Multas: pueden alcanzar hasta 30,000 UIT por infracción muy grave, con "
            "consideración de circunstancias agravantes y atenuantes (intencionalidad, "
            "daño ambiental, reincidencia, beneficio económico ilícito).\n\n"
            "Procedimiento administrativo sancionador (PAS): imputación de cargos → descargos "
            "(15 días hábiles) → resolución de primera instancia (Dirección de Fiscalización "
            "y Aplicación de Incentivos — DFAI) → recurso de apelación ante el Tribunal de "
            "Fiscalización Ambiental (TFA) → agotamiento de vía administrativa → contencioso "
            "administrativo."
        ),
    },
    # ── Residuos sólidos ─────────────────────────────────────────────────
    {
        "article": "1-RS",
        "section_path": "DL 1278 > Art. 1-7 Principios",
        "content": (
            "Artículos 1-7.- Principios de gestión de residuos sólidos (DL 1278 — Ley de GIRS).\n"
            "Principios rectores:\n"
            "1. Economía circular: maximizar el aprovechamiento de los residuos, valorizándolos.\n"
            "2. Valorización: prioridad a la valorización energética y material sobre la "
            "disposición final.\n"
            "3. Responsabilidad extendida del productor (REP): los fabricantes responden por "
            "el ciclo de vida completo de sus productos.\n"
            "4. Internalización de costos: el generador asume el costo del manejo de sus residuos.\n"
            "5. Protección del ambiente y la salud pública.\n\n"
            "Clasificación de residuos: por origen (urbano, no domiciliario), por peligrosidad "
            "(peligroso, no peligroso), por gestión (municipal, no municipal).\n\n"
            "Operadores: empresas operadoras de residuos sólidos (EO-RS) deben estar "
            "registradas en MINAM y autorizadas por DIGESA/DIRESA para residuos peligrosos."
        ),
    },
    # ── Áreas naturales protegidas ───────────────────────────────────────
    {
        "article": "ANP",
        "section_path": "Ley 26834 > ANP",
        "content": (
            "Ley 26834 — Ley de Áreas Naturales Protegidas (ANP).\n"
            "Las ANP son espacios continentales y/o marinos del territorio nacional reconocidos, "
            "establecidos y protegidos legalmente por el Estado por su importancia para la "
            "conservación de la diversidad biológica y otros valores asociados.\n\n"
            "Categorías de ANP:\n"
            "1. Parques Nacionales — uso indirecto (investigación, ecoturismo).\n"
            "2. Santuarios Nacionales.\n"
            "3. Santuarios Históricos.\n"
            "4. Reservas Paisajísticas.\n"
            "5. Refugios de Vida Silvestre.\n"
            "6. Reservas Nacionales — aprovechamiento controlado.\n"
            "7. Reservas Comunales.\n"
            "8. Bosques de Protección.\n"
            "9. Cotos de Caza.\n"
            "10. Zonas Reservadas — transitorias.\n\n"
            "Autoridad: SERNANP (Servicio Nacional de Áreas Naturales Protegidas por el Estado).\n"
            "Cualquier actividad dentro de ANP requiere compatibilidad y opinión técnica vinculante "
            "del SERNANP."
        ),
    },
    {
        "article": "Consulta-Previa",
        "section_path": "Ley 29785 > Consulta previa",
        "content": (
            "Ley 29785 — Ley del Derecho a la Consulta Previa a los Pueblos Indígenas u "
            "Originarios (PIO), conforme al Convenio 169 OIT.\n\n"
            "Derecho de los pueblos indígenas u originarios a ser consultados de forma previa "
            "sobre las medidas legislativas o administrativas que afecten directamente sus "
            "derechos colectivos, sobre su existencia física, identidad cultural, calidad de "
            "vida o desarrollo.\n\n"
            "Etapas del proceso de consulta:\n"
            "1. Identificación de la medida objeto de consulta.\n"
            "2. Identificación de los pueblos indígenas a ser consultados.\n"
            "3. Publicidad de la medida.\n"
            "4. Información sobre la medida.\n"
            "5. Evaluación interna por las organizaciones de los PIO.\n"
            "6. Proceso de diálogo intercultural.\n"
            "7. Decisión final de la entidad estatal.\n\n"
            "Plazo del proceso: máximo 120 días calendario. La decisión final corresponde al "
            "Estado, pero debe estar adecuadamente motivada.\n"
            "Aplicable a proyectos extractivos (minería, hidrocarburos, forestal) que afecten "
            "territorios de comunidades."
        ),
    },
]
