"""
Seed: Protección de Datos Personales (Perú).

Núcleo normativo:
    - Ley 29733 (2011) — Ley de Protección de Datos Personales (LPDP).
    - DS 003-2013-JUS — Reglamento de la LPDP.

Cada chunk resume una institución / regla con cita exacta al artículo.
Autoridad: ANPDP — Autoridad Nacional de Protección de Datos Personales,
adscrita al MINJUS. URL institucional: gob.pe/anpd.
"""

DATOS_PERSONALES_ARTICLES = [
    {
        "article": "1",
        "section_path": "LPDP > Disposiciones generales > Art. 1",
        "content": (
            "Artículo 1.- Objeto (Ley 29733).\n"
            "La Ley de Protección de Datos Personales tiene por objeto garantizar el derecho "
            "fundamental a la protección de los datos personales, reconocido en el artículo 2 "
            "numeral 6 de la Constitución Política del Perú, mediante su adecuado tratamiento, "
            "en un marco de respeto de los demás derechos fundamentales que en ella se reconocen."
        ),
    },
    {
        "article": "2",
        "section_path": "LPDP > Disposiciones generales > Art. 2 — Definiciones",
        "content": (
            "Artículo 2.- Definiciones (Ley 29733).\n"
            "Datos personales: toda información sobre una persona natural que la identifica o "
            "la hace identificable a través de medios que pueden ser razonablemente utilizados.\n\n"
            "Datos sensibles: los datos personales constituidos por datos biométricos, los "
            "relacionados con el origen racial y étnico, ingresos económicos, opiniones políticas, "
            "convicciones religiosas, filosóficas o morales, afiliación sindical y los "
            "referidos a la salud, vida sexual u orientación sexual.\n\n"
            "Banco de datos personales: conjunto organizado de datos personales, automatizado o "
            "no, independientemente del soporte, cuyo tratamiento permite el acceso a los datos "
            "según criterios determinados.\n\n"
            "Tratamiento de datos personales: cualquier operación o procedimiento técnico, "
            "automatizado o no, que permita la recopilación, registro, organización, "
            "almacenamiento, conservación, elaboración, modificación, extracción, consulta, "
            "utilización, bloqueo, supresión, comunicación por transferencia o difusión."
        ),
    },
    {
        "article": "3",
        "section_path": "LPDP > Disposiciones generales > Art. 3",
        "content": (
            "Artículo 3.- Ámbito de aplicación (Ley 29733).\n"
            "La ley se aplica al tratamiento de datos personales contenidos o destinados a ser "
            "contenidos en bancos de datos personales de administración pública y de "
            "administración privada, cuyo tratamiento se realice en el territorio nacional.\n\n"
            "También se aplica al tratamiento realizado en el extranjero cuando el responsable "
            "del banco esté domiciliado en el Perú o cuando, sin estarlo, utilice medios "
            "ubicados en el territorio nacional (criterio de medios, similar al RGPD europeo)."
        ),
    },
    {
        "article": "4",
        "section_path": "LPDP > Principios rectores > Art. 4-11",
        "content": (
            "Artículos 4-11.- Principios rectores del tratamiento (Ley 29733).\n"
            "1. Principio de legalidad: el tratamiento debe efectuarse conforme a ley.\n"
            "2. Principio de consentimiento: requiere consentimiento previo, informado, expreso "
            "e inequívoco del titular, salvo las excepciones de los arts. 14 y 17.\n"
            "3. Principio de finalidad: los datos solo se recopilan para finalidades determinadas, "
            "explícitas y lícitas; no se pueden tratar para fines distintos sin consentimiento.\n"
            "4. Principio de proporcionalidad: el tratamiento debe ser adecuado, relevante y no "
            "excesivo respecto de la finalidad.\n"
            "5. Principio de calidad: datos veraces, exactos, completos, necesarios y actualizados.\n"
            "6. Principio de seguridad: medidas técnicas, organizativas y legales para garantizar "
            "su seguridad y evitar su alteración, pérdida o tratamiento no autorizado.\n"
            "7. Principio de disposición de recurso: garantía de tutela administrativa y jurisdiccional.\n"
            "8. Principio de nivel de protección adecuado: las transferencias internacionales "
            "requieren que el país de destino tenga nivel de protección adecuado."
        ),
    },
    {
        "article": "13",
        "section_path": "LPDP > Tratamiento > Art. 13",
        "content": (
            "Artículo 13.- Alcance del consentimiento (Ley 29733).\n"
            "El consentimiento del titular para el tratamiento de sus datos personales debe ser:\n"
            "- LIBRE: sin que medie error, mala fe, violencia o dolo que afecten su voluntad.\n"
            "- PREVIO: anterior al tratamiento.\n"
            "- EXPRESO: manifestado de manera inequívoca.\n"
            "- INFORMADO: precedido de información adecuada sobre la finalidad, identidad del "
            "responsable, destinatarios, derechos del titular y forma de ejercerlos.\n\n"
            "Para datos sensibles, el consentimiento debe ser expreso por ESCRITO mediante "
            "firma manuscrita, electrónica o cualquier otro mecanismo equivalente."
        ),
    },
    {
        "article": "14",
        "section_path": "LPDP > Tratamiento > Art. 14 — Excepciones al consentimiento",
        "content": (
            "Artículo 14.- Limitaciones al consentimiento (Ley 29733).\n"
            "No se requiere consentimiento del titular cuando:\n"
            "1. Los datos figuren en fuentes accesibles para el público.\n"
            "2. Sean recopilados o transferidos para el ejercicio de funciones de las entidades "
            "públicas en el ámbito de sus competencias.\n"
            "3. Se trate de datos relativos a la salud y sean necesarios para circunstancias de "
            "riesgo o motivos de salud pública.\n"
            "4. Sean para fines de investigación científica, histórica o estadística, cuando los "
            "datos no permitan la identificación de las personas.\n"
            "5. Tenga por finalidad la prevención o el diagnóstico médico, la prestación de "
            "asistencia sanitaria o tratamientos médicos.\n"
            "6. Se refieran a las partes de un contrato o precontrato comercial, civil o laboral.\n"
            "7. Se trate de información de creación, modificación o extinción de una relación "
            "jurídica entre el titular y el responsable del tratamiento."
        ),
    },
    {
        "article": "15",
        "section_path": "LPDP > Transferencia internacional > Art. 15",
        "content": (
            "Artículo 15.- Flujo transfronterizo de datos (Ley 29733).\n"
            "El flujo transfronterizo de datos personales requiere que el país receptor cuente "
            "con niveles SUFICIENTES de protección o que el responsable del banco garantice los "
            "estándares mediante cláusulas contractuales, normas corporativas vinculantes o "
            "garantías equivalentes.\n\n"
            "Excepciones (no requieren nivel adecuado):\n"
            "1. Tratados o acuerdos internacionales en los que el Perú sea parte.\n"
            "2. Cooperación judicial internacional.\n"
            "3. Transferencias para el cumplimiento de obligaciones legales del responsable.\n"
            "4. Cuando el titular ha dado su consentimiento expreso e inequívoco para la transferencia.\n"
            "5. Cuando la transferencia es necesaria para la ejecución de un contrato en el que "
            "es parte el titular o para la adopción de medidas precontractuales a su solicitud."
        ),
    },
    {
        "article": "18",
        "section_path": "LPDP > Derechos del titular > Art. 18-25 (ARCO + +)",
        "content": (
            "Artículos 18-25.- Derechos del titular de datos personales (Ley 29733).\n"
            "Derechos ARCO + extensiones:\n"
            "1. ACCESO (art. 19): conocer si sus datos son objeto de tratamiento, sobre la "
            "finalidad, los destinatarios, la fuente y los criterios de tratamiento.\n"
            "2. RECTIFICACIÓN (art. 20): corregir datos inexactos, incompletos o desactualizados.\n"
            "3. CANCELACIÓN / SUPRESIÓN (art. 21): obtener la supresión cuando dejen de ser "
            "necesarios para la finalidad, haya transcurrido el plazo legal de conservación, "
            "o el titular revoque su consentimiento.\n"
            "4. OPOSICIÓN (art. 22): oponerse al tratamiento por motivos legítimos relativos a "
            "su situación particular; aplica especialmente a marketing directo.\n"
            "5. Derecho a NO ser sometido a decisiones que produzcan efectos jurídicos basadas "
            "exclusivamente en tratamiento automatizado (art. 23) — análogo al art. 22 del RGPD.\n"
            "6. Derecho a la TUTELA: acudir a la ANPDP en caso de incumplimiento.\n\n"
            "Plazo de respuesta del responsable: 20 días hábiles para acceso; 10 días hábiles "
            "para rectificación, cancelación y oposición."
        ),
    },
    {
        "article": "26",
        "section_path": "LPDP > Datos del menor > Art. 14 reglamento",
        "content": (
            "Datos personales de menores de edad (Ley 29733 + DS 003-2013-JUS).\n"
            "El tratamiento de datos personales de menores requiere el consentimiento de los "
            "padres o representantes legales, salvo en supuestos previstos por ley. Para "
            "adolescentes a partir de los 14 años, se admite consentimiento propio para "
            "actividades que la ley les autorice expresamente.\n\n"
            "Se prohíbe la recopilación de datos personales de niños sin el consentimiento "
            "expreso del padre o tutor, especialmente en plataformas digitales."
        ),
    },
    {
        "article": "28",
        "section_path": "LPDP > Obligaciones del responsable > Art. 28",
        "content": (
            "Artículo 28.- Obligaciones del titular del banco de datos personales o "
            "responsable del tratamiento (Ley 29733).\n"
            "1. Tratar los datos personales con respeto absoluto a los principios y derechos.\n"
            "2. Mantener la confidencialidad de los datos (inclusive luego de finalizar el "
            "tratamiento — deber de secreto perpetuo).\n"
            "3. Establecer mecanismos para el ejercicio de derechos ARCO.\n"
            "4. Adoptar medidas técnicas y organizativas de seguridad (Directiva 01-2020-JUS/DGTAIPD).\n"
            "5. INSCRIBIR los bancos de datos personales ante la ANPDP en el Registro Nacional "
            "de Protección de Datos Personales — salvo bancos de personas naturales para uso "
            "personal o doméstico.\n"
            "6. Comunicar al titular cuando se realicen cambios sustanciales en la política de "
            "privacidad o en las finalidades del tratamiento."
        ),
    },
    {
        "article": "29",
        "section_path": "LPDP > Seguridad > Art. 29 + Directiva 01-2020",
        "content": (
            "Artículo 29.- Seguridad del tratamiento (Ley 29733).\n"
            "El responsable adopta las medidas técnicas, organizativas y legales necesarias para "
            "garantizar la seguridad de los datos personales, conforme a su naturaleza, "
            "ámbito y categoría.\n\n"
            "La Directiva 01-2020-JUS/DGTAIPD establece estándares mínimos según el nivel de "
            "riesgo:\n"
            "- Nivel BÁSICO: controles de acceso, registros de auditoría, capacitación, "
            "política de seguridad documentada.\n"
            "- Nivel INTERMEDIO: cifrado en tránsito, copias de respaldo, pruebas de "
            "vulnerabilidad anuales.\n"
            "- Nivel AVANZADO: cifrado en reposo, segmentación de redes, pruebas de "
            "penetración, doble factor de autenticación, gestión de incidentes formal.\n\n"
            "Notificación de incidentes: el responsable debe comunicar a la ANPDP y a los "
            "afectados cualquier incidente que afecte la confidencialidad o integridad de los "
            "datos."
        ),
    },
    {
        "article": "32",
        "section_path": "LPDP > Autoridad > Art. 32-39",
        "content": (
            "Artículos 32-39.- Autoridad Nacional de Protección de Datos Personales — ANPDP "
            "(Ley 29733).\n"
            "La ANPDP es la autoridad rectora del sistema, adscrita al Ministerio de Justicia y "
            "Derechos Humanos. Funciones:\n"
            "1. Llevar el Registro Nacional de Protección de Datos Personales.\n"
            "2. Atender denuncias, tramitar procedimientos sancionadores.\n"
            "3. Emitir opiniones y recomendaciones.\n"
            "4. Aprobar códigos de conducta.\n"
            "5. Cooperar con autoridades extranjeras de protección de datos.\n\n"
            "Procedimientos ante ANPDP:\n"
            "a) Procedimiento de tutela de derechos: a solicitud del titular cuando un "
            "responsable no atendió su requerimiento ARCO en plazo legal.\n"
            "b) Procedimiento administrativo sancionador (PAS): por infracciones a la LPDP."
        ),
    },
    {
        "article": "39",
        "section_path": "LPDP > Sanciones > Art. 39",
        "content": (
            "Artículo 39.- Infracciones y sanciones (Ley 29733).\n"
            "Clasificación de infracciones:\n"
            "- LEVES: tratamiento sin cumplir formalidades no esenciales, falta de información "
            "al titular sobre cambios menores. Multa: 0.5 a 5 UIT.\n"
            "- GRAVES: tratamiento sin consentimiento cuando éste es exigible, incumplimiento "
            "de derechos ARCO, transferencia internacional sin garantías, omisión de inscripción "
            "del banco de datos. Multa: 5 a 50 UIT.\n"
            "- MUY GRAVES: tratamiento de datos sensibles sin consentimiento expreso por "
            "escrito, comercialización ilícita de datos, incumplimientos reiterados de medidas "
            "de seguridad, obstrucción al ejercicio del titular. Multa: 50 a 100 UIT.\n\n"
            "Las sanciones se aplican sin perjuicio de la responsabilidad civil y penal "
            "(delito de violación de la intimidad — arts. 154-157 del Código Penal)."
        ),
    },
    {
        "article": "REGL-25",
        "section_path": "DS 003-2013-JUS > Reglamento > Cláusulas modelo",
        "content": (
            "Reglamento de la LPDP (DS 003-2013-JUS) — Cláusulas y políticas de privacidad.\n"
            "Toda política de privacidad debe contener como mínimo:\n"
            "1. Identidad y datos de contacto del responsable del banco.\n"
            "2. Finalidad o finalidades específicas del tratamiento.\n"
            "3. Categorías de destinatarios o cesionarios.\n"
            "4. Existencia de transferencias internacionales y, si aplica, garantías.\n"
            "5. Existencia del banco de datos y su inscripción ante la ANPDP.\n"
            "6. Derechos del titular y forma de ejercerlos (canal, plazo, gratuidad).\n"
            "7. Consecuencias de proporcionar o no proporcionar los datos.\n"
            "8. Plazo de conservación.\n\n"
            "La política debe estar redactada en lenguaje claro, accesible y disponible "
            "antes del momento del tratamiento."
        ),
    },
    {
        "article": "REGL-PROC",
        "section_path": "DS 003-2013-JUS > Procedimiento de tutela",
        "content": (
            "Procedimiento de tutela ante la ANPDP (DS 003-2013-JUS).\n"
            "Cuando un responsable no atiende un derecho ARCO en el plazo legal, el titular "
            "puede presentar reclamo ante la ANPDP. Pasos:\n"
            "1. Solicitud inicial al responsable (formal, por canal idóneo). El responsable "
            "debe responder dentro del plazo (20 días hábiles para acceso; 10 hábiles para "
            "rectificación/cancelación/oposición).\n"
            "2. Si no hay respuesta o ésta es insatisfactoria, presentar reclamo ante la ANPDP "
            "dentro de los 15 días hábiles siguientes al vencimiento del plazo.\n"
            "3. La ANPDP corre traslado al responsable por 15 días hábiles.\n"
            "4. Se emite resolución en 30 días hábiles desde respuesta. La resolución es "
            "apelable ante el Tribunal de la ANPDP (15 días hábiles).\n"
            "5. Agotada la vía administrativa, procede acción contencioso-administrativa o "
            "habeas data según corresponda."
        ),
    },
]
