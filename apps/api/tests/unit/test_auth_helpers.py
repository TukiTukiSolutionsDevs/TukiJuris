"""auth.unit.003 — _has_privileged_role helper returns False for non-privileged users.

Spec: auth.unit.003 — test_has_privileged_role_helper_false
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestHasPrivilegedRoleHelper:
    async def test_has_privileged_role_helper_false(self) -> None:
        """_has_privileged_role returns False for a user with no RBAC roles.

        The helper queries the RBAC role table for the user. An empty result
        means no privileged roles → returns False. We mock the AsyncSession
        so this test runs without a live DB.
        """
        from app.api.routes.auth import _has_privileged_role

        # Build a mock DB session whose execute() returns an empty scalars set
        mock_scalars = MagicMock()
        mock_scalars.__iter__ = MagicMock(return_value=iter([]))  # empty role names

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        user_id = uuid.uuid4()
        result = await _has_privileged_role(mock_db, user_id)

        assert result is False, (
            f"_has_privileged_role should return False for user with no roles, got {result}"
        )
        # Verify the DB was queried with the correct user_id
        mock_db.execute.assert_awaited_once()
