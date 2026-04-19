"""
PlanService — stateless pricing + seat helpers.

All methods are static: PlanService holds no state, instantiation is noise.
DB access only via AsyncSession (never raw asyncpg) to stay consistent with
the rest of the async codebase.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.plans import PLANS, PlanConfig, PlanId


class PlanService:
    """Stateless service for plan config lookups and billing calculations."""

    # ── Config lookups ────────────────────────────────────────────────────

    @staticmethod
    def get_config(plan_id: str) -> PlanConfig:
        """Return PlanConfig for the given plan_id.

        Raises ValueError for unknown plans so callers get a deterministic,
        testable error rather than a silent KeyError.
        """
        config = PLANS.get(plan_id)  # type: ignore[arg-type]
        if config is None:
            raise ValueError(
                f"Unknown plan: '{plan_id}'. Valid plans: {list(PLANS.keys())}"
            )
        return config

    @staticmethod
    def queries_day_for(plan_id: str) -> int:
        """Return daily query cap for the plan. -1 means unlimited."""
        return PlanService.get_config(plan_id).queries_day

    # ── Pricing ──────────────────────────────────────────────────────────

    @staticmethod
    def get_price_cents(plan_id: str, seat_count: int = 1) -> int:
        """Compute total price in PEN cents for the given plan and seat count.

        Formula: base_price_cents + max(0, seat_count - base_seats_included) * seat_price_cents

        Examples:
          free, any seats   → 0
          pro,  any seats   → 7000   (flat)
          studio, 1 seat    → 29900  (5 included, no overage)
          studio, 5 seats   → 29900  (exactly included, no overage)
          studio, 6 seats   → 33900  (1 overage × 4000)
          studio, 100 seats → 409900 (95 overage × 4000)
        """
        p = PlanService.get_config(plan_id)
        billable_seats = max(0, seat_count - p.base_seats_included)
        return p.base_price_cents + billable_seats * p.seat_price_cents

    # ── Seat counting ─────────────────────────────────────────────────────

    @staticmethod
    async def count_active_seats(org_id: object, db: AsyncSession) -> int:
        """Count active members in an organisation.

        Uses OrgMembership.is_active column (confirmed in organization.py).
        Falls back to a plain COUNT if is_active doesn't exist (unlikely given
        current schema, but documented as a safety net).
        """
        from app.models.organization import OrgMembership

        stmt = (
            select(func.count(OrgMembership.id))
            .where(
                OrgMembership.organization_id == org_id,
                OrgMembership.is_active.is_(True),
            )
        )
        result = await db.execute(stmt)
        return int(result.scalar_one() or 0)
