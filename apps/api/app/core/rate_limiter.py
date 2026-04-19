"""Rate limiting using Redis sliding window (sorted sets)."""

import logging
import time
from enum import Enum

import redis.asyncio as redis
from fastapi import HTTPException, Request

from app.config import settings

logger = logging.getLogger(__name__)

# Rate limit tiers: (requests_per_minute, requests_per_day | None)
# Keys are the FINAL canonical plan IDs: free | pro | studio
# Established by plan-model-refactor (Sprint 2) — do NOT rename these keys.
RATE_LIMIT_TIERS: dict[str, tuple[int, int | None]] = {
    "anonymous": (10, None),
    "free": (30, 100),
    "pro": (120, 2000),
    "studio": (600, None),
}


class RateLimiter:
    """Singleton Redis-backed sliding window rate limiter.

    Uses sorted sets where the score is the Unix timestamp.
    Old entries outside the window are pruned on every check.
    If Redis is unavailable, requests are allowed through (fail-open).
    """

    def __init__(self) -> None:
        self._redis: redis.Redis | None = None

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> dict:
        """Check and record a request against the sliding window.

        Args:
            key: Unique identifier for the rate limit bucket (e.g. "user:uuid").
            max_requests: Maximum requests allowed in the window.
            window_seconds: Length of the sliding window in seconds.

        Returns:
            dict with keys: allowed, remaining, limit, reset_at.
        """
        r = await self._get_redis()
        now = int(time.time())
        window_start = now - window_seconds
        redis_key = f"ratelimit:{key}"

        async with r.pipeline(transaction=True) as pipe:
            # Drop entries older than the current window
            pipe.zremrangebyscore(redis_key, 0, window_start)
            # Count entries still within the window (before adding current)
            pipe.zcard(redis_key)
            # Record this request with a unique member to avoid collisions
            member = f"{now}:{id(pipe)}"
            pipe.zadd(redis_key, {member: now})
            # TTL slightly longer than the window so Redis can GC the key
            pipe.expire(redis_key, window_seconds + 1)
            results = await pipe.execute()

        current_count: int = results[1]  # zcard result (before this request)
        allowed = current_count < max_requests
        remaining = max(0, max_requests - current_count - 1) if allowed else 0

        if not allowed:
            # Remove the entry we just added — denied requests don't consume quota
            await r.zrem(redis_key, member)

        return {
            "allowed": allowed,
            "remaining": remaining,
            "limit": max_requests,
            "reset_at": now + window_seconds,
        }

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None


# Module-level singleton — one connection pool for the process lifetime
rate_limiter = RateLimiter()


# ---------------------------------------------------------------------------
# Rate-limit buckets — READ vs WRITE
# ---------------------------------------------------------------------------


class RateLimitBucket(str, Enum):
    """Identifies which rate-limit bucket a route belongs to.

    READ  — flat cap, same for all plans (search, list, get operations).
    WRITE — plan-based cap (chat, stream, mutations that consume quota).
    """

    READ = "read"
    WRITE = "write"


# Flat ceiling for READ routes — all plans get the same cap.
# High enough not to throttle normal API consumers but blocks runaway scrapers.
READ_LIMIT_PER_MIN: int = 600


def get_write_limit_for_plan(plan: str) -> int:
    """Return the WRITE requests-per-minute limit for the given plan.

    Looks up the first element (rpm) of ``RATE_LIMIT_TIERS[plan]``.
    Falls back to the "free" tier for unknown / None plan strings so the
    guard is always well-defined even if user.plan is stale or missing.
    """
    tier = RATE_LIMIT_TIERS.get(plan) or RATE_LIMIT_TIERS["free"]
    return tier[0]  # (requests_per_minute, requests_per_day | None)


# ---------------------------------------------------------------------------
# Route-level dependency: /auth/refresh specific bucket
# ---------------------------------------------------------------------------

_REFRESH_REQUESTS_PER_MINUTE = 10
_REFRESH_WINDOW_SECONDS = 60


async def refresh_rate_limit(request: Request) -> None:
    """Route-level rate limiter for /auth/refresh — 10 req/min per IP.

    Uses a dedicated bucket key ``refresh:ip:{ip}`` that is completely
    separate from the global anonymous middleware bucket (``ip:{ip}``) and
    the login attempt bucket (``login:ip:{ip}``).

    Fail-open: if Redis is unavailable the request is allowed through so
    that an infrastructure outage does not lock users out of token refresh.
    """
    client_ip = request.client.host if request.client else "unknown"
    key = f"refresh:ip:{client_ip}"
    try:
        result = await rate_limiter.check_rate_limit(
            key, _REFRESH_REQUESTS_PER_MINUTE, _REFRESH_WINDOW_SECONDS
        )
        if not result["allowed"]:
            raise HTTPException(
                status_code=429,
                detail="Too many refresh requests. Try again later.",
                headers={"Retry-After": str(_REFRESH_WINDOW_SECONDS)},
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Refresh rate limiter error (fail-open): %s", exc)
