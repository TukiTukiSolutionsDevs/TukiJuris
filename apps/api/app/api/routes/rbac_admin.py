"""RBAC Admin API routes — role listing and user-role assignment."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RateLimitBucket, RateLimitGuard, get_db, get_refresh_service
from app.models.user import User
from app.rbac.audit import AuditService
from app.rbac.cache import PermissionCache
from app.rbac.dependencies import get_redis, require_permission
from app.rbac.schemas import PermissionResponse, RoleResponse, UserRoleAssign, UserRoleResponse
from app.rbac.service import RBACService
from app.services.refresh_token_service import RefreshTokenService

router = APIRouter(prefix="/admin", tags=["admin-rbac"])


def _make_service(
    db: AsyncSession,
    redis,
    refresh_tokens: RefreshTokenService | None = None,
    audit: AuditService | None = None,
) -> RBACService:
    """Construct an RBACService with a Redis-backed PermissionCache."""
    return RBACService(db, PermissionCache(redis), refresh_tokens=refresh_tokens, audit=audit)


@router.get(
    "/roles",
    response_model=list[RoleResponse],
    summary="List all roles",
    description="Return all system roles. Requires roles:read permission.",
)
async def list_roles(
    current_user: User = Depends(require_permission("roles:read")),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> list[RoleResponse]:
    """List all system roles."""
    service = _make_service(db, redis)
    return await service.get_all_roles()


@router.get(
    "/roles/{role_id}/permissions",
    response_model=list[PermissionResponse],
    summary="Get role permissions",
    description="Return all permissions assigned to a role. Requires roles:read permission.",
)
async def get_role_permissions(
    role_id: uuid.UUID,
    current_user: User = Depends(require_permission("roles:read")),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> list[PermissionResponse]:
    """Return all permissions for the given role."""
    service = _make_service(db, redis)
    return await service.get_role_permissions(role_id)


@router.post(
    "/users/{user_id}/roles",
    response_model=UserRoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign role to user",
    description="Assign a role to a user. Requires roles:write permission. Logs an audit entry.",
    responses={
        201: {"description": "Role assigned"},
        403: {"description": "Insufficient permissions"},
    },
)
async def assign_user_role(
    user_id: uuid.UUID,
    body: UserRoleAssign,
    current_user: User = Depends(require_permission("roles:write")),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    refresh_tokens: RefreshTokenService = Depends(get_refresh_service),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> UserRoleResponse:
    """Assign a role to a user, invalidate cache, and emit an audit entry."""
    service = _make_service(db, redis, refresh_tokens=refresh_tokens, audit=AuditService(db=db))
    user_role = await service.assign_role(user_id, body.role_id, current_user.id)
    role = await service.get_role_by_id(body.role_id)
    return UserRoleResponse(
        role_id=user_role.role_id,
        role_name=role.name if role else str(body.role_id),
        assigned_at=user_role.assigned_at or datetime.now(UTC),
        assigned_by=user_role.assigned_by,
        expires_at=user_role.expires_at,
    )


@router.delete(
    "/users/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke role from user",
    description="Revoke a role from a user. Requires roles:write permission. Logs an audit entry.",
    responses={
        204: {"description": "Role revoked"},
        403: {"description": "Insufficient permissions"},
    },
)
async def revoke_user_role(
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    current_user: User = Depends(require_permission("roles:write")),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    refresh_tokens: RefreshTokenService = Depends(get_refresh_service),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> None:
    """Revoke a role from a user, invalidate cache, and emit an audit entry.

    Returns 409 CANNOT_REVOKE_OWN_ADMIN if the caller attempts to revoke their
    own last admin role. Ask another admin to perform this operation.
    """
    service = _make_service(db, redis, refresh_tokens=refresh_tokens, audit=AuditService(db=db))
    await service.revoke_role(user_id, role_id, revoked_by=current_user.id)
