"""Notification routes — list, mark as read, delete, unread count."""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RateLimitBucket, RateLimitGuard, get_current_user
from app.core.database import get_db
from app.models.notification import Notification
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class NotificationOut(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    message: str
    is_read: bool
    action_url: str | None
    extra_data: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    notifications: list[NotificationOut]
    unread_count: int
    total: int


class StatusResponse(BaseModel):
    status: str


class MarkAllReadResponse(BaseModel):
    status: str
    updated: int


class UnreadCountResponse(BaseModel):
    count: int


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="List user notifications",
    description=(
        "Returns paginated notifications for the authenticated user, newest first. "
        "Use `unread_only=true` to filter to unread notifications only."
    ),
)
async def list_notifications(
    unread_only: bool = Query(False, description="Return only unread notifications"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> NotificationListResponse:
    """List notifications for the current user."""
    base_filter = [Notification.user_id == current_user.id]
    if unread_only:
        base_filter.append(Notification.is_read.is_(False))

    # Unread count (always the global unread count, not filtered)
    unread_result = await db.execute(
        select(func.count()).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    )
    unread_count = unread_result.scalar_one()

    # Total matching the current filter
    total_result = await db.execute(
        select(func.count()).where(*base_filter)
    )
    total = total_result.scalar_one()

    # Paginated rows
    offset = (page - 1) * per_page
    rows_result = await db.execute(
        select(Notification)
        .where(*base_filter)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    notifications = rows_result.scalars().all()

    return NotificationListResponse(
        notifications=list(notifications),
        unread_count=unread_count,
        total=total,
    )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="Get unread notification count",
    description="Lightweight endpoint for badge updates. Backed by a partial index — O(1).",
)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> UnreadCountResponse:
    """Return the unread notification count for the current user."""
    result = await db.execute(
        select(func.count()).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    )
    count = result.scalar_one()
    return UnreadCountResponse(count=count)


@router.put(
    "/read-all",
    response_model=MarkAllReadResponse,
    summary="Mark all notifications as read",
)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> MarkAllReadResponse:
    """Mark every unread notification as read for the current user."""
    result = await db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True)
        .returning(Notification.id)
    )
    updated_ids = result.scalars().all()
    return MarkAllReadResponse(status="ok", updated=len(updated_ids))


@router.put(
    "/{notification_id}/read",
    response_model=StatusResponse,
    summary="Mark a notification as read",
)
async def mark_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> StatusResponse:
    """Mark a single notification as read. Returns 404 if not found or not owned by user."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    notification.is_read = True
    await db.flush()
    return StatusResponse(status="ok")


@router.delete(
    "/{notification_id}",
    response_model=StatusResponse,
    summary="Delete a notification",
)
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> StatusResponse:
    """Permanently delete a notification. Returns 404 if not found or not owned by user."""
    result = await db.execute(
        delete(Notification)
        .where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .returning(Notification.id)
    )
    deleted = result.scalar_one_or_none()
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return StatusResponse(status="ok")
