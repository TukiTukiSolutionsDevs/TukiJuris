"""Unit tests for EntitlementService — plan-model-refactor Sprint 2.

Full matrix: {free, pro, studio} × {all feature keys} × {BETA_MODE=True, BETA_MODE=False}
No DB, no Docker required.
Run: python -m pytest tests/unit/test_entitlement_service.py -v
"""

import pytest

from app.config.plans import ALL_FEATURE_KEYS
from app.services.entitlement_service import EntitlementService


# ── has_feature — BETA_MODE=False (plan-based) ───────────────────────────────


class TestHasFeatureNoBeta:
    # Free plan
    def test_free_chat_allowed(self):
        assert EntitlementService.has_feature_by_plan("free", "chat", beta_mode=False) is True

    def test_free_pdf_export_denied(self):
        assert EntitlementService.has_feature_by_plan("free", "pdf_export", beta_mode=False) is False

    def test_free_file_upload_denied(self):
        assert EntitlementService.has_feature_by_plan("free", "file_upload", beta_mode=False) is False

    def test_free_byok_denied(self):
        assert EntitlementService.has_feature_by_plan("free", "byok_enabled", beta_mode=False) is False

    def test_free_team_seats_denied(self):
        assert EntitlementService.has_feature_by_plan("free", "team_seats", beta_mode=False) is False

    def test_free_priority_support_denied(self):
        assert EntitlementService.has_feature_by_plan("free", "priority_support", beta_mode=False) is False

    # Pro plan
    def test_pro_chat_allowed(self):
        assert EntitlementService.has_feature_by_plan("pro", "chat", beta_mode=False) is True

    def test_pro_pdf_export_allowed(self):
        assert EntitlementService.has_feature_by_plan("pro", "pdf_export", beta_mode=False) is True

    def test_pro_file_upload_allowed(self):
        assert EntitlementService.has_feature_by_plan("pro", "file_upload", beta_mode=False) is True

    def test_pro_byok_allowed(self):
        assert EntitlementService.has_feature_by_plan("pro", "byok_enabled", beta_mode=False) is True

    def test_pro_team_seats_denied(self):
        assert EntitlementService.has_feature_by_plan("pro", "team_seats", beta_mode=False) is False

    def test_pro_priority_support_allowed(self):
        assert EntitlementService.has_feature_by_plan("pro", "priority_support", beta_mode=False) is True

    # Studio plan
    def test_studio_all_features_allowed(self):
        for key in ALL_FEATURE_KEYS:
            result = EntitlementService.has_feature_by_plan("studio", key, beta_mode=False)
            assert result is True, f"studio.{key} should be True without beta"


# ── has_feature — BETA_MODE=True ────────────────────────────────────────────


class TestHasFeatureBeta:
    # Free + beta → all features EXCEPT byok_enabled
    def test_free_chat_allowed_in_beta(self):
        assert EntitlementService.has_feature_by_plan("free", "chat", beta_mode=True) is True

    def test_free_pdf_export_allowed_in_beta(self):
        assert EntitlementService.has_feature_by_plan("free", "pdf_export", beta_mode=True) is True

    def test_free_file_upload_allowed_in_beta(self):
        assert EntitlementService.has_feature_by_plan("free", "file_upload", beta_mode=True) is True

    def test_free_byok_denied_in_beta(self):
        """BYOK is paid-only regardless of BETA_MODE — hard exclusion."""
        assert EntitlementService.has_feature_by_plan("free", "byok_enabled", beta_mode=True) is False

    def test_free_team_seats_allowed_in_beta(self):
        assert EntitlementService.has_feature_by_plan("free", "team_seats", beta_mode=True) is True

    def test_free_priority_support_allowed_in_beta(self):
        assert EntitlementService.has_feature_by_plan("free", "priority_support", beta_mode=True) is True

    # Pro + beta → all True (byok already granted normally)
    def test_pro_all_features_allowed_in_beta(self):
        for key in ALL_FEATURE_KEYS:
            result = EntitlementService.has_feature_by_plan("pro", key, beta_mode=True)
            assert result is True, f"pro.{key} should be True in beta"

    # Studio + beta → all True
    def test_studio_all_features_allowed_in_beta(self):
        for key in ALL_FEATURE_KEYS:
            result = EntitlementService.has_feature_by_plan("studio", key, beta_mode=True)
            assert result is True, f"studio.{key} should be True in beta"


# ── has_feature — unknown plan ───────────────────────────────────────────────


class TestHasFeatureUnknownPlan:
    def test_unknown_plan_returns_false(self):
        assert EntitlementService.has_feature_by_plan("enterprise", "chat", beta_mode=False) is False

    def test_legacy_base_returns_false(self):
        assert EntitlementService.has_feature_by_plan("base", "pdf_export", beta_mode=False) is False

    def test_unknown_plan_in_beta_returns_false(self):
        assert EntitlementService.has_feature_by_plan("enterprise", "chat", beta_mode=True) is False


# ── list_user_features ────────────────────────────────────────────────────────


class TestListUserFeatures:
    def test_free_no_beta_returns_only_chat(self):
        features = EntitlementService.list_user_features("free", beta_mode=False)
        assert features == ["chat"]

    def test_pro_no_beta_excludes_team_seats(self):
        features = EntitlementService.list_user_features("pro", beta_mode=False)
        assert "team_seats" not in features
        assert "pdf_export" in features
        assert "byok_enabled" in features

    def test_studio_no_beta_returns_all_features(self):
        features = EntitlementService.list_user_features("studio", beta_mode=False)
        for key in ALL_FEATURE_KEYS:
            assert key in features

    def test_free_beta_excludes_byok(self):
        features = EntitlementService.list_user_features("free", beta_mode=True)
        assert "byok_enabled" not in features
        assert "pdf_export" in features

    def test_pro_beta_includes_all_features(self):
        features = EntitlementService.list_user_features("pro", beta_mode=True)
        for key in ALL_FEATURE_KEYS:
            assert key in features

    def test_output_is_sorted(self):
        features = EntitlementService.list_user_features("studio", beta_mode=False)
        assert features == sorted(features)

    def test_unknown_plan_returns_empty_list(self):
        features = EntitlementService.list_user_features("base", beta_mode=False)
        assert features == []
