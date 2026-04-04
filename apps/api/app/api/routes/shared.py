"""Public shared conversation route — no authentication required."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import conversations as conv_service

router = APIRouter(prefix="/shared", tags=["shared"])


class MessageOut(BaseModel):
    role: str
    content: str
    agent_used: str | None
    created_at: str

    model_config = {"from_attributes": True}


class SharedConversationOut(BaseModel):
    title: str | None
    legal_area: str | None
    messages: list[MessageOut]


@router.get("/{share_id}", response_model=SharedConversationOut)
async def get_shared_conversation(
    share_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return a publicly shared conversation. No authentication required — read-only.

    The share_id is a 12-character alphanumeric string generated when the owner
    calls POST /api/conversations/{id}/share.
    """
    conv = await conv_service.get_shared_conversation(db, share_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversacion compartida no encontrada")

    return SharedConversationOut(
        title=conv.title,
        legal_area=conv.legal_area,
        messages=[
            MessageOut(
                role=m.role,
                content=m.content,
                agent_used=m.agent_used,
                created_at=m.created_at.isoformat(),
            )
            for m in sorted(conv.messages, key=lambda x: x.created_at)
        ],
    )
