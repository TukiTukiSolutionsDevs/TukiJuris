"""Case analysis endpoint — structured legal analysis of a user's situation."""

import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import RateLimitBucket, RateLimitGuard, get_optional_user
from app.config import settings
from app.models.user import User
from app.services.llm_adapter import llm_service
from app.services.rag import rag_service

router = APIRouter(prefix="/analysis", tags=["analysis"])

ANALYSIS_SYSTEM_PROMPT = """Eres un analista jurídico peruano experto. El usuario te describirá una situación 
o caso legal. Tu trabajo es hacer un ANÁLISIS ESTRUCTURADO identificando:

1. **ÁREAS DEL DERECHO INVOLUCRADAS**: Qué ramas del derecho peruano aplican al caso.
2. **NORMATIVA APLICABLE**: Las leyes, códigos y normas específicas que regulan la situación.
3. **DERECHOS Y OBLIGACIONES**: Qué derechos tiene la persona y qué obligaciones enfrenta.
4. **POSIBLES VÍAS LEGALES**: Qué acciones legales puede tomar (demanda, denuncia, recurso, etc.).
5. **PLAZOS IMPORTANTES**: Plazos de prescripción, caducidad, términos procesales relevantes.
6. **RIESGOS Y CONSIDERACIONES**: Aspectos que podrían complicar el caso.
7. **RECOMENDACIÓN GENERAL**: Orientación sobre los pasos a seguir.

REGLAS:
- Basa tu análisis EXCLUSIVAMENTE en el derecho peruano.
- Cita artículos, leyes y normas específicas.
- Sé claro sobre qué es opinión orientativa vs lo que dice la ley textualmente.
- Incluye el disclaimer de que esto no es asesoría legal.

Usa la normativa proporcionada como contexto para fundamentar tu análisis."""


class AnalysisRequest(BaseModel):
    case_description: str
    focus_areas: list[str] | None = None  # Optional: limit analysis to specific areas


class AnalysisResponse(BaseModel):
    analysis: str
    areas_identified: list[str]
    model_used: str
    latency_ms: int


@router.post("/case", response_model=AnalysisResponse)
async def analyze_case(
    body: AnalysisRequest,
    current_user: User | None = Depends(get_optional_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """
    Perform a structured legal analysis of a case description.
    Returns a comprehensive analysis with applicable norms and recommendations.
    Anonymous access is allowed; authenticated users enable usage tracking.
    """
    start = time.time()

    # Retrieve relevant context from multiple areas
    context_parts = []
    areas_found = set()

    # Search across all areas for relevant content
    results = await rag_service.search_bm25(query=body.case_description, limit=10)
    for r in results:
        areas_found.add(r["legal_area"])

    # Get context
    context = await rag_service.retrieve(query=body.case_description, limit=10)

    messages = [
        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
    ]
    if context:
        messages.append({
            "role": "system",
            "content": f"NORMATIVA PERUANA RELEVANTE PARA ESTE CASO:\n\n{context}",
        })

    messages.append({
        "role": "user",
        "content": f"Analiza la siguiente situación legal:\n\n{body.case_description}",
    })

    result = await llm_service.completion(
        messages=messages,
        model=settings.default_llm_model,
        max_tokens=6000,
        temperature=0.1,
    )

    latency_ms = int((time.time() - start) * 1000)

    return AnalysisResponse(
        analysis=result["content"],
        areas_identified=sorted(areas_found),
        model_used=result["model"],
        latency_ms=latency_ms,
    )
