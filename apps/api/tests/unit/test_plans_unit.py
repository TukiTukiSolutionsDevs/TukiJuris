"""Unit tests for plans route helper functions and constants.

Tests pure module-level helpers without spinning up FastAPI or hitting the DB.
No fixtures needed, no Docker required for this file.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/unit/test_plans_unit.py -v
"""

from __future__ import annotations

from decimal import Decimal

from app.api.routes.plans import (
    FEATURE_LABELS,
    _cents_to_pen,
    _enabled_feature_labels,
    _limits_for,
)
from app.config.plans import ALL_FEATURE_KEYS


# ---------------------------------------------------------------------------
# FEATURE_LABELS coverage
# ---------------------------------------------------------------------------


class TestFeatureLabelsCoverage:
    def test_every_feature_key_has_a_label(self):
        """Every key in ALL_FEATURE_KEYS must have a FEATURE_LABELS entry.

        This test prevents silent label loss when a new feature key is added
        to PlanConfig but FEATURE_LABELS is not updated.
        """
        for key in ALL_FEATURE_KEYS:
            assert key in FEATURE_LABELS, (
                f"Feature key '{key}' has no entry in FEATURE_LABELS. "
                "Add a human-readable es-PE label."
            )

    def test_feature_label_values_are_non_empty(self):
        """All label values are non-empty strings."""
        for key, label in FEATURE_LABELS.items():
            assert isinstance(label, str) and len(label.strip()) > 0, (
                f"FEATURE_LABELS['{key}'] is empty or not a string"
            )

    def test_feature_labels_have_spaces(self):
        """Human-readable labels contain spaces (not snake_case machine keys)."""
        for key, label in FEATURE_LABELS.items():
            assert " " in label, (
                f"FEATURE_LABELS['{key}'] = '{label}' looks like a machine key (no spaces)"
            )


# ---------------------------------------------------------------------------
# _cents_to_pen
# ---------------------------------------------------------------------------


class TestCentsToPen:
    def test_zero(self):
        assert _cents_to_pen(0) == Decimal("0.00")

    def test_pro_base(self):
        assert _cents_to_pen(7000) == Decimal("70.00")

    def test_studio_base(self):
        assert _cents_to_pen(29900) == Decimal("299.00")

    def test_studio_seat(self):
        assert _cents_to_pen(4000) == Decimal("40.00")

    def test_result_is_decimal(self):
        result = _cents_to_pen(7000)
        assert isinstance(result, Decimal)

    def test_two_decimal_places(self):
        """Result is always quantized to exactly 2 decimal places."""
        result = _cents_to_pen(1)  # 0.01
        assert result == Decimal("0.01")
        # String representation confirms scale
        assert str(result) == "0.01"


# ---------------------------------------------------------------------------
# _limits_for
# ---------------------------------------------------------------------------


class TestLimitsFor:
    def test_minus_one_returns_none(self):
        """queries_day=-1 (unlimited) maps to chat_per_day=None."""
        result = _limits_for(-1)
        assert result == {"chat_per_day": None}

    def test_positive_value_passes_through(self):
        """Positive cap passes through as integer."""
        assert _limits_for(10) == {"chat_per_day": 10}

    def test_arbitrary_positive(self):
        assert _limits_for(100) == {"chat_per_day": 100}

    def test_returns_dict_with_chat_per_day_key(self):
        result = _limits_for(5)
        assert "chat_per_day" in result


# ---------------------------------------------------------------------------
# _enabled_feature_labels
# ---------------------------------------------------------------------------


class TestEnabledFeatureLabels:
    def test_filters_out_false_flags(self):
        """Features set to False are excluded from the output list."""
        features = {"chat": True, "pdf_export": False, "file_upload": False,
                    "byok_enabled": False, "team_seats": False, "priority_support": False}
        result = _enabled_feature_labels(features)
        assert result == ["Chat con IA legal"]

    def test_all_true_returns_all_labels(self):
        """All True → all 6 labels in FEATURE_LABELS insertion order."""
        features = {k: True for k in FEATURE_LABELS}
        result = _enabled_feature_labels(features)
        assert result == list(FEATURE_LABELS.values())

    def test_all_false_returns_empty(self):
        features = {k: False for k in FEATURE_LABELS}
        assert _enabled_feature_labels(features) == []

    def test_order_follows_feature_labels_insertion(self):
        """Labels appear in FEATURE_LABELS dict insertion order."""
        features = {"chat": True, "pdf_export": False, "file_upload": True,
                    "byok_enabled": False, "team_seats": False, "priority_support": True}
        result = _enabled_feature_labels(features)
        assert result == [
            "Chat con IA legal",
            "Subir archivos (PDF, DOCX)",
            "Soporte prioritario",
        ]

    def test_unknown_key_in_features_silently_skipped(self):
        """Keys not in FEATURE_LABELS are ignored (forward-compat)."""
        features = {"chat": True, "future_feature": True}
        result = _enabled_feature_labels(features)
        assert result == ["Chat con IA legal"]
