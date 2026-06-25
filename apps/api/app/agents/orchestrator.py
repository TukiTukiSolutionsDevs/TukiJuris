"""
Legal Orchestrator — Deliberative Agent Loop with Meta-Reasoning.

This is the brain of Agente Derecho. It:
1. Classifies the user's query into a legal domain (using conversation history)
2. Routes to the appropriate specialized agent
3. EVALUATES the primary response (meta-reasoning step)
4. If needed, delegates to secondary specialists (max 2)
5. SYNTHESIZES all responses into ONE coherent final answer
6. Returns the final integrated response
"""

import asyncio
import contextvars
import json
import logging
import re
from collections.abc import Awaitable, Callable
from typing import Any as _Any


def _extract_json_robust(text: str) -> dict | None:
    """Extract a JSON object from LLM output, handling all common edge cases.

    Reasoning models (Gemini 3.1 Pro, DeepSeek Reasoner, etc.) often produce:
    - Thinking text BEFORE the JSON
    - Markdown code fences around the JSON
    - Explanatory text AFTER the JSON
    - Multiple JSON-like fragments (we want the one with "needs_more")

    Strategy: try multiple extraction methods, return first valid parse.
    """
    if not text or not text.strip():
        return None

    clean = text.strip()

    # Strategy 1: Try parsing the entire response as JSON directly
    try:
        parsed = json.loads(clean)
        if isinstance(parsed, dict) and "needs_more" in parsed:
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass

    # Strategy 2: Strip markdown code fences, then parse
    defenced = clean
    if "```" in defenced:
        # Extract content between first ``` and last ```
        fence_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', defenced, re.DOTALL)
        if fence_match:
            try:
                parsed = json.loads(fence_match.group(1).strip())
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass

    # Strategy 3: Find ALL {…} candidates, try each one, pick the one with "needs_more"
    # This handles thinking text before/after the JSON
    brace_depth = 0
    start_idx = None
    candidates = []
    for i, ch in enumerate(clean):
        if ch == '{':
            if brace_depth == 0:
                start_idx = i
            brace_depth += 1
        elif ch == '}':
            brace_depth -= 1
            if brace_depth == 0 and start_idx is not None:
                candidates.append(clean[start_idx:i + 1])
                start_idx = None

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and "needs_more" in parsed:
                return parsed
        except (json.JSONDecodeError, ValueError):
            continue

    # Strategy 4: Last resort — greedy regex (handles simple cases)
    json_match = re.search(r'\{[^{}]*"needs_more"[^{}]*\}', clean)
    if json_match:
        try:
            return json.loads(json_match.group())
        except (json.JSONDecodeError, ValueError):
            pass

    return None
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.domain_agents import AGENT_REGISTRY, get_agent
from app.agents.intake_templates import (
    INTAKE_MAX_TOKENS,
    INVESTIGATE_MAX_TOKENS,
    MAX_INVESTIGATION_TURNS,
    get_template,
    normalize_pending,
    user_signaled_analysis,
)
from app.config import settings
from app.services.llm_adapter import llm_service
from app.services.rag import rag_service

logger = logging.getLogger(__name__)


EmitCallback = Callable[[str, dict], Awaitable[None]]

_emit_event: contextvars.ContextVar[EmitCallback | None] = contextvars.ContextVar(
    "orchestrator_emit_event", default=None
)


async def _emit(event_type: str, data: dict) -> None:
    """Forward a progress event to the active SSE callback, if any.

    Streaming routes set this ContextVar before invoking the orchestrator so
    each graph node + case-phase step can publish progress without changing
    function signatures. When no callback is set (e.g. /api/chat/query), this
    is a no-op.
    """
    cb = _emit_event.get()
    if cb is None:
        return
    try:
        await cb(event_type, data)
    except Exception as exc:  # never let observability break the pipeline
        logger.warning("emit_event(%s) failed: %s", event_type, exc)


# Legal areas the orchestrator can route to.
# Keep in sync with apps/api/app/core/validators.py:_VALID_LEGAL_AREAS
# and apps/web/src/app/chat/constants.ts:LEGAL_AREAS.
LEGAL_AREAS = [
    # Núcleo heredado
    "civil",
    "penal",
    "laboral",
    "tributario",
    "constitucional",
    "administrativo",
    "corporativo",
    "registral",
    "competencia",
    "compliance",
    "comercio_exterior",
    # Privado/procesal extendido
    "procesal",
    "familia",
    "comercial",
    "notarial",
    "seguridad_social",
    # Económico-regulatorio
    "consumidor",
    "propiedad_intelectual",
    "datos_personales",
    "financiero",
    "mercado_valores",
    "seguros",
    # Sectoriales
    "ambiental",
    "minero",
    "hidrocarburos",
    "telecom",
    "transporte",
    "salud",
    # Estado
    "contrataciones_estado",
]


# --- State Definition ---


class OrchestratorState(TypedDict):
    """State that flows through the orchestrator graph."""

    query: str
    model: str | None
    legal_area_hint: str | None
    conversation_history: list[dict]
    user_context: str  # Memory context injected at agent level, NOT at classification
    user_api_key: str | None  # BYOK: user's own provider key — passed to LLM calls

    # Classification results
    primary_area: str
    secondary_areas: list[str]
    classification_confidence: float
    low_confidence_note: str  # Warning note when confidence < 0.5

    # RAG context
    retrieved_context: str

    # Agent responses
    primary_response: dict
    secondary_responses: list[dict]

    # Deliberative loop state
    primary_agent_name: str
    needs_enrichment: bool
    evaluation_reason: str
    citations: list[dict]

    # Final output
    response: str
    agent_used: str
    legal_area: str
    model_used: str
    tokens_used: int | None
    is_multi_area: bool

    # Legacy keys for process_query compatibility
    final_response: str

    # ── Case-analysis state (new in 2026-06-25) ─────────────────────────
    # Carried across turns by the API caller. The orchestrator reads `case_phase`
    # to decide whether to run intake / investigation / full analysis.
    #
    #   intake         → first turn of a new conversation; agent introduces
    #                    the legal area + asks 4-6 targeted intake questions.
    #   investigation  → turns 2..N; agent ack's user response, fills slots
    #                    in `case_facts`, asks remaining `case_pending`.
    #   analysis       → final turn; full multi-agent pipeline runs using the
    #                    accumulated `case_facts` as context.
    case_phase: str               # "intake" | "investigation" | "analysis"
    case_facts: list[dict]        # [{slot, value, source}] accumulated facts
    case_pending: list[str]       # questions the agent still wants answered
    case_turn_count: int          # 0 = intake turn, 1+ = investigation turns
    case_area_hint: str           # area inferred during intake (for routing)


# --- Keyword-based fallback classifier ---

