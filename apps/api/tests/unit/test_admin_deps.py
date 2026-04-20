"""Unit tests for require_admin FastAPI dependency.

Spec ID: admin-rbac.unit.001
Layer: unit — no DB, no Redis, no auth required.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.user import User


def _make_user(*, is_admin: bool) -> MagicMock:
    user = MagicMock(spec=User)
    user.is_admin = is_admin
    return user


@pytest.mark.asyncio
async def test_require_admin_passes_for_admin_user():
    """require_admin returns the user unchanged when is_admin=True."""
    from app.api.deps import require_admin

    user = _make_user(is_admin=True)
    result = await require_admin(current_user=user)
    assert result is user


@pytest.mark.asyncio
async def test_require_admin_raises_403_for_non_admin():
    """require_admin raises HTTPException(403) when is_admin=False."""
    from app.api.deps import require_admin

    user = _make_user(is_admin=False)
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(current_user=user)
    assert exc_info.value.status_code == 403
