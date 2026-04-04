"""Conversation history routes — list, get, rename, pin, archive, share, delete."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.tag import ConversationTag, Folder, Tag
from app.models.user import User
from app.services import conversations as conv_service

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TagSummary(BaseModel):
    id: uuid.UUID
    name: str
    color: str

    model_config = {"from_attributes": True}


class ConversationSummary(BaseModel):
    id: uuid.UUID
    title: str | None
    legal_area: str | None
    model_used: str
    is_pinned: bool
    is_archived: bool
    is_shared: bool
    folder_id: uuid.UUID | None
    folder_name: str | None
    tags: list[TagSummary]
    message_count: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    agent_used: str | None
    citations: list[dict] | dict | None
    latency_ms: int | None
    created_at: str

    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    id: uuid.UUID
    title: str | None
    legal_area: str | None
    is_pinned: bool
    is_archived: bool
    is_shared: bool
    messages: list[MessageOut]

    model_config = {"from_attributes": True}


class RenameBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)


class ShareResponse(BaseModel):
    share_id: str
    url: str


class SharedConversationOut(BaseModel):
    id: uuid.UUID
    title: str | None
    legal_area: str | None
    messages: list[MessageOut]


# ---------------------------------------------------------------------------
# List & Get
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[ConversationSummary])
async def list_conversations(
    status: str = Query("active", description="active | archived | pinned | all"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List conversations for the authenticated user, filtered by status.

    - **active** (default): non-archived conversations, pinned ones first.
    - **archived**: only archived conversations.
    - **pinned**: only pinned (and not archived) conversations.
    - **all**: every conversation regardless of state.
    """
    valid_statuses = {"active", "archived", "pinned", "all"}
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"status must be one of: {valid_statuses}")

    convs = await conv_service.get_user_conversations(db, user.id, status=status)

    result = []
    for c in convs:
        count = await conv_service.get_conversation_message_count(db, c.id)

        # Fetch tags for this conversation
        tags_result = await db.execute(
            select(Tag)
            .join(ConversationTag, ConversationTag.tag_id == Tag.id)
            .where(ConversationTag.conversation_id == c.id)
            .order_by(Tag.name)
        )
        tags = tags_result.scalars().all()

        # Fetch folder name if assigned
        folder_name: str | None = None
        if c.folder_id:
            folder_result = await db.execute(
                select(Folder).where(Folder.id == c.folder_id)
            )
            folder = folder_result.scalar_one_or_none()
            folder_name = folder.name if folder else None

        result.append(
            ConversationSummary(
                id=c.id,
                title=c.title,
                legal_area=c.legal_area,
                model_used=c.model_used,
                is_pinned=c.is_pinned,
                is_archived=c.is_archived,
                is_shared=c.is_shared,
                folder_id=c.folder_id,
                folder_name=folder_name,
                tags=[TagSummary(id=t.id, name=t.name, color=t.color) for t in tags],
                message_count=count,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
        )
    return result


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with all its messages."""
    conv = await conv_service.get_conversation_with_messages(db, conversation_id, user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        legal_area=conv.legal_area,
        is_pinned=conv.is_pinned,
        is_archived=conv.is_archived,
        is_shared=conv.is_shared,
        messages=[
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                agent_used=m.agent_used,
                citations=m.citations,
                latency_ms=m.latency_ms,
                created_at=m.created_at.isoformat(),
            )
            for m in sorted(conv.messages, key=lambda x: x.created_at)
        ],
    )


# ---------------------------------------------------------------------------
# Organization actions
# ---------------------------------------------------------------------------


@router.put("/{conversation_id}/rename", response_model=ConversationSummary)
async def rename_conversation(
    conversation_id: uuid.UUID,
    body: RenameBody,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rename a conversation."""
    conv = await conv_service.rename_conversation(db, conversation_id, user.id, body.title)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")
    await db.commit()
    count = await conv_service.get_conversation_message_count(db, conv.id)
    return ConversationSummary(
        id=conv.id,
        title=conv.title,
        legal_area=conv.legal_area,
        model_used=conv.model_used,
        is_pinned=conv.is_pinned,
        is_archived=conv.is_archived,
        is_shared=conv.is_shared,
        folder_id=conv.folder_id,
        folder_name=None,
        tags=[],
        message_count=count,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
    )


@router.put("/{conversation_id}/pin", response_model=ConversationSummary)
async def toggle_pin(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle pin state. Pinned conversations appear at the top of the list."""
    conv = await conv_service.toggle_pin(db, conversation_id, user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")
    await db.commit()
    count = await conv_service.get_conversation_message_count(db, conv.id)
    return ConversationSummary(
        id=conv.id,
        title=conv.title,
        legal_area=conv.legal_area,
        model_used=conv.model_used,
        is_pinned=conv.is_pinned,
        is_archived=conv.is_archived,
        is_shared=conv.is_shared,
        folder_id=conv.folder_id,
        folder_name=None,
        tags=[],
        message_count=count,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
    )


@router.put("/{conversation_id}/archive", response_model=ConversationSummary)
async def toggle_archive(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle archive state. Archived conversations are hidden from the main list."""
    conv = await conv_service.toggle_archive(db, conversation_id, user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")
    await db.commit()
    count = await conv_service.get_conversation_message_count(db, conv.id)
    return ConversationSummary(
        id=conv.id,
        title=conv.title,
        legal_area=conv.legal_area,
        model_used=conv.model_used,
        is_pinned=conv.is_pinned,
        is_archived=conv.is_archived,
        is_shared=conv.is_shared,
        folder_id=conv.folder_id,
        folder_name=None,
        tags=[],
        message_count=count,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
    )


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a conversation and all its messages."""
    deleted = await conv_service.hard_delete_conversation(db, conversation_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")
    await db.commit()


# ---------------------------------------------------------------------------
# Sharing
# ---------------------------------------------------------------------------


@router.post("/{conversation_id}/share", response_model=ShareResponse)
async def share_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate (or return existing) a public shareable link for this conversation."""
    conv = await conv_service.generate_share_link(db, conversation_id, user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")
    await db.commit()

    base_url = settings.app_base_url
    return ShareResponse(
        share_id=conv.share_id,
        url=f"{base_url}/compartido/{conv.share_id}",
    )
