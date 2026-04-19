"""Redis-backed denylist for revoked refresh tokens (jti-indexed).

Keys live under ``{prefix}{jti}`` so they are isolated from other Redis data.
The default prefix is ``{settings.redis_key_prefix}denylist:`` (e.g. ``tukijuris:denylist:<jti>``).

Fail-open contract
------------------
Callers (service layer) MUST catch exceptions from add/contains and treat any
Redis error as "not denied" so that a Redis outage does not lock out users.
This wrapper intentionally does NOT swallow exceptions — the service layer
decides the recovery strategy.
"""

from __future__ import annotations

from app.config import settings


class TokenDenylist:
    """Thin async wrapper over a redis.asyncio client for jti revocation.

    Args:
        redis:  An async Redis client (redis.asyncio.Redis or compatible mock).
        prefix: Key namespace. Defaults to ``{settings.redis_key_prefix}denylist:``.
    """

    def __init__(self, redis, prefix: str | None = None) -> None:
        self._redis = redis
        self._prefix: str = (
            prefix if prefix is not None
            else f"{settings.redis_key_prefix}denylist:"
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _key(self, jti: str) -> str:
        """Build the full Redis key for a given jti."""
        return f"{self._prefix}{jti}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def add(self, jti: str, ttl_seconds: int) -> None:
        """Mark a jti as revoked with the given TTL.

        The key expires automatically when the underlying token's natural
        expiry is reached — no background cleanup needed.
        """
        await self._redis.set(self._key(jti), 1, ex=ttl_seconds)

    async def contains(self, jti: str) -> bool:
        """Return True if the jti is in the denylist (token is revoked)."""
        count = await self._redis.exists(self._key(jti))
        return bool(count)
