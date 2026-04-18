"""Authentication routes — register, login, refresh, logout, sessions."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_refresh_service
from app.core.database import get_db
from app.core.exceptions import AuthError
from app.core.rate_limiter import refresh_rate_limit
from app.core.security import (
    check_login_attempts,
    hash_password,
    verify_password,
)
from app.core.validators import validate_password
from app.models.user import User
from app.rbac.constants import SystemRole
from app.rbac.dependencies import get_user_permissions_dep
from app.rbac.models import Role as RBACRole
from app.rbac.models import UserRole as RBACUserRole
from app.rbac.schemas import PermissionSetResponse
from app.services.email_service import email_service
from app.services.notification_service import notification_service
from app.services.refresh_token_service import RefreshTokenService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={
        422: {"description": "Validation error — invalid request body"},
    },
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPairResponse(BaseModel):
    """Returned by register, login, and refresh endpoints."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # access token TTL in seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class LogoutAllResponse(BaseModel):
    revoked: int


class SessionResponse(BaseModel):
    jti: str
    family_id: str
    created_at: str
    expires_at: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    plan: str
    is_active: bool

    model_config = {"from_attributes": True}


class UpdateProfileBody(BaseModel):
    full_name: str | None = None
    default_org_id: uuid.UUID | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_device_info(request: Request) -> dict:
    """Extract user-agent and IP from request for device fingerprinting."""
    return {
        "user_agent": request.headers.get("user-agent", "unknown"),
        "ip_address": request.client.host if request.client else "unknown",
    }


_PRIVILEGED_ROLES: frozenset[str] = frozenset({
    SystemRole.SUPER_ADMIN.value,
    SystemRole.ADMIN.value,
    SystemRole.SUPPORT.value,
    SystemRole.FINANCE.value,
})


