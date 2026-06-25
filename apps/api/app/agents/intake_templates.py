"""
Intake templates — preguntas canónicas por área legal que el agente usa
durante la fase INTAKE de una conversación de análisis de caso.

Patrón híbrido:
- Cada área tiene una **plantilla base** con framing + preguntas + uploads_hint.
- El LLM en `intake_node` puede ADAPTAR las preguntas al contexto del usuario
  (omitir las ya respondidas, reformularlas, agregar 1-2 específicas).
- Áreas sin plantilla específica usan `GENERIC_TEMPLATE`.

Estructura de cada plantilla:
    framing: str              — 2-3 frases que sitúan al caso en la normativa peruana.
    questions: list[str]      — 4-6 preguntas iniciales, en orden de criticidad.
    uploads_hint: str         — qué documentos invitar a subir.
    next_phase_signal: str    — ejemplos del lenguaje que el agente puede usar
                                para señalar transición a investigación profunda.
"""

from typing import TypedDict


class IntakeTemplate(TypedDict):
    framing: str
    questions: list[str]
    uploads_hint: str


# ──────────────────────────────────────────────────────────────────────────
# Templates by area
# ──────────────────────────────────────────────────────────────────────────

INTAKE_TEMPLATES: dict[str, IntakeTemplate] = {
    "laboral": {
        "framing": (
            "Tu caso entra en materia laboral. En Perú la normativa central es el "
            "TUO del DL 728 (DS 003-97-TR, Ley de Productividad y Competitividad "
            "Laboral) y la Ley 29783 (Seguridad y Salud en el Trabajo). Necesito "
            "datos puntuales para identificar tu régimen y la vía adecuada (interna, "
            "SUNAFIL o judicial laboral)."
        ),
        "questions": [
            "¿En qué régimen estás contratado? (régimen privado 728 / CAS / MYPE / SERVIR / agrario)",
            "¿Cuánto tiempo llevas en la empresa y tienes contrato firmado?",
            "¿Recibes boletas de pago todos los meses?",
            "¿Hay testigos directos de los hechos que afectan tus derechos?",
            "¿Tienes mensajes, correos, audios o capturas que documenten el problema?",
            "¿Has hecho algún reclamo interno o externo previo? Si sí, ¿qué pasó?",
        ],
        "uploads_hint": "contrato de trabajo, boletas de pago, correos con RRHH, capturas de WhatsApp",
    },
    "familia": {
        "framing": (
            "Tu caso entra en derecho de familia. La base es el Código Civil "
            "(Libro III), el Código de los Niños y Adolescentes (Ley 27337) y, "
            "si hay violencia, la Ley 30364. Necesito datos personales del núcleo "
            "para definir la vía (notarial, conciliación o juzgado de familia)."
        ),
        "questions": [
            "¿Estás casado(a), conviviente o separado(a)? ¿Hace cuánto?",
            "¿Hay hijos menores de edad involucrados? ¿De qué edad?",
            "¿Existe régimen de sociedad de gananciales o separación de patrimonios?",
            "¿Hay bienes en común (inmuebles, vehículos, cuentas, negocios)?",
            "¿Has intentado un acuerdo conjunto o estás considerando vía judicial?",
            "¿Hay antecedentes de violencia familiar o medidas de protección vigentes?",
        ],
        "uploads_hint": "partida de matrimonio o reconocimiento de unión de hecho, partidas de hijos, escrituras de bienes",
    },
    "penal": {
        "framing": (
            "Tu caso entra en derecho penal. La normativa central es el Código "
            "Penal (DL 635) y el Nuevo Código Procesal Penal (DL 957). Necesito "
            "saber tu rol (denunciante, agraviado, imputado) y el estado actual "
            "del proceso para guiarte sobre la vía y los plazos críticos."
        ),
        "questions": [
            "¿Eres la persona agraviada, denunciante o estás siendo investigado(a)?",
            "¿Ya hay una denuncia o investigación abierta? ¿Por qué fiscalía o comisaría?",
            "¿Conoces el tipo penal imputado o presunto delito? (robo, estafa, lesiones, agresión, etc.)",
            "¿Hay medidas cautelares (detención, comparecencia, impedimento de salida)?",
            "¿Tienes pruebas, testigos o documentos relevantes?",
            "¿Has tenido contacto con un abogado o defensoría pública?",
        ],
        "uploads_hint": "denuncia policial, citación fiscal, parte médico, declaraciones, fotos del lugar",
    },
    "civil": {
        "framing": (
            "Tu caso entra en derecho civil. La base es el Código Civil de 1984 "
            "(DL 295). Según el contenido específico (contratos, obligaciones, "
            "responsabilidad civil, derechos reales, sucesiones), la vía procesal "
            "y plazos cambian."
        ),
        "questions": [
            "¿Cuál es la institución civil involucrada? (contrato, propiedad, herencia, daño)",
            "¿Cuándo ocurrió el hecho que origina el reclamo?",
            "¿Cuál es la cuantía aproximada del bien o pretensión en juego?",
            "¿Hay documentación firmada (contratos, escrituras, recibos)?",
            "¿La contraparte está identificada y localizable?",
            "¿Ya hay un proceso judicial iniciado o todavía es extrajudicial?",
        ],
        "uploads_hint": "contratos, escrituras públicas, correos de tratativas, recibos, partidas registrales",
    },
    "tributario": {
        "framing": (
            "Tu caso entra en materia tributaria. La normativa marco es el TUO del "
            "Código Tributario (DS 133-2013-EF). Necesito identificar el tributo, "
            "el ejercicio fiscal y la situación actual frente a SUNAT para evaluar "
            "fraccionamiento, reclamación o defensa contenciosa."
        ),
        "questions": [
            "¿Cuál es el tributo en cuestión? (Renta, IGV, IR personas, RUS, predial, alcabala)",
            "¿En qué régimen tributario estás? (NRUS, RER, MYPE Tributario, Régimen General)",
            "¿Has recibido alguna notificación, resolución de determinación o multa de SUNAT?",
            "¿En qué ejercicio fiscal ocurrió el hecho?",
            "¿Has presentado declaración jurada o estás en omisión?",
            "¿Estás dentro de plazo para reclamar/apelar (20 días hábiles desde notificación)?",
        ],
        "uploads_hint": "resolución SUNAT, valores notificados, declaraciones presentadas, comprobantes",
    },
    "consumidor": {
        "framing": (
            "Tu caso entra en protección al consumidor. La normativa central es "
            "el Código de Protección y Defensa del Consumidor (Ley 29571) y INDECOPI "
            "es la autoridad. Necesito datos sobre la transacción y la prueba del "
            "incumplimiento para definir reclamo, denuncia o procedimiento sumarísimo."
        ),
        "questions": [
            "¿Qué producto o servicio adquiriste? ¿En qué fecha?",
            "¿En qué establecimiento o vía? (presencial, online, app, teléfono)",
            "¿Cuál es el problema concreto: idoneidad, información, garantía, cobro indebido?",
            "¿Conservas comprobante de pago, boleta, factura o orden de compra?",
            "¿Anotaste el reclamo en el Libro de Reclamaciones del proveedor?",
            "¿Cuál es el monto del perjuicio o lo que pides como medida correctiva?",
        ],
        "uploads_hint": "comprobante de pago, captura de la publicidad, conversaciones con el proveedor, hoja del Libro de Reclamaciones",
    },
    "datos_personales": {
        "framing": (
            "Tu caso entra en protección de datos personales. La Ley 29733 + DS "
            "016-2024-JUS regulan el tratamiento de tus datos y la ANPD es la "
            "autoridad. Identifiquemos quién es el responsable del tratamiento, "
            "el dato afectado y qué derecho ARCO-PD necesitas ejercer."
        ),
        "questions": [
            "¿Quién está tratando tus datos? (banco, empleador, red social, comercio, entidad pública)",
            "¿Qué datos en concreto te preocupan? ¿Son datos sensibles (salud, biométricos, ideología)?",
            "¿Diste consentimiento informado para el tratamiento? ¿Conservas evidencia?",
            "¿Cuál es el daño o riesgo que enfrentas? (suplantación, exposición, perfilamiento)",
            "¿Has ejercido derechos ARCO previamente sin respuesta?",
            "¿Hubo una brecha de seguridad o filtración pública conocida?",
        ],
        "uploads_hint": "captura del aviso de privacidad, correos de la empresa, evidencia de la filtración",
    },
    "contrataciones_estado": {
        "framing": (
            "Tu caso entra en contrataciones del Estado. Si el procedimiento se "
            "convocó después del 22-abr-2025 aplica la nueva Ley 32069 (LGCP); "
            "antes de esa fecha, la Ley 30225. Necesito identificar el tipo de "
            "procedimiento y la fase actual para definir si toca observación de "
            "bases, recurso de apelación o vía arbitral."
        ),
        "questions": [
            "¿Cuándo se convocó el procedimiento? (para saber si aplica Ley 32069 o 30225)",
            "¿Qué tipo de procedimiento es? (licitación pública, concurso público, adjudicación simplificada, contratación directa)",
            "¿En qué fase está el proceso? (bases, ofertas, otorgamiento, ejecución contractual)",
            "¿Cuál es el monto del contrato y el objeto contractual?",
            "¿Hay convenio arbitral en el contrato?",
            "¿Cuál es el plazo límite para tu próxima actuación procesal?",
        ],
        "uploads_hint": "bases del procedimiento, oferta presentada, contrato, notificaciones, OECE",
    },
    "ambiental": {
        "framing": (
            "Tu caso entra en derecho ambiental. La Ley General del Ambiente "
            "(Ley 28611) es la base. Según el componente afectado (agua, aire, "
            "suelo, biodiversidad), la autoridad competente cambia entre MINAM, "
            "OEFA, ANA, SERFOR o gobiernos regionales."
        ),
        "questions": [
            "¿Qué componente ambiental está siendo afectado? (agua, aire, suelo, biodiversidad)",
            "¿Quién es el presunto causante? (empresa formal, minería informal, vecino, entidad pública)",
            "¿La actividad cuenta con instrumento ambiental aprobado? (EIA-d, EIA-sd, DIA)",
            "¿Hay afectación a una comunidad indígena o área natural protegida?",
            "¿Existe denuncia previa ante OEFA, ANA o gobierno local?",
            "¿Tienes evidencia: fotos, videos, exámenes de calidad, testimonios?",
        ],
        "uploads_hint": "fotos del impacto, análisis de calidad de agua/aire, denuncia previa, EIA público",
    },
}