KEYWORD_MAP = {
    "penal": ["delito", "pena", "robo", "hurto", "estafa", "homicidio", "asesinato", "violación", "secuestro", "extorsión", "prisión", "cárcel", "denuncia penal", "fiscal", "acusado", "imputado", "agraviado", "código penal", "falta grave penal", "tráfico", "drogas", "lavado", "sicariato", "feminicidio", "lesiones"],
    "laboral": ["trabajo", "trabajador", "empleador", "despido", "cts", "gratificación", "vacaciones", "remuneración", "sueldo", "salario", "laboral", "sunafil", "contrato de trabajo", "liquidación", "beneficios sociales", "horas extras", "descanso", "planilla"],
    "tributario": ["impuesto", "tributo", "sunat", "igv", "renta", "uit", "declaración", "ruc", "factura", "boleta", "detracción", "retención", "percepción", "multa tributaria", "código tributario", "fiscal tributario"],
    "civil": ["contrato civil", "propiedad", "herencia", "sucesión", "divorcio", "alimentos", "familia", "código civil", "acto jurídico", "nulidad", "prescripción civil", "responsabilidad civil", "indemnización civil", "daños y perjuicios", "arrendamiento"],
    "constitucional": ["constitución", "constitucional", "amparo", "habeas corpus", "habeas data", "tribunal constitucional", "derecho fundamental", "inconstitucionalidad", "garantía constitucional"],
    "administrativo": ["procedimiento administrativo", "silencio administrativo", "lpag", "tupa", "funcionario público", "recurso de apelación administrativa", "contrataciones del estado", "osce", "entidad pública"],
    "corporativo": ["empresa", "sociedad", "sac", "srl", "eirl", "accionista", "directorio", "junta general", "constitución de empresa", "ley general de sociedades", "registrar empresa"],
    "registral": [
        "sunarp", "registros públicos", "inscripción registral", "partida registral",
        "escritura pública", "registro de propiedad", "registro mercantil",
        "anotación preventiva", "bloqueo registral", "tracto sucesivo",
        "calificación registral", "título archivado", "asiento registral",
    ],
    "competencia": [
        "indecopi", "propiedad intelectual", "marca", "patente",
        "consumidor", "protección al consumidor", "competencia desleal",
        "libre competencia", "signos distintivos", "derechos de autor",
        "reclamo consumidor", "libro de reclamaciones",
    ],
    "compliance": [
        "compliance", "cumplimiento normativo", "lavado de activos",
        "datos personales", "habeas data", "oficial de cumplimiento",
        "uif", "prevención", "debida diligencia", "programa de cumplimiento",
        "anticorrupción", "soborno", "riesgo operacional",
    ],
    "comercio_exterior": [
        "aduana", "sunat aduanas", "importación", "exportación",
        "arancel", "drawback", "tlc", "tratado libre comercio",
        "zona franca", "régimen aduanero", "dua", "declaración aduanera",
        "dumping", "salvaguardias", "certificado de origen",
    ],
    # === Procesal y privado extendido ===
    "procesal": [
        "proceso judicial", "juzgado", "demanda", "contestación", "recurso de apelación",
        "casación", "ejecución de sentencia", "medida cautelar", "tutela cautelar",
        "código procesal civil", "cpp", "nueva ley procesal del trabajo", "ncpp",
        "audiencia única", "saneamiento procesal",
    ],
    "familia": [
        "divorcio", "alimentos", "tenencia", "régimen de visitas", "patria potestad",
        "filiación", "adopción", "matrimonio", "régimen patrimonial", "violencia familiar",
        "ley 30364", "niños y adolescentes", "código de niños", "demarcación filial",
    ],
    "comercial": [
        "título valor", "letra de cambio", "pagaré", "cheque", "factura negociable",
        "contrato mercantil", "comercio interno", "agencia comercial", "franquicia",
        "ley 27287",
    ],
    "notarial": [
        "notario", "escritura pública", "minuta", "protocolización", "fe pública",
        "acta notarial", "carta notarial", "constatación notarial", "dl 1049",
        "ley del notariado",
    ],
    "seguridad_social": [
        "essalud", "onp", "afp", "sistema nacional de pensiones", "sistema privado de pensiones",
        "jubilación", "invalidez", "sobrevivencia", "aporte previsional",
        "ley 26790", "dl 19990", "dl 25897", "bono de reconocimiento",
    ],
    # === Económico-regulatorio ===
    "consumidor": [
        "consumidor", "código de consumo", "ley 29571", "idoneidad",
        "información del producto", "publicidad engañosa", "garantía del producto",
        "libro de reclamaciones", "cláusulas abusivas", "indecopi protección consumidor",
        "métodos comerciales agresivos",
    ],
    "propiedad_intelectual": [
        "marca", "patente", "diseño industrial", "modelo de utilidad", "signo distintivo",
        "derecho de autor", "obra protegida", "dl 822", "dl 1075", "decisión 486",
        "decisión 351", "registro de marca", "indecopi marcas", "ompi",
    ],
    "datos_personales": [
        "datos personales", "anpdp", "anpd", "ley 29733", "tratamiento de datos",
        "consentimiento informado", "banco de datos personales", "transferencia internacional de datos",
        "habeas data datos", "principio de finalidad", "rgpd peruano",
    ],
    "financiero": [
        "sbs", "banco", "sistema financiero", "ley 26702", "intermediación financiera",
        "tasa de interés", "tea", "crédito de consumo", "tarjeta de crédito",
        "ley general del sistema financiero", "fondos de inversión", "fondo de garantía",
    ],
    "mercado_valores": [
        "smv", "mercado de valores", "ley del mercado de valores", "dl 861",
        "oferta pública", "emisión de valores", "bolsa de valores", "fondos mutuos",
        "información privilegiada", "manipulación del mercado", "ds 093-2002-ef",
    ],
    "seguros": [
        "póliza de seguro", "ley 29946", "contrato de seguro", "contratante",
        "asegurado", "beneficiario", "siniestro", "prima del seguro",
        "deducible", "infraseguro", "buena fe contractual seguro",
    ],
    # === Sectoriales ===
    "ambiental": [
        "ambiental", "minam", "oefa", "ley 28611", "ley general del ambiente",
        "estudio de impacto ambiental", "eia", "ley 27446", "seia", "anla peruana",
        "recursos hídricos", "ley 29338", "ana", "ley forestal", "ley 29763",
        "residuos sólidos", "dl 1278", "contaminación", "ana resolución",
    ],
    "minero": [
        "minero", "minería", "concesión minera", "ds 014-92-em", "tuo lgm",
        "petitorio minero", "minam minería", "mape", "minería artesanal",
        "ley 28090", "cierre de minas", "pasivos ambientales mineros",
        "minería ilegal", "dl 1100",
    ],
    "hidrocarburos": [
        "hidrocarburos", "ley orgánica de hidrocarburos", "ley 26221", "perupetro",
        "concesión gasífera", "gas natural", "petróleo", "ley 27133",
        "concesiones eléctricas", "dl 25844", "osinergmin", "energía eléctrica",
    ],
    "telecom": [
        "telecomunicaciones", "osiptel", "ds 013-93-tcc", "tuo ley de telecomunicaciones",
        "operador móvil", "espectro radioeléctrico", "concesión telecomunicaciones",
        "ley 28295", "compartición de infraestructura", "ley 29904", "banda ancha",
        "telefónica", "claro", "entel", "bitel",
    ],
    "transporte": [
        "transporte", "tránsito", "ley 27181", "código de tránsito", "ds 016-2009-mtc",
        "licencia de conducir", "papeleta", "infracción de tránsito", "sutran",
        "atu", "permiso de operación", "carga pesada", "vehículo automotor",
        "reglamento nacional de vehículos",
    ],
    "salud": [
        "ley 26842", "ley general de salud", "minsa", "digemid", "susalud",
        "producto farmacéutico", "ley 29459", "dispositivos médicos",
        "atención médica", "historia clínica", "ley 30024",
        "derechos del paciente", "ley 29414", "essalud cobertura",
    ],
    # === Estado ===
    "contrataciones_estado": [
        "contrataciones del estado", "ley 32069", "ley 30225", "osce", "oece",
        "licitación pública", "concurso público", "adjudicación simplificada",
        "selección de consultores", "comparación de precios", "subasta inversa",
        "tribunal de contrataciones", "perú compras", "obra pública",
        "consultoría de obra", "supervisor de obra",
    ],
}


def _keyword_classify(query: str) -> str:
    """Classify query by keyword matching. Returns best-match legal area."""
    query_lower = query.lower()
    scores: dict[str, int] = {}
    for area, keywords in KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scores[area] = score
    if scores:
        return max(scores, key=scores.get)
    return "civil"  # ultimate fallback


# --- Graph Nodes ---


