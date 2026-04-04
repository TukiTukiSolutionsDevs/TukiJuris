"""Feedback routes — thumbs up/down on AI responses."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_optional_user
from app.core.database import get_db
from app.models.conversation import Message
from app.models.user import User

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    message_id: uuid.UUID
    feedback: str  # "thumbs_up" or "thumbs_down"
    comment: str | None = None


class FeedbackResponse(BaseModel):
    status: str
    message_id: uuid.UUID
    feedback: str


@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(
    body: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit feedback on an AI response (thumbs up/down). Requires authentication."""
    if body.feedback not in ("thumbs_up", "thumbs_down"):
        return FeedbackResponse(
            status="error", message_id=body.message_id, feedback="invalid"
        )

    await db.execute(
        update(Message)
        .where(Message.id == body.message_id)
        .values(feedback=body.feedback)
    )

    return FeedbackResponse(
        status="ok", message_id=body.message_id, feedback=body.feedback
    )


@router.get("/stats")
async def feedback_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """Get aggregated feedback statistics. Public endpoint, optional auth."""
    from sqlalchemy import func, select

    total = await db.execute(
        select(func.count(Message.id)).where(Message.feedback.isnot(None))
    )
    positive = await db.execute(
        select(func.count(Message.id)).where(Message.feedback == "thumbs_up")
    )
    negative = await db.execute(
        select(func.count(Message.id)).where(Message.feedback == "thumbs_down")
    )

    total_count = total.scalar() or 0
    pos_count = positive.scalar() or 0
    neg_count = negative.scalar() or 0

    return {
        "total_feedback": total_count,
        "thumbs_up": pos_count,
        "thumbs_down": neg_count,
        "satisfaction_rate": round(pos_count / total_count * 100, 1) if total_count > 0 else None,
    }
