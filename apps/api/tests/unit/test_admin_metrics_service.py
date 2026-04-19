"""Unit tests for AdminMetricsService.

Tests are pure: they mock AsyncSession so no DB or Docker is needed.
Run with: docker exec tukijuris-api-1 python -m pytest tests/unit/test_admin_metrics_service.py -v
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.admin_metrics_service import AdminMetricsService
from app.services.plan_service import PlanService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _exec_mock(*row_lists):
    """Return an AsyncMock whose .execute() side_effect yields successive MagicMocks.

    Each element of row_lists is the list of rows that the corresponding
    db.execute() call should return via .mappings().fetchall().
    """
    db = AsyncMock()
    side_effects = []
    for rows in row_lists:
        result = MagicMock()
        result.mappings.return_value.fetchall.return_value = rows
        side_effects.append(result)
    db.execute.side_effect = side_effects
    return db


def _scalar_mock(execute_rows, scalar_value):
    """DB mock where first call is execute (items) and scalar() is the count."""
    db = _exec_mock(execute_rows)
    db.scalar.return_value = scalar_value
    return db


# ---------------------------------------------------------------------------
# compute_revenue
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_compute_revenue_empty_when_no_active_orgs():
    """No active orgs → zeroed snapshot with empty breakdown."""
    db = _exec_mock([])  # empty rows from org query

    service = AdminMetricsService(db=db, plan_service=PlanService())
    snapshot = await service.compute_revenue()

    assert snapshot.source == "canonical_prices"
    assert snapshot.mrr_cents == 0
    assert snapshot.arr_cents == 0
    assert snapshot.breakdown == []


@pytest.mark.asyncio
async def test_compute_revenue_free_plan_contributes_zero():
    """Free orgs are counted in breakdown but add 0 revenue."""
    org_rows = [
        {"plan": "free", "org_id": str(uuid.uuid4()), "seat_count": 1},
        {"plan": "free", "org_id": str(uuid.uuid4()), "seat_count": 1},
    ]
    db = _exec_mock(org_rows)

    service = AdminMetricsService(db=db, plan_service=PlanService())
    snapshot = await service.compute_revenue()

    assert snapshot.mrr_cents == 0
    assert snapshot.arr_cents == 0
    assert len(snapshot.breakdown) == 1
    assert snapshot.breakdown[0].plan == "free"
    assert snapshot.breakdown[0].org_count == 2
    assert snapshot.breakdown[0].revenue_cents == 0


@pytest.mark.asyncio
async def test_compute_revenue_pro_plan_flat():
    """Pro plan: flat S/ 70.00 (7000 cents) per org regardless of seat count."""
    org_rows = [
        {"plan": "pro", "org_id": str(uuid.uuid4()), "seat_count": 1},
        {"plan": "pro", "org_id": str(uuid.uuid4()), "seat_count": 3},
    ]
    db = _exec_mock(org_rows)

    service = AdminMetricsService(db=db, plan_service=PlanService())
    snapshot = await service.compute_revenue()

    # Pro is flat-priced — seat count doesn't matter
    assert snapshot.mrr_cents == 7000 * 2
    assert snapshot.arr_cents == 7000 * 2 * 12
    pro_item = snapshot.breakdown[0]
    assert pro_item.plan == "pro"
    assert pro_item.org_count == 2
    assert pro_item.revenue_cents == 14000
    assert pro_item.display_name == "Profesional"


@pytest.mark.asyncio
async def test_compute_revenue_sums_base_plus_seat_overage():
    """Studio org with 7 seats: base 29900 + (7-5)*4000 = 37900."""
    org_rows = [
        {"plan": "studio", "org_id": str(uuid.uuid4()), "seat_count": 7},
    ]
    db = _exec_mock(org_rows)

    service = AdminMetricsService(db=db, plan_service=PlanService())
    snapshot = await service.compute_revenue()

    # 29900 + 2 overage * 4000 = 37900
    assert snapshot.mrr_cents == 37900
    studio_item = snapshot.breakdown[0]
    assert studio_item.plan == "studio"
    assert studio_item.revenue_cents == 37900
    assert studio_item.display_name == "Estudio"


@pytest.mark.asyncio
async def test_compute_revenue_excludes_inactive_orgs():
    """The SQL WHERE is_active=true is enforced; service returns 0 if all orgs inactive."""
    # Service receives empty list (simulates DB filtering out inactive orgs)
    db = _exec_mock([])

    service = AdminMetricsService(db=db, plan_service=PlanService())
    snapshot = await service.compute_revenue()

    assert snapshot.mrr_cents == 0
    assert snapshot.breakdown == []


@pytest.mark.asyncio
async def test_compute_revenue_mixed_plans():
    """Mixed plan portfolio sums correctly and arr = mrr * 12."""
    org_rows = [
        {"plan": "free", "org_id": str(uuid.uuid4()), "seat_count": 1},
        {"plan": "pro", "org_id": str(uuid.uuid4()), "seat_count": 1},
        {"plan": "studio", "org_id": str(uuid.uuid4()), "seat_count": 5},  # no overage
    ]
    db = _exec_mock(org_rows)

    service = AdminMetricsService(db=db, plan_service=PlanService())
    snapshot = await service.compute_revenue()

    # free=0, pro=7000, studio=29900 (5 seats = no overage)
    assert snapshot.mrr_cents == 0 + 7000 + 29900
    assert snapshot.arr_cents == snapshot.mrr_cents * 12
    assert len(snapshot.breakdown) == 3


# ---------------------------------------------------------------------------
# list_byok
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_byok_hides_encrypted_material():
    """BYOKItem returned by service must never include full key material."""
    byok_rows = [
        {
            "user_id": str(uuid.uuid4()),
            "user_email": "user@test.com",
            "provider": "openai",
            "is_active": True,
            "api_key_hint": "sk-...XYZ",
            "last_rotation_at": None,
        }
    ]
    db = _scalar_mock(byok_rows, scalar_value=1)

    service = AdminMetricsService(db=db, plan_service=PlanService())
    items, total = await service.list_byok(page=1, per_page=20, provider=None)

    assert total == 1
    assert len(items) == 1
    item = items[0]
    assert item.api_key_hint == "sk-...XYZ"
    assert not hasattr(item, "api_key_encrypted")
    assert item.provider == "openai"
    assert item.is_active is True


@pytest.mark.asyncio
async def test_list_byok_empty():
    """No BYOK keys → empty list, total=0."""
    db = _scalar_mock([], scalar_value=0)

    service = AdminMetricsService(db=db, plan_service=PlanService())
    items, total = await service.list_byok(page=1, per_page=20, provider=None)

    assert items == []
    assert total == 0


# ---------------------------------------------------------------------------
# list_users_extended
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_users_extended_includes_null_last_active():
    """Users with no refresh tokens must have last_active=None (not raise)."""
    now = datetime.now(UTC)
    user_rows = [
        {
            "id": str(uuid.uuid4()),
            "email": "nologin@test.com",
            "full_name": "No Login",
            "is_active": True,
            "is_admin": False,
            "plan": "free",
            "created_at": now,
            "org_name": None,
            "queries_this_month": 0,
            "last_active": None,
            "byok_count": 0,
        }
    ]
    db = _scalar_mock(user_rows, scalar_value=1)

    service = AdminMetricsService(db=db, plan_service=PlanService())
    items, total = await service.list_users_extended(page=1, per_page=20, q=None)

    assert total == 1
    assert len(items) == 1
    assert items[0].last_active is None
    assert items[0].byok_count == 0


@pytest.mark.asyncio
async def test_list_users_extended_byok_count():
    """Users with active BYOK keys must have byok_count > 0."""
    now = datetime.now(UTC)
    user_rows = [
        {
            "id": str(uuid.uuid4()),
            "email": "byok@test.com",
            "full_name": "BYOK User",
            "is_active": True,
            "is_admin": False,
            "plan": "pro",
            "created_at": now,
            "org_name": "Acme",
            "queries_this_month": 5,
            "last_active": now,
            "byok_count": 2,
        }
    ]
    db = _scalar_mock(user_rows, scalar_value=1)

    service = AdminMetricsService(db=db, plan_service=PlanService())
    items, total = await service.list_users_extended(page=1, per_page=20, q=None)

    assert items[0].byok_count == 2
    assert items[0].last_active == now