async def classify_query(state: OrchestratorState) -> dict[str, Any]:
    """
    Node 1: Classify the legal domain of the user's query.
    Uses conversation history to understand context for better classification.
    """
    await _emit("step", {"node": "classify", "status": "start", "phase": "analysis"})
    # If user provided a hint, use it as primary
    if state.get("legal_area_hint") and state["legal_area_hint"] in LEGAL_AREAS:
        return {
            "primary_area": state["legal_area_hint"],
            "secondary_areas": [],
            "classification_confidence": 0.95,
        }

    query = state["query"]
    history = state.get("conversation_history", [])

    # Build context summary from last 5 messages for better classification
    history_summary = ""
    if history:
        recent = history[-5:]
        history_summary = "\n".join([
            f"{'Usuario' if m['role'] == 'user' else 'Asistente'}: {m['content'][:200]}"
            for m in recent
        ])

    history_section = ""
    if history_summary:
        history_section = (
            f"CONTEXTO DE LA CONVERSACIÓN ANTERIOR:\n{history_summary}\n\n"
            "IMPORTANTE: Considera el contexto previo para clasificar correctamente la nueva pregunta.\n\n"
        )

    classification_prompt = f"""Eres un clasificador experto en derecho peruano. Clasifica la consulta en el ÁREA PRINCIPAL que corresponde.

{history_section}ÁREAS Y SUS TEMAS:
- penal: delitos, penas, robo, hurto, estafa, homicidio, violación, lavado de activos, crimen organizado, Código Penal (DL 635), NCPP (DL 957), fiscalía
- procesal: proceso judicial, demanda, contestación, casación, apelación, medidas cautelares, NLPT (Ley 29497), CPC
- civil: contratos civiles, propiedad, obligaciones, responsabilidad civil, prescripción civil, Código Civil (DL 295)
- familia: divorcio, alimentos, tenencia, patria potestad, filiación, violencia familiar (Ley 30364), Código de Niños y Adolescentes
- laboral: trabajo, despido, CTS, gratificaciones, vacaciones, remuneración, contrato de trabajo (DS 003-97-TR), SUNAFIL, SST (Ley 29783)
- seguridad_social: ONP, AFP, EsSalud, jubilación, pensiones, DL 19990, DL 25897, Ley 26790
- tributario: impuestos, SUNAT, IGV, renta, UIT, tributos, declaración jurada, RUC, Código Tributario (DS 133-2013-EF)
- constitucional: derechos fundamentales, amparo, habeas corpus, habeas data, Tribunal Constitucional, Constitución 1993, Código Procesal Constitucional (Ley 31307)
- administrativo: procedimiento administrativo, silencio administrativo, TUPA, LPAG (TUO DS 004-2019-JUS), contencioso administrativo, transparencia (Ley 27806)
- corporativo: sociedad, accionistas, directorio, junta general, fusión, escisión, LGS (Ley 26887), EIRL
- comercial: títulos valores (letra, cheque, pagaré, Ley 27287), arbitraje (DL 1071), contratos mercantiles, sistema concursal (Ley 27809)
- registral: SUNARP, registros públicos, inscripción, partida registral, predios (Ley 27755), Reglamento General (Res. 126-2012-SUNARP)
- notarial: notario, escritura pública, minuta, fe pública, DL 1049, asuntos no contenciosos (Ley 26662)
- competencia: libre competencia, INDECOPI, conductas anticompetitivas (DL 1034 / TUO DS 030-2019-PCM), competencia desleal (DL 1044), control de fusiones (Ley 31112)
- consumidor: protección al consumidor, Código de Consumo (Ley 29571), idoneidad, libro de reclamaciones, INDECOPI consumo, cláusulas abusivas
- propiedad_intelectual: marca, patente, derecho de autor (DL 822), propiedad industrial (DL 1075), Decisión 486, Decisión 351, INDECOPI marcas
- datos_personales: ANPDP, Ley 29733, DS 003-2013-JUS, tratamiento de datos, consentimiento, transferencia internacional, habeas data
- compliance: anticorrupción, lavado de activos, programa de cumplimiento, Ley 30424, UIF (Ley 27693), DL 1106, beneficiario final (DL 1372)
- comercio_exterior: aduanas, importación, exportación, TLC, aranceles, drawback, Ley General de Aduanas (DL 1053), MINCETUR
- financiero: SBS, sistema financiero, Ley 26702, bancos, créditos, intermediación financiera, tasas de interés
- mercado_valores: SMV, oferta pública, emisión de valores, bolsa, fondos mutuos, DL 861, TUO DS 093-2002-EF, información privilegiada
- seguros: contrato de seguro, póliza, prima, siniestro, beneficiario, Ley 29946
- ambiental: MINAM, OEFA, EIA, SEIA (Ley 27446), Ley General del Ambiente (28611), recursos hídricos (Ley 29338), forestal (Ley 29763), residuos sólidos (DL 1278)
- minero: concesión minera, TUO LGM (DS 014-92-EM), cierre de minas (Ley 28090), pasivos ambientales mineros (Ley 28271), MAPE, minería ilegal (DL 1100)
- hidrocarburos: gas natural, petróleo, Ley Orgánica de Hidrocarburos (Ley 26221 / TUO DS 042-2005-EM), concesiones eléctricas (DL 25844), OSINERGMIN
- telecom: telecomunicaciones, OSIPTEL, espectro radioeléctrico, TUO Ley de Telecomunicaciones (DS 013-93-TCC), banda ancha (Ley 29904)
- transporte: tránsito, transporte terrestre (Ley 27181), código de tránsito (DS 016-2009-MTC), MTC, ATU, SUTRAN, licencia de conducir
- salud: MINSA, DIGEMID, SUSALUD, Ley General de Salud (26842), productos farmacéuticos (Ley 29459), historia clínica electrónica (Ley 30024), derechos del paciente (Ley 29414)
- contrataciones_estado: nueva LCE Ley 32069 (vigente 22-abr-2025), Ley 30225 (derogada — procesos en curso), OSCE/OECE, Tribunal de Contrataciones, licitación pública, obra pública

EJEMPLOS:
- "me robaron mi celular" → PRINCIPAL: penal
- "me despidieron sin causa" → PRINCIPAL: laboral
- "quiero divorciame" → PRINCIPAL: civil
- "cuánto pago de impuesto a la renta" → PRINCIPAL: tributario
- "qué es el habeas corpus" → PRINCIPAL: constitucional
- "quiero registrar mi marca" → PRINCIPAL: competencia
- "pena por estafa" → PRINCIPAL: penal
- "cómo constituir una empresa" → PRINCIPAL: corporativo

Responde SOLO en este formato exacto (3 líneas, nada más):
PRINCIPAL: [area]
SECUNDARIAS: [area1, area2] o NINGUNA
CONFIANZA: [0.0-1.0]

Consulta: {query}"""

    llm_result = await llm_service.completion(
        messages=[{"role": "user", "content": classification_prompt}],
        model=state.get("model") or settings.default_llm_model,
        temperature=0.0,
        max_tokens=200,
        user_api_key=state.get("user_api_key"),
        reasoning_effort=state.get("reasoning_effort"),
    )

    # Parse classification response — guard against None from thinking models
    content = llm_result.get("content") or ""
    if not content:
        logger.warning("Classification returned empty content — model may have put everything in thinking block")
    primary = ""
    secondary = []
    confidence = 0.5

    # Try structured parsing first
    for line in content.strip().split("\n"):
        line = line.strip().replace("**", "")
        if "PRINCIPAL" in line.upper() and ":" in line:
            area = line.split(":", 1)[1].strip().lower().strip("*. ")
            if area in LEGAL_AREAS:
                primary = area
        elif "SECUNDARIA" in line.upper() and ":" in line:
            areas_str = line.split(":", 1)[1].strip()
            if "NINGUNA" not in areas_str.upper():
                secondary = [
                    a.strip().lower().strip("*. ")
                    for a in areas_str.split(",")
                    if a.strip().lower().strip("*. ") in LEGAL_AREAS
                ]
        elif "CONFIANZA" in line.upper() and ":" in line:
            try:
                val = line.split(":", 1)[1].strip().strip("*. ")
                confidence = float(val)
            except ValueError:
                pass

    # Also scan for area names anywhere in the response
    if not primary:
        content_lower = content.lower()
        for area in LEGAL_AREAS:
            if area in content_lower:
                primary = area
                break

    # Keyword fallback if LLM parsing failed
    if not primary:
        primary = _keyword_classify(state["query"])
        confidence = 0.7
        logger.info(f"LLM classification failed, using keyword fallback → {primary}")

    logger.info(
        f"Query classified: primary={primary}, secondary={secondary}, confidence={confidence} | raw='{content[:100]}'"
    )

    result: dict[str, Any] = {
        "primary_area": primary,
        "secondary_areas": secondary,
        "classification_confidence": confidence,
    }

    # Low confidence warning when no hint was provided
    if confidence < 0.5 and not state.get("legal_area_hint"):
        result["low_confidence_note"] = (
            "⚠️ No estoy completamente seguro del área legal más relevante para tu consulta. "
            "Si el análisis no se ajusta a lo que buscas, intenta especificar el área legal "
            "(ej: laboral, civil, penal) al inicio de tu pregunta."
        )

    return result


