"""Upload route — document upload for chat context analysis."""

import logging
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RateLimitBucket, RateLimitGuard, get_current_user, get_db
from app.models.uploaded_document import UploadedDocument
from app.models.user import User
from app.services import upload_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class UploadedDocumentListItem(BaseModel):
    """Safe public representation of an uploaded document.

    Explicitly excludes storage_path and extracted_text (private/sensitive).
    """

    id: str
    filename: str
    file_type: str
    file_size: int
    page_count: int | None
    conversation_id: str | None
    created_at: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[UploadedDocumentListItem])
async def list_uploaded_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> list[UploadedDocumentListItem]:
    """List all uploaded documents for the authenticated user (newest first)."""
    result = await db.execute(
        select(UploadedDocument)
        .where(UploadedDocument.user_id == current_user.id)
        .order_by(UploadedDocument.created_at.desc())
    )
    docs = result.scalars().all()
    return [
        UploadedDocumentListItem(
            id=str(doc.id),
            filename=doc.original_filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            page_count=doc.page_count,
            conversation_id=str(doc.conversation_id) if doc.conversation_id else None,
            created_at=doc.created_at.isoformat(),
        )
        for doc in docs
    ]


@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> dict:
    """Upload a document for analysis in chat."""
    if not file.filename:
        raise HTTPException(400, "No se proporcionó un archivo")

    content = await file.read()

    try:
        storage_path, file_type = await upload_service.save_file(
            content, file.filename, file.content_type or ""
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    extracted_text, page_count = await upload_service.extract_text(storage_path, file_type)

    conv_uuid = uuid.UUID(conversation_id) if conversation_id else None

    doc = UploadedDocument(
        user_id=current_user.id,
        conversation_id=conv_uuid,
        original_filename=file.filename,
        file_type=file_type,
        file_size=len(content),
        storage_path=storage_path,
        extracted_text=extracted_text,
        page_count=page_count,
    )
    db.add(doc)
    await db.flush()

    # Truncate preview for response
    preview = (
        (extracted_text[:500] + "...")
        if extracted_text and len(extracted_text) > 500
        else extracted_text
    )

    return {
        "id": str(doc.id),
        "filename": file.filename,
        "file_type": file_type,
        "file_size": len(content),
        "page_count": page_count,
        "text_preview": preview,
        "extracted_length": len(extracted_text) if extracted_text else 0,
    }


@router.get("/{doc_id}")
async def get_uploaded_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> dict:
    """Get uploaded document details and extracted text."""
    doc = await db.scalar(
        select(UploadedDocument).where(
            UploadedDocument.id == uuid.UUID(doc_id),
            UploadedDocument.user_id == current_user.id,
        )
    )
    if not doc:
        raise HTTPException(404, "Documento no encontrado")

    return {
        "id": str(doc.id),
        "filename": doc.original_filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "page_count": doc.page_count,
        "extracted_text": doc.extracted_text,
        "conversation_id": str(doc.conversation_id) if doc.conversation_id else None,
        "created_at": doc.created_at.isoformat(),
    }


@router.delete("/{doc_id}")
async def delete_uploaded_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> dict:
    """Delete an uploaded document."""
    import os

    doc = await db.scalar(
        select(UploadedDocument).where(
            UploadedDocument.id == uuid.UUID(doc_id),
            UploadedDocument.user_id == current_user.id,
        )
    )
    if not doc:
        raise HTTPException(404, "Documento no encontrado")

    # Delete file from disk
    if os.path.exists(doc.storage_path):
        os.remove(doc.storage_path)

    await db.delete(doc)
    return {"status": "deleted"}
