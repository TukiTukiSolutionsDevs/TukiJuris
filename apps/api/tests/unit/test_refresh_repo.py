"""Unit tests for RefreshTokenRepo — all DB interactions mocked via AsyncMock.

No real database connection required. Verifies:
  insert, find_by_hash, mark_revoked, revoke_family,
  revoke_all, list_active_by_user, SELECT FOR UPDATE (find_by_hash_for_update).
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_token(
    user_id: uuid.UUID | None = None,
    family_id: str | None = None,
    token_hash: str = "a" * 64,
    revoked_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> RefreshToken:
    now = datetime.now(UTC)
    return RefreshToken(
        id=uuid.uuid4(),
        jti=str(uuid.uuid4()),
        user_id=user_id or uuid.uuid4(),
        family_id=family_id or str(uuid.uuid4()),
        token_hash=token_hash,
        expires_at=expires_at or now + timedelta(days=30),
        revoked_at=revoked_at,
        created_at=now,
    )


def _mock_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


# ---------------------------------------------------------------------------
# T-4.0 — insert
# ---------------------------------------------------------------------------


class TestRefreshTokenRepoInsert:
    """insert() adds the token to the session and flushes."""

    @pytest.mark.asyncio
    async def test_insert_calls_add_and_flush(self):
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        repo = RefreshTokenRepo(session)
        token = _make_token()

        await repo.insert(token)

        session.add.assert_called_once_with(token)
        session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_insert_returns_same_instance(self):
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        repo = RefreshTokenRepo(session)
        token = _make_token()

        result = await repo.insert(token)

        assert result is token


# ---------------------------------------------------------------------------
# T-4.0 — find_by_hash
# ---------------------------------------------------------------------------


class TestRefreshTokenRepoFindByHash:
    """find_by_hash() queries by SHA-256 hash."""

    @pytest.mark.asyncio
    async def test_returns_token_when_found(self):
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        token = _make_token()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = token
        session.execute.return_value = result_mock

        repo = RefreshTokenRepo(session)
        found = await repo.find_by_hash(token.token_hash)

        session.execute.assert_awaited_once()
        assert found is token

    @pytest.mark.asyncio
    async def test_returns_none_when_missing(self):
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute.return_value = result_mock

        repo = RefreshTokenRepo(session)
        found = await repo.find_by_hash("b" * 64)

        assert found is None


# ---------------------------------------------------------------------------
# T-4.0 — mark_revoked
# ---------------------------------------------------------------------------


class TestRefreshTokenRepoMarkRevoked:
    """mark_revoked() issues an UPDATE for a single token by jti."""

    @pytest.mark.asyncio
    async def test_executes_update(self):
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        session.execute.return_value = MagicMock()

        repo = RefreshTokenRepo(session)
        await repo.mark_revoked("some-jti", datetime.now(UTC))

        session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none(self):
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        session.execute.return_value = MagicMock()

        repo = RefreshTokenRepo(session)
        result = await repo.mark_revoked(str(uuid.uuid4()), datetime.now(UTC))

        assert result is None


# ---------------------------------------------------------------------------
# T-4.0 — revoke_family
# ---------------------------------------------------------------------------


class TestRefreshTokenRepoRevokeFamily:
    """revoke_family() invalidates all active tokens sharing a family_id."""

    @pytest.mark.asyncio
    async def test_returns_affected_row_count(self):
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        result_mock = MagicMock()
        result_mock.rowcount = 3
        session.execute.return_value = result_mock

        repo = RefreshTokenRepo(session)
        count = await repo.revoke_family(str(uuid.uuid4()), datetime.now(UTC))

        assert count == 3

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_active_tokens(self):
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        result_mock = MagicMock()
        result_mock.rowcount = 0
        session.execute.return_value = result_mock

        repo = RefreshTokenRepo(session)
        count = await repo.revoke_family(str(uuid.uuid4()), datetime.now(UTC))

        assert count == 0

    @pytest.mark.asyncio
    async def test_executes_statement(self):
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        result_mock = MagicMock()
        result_mock.rowcount = 1
        session.execute.return_value = result_mock

        repo = RefreshTokenRepo(session)
        await repo.revoke_family(str(uuid.uuid4()), datetime.now(UTC))

        session.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# T-4.0 — revoke_all
# ---------------------------------------------------------------------------


class TestRefreshTokenRepoRevokeAll:
    """revoke_all() invalidates every active token for a given user."""

    @pytest.mark.asyncio
    async def test_returns_affected_row_count(self):
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        result_mock = MagicMock()
        result_mock.rowcount = 5
        session.execute.return_value = result_mock

        repo = RefreshTokenRepo(session)
        count = await repo.revoke_all(uuid.uuid4(), datetime.now(UTC))

        assert count == 5

    @pytest.mark.asyncio
    async def test_executes_statement(self):
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        result_mock = MagicMock()
        result_mock.rowcount = 2
        session.execute.return_value = result_mock

        repo = RefreshTokenRepo(session)
        await repo.revoke_all(uuid.uuid4(), datetime.now(UTC))

        session.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# T-4.0 — list_active_by_user
# ---------------------------------------------------------------------------


class TestRefreshTokenRepoListActiveByUser:
    """list_active_by_user() returns non-expired, non-revoked tokens."""

    @pytest.mark.asyncio
    async def test_returns_list_of_tokens(self):
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        tokens = [_make_token(), _make_token()]
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = tokens
        session.execute.return_value = result_mock

        repo = RefreshTokenRepo(session)
        active = await repo.list_active_by_user(uuid.uuid4())

        assert active == tokens

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_none_active(self):
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute.return_value = result_mock

        repo = RefreshTokenRepo(session)
        active = await repo.list_active_by_user(uuid.uuid4())

        assert active == []

    @pytest.mark.asyncio
    async def test_executes_statement(self):
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        session.execute.return_value = result_mock

        repo = RefreshTokenRepo(session)
        await repo.list_active_by_user(uuid.uuid4())

        session.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# T-4.0 — SELECT FOR UPDATE (race prevention)
# ---------------------------------------------------------------------------


class TestRefreshTokenRepoSelectForUpdate:
    """find_by_hash_for_update() serialises concurrent rotations via row lock."""

    @pytest.mark.asyncio
    async def test_returns_token_when_found(self):
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        token = _make_token()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = token
        session.execute.return_value = result_mock

        repo = RefreshTokenRepo(session)
        found = await repo.find_by_hash_for_update(token.token_hash)

        session.execute.assert_awaited_once()
        assert found is token

    @pytest.mark.asyncio
    async def test_returns_none_when_missing(self):
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute.return_value = result_mock

        repo = RefreshTokenRepo(session)
        found = await repo.find_by_hash_for_update("c" * 64)

        assert found is None

    @pytest.mark.asyncio
    async def test_distinct_method_from_find_by_hash(self):
        """for_update variant must be a separate method (different SQL semantics)."""
        from app.repositories.refresh_token_repo import RefreshTokenRepo

        session = _mock_session()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute.return_value = result_mock

        repo = RefreshTokenRepo(session)
        assert hasattr(repo, "find_by_hash_for_update")
        assert hasattr(repo, "find_by_hash")
        assert repo.find_by_hash is not repo.find_by_hash_for_update