async def _has_privileged_role(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """Return True if user has any privileged role requiring SSO authentication."""
    stmt = (
        select(RBACRole.name)
        .join(RBACUserRole, RBACUserRole.role_id == RBACRole.id)
        .where(RBACUserRole.user_id == user_id)
    )
    result = await db.execute(stmt)
    role_names = set(result.scalars())
    return bool(role_names & _PRIVILEGED_ROLES)


def _auth_error_response(exc: AuthError) -> JSONResponse:
    """Convert a domain AuthError into a structured 401 JSONResponse."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.detail_msg, "error_code": exc.error_code},
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=TokenPairResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
    description=(
        "Create a new user account. Returns an access + refresh token pair. "
        "Password must be at least 8 characters with uppercase, lowercase, and a digit."
    ),
    responses={
        201: {"description": "Account created — token pair returned"},
        409: {"description": "Email already registered"},
        422: {"description": "Password does not meet policy requirements"},
    },
)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: RefreshTokenService = Depends(get_refresh_service),
) -> TokenPairResponse:
    """Register a new user, return access + refresh token pair."""
    is_valid, error = validate_password(body.password)
    if not is_valid:
        raise HTTPException(status_code=422, detail=error)

    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    await db.flush()  # assign user.id before passing to service

    pair = await service.issue_pair(user, _extract_device_info(request))

    # Fire-and-forget: welcome email
    try:
        await email_service.send_welcome(
            to=user.email,
            name=user.full_name or user.email,
        )
    except Exception as exc:
        logger.warning("Welcome email failed for %s: %s", user.email, exc)

    # Fire-and-forget: welcome notification
    try:
        await notification_service.welcome(
            user_id=user.id,
            name=user.full_name or user.email,
        )
    except Exception as exc:
        logger.warning("Welcome notification failed for %s: %s", user.id, exc)

    return TokenPairResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=pair.expires_in,
    )


@router.post(
    "/login",
    response_model=TokenPairResponse,
    summary="Login with email and password",
    description=(
        "Authenticate and receive an access + refresh token pair. "
        "Login attempts are rate-limited per IP."
    ),
    responses={
        200: {"description": "Login successful — token pair returned"},
        401: {"description": "Invalid email or password"},
        403: {"description": "Account is disabled"},
        429: {"description": "Too many login attempts"},
    },
)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: RefreshTokenService = Depends(get_refresh_service),
) -> TokenPairResponse:
    """Login with email and password, return access + refresh token pair."""
    client_ip = request.client.host if request.client else "unknown"

    if not await check_login_attempts(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Try again later.",
        )

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    # T5.6 — SSO enforcement: privileged accounts must use Google SSO
    if await _has_privileged_role(db, user.id):
        raise HTTPException(
            status_code=403,
            detail="Privileged accounts must use Google SSO",
        )

    pair = await service.issue_pair(user, _extract_device_info(request))

    return TokenPairResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=pair.expires_in,
    )


@router.post(
    "/refresh",
    response_model=TokenPairResponse,
    summary="Rotate a refresh token",
    description=(
        "Exchange a valid refresh token for a new access + refresh token pair. "
        "The old refresh token is revoked (rotation). Reuse of a revoked token "
        "kills the entire token family and returns 401."
    ),
    responses={
        200: {"description": "New token pair issued"},
        401: {"description": "Invalid, expired, revoked, or reused refresh token"},
        422: {"description": "Missing refresh_token field"},
    },
)
async def refresh(
    body: RefreshRequest,
    request: Request,
    service: RefreshTokenService = Depends(get_refresh_service),
    _rl: None = Depends(refresh_rate_limit),
) -> JSONResponse | TokenPairResponse:
    """Rotate a refresh token — returns a new access + refresh pair."""
    try:
        pair = await service.rotate(body.refresh_token, _extract_device_info(request))
    except AuthError as exc:
        return _auth_error_response(exc)

    return TokenPairResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=pair.expires_in,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout (single device)",
    description=(
        "Revoke the provided refresh token. Idempotent — no error if the token "
        "is already revoked or not found. Requires a valid access token."
    ),
    responses={
        204: {"description": "Logged out — refresh token revoked"},
        401: {"description": "Access token missing or invalid"},
    },
)
async def logout(
    body: LogoutRequest,
    service: RefreshTokenService = Depends(get_refresh_service),
    current_user: User = Depends(get_current_user),
) -> None:
    """Revoke a single refresh token (single-device logout)."""
    if body.refresh_token:
        await service.revoke(body.refresh_token)


@router.post(
    "/logout-all",
    response_model=LogoutAllResponse,
    summary="Logout all devices",
    description="Revoke all active refresh tokens for the current user.",
    responses={
        200: {"description": "All sessions revoked"},
        401: {"description": "Access token missing or invalid"},
    },
)
async def logout_all(
    service: RefreshTokenService = Depends(get_refresh_service),
    current_user: User = Depends(get_current_user),
) -> LogoutAllResponse:
    """Revoke all refresh tokens for the current user (all-device logout)."""
    count = await service.revoke_all(current_user.id)
    return LogoutAllResponse(revoked=count)


@router.get(
    "/sessions",
    response_model=list[SessionResponse],
    summary="List active sessions",
    description="Return all active (non-revoked, non-expired) refresh token sessions.",
    responses={
        200: {"description": "List of active sessions"},
        401: {"description": "Access token missing or invalid"},
    },
)
async def list_sessions(
    service: RefreshTokenService = Depends(get_refresh_service),
    current_user: User = Depends(get_current_user),
) -> list[SessionResponse]:
    """List active refresh token sessions for the current user."""
    sessions = await service.list_sessions(current_user.id)
    return [
        SessionResponse(
            jti=s.jti,
            family_id=s.family_id,
            created_at=s.created_at.isoformat(),
            expires_at=s.expires_at.isoformat(),
        )
        for s in sessions
    ]


@router.get(
    "/me",
    summary="Get current user profile",
    description="Returns the authenticated user's profile data.",
)
async def get_current_profile(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return the current user's profile."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "avatar_url": current_user.avatar_url,
        "plan": current_user.plan,
        "is_admin": current_user.is_admin,
        "auth_provider": current_user.auth_provider,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }


@router.get(
    "/me/permissions",
    response_model=PermissionSetResponse,
    summary="Get current user permissions",
    description="Return the full set of permission strings for the authenticated user.",
)
async def get_my_permissions(
    permissions: set[str] = Depends(get_user_permissions_dep),
) -> PermissionSetResponse:
    """Return the current user's permission set, sorted for deterministic output."""
    return PermissionSetResponse(permissions=sorted(permissions))


@router.put(
    "/me",
    summary="Update current user profile",
    description="Update mutable profile fields: full_name and default_org_id.",
)
async def update_profile(
    body: UpdateProfileBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update the current user's profile fields."""
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.default_org_id is not None:
        current_user.default_org_id = body.default_org_id
    await db.flush()
    return {"status": "updated"}
