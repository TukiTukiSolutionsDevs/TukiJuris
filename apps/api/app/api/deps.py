"""Shared FastAPI dependencies — auth, database, rate limiting, org context."""

import hashlib
import time
import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.api_key import APIKey
from app.models.organization import OrgMembership, Organization
from app.models.user import User

security = HTTPBearer(auto_error=False)

# Role hierarchy: higher index = more permissions
_ROLE_RANK: dict[str, int] = {
    "member": 0,
    "admin": 1,
    "owner": 2,
}

# Anti-abuse rate limit — flat cap regardless of plan.
# BYOK: TukiJuris does not tier features by plan (users bring their own keys).
# This is an infrastructure protection cap, not a feature gate.
_ANTI_ABUSE_LIMIT_AUTHENTICATED = 60   # 60 req/min for any authenticated user
_ANTI_ABUSE_LIMIT_ANONYMOUS = 10       # 10 req/min for anonymous requests

# Keep the dict for backward compatibility with any code that imports _PLAN_LIMITS
_PLAN_LIMITS: dict[str, int] = {
    "free": _ANTI_ABUSE_LIMIT_AUTHENTICATED,
    "base": _ANTI_ABUSE_LIMIT_AUTHENTICATED,
    "enterprise": _ANTI_ABUSE_LIMIT_AUTHENTICATED,
}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido",
        )

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )

    # Type enforcement: only accept tokens explicitly typed as access tokens
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido (tipo incorrecto — usar access token)",
        )

    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o desactivado",
        )

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Same as get_current_user but returns None instead of 401."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# TODO: Remove or integrate — get_current_user_with_org is currently unused
# (no route imports it). Keep for now as it may be useful for future org-scoped endpoints.
async def get_current_user_with_org(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> tuple[User, Organization | None]:
    """Resolve the current user AND their default organisation (if any).

    Returns a (user, org) tuple. `org` is None when the user has no
    default_org_id set or the referenced organisation no longer exists.
    """
    user = await get_current_user(credentials, db)
    org: Organization | None = None

    if user.default_org_id is not None:
        result = await db.execute(
            select(Organization).where(Organization.id == user.default_org_id)
        )
        org = result.scalar_one_or_none()

    return user, org


async def require_org_role(
    user: User,
    org_id: uuid.UUID,
    role: str,
    db: AsyncSession,
) -> OrgMembership:
    """Verify the user holds at least `role` in the given organisation.

    Role hierarchy (ascending): member < admin < owner.

    Raises:
        HTTPException 403 — user is not a member or has insufficient role.
    """
    result = await db.execute(
        select(OrgMembership).where(
            OrgMembership.user_id == user.id,
            OrgMembership.organization_id == org_id,
            OrgMembership.is_active.is_(True),
        )
    )
    membership = result.scalar_one_or_none()

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No eres miembro de esta organización",
        )

    required_rank = _ROLE_RANK.get(role, 0)
    actual_rank = _ROLE_RANK.get(membership.role, 0)

    if actual_rank < required_rank:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Se requiere rol '{role}' o superior",
        )

    return membership


async def check_rate_limit(
    request: Request,
    user: User | None = Depends(get_optional_user),
) -> dict:
    """FastAPI dependency that enforces anti-abuse rate limiting.

    BYOK: Rate limits are flat infrastructure protection caps — NOT plan-based.
    TukiJuris does not restrict features or query volume by plan.
    Authenticated users get 60 req/min regardless of their plan tier.
    Anonymous requests are capped at 10 req/min.

    Adds X-RateLimit-* headers to the response on success.
    Raises HTTP 429 when the limit is exceeded.
    """
    from app.core.rate_limiter import rate_limiter

    if user is not None:
        key = f"user:{user.id}"
        max_requests = _ANTI_ABUSE_LIMIT_AUTHENTICATED
    else:
        client_ip = request.client.host if request.client else "unknown"
        key = f"ip:{client_ip}"
        max_requests = _ANTI_ABUSE_LIMIT_ANONYMOUS

    result = await rate_limiter.check_rate_limit(key, max_requests, 60)

    if not result["allowed"]:
        retry_after = max(1, result["reset_at"] - int(time.time()))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry in {retry_after}s.",
            headers={
                "X-RateLimit-Limit": str(result["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(result["reset_at"]),
                "Retry-After": str(retry_after),
            },
        )

    return result


async def get_api_key_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Authenticate via API key.

    Accepts the key from:
      - X-API-Key header  (preferred)
      - Authorization: Bearer ak_...  (alternative — for clients that only do Bearer)

    Returns the owner User if the key is valid, active, and not expired.
    Returns None (no exception) when no API key header is present so callers
    can chain with JWT auth.
    """
    from datetime import UTC, datetime

    api_key = request.headers.get("X-API-Key", "").strip()
    if not api_key:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer ak_"):
            api_key = auth_header[len("Bearer "):]

    if not api_key or not api_key.startswith("ak_"):
        return None

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    result = await db.execute(
        select(APIKey).where(APIKey.key_hash == key_hash)
    )
    api_key_obj = result.scalar_one_or_none()

    if not api_key_obj:
        return None

    if not api_key_obj.is_active:
        return None

    if api_key_obj.expires_at is not None and api_key_obj.expires_at < datetime.now(UTC):
        return None

    # Non-blocking best-effort update of last_used_at
    api_key_obj.last_used_at = datetime.now(UTC)

    # Load and return the owner
    user_result = await db.execute(
        select(User).where(User.id == api_key_obj.user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user or not user.is_active:
        return None

    return user


async def get_refresh_service(
    db: AsyncSession = Depends(get_db),
) -> "RefreshTokenService":
    """Create a RefreshTokenService — override via app.dependency_overrides in tests.

    Uses the shared Redis URL from settings. Fail-open: if Redis is unavailable,
    the denylist raises and the service handles it.
    """
    from redis import asyncio as aioredis

    from app.config import settings
    from app.core.token_denylist import TokenDenylist
    from app.repositories.refresh_token_repo import RefreshTokenRepo
    from app.services.refresh_token_service import RefreshTokenService

    redis = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=False)
    denylist = TokenDenylist(redis)
    repo = RefreshTokenRepo(db)
    return RefreshTokenService(db, repo, denylist)


async def get_authenticated_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dual-auth dependency — accepts JWT or API key.

    Tries JWT first (when the Bearer token does NOT start with 'ak_').
    Falls back to API key authentication otherwise.
    Raises HTTP 401 if neither method succeeds.
    """
    # JWT path
    if (
        credentials is not None
        and credentials.credentials
        and not credentials.credentials.startswith("ak_")
    ):
        return await get_current_user(credentials, db)

    # API key path
    user = await get_api_key_user(request, db)
    if user is not None:
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required (JWT or API key)",
    )
