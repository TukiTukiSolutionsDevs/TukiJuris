"""Conversation persistence — save and retrieve chat history."""

import secrets
import string
import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, Message


def _generate_share_id(length: int = 12) -> str:
    """Generate a random alphanumeric share ID."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def create_conversation(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str | None = None,
    legal_area: str | None = None,
    model_used: str = "gpt-4o-mini",
) -> Conversation:
    """Create a new conversation."""
    conv = Conversation(
        user_id=user_id,
        title=title,
        legal_area=legal_area,
        model_used=model_used,
    )
    db.add(conv)
    await db.flush()
    return conv


async def add_message(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    role: str,
    content: str,
    agent_used: str | None = None,
    legal_area: str | None = None,
    model: str | None = None,
    citations: dict | None = None,
    tokens_used: int | None = None,
    latency_ms: int | None = None,
) -> Message:
    """Add a message to a conversation."""
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        agent_used=agent_used,
        legal_area=legal_area,
        model=model,
        citations=citations,
        tokens_used=tokens_used,
        latency_ms=latency_ms,
    )
    db.add(msg)
    await db.flush()
    return msg


async def get_user_conversations(
    db: AsyncSession,
    user_id: uuid.UUID,
    status: str = "active",
    limit: int = 30,
) -> list[Conversation]:
    """Get recent conversations for a user, filtered by status.

    status values:
      - "active"    -> not archived (default)
      - "archived"  -> only archived
      - "pinned"    -> only pinned (and not archived)
      - "all"       -> everything
    """
    stmt = select(Conversation).where(Conversation.user_id == user_id)

    if status == "active":
        stmt = stmt.where(Conversation.is_archived.is_(False))
    elif status == "archived":
        stmt = stmt.where(Conversation.is_archived.is_(True))
    elif status == "pinned":
        stmt = stmt.where(
            Conversation.is_pinned.is_(True),
            Conversation.is_archived.is_(False),
        )
    # "all" -> no extra filter

    # Pinned conversations always float to the top within any status query
    stmt = stmt.order_by(
        Conversation.is_pinned.desc(),
        Conversation.updated_at.desc(),
    ).limit(limit)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_conversation_with_messages(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Conversation | None:
    """Get a conversation with all its messages."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def auto_title_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    first_message: str,
) -> None:
    """Set conversation title from first user message (truncated)."""
    title = first_message[:80].strip()
    if len(first_message) > 80:
        title += "..."
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(title=title)
    )


async def update_conversation_area(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    legal_area: str,
) -> None:
    """Update the legal area of a conversation."""
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(legal_area=legal_area)
    )


async def rename_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str,
) -> Conversation | None:
    """Rename a conversation. Returns the updated object or None if not found."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        return None
    conv.title = title
    await db.flush()
    return conv


async def toggle_pin(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Conversation | None:
    """Toggle the pinned state of a conversation."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        return None
    conv.is_pinned = not conv.is_pinned
    await db.flush()
    return conv


async def toggle_archive(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Conversation | None:
    """Toggle the archived state of a conversation."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        return None
    conv.is_archived = not conv.is_archived
    await db.flush()
    return conv


async def hard_delete_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """Permanently delete a conversation (cascades to messages). Returns True if deleted."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        return False
    await db.delete(conv)
    await db.flush()
    return True


async def generate_share_link(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Conversation | None:
    """Create (or return existing) share_id for a conversation."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        return None

    if not conv.share_id:
        # Ensure uniqueness — try up to 5 times (collision probability is negligible)
        for _ in range(5):
            candidate = _generate_share_id()
            existing = await db.execute(
                select(Conversation).where(Conversation.share_id == candidate)
            )
            if not existing.scalar_one_or_none():
                conv.share_id = candidate
                break

    conv.is_shared = True
    await db.flush()
    return conv


async def get_shared_conversation(
    db: AsyncSession,
    share_id: str,
) -> Conversation | None:
    """Fetch a publicly shared conversation by its share_id (no auth required)."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.share_id == share_id,
            Conversation.is_shared.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def get_conversation_message_count(
    db: AsyncSession,
    conversation_id: uuid.UUID,
) -> int:
    """Return the number of messages in a conversation (for history page cards)."""
    from sqlalchemy import func

    result = await db.execute(
        select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
    )
    return result.scalar_one() or 0
