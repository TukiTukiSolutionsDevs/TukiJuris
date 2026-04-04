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

import json
import logging
import re
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.domain_agents import AGENT_REGISTRY, get_agent
from app.config import settings
from app.services.llm_adapter import llm_service
from app.services.rag import rag_service

logger = logging.getLogger(__name__)

# Legal areas the orchestrator can route to
LEGAL_AREAS = [
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
- penal: delitos, penas, robo, hurto, estafa, homicidio, violación, faltas, Código Penal, fiscalía, prisión, denuncia penal, sentencia penal, proceso penal
- laboral: trabajo, despido, CTS, gratificaciones, vacaciones, remuneración, empleador, trabajador, contrato de trabajo, SUNAFIL, beneficios sociales
- civil: contratos civiles, propiedad, herencia, sucesiones, familia, divorcio, obligaciones, responsabilidad civil, prescripción civil, Código Civil
- tributario: impuestos, SUNAT, IGV, renta, UIT, tributos, declaración jurada, multa tributaria, RUC, factura, Código Tributario
- constitucional: derechos fundamentales, amparo, habeas corpus, Tribunal Constitucional, inconstitucionalidad, Constitución
- administrativo: trámite, procedimiento administrativo, silencio administrativo, TUPA, funcionario público, contrataciones del Estado, OSCE
- corporativo: empresa, sociedad, accionistas, directorio, junta general, fusión, escisión, Ley General de Sociedades
- registral: SUNARP, registros públicos, inscripción, partida registral, propiedad registral
- competencia: INDECOPI, marcas, patentes, consumidor, competencia desleal, propiedad intelectual
- compliance: datos personales, lavado de activos, anticorrupción, programa de cumplimiento
- comercio_exterior: aduanas, importación, exportación, TLC, aranceles, MINCETUR

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
    )

    # Parse classification response
    content = llm_result["content"]
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
            user_api_key=state.get("user_api_key"),  # BYOK
        )
        return {
            "primary_response": {
                "response": result["content"],
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
    query = state["query"]
    primary_response = state.get("primary_response", {})
    primary_text = primary_response.get("response", "") if isinstance(primary_response, dict) else str(primary_response)
    primary_area = state.get("primary_area", "")
    user_api_key = state.get("user_api_key")

    eval_prompt = f"""Eres el orquestador jurídico de TukiJuris — un general que supervisa un equipo de abogados especializados.

Acabas de recibir la respuesta del abogado de {primary_area}. Ahora debes EVALUAR si esta respuesta es suficiente o si necesitas consultar a otro especialista.

CONSULTA ORIGINAL DEL USUARIO:
{query}

RESPUESTA DEL ABOGADO DE {primary_area.upper()}:
{primary_text[:2000]}

PREGUNTA: ¿Esta respuesta cubre completamente la consulta del usuario, o se necesita la opinión de otro especialista?

Responde en EXACTAMENTE este formato JSON:
{{"needs_more": true/false, "additional_areas": ["area1", "area2"], "reason": "explicación breve"}}

REGLAS:
- needs_more = true SOLO si la respuesta claramente necesita otra perspectiva legal
- additional_areas debe ser de: {', '.join(LEGAL_AREAS)}
- NO incluyas el área primaria ({primary_area}) en additional_areas
- Máximo 2 áreas adicionales
- Si la respuesta ya es completa y coherente, needs_more = false
- Ejemplos de cuándo needs_more=true:
  * El usuario pregunta sobre costos/impuestos pero solo recibió respuesta civil
  * El caso mezcla laboral con penal (ej: acoso laboral que es delito)
  * Se mencionan trámites administrativos pero solo respondió el civilista
  * El usuario pregunta por una empresa y también hay implicancias tributarias"""

    try:
        result = await llm_service.completion(
            messages=[{"role": "user", "content": eval_prompt}],
            model=state.get("model") or settings.default_llm_model,
            temperature=0.0,
            max_tokens=300,
            user_api_key=user_api_key,
        )
        content = result.get("content", "")

        # Parse JSON response — look for the JSON object in the response
        json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                needs_more = parsed.get("needs_more", False)
                additional = parsed.get("additional_areas", [])
                reason = parsed.get("reason", "")

                # Validate: only known areas, never the primary area, max 2
                valid_additional = [
                    a for a in additional
                    if a in LEGAL_AREAS and a != primary_area
                ][:2]

                logger.info(
                    f"Evaluation: needs_more={needs_more}, areas={valid_additional}, reason={reason[:100]}"
                )

                return {
                    "needs_enrichment": needs_more and len(valid_additional) > 0,
                    "secondary_areas": valid_additional,
                    "evaluation_reason": reason,
                }
            except (json.JSONDecodeError, KeyError) as parse_err:
                logger.warning(f"Evaluation JSON parse failed: {parse_err} | raw: {content[:200]}")
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
    Secondary agents receive RAG context for their specific area.
    """
    secondary_responses = []
    for area in state.get("secondary_areas", [])[:2]:  # Max 2 secondary agents
        agent = get_agent(area)
        if agent:
            enrichment_query = (
                f"En relación a la siguiente consulta, proporciona tu análisis desde la perspectiva "
                f"del {agent.name}. Sé específico con la normativa aplicable.\n\n"
                f"Consulta: {state['query']}"
            )

            # Retrieve RAG context for this secondary area
            secondary_context = ""
            try:
                secondary_context = await rag_service.retrieve(
                    query=state["query"],
                    legal_area=area,
                    limit=4,
                )
            except Exception as exc:
                logger.warning(f"RAG retrieval failed for secondary area={area}: {exc}")

            result = await agent.process(
                query=enrichment_query,
                context=secondary_context,
                model=state.get("model"),
                conversation_history=state.get("conversation_history", []),
                user_api_key=state.get("user_api_key"),
            )
            secondary_responses.append(result)

    return {"secondary_responses": secondary_responses}


async def synthesize_response(state: OrchestratorState) -> dict[str, Any]:
    """
    Node 6a: The orchestrator synthesizes all agent responses into ONE coherent answer.

    Acts as the 'general' making the final decision after consulting all specialists.
    Used when needs_enrichment=True (multi-area responses).
    """
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
    ) -> dict:
        """
        Process a legal query through the full deliberative orchestration pipeline.

        Args:
            query: The user's legal question (clean — no memory prepended)
            model: Optional model override
            legal_area_hint: Optional hint for legal area routing
            conversation_history: Prior messages for context continuity
            user_context: User memory context — injected at agent level only,
                          NOT at classification
            user_api_key: BYOK — the user's own LLM provider key.
                Internal operations (classification, evaluation) use platform keys.
                Only agent responses use this key.

        Returns:
            dict with response, agent_used, legal_area, citations, model_used, is_multi_area
        """
        initial_state: OrchestratorState = {
            "query": query,
            "model": model,
            "legal_area_hint": legal_area_hint,
            "conversation_history": conversation_history or [],
            "user_context": user_context or "",
            "user_api_key": user_api_key,  # BYOK
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
        }

        result = await self.app.ainvoke(initial_state)

        return {
            "response": result.get("response", result.get("final_response", "")),
            "agent_used": result.get("agent_used", ""),
            "legal_area": result.get("legal_area", ""),
            "citations": result.get("citations", []),
            "model_used": result.get("model_used", ""),
            "tokens_used": result.get("tokens_used"),
            "is_multi_area": result.get("is_multi_area", False),
        }


# Singleton
legal_orchestrator = LegalOrchestrator()
