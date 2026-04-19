"""Export routes — generate downloadable PDF documents from consultations."""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RateLimitBucket, RateLimitGuard, get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services import conversations as conv_service
from app.services.pdf_service import pdf_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class ConsultationExportRequest(BaseModel):
    """Payload for exporting a single consultation as PDF."""

    query: str
    answer: str
    citations: list[dict] = []
    area: str
    agent_used: str
    model: str
    timestamp: str


class ConversationExportRequest(BaseModel):
    """Payload for exporting an entire conversation as PDF."""

    conversation_id: uuid.UUID


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pdf_response(pdf_bytes: bytes, filename: str) -> StreamingResponse:
    """Wrap bytes in a StreamingResponse suitable for file download."""
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


def _today_str() -> str:
    return datetime.now(UTC).strftime("%Y%m%d")


# ---------------------------------------------------------------------------
# POST /api/export/consultation/pdf
# ---------------------------------------------------------------------------


@router.post("/consultation/pdf")
async def export_consultation_pdf(
    body: ConsultationExportRequest,
    current_user: User = Depends(get_current_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> StreamingResponse:
    """Generate and download a PDF for a single consultation.

    Accepts the raw consultation data (query + answer + metadata) and returns
    a professional PDF document ready for filing or client presentation.
    """
    try:
        pdf_bytes = pdf_service.generate_consultation_pdf(
            query=body.query,
            answer=body.answer,
            citations=body.citations,
            area=body.area,
            agent_used=body.agent_used,
            model=body.model,
            timestamp=body.timestamp,
            user_name=current_user.full_name,
        )
    except Exception:
        logger.exception("PDF generation failed for consultation export")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al generar el PDF. Intenta nuevamente.",
        )

    filename = f"consulta-tukijuris-{_today_str()}.pdf"
    return _pdf_response(pdf_bytes, filename)


# ---------------------------------------------------------------------------
# POST /api/export/conversation/pdf
# ---------------------------------------------------------------------------


@router.post("/conversation/pdf")
async def export_conversation_pdf(
    body: ConversationExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> StreamingResponse:
    """Export an entire saved conversation as a multi-consultation PDF.

    Retrieves the conversation from the database and renders all assistant
    messages (with their corresponding user messages) into a single PDF.
    Only the owner of the conversation can export it.
    """
    # get_conversation_with_messages already filters by user_id — returns None when
    # the conversation does not exist OR belongs to a different user.
    conversation = await conv_service.get_conversation_with_messages(
        db, body.conversation_id, current_user.id
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversacion no encontrada o no tienes permiso para acceder a ella",
        )

    messages = conversation.messages or []

    # Build a combined answer from all assistant turns
    user_queries = [m.content for m in messages if m.role == "user"]
    assistant_responses = [m.content for m in messages if m.role == "assistant"]

    combined_query = "\n\n---\n\n".join(user_queries) if user_queries else "Consulta multiple"
    combined_answer = "\n\n---\n\n".join(assistant_responses) if assistant_responses else "Sin respuestas"

    # Collect citations from all messages
    all_citations: list[dict] = []
    for m in messages:
        if m.role == "assistant" and m.citations:
            if isinstance(m.citations, list):
                all_citations.extend(m.citations)
            elif isinstance(m.citations, dict) and "citations" in m.citations:
                all_citations.extend(m.citations["citations"])

    # Deduplicate citations by title
    seen: set[str] = set()
    unique_citations: list[dict] = []
    for c in all_citations:
        key = c.get("title") or c.get("document") or ""
        if key and key not in seen:
            seen.add(key)
            unique_citations.append(c)

    last_assistant = next(
        (m for m in reversed(messages) if m.role == "assistant"), None
    )
    agent_used = last_assistant.agent_used if last_assistant and last_assistant.agent_used else "TukiJuris"
    area = conversation.legal_area or "general"
    model = conversation.model_used or "N/A"
    timestamp = conversation.created_at.isoformat() if conversation.created_at else datetime.now(UTC).isoformat()

    try:
        pdf_bytes = pdf_service.generate_consultation_pdf(
            query=combined_query,
            answer=combined_answer,
            citations=unique_citations,
            area=area,
            agent_used=agent_used,
            model=model,
            timestamp=timestamp,
            user_name=current_user.full_name,
        )
    except Exception:
        logger.exception("PDF generation failed for conversation export")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al generar el PDF. Intenta nuevamente.",
        )

    filename = f"conversacion-tukijuris-{_today_str()}.pdf"
    return _pdf_response(pdf_bytes, filename)


# ---------------------------------------------------------------------------
# GET /api/export/search-results/pdf
# ---------------------------------------------------------------------------


@router.get("/search-results/pdf")
async def export_search_results_pdf(
    q: str,
    area: str = "general",
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> StreamingResponse:
    """Export document search results as a PDF reference sheet.

    Performs a search and renders the results into a formatted table PDF.
    Useful for saving a snapshot of normativa findings for a case file.
    """
    from app.services.rag import rag_service

    if not q.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El parametro 'q' no puede estar vacio",
        )

    limit = min(limit, 50)

    try:
        results = await rag_service.search_bm25(query=q, limit=limit)
    except Exception:
        logger.exception("Search failed during PDF export")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al realizar la busqueda",
        )

    # Format results as citations list
    citations = [
        {
            "title": r.get("title") or r.get("document") or "Documento",
            "article": r.get("article") or r.get("chunk_text", "")[:120],
        }
        for r in results
    ]

    answer_lines = [f"Resultados para: {q}"]
    if area != "general":
        answer_lines.append(f"Area del derecho: {area.replace('_', ' ').title()}")
    answer_lines.append(f"Total de resultados: {len(results)}")

    try:
        pdf_bytes = pdf_service.generate_consultation_pdf(
            query=q,
            answer="\n\n".join(answer_lines),
            citations=citations,
            area=area,
            agent_used="Buscador de Normativa",
            model="BM25 Search",
            timestamp=datetime.now(UTC).isoformat(),
            user_name=current_user.full_name,
        )
    except Exception:
        logger.exception("PDF generation failed for search export")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al generar el PDF",
        )

    filename = f"busqueda-tukijuris-{_today_str()}.pdf"
    return _pdf_response(pdf_bytes, filename)
