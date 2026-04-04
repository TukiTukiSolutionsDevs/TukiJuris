"""
Billing routes — plan listing, usage, subscription management.

Supports MercadoPago and Culqi as payment providers (dual-provider).

When no payment provider is configured, endpoints degrade gracefully:
  - /plans, /usage, /subscription work as before.
  - /checkout returns 503 with a human-readable message.
  - /webhook/mp and /webhook/culqi return {"status": "skipped"}.
  - /config returns payments_enabled: false, providers: [].

When one or more providers are configured, all payment operations are live.
"""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.organization import OrgMembership, Organization
from app.models.subscription import Subscription
from app.models.user import User
from app.services.payment_service import PLAN_PRICING, payment_service
from app.services.usage import PLAN_LIMITS, usage_service


logger = logging.getLogger(__name__)


async def _sync_member_plans(org_id: uuid.UUID, plan: str, db: AsyncSession) -> None:
    """Sync User.plan for all active members of an organization after a plan change."""
    members = await db.execute(
        select(User).join(OrgMembership, OrgMembership.user_id == User.id).where(
            OrgMembership.organization_id == org_id,
            OrgMembership.is_active == True,  # noqa: E712
        )
    )
    for member in members.scalars():
        member.plan = plan

router = APIRouter(prefix="/billing", tags=["billing"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class PlanDetail(BaseModel):
    name: str
    description: str
    areas: int
    multi_user: bool
    price_pen: float | None = None   # price in Peruvian Soles (None = contact sales)
    daily_limit: int | None = None   # -1 = unlimited, None = not applicable
    # BYOK: No model restrictions — users bring their own API keys.


class UsageResponse(BaseModel):
    org_id: str
    month: str
    total_queries: int
    total_tokens: int
    by_user: list[dict]


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    plan: str
    status: str
    current_period_start: datetime | None
    current_period_end: datetime | None
    payment_subscription_id: str | None

    model_config = {"from_attributes": True}


class CheckoutRequest(BaseModel):
    plan: str
    provider: str | None = None   # "mercadopago" | "culqi" — if None, use primary


class BillingConfigResponse(BaseModel):
    payments_enabled: bool
    providers: list[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _require_org_member(
    org_id: uuid.UUID,
    user: User,
    db: AsyncSession,
    allowed_roles: tuple[str, ...] = ("owner", "admin", "member"),
) -> Organization:
    """Return org if user is a member with one of the allowed_roles, else raise 403."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    membership_result = await db.execute(
        select(OrgMembership).where(
            OrgMembership.organization_id == org_id,
            OrgMembership.user_id == user.id,
            OrgMembership.is_active == True,  # noqa: E712
        )
    )
    membership = membership_result.scalar_one_or_none()
    if not membership or membership.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return org


async def _get_payer_email(org: Organization, db: AsyncSession) -> str:
    """Return the owner's email for the org — used as payer email for checkout."""
    result = await db.execute(
        select(OrgMembership).where(
            OrgMembership.organization_id == org.id,
            OrgMembership.role == "owner",
            OrgMembership.is_active == True,  # noqa: E712
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Organization has no owner — cannot process checkout.",
        )

    from app.models.user import User as UserModel  # local to avoid circular

    user_result = await db.execute(
        select(UserModel).where(UserModel.id == membership.user_id)
    )
    owner = user_result.scalar_one_or_none()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Owner user not found — cannot process checkout.",
        )

    return owner.email


# ---------------------------------------------------------------------------
# Routes — informational
# ---------------------------------------------------------------------------


@router.get("/config", response_model=BillingConfigResponse)
async def get_billing_config():
    """Return available payment providers and whether payments are enabled."""
    return BillingConfigResponse(
        payments_enabled=payment_service.is_available,
        providers=[p.name for p in payment_service.providers],
    )


@router.get("/plans", response_model=dict[str, PlanDetail])
async def list_plans():
    """
    Return all available plan tiers with pricing in Peruvian Soles.

    BYOK: Plans are for platform access only.
    No model restrictions — users bring their own API keys.
    """
    plans = {}
    for plan_key, limits in PLAN_LIMITS.items():
        pricing = PLAN_PRICING.get(plan_key, {})
        plans[plan_key] = PlanDetail(
            name=plan_key,
            description=limits.get("description", ""),
            areas=limits["areas"],
            multi_user=limits["multi_user"],
            price_pen=pricing.get("price"),
            daily_limit=limits.get("queries_day"),
        )
    return plans


@router.get("/{org_id}/usage", response_model=UsageResponse)
async def get_usage(
    org_id: uuid.UUID,
    month: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get query and token usage for an organization.
    Optionally filter by month (YYYY-MM). Defaults to current month.
    """
    await _require_org_member(org_id, current_user, db)
    data = await usage_service.get_usage(org_id, month=month)
    return data


@router.get("/{org_id}/subscription", response_model=SubscriptionResponse | None)
async def get_subscription(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the latest active subscription for an organization."""
    await _require_org_member(org_id, current_user, db)

    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.organization_id == org_id,
            Subscription.status == "active",
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Routes — Payment operations
# ---------------------------------------------------------------------------


@router.post("/{org_id}/checkout")
async def create_checkout_session(
    org_id: uuid.UUID,
    body: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a checkout session for upgrading to the requested plan.

    Accepts optional `provider` field ("mercadopago" | "culqi").
    If omitted, uses the primary configured provider (prefers MercadoPago).

    Returns {"checkout_url": "https://..."}.
    Returns 503 when no payment provider is configured.
    """
    if not payment_service.is_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No payment provider configured — set MP_ACCESS_TOKEN or CULQI_SECRET_KEY.",
        )

    if body.plan not in PLAN_LIMITS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown plan '{body.plan}'. Valid plans: {list(PLAN_LIMITS.keys())}",
        )

    if body.plan == "free":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a checkout session for the free plan.",
        )

    plan_pricing = PLAN_PRICING.get(body.plan)
    if not plan_pricing or not plan_pricing.get("price"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Plan '{body.plan}' requires contacting sales — no self-serve checkout.",
        )

    # Resolve provider
    if body.provider:
        provider = payment_service.get_provider(body.provider)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider '{body.provider}' is not available or not configured.",
            )
    else:
        provider = payment_service.primary

    org = await _require_org_member(org_id, current_user, db, ("owner",))
    payer_email = await _get_payer_email(org, db)

    from app.config import settings as _settings
    success_url = f"{_settings.frontend_url}/billing/success"
    cancel_url = f"{_settings.frontend_url}/billing/cancel"

    checkout_url = await provider.create_checkout(
        plan=body.plan,
        org_id=str(org_id),
        payer_email=payer_email,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    logger.info(
        "billing.checkout: org=%s plan=%s provider=%s user=%s",
        org_id,
        body.plan,
        provider.name,
        current_user.id,
    )
    return {"checkout_url": checkout_url, "provider": provider.name}


# ---------------------------------------------------------------------------
# Webhooks — one endpoint per provider
# ---------------------------------------------------------------------------


@router.post("/webhook/mp", status_code=status.HTTP_200_OK)
async def mercadopago_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    MercadoPago webhook endpoint.

    Handled event types:
      - payment           -> payment approved → activate subscription
      - preapproval       -> subscription updated / deleted
    """
    provider = payment_service.get_provider("mercadopago")
    if not provider:
        logger.debug("billing.webhook.mp: MercadoPago not configured, skipping.")
        return {"status": "skipped", "reason": "mercadopago not configured"}

    payload = await request.body()
    headers = dict(request.headers)

    event = await provider.verify_webhook(payload, headers)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MercadoPago webhook payload.",
        )

    event_type: str = event.get("type", "")
    logger.info("billing.webhook.mp: received type=%s", event_type)

    raw = event.get("raw", {})

    # Extract payment/subscription metadata
    metadata = raw.get("metadata", {})
    org_id_str = metadata.get("org_id", "")
    plan = metadata.get("plan", "")
    data_id = event.get("data_id", "")

    if event_type in ("payment",):
        # Payment approved → activate plan
        payment_data = {
            "org_id": org_id_str,
            "plan": plan,
            "status": "active",
            "subscription_id": data_id,
            "provider": "mercadopago",
        }
        await _handle_checkout_completed(payment_data, db)

    elif event_type in ("preapproval",):
        status_value = raw.get("status", "")
        payment_data = {
            "org_id": org_id_str,
            "plan": plan,
            "status": status_value,
            "subscription_id": data_id,
            "provider": "mercadopago",
        }
        if status_value == "cancelled":
            await _handle_subscription_deleted(payment_data, db)
        else:
            await _handle_subscription_updated(payment_data, db)

    else:
        logger.debug("billing.webhook.mp: unhandled event type=%s", event_type)

    return {"status": "ok"}


@router.post("/webhook/culqi", status_code=status.HTTP_200_OK)
async def culqi_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Culqi webhook endpoint.

    Handled event types:
      - charge.succeeded      -> payment approved → activate subscription
      - order.paid            -> order paid → activate subscription
      - subscription.updated  -> sync plan / status
      - subscription.deleted  -> downgrade org to free
      - charge.failed         -> mark subscription as past_due
    """
    provider = payment_service.get_provider("culqi")
    if not provider:
        logger.debug("billing.webhook.culqi: Culqi not configured, skipping.")
        return {"status": "skipped", "reason": "culqi not configured"}

    payload = await request.body()
    headers = dict(request.headers)

    event = await provider.verify_webhook(payload, headers)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Culqi webhook payload.",
        )

    event_type: str = event.get("type", "")
    logger.info("billing.webhook.culqi: received type=%s", event_type)

    raw = event.get("raw", {})
    data = raw.get("data", {})
    metadata = data.get("metadata", raw.get("metadata", {}))

    org_id_str = metadata.get("org_id", "")
    plan = metadata.get("plan", "")
    data_id = event.get("data_id", "")

    if event_type in ("charge.succeeded", "order.paid"):
        payment_data = {
            "org_id": org_id_str,
            "plan": plan,
            "status": "active",
            "subscription_id": data_id,
            "provider": "culqi",
        }
        await _handle_checkout_completed(payment_data, db)

    elif event_type == "subscription.updated":
        payment_data = {
            "org_id": org_id_str,
            "plan": plan,
            "status": data.get("status", "active"),
            "subscription_id": data_id,
            "provider": "culqi",
        }
        await _handle_subscription_updated(payment_data, db)

    elif event_type == "subscription.deleted":
        payment_data = {
            "org_id": org_id_str,
            "plan": plan,
            "status": "cancelled",
            "subscription_id": data_id,
            "provider": "culqi",
        }
        await _handle_subscription_deleted(payment_data, db)

    elif event_type == "charge.failed":
        payment_data = {
            "org_id": org_id_str,
            "plan": plan,
            "status": "past_due",
            "subscription_id": data_id,
            "provider": "culqi",
        }
        await _handle_payment_failed(payment_data, db)

    else:
        logger.debug("billing.webhook.culqi: unhandled event type=%s", event_type)

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Webhook event handlers (private)
# ---------------------------------------------------------------------------


async def _handle_checkout_completed(payment_data: dict, db: AsyncSession) -> None:
    """
    Payment approved — a customer completed payment.

    payment_data keys:
      - org_id (str)
      - plan (str)
      - status (str)
      - subscription_id (str)
      - provider (str)

    Updates:
      - Organization.payment_subscription_id
      - Organization.payment_provider
      - Organization.plan + plan_queries_limit + plan_models_allowed
      - Subscription record (cancel existing, create new)
    """
    org_id_str: str = payment_data.get("org_id", "")
    plan: str = payment_data.get("plan", "")
    subscription_id: str = payment_data.get("subscription_id", "")
    provider: str = payment_data.get("provider", "")

    if not org_id_str or not plan:
        logger.warning(
            "billing.webhook _handle_checkout_completed: missing org_id or plan in payment_data"
        )
        return

    try:
        org_uuid = uuid.UUID(org_id_str)
    except ValueError:
        logger.warning("billing.webhook: invalid org_id: %s", org_id_str)
        return

    result = await db.execute(select(Organization).where(Organization.id == org_uuid))
    org = result.scalar_one_or_none()
    if not org:
        logger.warning("billing.webhook: org %s not found", org_uuid)
        return

    # Use plan from PLAN_LIMITS — fallback to "base" if unknown
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS.get("base", {}))

    # Update organization
    org.payment_subscription_id = subscription_id or None
    org.payment_provider = provider
    org.plan = plan
    # BYOK: No query caps or model restrictions — set unlimited/all-access values.
    org.plan_queries_limit = -1   # unlimited
    org.plan_models_allowed = ["*"]  # all models

    # Sync plan to all active org members
    await _sync_member_plans(org_uuid, plan, db)

    # Cancel existing active subscriptions
    existing_result = await db.execute(
        select(Subscription).where(
            Subscription.organization_id == org_uuid,
            Subscription.status == "active",
        )
    )
    for sub in existing_result.scalars().all():
        sub.status = "canceled"

    # Create the new subscription record
    now = datetime.now(UTC)
    new_sub = Subscription(
        organization_id=org_uuid,
        plan=plan,
        status="active",
        payment_subscription_id=subscription_id or None,
        payment_plan_id=plan,
        payment_provider=provider,
        current_period_start=now,
        current_period_end=None,  # MP/Culqi don't always return this on checkout
    )
    db.add(new_sub)
    await db.flush()

    # Fire-and-forget: payment confirmation email
    try:
        from app.services.email_service import email_service

        plan_info = PLAN_PRICING.get(plan, {})
        price_str = str(plan_info.get("price", "")) if plan_info.get("price") else "Contactar"

        # Get owner email
        owner_result = await db.execute(
            select(User).join(OrgMembership).where(
                OrgMembership.organization_id == org_uuid,
                OrgMembership.role == "owner",
                OrgMembership.is_active == True,  # noqa: E712
            )
        )
        owner = owner_result.scalar_one_or_none()
        if owner:
            await email_service.send_payment_confirmation(
                to=owner.email,
                plan_name=plan.capitalize(),
                amount=price_str,
                next_billing_date="—",
            )
    except Exception as exc:
        logger.warning("Payment confirmation email failed: %s", exc)

    logger.info(
        "billing.webhook checkout_completed: org=%s plan=%s provider=%s sub=%s",
        org_uuid,
        plan,
        provider,
        subscription_id,
    )


async def _handle_subscription_updated(payment_data: dict, db: AsyncSession) -> None:
    """
    Subscription updated — plan changed, renewal processed, etc.

    Syncs plan and status to the local Subscription row.
    """
    subscription_id: str = payment_data.get("subscription_id", "")
    plan: str = payment_data.get("plan", "")
    new_status: str = payment_data.get("status", "active")
    provider: str = payment_data.get("provider", "")
    org_id_str: str = payment_data.get("org_id", "")

    # Try to find by subscription_id first
    if subscription_id:
        result = await db.execute(
            select(Subscription).where(
                Subscription.payment_subscription_id == subscription_id
            )
        )
        local_sub = result.scalar_one_or_none()
    else:
        local_sub = None

    # Fallback: find by org_id
    if not local_sub and org_id_str:
        try:
            org_uuid = uuid.UUID(org_id_str)
            result = await db.execute(
                select(Subscription).where(
                    Subscription.organization_id == org_uuid,
                    Subscription.status == "active",
                ).order_by(Subscription.created_at.desc()).limit(1)
            )
            local_sub = result.scalar_one_or_none()
        except ValueError:
            pass

    if not local_sub:
        logger.warning(
            "billing.webhook subscription.updated: no local subscription for id=%s",
            subscription_id,
        )
        return

    if plan:
        local_sub.plan = plan
    local_sub.status = new_status

    # Keep org in sync
    org_result = await db.execute(
        select(Organization).where(Organization.id == local_sub.organization_id)
    )
    org = org_result.scalar_one_or_none()
    if org:
        if plan:
            org.plan = plan
        # BYOK: No query caps or model restrictions.
        org.plan_queries_limit = -1
        org.plan_models_allowed = ["*"]
        await _sync_member_plans(local_sub.organization_id, local_sub.plan, db)

    await db.flush()
    logger.info(
        "billing.webhook subscription.updated: id=%s plan=%s status=%s provider=%s",
        subscription_id,
        plan,
        new_status,
        provider,
    )


async def _handle_subscription_deleted(payment_data: dict, db: AsyncSession) -> None:
    """
    Subscription ended or was canceled immediately.

    Downgrades the org to the free plan and marks the local subscription as canceled.
    """
    subscription_id: str = payment_data.get("subscription_id", "")
    org_id_str: str = payment_data.get("org_id", "")

    # Try to find by subscription_id first
    if subscription_id:
        result = await db.execute(
            select(Subscription).where(
                Subscription.payment_subscription_id == subscription_id
            )
        )
        local_sub = result.scalar_one_or_none()
    else:
        local_sub = None

    # Fallback: find by org_id
    if not local_sub and org_id_str:
        try:
            org_uuid = uuid.UUID(org_id_str)
            result = await db.execute(
                select(Subscription).where(
                    Subscription.organization_id == org_uuid,
                    Subscription.status == "active",
                ).order_by(Subscription.created_at.desc()).limit(1)
            )
            local_sub = result.scalar_one_or_none()
        except ValueError:
            pass

    if not local_sub:
        logger.warning(
            "billing.webhook subscription.deleted: no local subscription for id=%s",
            subscription_id,
        )
        return

    local_sub.status = "canceled"

    # Downgrade org to free plan (platform access revoked)
    org_result = await db.execute(
        select(Organization).where(Organization.id == local_sub.organization_id)
    )
    org = org_result.scalar_one_or_none()
    if org:
        org.plan = "free"
        org.payment_subscription_id = None
        # BYOK: Even free plan has no query caps — users use their own keys.
        org.plan_queries_limit = -1
        org.plan_models_allowed = ["*"]
        # Sync downgrade to all active org members
        await _sync_member_plans(local_sub.organization_id, "free", db)

    await db.flush()
    logger.info(
        "billing.webhook subscription.deleted: id=%s org=%s downgraded to free",
        subscription_id,
        local_sub.organization_id,
    )


async def _handle_payment_failed(payment_data: dict, db: AsyncSession) -> None:
    """
    Payment failed — a renewal charge failed.

    Marks the subscription as past_due so the frontend can warn the user.
    """
    subscription_id: str = payment_data.get("subscription_id", "")
    org_id_str: str = payment_data.get("org_id", "")

    # Try to find by subscription_id first
    if subscription_id:
        result = await db.execute(
            select(Subscription).where(
                Subscription.payment_subscription_id == subscription_id
            )
        )
        local_sub = result.scalar_one_or_none()
    else:
        local_sub = None

    # Fallback: find by org_id
    if not local_sub and org_id_str:
        try:
            org_uuid = uuid.UUID(org_id_str)
            result = await db.execute(
                select(Subscription).where(
                    Subscription.organization_id == org_uuid,
                    Subscription.status == "active",
                ).order_by(Subscription.created_at.desc()).limit(1)
            )
            local_sub = result.scalar_one_or_none()
        except ValueError:
            pass

    if not local_sub:
        logger.warning(
            "billing.webhook payment.failed: no local subscription for id=%s",
            subscription_id,
        )
        return

    local_sub.status = "past_due"
    await db.flush()
    logger.info(
        "billing.webhook payment.failed: id=%s marked past_due",
        subscription_id,
    )
