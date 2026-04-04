"""
Seed: Código Civil Peruano (DL 295, 1984) — Artículos más consultados.
"""

CIVIL_ARTICLES = [
    # === TÍTULO PRELIMINAR ===
    {
        "article": "TP-III",
        "section_path": "CC > Título Preliminar > Art. III",
        "content": (
            "Artículo III del Título Preliminar.- La ley se aplica a las consecuencias de las relaciones "
            "y situaciones jurídicas existentes. No tiene fuerza ni efectos retroactivos, salvo las "
            "excepciones previstas en la Constitución Política del Perú."
        ),
    },
    # === ACTO JURÍDICO ===
    {
        "article": "140",
        "section_path": "CC > Libro II > Acto Jurídico > Requisitos de validez",
        "content": (
            "Artículo 140.- El acto jurídico es la manifestación de voluntad destinada a crear, regular, "
            "modificar o extinguir relaciones jurídicas. Para su validez se requiere:\n"
            "1. Agente capaz.\n"
            "2. Objeto física y jurídicamente posible.\n"
            "3. Fin lícito.\n"
            "4. Observancia de la forma prescrita bajo sanción de nulidad."
        ),
    },
    {
        "article": "219",
        "section_path": "CC > Libro II > Acto Jurídico > Nulidad",
        "content": (
            "Artículo 219.- El acto jurídico es nulo:\n"
            "1. Cuando falta la manifestación de voluntad del agente.\n"
            "2. Cuando se haya practicado por persona absolutamente incapaz, salvo lo dispuesto en el artículo 1358.\n"
            "3. Cuando su objeto es física o jurídicamente imposible o cuando sea indeterminable.\n"
            "4. Cuando su fin sea ilícito.\n"
            "5. Cuando adolezca de simulación absoluta.\n"
            "6. Cuando no revista la forma prescrita bajo sanción de nulidad.\n"
            "7. Cuando la ley lo declara nulo.\n"
            "8. En el caso del artículo V del Título Preliminar, salvo que la ley establezca sanción diversa."
        ),
    },
    # === DERECHOS REALES — PROPIEDAD ===
    {
        "article": "923",
        "section_path": "CC > Libro V > Derechos Reales > Propiedad",
        "content": (
            "Artículo 923.- La propiedad es el poder jurídico que permite usar, disfrutar, disponer y "
            "reivindicar un bien. Debe ejercerse en armonía con el interés social y dentro de los límites de la ley."
        ),
    },
    {
        "article": "950",
        "section_path": "CC > Libro V > Derechos Reales > Prescripción adquisitiva",
        "content": (
            "Artículo 950.- La propiedad inmueble se adquiere por prescripción mediante la posesión continua, "
            "pacífica y pública como propietario durante diez años.\n"
            "Se adquiere a los cinco años cuando median justo título y buena fe."
        ),
    },
    # === OBLIGACIONES ===
    {
        "article": "1132",
        "section_path": "CC > Libro VI > Obligaciones > Obligaciones de dar",
        "content": (
            "Artículo 1132.- El acreedor de bien cierto no puede ser obligado a recibir otro, aunque éste "
            "sea de mayor valor."
        ),
    },
    {
        "article": "1219",
        "section_path": "CC > Libro VI > Obligaciones > Efectos de las obligaciones",
        "content": (
            "Artículo 1219.- Es efecto de las obligaciones autorizar al acreedor para lo siguiente:\n"
            "1. Emplear las medidas legales a fin de que el deudor le procure aquello a que está obligado.\n"
            "2. Procurarse la prestación o hacérsela procurar por otro, a costa del deudor.\n"
            "3. Obtener del deudor la indemnización correspondiente.\n"
            "4. Ejercer los derechos del deudor, sea en vía de acción o para asumir su defensa, "
            "con excepción de los que sean inherentes a la persona o cuando lo prohíba la ley."
        ),
    },
    {
        "article": "1242",
        "section_path": "CC > Libro VI > Obligaciones > Intereses",
        "content": (
            "Artículo 1242.- El interés es compensatorio cuando constituye la contraprestación por el uso "
            "del dinero o de cualquier otro bien.\n"
            "Es moratorio cuanto tiene por finalidad indemnizar la mora en el pago."
        ),
    },
    # === CONTRATOS ===
    {
        "article": "1351",
        "section_path": "CC > Libro VII > Fuentes de las Obligaciones > Contratos > Disposiciones generales",
        "content": (
            "Artículo 1351.- El contrato es el acuerdo de dos o más partes para crear, regular, modificar "
            "o extinguir una relación jurídica patrimonial."
        ),
    },
    {
        "article": "1352",
        "section_path": "CC > Libro VII > Fuentes de las Obligaciones > Contratos > Disposiciones generales",
        "content": (
            "Artículo 1352.- Los contratos se perfeccionan por el consentimiento de las partes, excepto "
            "aquellos que, además, deben observar la forma señalada por la ley bajo sanción de nulidad."
        ),
    },
    {
        "article": "1361",
        "section_path": "CC > Libro VII > Fuentes de las Obligaciones > Contratos > Fuerza vinculante",
        "content": (
            "Artículo 1361.- Los contratos son obligatorios en cuanto se haya expresado en ellos.\n"
            "Se presume que la declaración expresada en el contrato responde a la voluntad común de las "
            "partes y quien niegue esa coincidencia debe probarla."
        ),
    },
    {
        "article": "1371",
        "section_path": "CC > Libro VII > Fuentes de las Obligaciones > Contratos > Resolución",
        "content": (
            "Artículo 1371.- La resolución deja sin efecto un contrato válido por causal sobreviniente "
            "a su celebración."
        ),
    },
    {
        "article": "1372",
        "section_path": "CC > Libro VII > Fuentes de las Obligaciones > Contratos > Rescisión",
        "content": (
            "Artículo 1372.- La rescisión se declara judicialmente, pero los efectos de la sentencia se "
            "retrotraen al momento de la celebración del contrato.\n"
            "La resolución se invoca judicial o extrajudicialmente. En ambos casos, los efectos de la "
            "sentencia se retrotraen al momento en que se produce la causal que la motiva.\n"
            "Por razón de la resolución, las partes deben restituirse las prestaciones en el estado en que "
            "se encontraran al momento indicado en el párrafo anterior, y si ello no fuera posible deben "
            "reembolsarse en dinero el valor que tenían en dicho momento."
        ),
    },
    # === RESPONSABILIDAD CIVIL EXTRACONTRACTUAL ===
    {
        "article": "1969",
        "section_path": "CC > Libro VII > Fuentes de las Obligaciones > Responsabilidad Extracontractual",
        "content": (
            "Artículo 1969.- Aquel que por dolo o culpa causa un daño a otro está obligado a indemnizarlo. "
            "El descargo por falta de dolo o culpa corresponde a su autor."
        ),
    },
    {
        "article": "1970",
        "section_path": "CC > Libro VII > Fuentes de las Obligaciones > Responsabilidad Extracontractual",
        "content": (
            "Artículo 1970.- Aquel que mediante un bien riesgoso o peligroso, o por el ejercicio de una "
            "actividad riesgosa o peligrosa, causa un daño a otro, está obligado a repararlo."
        ),
    },
    {
        "article": "1985",
        "section_path": "CC > Libro VII > Fuentes de las Obligaciones > Responsabilidad Extracontractual > Contenido de la indemnización",
        "content": (
            "Artículo 1985.- La indemnización comprende las consecuencias que deriven de la acción u omisión "
            "generadora del daño, incluyendo el lucro cesante, el daño a la persona y el daño moral, debiendo "
            "existir una relación de causalidad adecuada entre el hecho y el daño producido. El monto de la "
            "indemnización devenga intereses legales desde la fecha en que se produjo el daño."
        ),
    },
    # === PRESCRIPCIÓN ===
    {
        "article": "2001",
        "section_path": "CC > Libro VIII > Prescripción y Caducidad",
        "content": (
            "Artículo 2001.- Prescriben, salvo disposición diversa de la ley:\n"
            "1. A los diez años, la acción personal, la acción real, la que nace de una ejecutoria y la de nulidad del acto jurídico.\n"
            "2. A los siete años, la acción de daños y perjuicios derivados para las partes de la violación de un acto simulado.\n"
            "3. A los tres años, la acción para el pago de remuneraciones por servicios prestados como consecuencia de vínculo no laboral.\n"
            "4. A los dos años, la acción de anulabilidad, la acción revocatoria, la que proviene de pensión alimenticia, la acción indemnizatoria por responsabilidad extracontractual y la que corresponda contra los representantes de incapaces derivada del ejercicio del cargo."
        ),
    },
]
