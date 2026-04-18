"""Unit tests for RefreshTokenService — all external deps mocked.

Tests follow strict R-G-R: this file is the RED phase (T-7.0).
All tests fail before the service implementation exists.
"""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import (
    ExpiredRefreshToken,
    InvalidRefreshToken,
    ReuseDetected,
)
from app.models.refresh_token import RefreshToken


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _token(
    user_id: uuid.UUID | None = None,
    family_id: str | None = None,
    jti: str | None = None,
    revoked_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> RefreshToken:
    now = datetime.now(UTC)
    return RefreshToken(
        id=uuid.uuid4(),
        jti=jti or str(uuid.uuid4()),
        user_id=user_id or uuid.uuid4(),
        family_id=family_id or str(uuid.uuid4()),
        token_hash="a" * 64,
        expires_at=expires_at or now + timedelta(days=30),
        revoked_at=revoked_at,
        created_at=now,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.insert.return_value = _token()
    repo.mark_revoked.return_value = None
    repo.revoke_family.return_value = 1
    repo.revoke_all.return_value = 0
    repo.find_by_hash.return_value = None
    repo.find_by_hash_for_update.return_value = None
    repo.list_active_by_user.return_value = []
    return repo


@pytest.fixture
def mock_denylist() -> AsyncMock:
    dl = AsyncMock()
    dl.add.return_value = None
    dl.contains.return_value = False  # default: jti NOT in denylist
    return dl


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def svc(mock_session, mock_repo, mock_denylist):
    from app.services.refresh_token_service import RefreshTokenService

    return RefreshTokenService(
        session=mock_session,
        repo=mock_repo,
        denylist=mock_denylist,
    )


@pytest.fixture
def fake_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "unit@test.com"
    return user


# ---------------------------------------------------------------------------
# issue_pair
# ---------------------------------------------------------------------------


async def test_issue_pair_returns_token_pair(svc, mock_repo, fake_user):
    """issue_pair() creates a new family and returns a well-formed TokenPair."""
    from app.services.refresh_token_service import TokenPair

    pair = await svc.issue_pair(fake_user, device_info={"user_agent": "ua", "ip_address": "127.0.0.1"})

    assert isinstance(pair, TokenPair)
    assert pair.access_token and len(pair.access_token) > 10
    assert pair.refresh_token and len(pair.refresh_token) > 10
    assert pair.token_type == "bearer"
    assert pair.expires_in > 0
    mock_repo.insert.assert_awaited_once()


async def test_issue_pair_stores_correct_user_id(svc, mock_repo, fake_user):
    """The inserted RefreshToken uses the correct user_id."""
    await svc.issue_pair(fake_user, device_info={})

    inserted: RefreshToken = mock_repo.insert.call_args[0][0]
    assert inserted.user_id == fake_user.id


async def test_issue_pair_refresh_jwt_has_refresh_type(svc, fake_user):
    """The refresh_token in the pair has type=refresh in its payload."""
    from app.config import settings
    from jose import jwt as jose_jwt

    pair = await svc.issue_pair(fake_user, device_info={})
    payload = jose_jwt.decode(
        pair.refresh_token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        options={"verify_exp": False},
    )
    assert payload["type"] == "refresh"
    assert payload["sub"] == str(fake_user.id)


async def test_issue_pair_access_jwt_has_access_type_and_iat(svc, fake_user):
    """The access_token in the pair has type=access and numeric iat."""
    from app.config import settings
    from jose import jwt as jose_jwt

    pair = await svc.issue_pair(fake_user, device_info={})
    payload = jose_jwt.decode(
        pair.access_token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        options={"verify_exp": False},
    )
    assert payload.get("type") == "access", f"Expected type=access, got: {payload}"
    assert "iat" in payload, "access token must include iat claim"
    assert isinstance(payload["iat"], (int, float))


async def test_issue_pair_flushes_session(svc, mock_session, fake_user):
    """issue_pair() flushes the session after inserting."""
    await svc.issue_pair(fake_user, device_info={})
    mock_session.flush.assert_awaited()


# ---------------------------------------------------------------------------
# rotate — happy path
# ---------------------------------------------------------------------------


async def test_rotate_happy_path_returns_new_pair(svc, mock_repo, mock_denylist, fake_user):
    """rotate() on a valid active token returns a new TokenPair."""
    from app.services.refresh_token_service import TokenPair

    first_pair = await svc.issue_pair(fake_user, device_info={})

    active_row = _token(user_id=fake_user.id)
    mock_repo.find_by_hash_for_update.return_value = active_row

    result = await svc.rotate(first_pair.refresh_token, device_info={})

    assert isinstance(result, TokenPair)
    mock_repo.mark_revoked.assert_awaited_once()
    mock_denylist.add.assert_awaited_once()


async def test_rotate_invalid_jwt_raises_invalid(svc):
    """rotate() with a non-JWT string raises InvalidRefreshToken."""
    with pytest.raises(InvalidRefreshToken):
        await svc.rotate("not.a.jwt", device_info={})


async def test_rotate_access_token_passed_raises_invalid(svc, fake_user):
    """rotate() with an access token (wrong type) raises InvalidRefreshToken."""
    from app.core.security import create_access_token

    access = create_access_token(data={"sub": str(fake_user.id), "email": fake_user.email})
    with pytest.raises(InvalidRefreshToken):
        await svc.rotate(access, device_info={})


async def test_rotate_token_not_in_db_raises_invalid(svc, mock_repo, fake_user):
    """rotate() when hash is absent from DB raises InvalidRefreshToken."""
    pair = await svc.issue_pair(fake_user, device_info={})
    mock_repo.find_by_hash_for_update.return_value = None

    with pytest.raises(InvalidRefreshToken):
        await svc.rotate(pair.refresh_token, device_info={})


async def test_rotate_expired_db_row_raises_expired(svc, mock_repo, fake_user):
    """rotate() when DB row's expires_at is past raises ExpiredRefreshToken."""
    pair = await svc.issue_pair(fake_user, device_info={})

    expired_row = _token(
        user_id=fake_user.id,
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    mock_repo.find_by_hash_for_update.return_value = expired_row

    with pytest.raises(ExpiredRefreshToken):
        await svc.rotate(pair.refresh_token, device_info={})


async def test_rotate_revoked_token_raises_reuse_and_kills_family(
    svc, mock_repo, mock_denylist, fake_user
):
    """rotate() on a revoked DB row raises ReuseDetected and calls revoke_family."""
    pair = await svc.issue_pair(fake_user, device_info={})

    revoked_row = _token(
        user_id=fake_user.id,
        revoked_at=datetime.now(UTC) - timedelta(hours=1),
    )
    mock_repo.find_by_hash_for_update.return_value = revoked_row

    with pytest.raises(ReuseDetected):
        await svc.rotate(pair.refresh_token, device_info={})

    mock_repo.revoke_family.assert_awaited_once()


async def test_rotate_inserts_new_token_in_same_family(svc, mock_repo, fake_user):
    """rotate() inserts a new RefreshToken with the same family_id."""
    pair = await svc.issue_pair(fake_user, device_info={})

    family_id = str(uuid.uuid4())
    active_row = _token(user_id=fake_user.id, family_id=family_id)
    mock_repo.find_by_hash_for_update.return_value = active_row

    await svc.rotate(pair.refresh_token, device_info={})

    # Second insert call (first was issue_pair, second is rotate)
    calls = mock_repo.insert.await_args_list
    assert len(calls) == 2
    new_rt: RefreshToken = calls[1][0][0]
    assert new_rt.family_id == family_id


# ---------------------------------------------------------------------------
# revoke
# ---------------------------------------------------------------------------


async def test_revoke_marks_token_revoked_and_denylists(svc, mock_repo, mock_denylist, fake_user):
    """revoke() marks the token revoked in DB and adds jti to denylist."""
    pair = await svc.issue_pair(fake_user, device_info={})

    active_row = _token(user_id=fake_user.id)
    mock_repo.find_by_hash.return_value = active_row

    await svc.revoke(pair.refresh_token)

    mock_repo.mark_revoked.assert_awaited()
    mock_denylist.add.assert_awaited()


async def test_revoke_idempotent_when_token_not_found(svc, mock_repo, mock_denylist, fake_user):
    """revoke() with unknown token does not raise — idempotent."""
    pair = await svc.issue_pair(fake_user, device_info={})
    mock_repo.find_by_hash.return_value = None

    await svc.revoke(pair.refresh_token)  # must not raise

    mock_repo.mark_revoked.assert_not_awaited()
    mock_denylist.add.assert_not_awaited()


async def test_revoke_idempotent_when_already_revoked(svc, mock_repo, fake_user):
    """revoke() on an already-revoked token does not call mark_revoked again."""
    pair = await svc.issue_pair(fake_user, device_info={})

    already_revoked = _token(user_id=fake_user.id, revoked_at=datetime.now(UTC))
    mock_repo.find_by_hash.return_value = already_revoked

    await svc.revoke(pair.refresh_token)  # must not raise

    mock_repo.mark_revoked.assert_not_awaited()


async def test_revoke_invalid_jwt_is_silently_ignored(svc, mock_repo):
    """revoke() with a garbage token does not raise — invalid tokens have nothing to revoke."""
    await svc.revoke("garbage.token.here")  # must not raise
    mock_repo.find_by_hash.assert_not_awaited()


# ---------------------------------------------------------------------------
# revoke_all
# ---------------------------------------------------------------------------


async def test_revoke_all_delegates_to_repo_and_returns_count(svc, mock_repo):
    """revoke_all() delegates to repo.revoke_all and returns the count."""
    mock_repo.revoke_all.return_value = 3
    count = await svc.revoke_all(uuid.uuid4())
    assert count == 3
    mock_repo.revoke_all.assert_awaited_once()


async def test_revoke_all_flushes_session(svc, mock_session, mock_repo):
    """revoke_all() flushes the session after revoking."""
    mock_repo.revoke_all.return_value = 1
    await svc.revoke_all(uuid.uuid4())
    mock_session.flush.assert_awaited()


# ---------------------------------------------------------------------------
# list_sessions
# ---------------------------------------------------------------------------


async def test_list_sessions_returns_session_dtos(svc, mock_repo):
    """list_sessions() maps active tokens to SessionDTO list."""
    from app.services.refresh_token_service import SessionDTO

    user_id = uuid.uuid4()
    mock_repo.list_active_by_user.return_value = [
        _token(user_id=user_id),
        _token(user_id=user_id),
    ]

    sessions = await svc.list_sessions(user_id)

    assert len(sessions) == 2
    assert all(isinstance(s, SessionDTO) for s in sessions)


async def test_list_sessions_empty_when_no_active_tokens(svc, mock_repo):
    """list_sessions() returns empty list when no active tokens exist."""
    mock_repo.list_active_by_user.return_value = []
    sessions = await svc.list_sessions(uuid.uuid4())
    assert sessions == []


# ---------------------------------------------------------------------------
# Race — asyncio.gather double-rotate simulation
# ---------------------------------------------------------------------------


async def test_race_double_rotate_one_raises_reuse(svc, mock_repo, mock_denylist, fake_user):
    """Two concurrent rotate calls: first wins, second gets ReuseDetected.

    Simulates the DB-level SELECT FOR UPDATE race: the second caller sees
    the token already revoked (by the first) and triggers reuse detection.
    """
    pair = await svc.issue_pair(fake_user, device_info={})

    active_row = _token(user_id=fake_user.id)
    revoked_row = _token(
        user_id=fake_user.id,
        jti=active_row.jti,
        family_id=active_row.family_id,
        revoked_at=datetime.now(UTC),
    )

    call_count = 0

    async def alternating_side_effect(token_hash: str):
        nonlocal call_count
        call_count += 1
        return active_row if call_count == 1 else revoked_row

    mock_repo.find_by_hash_for_update.side_effect = alternating_side_effect

    results = await asyncio.gather(
        svc.rotate(pair.refresh_token, device_info={}),
        svc.rotate(pair.refresh_token, device_info={}),
        return_exceptions=True,
    )

    errors = [r for r in results if isinstance(r, Exception)]
    successes = [r for r in results if not isinstance(r, Exception)]

    assert len(errors) == 1, f"Expected 1 error, got {errors}"
    assert isinstance(errors[0], ReuseDetected)
    assert len(successes) == 1


# ---------------------------------------------------------------------------
# C1 — denylist.add() kwarg signature (real TokenDenylist, no AsyncMock)
# ---------------------------------------------------------------------------


class _FakeRedis:
    """Minimal in-memory Redis stub — only set/exists needed."""

    def __init__(self) -> None:
        self.store: dict = {}

    async def set(self, key: str, value, ex: int | None = None) -> None:
        self.store[key] = (value, ex)

    async def exists(self, key: str) -> int:
        return 1 if key in self.store else 0


async def test_rotate_denylist_add_uses_ttl_seconds_kwarg(mock_repo, mock_session, fake_user):
    """rotate() must call denylist.add(jti, ttl_seconds=X) — not ttl=X.

    Uses a real TokenDenylist (not AsyncMock) so the wrong kwarg name causes
    a TypeError that the AsyncMock would silently swallow.
    """
    from app.core.token_denylist import TokenDenylist
    from app.services.refresh_token_service import RefreshTokenService

    real_denylist = TokenDenylist(_FakeRedis(), prefix="test:deny:")
    svc_real = RefreshTokenService(
        session=mock_session, repo=mock_repo, denylist=real_denylist
    )

    pair = await svc_real.issue_pair(fake_user, device_info={})
    active_row = _token(user_id=fake_user.id)
    mock_repo.find_by_hash_for_update.return_value = active_row

    # Must not raise TypeError
    result = await svc_real.rotate(pair.refresh_token, device_info={})
    assert result is not None


async def test_revoke_denylist_add_uses_ttl_seconds_kwarg(mock_repo, mock_session, fake_user):
    """revoke() must call denylist.add(jti, ttl_seconds=X) — not ttl=X."""
    from app.core.token_denylist import TokenDenylist
    from app.services.refresh_token_service import RefreshTokenService

    real_denylist = TokenDenylist(_FakeRedis(), prefix="test:deny:")
    svc_real = RefreshTokenService(
        session=mock_session, repo=mock_repo, denylist=real_denylist
    )

    pair = await svc_real.issue_pair(fake_user, device_info={})
    active_row = _token(user_id=fake_user.id)
    mock_repo.find_by_hash.return_value = active_row

    # Must not raise TypeError
    await svc_real.revoke(pair.refresh_token)


# ---------------------------------------------------------------------------
# C4 — denylist.contains() wired in rotate() (FR-6)
# ---------------------------------------------------------------------------


async def test_rotate_jti_in_denylist_raises_revoked_without_db_lookup(
    mock_repo, mock_session, fake_user
):
    """rotate() must check denylist BEFORE DB lookup.

    If jti is already in the denylist, raise RevokedRefreshToken (or
    ReuseDetected) without calling find_by_hash_for_update.
    """
    from app.core.exceptions import RevokedRefreshToken
    from app.core.token_denylist import TokenDenylist
    from app.services.refresh_token_service import RefreshTokenService

    fake_redis = _FakeRedis()
    real_denylist = TokenDenylist(fake_redis, prefix="test:deny:")
    svc_real = RefreshTokenService(
        session=mock_session, repo=mock_repo, denylist=real_denylist
    )

    pair = await svc_real.issue_pair(fake_user, device_info={})

    # Extract jti from refresh JWT
    from app.config import settings
    from jose import jwt as jose_jwt

    payload = jose_jwt.decode(
        pair.refresh_token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        options={"verify_exp": False},
    )
    jti = payload["jti"]

    # Pre-populate denylist
    await real_denylist.add(jti, ttl_seconds=3600)

    mock_repo.find_by_hash_for_update.reset_mock()

    with pytest.raises(RevokedRefreshToken):
        await svc_real.rotate(pair.refresh_token, device_info={})

    mock_repo.find_by_hash_for_update.assert_not_awaited()
