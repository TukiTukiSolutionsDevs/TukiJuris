"""Authentication routes — register, login, refresh, logout, sessions."""

import logging
import uuid

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jose import JWTError, jwt as jose_jwt

from app.api.deps import RateLimitBucket, RateLimitGuard, get_audit_service, get_current_user, get_refresh_service
from app.config import settings
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


class AccessTokenResponse(BaseModel):
    """Returned by login, register, refresh, and OAuth endpoints.

    The refresh token is delivered via Set-Cookie (HttpOnly, SameSite=Lax,
    Path=/api/auth) and is NOT present in the JSON body.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # access token TTL in seconds


class TokenPairResponse(BaseModel):
    """Deprecated — kept for internal DTO compatibility only.

    External HTTP responses now use AccessTokenResponse. The refresh token
    is delivered via httpOnly cookie, not in the JSON body.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900


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
# Cookie constants
# ---------------------------------------------------------------------------

_REFRESH_COOKIE_NAME = "refresh_token"
_REFRESH_COOKIE_PATH = "/api/auth"
_TK_SESSION_COOKIE_NAME = "tk_session"
_TK_SESSION_COOKIE_PATH = "/"
_COOKIE_MAX_AGE = 30 * 24 * 3600  # 30 days — matches REFRESH_TOKEN_TTL_DAYS


# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------


def _set_session_cookies(response: Response, refresh_token: str) -> None:
    """Set both refresh_token (Path=/api/auth) and tk_session (Path=/) cookies.

    refresh_token: httpOnly, scoped to /api/auth — JS cannot read it.
    tk_session:    httpOnly, scoped to / — lets Next.js middleware detect
                   login state without exposing token material.

    When ``settings.cookie_domain`` is set (e.g. ".tukijuris.net.pe"), the
    ``Domain`` attribute is included so the cookies are shared across
    subdomains.  When empty (localhost dev), the attribute is fully absent —
    not "Domain=", but absent — so the cookie becomes host-only.
    """
    _secure = not settings.app_debug
    _domain_kw: dict = {"domain": settings.cookie_domain} if settings.cookie_domain else {}
    response.set_cookie(
        key=_REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=_COOKIE_MAX_AGE,
        httponly=True,
        secure=_secure,
        samesite="lax",
        path=_REFRESH_COOKIE_PATH,
        **_domain_kw,
    )
    response.set_cookie(
        key=_TK_SESSION_COOKIE_NAME,
        value="1",
        max_age=_COOKIE_MAX_AGE,
        httponly=True,
        secure=_secure,
        samesite="lax",
        path=_TK_SESSION_COOKIE_PATH,
        **_domain_kw,
    )


def _clear_session_cookies(response: Response) -> None:
    """Expire both session cookies (Max-Age=0) on the given response.

    Safe to call on any Response or JSONResponse instance.
    Domain kwarg is included only when ``settings.cookie_domain`` is set —
    the clear directive must carry the same Domain as the original Set-Cookie.
    """
    _secure = not settings.app_debug
    _domain_kw: dict = {"domain": settings.cookie_domain} if settings.cookie_domain else {}
    response.delete_cookie(
        key=_REFRESH_COOKIE_NAME,
        path=_REFRESH_COOKIE_PATH,
        httponly=True,
        secure=_secure,
        samesite="lax",
        **_domain_kw,
    )
    response.delete_cookie(
        key=_TK_SESSION_COOKIE_NAME,
        path=_TK_SESSION_COOKIE_PATH,
        httponly=True,
        secure=_secure,
        samesite="lax",
        **_domain_kw,
    )


# ---------------------------------------------------------------------------
# Other helpers
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


