"""Tags routes — CRUD for conversation tags and tag assignments."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import RateLimitBucket, RateLimitGuard, get_current_user
from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.tag import ConversationTag, Tag
from app.models.user import User

router = APIRouter(tags=["tags"])

TAG_COLOR_PRESETS = [
    "#3b82f6",  # blue
    "#ef4444",  # red
    "#22c55e",  # green
    "#f59e0b",  # amber
    "#8b5cf6",  # violet
    "#ec4899",  # pink
    "#06b6d4",  # cyan
    "#f97316",  # orange
]
MAX_TAGS_PER_USER = 20


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TagOut(BaseModel):
    id: uuid.UUID
    name: str
    color: str
    created_at: str

    model_config = {"from_attributes": True}


class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(default="#3b82f6", max_length=7)


class TagUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    color: str | None = Field(None, max_length=7)


# ---------------------------------------------------------------------------
# Tag CRUD
# ---------------------------------------------------------------------------


@router.get("/tags/", response_model=list[TagOut])
async def list_tags(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
):
    """List all tags for the authenticated user."""
    result = await db.execute(
        select(Tag)
        .where(Tag.user_id == user.id)
        .order_by(Tag.name)
    )
    tags = result.scalars().all()
    return [
        TagOut(
            id=t.id,
            name=t.name,
            color=t.color,
            created_at=t.created_at.isoformat(),
        )
        for t in tags
    ]


@router.post("/tags/", response_model=TagOut, status_code=201)
async def create_tag(
    body: TagCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """Create a new tag. Max 20 tags per user."""
    # Enforce limit
    count_result = await db.execute(
        select(func.count(Tag.id)).where(Tag.user_id == user.id)
    )
    tag_count = count_result.scalar_one() or 0
    if tag_count >= MAX_TAGS_PER_USER:
        raise HTTPException(
            status_code=400,
            detail=f"Maximo {MAX_TAGS_PER_USER} etiquetas por usuario",
        )

    # Check duplicate name
    existing = await db.execute(
        select(Tag).where(Tag.user_id == user.id, Tag.name == body.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe una etiqueta con ese nombre")

    tag = Tag(user_id=user.id, name=body.name, color=body.color)
    db.add(tag)
    await db.flush()
    await db.commit()
    await db.refresh(tag)

    return TagOut(
        id=tag.id,
        name=tag.name,
        color=tag.color,
        created_at=tag.created_at.isoformat(),
    )


@router.put("/tags/{tag_id}", response_model=TagOut)
async def update_tag(
    tag_id: uuid.UUID,
    body: TagUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """Update a tag's name or color."""
    result = await db.execute(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == user.id)
    )
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")

    if body.name is not None:
        # Check duplicate name (excluding itself)
        dup = await db.execute(
            select(Tag).where(
                Tag.user_id == user.id,
                Tag.name == body.name,
                Tag.id != tag_id,
            )
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Ya existe una etiqueta con ese nombre")
        tag.name = body.name

    if body.color is not None:
        tag.color = body.color

    await db.flush()
    await db.commit()
    await db.refresh(tag)

    return TagOut(
        id=tag.id,
        name=tag.name,
        color=tag.color,
        created_at=tag.created_at.isoformat(),
    )


@router.delete("/tags/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """Delete a tag. Removes all conversation_tag associations via cascade."""
    result = await db.execute(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == user.id)
    )
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")

    await db.delete(tag)
    await db.commit()


# ---------------------------------------------------------------------------
# Tag assignment to conversations
# ---------------------------------------------------------------------------


@router.get("/conversations/{conversation_id}/tags", response_model=list[TagOut])
async def list_conversation_tags(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
):
    """List all tags assigned to a conversation."""
    # Verify conversation ownership
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    if not conv_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    result = await db.execute(
        select(Tag)
        .join(ConversationTag, ConversationTag.tag_id == Tag.id)
        .where(ConversationTag.conversation_id == conversation_id)
        .order_by(Tag.name)
    )
    tags = result.scalars().all()

    return [
        TagOut(
            id=t.id,
            name=t.name,
            color=t.color,
            created_at=t.created_at.isoformat(),
        )
        for t in tags
    ]


@router.post("/conversations/{conversation_id}/tags/{tag_id}", status_code=201)
async def assign_tag_to_conversation(
    conversation_id: uuid.UUID,
    tag_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """Assign a tag to a conversation."""
    # Verify conversation ownership
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    if not conv_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    # Verify tag ownership
    tag_result = await db.execute(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == user.id)
    )
    if not tag_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")

    # Check if already assigned
    existing = await db.execute(
        select(ConversationTag).where(
            ConversationTag.conversation_id == conversation_id,
            ConversationTag.tag_id == tag_id,
        )
    )
    if existing.scalar_one_or_none():
        return {"detail": "Etiqueta ya asignada"}

    ct = ConversationTag(conversation_id=conversation_id, tag_id=tag_id)
    db.add(ct)
    await db.flush()
    await db.commit()

    return {"detail": "Etiqueta asignada"}


@router.delete("/conversations/{conversation_id}/tags/{tag_id}", status_code=204)
async def remove_tag_from_conversation(
    conversation_id: uuid.UUID,
    tag_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """Remove a tag from a conversation."""
    # Verify conversation ownership
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    if not conv_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    result = await db.execute(
        select(ConversationTag).where(
            ConversationTag.conversation_id == conversation_id,
            ConversationTag.tag_id == tag_id,
        )
    )
    ct = result.scalar_one_or_none()
    if not ct:
        raise HTTPException(status_code=404, detail="Asignacion no encontrada")

    await db.delete(ct)
    await db.commit()
