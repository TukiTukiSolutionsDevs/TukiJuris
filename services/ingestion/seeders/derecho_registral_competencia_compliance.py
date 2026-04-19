"""
Seed: Registral (SUNARP), Competencia/PI (INDECOPI), Compliance.
Las 3 áreas que tenían 0 chunks.
"""

REGISTRAL_ARTICLES = [
    {
        "article": "REG-1",
        "section_path": "Ley 26366 > SINARP > Creación",
        "content": (
            "Ley 26366 — Ley de Creación del Sistema Nacional de los Registros Públicos y de la SUNARP.\n"
            "El Sistema Nacional de los Registros Públicos (SINARP) tiene por objeto dictar las políticas "
            "técnico-administrativas de los Registros Públicos. La SUNARP es el ente rector del SINARP.\n"
            "Los Registros que integran el SINARP son:\n"
            "- Registro de Propiedad Inmueble\n"
            "- Registro de Personas Jurídicas\n"
            "- Registro de Personas Naturales\n"
            "- Registro de Bienes Muebles"
        ),
    },
    {
        "article": "REG-2012",
        "section_path": "Reglamento General > Principios registrales",
        "content": (
            "Reglamento General de los Registros Públicos (Res. N° 126-2012-SUNARP-SN).\n"
            "Principios registrales fundamentales:\n"
            "1. Principio de Legalidad: El Registrador califica la legalidad de los títulos.\n"
            "2. Principio de Rogación: La inscripción se solicita por el interesado, no de oficio.\n"
            "3. Principio de Especialidad: Cada bien o persona tiene una partida registral propia.\n"
            "4. Principio de Tracto Sucesivo: Las inscripciones deben seguir un orden correlativo.\n"
            "5. Principio de Legitimación: Se presume cierto el contenido de las inscripciones.\n"
            "6. Principio de Fe Pública Registral: El tercero que adquiere de buena fe y a título oneroso, "
            "confiando en lo que dice el registro, mantiene su adquisición aunque luego se anule el derecho del transferente.\n"
            "7. Principio de Prioridad: El título que ingresa primero al registro tiene prioridad sobre los posteriores.\n"
            "8. Principio de Publicidad: Toda persona tiene derecho a conocer el contenido de las inscripciones."
        ),
    },
    {
        "article": "REG-PLAZOS",
        "section_path": "Reglamento General > Procedimiento registral > Plazos",
        "content": (
            "Procedimiento registral — plazos y trámites principales:\n"
            "- Plazo de calificación: 7 días hábiles para títulos en general.\n"
            "- Plazo de vigencia del asiento de presentación: 35 días hábiles (prorrogable 25 más).\n"
            "- Recurso de apelación ante el Tribunal Registral: 15 días hábiles desde la notificación de la observación o tacha.\n"
            "- Tacha sustantiva: cuando el título adolece de defecto insubsanable.\n"
            "- Observación: cuando el título tiene defectos subsanables que impiden la inscripción.\n"
            "- Liquidación: cuando se requiere el pago de derechos registrales adicionales.\n"
            "- Derechos registrales: varían según el acto y el valor del bien. Consultar TUPA de SUNARP."
        ),
    },
    {
        "article": "REG-INMATR",
        "section_path": "Reglamento > Inscripción de propiedad > Inmatriculación",
        "content": (
            "Inmatriculación de predios — Primera inscripción de dominio.\n"
            "Para inscribir un predio por primera vez en el Registro de Propiedad Inmueble se requiere:\n"
            "1. Título de propiedad (escritura pública, resolución judicial, resolución administrativa).\n"
            "2. Plano perimétrico y de ubicación visados por la autoridad competente.\n"
            "3. Certificado catastral emitido por la municipalidad o COFOPRI.\n"
            "4. Declaración jurada de no existencia de oposición.\n"
            "5. Publicación en el Diario Oficial El Peruano (para predios urbanos) o diario de mayor circulación.\n\n"
            "Para la prescripción adquisitiva de dominio notarial o judicial (Art. 950 CC), se requiere posesión "
            "continua, pacífica y pública como propietario durante 10 años (5 años con justo título y buena fe)."
        ),
    },
]

