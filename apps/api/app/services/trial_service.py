"""TrialService — 14-day trial lifecycle management.

All user-facing methods own their own transaction boundary via
``async with self.db.begin()``. Internal transition methods (mark_*)
are flush-only — the caller (webhook Phase 1 or scheduler) owns the
transaction. This mirrors the InvoiceService pattern established in item 4b.

Constraints enforced:
- Check-first SELECT for all idempotent operations (SA gotcha #2 — no begin_nested).
- HTTP calls (provider.charge_stored_card) are placed OUTSIDE db.begin() in the
  scheduler path to avoid idle-in-transaction on slow provider responses (R-D3).
- AuditService is injected explicitly (Sprint 2 pattern).
- Subscription is org-scoped; org is resolved via user.default_org_id or
  OrgMembership owner lookup.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import OrgMembership
from app.models.subscription import Subscription
from app.models.trial import RETRY_WINDOW_HOURS, Trial
from app.models.user import User
from app.rbac.audit import AuditService
from app.schemas.trials import AdminTrialFilters, AdminTrialPatch
from app.services.email_service import EmailService
from app.services.payment_providers.base import ChargeResult, PaymentProviderAdapter, ProviderError
from app.services.plan_service import PlanService
from app.services.subscription_service import upsert_subscription_for_checkout

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain error
# ---------------------------------------------------------------------------


class TrialError(HTTPException):
    """Trial domain error — maps directly to an HTTP status code.

    Raising TrialError inside a route handler causes FastAPI to return the
    appropriate HTTP response without any additional handling.
    """

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(status_code=status_code, detail=detail)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class TrialService:
    """Async service for the full trial lifecycle.

    Constructor args are injected explicitly (no module-level globals).
    Use ``get_trial_service`` from ``app.api.deps`` in route handlers.
    """

    def __init__(
        self,
        db: AsyncSession,
        audit: AuditService,
        culqi: PaymentProviderAdapter,
        mp: PaymentProviderAdapter,
        email: EmailService,
        settings: object,
    ) -> None:
        self.db = db
        self.audit = audit
        self._providers: dict[str, PaymentProviderAdapter] = {
            "culqi": culqi,
            "mp": mp,
        }
        self.email = email
        self.settings = settings

    # ── Provider lookup ─────────────────────────────────────────────────────

    def _provider_for(self, name: str) -> PaymentProviderAdapter:
        try:
            return self._providers[name]
        except KeyError:
            raise TrialError(422, f"Unknown provider '{name}'. Valid: culqi, mp")

    # ── DB helpers ──────────────────────────────────────────────────────────

    def provider_for(self, name: str) -> PaymentProviderAdapter:
        """Public accessor for payment provider adapters (used by scheduler)."""
        return self._provider_for(name)

    async def _load_owned_for_update(
        self, trial_id: UUID, user_id: UUID
    ) -> Trial:
        """Load a trial by id with FOR UPDATE, checking ownership.

        Raises 404 if trial does not exist, 403 if it belongs to another user (AC12).
        """
        q = select(Trial).where(Trial.id == trial_id).with_for_update()
        trial = (await self.db.execute(q)).scalar_one_or_none()
        if trial is None:
            raise TrialError(404, "Trial not found")
        if trial.user_id != user_id:
            raise TrialError(403, "Forbidden")
        return trial

    async def _resolve_user_and_org(
        self, user_id: UUID
    ) -> tuple[Optional[User], Optional[UUID]]:
        """Return (user, org_id). org_id may be None when user has no org."""
        user: Optional[User] = (
            await self.db.execute(select(User).where(User.id == user_id))
        ).scalar_one_or_none()
        if user is None:
            return None, None

        org_id: Optional[UUID] = user.default_org_id
        if org_id is None:
            # Fallback: first owner membership
            row = (
                await self.db.execute(
                    select(OrgMembership.organization_id)
                    .where(
                        OrgMembership.user_id == user_id,
                        OrgMembership.role == "owner",
                        OrgMembership.is_active == True,  # noqa: E712
                    )
                    .limit(1)
                )
            ).first()
            if row:
                org_id = row[0]

        return user, org_id

    # ── Subscription helpers ────────────────────────────────────────────────

    async def _activate_subscription_trialing(
        self, user_id: UUID, plan_code: str
    ) -> Optional[UUID]:
        """Upsert the user's org subscription to status='trialing' and sync user.plan.

        Returns the subscription id, or None if the user has no org.
        Caller must be inside an open transaction (flush-only inside).
        """
        user, org_id = await self._resolve_user_and_org(user_id)
        if user is None:
            return None

        user.plan = plan_code

        if org_id is None:
            logger.warning(
                "trial.activate_sub: user %s has no org — skipping subscription upsert",
                user_id,
            )
            return None

        sub = await upsert_subscription_for_checkout(
            self.db,
            org_id=org_id,
            provider="trials",
            provider_subscription_id=None,
            plan=plan_code,
            status="trialing",
        )
        await self.db.flush()
        return sub.id

    async def _deactivate_to_free(self, user_id: UUID) -> None:
        """Revert user.plan to 'free' and downgrade the org subscription.

        Caller must be inside an open transaction (flush-only inside).
        """
        user, org_id = await self._resolve_user_and_org(user_id)
        if user is None:
            return

        user.plan = "free"

        if org_id is None:
            return

        # Find any trialing subscription for this org and revert it to free.
        sub: Optional[Subscription] = (
            await self.db.execute(
                select(Subscription)
                .where(
                    Subscription.organization_id == org_id,
                    Subscription.status == "trialing",
                )
                .limit(1)
            )
        ).scalar_one_or_none()

        if sub is not None:
            sub.plan = "free"
            sub.status = "active"
            await self.db.flush()

    # ── Charge helper ───────────────────────────────────────────────────────

    async def _charge_trial(
        self, trial: Trial, *, idempotency_key: str
    ) -> ChargeResult:
        """Call the provider adapter to charge the stored card / preapproval.

        Never raises — returns ChargeResult(success=False) on any failure.
        Does NOT touch the DB; caller decides what to persist based on result.
        """
        if trial.provider is None or trial.provider_card_token is None:
            return ChargeResult(
                success=False,
                error_code="no_card",
                error_message="No stored card on trial",
            )

        provider = self._provider_for(trial.provider)
        amount_cents = PlanService.get_price_cents(trial.plan_code, seat_count=1)
        metadata = {
            "trial_id": str(trial.id),
            "user_id": str(trial.user_id),
            "plan_code": trial.plan_code,
        }
        return await provider.charge_stored_card(
            customer_id=trial.provider_customer_id or "",
            card_id=trial.provider_card_token,
            amount_cents=amount_cents,
            currency="PEN",
            metadata=metadata,
            idempotency_key=idempotency_key,
        )

    # ── User-facing API ─────────────────────────────────────────────────────

    async def start_trial(self, user_id: UUID, plan_code: str) -> Trial:
        """Create a new trial for the user.

        Checks:
          - BETA_MODE → 409
          - plan_code not in (pro, studio) → 422
          - existing trial for same plan → 409
          - existing active trial → 409

        Owns its own transaction.
        """
        async with self.db.begin():
            if getattr(self.settings, "beta_mode", False):
                raise TrialError(409, "BETA_MODE on — upgrade directo")

            if plan_code not in ("pro", "studio"):
                raise TrialError(422, "Cannot start trial for free plan")

            # Check 1 — plan already used (ever)
            used = (
                await self.db.execute(
                    select(Trial).where(
                        Trial.user_id == user_id,
                        Trial.plan_code == plan_code,
                    )
                )
            ).scalar_one_or_none()
            if used is not None:
                raise TrialError(409, f"Trial already used for plan '{plan_code}'")

            # Check 2 — currently active
            active = (
                await self.db.execute(
                    select(Trial).where(
                        Trial.user_id == user_id,
                        Trial.status == "active",
                    )
                )
            ).scalar_one_or_none()
            if active is not None:
                raise TrialError(409, "Trial already active for this user")

            trial = Trial(user_id=user_id, plan_code=plan_code)
            self.db.add(trial)
            await self.db.flush()

            await self._activate_subscription_trialing(user_id, plan_code)

            await self.audit.log_action(
                user_id=user_id,
                action="trial.started",
                resource_type="trial",
                resource_id=str(trial.id),
                after_state={
                    "plan_code": plan_code,
                    "ends_at": trial.ends_at.isoformat(),
                },
            )
        # Email is fire-and-forget, outside the transaction
        await self.email.send_trial_email(
            "trial.started_confirmation",
            user_id=user_id,
            trial_id=trial.id,
            plan_code=plan_code,
            days_remaining=14,
        )
        return trial

    async def add_card(
        self,
        trial_id: UUID,
        user_id: UUID,
        provider_name: str,
        token_id: str,
        customer_info: object,
    ) -> Trial:
        """Add a payment card to an active trial.

        Owns its own transaction. Provider HTTP calls happen inside the
        transaction (user is waiting — short latency acceptable).
        For MP, metadata (amount_cents, plan_code) is passed to create_card
        so the preapproval can be created with the correct amount while the
        fresh token is still valid.
        """
        async with self.db.begin():
            trial = await self._load_owned_for_update(trial_id, user_id)

            if trial.status != "active":
                raise TrialError(409, "Trial is not active")
            if trial.card_added_at is not None:
                raise TrialError(409, "Card already added to this trial")

            provider = self._provider_for(provider_name)

            # Create or reuse provider customer; map invalid-token errors to 400 (AC8)
            try:
                customer_id = trial.provider_customer_id
                if customer_id is None:
                    customer_id = await provider.create_customer(
                        email=getattr(customer_info, "email", ""),
                        first_name=getattr(customer_info, "first_name", ""),
                        last_name=getattr(customer_info, "last_name", ""),
                        phone=getattr(customer_info, "phone_number", None),
                    )

                # Metadata passed to create_card — required by MPAdapter for preapproval
                amount_cents = PlanService.get_price_cents(trial.plan_code, seat_count=1)
                meta = {
                    "email": getattr(customer_info, "email", ""),
                    "amount_cents": amount_cents,
                    "plan_code": trial.plan_code,
                    "currency": "PEN",
                }
                card_token = await provider.create_card(customer_id, token_id, meta)
            except ProviderError as exc:
                raise TrialError(400, exc.message or str(exc)) from exc

            now = datetime.now(UTC)
            trial.provider = provider_name
            trial.provider_customer_id = customer_id
            trial.provider_card_token = card_token
            trial.card_added_at = now
            trial.updated_at = now

            await self.audit.log_action(
                user_id=user_id,
                action="trial.card_added",
                resource_type="trial",
                resource_id=str(trial.id),
                after_state={"provider": provider_name},
            )
        await self.email.send_trial_email(
            "trial.card_added", user_id=user_id, trial_id=trial.id
        )
        return trial

    async def cancel(self, trial_id: UUID, user_id: UUID) -> Trial:
        """Cancel a trial (transition to canceled_pending).

        Idempotent: if already canceled/canceled_pending, returns as-is.
        Owns its own transaction.
        """
        async with self.db.begin():
            trial = await self._load_owned_for_update(trial_id, user_id)

            if trial.status in ("canceled_pending", "canceled"):
                return trial  # idempotent

            if trial.status not in ("active", "charge_failed"):
                raise TrialError(
                    422, f"Cannot cancel trial in status '{trial.status}'"
                )

            now = datetime.now(UTC)
            trial.status = "canceled_pending"
            trial.canceled_by_user = True
            trial.canceled_at = now
            trial.updated_at = now

            await self.audit.log_action(
                user_id=user_id,
                action="trial.canceled_by_user",
                resource_type="trial",
                resource_id=str(trial.id),
                after_state={"canceled_at": now.isoformat()},
            )
        await self.email.send_trial_email(
            "trial.canceled_confirmation",
            user_id=user_id,
            trial_id=trial.id,
            ends_at=trial.ends_at.isoformat(),
        )
        return trial

    async def retry_charge(self, trial_id: UUID, user_id: UUID) -> Trial:
        """User-initiated retry of a failed charge.

        Requires status='charge_failed' and open retry window (72h).
        HTTP call happens inside the transaction (user is waiting).
        Owns its own transaction.
        """
        async with self.db.begin():
            trial = await self._load_owned_for_update(trial_id, user_id)

            if trial.status != "charge_failed":
                raise TrialError(422, "Trial is not in charge_failed state")
            if trial.provider is None or trial.provider_card_token is None:
                raise TrialError(422, "No stored card on this trial")

            if trial.charge_failed_at is None or (
                datetime.now(UTC) - trial.charge_failed_at
                > timedelta(hours=RETRY_WINDOW_HOURS)
            ):
                raise TrialError(422, "Retry window has closed")

            idem_key = f"{trial.id}:user_retry:{trial.retry_count + 1}"
            result = await self._charge_trial(trial, idempotency_key=idem_key)

            now = datetime.now(UTC)
            if result.success:
                # Clear failed flags optimistically; webhook finalises to 'charged'
                trial.charge_failure_reason = None
                trial.updated_at = now
                await self.audit.log_action(
                    user_id=user_id,
                    action="trial.charge_retry_initiated",
                    resource_type="trial",
                    resource_id=str(trial.id),
                    after_state={"charge_id": result.provider_charge_id},
                )
            else:
                trial.retry_count += 1
                trial.charge_failed_at = now
                trial.charge_failure_reason = (
                    f"{result.error_code}: {result.error_message}"
                )[:500]
                trial.updated_at = now
                await self.audit.log_action(
                    user_id=user_id,
                    action="trial.charge_retry_failed",
                    resource_type="trial",
                    resource_id=str(trial.id),
                    after_state={
                        "error_code": result.error_code,
                        "retry_count": trial.retry_count,
                    },
                )
        return trial

    async def get_current(self, user_id: UUID) -> Optional[Trial]:
        """Return the most recent trial for the user (read-only, no transaction)."""
        q = (
            select(Trial)
            .where(Trial.user_id == user_id)
            .order_by(Trial.created_at.desc())
            .limit(1)
        )
        return (await self.db.execute(q)).scalar_one_or_none()

    # ── Admin API ───────────────────────────────────────────────────────────

    async def admin_list(
        self, f: AdminTrialFilters
    ) -> tuple[list[Trial], int]:
        """Paginated admin list with optional filters (no transaction needed)."""
        stmt = select(Trial)

        if f.status:
            stmt = stmt.where(Trial.status == f.status)
        if f.plan_code:
            stmt = stmt.where(Trial.plan_code == f.plan_code)
        if f.expiring_in_days is not None:
            cutoff = datetime.now(UTC) + timedelta(days=f.expiring_in_days)
            stmt = stmt.where(
                Trial.status == "active",
                Trial.ends_at <= cutoff,
            )

        count_q = select(func.count()).select_from(stmt.subquery())
        total: int = (await self.db.scalar(count_q)) or 0

        items = list(
            (
                await self.db.execute(
                    stmt.order_by(Trial.created_at.desc())
                    .offset((f.page - 1) * f.per_page)
                    .limit(f.per_page)
                )
            )
            .scalars()
            .all()
        )
        return items, total

    async def admin_patch(
        self, trial_id: UUID, admin_id: UUID, patch: AdminTrialPatch
    ) -> Trial:
        """Admin-initiated trial state transition. Owns its own transaction."""
        async with self.db.begin():
            trial = (
                await self.db.execute(
                    select(Trial).where(Trial.id == trial_id).with_for_update()
                )
            ).scalar_one_or_none()
            if trial is None:
                raise TrialError(404, "Trial not found")

            now = datetime.now(UTC)

            if patch.action == "force_downgrade":
                if trial.status in ("downgraded", "canceled", "charged"):
                    raise TrialError(
                        422, f"Already in terminal status '{trial.status}'"
                    )
                old_status = trial.status
                trial.status = "downgraded"
                trial.downgraded_at = now
                trial.updated_at = now
                await self._deactivate_to_free(trial.user_id)
                await self.audit.log_action(
                    user_id=admin_id,
                    action="trial.downgraded_no_card",
                    resource_type="trial",
                    resource_id=str(trial.id),
                    before_state={"status": old_status},
                    after_state={"status": "downgraded", "reason": patch.reason},
                )

            elif patch.action == "extend_days":
                if patch.extend_days is None:
                    raise TrialError(422, "extend_days is required for extend_days action")
                if trial.status not in ("active", "charge_failed"):
                    raise TrialError(
                        422, f"Cannot extend trial in status '{trial.status}'"
                    )
                trial.ends_at = trial.ends_at + timedelta(days=patch.extend_days)
                trial.updated_at = now
                await self.audit.log_action(
                    user_id=admin_id,
                    action="trial.extended",
                    resource_type="trial",
                    resource_id=str(trial.id),
                    after_state={
                        "extend_days": patch.extend_days,
                        "new_ends_at": trial.ends_at.isoformat(),
                    },
                )

            elif patch.action == "force_cancel":
                if trial.status in ("canceled", "downgraded", "charged"):
                    raise TrialError(
                        422, f"Cannot cancel trial in terminal status '{trial.status}'"
                    )
                trial.status = "canceled"
                trial.canceled_at = now
                trial.updated_at = now
                await self._deactivate_to_free(trial.user_id)
                await self.audit.log_action(
                    user_id=admin_id,
                    action="trial.expired",
                    resource_type="trial",
                    resource_id=str(trial.id),
                    after_state={"reason": patch.reason},
                )

            elif patch.action == "force_charge":
                if trial.status != "charge_failed":
                    raise TrialError(422, "force_charge requires charge_failed status")
                if trial.provider is None or trial.provider_card_token is None:
                    raise TrialError(422, "No stored card on this trial")
                idem_key = f"{trial.id}:admin_force:{int(now.timestamp())}"
                result = await self._charge_trial(trial, idempotency_key=idem_key)
                if result.success:
                    trial.charge_failure_reason = None
                    trial.updated_at = now
                    await self.audit.log_action(
                        user_id=admin_id,
                        action="trial.charge_retry_initiated",
                        resource_type="trial",
                        resource_id=str(trial.id),
                        after_state={
                            "charge_id": result.provider_charge_id,
                            "reason": patch.reason,
                        },
                    )
                else:
                    trial.retry_count += 1
                    trial.charge_failed_at = now
                    trial.charge_failure_reason = (
                        f"{result.error_code}: {result.error_message}"
                    )[:500]
                    trial.updated_at = now
                    await self.audit.log_action(
                        user_id=admin_id,
                        action="trial.charge_retry_failed",
                        resource_type="trial",
                        resource_id=str(trial.id),
                        after_state={"error": trial.charge_failure_reason},
                    )
            else:
                raise TrialError(422, f"Unknown action: '{patch.action}'")

        return trial

    # ── Scheduler / webhook internal transitions (caller owns transaction) ──

    async def mark_charged(
        self,
        trial_id: UUID,
        *,
        charge_id: str,
        provider: str,
        subscription_id: Optional[UUID] = None,
    ) -> Trial:
        """Mark trial as charged. Idempotent: no-op if already charged.

        Flush-only — webhook Phase 1 caller owns the transaction boundary.
        """
        # Idempotency: check-first (SA gotcha #2 — no begin_nested)
        trial = (
            await self.db.execute(select(Trial).where(Trial.id == trial_id))
        ).scalar_one_or_none()
        if trial is None:
            raise TrialError(404, f"Trial {trial_id} not found")
        if trial.charged_at is not None:
            logger.info(
                "trial.mark_charged: already charged — idempotent (trial_id=%s)",
                trial_id,
            )
            return trial

        now = datetime.now(UTC)
        trial.status = "charged"
        trial.charged_at = now
        trial.updated_at = now
        if subscription_id is not None:
            trial.subscription_id = subscription_id

        # Sync user.plan so BYOK gate stays consistent
        user = (
            await self.db.execute(select(User).where(User.id == trial.user_id))
        ).scalar_one_or_none()
        if user is not None:
            user.plan = trial.plan_code

        await self.audit.log_action(
            user_id=trial.user_id,
            action="trial.auto_charged",
            resource_type="trial",
            resource_id=str(trial_id),
            after_state={
                "charge_id": charge_id,
                "provider": provider,
                "charged_at": now.isoformat(),
            },
        )
        await self.db.flush()
        return trial

    async def mark_downgraded(self, trial_id: UUID) -> Trial:
        """Mark trial as downgraded and revert plan to free.

        Flush-only — scheduler caller owns the transaction boundary.
        """
        trial = (
            await self.db.execute(select(Trial).where(Trial.id == trial_id))
        ).scalar_one_or_none()
        if trial is None:
            raise TrialError(404, f"Trial {trial_id} not found")

        now = datetime.now(UTC)
        trial.status = "downgraded"
        trial.downgraded_at = now
        trial.updated_at = now

        await self._deactivate_to_free(trial.user_id)

        await self.audit.log_action(
            user_id=trial.user_id,
            action="trial.downgraded_no_card",
            resource_type="trial",
            resource_id=str(trial_id),
            after_state={"downgraded_at": now.isoformat()},
        )
        await self.db.flush()
        return trial

    async def mark_canceled(self, trial_id: UUID) -> Trial:
        """Mark trial as canceled (from canceled_pending at scheduler day-14 tick).

        Flush-only — scheduler caller owns the transaction boundary.
        """
        trial = (
            await self.db.execute(select(Trial).where(Trial.id == trial_id))
        ).scalar_one_or_none()
        if trial is None:
            raise TrialError(404, f"Trial {trial_id} not found")

        now = datetime.now(UTC)
        trial.status = "canceled"
        trial.updated_at = now
        if trial.canceled_at is None:
            trial.canceled_at = now

        await self._deactivate_to_free(trial.user_id)

        await self.audit.log_action(
            user_id=trial.user_id,
            action="trial.expired",
            resource_type="trial",
            resource_id=str(trial_id),
            after_state={"canceled_at": trial.canceled_at.isoformat()},
        )
        await self.db.flush()
        return trial

    async def mark_charge_failed(self, trial_id: UUID, *, reason: str) -> Trial:
        """Record a charge failure. Increments retry_count.

        Flush-only — scheduler caller owns the transaction boundary.
        """
        trial = (
            await self.db.execute(select(Trial).where(Trial.id == trial_id))
        ).scalar_one_or_none()
        if trial is None:
            raise TrialError(404, f"Trial {trial_id} not found")

        now = datetime.now(UTC)
        trial.status = "charge_failed"
        trial.charge_failed_at = now
        trial.charge_failure_reason = reason[:500]
        trial.retry_count = (trial.retry_count or 0) + 1
        trial.updated_at = now

        await self.audit.log_action(
            user_id=trial.user_id,
            action="trial.charge_failed",
            resource_type="trial",
            resource_id=str(trial_id),
            after_state={
                "reason": reason[:200],
                "retry_count": trial.retry_count,
            },
        )
        await self.db.flush()

        # Email outside flush (fire-and-forget; no transaction impact)
        await self.email.send_trial_email(
            "trial.charge_failed_update_card",
            user_id=trial.user_id,
            trial_id=trial.id,
            reason=reason,
        )
        return trial
