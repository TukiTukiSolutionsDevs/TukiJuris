"""Invoice pricing helper — IGV computation on top of PlanService.

Single source of truth for invoice money math. All values in PEN (Soles).

Design decisions:
- Reuses PlanService.get_config() for base/seat/included — no PLAN_PRICING duplication.
- IGV (18%) lives here, NOT in PlanService (tax is invoice-domain, not plan-config).
- All Decimal arithmetic with ROUND_HALF_UP to 2 decimal places.
- Pure function — no DB, no async, no side effects.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import TypedDict

from app.services.plan_service import PlanService

IGV_RATE = Decimal("0.18")
_CENTS = Decimal("0.01")


class InvoiceAmounts(TypedDict):
    base_amount: Decimal       # plan base price (e.g. 70.00, 299.00)
    seats_count: int           # raw seat count passed in
    seat_amount: Decimal       # billable_seats × per-seat PEN
    subtotal_amount: Decimal   # base + seat_amount
    tax_amount: Decimal        # subtotal × 0.18, ROUND_HALF_UP
    total_amount: Decimal      # subtotal + tax


def compute_invoice_amounts(plan: str, seats_count: int) -> InvoiceAmounts:
    """Compute full invoice price breakdown for a plan + seat count.

    Raises:
        ValueError: if plan is unknown (propagated from PlanService.get_config).

    Studio example (base_seats_included=5):
        3 seats → billable=0 → seat_amount=0 → subtotal=299 → tax=53.82 → total=352.82
        7 seats → billable=2 → seat_amount=80 → subtotal=379 → tax=68.22 → total=447.22

    Pro example (no seat pricing):
        any seats → subtotal=70 → tax=12.60 → total=82.60
    """
    cfg = PlanService.get_config(plan)  # raises ValueError on unknown plan

    # Convert integer cents → Decimal PEN (never pass float to Decimal)
    base = (Decimal(cfg.base_price_cents) / 100).quantize(_CENTS, ROUND_HALF_UP)
    per_seat = (Decimal(cfg.seat_price_cents) / 100).quantize(_CENTS, ROUND_HALF_UP)

    billable_seats = max(0, seats_count - cfg.base_seats_included)
    seat_amount = (per_seat * billable_seats).quantize(_CENTS, ROUND_HALF_UP)

    subtotal = (base + seat_amount).quantize(_CENTS, ROUND_HALF_UP)
    tax = (subtotal * IGV_RATE).quantize(_CENTS, ROUND_HALF_UP)
    total = (subtotal + tax).quantize(_CENTS, ROUND_HALF_UP)

    return InvoiceAmounts(
        base_amount=base,
        seats_count=seats_count,
        seat_amount=seat_amount,
        subtotal_amount=subtotal,
        tax_amount=tax,
        total_amount=total,
    )