COMPETENCIA_ARTICLES = [
    {
        "article": "INDECOPI-CDC",
        "section_path": "Código de Protección y Defensa del Consumidor > Ley 29571",
        "content": (
            "Código de Protección y Defensa del Consumidor (Ley 29571).\n"
            "Artículo 1.- Derechos de los consumidores:\n"
            "a) Derecho a una protección eficaz respecto de los productos y servicios que, en condiciones normales, "
            "representen riesgo o peligro para la vida, salud e integridad física.\n"
            "b) Derecho a acceder a información oportuna, suficiente, veraz y fácilmente accesible, relevante para "
            "tomar una decisión o realizar una elección de consumo que se ajuste a sus intereses.\n"
            "c) Derecho a la protección de sus intereses económicos y en particular contra las cláusulas abusivas, "
            "métodos comerciales coercitivos, cobros indebidos y prácticas análogas.\n"
            "d) Derecho a un trato justo y equitativo en toda transacción comercial.\n"
            "e) Derecho a la reparación o reposición del producto, a una nueva ejecución del servicio, o a la "
            "devolución de la cantidad pagada."
        ),
    },
    {
        "article": "INDECOPI-MARCAS",
        "section_path": "DL 1075 > Propiedad Industrial > Marcas",
        "content": (
            "Registro de marcas en el Perú — DL 1075 (Disposiciones Complementarias a la Decisión 486 CAN).\n"
            "Requisitos para registrar una marca:\n"
            "1. Solicitud ante la Dirección de Signos Distintivos de INDECOPI.\n"
            "2. Descripción clara de la marca (denominativa, figurativa, mixta, tridimensional, sonora).\n"
            "3. Indicación de los productos o servicios según la Clasificación de Niza.\n"
            "4. Pago de la tasa: aproximadamente S/ 534.99 (2024).\n"
            "5. Plazo de trámite: aproximadamente 90 a 120 días hábiles.\n"
            "6. Vigencia: 10 años renovables.\n\n"
            "Causales de denegatoria:\n"
            "- Signos genéricos, descriptivos o de uso común.\n"
            "- Signos confundibles con marcas ya registradas.\n"
            "- Signos que vulneren derechos de terceros.\n"
            "- Signos contrarios a la moral o al orden público."
        ),
    },
    {
        "article": "INDECOPI-RECLAMO",
        "section_path": "Ley 29571 > Procedimientos > Reclamo y denuncia",
        "content": (
            "Procedimientos de protección al consumidor ante INDECOPI:\n\n"
            "1. LIBRO DE RECLAMACIONES: Todo proveedor debe contar con un Libro de Reclamaciones (físico o virtual). "
            "Plazo de respuesta: 30 días calendario.\n\n"
            "2. RECLAMO ante INDECOPI: Se interpone ante el Servicio de Atención al Ciudadano (SAC). "
            "Es gratuito y se resuelve en 30 días hábiles. No tiene carácter sancionador.\n\n"
            "3. DENUNCIA administrativa: Se interpone ante la Comisión de Protección al Consumidor o el "
            "Órgano Resolutivo de Procedimientos Sumarísimos (OPS). Tiene carácter sancionador. "
            "Tasa: desde S/ 36.00 (OPS) hasta S/ 72.00 (Comisión).\n"
            "Multas posibles: hasta 450 UIT para el proveedor infractor.\n\n"
            "4. ARBITRAJE DE CONSUMO: Vía alternativa gratuita y voluntaria para resolver controversias."
        ),
    },
    {
        "article": "INDECOPI-COMPET",
        "section_path": "DL 1034 > Libre Competencia",
        "content": (
            "Ley de Represión de Conductas Anticompetitivas (DL 1034).\n"
            "Conductas anticompetitivas prohibidas:\n"
            "1. Abuso de posición de dominio: cuando una empresa con posición dominante explota esa posición.\n"
            "2. Prácticas colusorias horizontales (carteles): acuerdos entre competidores para fijar precios, "
            "repartirse mercados, limitar producción.\n"
            "3. Prácticas colusorias verticales: acuerdos entre empresas de distintos niveles de la cadena "
            "productiva que restringen la competencia.\n\n"
            "La Comisión de Defensa de la Libre Competencia de INDECOPI es la autoridad competente.\n"
            "Multas: hasta 12% de los ingresos brutos del infractor en el año anterior."
        ),
    },
]