async def retrieve_context(state: OrchestratorState) -> dict[str, Any]:
    """
    Node 2: Retrieve relevant legal documents via RAG.

    Uses the agent's get_rag_filter() to retrieve from all relevant
    sub-areas (e.g. civil → civil + procesal_civil + familia + sucesiones).
    When multiple sub-areas exist, retrieves from each and merges, deduplicating
    by content prefix to avoid repeating the same fragment.
    """
    await _emit("step", {"node": "retrieve", "status": "start", "phase": "analysis", "area": state.get("primary_area", "")})
    area = state.get("primary_area", "civil")

    # Determine which sub-areas to query via the agent's RAG filter
    agent = get_agent(area)
    sub_areas: list[str] = [area]
    if agent and hasattr(agent, "get_rag_filter"):
        rag_filter = agent.get_rag_filter()
        if isinstance(rag_filter, dict):
            legal_area_filter = rag_filter.get("legal_area", {})
            if isinstance(legal_area_filter, dict) and "$in" in legal_area_filter:
                sub_areas = legal_area_filter["$in"]

    try:
        if len(sub_areas) == 1:
            # Single area — simple path, no merging needed
            context = await rag_service.retrieve(
                query=state["query"],
                legal_area=sub_areas[0],
                limit=6,
            )
        else:
            # Multiple sub-areas: retrieve 3 chunks per area then merge
            per_area_limit = max(2, 6 // len(sub_areas))
            context_parts: list[str] = []
            seen_prefixes: set[str] = set()

            for sub_area in sub_areas:
                sub_context = await rag_service.retrieve(
                    query=state["query"],
                    legal_area=sub_area,
                    limit=per_area_limit,
                )
                if sub_context:
                    for chunk in sub_context.split("\n\n---\n\n"):
                        prefix = chunk[:80]
                        if prefix not in seen_prefixes:
                            seen_prefixes.add(prefix)
                            context_parts.append(chunk)

            context = "\n\n---\n\n".join(context_parts)

        if context:
            logger.info(
                f"RAG retrieved context ({len(context)} chars) for area={area} "
                f"sub_areas={sub_areas}"
            )
        else:
            logger.info("RAG returned no context — agent will use built-in knowledge")
        return {"retrieved_context": context}
    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e} — continuing without context")
        return {"retrieved_context": ""}


async def execute_primary_agent(state: OrchestratorState) -> dict[str, Any]:
    """
    Node 3: Execute the primary domain agent.

    user_context is injected HERE (agent level), not at classification.
    This keeps the classifier working on the clean query only.
    """
    await _emit("step", {"node": "primary_agent", "status": "start", "phase": "analysis", "area": state.get("primary_area", "")})
    # Build agent query: prepend user memory context if present
    agent_query = state["query"]
    if state.get("user_context"):
        agent_query = f"{state['user_context']}\n\n---\n\n{state['query']}"

    agent = get_agent(state["primary_area"])
    if not agent:
        # Fallback: use a general response
        logger.warning(f"No agent found for area: {state['primary_area']}")
        result = await llm_service.completion(
            messages=[
                {"role": "system", "content": "Eres un asistente legal peruano general."},
                {"role": "user", "content": agent_query},
            ],
            model=state.get("model"),
            user_api_key=state.get("user_api_key"),
            reasoning_effort=state.get("reasoning_effort"),
        )
        return {
            "primary_response": {
                "response": result.get("content") or "",
                "agent_used": "General",
                "legal_area": state["primary_area"],
                "model_used": result["model"],
                "tokens_used": result.get("tokens_used"),
                "citations": [],
            },
            "primary_agent_name": "General",
        }

    result = await agent.process(
        query=agent_query,
        context=state.get("retrieved_context", ""),
        model=state.get("model"),
        conversation_history=state.get("conversation_history", []),
        user_api_key=state.get("user_api_key"),  # BYOK
    )
    return {
        "primary_response": result,
        "primary_agent_name": result.get("agent_used", agent.name),
    }


async def evaluate_response(state: OrchestratorState) -> dict[str, Any]:
    """
    Node 4: META-REASONING — The orchestrator THINKS about whether the primary
    response is sufficient or needs input from other legal areas.

    This is the deliberative loop step that makes the orchestrator a true "general":
    it evaluates the primary specialist's output and decides if another perspective is needed.
    """
    await _emit("step", {"node": "evaluate", "status": "start", "phase": "analysis"})
    query = state["query"]
    primary_response = state.get("primary_response", {})
    primary_text = primary_response.get("response", "") if isinstance(primary_response, dict) else str(primary_response)
    primary_area = state.get("primary_area", "")
    user_api_key = state.get("user_api_key")

    eval_prompt = f"""Eres el ORQUESTADOR JURÍDICO de TukiJuris — el socio director de un bufete de abogados especializados en derecho peruano.

Tu trabajo es GARANTIZAR que el cliente reciba la respuesta más COMPLETA posible. Diriges un equipo de 11 especialistas y tu deber es convocar a TODOS los que tengan algo que aportar.

CONSULTA DEL CLIENTE:
{query}

RESPUESTA DEL ESPECIALISTA EN {primary_area.upper()}:
{primary_text[:3000]}

INSTRUCCIONES:
Analiza si la respuesta del {primary_area} cubre TODAS las dimensiones legales de la consulta. En un bufete serio, si hay la MÍNIMA implicancia de otra área, SE CONVOCA al especialista. No somos conservadores — somos exhaustivos.

Responde SOLO con este JSON (sin markdown, sin comentarios, reason máximo 50 palabras):
{{"needs_more": true/false, "additional_areas": ["area1", "area2"], "reason": "breve"}}

CRITERIOS PARA needs_more = true (convoca si aplica CUALQUIERA):
- La consulta MENCIONA o IMPLICA temas de otra área (aunque sea tangencialmente)
- El usuario pide explícitamente consultar a otro especialista
- Hay consecuencias tributarias no cubiertas (impuestos, SUNAT, IGV, RUC)
- Hay trámites administrativos no detallados (municipalidad, licencias, TUPA)
- Hay aspectos corporativos (constitución de empresa, sociedad)
- Hay implicancias registrales (SUNARP, inscripción, títulos)
- Hay aspectos laborales (contratos de trabajo, beneficios)
- Hay riesgos penales no mencionados
- El caso tiene dimensión constitucional
- Hay temas de compliance o competencia

ÁREAS DISPONIBLES: {', '.join(LEGAL_AREAS)}
ÁREA YA CUBIERTA (NO repetir): {primary_area}

needs_more = false SOLO cuando la consulta es 100% de una sola área y la respuesta la cubre completamente sin dejar ningún flanco legal abierto.

EJEMPLOS:
- Terreno + papeles → civil + registral + tributario (impuesto predial) + administrativo (municipalidad)
- Despido + empresa → laboral + tributario (liquidación) + corporativo
- Negocio + restaurante → corporativo + tributario + administrativo (licencias)
- Robo simple → solo penal (needs_more = false)
- Divorcio con bienes e hijos → civil + tributario (bienes)"""

    try:
        result = await llm_service.completion(
            messages=[{"role": "user", "content": eval_prompt}],
            model=state.get("model") or settings.default_llm_model,
            temperature=0.0,
            max_tokens=2048,
            user_api_key=user_api_key,
            reasoning_effort=state.get("reasoning_effort"),
        )
        content = result.get("content", "")
        logger.info(f"Evaluation raw response: {content[:400]}")

        parsed = _extract_json_robust(content)
        if parsed:
            needs_more = parsed.get("needs_more", False)
            additional = parsed.get("additional_areas", [])
            reason = parsed.get("reason", "")

            # Validate: only known areas, never the primary area, up to 4
            valid_additional = [
                a for a in additional
                if a in LEGAL_AREAS and a != primary_area
            ][:4]

            logger.info(
                f"Evaluation: needs_more={needs_more}, areas={valid_additional}, reason={reason[:100]}"
            )

            return {
                "needs_enrichment": needs_more and len(valid_additional) > 0,
                "secondary_areas": valid_additional,
                "evaluation_reason": reason,
            }
        else:
            logger.warning(f"Evaluation: could not extract JSON from response: {content[:300]}")
    except Exception as e:
        logger.warning("Evaluation LLM call failed: %s", e)

    return {
        "needs_enrichment": False,
        "secondary_areas": [],
        "evaluation_reason": "",
    }