def _auth_error_response(exc: AuthError, *, clear_cookies: bool = False) -> JSONResponse:
    """Convert a domain AuthError into a structured 401 JSONResponse.

    When clear_cookies=True the response also expires both session cookies,
    preventing stale cookie state after a rotation failure or reuse event.
    We call _clear_session_cookies directly on the JSONResponse because
    FastAPI does NOT merge the injected Response headers when the route
    returns a Response subclass directly.
    """
    resp = JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.detail_msg, "error_code": exc.error_code},
    )
    if clear_cookies:
        _clear_session_cookies(resp)
    return resp


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=AccessTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
    description=(
        "Create a new user account. Returns an access token in the JSON body "
        "and sets an httpOnly refresh-token cookie (Path=/api/auth). "
        "Password must be at least 8 characters with uppercase, lowercase, and a digit."
    ),
    responses={
        201: {"description": "Account created — access token returned, refresh cookie set"},
        409: {"description": "Email already registered"},
        422: {"description": "Password does not meet policy requirements"},
    },
)
async def register(
    body: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    service: RefreshTokenService = Depends(get_refresh_service),
) -> AccessTokenResponse:
    """Register a new user, return access token + set refresh-token cookie."""
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
    _set_session_cookies(response, pair.refresh_token)

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

    return AccessTokenResponse(
        access_token=pair.access_token,
        expires_in=pair.expires_in,
    )


