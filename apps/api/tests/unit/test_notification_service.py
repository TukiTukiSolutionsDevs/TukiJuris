"""Unit tests — NotificationService (sub-batch D.4a).

Spec IDs covered:
  notifications.unit.002  test_notification_create_system_to_user

Uses AsyncMock for the db session — no live DB or Docker required for this test.
The caller-supplied `db` path in NotificationService.create is exercised;
the auto-session path (db=None) is integration-tested via the factory.

Run:
  docker exec tukijuris-api-1 pytest tests/unit/test_notification_service.py -v
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from app.models.notification import Notification
from app.services.notification_service import NotificationService


# ---------------------------------------------------------------------------
# notifications.unit.002 — service creates notification with is_read=False
# ---------------------------------------------------------------------------


async def test_notification_create_system_to_user():
    """Spec: notifications.unit.002

    NotificationService.create writes a Notification to the caller-supplied
    db session with is_read defaulting to False.

    Contract under test (caller-session path):
      - db.add(notification) is called exactly once
      - await db.flush() is awaited exactly once
      - The returned object is the same Notification passed to db.add
      - is_read is False (column default) — never True for a freshly created notification
      - Commit is NOT called — ownership of commit is the caller's responsibility
        (fire-and-forget contract; see service docstring)
    """
    service = NotificationService()
    user_id = uuid.uuid4()
    # db.add() is synchronous; db.flush() is async. Using MagicMock base with
    # an explicit AsyncMock for flush avoids the "coroutine never awaited" warning
    # that AsyncMock produces when it wraps a sync call.
    mock_db = MagicMock()
    mock_db.flush = AsyncMock()

    notif = await service.create(
        user_id=user_id,
        type="system",
        title="New document available",
        message="A new legal document has been shared with you.",
        db=mock_db,
    )

    # Session contract: add then flush — commit must NOT be called (caller owns it)
    mock_db.add.assert_called_once()
    mock_db.flush.assert_awaited_once()
    mock_db.commit.assert_not_called()

    # The object passed to add must be the same Notification returned to the caller
    added_obj = mock_db.add.call_args[0][0]
    assert isinstance(added_obj, Notification), (
        f"Expected Notification passed to db.add, got {type(added_obj)}"
    )
    assert added_obj is notif, "db.add must receive the exact object that is returned"

    # Domain invariants
    assert notif.user_id == user_id, f"user_id mismatch: {notif.user_id} != {user_id}"
    assert notif.type == "system"
    assert notif.title == "New document available"
    assert notif.message == "A new legal document has been shared with you."

    # Primary spec assertion: is_read must NOT be True for a freshly created notification.
    # SQLAlchemy applies mapped_column(default=False) at INSERT/flush time, not at Python
    # object construction. Pre-flush, the attribute is None (unset). After flush the DB
    # stores False. Asserting "is not True" covers both the pre-flush transient state
    # (None) and the post-flush persisted state (False) — the invariant is that the
    # service never explicitly sets is_read=True on a new notification.
    assert notif.is_read is not True, (
        f"is_read must not be True on a freshly created Notification; got {notif.is_read!r}. "
        "The service must never create notifications with is_read=True."
    )