async def enrich_with_secondary(state: OrchestratorState) -> dict[str, Any]:
    """
    Node 5 (conditional): Get additional context from secondary domain agents.

    Only runs when evaluate_response() determines needs_enrichment=True.
    Secondary agents receive:
    1. The user's original query
    2. The PRIMARY agent's response (so they can COMPLEMENT, not repeat)
    3. RAG context for their specific area
    """
    # Up to 4 secondaries — more areas = richer multi-perspective analysis,
    # which is the whole point of the orchestrator. We run them in parallel
    # (asyncio.gather) so the total elapsed time is max(per-agent) instead
    # of sum() — capping wouldn't add quality but would skip perspectives.
    target_areas = state.get("secondary_areas", [])[:4]
    total = len(target_areas)
    started_at = asyncio.get_event_loop().time()
    await _emit("step", {
        "node": "enrich",
        "status": "start",
        "phase": "analysis",
        "secondary_areas": target_areas,
        "total": total,
    })
    primary = state.get("primary_response", {})
    primary_text = primary.get("response", "") if isinstance(primary, dict) else str(primary)
    primary_agent_name = state.get("primary_agent_name", "especialista previo")

    # Atomic-ish completion counter — asyncio is single-threaded so plain
    # closure mutation is safe between awaits.
    completed = 0

    async def _run_one(area: str) -> dict | None:
        """Run a single secondary agent end-to-end. Returns None on failure
        so the gather can keep the rest of the responses."""
        nonlocal completed
        agent = get_agent(area)
        if not agent:
            return None

        agent_start = asyncio.get_event_loop().time()
        enrichment_query = (
            f"Otro especialista ({primary_agent_name}) ya analizó esta consulta. "
            f"Tu rol es COMPLEMENTAR su análisis desde tu perspectiva como {agent.name}. "
            f"NO repitas lo que ya dijo — enfocate en lo que falta o difiere.\n\n"
            f"CONSULTA ORIGINAL: {state['query']}\n\n"
            f"ANÁLISIS PREVIO DEL {primary_agent_name.upper()}:\n"
            f"{primary_text[:2500]}\n\n"
            f"Ahora da tu análisis complementario desde {agent.name}. "
            f"Sé específico con normativa y artículos aplicables."
        )

        secondary_context = ""
        try:
            secondary_context = await rag_service.retrieve(
                query=state["query"],
                legal_area=area,
                limit=4,
            )
        except Exception as exc:
            logger.warning(f"RAG retrieval failed for secondary area={area}: {exc}")

        skipped = False
        result: dict | None = None
        try:
            result = await agent.process(
                query=enrichment_query,
                context=secondary_context,
                model=state.get("model"),
                conversation_history=state.get("conversation_history", []),
                user_api_key=state.get("user_api_key"),
            )
        except Exception as exc:
            skipped = True
            logger.warning(
                "Secondary agent failed (area=%s) — skipping. Reason: %s",
                area, exc,
            )

        completed += 1
        took_ms = int((asyncio.get_event_loop().time() - agent_start) * 1000)
        elapsed_ms = int((asyncio.get_event_loop().time() - started_at) * 1000)
        await _emit("enrich_progress", {
            "completed": completed,
            "total": total,
            "area": area,
            "agent_name": agent.name,
            "took_ms": took_ms,
            "elapsed_ms": elapsed_ms,
            "skipped": skipped,
        })
        return result

    # Run all secondaries in parallel. asyncio.gather waits for the slowest
    # so total elapsed time = max(per-agent), not sum().
    results = await asyncio.gather(
        *[_run_one(area) for area in target_areas],
        return_exceptions=False,
    )
    secondary_responses = [r for r in results if r is not None]
    return {"secondary_responses": secondary_responses}


async def synthesize_response(state: OrchestratorState) -> dict[str, Any]:
    """
    Node 6a: The orchestrator synthesizes all agent responses into ONE coherent answer.

    Acts as the 'general' making the final decision after consulting all specialists.
    Used when needs_enrichment=True (multi-area responses).
    """
    await _emit("step", {"node": "synthesize", "status": "start", "phase": "analysis"})
    primary = state.get("primary_response", {})
    primary_text = primary.get("response", "") if isinstance(primary, dict) else str(primary)
    primary_area = state.get("primary_area", "")
    secondary_responses = state.get("secondary_responses", [])
    evaluation_reason = state.get("evaluation_reason", "")
    user_api_key = state.get("user_api_key")

    # Collect all citations
    all_citations = list(primary.get("citations", []) if isinstance(primary, dict) else [])
    secondary_texts = []
    for sec in secondary_responses:
        area_name = sec.get("agent_used", "Especialista")
        secondary_texts.append(f"### Análisis de {area_name}:\n{sec.get('response', '')}")
        if sec.get("citations"):
            all_citations.extend(sec["citations"])

    synthesis_prompt = f"""Eres el ORQUESTADOR JURÍDICO de TukiJuris — el abogado senior que dirige un equipo de especialistas.

Has convocado una reunión con tus especialistas sobre este caso. Ahora debes redactar la RESPUESTA FINAL para el cliente, integrando todos los análisis.

CONSULTA DEL CLIENTE:
{state['query']}

RAZÓN POR LA QUE CONVOCASTE MÁS ESPECIALISTAS:
{evaluation_reason}

ANÁLISIS DEL ESPECIALISTA EN {primary_area.upper()}:
{primary_text[:3000]}

{chr(10).join(secondary_texts)}

INSTRUCCIONES PARA LA RESPUESTA FINAL:
1. Integra TODOS los análisis en UNA respuesta coherente y fluida
2. NO repitas disclaimers — pon uno solo al final
3. Organiza por temas, no por agente (el cliente no necesita saber que hubo "reunión")
4. Cita las normas específicas de CADA área mencionada
5. Si hay conflicto entre áreas (ej: derecho civil dice A pero administrativo dice B), explica ambas posiciones
6. Da una recomendación clara al final: qué debería hacer el cliente PRIMERO
7. Escribe como un abogado senior que ya consultó con todo su equipo

Escribe la respuesta final integrada:"""

    try:
        result = await llm_service.completion(
            messages=[{"role": "user", "content": synthesis_prompt}],
            model=state.get("model") or settings.default_llm_model,
            temperature=0.3,
            max_tokens=4096,
            user_api_key=user_api_key,
            reasoning_effort=state.get("reasoning_effort"),
        )
        synthesized = result.get("content", primary_text)
    except Exception as exc:
        logger.warning(f"Synthesis LLM call failed, falling back to concatenation: {exc}")
        # Fallback: concatenation
        synthesized = primary_text
        for sec in secondary_responses:
            synthesized += f"\n\n**Complemento ({sec.get('agent_used', '')}):**\n{sec.get('response', '')}"

    secondary_area_names = [
        sec.get("agent_used", "") for sec in secondary_responses if sec.get("agent_used")
    ]
    agent_label = f"Orquestador ({primary_area} + {', '.join(state.get('secondary_areas', []))})"

    return {
        "response": synthesized,
        "citations": all_citations,
        "agent_used": agent_label,
        "legal_area": primary_area,
        "model_used": primary.get("model_used", "") if isinstance(primary, dict) else "",
        "tokens_used": primary.get("tokens_used") if isinstance(primary, dict) else None,
        "is_multi_area": True,
        "final_response": synthesized,  # legacy compat
    }


