"""Unit tests for app.config.plans — plan-model-refactor Sprint 2.

Pure module tests: no fixtures, no DB, no Docker required.
Run: python -m pytest tests/unit/test_plans_config.py -v
"""

from app.config.plans import ALL_FEATURE_KEYS, BETA_HARD_LIMITS, PLANS, PlanConfig


class TestPlansDict:
    def test_plan_ids_are_free_pro_studio(self):
        assert set(PLANS.keys()) == {"free", "pro", "studio"}

    def test_each_plan_is_frozen_dataclass(self):
        for plan in PLANS.values():
            assert isinstance(plan, PlanConfig)

    def test_plan_ids_match_keys(self):
        for key, plan in PLANS.items():
            assert plan.id == key


class TestFreePlan:
    def test_queries_day_is_ten(self):
        assert PLANS["free"].queries_day == 10

    def test_base_price_cents_is_zero(self):
        assert PLANS["free"].base_price_cents == 0

    def test_byok_disabled(self):
        assert PLANS["free"].byok_enabled is False

    def test_chat_enabled(self):
        assert PLANS["free"].features["chat"] is True

    def test_pdf_export_disabled(self):
        assert PLANS["free"].features["pdf_export"] is False

    def test_file_upload_disabled(self):
        assert PLANS["free"].features["file_upload"] is False

    def test_byok_feature_disabled(self):
        assert PLANS["free"].features["byok_enabled"] is False

    def test_team_seats_disabled(self):
        assert PLANS["free"].features["team_seats"] is False

    def test_display_name(self):
        assert PLANS["free"].display_name == "Gratuito"


class TestProPlan:
    def test_queries_day_is_unlimited(self):
        assert PLANS["pro"].queries_day == -1

    def test_base_price_cents(self):
        assert PLANS["pro"].base_price_cents == 7000

    def test_byok_enabled(self):
        assert PLANS["pro"].byok_enabled is True

    def test_pdf_export_enabled(self):
        assert PLANS["pro"].features["pdf_export"] is True

    def test_file_upload_enabled(self):
        assert PLANS["pro"].features["file_upload"] is True

    def test_byok_feature_enabled(self):
        assert PLANS["pro"].features["byok_enabled"] is True

    def test_team_seats_disabled(self):
        assert PLANS["pro"].features["team_seats"] is False

    def test_seat_price_cents_is_zero(self):
        assert PLANS["pro"].seat_price_cents == 0

    def test_display_name(self):
        assert PLANS["pro"].display_name == "Profesional"


class TestStudioPlan:
    def test_queries_day_is_unlimited(self):
        assert PLANS["studio"].queries_day == -1

    def test_base_price_cents(self):
        assert PLANS["studio"].base_price_cents == 29900

    def test_seat_price_cents(self):
        assert PLANS["studio"].seat_price_cents == 4000

    def test_base_seats_included(self):
        assert PLANS["studio"].base_seats_included == 5

    def test_byok_enabled(self):
        assert PLANS["studio"].byok_enabled is True

    def test_team_seats_enabled(self):
        assert PLANS["studio"].features["team_seats"] is True

    def test_all_features_enabled(self):
        for key in ALL_FEATURE_KEYS:
            assert PLANS["studio"].features[key] is True, f"studio.{key} should be True"

    def test_display_name(self):
        assert PLANS["studio"].display_name == "Estudio"


class TestFeatureKeyCoverage:
    def test_all_feature_keys_present_in_every_plan(self):
        for plan_id, plan in PLANS.items():
            for key in ALL_FEATURE_KEYS:
                assert key in plan.features, f"{plan_id}.features missing key: {key}"

    def test_all_feature_keys_tuple_is_complete(self):
        assert "chat" in ALL_FEATURE_KEYS
        assert "pdf_export" in ALL_FEATURE_KEYS
        assert "file_upload" in ALL_FEATURE_KEYS
        assert "byok_enabled" in ALL_FEATURE_KEYS
        assert "team_seats" in ALL_FEATURE_KEYS
        assert "priority_support" in ALL_FEATURE_KEYS


class TestBetaHardLimits:
    def test_free_queries_day_is_ten(self):
        assert BETA_HARD_LIMITS["free_queries_day"] == 10

    def test_byok_paid_only_is_true(self):
        assert BETA_HARD_LIMITS["byok_paid_only"] is True


class TestImmutability:
    def test_plans_are_frozen(self):
        import dataclasses

        plan = PLANS["free"]
        assert dataclasses.is_dataclass(plan)
        # Attempt to mutate should raise FrozenInstanceError
        import pytest

        with pytest.raises(Exception):
            plan.queries_day = 999  # type: ignore[misc]