GENERIC_TEMPLATE: IntakeTemplate = {
    "framing": (
        "Tu consulta entra en derecho peruano. Antes de analizarla en profundidad "
        "necesito información puntual para identificar la mejor vía y citar las "
        "normas exactas que aplican a tu situación."
    ),
    "questions": [
        "¿Cuándo y dónde ocurrió el hecho que motiva tu consulta?",
        "¿Quiénes son las partes involucradas? (personas, empresas, entidades públicas)",
        "¿Qué documentación tienes hasta ahora? (contratos, mensajes, resoluciones)",
        "¿Has tomado alguna acción previa o presentado algún reclamo formal?",
        "¿Cuál es el resultado concreto que buscas? (cese de un acto, indemnización, regularización)",
        "¿Hay un plazo límite que te preocupe? (notificación recibida, vencimiento contractual)",
    ],
    "uploads_hint": "cualquier documento, correo, captura o resolución vinculada al caso",
}


def get_template(area: str) -> IntakeTemplate:
    """Return the intake template for a legal area, falling back to GENERIC."""
    return INTAKE_TEMPLATES.get(area, GENERIC_TEMPLATE)


# ──────────────────────────────────────────────────────────────────────────
# Tuning constants
# ──────────────────────────────────────────────────────────────────────────

# Hard cap on investigation turns before forcing analysis. After this many
# back-and-forth exchanges the orchestrator commits to a final analysis to
# avoid feeling like an interrogation.
MAX_INVESTIGATION_TURNS = 3

# Tokens budget for intake / investigation LLM calls.
# Intake: only the framing + 4-6 questions — 1100 is enough.
# Investigation: returns JSON with response + facts + remaining + ready flag.
# Empirically Groq llama-3.3-70b uses ~1100-1400 tokens for the JSON payload,
# so we give 1800 to leave headroom and avoid mid-JSON truncation that
# breaks parsing downstream.
INTAKE_MAX_TOKENS = 1100
INVESTIGATE_MAX_TOKENS = 1800

# User signals that force immediate transition to analysis phase.
FORCE_ANALYSIS_SIGNALS = (
    "analiza ya",
    "pasa al análisis",
    "pasa al analisis",
    "dame el análisis",
    "dame el analisis",
    "ya tengo todo",
    "ya tienes todo",
    "analiza ahora",
    "responde ya",
    "salta",
    "skip",
)


def user_signaled_analysis(message: str) -> bool:
    """True if the user explicitly asks to jump to the analysis phase."""
    low = message.lower()
    return any(sig in low for sig in FORCE_ANALYSIS_SIGNALS)