@router.post(
    "/login",
    response_model=AccessTokenResponse,
    summary="Login with email and password",
    description=(
        "Authenticate and receive an access token. The refresh token is set as "
        "an httpOnly cookie (Path=/api/auth). Login attempts are rate-limited per IP."
    ),
    responses={
        200: {"description": "Login successful — access token returned, refresh cookie set"},
        401: {"description": "Invalid email or password"},
        403: {"description": "Account is disabled or must use SSO"},
        429: {"description": "Too many login attempts"},
    },
)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    service: RefreshTokenService = Depends(get_refresh_service),
) -> AccessTokenResponse:
    """Login with email and password, return access token + set refresh-token cookie."""
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
    _set_session_cookies(response, pair.refresh_token)

    return AccessTokenResponse(
        access_token=pair.access_token,
        expires_in=pair.expires_in,
    )


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Rotate a refresh token",
    description=(
        "Exchange the refresh-token cookie for a new access token. "
        "The old refresh token is revoked (rotation). Reuse of a revoked token "
        "kills the entire token family and returns 401. "
        "Both session cookies are refreshed on success and expired on failure."
    ),
    responses={
        200: {"description": "New access token issued, cookies rotated"},
        401: {"description": "Missing, invalid, expired, revoked, or reused refresh token"},
    },
)
async def refresh(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    service: RefreshTokenService = Depends(get_refresh_service),
    _rl: None = Depends(refresh_rate_limit),
) -> AccessTokenResponse | JSONResponse:
    """Rotate the refresh-token cookie — returns a new access token."""
    if not refresh_token:
        json_resp = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing refresh token", "error_code": "missing_refresh_token"},
        )
        _clear_session_cookies(json_resp)
        return json_resp

    try:
        pair = await service.rotate(refresh_token, _extract_device_info(request))
    except AuthError as exc:
        # Clear cookies on any auth failure — prevents stale cookie loops
        return _auth_error_response(exc, clear_cookies=True)

    _set_session_cookies(response, pair.refresh_token)
    return AccessTokenResponse(access_token=pair.access_token, expires_in=pair.expires_in)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout (single device)",
    description=(
        "Revoke the refresh-token cookie. Idempotent — no error if the token "
        "is already revoked, the cookie is absent, or the access token is expired. "
        "Both session cookies are cleared. Does NOT require a valid access token."
    ),
    responses={
        204: {"description": "Logged out — refresh token revoked, cookies cleared"},
    },
)
async def logout(
    refresh_token: str | None = Cookie(default=None),
    service: RefreshTokenService = Depends(get_refresh_service),
    db: AsyncSession = Depends(get_db),
    audit: "AuditService" = Depends(get_audit_service),
) -> Response:
    """Relaxed logout — never fails, even with expired or missing access token.

    Strategy:
      1. Decode the refresh cookie (verify_exp=False) to extract user_id for audit.
      2. Call service.revoke() which handles DB mark + Redis denylist (idempotent).
      3. Always clear both session cookies.
      4. Emit auth.logout audit if user_id could be extracted.

    NOTE: we construct the Response directly here — FastAPI does NOT merge
    Set-Cookie headers when the route returns a Response subclass directly.
    """
    from app.rbac.audit import AuditService  # noqa: F401

    user_id: uuid.UUID | None = None

    if refresh_token:
        # Decode with verify_exp=False — accept expired refresh tokens for logout
        try:
            payload = jose_jwt.decode(
                refresh_token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
                options={"verify_exp": False},
            )
            if payload.get("sub"):
                user_id = uuid.UUID(payload["sub"])
        except (JWTError, Exception):
            logger.info("logout: unparseable refresh token, idempotent success")

        # Revoke in DB + add to Redis denylist (handles expired tokens gracefully)
        try:
            await service.revoke(refresh_token)
        except Exception as exc:
            logger.warning("logout: service.revoke failed (idempotent): %s", exc)

    resp = Response(status_code=status.HTTP_204_NO_CONTENT)
    _clear_session_cookies(resp)

    if user_id is not None:
        try:
            await audit.log_action(
                user_id=user_id,
                action="auth.logout",
                resource_type="user",
                resource_id=str(user_id),
            )
            await db.commit()
        except Exception:
            logger.warning("audit.log_action failed for auth.logout user=%s", user_id)

    return resp


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
    response: Response,
    service: RefreshTokenService = Depends(get_refresh_service),
    current_user: User = Depends(get_current_user),
) -> LogoutAllResponse:
    """Revoke all refresh tokens for the current user (all-device logout)."""
    count = await service.revoke_all(current_user.id)
    # Also clear the current device's session cookies
    _clear_session_cookies(response)
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
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
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
    description="Returns the authenticated user's profile data including plan entitlements.",
)
async def get_current_profile(
    current_user: User = Depends(get_current_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> dict:
    """Return the current user's profile.

    The `entitlements` array is computed server-side per request using
    EntitlementService, honouring BETA_MODE. Frontend should treat this as
    the authoritative feature-gate source — do not duplicate logic client-side.
    """
    from app.config import settings
    from app.services.entitlement_service import EntitlementService

    entitlements = EntitlementService.list_user_features(
        plan_id=current_user.plan,
        beta_mode=settings.beta_mode,
    )
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "avatar_url": current_user.avatar_url,
        "plan": current_user.plan,
        "entitlements": entitlements,
        "is_admin": current_user.is_admin,
        "onboarding_completed": current_user.onboarding_completed,
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
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
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
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> dict:
    """Update the current user's profile fields."""
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.default_org_id is not None:
        current_user.default_org_id = body.default_org_id
    await db.flush()
    return {"status": "updated"}


@router.post(
    "/me/onboarding",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark onboarding as completed",
    description=(
        "Idempotent — sets onboarding_completed=True for the current user. "
        "Returns 204 whether the flag was already set or just flipped. "
        "Emits an audit log entry on first call only."
    ),
    responses={
        204: {"description": "Onboarding marked complete"},
        401: {"description": "Access token missing or invalid"},
    },
)
async def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    audit: "AuditService" = Depends(get_audit_service),
) -> Response:
    """Flip onboarding_completed to True. Idempotent — skips update and audit if already done."""
    from app.rbac.audit import AuditService  # noqa: F401 — used for type hint only

    if not current_user.onboarding_completed:
        current_user.onboarding_completed = True
        await db.commit()
        try:
            await audit.log_action(
                user_id=current_user.id,
                action="auth.onboarding_completed",
                resource_type="user",
                resource_id=str(current_user.id),
            )
            await db.commit()
        except Exception:
            # Audit is non-blocking observability — do not fail the request.
            logger.warning(
                "audit.log_action failed for auth.onboarding_completed user=%s",
                current_user.id,
            )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