async def format_simple_response(state: OrchestratorState) -> dict[str, Any]:
    """
    Node 6b: For single-agent responses that don't need synthesis.
    Used when needs_enrichment=False.
    """
    await _emit("step", {"node": "format_simple", "status": "start", "phase": "analysis"})
    primary = state.get("primary_response", {})
    primary_text = primary.get("response", "") if isinstance(primary, dict) else ""

    # Prepend low-confidence note if classification was uncertain
    if state.get("low_confidence_note"):
        primary_text = f"{state['low_confidence_note']}\n\n{primary_text}"

    all_citations = primary.get("citations", []) if isinstance(primary, dict) else []

    return {
        "response": primary_text,
        "citations": all_citations,
        "agent_used": state.get("primary_agent_name", ""),
        "legal_area": state.get("primary_area", ""),
        "model_used": primary.get("model_used", "") if isinstance(primary, dict) else "",
        "tokens_used": primary.get("tokens_used") if isinstance(primary, dict) else None,
        "is_multi_area": False,
        "final_response": primary_text,  # legacy compat
    }


# --- Graph Routing ---


def _route_after_evaluate(state: OrchestratorState) -> str:
    """Conditional edge: route to enrichment or simple format."""
    if state.get("needs_enrichment") and state.get("secondary_areas"):
        return "enrich"
    return "format_simple"


# --- Build the Graph ---


def build_orchestrator_graph() -> StateGraph:
    """Construct the LangGraph orchestrator workflow with deliberative loop."""
    workflow = StateGraph(OrchestratorState)

    # Add nodes
    workflow.add_node("classify", classify_query)
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("primary_agent", execute_primary_agent)
    workflow.add_node("evaluate", evaluate_response)       # META-REASONING
    workflow.add_node("enrich", enrich_with_secondary)     # Secondary agents
    workflow.add_node("synthesize", synthesize_response)   # Multi-area synthesis
    workflow.add_node("format_simple", format_simple_response)  # Single-agent

    # Define edges
    workflow.set_entry_point("classify")
    workflow.add_edge("classify", "retrieve")
    workflow.add_edge("retrieve", "primary_agent")
    workflow.add_edge("primary_agent", "evaluate")  # Always evaluate after primary

    # Conditional: does the orchestrator think we need more agents?
    workflow.add_conditional_edges(
        "evaluate",
        _route_after_evaluate,
        {"enrich": "enrich", "format_simple": "format_simple"},
    )
    workflow.add_edge("enrich", "synthesize")
    workflow.add_edge("synthesize", END)
    workflow.add_edge("format_simple", END)

    return workflow


# ──────────────────────────────────────────────────────────────────────────
# Case-analysis phases — intake + investigation (run OUTSIDE the LangGraph
# analysis pipeline). These are simple LLM calls that produce structured
# output; the full multi-agent LangGraph is reserved for the analysis phase.
# ──────────────────────────────────────────────────────────────────────────


def _extract_first_json_obj(text: str) -> dict | None:
    """Return the first balanced {…} parsed as JSON from `text`, else None.

    Lighter alternative to `_extract_json_robust` for intake/investigation,
    where we don't require the `needs_more` discriminator.
    """
    if not text:
        return None
    try:
        return json.loads(text.strip())
    except (json.JSONDecodeError, ValueError):
        pass
    fence = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            pass
    # Brace balancing scan
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return json.loads(text[start : i + 1])
                except (json.JSONDecodeError, ValueError):
                    start = None
    return None


async def _quick_classify(
    query: str,
    model: str | None,
    user_api_key: str | None,
) -> str:
    """One-shot light classifier used by the intake step.

    Reuses the same prompt structure as `classify_query` but trims the
    secondary-areas/confidence parsing for speed. Falls back to keyword match
    on LLM failure.
    """
    prompt = (
        "Clasifica la siguiente consulta legal peruana en UNA sola área. "
        "Responde solo con el slug del área en minúsculas (ej: laboral, "
        "familia, penal, civil, tributario, consumidor, ambiental, contrataciones_estado).\n"
        f"Áreas válidas: {', '.join(LEGAL_AREAS)}.\n\n"
        f"Consulta: {query}\n\n"
        "Solo el slug, nada más:"
    )
    try:
        result = await llm_service.completion(
            messages=[{"role": "user", "content": prompt}],
            model=model or settings.default_llm_model,
            temperature=0.0,
            max_tokens=20,
            user_api_key=user_api_key,
        )
        raw = (result.get("content") or "").strip().lower()
        raw = raw.strip("*. ").splitlines()[0] if raw else ""
        if raw in LEGAL_AREAS:
            return raw
    except Exception as exc:
        logger.warning(f"_quick_classify LLM failed, falling back to keywords: {exc}")
    return _keyword_classify(query)


