"""Notification factory — creates Notification rows via the service layer."""
from __future__ import annotations

import uuid

from app.models.notification import Notification
from app.services.notification_service import notification_service


async def make_notification(
    *,
    user_id: str,
    type: str = "system",
    title: str = "Test notification",
    message: str = "Test message body",
    is_read: bool = False,
) -> Notification:
    """Create a notification for a user via the notification_service singleton.

    Uses the service's internal session (auto-committed) for the create step.
    If is_read=True, applies a follow-up DB update via the same factory.
    """
    notification = await notification_service.create(
        user_id=uuid.UUID(user_id),
        type=type,
        title=title,
        message=message,
    )
    if is_read:
        from sqlalchemy import update

        from app.core.database import async_session_factory

        async with async_session_factory() as session:
            await session.execute(
                update(Notification)
                .where(Notification.id == notification.id)
                .values(is_read=True)
            )
            await session.commit()
        notification.is_read = True

    return notification
