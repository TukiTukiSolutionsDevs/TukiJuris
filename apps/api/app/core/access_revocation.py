"""User-level access-token revocation.

Access tokens are short-lived JWTs (15 min) carried as Bearer headers.
They have no `jti` claim — revoking individual tokens would require either
adding `jti` to every access token (changing the JWT shape and breaking
existing clients mid-deploy) or scanning all refresh-token records.

The pragmatic primitive used instead is **user-level revoke-after**:

  - When the user logs out everywhere or changes their password, we write
    ``tukijuris:access_revoke:user:<uid>`` in Redis with value = unix time
    of the revocation and a TTL ≥ ACCESS_TOKEN_EXPIRE_MINUTES * 60.
  - On every authenticated request, ``get_current_user`` reads the marker.
    If it exists and the access token's ``iat`` is ≤ the marker, the token
    is rejected as ``revoked_session``.

Effect: every access token issued **before** the revoke is killed within
the natural TTL window. New access tokens issued after the revoke survive
because their ``iat`` is newer.

Fail-open: Redis errors are logged but never block the request — an infra
outage must not lock everyone out.
"""

from __future__ import annotations

import logging
import time
import uuid

from redis import asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_KEY_PREFIX = f"{settings.redis_key_prefix}access_revoke:user:"
_redis_client: "aioredis.Redis | None" = None


def _redis() -> aioredis.Redis:
    """Lazy singleton — created on first use, reused for process lifetime."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def mark_user_revoked(user_id: uuid.UUID, *, ttl_seconds: int) -> None:
    """Mark all access tokens issued before now as revoked for this user.

    The TTL should be ≥ the access token lifetime so the marker outlives
    every token it intends to invalidate.
    """
    try:
        now = int(time.time())
        await _redis().set(f"{_KEY_PREFIX}{user_id}", str(now), ex=max(60, ttl_seconds))
    except Exception as exc:
        logger.warning("mark_user_revoked failed (fail-open) for user=%s: %s", user_id, exc)


async def user_revoked_after(user_id: uuid.UUID) -> int | None:
    """Return the unix-timestamp of the most recent revocation, or None."""
    try:
        raw = await _redis().get(f"{_KEY_PREFIX}{user_id}")
        if raw is None:
            return None
        return int(raw)
    except Exception as exc:
        logger.warning("user_revoked_after failed (fail-open) for user=%s: %s", user_id, exc)
        return None
