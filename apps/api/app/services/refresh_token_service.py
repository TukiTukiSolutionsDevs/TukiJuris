"""Refresh token lifecycle service: issue, rotate, revoke, list sessions."""

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    ExpiredRefreshToken,
    InvalidRefreshToken,
    ReuseDetected,
    RevokedRefreshToken,
)
from app.core.monitoring import refresh_metrics
from app.core.security import (
    CLOCK_SKEW_SECONDS,
    build_refresh_claims,
    compute_refresh_expires_at,
    create_access_token,
    hash_token,
)
from app.core.token_denylist import TokenDenylist
from app.models.refresh_token import RefreshToken
from app.repositories.refresh_token_repo import RefreshTokenRepo

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DTOs — no ORM leakage past the service boundary
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TokenPair:
    """Access + refresh token pair returned to callers."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # access token TTL in seconds


@dataclass(frozen=True)
class SessionDTO:
    """A single active refresh-token session (safe to serialize)."""

    jti: str
    family_id: str
    created_at: datetime
    expires_at: datetime


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class RefreshTokenService:
    """Orchestrates the refresh token lifecycle.

    Depends on:
      - session:  SQLAlchemy AsyncSession — caller (route / get_db) owns the transaction.
      - repo:     RefreshTokenRepo — injected for testability.
      - denylist: TokenDenylist   — Redis-backed fast revocation cache.
    """

    def __init__(
        self,
        session: AsyncSession,
        repo: RefreshTokenRepo,
        denylist: TokenDenylist,
    ) -> None:
        self._session = session
        self._repo = repo
        self._denylist = denylist

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _decode_refresh_jwt(self, token: str) -> dict:
        """Decode and structurally validate a refresh JWT.

        Does NOT check DB state. Raises:
            InvalidRefreshToken — bad signature, malformed, wrong type.
            ExpiredRefreshToken — past exp (with CLOCK_SKEW_SECONDS tolerance).
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
                options={"verify_exp": False},  # manual expiry check with clock skew
            )
        except JWTError:
            raise InvalidRefreshToken()

        required = {"sub", "jti", "family_id", "type", "iat", "exp"}
        if not required.issubset(payload.keys()) or payload.get("type") != "refresh":
            raise InvalidRefreshToken()

        now = datetime.now(UTC).timestamp()
        if payload["exp"] + CLOCK_SKEW_SECONDS < now:
            raise ExpiredRefreshToken()

        return payload

    def _build_refresh_jwt(
        self,
        user_id: uuid.UUID,
        family_id: str,
        jti: str,
        now: datetime,
    ) -> str:
        claims = build_refresh_claims(
            user_id=user_id,
            family_id=uuid.UUID(family_id),
            jti=uuid.UUID(jti),
            issued_at=now,
        )
        return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def _aware(dt: datetime) -> datetime:
        """Ensure a datetime is UTC-aware (SQLAlchemy may return naive datetimes)."""
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def issue_pair(self, user: object, device_info: dict) -> TokenPair:
        """Issue a brand-new access + refresh token pair for a user.

        Creates a new token family. Caller's session is used for the insert;
        commit is handled by the caller (route / get_db dependency).

        Args:
            user:        ORM User object with `.id` (UUID) and `.email` (str).
            device_info: Dict with ``user_agent`` and ``ip_address``.

        Returns:
            TokenPair with both tokens and access TTL.
        """
        now = datetime.now(UTC)
        family_id = str(uuid.uuid4())
        jti = str(uuid.uuid4())
        expires_at = compute_refresh_expires_at(now)

        refresh_jwt = self._build_refresh_jwt(user.id, family_id, jti, now)
        token_hash = hash_token(refresh_jwt)

        rt = RefreshToken(
            jti=jti,
            user_id=user.id,
            family_id=family_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        await self._repo.insert(rt)
        await self._session.flush()

        access_jwt = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )

        logger.info(
            "refresh.issued",
            extra={"user_id": str(user.id), "family_id": family_id},
        )

        return TokenPair(
            access_token=access_jwt,
            refresh_token=refresh_jwt,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def rotate(self, refresh_jwt: str, device_info: dict) -> TokenPair:
        """Rotate a refresh token: revoke old, issue new in the same family.

        Uses SELECT FOR UPDATE for row-level locking (concurrent rotate
        protection). The caller's transaction is the lock scope.

        Raises:
            InvalidRefreshToken — JWT invalid or not in DB.
            ExpiredRefreshToken — JWT or DB record expired.
            ReuseDetected       — revoked token reused (entire family killed).
        """
        payload = self._decode_refresh_jwt(refresh_jwt)
        jti = payload["jti"]
        token_hash = hash_token(refresh_jwt)
        now = datetime.now(UTC)

        # FR-6: fast-path denylist check — fail-open if Redis is down
        try:
            if await self._denylist.contains(jti):
                raise RevokedRefreshToken()
        except RevokedRefreshToken:
            raise
        except Exception as exc:
            logger.warning("denylist.contains error (fail-open): %s", exc)

        row = await self._repo.find_by_hash_for_update(token_hash)

        if row is None:
            raise InvalidRefreshToken()

        if row.revoked_at is not None:
            # Reuse detected — kill entire family to protect the user
            await self._repo.revoke_family(row.family_id, now)
            await self._session.flush()
            remaining = max(0, int(payload["exp"] - now.timestamp()))
            try:
                await self._denylist.add(row.jti, ttl_seconds=remaining)
                refresh_metrics.record_denylist_hit()
            except Exception as exc:
                logger.warning("denylist.add error (fail-open, reuse): %s", exc)
            logger.warning(
                "refresh.reuse_detected",
                extra={"family_id": row.family_id, "user_id": str(row.user_id)},
            )
            refresh_metrics.record_reuse_detected()
            raise ReuseDetected()

        if self._aware(row.expires_at) < now:
            raise ExpiredRefreshToken()

        # --- Atomic rotation ---
        await self._repo.mark_revoked(row.jti, now)

        new_jti = str(uuid.uuid4())
        new_expires_at = compute_refresh_expires_at(now)
        new_refresh_jwt = self._build_refresh_jwt(
            uuid.UUID(str(row.user_id)),
            row.family_id,
            new_jti,
            now,
        )
        new_hash = hash_token(new_refresh_jwt)

        new_rt = RefreshToken(
            jti=new_jti,
            user_id=row.user_id,
            family_id=row.family_id,
            token_hash=new_hash,
            expires_at=new_expires_at,
        )
        await self._repo.insert(new_rt)
        await self._session.flush()

        # Post-flush: denylist the old JTI (DB flushed → safe to write Redis)
        remaining = max(0, int(payload["exp"] - now.timestamp()))
        try:
            await self._denylist.add(row.jti, ttl_seconds=remaining)
            refresh_metrics.record_denylist_hit()
        except Exception as exc:
            logger.warning("denylist.add error (fail-open, rotate): %s", exc)

        logger.info(
            "refresh.rotated",
            extra={"family_id": row.family_id, "user_id": str(row.user_id)},
        )
        refresh_metrics.record_rotation()

        access_jwt = create_access_token(data={"sub": str(row.user_id)})

        return TokenPair(
            access_token=access_jwt,
            refresh_token=new_refresh_jwt,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def revoke(self, refresh_jwt: str) -> None:
        """Revoke a single refresh token. Idempotent — no error if not found.

        Used for single-device logout.
        """
        try:
            payload = self._decode_refresh_jwt(refresh_jwt)
        except (InvalidRefreshToken, ExpiredRefreshToken):
            return  # Invalid/expired token — nothing to revoke

        token_hash = hash_token(refresh_jwt)
        now = datetime.now(UTC)

        row = await self._repo.find_by_hash(token_hash)
        if row is None or row.revoked_at is not None:
            return  # Already revoked or unknown — idempotent

        await self._repo.mark_revoked(row.jti, now)
        await self._session.flush()

        remaining = max(0, int(payload["exp"] - now.timestamp()))
        try:
            await self._denylist.add(row.jti, ttl_seconds=remaining)
            refresh_metrics.record_denylist_hit()
        except Exception as exc:
            logger.warning("denylist.add error (fail-open, revoke): %s", exc)

        logger.info(
            "refresh.revoked",
            extra={
                "user_id": str(row.user_id),
                "family_id": row.family_id,
                "reason": "logout",
            },
        )

    async def revoke_all(self, user_id: uuid.UUID) -> int:
        """Revoke all active refresh tokens for a user (logout-all).

        Returns:
            Number of tokens revoked.
        """
        now = datetime.now(UTC)
        count = await self._repo.revoke_all(user_id, now)
        await self._session.flush()

        logger.info(
            "refresh.revoked",
            extra={"user_id": str(user_id), "reason": "logout_all", "count": count},
        )

        return count

    async def list_sessions(self, user_id: uuid.UUID) -> list[SessionDTO]:
        """Return active (non-revoked, non-expired) refresh token sessions for a user."""
        tokens = await self._repo.list_active_by_user(user_id)
        return [
            SessionDTO(
                jti=t.jti,
                family_id=t.family_id,
                created_at=self._aware(t.created_at),
                expires_at=self._aware(t.expires_at),
            )
            for t in tokens
        ]
