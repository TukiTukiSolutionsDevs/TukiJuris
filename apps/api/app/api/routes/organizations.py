"""Organization management routes — create, list, invite, manage members."""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RateLimitBucket, RateLimitGuard, get_current_user
from app.config import settings
from app.core.database import get_db
from app.models.organization import OrgMembership, Organization
from app.models.trial import Trial
from app.models.user import User
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organizations", tags=["organizations"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class OrgCreate(BaseModel):
    name: str
    slug: str

    @field_validator("slug")
    @classmethod
    def slug_must_be_url_safe(cls, v: str) -> str:
        import re
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("slug must contain only lowercase letters, digits, and hyphens")
        return v


class OrgUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class OrgResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    plan: str
    plan_queries_limit: int
    plan_models_allowed: list
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    role: str
    joined_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class InviteRequest(BaseModel):
    email: str
    role: str = "member"

    @field_validator("role")
    @classmethod
    def role_must_be_valid(cls, v: str) -> str:
        if v not in ("owner", "admin", "member"):
            raise ValueError("role must be one of: owner, admin, member")
        return v


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_org_or_404(org_id: uuid.UUID, db: AsyncSession) -> Organization:
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


async def _require_role(
    org_id: uuid.UUID,
    user: User,
    db: AsyncSession,
    allowed_roles: tuple[str, ...],
) -> OrgMembership:
    """Return the membership row or raise 403 if user is not in allowed_roles."""
    result = await db.execute(
        select(OrgMembership).where(
            OrgMembership.organization_id == org_id,
            OrgMembership.user_id == user.id,
            OrgMembership.is_active == True,  # noqa: E712
        )
    )
    membership = result.scalar_one_or_none()
    if not membership or membership.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this organization",
        )
    return membership


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    body: OrgCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """Create a new organization. The requesting user becomes owner."""
    # Check slug uniqueness
    existing = await db.execute(select(Organization).where(Organization.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slug already taken",
        )

    org = Organization(name=body.name, slug=body.slug)
    db.add(org)
    await db.flush()  # get org.id before creating membership

    membership = OrgMembership(
        user_id=current_user.id,
        organization_id=org.id,
        role="owner",
        joined_at=datetime.now(UTC),
    )
    db.add(membership)
    await db.flush()

    return org


@router.get("/", response_model=list[OrgResponse])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
):
    """List all organizations the current user belongs to."""
    result = await db.execute(
        select(Organization)
        .join(OrgMembership, OrgMembership.organization_id == Organization.id)
        .where(
            OrgMembership.user_id == current_user.id,
            OrgMembership.is_active == True,  # noqa: E712
            Organization.is_active == True,  # noqa: E712
        )
    )
    return result.scalars().all()


@router.get("/{org_id}", response_model=OrgResponse)
async def get_organization(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
):
    """Get organization details. User must be a member."""
    org = await _get_org_or_404(org_id, db)
    await _require_role(org_id, current_user, db, ("owner", "admin", "member"))
    return org


@router.put("/{org_id}", response_model=OrgResponse)
async def update_organization(
    org_id: uuid.UUID,
    body: OrgUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """Update organization. Requires owner or admin role."""
    org = await _get_org_or_404(org_id, db)
    await _require_role(org_id, current_user, db, ("owner", "admin"))

    if body.name is not None:
        org.name = body.name
    if body.is_active is not None:
        org.is_active = body.is_active

    await db.flush()
    return org


@router.post("/{org_id}/invite", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    org_id: uuid.UUID,
    body: InviteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """
    Invite a user by email to the organization.
    Only owner/admin can invite. The invited user must already have an account.
    """
    await _get_org_or_404(org_id, db)
    await _require_role(org_id, current_user, db, ("owner", "admin"))

    # Block studio trial owners from inviting members: studio trial is single-seat
    # until payment is confirmed. Card-holders will be promoted after auto-charge.
    active_studio_trial = (
        await db.execute(
            select(Trial).where(
                Trial.user_id == current_user.id,
                Trial.plan_code == "studio",
                Trial.status == "active",
            )
        )
    ).scalar_one_or_none()
    if active_studio_trial is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot invite members during an active studio trial. "
                   "Add a payment card to unlock multi-user access.",
        )

    # Resolve invite target
    user_result = await db.execute(select(User).where(User.email == body.email))
    invitee = user_result.scalar_one_or_none()
    if not invitee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found for that email",
        )

    # Prevent duplicates
    existing_membership = await db.execute(
        select(OrgMembership).where(
            OrgMembership.organization_id == org_id,
            OrgMembership.user_id == invitee.id,
        )
    )
    if existing_membership.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this organization",
        )

    now = datetime.now(UTC)
    membership = OrgMembership(
        user_id=invitee.id,
        organization_id=org_id,
        role=body.role,
        invited_by=current_user.id,
        invited_at=now,
        joined_at=now,
    )
    db.add(membership)
    await db.flush()

    # Fire-and-forget: send invitation email (never block the response)
    org = await _get_org_or_404(org_id, db)
    try:
        await email_service.send_org_invite(
            to=body.email,
            inviter_name=current_user.full_name or current_user.email,
            org_name=org.name,
            invite_url=f"{settings.frontend_url}/organizacion?invite={membership.id}",
        )
    except Exception as exc:
        logger.warning("Invite email failed for %s: %s", body.email, exc)

    return membership


@router.get("/{org_id}/members", response_model=list[MemberResponse])
async def list_members(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
):
    """List all active members of an organization."""
    await _get_org_or_404(org_id, db)
    await _require_role(org_id, current_user, db, ("owner", "admin", "member"))

    result = await db.execute(
        select(OrgMembership).where(
            OrgMembership.organization_id == org_id,
            OrgMembership.is_active == True,  # noqa: E712
        )
    )
    return result.scalars().all()


@router.delete(
    "/{org_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """
    Remove a member from the organization.
    Owner/admin can remove any member. Members cannot remove themselves
    if they are the only owner.
    """
    await _get_org_or_404(org_id, db)
    await _require_role(org_id, current_user, db, ("owner", "admin"))

    # Prevent removing the sole owner
    if user_id == current_user.id:
        owners_result = await db.execute(
            select(OrgMembership).where(
                OrgMembership.organization_id == org_id,
                OrgMembership.role == "owner",
                OrgMembership.is_active == True,  # noqa: E712
            )
        )
        owners = owners_result.scalars().all()
        if len(owners) == 1 and owners[0].user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the sole owner of an organization",
            )

    target_result = await db.execute(
        select(OrgMembership).where(
            OrgMembership.organization_id == org_id,
            OrgMembership.user_id == user_id,
        )
    )
    target = target_result.scalar_one_or_none()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this organization",
        )

    target.is_active = False
    await db.flush()
