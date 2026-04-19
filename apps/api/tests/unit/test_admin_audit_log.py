"""Unit tests for GET /api/admin/audit-log endpoint — T4.3 RED tests.

Tests call the route handler directly with mocked dependencies.
No real DB, Redis, or auth required.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rbac.models import AuditLog


def make_user():
    from app.models.user import User

    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    return user


def make_audit_entry(**kwargs) -> MagicMock:
    """Mock AuditLog with all fields populated for Pydantic model_validate."""
    defaults = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "action": "role.assign",
        "resource_type": "user_role",
        "resource_id": None,
        "before_state": None,
        "after_state": None,
        "ip_address": None,
        "user_agent": None,
        "created_at": datetime.now(UTC),
    }
    defaults.update(kwargs)
    entry = MagicMock(spec=AuditLog)
    for k, v in defaults.items():
        setattr(entry, k, v)
    return entry


class TestAdminAuditLogEndpoint:
    async def test_returns_audit_log_page(self):
        from app.api.routes.admin import admin_audit_log

        entry = make_audit_entry()
        db = AsyncMock()

        with patch("app.api.routes.admin.AuditService") as mock_cls:
            mock_svc = AsyncMock()
            mock_svc.query_log = AsyncMock(return_value=([entry], 1))
            mock_cls.return_value = mock_svc

            result = await admin_audit_log(
                page=1,
                page_size=20,
                user_id=None,
                action=None,
                resource_type=None,
                date_from=None,
                date_to=None,
                db=db,
                _=make_user(),
            )

        assert result.total == 1
        assert result.page == 1
        assert result.page_size == 20
        assert len(result.items) == 1

    async def test_returns_empty_page_when_no_entries(self):
        from app.api.routes.admin import admin_audit_log

        db = AsyncMock()

        with patch("app.api.routes.admin.AuditService") as mock_cls:
            mock_svc = AsyncMock()
            mock_svc.query_log = AsyncMock(return_value=([], 0))
            mock_cls.return_value = mock_svc

            result = await admin_audit_log(
                page=1,
                page_size=20,
                user_id=None,
                action=None,
                resource_type=None,
                date_from=None,
                date_to=None,
                db=db,
                _=make_user(),
            )

        assert result.total == 0
        assert result.items == []

    async def test_passes_filters_to_audit_service(self):
        from app.api.routes.admin import admin_audit_log

        db = AsyncMock()
        filter_user_id = uuid.uuid4()

        with patch("app.api.routes.admin.AuditService") as mock_cls:
            mock_svc = AsyncMock()
            mock_svc.query_log = AsyncMock(return_value=([], 0))
            mock_cls.return_value = mock_svc

            await admin_audit_log(
                page=2,
                page_size=10,
                user_id=filter_user_id,
                action="role.assign",
                resource_type=None,
                date_from=None,
                date_to=None,
                db=db,
                _=make_user(),
            )

            call_kwargs = mock_svc.query_log.call_args[1]
            assert call_kwargs["page"] == 2
            assert call_kwargs["page_size"] == 10
            filters = call_kwargs["filters"]
            assert filters["user_id"] == filter_user_id
            assert filters["action"] == "role.assign"

    async def test_excludes_none_filters(self):
        from app.api.routes.admin import admin_audit_log

        db = AsyncMock()

        with patch("app.api.routes.admin.AuditService") as mock_cls:
            mock_svc = AsyncMock()
            mock_svc.query_log = AsyncMock(return_value=([], 0))
            mock_cls.return_value = mock_svc

            await admin_audit_log(
                page=1,
                page_size=20,
                user_id=None,
                action=None,
                resource_type=None,
                date_from=None,
                date_to=None,
                db=db,
                _=make_user(),
            )

            filters = mock_svc.query_log.call_args[1]["filters"]
            assert "user_id" not in filters
            assert "action" not in filters
            assert "resource_type" not in filters

    async def test_pagination_reflected_in_response(self):
        from app.api.routes.admin import admin_audit_log

        db = AsyncMock()

        with patch("app.api.routes.admin.AuditService") as mock_cls:
            mock_svc = AsyncMock()
            mock_svc.query_log = AsyncMock(return_value=([], 50))
            mock_cls.return_value = mock_svc

            result = await admin_audit_log(
                page=3,
                page_size=10,
                user_id=None,
                action=None,
                resource_type=None,
                date_from=None,
                date_to=None,
                db=db,
                _=make_user(),
            )

        assert result.page == 3
        assert result.page_size == 10
        assert result.total == 50

    async def test_date_filters_passed_to_service(self):
        from app.api.routes.admin import admin_audit_log

        db = AsyncMock()
        date_from = datetime(2026, 1, 1, tzinfo=UTC)
        date_to = datetime(2026, 12, 31, tzinfo=UTC)

        with patch("app.api.routes.admin.AuditService") as mock_cls:
            mock_svc = AsyncMock()
            mock_svc.query_log = AsyncMock(return_value=([], 0))
            mock_cls.return_value = mock_svc

            await admin_audit_log(
                page=1,
                page_size=20,
                user_id=None,
                action=None,
                resource_type=None,
                date_from=date_from,
                date_to=date_to,
                db=db,
                _=make_user(),
            )

            filters = mock_svc.query_log.call_args[1]["filters"]
            assert filters["date_from"] == date_from
            assert filters["date_to"] == date_to