async def run_intake_turn(
    query: str,
    model: str | None,
    legal_area_hint: str | None,
    user_api_key: str | None,
) -> dict:
    """
    Generate the first response of a case-analysis conversation.

    Output shape:
    {
      "response":      str,              # markdown to show the user
      "case_state": {
        "case_phase":      "investigation",
        "case_facts":      [],           # nothing filled yet
        "case_pending":    list[str],    # questions still pending
        "case_turn_count": 1,
        "case_area_hint":  str,
      },
      "legal_area":  str,
      "agent_used":  "Intake",
    }
    """
    await _emit("step", {"node": "intake_classify", "status": "start", "phase": "intake"})
    area = legal_area_hint if legal_area_hint in LEGAL_AREAS else None
    if not area:
        area = await _quick_classify(query, model, user_api_key)
    await _emit("step", {"node": "intake_classify", "status": "done", "phase": "intake", "area": area})

    template = get_template(area)
    await _emit("step", {"node": "intake_template", "status": "done", "phase": "intake", "area": area})
    await _emit("step", {"node": "intake_llm", "status": "start", "phase": "intake", "area": area})

    # The structured questions live in the template; the LLM only writes the
    # framing intro. The frontend renders the questions as a QuestionForm
    # (cards + chips + free-text input) — so embedding them in the markdown
    # body would just duplicate the UI.
    intake_prompt = f"""Eres el agente de INTAKE de TukiJuris — un abogado peruano que recibe a un cliente nuevo. Tu trabajo en este turno es UBICAR el caso en la normativa peruana relevante, NO responder ni dar análisis aún.

CONSULTA INICIAL DEL CLIENTE:
{query}

CONTEXTO NORMATIVO BASE (úsalo como punto de partida):
{template['framing']}

INSTRUCCIONES DE RESPUESTA — ESTRICTAS:
1. Escribe 3-5 frases que (a) reconozcan brevemente la situación del cliente, (b) sitúen el caso en la normativa peruana específica del área "{area}", citando 1-2 leyes/DL/decretos clave.
2. Cierra con UNA sola frase tipo: "Para armar el análisis necesito que respondas algunas preguntas; abajo te las dejo organizadas." (puedes parafrasearla).
3. NO incluyas preguntas numeradas ni en bullets — las preguntas se le muestran al cliente como un formulario aparte, abajo del mensaje. Si las repites acá quedan duplicadas.
4. NO des recomendaciones ni análisis legal sustantivo.
5. Menciona brevemente que puede adjuntar: {template['uploads_hint']}.
6. Tono: profesional, cercano, empático. Idioma: español peruano.
7. Máximo 7 frases en total. Sé directo.
"""

    try:
        result = await llm_service.completion(
            messages=[{"role": "user", "content": intake_prompt}],
            model=model or settings.default_llm_model,
            temperature=0.4,
            max_tokens=INTAKE_MAX_TOKENS,
            user_api_key=user_api_key,
        )
        content = (result.get("content") or "").strip()
    except Exception as exc:
        logger.warning(f"Intake LLM call failed: {exc}")
        content = ""

    if not content:
        # Deterministic fallback: just the framing + a closing line.
        content = (
            f"{template['framing']}\n\n"
            f"Para armar el análisis necesito que respondas algunas preguntas; "
            f"abajo te las dejo organizadas. Si tienes a la mano "
            f"{template['uploads_hint']}, súbelo en el adjunto."
        )

    # Structured pending questions come straight from the template — the
    # frontend renders them as chips + free-text input.
    pending = list(template["questions"])

    return {
        "response": content,
        "case_state": {
            "case_phase": "investigation",
            "case_facts": [],
            "case_pending": pending,
            "case_turn_count": 1,
            "case_area_hint": area,
        },
        "legal_area": area,
        "agent_used": "Intake",
        "model_used": (result.get("model") if "result" in locals() else "") or "",
        "tokens_used": (result.get("tokens_used") if "result" in locals() else None),
    }


async def run_investigation_turn(
    query: str,
    model: str | None,
    case_state: dict,
    user_api_key: str | None,
) -> dict:
    """
    Process a user response during the investigation phase.

    The LLM is asked to:
      1. Extract structured facts from the user's reply → updates case_facts.
      2. Decide which of the pending questions remain unanswered.
      3. Determine `case_ready` — whether enough is known to move to analysis.
      4. Write a short acknowledgement + the next 2-3 follow-up questions
         (or a brief "ok, paso al análisis" if case_ready=true).

    The phase transitions to "analysis" when either:
      - The LLM reports case_ready=true, OR
      - `case_turn_count + 1 >= MAX_INVESTIGATION_TURNS`.

    The actual analysis (full multi-agent pipeline) is NOT executed here —
    the caller (`process_query`) inspects the returned `case_phase` and runs
    the analysis graph in the SAME turn if the phase flipped.
    """
    area = case_state.get("case_area_hint") or _keyword_classify(query)
    # Tolerate legacy list[str] in case_pending — wrap as structured.
    pending = normalize_pending(case_state.get("case_pending") or [])
    facts = list(case_state.get("case_facts") or [])
    turn_count = int(case_state.get("case_turn_count") or 1)
    await _emit("step", {"node": "investigation_extract", "status": "start", "phase": "investigation", "area": area, "turn": turn_count + 1})

    # Render structured pending as `[slot] question` so the LLM can reference
    # each item by its canonical slot when reporting what's still open.
    pending_rendered = (
        "\n".join(f"- [{p['slot']}] {p['question']}" for p in pending)
        if pending else "(ninguna pendiente)"
    )

    investigation_prompt = f"""Eres el agente de INVESTIGACIÓN de TukiJuris — un abogado peruano construyendo el caso turno a turno con el cliente.

ÁREA DEL CASO: {area}
TURNO DE INVESTIGACIÓN ACTUAL: {turn_count + 1} (máximo {MAX_INVESTIGATION_TURNS} antes de pasar al análisis final).

HECHOS YA RECOGIDOS (JSON):
{json.dumps(facts, ensure_ascii=False)}

PREGUNTAS PENDIENTES (formato: [slot] pregunta — usa el slot para referirte a ellas):
{pending_rendered}

NUEVA RESPUESTA DEL CLIENTE:
{query}

TAREAS:
1. Extrae los hechos NUEVOS que aporta esta respuesta. Cada hecho es un {{"slot": "<slot_canónico>", "value": "<dato>"}}. Usa los slots de la lista pendiente cuando puedas mapear directamente; inventa slots nuevos solo para datos extra.
2. Lista los `remaining_pending_slots` — slots de la sección pendiente que quedan SIN responder.
3. Si crees que ya hay información SUFICIENTE para dar un análisis sólido (no exhaustivo, sólido), marca `case_ready=true`.
4. Escribe un mensaje corto al cliente (máximo 4 frases):
   - ACUSE breve: qué entendiste, qué encaje legal preliminar ves (cita 1-2 normas).
   - Si case_ready=true: cierra con "Voy a preparar tu análisis ahora." y NADA más.
   - Si case_ready=false: cierra con "Faltan unos datos más; respondé las preguntas restantes abajo." (las preguntas se muestran en un formulario aparte, NO las repitas acá).

Devuelve un único objeto JSON puro. Sin markdown, sin texto adicional fuera del JSON:
{{
  "response": "<mensaje markdown corto, sin preguntas numeradas>",
  "new_facts": [{{"slot": "string", "value": "string"}}, ...],
  "remaining_pending_slots": ["slot_a", "slot_b", ...],
  "case_ready": true|false
}}
"""

    response_text = ""
    new_facts: list[dict] = []
    remaining: list = list(pending)
    case_ready = False

    try:
        result = await llm_service.completion(
            messages=[{"role": "user", "content": investigation_prompt}],
            model=model or settings.default_llm_model,
            temperature=0.3,
            max_tokens=INVESTIGATE_MAX_TOKENS,
            user_api_key=user_api_key,
        )
        raw = result.get("content") or ""
        parsed = _extract_first_json_obj(raw)
        if not parsed:
            logger.warning(
                "Investigation JSON parse failed — falling back to free-text. "
                "Raw head: %r",
                raw[:200],
            )
        if parsed:
            response_text = str(parsed.get("response") or "").strip()
            nf = parsed.get("new_facts") or []
            if isinstance(nf, list):
                new_facts = [
                    {"slot": str(x.get("slot", "")), "value": str(x.get("value", ""))}
                    for x in nf
                    if isinstance(x, dict) and x.get("value")
                ]
            # New shape: filter the structured pending by the slots the LLM
            # says are still open. Fall back to the legacy `remaining_pending`
            # key for one transition cycle.
            rps = parsed.get("remaining_pending_slots")
            if isinstance(rps, list) and rps:
                open_slots = {str(s) for s in rps if s}
                remaining = [p for p in pending if p.get("slot") in open_slots]
            else:
                legacy_rp = parsed.get("remaining_pending") or []
                if isinstance(legacy_rp, list) and legacy_rp:
                    # LLM returned free-text remaining; wrap each as structured
                    # so the frontend can still render a textbox per item.
                    remaining = normalize_pending([str(q) for q in legacy_rp])
                else:
                    remaining = []
            case_ready = bool(parsed.get("case_ready"))
        else:
            # If parsing failed, just echo the raw content and assume we still
            # need more info.
            response_text = raw.strip()
            new_facts = [{"slot": "free_text", "value": query}]
    except Exception as exc:
        logger.warning(f"Investigation LLM call failed: {exc}")
        response_text = (
            "Gracias por la información. Faltan unos datos más; "
            "respondé las preguntas restantes abajo."
        )
        new_facts = [{"slot": "free_text", "value": query}]

    # Merge accumulated state
    updated_facts = facts + new_facts
    next_turn_count = turn_count + 1

    # Force analysis if we hit the cap OR the user explicitly asks for it
    forced_by_signal = user_signaled_analysis(query)
    forced_by_cap = next_turn_count >= MAX_INVESTIGATION_TURNS
    final_ready = case_ready or forced_by_signal or forced_by_cap

    next_phase = "analysis" if final_ready else "investigation"

    return {
        "response": response_text,
        "case_state": {
            "case_phase": next_phase,
            "case_facts": updated_facts,
            "case_pending": [] if final_ready else remaining,
            "case_turn_count": next_turn_count,
            "case_area_hint": area,
        },
        "legal_area": area,
        "agent_used": "Investigación" if not final_ready else "Investigación (cierre)",
        "model_used": (result.get("model") if "result" in locals() else "") or "",
        "tokens_used": (result.get("tokens_used") if "result" in locals() else None),
        # Signal to the caller whether analysis must be triggered next.
        "_run_analysis_next": final_ready,
    }


