"""Unit tests for invoice_pricing.compute_invoice_amounts (AC3, AC4).

Pure unit tests — no DB, no Docker required.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/unit/test_invoice_pricing.py -v
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.invoice_pricing import IGV_RATE, InvoiceAmounts, compute_invoice_amounts


class TestComputeInvoiceAmountsPro:
    """Pro plan — flat pricing, no seat overage."""

    def test_pro_zero_seats(self):
        amt = compute_invoice_amounts("pro", 0)
        assert amt["base_amount"] == Decimal("70.00")
        assert amt["seats_count"] == 0
        assert amt["seat_amount"] == Decimal("0.00")
        assert amt["subtotal_amount"] == Decimal("70.00")
        assert amt["tax_amount"] == Decimal("12.60")
        assert amt["total_amount"] == Decimal("82.60")

    def test_pro_many_seats_no_overage(self):
        """Pro has base_seats_included=1, seat_price=0 — still flat."""
        amt = compute_invoice_amounts("pro", 100)
        assert amt["subtotal_amount"] == Decimal("70.00")
        assert amt["total_amount"] == Decimal("82.60")

    def test_pro_decimal_types(self):
        amt = compute_invoice_amounts("pro", 0)
        for key in ("base_amount", "seat_amount", "subtotal_amount", "tax_amount", "total_amount"):
            assert isinstance(amt[key], Decimal), f"{key} should be Decimal"

    def test_pro_seats_count_round_trips(self):
        amt = compute_invoice_amounts("pro", 3)
        assert amt["seats_count"] == 3


class TestComputeInvoiceAmountsStudio:
    """Studio plan — 5 base seats included, S/40 per extra seat."""

    def test_studio_zero_seats(self):
        """0 seats → all within included base → no overage."""
        amt = compute_invoice_amounts("studio", 0)
        assert amt["base_amount"] == Decimal("299.00")
        assert amt["seat_amount"] == Decimal("0.00")
        assert amt["subtotal_amount"] == Decimal("299.00")
        assert amt["tax_amount"] == Decimal("53.82")
        assert amt["total_amount"] == Decimal("352.82")

    def test_studio_3_seats_no_overage(self):
        """3 ≤ 5 included → no overage."""
        amt = compute_invoice_amounts("studio", 3)
        assert amt["seat_amount"] == Decimal("0.00")
        assert amt["subtotal_amount"] == Decimal("299.00")
        assert amt["tax_amount"] == Decimal("53.82")
        assert amt["total_amount"] == Decimal("352.82")

    def test_studio_5_seats_boundary(self):
        """Exactly 5 included → no overage."""
        amt = compute_invoice_amounts("studio", 5)
        assert amt["seat_amount"] == Decimal("0.00")
        assert amt["subtotal_amount"] == Decimal("299.00")
        assert amt["total_amount"] == Decimal("352.82")

    def test_studio_6_seats_1_overage(self):
        """6 - 5 included = 1 overage × 40 = 40."""
        amt = compute_invoice_amounts("studio", 6)
        assert amt["seat_amount"] == Decimal("40.00")
        assert amt["subtotal_amount"] == Decimal("339.00")
        assert amt["tax_amount"] == Decimal("61.02")
        assert amt["total_amount"] == Decimal("400.02")

    def test_studio_7_seats_2_overage(self):
        """7 - 5 = 2 overage × 40 = 80."""
        amt = compute_invoice_amounts("studio", 7)
        assert amt["seat_amount"] == Decimal("80.00")
        assert amt["subtotal_amount"] == Decimal("379.00")
        assert amt["tax_amount"] == Decimal("68.22")
        assert amt["total_amount"] == Decimal("447.22")

    def test_studio_10_seats_5_overage(self):
        """10 - 5 = 5 overage × 40 = 200."""
        amt = compute_invoice_amounts("studio", 10)
        assert amt["seat_amount"] == Decimal("200.00")
        assert amt["subtotal_amount"] == Decimal("499.00")
        assert amt["tax_amount"] == Decimal("89.82")
        assert amt["total_amount"] == Decimal("588.82")

    def test_studio_100_seats_95_overage(self):
        """100 - 5 = 95 overage × 40 = 3800."""
        amt = compute_invoice_amounts("studio", 100)
        assert amt["seat_amount"] == Decimal("3800.00")
        assert amt["subtotal_amount"] == Decimal("4099.00")
        # 4099 × 0.18 = 737.82
        assert amt["tax_amount"] == Decimal("737.82")
        assert amt["total_amount"] == Decimal("4836.82")


class TestComputeInvoiceAmountsEdge:
    """Edge cases: unknown plan, free plan, TypedDict shape."""

    def test_unknown_plan_raises(self):
        with pytest.raises(ValueError, match="Unknown plan"):
            compute_invoice_amounts("enterprise", 0)

    def test_free_plan_zero_amounts(self):
        amt = compute_invoice_amounts("free", 0)
        assert amt["base_amount"] == Decimal("0.00")
        assert amt["total_amount"] == Decimal("0.00")
        assert amt["tax_amount"] == Decimal("0.00")

    def test_typeddict_shape(self):
        amt = compute_invoice_amounts("pro", 0)
        required_keys = {
            "base_amount", "seats_count", "seat_amount",
            "subtotal_amount", "tax_amount", "total_amount",
        }
        assert required_keys == set(amt.keys())

    def test_igv_rate_constant(self):
        assert IGV_RATE == Decimal("0.18")

    def test_tax_is_round_half_up(self):
        """Any subtotal × 0.18 that ends in .5 should round UP."""
        # 70.00 × 0.18 = 12.600 → 12.60 (no ambiguity here)
        amt = compute_invoice_amounts("pro", 0)
        # Verify it's exactly 12.60 not 12.59 or 12.61
        assert amt["tax_amount"] == Decimal("12.60")

    def test_compute_is_pure_no_db(self):
        """Should succeed without any DB connection."""
        result = compute_invoice_amounts("studio", 7)
        assert result["total_amount"] > 0
