"""Shared FastAPI dependencies — auth, database, rate limiting, org context."""

import hashlib
import logging
import time
import uuid

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limiter import READ_LIMIT_PER_MIN, RateLimitBucket, get_write_limit_for_plan
from app.core.security import decode_access_token
from app.models.api_key import APIKey
from app.models.organization import OrgMembership, Organization
from app.models.user import User

logger = logging.getLogger(__name__)

# Re-export so route files only need to import from app.api.deps
__all__ = [
    "RateLimitBucket",
    "RateLimitGuard",
    "get_current_user",
    "get_optional_user",
    "get_authenticated_user",
    "get_api_key_user",
    "get_db",
    "require_admin",
    "require_org_role",
]

security = HTTPBearer(auto_error=False)

# Role hierarchy: higher index = more permissions
_ROLE_RANK: dict[str, int] = {
    "member": 0,
    "admin": 1,
    "owner": 2,
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


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Defense-in-depth: enforce is_admin=True above RBAC permissions.

    Raises HTTPException(403) if the authenticated user does not have
    is_admin=True. Use as a FastAPI dependency on any admin-only route::

        user: User = Depends(require_admin)

    FIX-02: consolidated from duplicated helpers in admin_saas.py,
    admin_invoices.py, admin_trials.py (admin-rbac.unit.001).
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin_required",
        )
    return current_user


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


async def get_denylist() -> "TokenDenylist":
    """Create a TokenDenylist backed by the app's Redis connection.

    Used by routes that need to populate the denylist directly (e.g. logout-all).
    Fail-open: callers must catch exceptions from denylist.add().
    """
    from redis import asyncio as aioredis

    from app.config import settings
    from app.core.token_denylist import TokenDenylist

    redis = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=False)
    return TokenDenylist(redis)


async def get_audit_service(
    db: AsyncSession = Depends(get_db),
) -> "AuditService":
    """Create an AuditService bound to the current DB session.

    Follows Sprint 2 injection pattern — never use AuditService as a global/singleton.
    """
    from app.rbac.audit import AuditService

    return AuditService(db)


async def get_invoice_service(
    db: AsyncSession = Depends(get_db),
    audit: "AuditService" = Depends(get_audit_service),
) -> "InvoiceService":
    """Create an InvoiceService bound to the current DB session.

    Follows Sprint 2/3 injection pattern — same session as route handler
    so invoice INSERT and other business logic share one transaction.
    Override via app.dependency_overrides[get_invoice_service] in tests.
    """
    from app.services.invoice_service import InvoiceService

    return InvoiceService(db=db, audit=audit)


async def get_idempotency_service(
    db: AsyncSession = Depends(get_db),
) -> "WebhookIdempotencyService":
    """Create a WebhookIdempotencyService bound to the current DB session.

    Follows Sprint 2 injection pattern — same session as the route handler
    so the idempotency INSERT and the business logic share one transaction.
    """
    from app.services.webhook_idempotency_service import WebhookIdempotencyService

    return WebhookIdempotencyService(db)


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


# ---------------------------------------------------------------------------
# RateLimitGuard — plan-aware per-route dependency factory
# ---------------------------------------------------------------------------


def RateLimitGuard(bucket: RateLimitBucket):
    """Return a FastAPI dependency that enforces per-bucket rate limits.

    READ  bucket: flat 600 req/min — identical for all plans.
    WRITE bucket: plan-based (free=30, pro=120, studio=600 req/min).

    Behaviour:
    - Admin users (is_admin=True) bypass all limits unconditionally.
    - Anonymous users are keyed by client IP.
    - Authenticated users are keyed by user.id — plan is read from user.plan.
    - Fail-open: Redis errors are logged as WARNING but never block the request.
    - On 429, raises HTTPException with a structured detail dict and standard
      X-RateLimit-* / Retry-After headers.

    Usage::

        @router.get("/something")
        async def handler(
            _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
            user: User = Depends(get_current_user),
        ):
            ...
    """

    async def _guard(
        request: Request,
        response: Response,
        user: User | None = Depends(get_optional_user),
    ) -> None:
        from app.core.rate_limiter import rate_limiter

        # Admin bypass — admins are never throttled
        if user is not None and getattr(user, "is_admin", False):
            return

        # Resolve limit
        if bucket == RateLimitBucket.READ:
            max_requests = READ_LIMIT_PER_MIN
        else:  # WRITE
            plan = getattr(user, "plan", "free") if user else "free"
            max_requests = get_write_limit_for_plan(plan)

        # Resolve bucket key
        if user is not None:
            key = f"rl:{bucket.value}:user:{user.id}"
        else:
            client_ip = request.client.host if request.client else "unknown"
            key = f"rl:{bucket.value}:ip:{client_ip}"

        try:
            result = await rate_limiter.check_rate_limit(key, max_requests, 60)
            if not result["allowed"]:
                retry_after = max(1, result["reset_at"] - int(time.time()))
                used = result["limit"] - result.get("remaining", 0)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error_code": "rate_limit_exceeded",
                        "bucket": bucket.value,
                        "retry_after_seconds": retry_after,
                        "limit": result["limit"],
                        "used": used,
                    },
                    headers={
                        "X-RateLimit-Limit": str(result["limit"]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(result["reset_at"]),
                        "Retry-After": str(retry_after),
                    },
                )
            # FIX-06: inject rate-limit headers on successful (allowed) responses
            # so API consumers can track their quota without waiting for a 429.
            response.headers["X-RateLimit-Limit"] = str(result["limit"])
            response.headers["X-RateLimit-Remaining"] = str(result["remaining"])
            response.headers["X-RateLimit-Reset"] = str(result["reset_at"])
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning(
                "RateLimitGuard fail-open (bucket=%s key=%s): %s",
                bucket.value,
                key,
                exc,
            )

    return _guard


# ---------------------------------------------------------------------------
# Payment provider adapters & trial service (Sprint 3 — item 4c)
# ---------------------------------------------------------------------------

_shared_http_client: "httpx.AsyncClient | None" = None


def _get_http_client() -> "httpx.AsyncClient":
    """Shared httpx client — created once, reused across requests."""
    import httpx

    global _shared_http_client
    if _shared_http_client is None:
        _shared_http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=10),
        )
    return _shared_http_client


def get_culqi_adapter() -> "CulqiAdapter":
    """Return a CulqiAdapter using settings credentials and the shared HTTP client."""
    from app.config import settings
    from app.services.payment_providers.culqi_adapter import CulqiAdapter

    return CulqiAdapter(
        secret_key=settings.culqi_secret_key,
        client=_get_http_client(),
    )


def get_mp_adapter() -> "MPAdapter":
    """Return an MPAdapter using settings credentials and the shared HTTP client."""
    from app.config import settings
    from app.services.payment_providers.mp_adapter import MPAdapter

    return MPAdapter(
        access_token=settings.mp_access_token,
        client=_get_http_client(),
    )


def get_email_service() -> "EmailService":
    """Return the singleton EmailService instance."""
    from app.services.email_service import email_service

    return email_service


async def get_trial_service(
    db: AsyncSession = Depends(get_db),
    audit: "AuditService" = Depends(get_audit_service),
) -> "TrialService":
    """Create a TrialService bound to the current DB session.

    Override via app.dependency_overrides[get_trial_service] in tests.
    """
    from app.services.trial_service import TrialService

    return TrialService(
        db=db,
        audit=audit,
        culqi=get_culqi_adapter(),
        mp=get_mp_adapter(),
        email=get_email_service(),
        settings=__import__("app.config", fromlist=["settings"]).settings,
    )
