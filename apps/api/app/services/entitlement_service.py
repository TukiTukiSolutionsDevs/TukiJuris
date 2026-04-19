"""
EntitlementService — feature-flag resolution with BETA_MODE override.

RESPONSIBILITY: Determine which features a user can access.
NOT responsible for: daily query caps (usage.py), seat counts (PlanService),
or billing calculations.

BETA_MODE rules (hardcoded invariants, non-negotiable):
  1. free tier: daily cap stays at 10 msg/day regardless of BETA_MODE.
     (Enforced in usage.py, not here — this service deals with feature flags only.)
  2. byok_enabled: always False for free tier, even in BETA_MODE.
  3. All other features: BETA_MODE=True grants access across all plan tiers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.config.plans import ALL_FEATURE_KEYS, PLANS

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.user import User


class EntitlementService:
    """Stateless service for user feature-flag resolution."""

    @staticmethod
    async def has_feature(user: "User", feature_key: str, db: "AsyncSession") -> bool:
        """Return True if the user's plan grants access to the given feature.

        Canonical user-centric entrypoint. Derives plan_id from user.plan
        and reads beta_mode from settings automatically.

        Args:
            user:        Authenticated user (plan read from user.plan).
            feature_key: Feature identifier. Use 'byok' for BYOK access;
                         mapped internally to 'byok_enabled' in plan config.
            db:          AsyncSession (reserved for future DB-backed features;
                         not used currently — plan is read from user object).

        Hard exclusions (always enforced, even in beta):
            - free + byok → always False
        """
        from app.config import settings

        plan_id = user.plan or "free"
        beta_mode = settings.beta_mode

        # Normalize canonical external key → internal plan-config key
        internal_key = "byok_enabled" if feature_key == "byok" else feature_key

        return EntitlementService.has_feature_by_plan(plan_id, internal_key, beta_mode)

    @staticmethod
    def has_feature_by_plan(plan_id: str, feature_key: str, beta_mode: bool) -> bool:
        """Plan-centric entitlement check (internal / legacy convenience method).

        Prefer has_feature(user, feature_key, db) for new callers.

        Args:
            plan_id:     User's current plan ('free', 'pro', 'studio').
            feature_key: Feature identifier (e.g. 'byok_enabled').
            beta_mode:   Value of BETA_MODE from settings.

        Hard exclusions (always enforced, even in beta):
            - free + byok_enabled → always False
        """
        plan = PLANS.get(plan_id)  # type: ignore[arg-type]
        if plan is None:
            # Unknown plan — deny all features defensively.
            return False

        # Hard exclusion: BYOK is paid-only regardless of beta mode.
        if feature_key == "byok_enabled" and plan_id == "free":
            return False

        if beta_mode:
            # Beta grants all features except hard-excluded ones above.
            return True

        return bool(plan.features.get(feature_key, False))  # type: ignore[arg-type]

    @staticmethod
    def list_user_features(plan_id: str, beta_mode: bool) -> list[str]:
        """Return sorted list of feature keys the user can access.

        Used by /me to populate the entitlements array in the response.
        Output is sorted for deterministic serialisation.
        """
        if beta_mode:
            # Grant every known feature key except BYOK for free.
            enabled = set(ALL_FEATURE_KEYS)
            if plan_id == "free":
                enabled.discard("byok_enabled")
            return sorted(enabled)

        plan = PLANS.get(plan_id)  # type: ignore[arg-type]
        if plan is None:
            return []

        return sorted(k for k, v in plan.features.items() if v)
