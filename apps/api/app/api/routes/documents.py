"""Document search and browsing routes."""

from fastapi import APIRouter, Depends, Query
from app.api.deps import RateLimitBucket, RateLimitGuard
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.document import Document, DocumentChunk
from app.services.rag import rag_service

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentSummary(BaseModel):
    id: str
    title: str
    document_type: str
    document_number: str | None
    legal_area: str
    hierarchy: str | None
    source: str
    chunk_count: int | None = None

    model_config = {"from_attributes": True}


class SearchResult(BaseModel):
    article_number: str | None
    content: str
    legal_area: str
    section_path: str | None
    document_title: str
    document_number: str | None
    score: float


class KBStats(BaseModel):
    total_documents: int
    total_chunks: int
    chunks_by_area: dict[str, int]


@router.get("/", response_model=list[DocumentSummary])
async def list_documents(
    area: str | None = None,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
):
    """List all documents in the knowledge base, optionally filtered by area."""
    query = select(Document).order_by(Document.legal_area, Document.title)
    if area:
        query = query.where(Document.legal_area == area)

    result = await db.execute(query)
    docs = result.scalars().all()

    return [
        DocumentSummary(
            id=str(d.id),
            title=d.title,
            document_type=d.document_type,
            document_number=d.document_number,
            legal_area=d.legal_area,
            hierarchy=d.hierarchy,
            source=d.source,
        )
        for d in docs
    ]


@router.get("/search", response_model=list[SearchResult])
async def search_documents(
    q: str = Query(..., min_length=2, description="Texto a buscar"),
    area: str | None = Query(None, description="Filtrar por area legal"),
    limit: int = Query(10, ge=1, le=50),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
):
    """
    Search the legal knowledge base using full-text search.
    Returns matching document chunks ranked by relevance.
    """
    results = await rag_service.search_bm25(query=q, legal_area=area, limit=limit)

    return [
        SearchResult(
            article_number=r.get("article_number"),
            content=r["content"],
            legal_area=r["legal_area"],
            section_path=r.get("section_path"),
            document_title=r["document_title"],
            document_number=r.get("document_number"),
            score=float(r.get("score", 0)),
        )
        for r in results
    ]


@router.get("/stats", response_model=KBStats)
async def knowledge_base_stats(
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
):
    """Get knowledge base statistics."""
    stats = await rag_service.get_stats()
    return KBStats(**stats)


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
):
    """Get all chunks (articles) for a specific document."""
    import uuid as _uuid

    try:
        doc_uuid = _uuid.UUID(document_id)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="ID de documento inválido")

    # Get document info
    doc_result = await db.execute(select(Document).where(Document.id == doc_uuid))
    doc = doc_result.scalar_one_or_none()
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Get chunks ordered
    chunks_result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == doc_uuid)
        .order_by(DocumentChunk.chunk_index)
    )
    chunks = chunks_result.scalars().all()

    return {
        "document": {
            "id": str(doc.id),
            "title": doc.title,
            "document_type": doc.document_type,
            "document_number": doc.document_number,
            "legal_area": doc.legal_area,
            "source": doc.source,
        },
        "chunks": [
            {
                "id": str(c.id),
                "article_number": c.article_number,
                "section_path": c.section_path,
                "content": c.content,
            }
            for c in chunks
        ],
        "total_chunks": len(chunks),
    }
