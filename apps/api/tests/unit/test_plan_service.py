"""Unit tests for PlanService — plan-model-refactor Sprint 2.

No DB, no Docker required for pricing tests.
Seat counting test uses AsyncMock to simulate AsyncSession.
Run: python -m pytest tests/unit/test_plan_service.py -v
"""

import pytest

from app.services.plan_service import PlanService


class TestGetConfig:
    def test_free_config_returns_correct_plan(self):
        config = PlanService.get_config("free")
        assert config.id == "free"

    def test_pro_config_returns_correct_plan(self):
        config = PlanService.get_config("pro")
        assert config.id == "pro"

    def test_studio_config_returns_correct_plan(self):
        config = PlanService.get_config("studio")
        assert config.id == "studio"

    def test_unknown_plan_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown plan"):
            PlanService.get_config("enterprise")

    def test_legacy_base_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown plan"):
            PlanService.get_config("base")


class TestQueriesDay:
    def test_free_queries_day_is_ten(self):
        assert PlanService.queries_day_for("free") == 10

    def test_pro_queries_day_is_unlimited(self):
        assert PlanService.queries_day_for("pro") == -1

    def test_studio_queries_day_is_unlimited(self):
        assert PlanService.queries_day_for("studio") == -1


class TestGetPriceCents:
    # free — always 0
    def test_free_one_seat(self):
        assert PlanService.get_price_cents("free", 1) == 0

    def test_free_one_hundred_seats(self):
        assert PlanService.get_price_cents("free", 100) == 0

    # pro — flat, no seat overage
    def test_pro_one_seat(self):
        assert PlanService.get_price_cents("pro", 1) == 7000

    def test_pro_five_seats(self):
        assert PlanService.get_price_cents("pro", 5) == 7000

    def test_pro_one_hundred_seats(self):
        # pro has seat_price_cents=0 → no overage regardless of count
        assert PlanService.get_price_cents("pro", 100) == 7000

    # studio — base_seats_included=5, seat_price_cents=4000
    def test_studio_one_seat(self):
        # 1 < 5 included → no overage
        assert PlanService.get_price_cents("studio", 1) == 29900

    def test_studio_five_seats_exactly_included(self):
        assert PlanService.get_price_cents("studio", 5) == 29900

    def test_studio_six_seats_one_overage(self):
        # 6 - 5 = 1 overage × 4000 = 4000 → 29900 + 4000 = 33900
        assert PlanService.get_price_cents("studio", 6) == 33900

    def test_studio_one_hundred_seats(self):
        # 100 - 5 = 95 overage × 4000 = 380000 → 29900 + 380000 = 409900
        assert PlanService.get_price_cents("studio", 100) == 409900

    def test_studio_zero_seats(self):
        # 0 < 5 included → no overage
        assert PlanService.get_price_cents("studio", 0) == 29900

    def test_result_is_integer(self):
        result = PlanService.get_price_cents("studio", 6)
        assert isinstance(result, int)


class TestCountActiveSeats:
    async def test_count_delegates_to_org_membership(self):
        """count_active_seats queries OrgMembership with is_active=True filter."""
        import uuid
        from unittest.mock import AsyncMock, MagicMock

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 3
        mock_db.execute.return_value = mock_result

        org_id = uuid.uuid4()
        count = await PlanService.count_active_seats(org_id, mock_db)

        assert count == 3
        mock_db.execute.assert_awaited_once()

    async def test_count_returns_zero_when_scalar_is_none(self):
        """Handles NULL COUNT result safely."""
        import uuid
        from unittest.mock import AsyncMock, MagicMock

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = None
        mock_db.execute.return_value = mock_result

        count = await PlanService.count_active_seats(uuid.uuid4(), mock_db)
        assert count == 0