COMPLIANCE_ARTICLES = [
    {
        "article": "COMP-29733",
        "section_path": "Ley 29733 > Protección de Datos Personales",
        "content": (
            "Ley 29733 — Ley de Protección de Datos Personales (modificada por DS 016-2024-JUS).\n"
            "Principios rectores del tratamiento de datos personales:\n"
            "1. Principio de consentimiento: se requiere consentimiento libre, previo, expreso, informado e inequívoco.\n"
            "2. Principio de finalidad: los datos deben recopilarse para una finalidad determinada, explícita y lícita.\n"
            "3. Principio de proporcionalidad: solo se deben tratar los datos adecuados, relevantes y no excesivos.\n"
            "4. Principio de calidad: los datos deben ser veraces, exactos y actualizados.\n"
            "5. Principio de seguridad: se deben adoptar medidas técnicas y organizativas para garantizar la seguridad.\n\n"
            "Derechos ARCO del titular:\n"
            "- Acceso: derecho a conocer qué datos se tienen.\n"
            "- Rectificación: derecho a corregir datos inexactos.\n"
            "- Cancelación: derecho a solicitar la eliminación.\n"
            "- Oposición: derecho a oponerse al tratamiento.\n\n"
            "Autoridad: Autoridad Nacional de Protección de Datos Personales (ANPDP) del MINJUSDH.\n"
            "Multas: hasta 100 UIT por infracciones muy graves."
        ),
    },
    {
        "article": "COMP-30424",
        "section_path": "Ley 30424 > Responsabilidad administrativa de PJ",
        "content": (
            "Ley 30424 — Responsabilidad administrativa de las personas jurídicas.\n"
            "Las personas jurídicas pueden ser responsables administrativamente por los delitos de:\n"
            "- Cohecho activo transnacional, genérico y específico.\n"
            "- Lavado de activos.\n"
            "- Financiamiento del terrorismo.\n"
            "- Colusión.\n"
            "- Tráfico de influencias.\n\n"
            "MODELO DE PREVENCIÓN (Compliance Program):\n"
            "La persona jurídica está exenta de responsabilidad si cuenta con un modelo de prevención "
            "implementado antes de la comisión del delito, que debe incluir:\n"
            "1. Persona u órgano encargado de la prevención (Oficial de Cumplimiento).\n"
            "2. Identificación, evaluación y mitigación de riesgos.\n"
            "3. Procedimientos de denuncia interna.\n"
            "4. Difusión y capacitación del modelo.\n"
            "5. Evaluación y monitoreo continuo del modelo.\n\n"
            "La SMV certifica la idoneidad del modelo de prevención.\n"
            "Sanciones: multa de 2 a 10,000 UIT, inhabilitación, cancelación de licencias."
        ),
    },
    {
        "article": "COMP-ANTILAVADO",
        "section_path": "DL 1106 > Lavado de activos > Obligaciones",
        "content": (
            "Sistema de prevención del lavado de activos y financiamiento del terrorismo.\n"
            "Sujetos obligados (Ley 27693 y normas SBS):\n"
            "- Empresas del sistema financiero.\n"
            "- Empresas de seguros y AFP.\n"
            "- Notarios públicos.\n"
            "- Agentes inmobiliarios.\n"
            "- Casas de cambio.\n"
            "- Empresas de transferencia de fondos.\n"
            "- Abogados y contadores (en determinadas operaciones).\n\n"
            "Obligaciones principales:\n"
            "1. Designar un Oficial de Cumplimiento.\n"
            "2. Implementar un sistema de prevención LAFT.\n"
            "3. Conocer al cliente (KYC — Know Your Customer).\n"
            "4. Reportar Operaciones Sospechosas (ROS) a la UIF-Perú.\n"
            "5. Reportar Operaciones superiores a US$ 10,000 o equivalente en soles.\n"
            "6. Conservar documentación por 10 años.\n\n"
            "La UIF-Perú (Unidad de Inteligencia Financiera) es la autoridad central."
        ),
    },
    {
        "article": "COMP-ANTICORR",
        "section_path": "DL 1385 > Integridad > Sector público y privado",
        "content": (
            "Marco normativo anticorrupción en el Perú:\n"
            "1. DL 1385 — Ley que sanciona la corrupción en el sector privado.\n"
            "2. Ley 30424 — Responsabilidad administrativa de personas jurídicas.\n"
            "3. Código Penal — Delitos contra la administración pública (Arts. 382-401).\n\n"
            "Medidas de integridad obligatorias para empresas contratistas del Estado:\n"
            "- Código de ética.\n"
            "- Programa anticorrupción.\n"
            "- Canal de denuncias.\n"
            "- Due diligence de terceros.\n"
            "- Capacitación a empleados.\n\n"
            "La Secretaría de Integridad Pública (SIP) de la PCM coordina la política anticorrupción."
        ),
    },
]
