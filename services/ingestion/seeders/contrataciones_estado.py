"""
Seed: Contrataciones del Estado (Perú).

Núcleo normativo:
    - Ley 32069 (2024) — Ley General de Contrataciones Públicas (LGCP), vigente
      desde el 22 de abril de 2025. Deroga la Ley 30225.
    - DS 009-2025-EF — Reglamento de la Ley 32069 [verify final number].
    - Ley 30225 (2014) — Ley de Contrataciones del Estado (derogada — útil para
      procesos en curso y para aquellos cuya convocatoria fue anterior).

Autoridad: OECE (antes OSCE) y PERÚ COMPRAS. Tribunal de Contrataciones del
Estado (TCE) como instancia colegiada para impugnaciones y sanciones.

Cada chunk resume institución / regla con cita exacta. La nueva LGCP busca:
agilizar procesos, reforzar gobernanza, simplificar tipos de procedimiento e
integrar plataforma digital (SEACE 3.0).
"""

CONTRATACIONES_ESTADO_ARTICLES = [
    # ── Disposiciones generales nueva LCE ────────────────────────────────
    {
        "article": "1-LGCP",
        "section_path": "Ley 32069 > Título I > Art. 1-2",
        "content": (
            "Artículos 1-2.- Objeto y finalidad (Ley 32069 — Ley General de Contrataciones Públicas).\n"
            "La ley establece principios, normas y procedimientos que deben observar las "
            "Entidades Contratantes del Estado en sus contrataciones, con la finalidad de "
            "satisfacer las necesidades públicas, en condiciones de calidad y al menor costo "
            "para la Nación, con plena observancia del régimen de gobernanza, transparencia e "
            "integridad pública.\n\n"
            "VIGENCIA: 22 de abril de 2025 — fecha desde la cual rige la Ley 32069 y queda "
            "derogada la Ley 30225. Los procedimientos convocados con anterioridad continúan "
            "rigiéndose por la norma vigente al momento de la convocatoria."
        ),
    },
    {
        "article": "2-LGCP",
        "section_path": "Ley 32069 > Título I > Principios",
        "content": (
            "Artículo 2.- Principios que rigen la contratación pública (Ley 32069).\n"
            "1. Libertad de concurrencia: las Entidades garantizan acceso libre y la "
            "participación efectiva del mayor número de competidores.\n"
            "2. Igualdad de trato: no discriminación entre proveedores nacionales e "
            "internacionales que cumplan los requisitos.\n"
            "3. Transparencia: información clara, oportuna y accesible.\n"
            "4. Publicidad: difusión adecuada en plataforma digital.\n"
            "5. Competencia: regla orientadora de los procedimientos de selección.\n"
            "6. Eficacia y eficiencia: cumplimiento del fin público al menor costo posible.\n"
            "7. Vigencia tecnológica: condiciones técnicas vigentes al momento de la "
            "contratación.\n"
            "8. Sostenibilidad ambiental y social: consideración de impactos.\n"
            "9. Equidad e integridad: actuación honesta de todos los actores.\n"
            "10. Estandarización y simplificación de procedimientos."
        ),
    },
    {
        "article": "5-LGCP",
        "section_path": "Ley 32069 > Título I > Ámbito",
        "content": (
            "Artículo 5.- Ámbito de aplicación (Ley 32069).\n"
            "Se aplica a las contrataciones de bienes, servicios, consultorías y obras que "
            "realicen las Entidades Contratantes con cargo a fondos públicos.\n\n"
            "Entidades comprendidas: el Gobierno Nacional, gobiernos regionales y locales, "
            "Poder Legislativo y Judicial, organismos constitucionales autónomos, "
            "universidades públicas, FONAFE y sus empresas, Petroperú, EsSalud, entre otras.\n\n"
            "EXCLUSIONES: contrataciones bajo regímenes especiales (PMI Reconstrucción, "
            "APP - Ley 30167, OxI - obras por impuestos, contratos internacionales en virtud "
            "de tratados, contrataciones intergubernamentales con organismos internacionales).\n\n"
            "Umbral de inaplicación: las contrataciones por monto IGUAL O MENOR a 8 UIT NO se "
            "sujetan a la LGCP — son contrataciones directas no sujetas a procedimiento de "
            "selección."
        ),
    },
    # ── Procedimientos de selección ──────────────────────────────────────
    {
        "article": "Procedimientos",
        "section_path": "Ley 32069 > Procedimientos de selección",
        "content": (
            "Procedimientos de selección (Ley 32069).\n"
            "La nueva LGCP simplifica los tipos a:\n"
            "1. LICITACIÓN PÚBLICA (LP): bienes, servicios u obras de mayor monto, con concurrencia "
            "amplia.\n"
            "2. CONCURSO PÚBLICO (CP): para servicios de consultoría y consultoría de obra.\n"
            "3. ADJUDICACIÓN SIMPLIFICADA (AS): para contrataciones de monto intermedio.\n"
            "4. SELECCIÓN DE CONSULTORES INDIVIDUALES (SCI): consultorías especializadas con "
            "personalidad profesional.\n"
            "5. SUBASTA INVERSA ELECTRÓNICA (SIE): para bienes/servicios con ficha técnica.\n"
            "6. COMPARACIÓN DE PRECIOS: para bienes de fácil obtención.\n"
            "7. CONTRATACIÓN DIRECTA: supuestos excepcionales (urgencia, situación de emergencia, "
            "exclusividad técnica, contratos secretos, entre otros estrictamente tasados).\n\n"
            "Los topes/umbrales se actualizan anualmente por DS del MEF a partir de la UIT."
        ),
    },
    {
        "article": "Etapas",
        "section_path": "Ley 32069 > Etapas del procedimiento",
        "content": (
            "Etapas del procedimiento de selección (Ley 32069 + Reglamento).\n"
            "1. ACTOS PREPARATORIOS: estudio de mercado, requerimiento técnico mínimo, "
            "valor referencial, expediente de contratación, aprobación interna.\n"
            "2. CONVOCATORIA: publicación en SEACE 3.0.\n"
            "3. REGISTRO DE PARTICIPANTES.\n"
            "4. FORMULACIÓN DE CONSULTAS Y OBSERVACIONES por participantes.\n"
            "5. INTEGRACIÓN DE BASES — incorporación de consultas, observaciones y absoluciones.\n"
            "6. PRESENTACIÓN DE OFERTAS — vía electrónica salvo excepciones.\n"
            "7. EVALUACIÓN, CALIFICACIÓN Y OTORGAMIENTO DE LA BUENA PRO.\n"
            "8. CONSENTIMIENTO de la buena pro.\n"
            "9. PERFECCIONAMIENTO DEL CONTRATO."
        ),
    },
    # ── Impedimentos para contratar ──────────────────────────────────────
    {
        "article": "Impedimentos",
        "section_path": "Ley 32069 > Impedimentos para contratar",
        "content": (
            "Impedimentos para ser participante, postor, contratista o subcontratista (Ley 32069).\n"
            "1. El Presidente y vicepresidentes, congresistas, ministros, viceministros, jueces "
            "y fiscales supremos, magistrados del TC, gobernadores regionales y alcaldes "
            "durante su mandato y hasta 12 meses después.\n"
            "2. Los funcionarios y servidores públicos con poder de decisión en la entidad "
            "contratante.\n"
            "3. Los cónyuges, convivientes y parientes hasta el cuarto grado de consanguinidad y "
            "segundo de afinidad de los anteriores.\n"
            "4. Las personas inhabilitadas o suspendidas por el Tribunal de Contrataciones del "
            "Estado.\n"
            "5. Las personas naturales o jurídicas que tengan procesos pendientes ante el "
            "Tribunal por incumplimiento contractual u otras infracciones tasadas.\n"
            "6. Las empresas con antecedentes registrados en el Registro Único de Infractores "
            "del Estado.\n"
            "7. Las personas naturales o jurídicas con responsabilidad declarada por delitos de "
            "corrupción, colusión, cohecho u otros conexos."
        ),
    },
    # ── Tribunal de Contrataciones ───────────────────────────────────────
    {
        "article": "TCE",
        "section_path": "Ley 32069 > Tribunal de Contrataciones del Estado",
        "content": (
            "Tribunal de Contrataciones del Estado (TCE) — Ley 32069.\n"
            "Órgano resolutivo del OECE. Funciones:\n"
            "1. Resolver controversias entre Entidades y participantes/postores/contratistas en "
            "la etapa de selección (recursos de apelación).\n"
            "2. Aplicar sanciones administrativas a proveedores por incumplimiento de las "
            "obligaciones derivadas del contrato o de su participación en procedimientos.\n"
            "3. Resolver recursos de reconsideración respecto de sus propias resoluciones.\n\n"
            "Sanciones: multa, inhabilitación temporal (3 meses a 36 meses) o inhabilitación "
            "definitiva. Las inhabilitaciones se inscriben en el Registro Nacional de "
            "Proveedores (RNP) y en el Registro Único de Infractores.\n\n"
            "Plazos: el TCE resuelve los recursos de apelación dentro del plazo legal "
            "(usualmente 30 días hábiles). Las resoluciones agotan la vía administrativa y "
            "habilitan el contencioso administrativo."
        ),
    },
    {
        "article": "Recurso-Apelacion",
        "section_path": "Ley 32069 > Recurso de apelación",
        "content": (
            "Recurso de apelación en contrataciones públicas (Ley 32069).\n"
            "Procedente contra:\n"
            "1. Actos administrativos emitidos durante la etapa del procedimiento de selección "
            "hasta antes del perfeccionamiento del contrato.\n"
            "2. Resoluciones que declaran la nulidad o la cancelación del procedimiento.\n"
            "3. Resoluciones que declaran improcedente, inadmisible o ineficaz la oferta del impugnante.\n\n"
            "Plazo: 8 días hábiles desde la notificación del acto impugnado o desde tomar "
            "conocimiento (en obras: 10 días hábiles).\n\n"
            "Conoce: el Tribunal de Contrataciones del Estado (TCE) cuando el valor referencial "
            "supere las 50 UIT; la propia Entidad cuando sea menor (recurso administrativo de "
            "apelación ante el Titular). En SIE conoce siempre el TCE.\n\n"
            "Suspensión: la presentación del recurso suspende automáticamente el procedimiento, "
            "salvo en los supuestos excepcionales previstos."
        ),
    },
    # ── Ejecución contractual ────────────────────────────────────────────
    {
        "article": "Ejecucion",
        "section_path": "Ley 32069 > Ejecución contractual",
        "content": (
            "Ejecución contractual (Ley 32069).\n"
            "Garantías exigibles al contratista:\n"
            "1. Garantía de fiel cumplimiento: 10% del monto contractual.\n"
            "2. Garantía por adelantos (si los hay): 100% del monto del adelanto.\n"
            "3. Garantía por adicionales de obra que excedan el 50% del monto original (cuando "
            "corresponda).\n\n"
            "Penalidad por mora: aplicación automática conforme a fórmula prevista en bases, "
            "hasta un máximo del 10% del monto del contrato. Excedido este tope, la Entidad "
            "puede resolver el contrato.\n\n"
            "Modificaciones contractuales: adicionales hasta el 25% del monto del contrato "
            "original sin requerir nueva autorización; entre 25% y 50% requieren autorización "
            "previa del Titular de la Entidad; mayores al 50% requieren autorización de la "
            "Contraloría General de la República en obras."
        ),
    },
    {
        "article": "Arbitraje",
        "section_path": "Ley 32069 > Solución de controversias en ejecución",
        "content": (
            "Solución de controversias en ejecución contractual (Ley 32069).\n"
            "Mecanismos:\n"
            "1. Trato directo o conciliación.\n"
            "2. Junta de Resolución de Disputas (JRD) — obligatoria en contratos de obra de "
            "monto superior al umbral reglamentario (S/ 40 millones aprox.) — emite "
            "decisiones vinculantes que pueden ser revisadas posteriormente en arbitraje.\n"
            "3. Arbitraje institucional — administrado por el OECE u otra institución arbitral "
            "autorizada. Las controversias en ejecución contractual se someten a arbitraje "
            "OBLIGATORIO, salvo enriquecimiento sin causa y otros supuestos no patrimoniales.\n\n"
            "Plazo para solicitar arbitraje: 30 días hábiles desde el acto que motiva la "
            "controversia o desde la conclusión del trato directo/conciliación.\n\n"
            "Las normas aplicables a este arbitraje se complementan con el DL 1071 — Ley de "
            "Arbitraje. El laudo es definitivo y solo admite recurso de anulación ante el "
            "Poder Judicial."
        ),
    },
    # ── Tipos contractuales ──────────────────────────────────────────────
    {
        "article": "Tipos",
        "section_path": "Ley 32069 > Tipos de contrato",
        "content": (
            "Tipos de contrato en contrataciones públicas (Ley 32069).\n"
            "1. Contrato de bienes: suministro o entrega de un objeto material.\n"
            "2. Contrato de servicios: prestación de actividades intelectuales o materiales sin "
            "obra física resultante.\n"
            "3. Contrato de consultoría: servicios profesionales especializados intelectuales (de "
            "obra o no de obra).\n"
            "4. Contrato de obra: ejecución, ampliación, mejora, rehabilitación de una obra "
            "(infraestructura).\n\n"
            "Modalidades especiales:\n"
            "- Llave en mano (turn-key): el contratista entrega la obra terminada y operativa.\n"
            "- Concurso oferta: bases y proyecto definitivo se desarrollan en paralelo a la oferta.\n"
            "- EPC (Ingeniería, Procura y Construcción): integra diseño detallado, suministro y construcción.\n"
            "- BIM (Building Information Modeling): obligatorio para obras de gran envergadura "
            "según gradualidad establecida por MEF."
        ),
    },
    # ── PERÚ COMPRAS y catálogos ────────────────────────────────────────
    {
        "article": "PeruCompras",
        "section_path": "Ley 32069 > Central de Compras",
        "content": (
            "PERÚ COMPRAS — Central de Compras Públicas (Ley 32069).\n"
            "Funciones:\n"
            "1. Administrar y gestionar Catálogos Electrónicos de Acuerdo Marco, los cuales "
            "definen las condiciones técnicas y económicas mediante las cuales las Entidades "
            "adquieren bienes/servicios estandarizados (sin necesidad de procedimiento adicional).\n"
            "2. Operar la Subasta Inversa Electrónica.\n"
            "3. Realizar Compras Corporativas (compras agregadas de varias entidades).\n"
            "4. Brindar capacitación y asistencia técnica.\n\n"
            "Las Entidades NO pueden adquirir por otro procedimiento aquellos bienes/servicios "
            "que se encuentren disponibles en Catálogo Electrónico, salvo que demuestren "
            "técnica o económicamente mejor oportunidad. La inobservancia genera responsabilidad."
        ),
    },
    # ── RNP ──────────────────────────────────────────────────────────────
    {
        "article": "RNP",
        "section_path": "Ley 32069 > Registro Nacional de Proveedores",
        "content": (
            "Registro Nacional de Proveedores (RNP) — Ley 32069.\n"
            "Administrado por el OECE. Inscripción OBLIGATORIA y previa para todo proveedor que "
            "participe en procedimientos de selección y/o contrate con el Estado.\n\n"
            "Categorías del RNP:\n"
            "1. Bienes.\n"
            "2. Servicios.\n"
            "3. Consultoría de obras (con especialidades).\n"
            "4. Ejecución de obras (con categorías por monto).\n\n"
            "Requisitos generales: RUC activo, no estar inhabilitado, presentar declaración "
            "jurada de cumplimiento de la LGCP, pago de derechos.\n\n"
            "Vigencia: la inscripción rige por 1 año renovable. La inhabilitación del proveedor "
            "se anota en el RNP y se publica en SEACE 3.0."
        ),
    },
    # ── Integridad y prevención de corrupción ────────────────────────────
    {
        "article": "Integridad",
        "section_path": "Ley 32069 > Integridad en contrataciones",
        "content": (
            "Integridad y prevención de corrupción en contrataciones (Ley 32069).\n"
            "Obligaciones:\n"
            "1. Declaración jurada de NO encontrarse incurso en supuestos de impedimento.\n"
            "2. Declaración jurada de aceptación de los lineamientos de integridad pública.\n"
            "3. Programa de cumplimiento normativo (compliance) para personas jurídicas — "
            "vinculado a la Ley 30424 (responsabilidad administrativa de personas jurídicas).\n"
            "4. Lineamiento de gestión de conflicto de intereses, especialmente en funcionarios "
            "que participan en procedimientos.\n\n"
            "Causales de nulidad del contrato:\n"
            "- Vicios insubsanables en convocatoria/selección.\n"
            "- Trasgresión a normas imperativas y al orden público.\n"
            "- Conducta de cohecho/colusión declarada por el Ministerio Público o sentencia firme.\n"
            "- Declaración de responsabilidad penal del representante legal del contratista "
            "por delitos de corrupción cometidos en el marco de la contratación.\n\n"
            "La nulidad acarrea inhabilitación para nuevos procedimientos y reparación al Estado."
        ),
    },
    # ── Transición ───────────────────────────────────────────────────────
    {
        "article": "Transicion",
        "section_path": "Ley 32069 > Disposiciones complementarias",
        "content": (
            "Disposiciones complementarias transitorias (Ley 32069).\n"
            "1. Los procedimientos de selección convocados con anterioridad al 22-abr-2025 se "
            "siguen rigiendo por la Ley 30225 y su reglamento DS 344-2018-EF.\n"
            "2. Los contratos perfeccionados antes de esa fecha se rigen por la norma vigente al "
            "momento de la convocatoria, incluyendo las modificaciones, controversias y "
            "sanciones aplicables.\n"
            "3. Las plataformas SEACE 2.0 mantienen vigencia transitoria hasta la migración "
            "completa al SEACE 3.0.\n"
            "4. El OSCE se transforma en OECE y conserva su personería jurídica para todos los "
            "efectos.\n"
            "5. Las inhabilitaciones impuestas bajo la Ley 30225 siguen vigentes por el plazo "
            "originalmente fijado."
        ),
    },
]
