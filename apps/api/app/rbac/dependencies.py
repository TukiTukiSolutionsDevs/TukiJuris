"""RBAC FastAPI dependency factories.

Provides:
  - require_permission(*permissions) → Depends factory
  - get_user_permissions_dep        → returns current user's set[str]
"""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.rbac.cache import PermissionCache
from app.rbac.service import RBACService


async def get_redis():
    """FastAPI dependency that yields a Redis client for RBAC operations.

    Creates a per-request connection. Uses decode_responses=True so
    PermissionCache can work with plain str values from Redis.
    """
    from redis import asyncio as aioredis

    from app.config import settings

    redis = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    try:
        yield redis
    finally:
        await redis.aclose()


def require_permission(*permissions: str) -> Callable:
    """Factory that returns a FastAPI dependency enforcing all given permissions.

    Usage::

        @router.get("/admin/users")
        async def list_users(
            _: User = Depends(require_permission("users:read")),
        ): ...

    Logic:
      1. Resolve current user (JWT via get_current_user).
      2. Build RBACService with Redis-backed PermissionCache.
      3. Call check_permission(user_id, *permissions) — AND semantics.
      4. 403 on failure, returns user on success.

    No permissions → always allowed (check_permission short-circuits to True).
    """

    async def dependency(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
        redis=Depends(get_redis),
    ) -> User:
        cache = PermissionCache(redis)
        service = RBACService(db, cache)
        allowed = await service.check_permission(current_user.id, *permissions)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return dependency


async def get_user_permissions_dep(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> set[str]:
    """Dependency that returns the current user's full set of permission strings.

    Cache-first: reads from Redis if warm, falls back to DB query on miss.
    Returns an empty set for users with no assigned roles.
    """
    cache = PermissionCache(redis)
    service = RBACService(db, cache)
    return await service.get_user_permissions(current_user.id)
