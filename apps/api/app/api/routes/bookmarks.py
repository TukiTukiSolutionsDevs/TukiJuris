"""Bookmarks routes — save and retrieve bookmarked messages."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import RateLimitBucket, RateLimitGuard, get_current_user
from app.core.database import get_db
from app.models.conversation import Conversation, Message
from app.models.user import User

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


class BookmarkToggleResponse(BaseModel):
    message_id: uuid.UUID
    is_bookmarked: bool


class BookmarkedMessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    agent_used: str | None
    is_bookmarked: bool
    created_at: str
    conversation_id: uuid.UUID
    conversation_title: str | None
    legal_area: str | None

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[BookmarkedMessageOut])
async def list_bookmarks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
):
    """List all bookmarked messages for the authenticated user, with conversation context."""
    result = await db.execute(
        select(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .options(selectinload(Message.conversation))
        .where(
            Conversation.user_id == user.id,
            Message.is_bookmarked.is_(True),
        )
        .order_by(Message.created_at.desc())
    )
    messages = result.scalars().all()

    return [
        BookmarkedMessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            agent_used=m.agent_used,
            is_bookmarked=m.is_bookmarked,
            created_at=m.created_at.isoformat(),
            conversation_id=m.conversation_id,
            conversation_title=m.conversation.title if m.conversation else None,
            legal_area=m.conversation.legal_area if m.conversation else None,
        )
        for m in messages
    ]


@router.put("/{message_id}", response_model=BookmarkToggleResponse)
async def toggle_bookmark(
    message_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """Toggle bookmark on a message. Only messages from user's own conversations."""
    # Verify message belongs to the user
    result = await db.execute(
        select(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(
            Message.id == message_id,
            Conversation.user_id == user.id,
        )
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")

    new_state = not message.is_bookmarked

    await db.execute(
        update(Message)
        .where(Message.id == message_id)
        .values(is_bookmarked=new_state)
    )
    await db.commit()

    return BookmarkToggleResponse(message_id=message_id, is_bookmarked=new_state)


@router.delete("/{message_id}", response_model=BookmarkToggleResponse)
async def remove_bookmark(
    message_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """Remove bookmark from a message."""
    result = await db.execute(
        select(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(
            Message.id == message_id,
            Conversation.user_id == user.id,
        )
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")

    await db.execute(
        update(Message)
        .where(Message.id == message_id)
        .values(is_bookmarked=False)
    )
    await db.commit()

    return BookmarkToggleResponse(message_id=message_id, is_bookmarked=False)
