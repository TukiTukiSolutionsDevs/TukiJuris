"""Redis-based caching layer for expensive operations."""

import hashlib
import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis caching service with graceful degradation.

    All methods fail silently — if Redis is down or unavailable,
    the application continues to work, just without cache benefits.
    """

    def __init__(self):
        self._redis: redis.Redis | None = None

    async def _get_redis(self) -> redis.Redis:
        """Lazy-init Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    def _make_key(self, prefix: str, *args) -> str:
        """Generate a deterministic cache key from prefix + args.

        The key is hashed to avoid exceeding Redis key length limits and
        to normalise whitespace / special characters in query strings.
        """
        raw = f"{prefix}:" + ":".join(str(a) for a in args)
        return f"cache:{hashlib.md5(raw.encode()).hexdigest()[:16]}"

    async def get(self, key: str) -> Any | None:
        """Return cached value, or None on miss or Redis error."""
        if not settings.cache_enabled:
            return None
        try:
            r = await self._get_redis()
            val = await r.get(key)
            return json.loads(val) if val else None
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Store value in cache with TTL. Fails silently on error."""
        if not settings.cache_enabled:
            return
        try:
            r = await self._get_redis()
            await r.setex(key, ttl_seconds, json.dumps(value, default=str))
        except Exception:
            pass  # Cache failures are non-critical

    async def delete(self, key: str):
        """Remove a single key from cache."""
        try:
            r = await self._get_redis()
            await r.delete(key)
        except Exception:
            pass

    async def invalidate_prefix(self, prefix: str):
        """Delete all cache keys matching a prefix pattern (scan-based)."""
        try:
            r = await self._get_redis()
            keys = []
            async for key in r.scan_iter(f"cache:{prefix}*"):
                keys.append(key)
            if keys:
                await r.delete(*keys)
        except Exception:
            pass


# Module-level singleton — import this throughout the app
cache = CacheService()
