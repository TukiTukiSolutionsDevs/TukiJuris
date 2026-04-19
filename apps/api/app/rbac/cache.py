"""RBAC Permission Cache — Redis-backed, fail-open.

Key format : tukijuris:rbac:perms:{user_id}
TTL        : 3600 seconds
Fail-open  : any Redis error returns None / is silently swallowed.
"""

import json
import logging
import uuid

logger = logging.getLogger(__name__)

_REDIS_PREFIX = "tukijuris:rbac:perms:"
_TTL = 3600  # seconds


class PermissionCache:
    """Cache layer for user permission sets backed by Redis.

    All public methods are fail-open: a Redis outage degrades to a cache miss,
    never to an application error.
    """

    def __init__(self, redis) -> None:  # redis: redis.asyncio.Redis
        self._redis = redis

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _key(self, user_id: uuid.UUID) -> str:
        return f"{_REDIS_PREFIX}{user_id}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_permissions(self, user_id: uuid.UUID) -> set[str] | None:
        """Return cached permission set or None on miss / error."""
        try:
            raw = await self._redis.get(self._key(user_id))
            if raw is None:
                return None
            # raw may be bytes or str depending on decode_responses setting
            data = raw if isinstance(raw, str) else raw.decode()
            return set(json.loads(data))
        except Exception:
            logger.warning("rbac cache get failed for user %s — fail-open", user_id)
            return None

    async def set_permissions(self, user_id: uuid.UUID, permissions: set[str]) -> None:
        """Store permission set with TTL. Silently swallows Redis errors."""
        try:
            payload = json.dumps(sorted(permissions))
            await self._redis.set(self._key(user_id), payload, ex=_TTL)
        except Exception:
            logger.warning("rbac cache set failed for user %s — fail-open", user_id)

    async def invalidate(self, user_id: uuid.UUID) -> None:
        """Delete cached permissions for one user. Silently swallows errors."""
        try:
            await self._redis.delete(self._key(user_id))
        except Exception:
            logger.warning("rbac cache invalidate failed for user %s — fail-open", user_id)

    async def invalidate_all(self) -> None:
        """Scan and delete all rbac permission keys. Silently swallows errors."""
        try:
            cursor, keys = await self._redis.scan(match=f"{_REDIS_PREFIX}*", count=100)
            if keys:
                await self._redis.delete(*keys)
        except Exception:
            logger.warning("rbac cache invalidate_all failed — fail-open")