def _build_case_context_block(case_state: dict, current_message: str) -> str:
    """
    Build the rich query that gets fed to the analysis pipeline when an
    investigation flips to analysis. We collapse the recorded facts into a
    structured brief so the multi-agent flow has everything in one place.
    """
    facts = case_state.get("case_facts") or []
    area = case_state.get("case_area_hint") or ""
    lines = [f"CASO EN ANÁLISIS — área detectada: {area}.", "", "HECHOS RECOPILADOS:"]
    if facts:
        for f in facts:
            slot = f.get("slot", "dato")
            value = f.get("value", "")
            lines.append(f"- {slot}: {value}")
    else:
        lines.append("- (ningún hecho estructurado registrado)")
    lines += [
        "",
        "ÚLTIMO MENSAJE DEL CLIENTE EN LA CONVERSACIÓN:",
        current_message,
        "",
        "Da el análisis final del caso siguiendo el formato profesional habitual.",
    ]
    return "\n".join(lines)


# --- Orchestrator Interface ---


class LegalOrchestrator:
    """High-level interface for the legal orchestrator."""

    def __init__(self):
        graph = build_orchestrator_graph()
        self.app = graph.compile()

    async def process_query(
        self,
        query: str,
        model: str | None = None,
        legal_area_hint: str | None = None,
        conversation_history: list[dict] | None = None,
        user_context: str | None = None,
        user_api_key: str | None = None,
        case_state: dict | None = None,
    ) -> dict:
        """
        Process a legal query through the case-analysis pipeline.

        Flow depends on `case_state["case_phase"]`:
        - None or "intake" → run `run_intake_turn`. No analysis yet.
        - "investigation"  → run `run_investigation_turn`. If the LLM (or the
                             turn cap) flips the phase to "analysis", we ALSO
                             run the full multi-agent pipeline in the same turn
                             so the user gets the final analysis right away.
        - "analysis"       → caller already has the brief; jump straight to the
                             multi-agent LangGraph pipeline.

        Args:
            query: The user's message (clean — no memory prepended)
            model: Optional model override
            legal_area_hint: Optional area hint (used during intake)
            conversation_history: Prior messages for continuity
            user_context: User memory context — injected at agent level only
            user_api_key: BYOK — user's own LLM provider key
            case_state: Persistent case-analysis state across turns. Pass back
                        the `case_state` from the previous response unchanged.

        Returns:
            dict with response, agent_used, legal_area, citations, model_used,
            is_multi_area, AND `case_state` (carry to next turn).
        """
        phase = (case_state or {}).get("case_phase") or "intake"
        await _emit("phase_start", {"phase": phase})

        # ── INTAKE — first turn of a brand-new case ────────────────────────
        if phase == "intake":
            intake = await run_intake_turn(
                query=query,
                model=model,
                legal_area_hint=legal_area_hint,
                user_api_key=user_api_key,
            )
            return {
                "response": intake["response"],
                "agent_used": intake["agent_used"],
                "legal_area": intake["legal_area"],
                "citations": [],
                "model_used": intake.get("model_used", ""),
                "tokens_used": intake.get("tokens_used"),
                "is_multi_area": False,
                "case_state": intake["case_state"],
            }

        # ── INVESTIGATION — turns 2..N ─────────────────────────────────────
        if phase == "investigation":
            inv = await run_investigation_turn(
                query=query,
                model=model,
                case_state=case_state or {},
                user_api_key=user_api_key,
            )
            # If the investigation step flipped the phase to "analysis", we
            # continue right into the multi-agent pipeline so the user sees
            # the final answer in the same turn.
            if not inv.get("_run_analysis_next"):
                return {
                    "response": inv["response"],
                    "agent_used": inv["agent_used"],
                    "legal_area": inv["legal_area"],
                    "citations": [],
                    "model_used": inv.get("model_used", ""),
                    "tokens_used": inv.get("tokens_used"),
                    "is_multi_area": False,
                    "case_state": inv["case_state"],
                }
            # Fall through to analysis using the enriched case_state
            case_state = inv["case_state"]
            legal_area_hint = inv["legal_area"]
            await _emit("phase_start", {"phase": "analysis", "auto_transition": True})

        # ── ANALYSIS — full multi-agent LangGraph pipeline ────────────────
        # Build a rich query that bakes the recorded case facts into the
        # prompt so every downstream agent has the same view.
        enriched_query = (
            _build_case_context_block(case_state or {}, query)
            if case_state else query
        )

        initial_state: OrchestratorState = {
            "query": enriched_query,
            "model": model,
            "legal_area_hint": legal_area_hint or (case_state or {}).get("case_area_hint"),
            "conversation_history": conversation_history or [],
            "user_context": user_context or "",
            "user_api_key": user_api_key,
            "primary_area": "",
            "secondary_areas": [],
            "classification_confidence": 0.0,
            "low_confidence_note": "",
            "retrieved_context": "",
            "primary_response": {},
            "primary_agent_name": "",
            "secondary_responses": [],
            "needs_enrichment": False,
            "evaluation_reason": "",
            "citations": [],
            "response": "",
            "agent_used": "",
            "legal_area": "",
            "model_used": "",
            "tokens_used": None,
            "is_multi_area": False,
            "final_response": "",
            "case_phase": "analysis",
            "case_facts": (case_state or {}).get("case_facts") or [],
            "case_pending": [],
            "case_turn_count": (case_state or {}).get("case_turn_count") or 0,
            "case_area_hint": (case_state or {}).get("case_area_hint") or "",
        }

        result = await self.app.ainvoke(initial_state)

        # After analysis, the case is "complete" — caller may discard or keep
        # for audit. We mark phase as such.
        final_case_state = {
            **(case_state or {}),
            "case_phase": "complete",
        }

        return {
            "response": result.get("response", result.get("final_response", "")),
            "agent_used": result.get("agent_used", ""),
            "legal_area": result.get("legal_area", ""),
            "citations": result.get("citations", []),
            "model_used": result.get("model_used", ""),
            "tokens_used": result.get("tokens_used"),
            "is_multi_area": result.get("is_multi_area", False),
            "case_state": final_case_state,
        }


# Singleton
legal_orchestrator = LegalOrchestrator()
