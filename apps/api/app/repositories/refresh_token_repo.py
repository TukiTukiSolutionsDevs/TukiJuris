"""Async repository for RefreshToken persistence operations."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepo:
    """Data-access object for the refresh_tokens table.

    All operations are async and accept an external AsyncSession — the caller
    (service layer or FastAPI dependency) owns the transaction lifecycle.
    Raw tokens are never handled here; only their SHA-256 hashes.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def insert(self, token: RefreshToken) -> RefreshToken:
        """Persist a new refresh token and flush to populate DB-generated fields."""
        self._session.add(token)
        await self._session.flush()
        return token

    async def mark_revoked(self, jti: str, revoked_at: datetime) -> None:
        """Set revoked_at on the single token identified by its JTI."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.jti == jti)
            .values(revoked_at=revoked_at)
        )
        await self._session.execute(stmt)

    async def revoke_family(self, family_id: str, revoked_at: datetime) -> int:
        """Revoke all currently-active tokens in a token family.

        Returns the number of rows affected (0 if none were active).
        Used for theft-detection: when a reused token is detected, the
        entire family is killed to force re-authentication.
        """
        stmt = (
            update(RefreshToken)
            .where(
                and_(
                    RefreshToken.family_id == family_id,
                    RefreshToken.revoked_at.is_(None),
                )
            )
            .values(revoked_at=revoked_at)
        )
        result = await self._session.execute(stmt)
        return result.rowcount

    async def revoke_all(self, user_id: uuid.UUID, revoked_at: datetime) -> int:
        """Revoke every active token for a user (logout-all).

        Returns the number of rows affected.
        """
        stmt = (
            update(RefreshToken)
            .where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.revoked_at.is_(None),
                )
            )
            .values(revoked_at=revoked_at)
        )
        result = await self._session.execute(stmt)
        return result.rowcount

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def find_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Look up a token by its SHA-256 hash. Returns None if not found."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_hash_for_update(self, token_hash: str) -> RefreshToken | None:
        """Look up a token with SELECT FOR UPDATE to serialise concurrent rotations.

        Use this instead of find_by_hash when the caller is about to mutate
        the token (e.g. rotation flow) to prevent double-rotation races.
        """
        stmt = (
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .with_for_update()
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active_by_user(self, user_id: uuid.UUID) -> list[RefreshToken]:
        """Return all non-revoked, non-expired tokens for a given user.

        Used to display active sessions and for pre-logout enumeration.
        """
        now = datetime.now(UTC)
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
