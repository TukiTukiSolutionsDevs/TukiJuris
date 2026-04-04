"""
Notification service — create in-app notifications programmatically.

All public methods are fire-and-forget safe: callers should wrap them in
try/except so a notification failure never blocks the main request flow.
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.notification import Notification
from app.models.organization import OrgMembership

logger = logging.getLogger(__name__)


class NotificationService:
    """Service to create notifications stored in the database."""

    async def create(
        self,
        user_id: uuid.UUID,
        type: str,
        title: str,
        message: str,
        action_url: str | None = None,
        metadata: dict | None = None,
        db: AsyncSession | None = None,
    ) -> Notification:
        """Create a notification for a single user.

        If `db` is provided the caller is responsible for committing the
        session.  When omitted a short-lived internal session is used and
        auto-committed.
        """
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            action_url=action_url,
            extra_data=metadata,
        )

        if db is not None:
            db.add(notification)
            await db.flush()
            return notification

        async with async_session_factory() as session:
            session.add(notification)
            await session.commit()
            await session.refresh(notification)

        return notification

    async def create_for_org(
        self,
        org_id: uuid.UUID,
        type: str,
        title: str,
        message: str,
        action_url: str | None = None,
        metadata: dict | None = None,
    ) -> int:
        """Create a notification for every active member of an org.

        Returns the number of notifications created.
        """
        async with async_session_factory() as session:
            result = await session.execute(
                select(OrgMembership.user_id).where(
                    OrgMembership.organization_id == org_id,
                    OrgMembership.is_active.is_(True),
                )
            )
            user_ids = result.scalars().all()

            if not user_ids:
                logger.warning(
                    "NotificationService.create_for_org: no active members for org %s", org_id
                )
                return 0

            notifications = [
                Notification(
                    user_id=uid,
                    type=type,
                    title=title,
                    message=message,
                    action_url=action_url,
                    extra_data=metadata,
                )
                for uid in user_ids
            ]
            session.add_all(notifications)
            await session.commit()

        logger.debug(
            "NotificationService.create_for_org: created %d notifications for org %s",
            len(notifications),
            org_id,
        )
        return len(notifications)

    async def usage_alert(self, org_id: uuid.UUID, used: int, limit: int) -> None:
        """Create usage alert notifications at 80% and 100% thresholds.

        Does nothing when usage is below 80% of the limit.
        Unlimited orgs (limit == -1) are never alerted.
        """
        if limit <= 0:
            return

        pct = int(used / limit * 100)

        if pct >= 100:
            title = "Limite de consultas alcanzado"
            message = f"Tu organizacion ha usado {used}/{limit} consultas este mes."
        elif pct >= 80:
            title = "80% del limite de consultas"
            message = f"Tu organizacion ha usado {used}/{limit} consultas ({pct}%)."
        else:
            return

        await self.create_for_org(
            org_id,
            "usage_alert",
            title,
            message,
            action_url="/billing",
            metadata={"used": used, "limit": limit, "pct": pct},
        )

    async def welcome(self, user_id: uuid.UUID, name: str) -> None:
        """Welcome notification for newly registered users."""
        await self.create(
            user_id,
            "welcome",
            "Bienvenido a TukiJuris!",
            f"Hola {name}, tu cuenta esta lista. Haz tu primera consulta legal.",
            action_url="/",
        )

    async def invite_accepted(
        self, inviter_id: uuid.UUID, invitee_name: str, org_name: str
    ) -> None:
        """Notify the inviter when someone accepts their invitation."""
        await self.create(
            inviter_id,
            "invite",
            f"{invitee_name} se unio a {org_name}",
            f"{invitee_name} acepto tu invitacion a {org_name}.",
            action_url="/organizacion",
        )


# Singleton — mirrors rag_service / usage_service pattern
notification_service = NotificationService()
