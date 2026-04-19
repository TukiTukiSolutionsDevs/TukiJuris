"""Integration-style tests: RefreshTokenService + real TokenDenylist.

These tests use a real TokenDenylist backed by an in-memory FakeRedis stub
instead of AsyncMock.  This catches signature mismatches (e.g. wrong kwarg
names) that AsyncMock silently swallows.

Covers C1 + C4 from the verify-report corrections:
  - C1: denylist.add() called with correct kwarg ``ttl_seconds`` (not ``ttl``)
  - C4: denylist.contains() checked BEFORE DB lookup in rotate()
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.refresh_token import RefreshToken


# ---------------------------------------------------------------------------
# Minimal in-memory Redis stub
# ---------------------------------------------------------------------------


class _FakeRedis:
    """dict-backed Redis stub — implements only the methods TokenDenylist uses."""

    def __init__(self) -> None:
        self.store: dict[str, tuple] = {}

    async def set(self, key: str, value, ex: int | None = None) -> None:
        self.store[key] = (value, ex)

    async def exists(self, key: str) -> int:
        return 1 if key in self.store else 0


# ---------------------------------------------------------------------------
# Shared helpers / fixtures
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


@pytest.fixture
def fake_redis() -> _FakeRedis:
    return _FakeRedis()


@pytest.fixture
def real_denylist(fake_redis):
    from app.core.token_denylist import TokenDenylist

    return TokenDenylist(fake_redis, prefix="test:denylist:")


@pytest.fixture
def mock_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.insert.return_value = _token()
    repo.mark_revoked.return_value = None
    repo.revoke_family.return_value = 1
    repo.find_by_hash.return_value = None
    repo.find_by_hash_for_update.return_value = None
    return repo


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def fake_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "integration@test.com"
    return user


@pytest.fixture
def svc(mock_session, mock_repo, real_denylist):
    from app.services.refresh_token_service import RefreshTokenService

    return RefreshTokenService(
        session=mock_session,
        repo=mock_repo,
        denylist=real_denylist,
    )


# ---------------------------------------------------------------------------
# C1 — ttl_seconds kwarg correctness
# ---------------------------------------------------------------------------


async def test_rotate_no_typeerror_from_denylist_add(svc, mock_repo, fake_user, fake_redis):
    """rotate() must call denylist.add(jti, ttl_seconds=X) without TypeError.

    If the kwarg name is wrong (e.g. ttl=) this raises TypeError at runtime.
    AsyncMock silently accepts any kwarg — only a real TokenDenylist exposes this.
    """
    pair = await svc.issue_pair(fake_user, device_info={})
    active_row = _token(user_id=fake_user.id)
    mock_repo.find_by_hash_for_update.return_value = active_row

    result = await svc.rotate(pair.refresh_token, device_info={})

    assert result is not None
    # Denylist must have written the old JTI
    assert len(fake_redis.store) > 0


async def test_revoke_no_typeerror_from_denylist_add(svc, mock_repo, fake_user, fake_redis):
    """revoke() must call denylist.add(jti, ttl_seconds=X) without TypeError."""
    pair = await svc.issue_pair(fake_user, device_info={})
    active_row = _token(user_id=fake_user.id)
    mock_repo.find_by_hash.return_value = active_row

    await svc.revoke(pair.refresh_token)

    assert len(fake_redis.store) > 0


async def test_reuse_no_typeerror_from_denylist_add(svc, mock_repo, fake_user):
    """rotate() on a revoked token (reuse path) must not TypeError on denylist.add."""
    from app.core.exceptions import ReuseDetected

    pair = await svc.issue_pair(fake_user, device_info={})
    revoked_row = _token(
        user_id=fake_user.id,
        revoked_at=datetime.now(UTC),
    )
    mock_repo.find_by_hash_for_update.return_value = revoked_row

    with pytest.raises(ReuseDetected):
        await svc.rotate(pair.refresh_token, device_info={})


# ---------------------------------------------------------------------------
# C4 — denylist.contains() checked before DB lookup
# ---------------------------------------------------------------------------


async def test_rotate_skips_db_when_jti_in_denylist(
    svc, mock_repo, fake_user, real_denylist
):
    """rotate() must short-circuit to RevokedRefreshToken when jti is in denylist.

    The DB (find_by_hash_for_update) must NOT be called.
    """
    from app.config import settings
    from app.core.exceptions import RevokedRefreshToken
    from jose import jwt as jose_jwt

    pair = await svc.issue_pair(fake_user, device_info={})

    # Extract jti from the refresh token
    payload = jose_jwt.decode(
        pair.refresh_token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        options={"verify_exp": False},
    )
    jti = payload["jti"]

    # Pre-populate the real denylist
    await real_denylist.add(jti, ttl_seconds=3600)

    mock_repo.find_by_hash_for_update.reset_mock()

    with pytest.raises(RevokedRefreshToken):
        await svc.rotate(pair.refresh_token, device_info={})

    mock_repo.find_by_hash_for_update.assert_not_awaited()


async def test_rotate_proceeds_when_jti_not_in_denylist(svc, mock_repo, fake_user):
    """rotate() must proceed to DB lookup when jti is NOT in denylist."""
    pair = await svc.issue_pair(fake_user, device_info={})
    active_row = _token(user_id=fake_user.id)
    mock_repo.find_by_hash_for_update.return_value = active_row

    result = await svc.rotate(pair.refresh_token, device_info={})

    assert result is not None
    mock_repo.find_by_hash_for_update.assert_awaited_once()


async def test_rotate_fail_open_when_denylist_raises(mock_session, mock_repo, fake_user):
    """rotate() must continue if denylist.contains() raises (fail-open)."""

    class _BrokenRedis:
        async def set(self, *a, **kw):
            raise ConnectionError("Redis down")

        async def exists(self, *a, **kw):
            raise ConnectionError("Redis down")

    from app.core.token_denylist import TokenDenylist
    from app.services.refresh_token_service import RefreshTokenService

    broken_denylist = TokenDenylist(_BrokenRedis(), prefix="test:")
    svc_broken = RefreshTokenService(
        session=mock_session, repo=mock_repo, denylist=broken_denylist
    )

    pair = await svc_broken.issue_pair(fake_user, device_info={})
    active_row = _token(user_id=fake_user.id)
    mock_repo.find_by_hash_for_update.return_value = active_row

    # Must NOT raise — fail-open means Redis errors are swallowed
    result = await svc_broken.rotate(pair.refresh_token, device_info={})
    assert result is not None
