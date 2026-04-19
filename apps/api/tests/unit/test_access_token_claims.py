"""Access token claims tests — Task 16.

Asserts that is_admin is correctly embedded in JWTs issued by:
  - RefreshTokenService.issue_pair()
  - RefreshTokenService.rotate()

Both admin=True and admin=False cases are covered.
All external deps (DB, Redis) are mocked.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.security import decode_access_token
from app.models.refresh_token import RefreshToken


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(is_admin: bool = False) -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = f"{'admin' if is_admin else 'user'}@test.com"
    user.is_admin = is_admin
    user.is_active = True
    return user


def _make_refresh_token_row(user_id: uuid.UUID, revoked: bool = False) -> RefreshToken:
    now = datetime.now(UTC)
    return RefreshToken(
        id=uuid.uuid4(),
        jti=str(uuid.uuid4()),
        user_id=user_id,
        family_id=str(uuid.uuid4()),
        token_hash="a" * 64,
        expires_at=now + timedelta(days=30),
        revoked_at=None,
        created_at=now,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.insert.return_value = None
    repo.mark_revoked.return_value = None
    repo.find_by_hash_for_update.return_value = None
    return repo


@pytest.fixture
def mock_denylist() -> AsyncMock:
    dl = AsyncMock()
    dl.add.return_value = None
    dl.contains.return_value = False
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


# ---------------------------------------------------------------------------
# issue_pair() — is_admin claim
# ---------------------------------------------------------------------------


class TestIssuePairAdminClaim:
    async def test_non_admin_user_has_is_admin_false(self, svc):
        user = _make_user(is_admin=False)
        pair = await svc.issue_pair(user, {"user_agent": "test", "ip_address": "127.0.0.1"})

        payload = decode_access_token(pair.access_token)
        assert payload is not None, "Access token must be decodable"
        assert "is_admin" in payload, "is_admin claim must be present"
        assert payload["is_admin"] is False

    async def test_admin_user_has_is_admin_true(self, svc):
        user = _make_user(is_admin=True)
        pair = await svc.issue_pair(user, {"user_agent": "test", "ip_address": "127.0.0.1"})

        payload = decode_access_token(pair.access_token)
        assert payload is not None
        assert payload["is_admin"] is True

    async def test_is_admin_matches_user_attribute(self, svc):
        for is_admin in [True, False]:
            user = _make_user(is_admin=is_admin)
            pair = await svc.issue_pair(user, {"user_agent": "test", "ip_address": "127.0.0.1"})
            payload = decode_access_token(pair.access_token)
            assert payload["is_admin"] == is_admin, (
                f"is_admin={is_admin} in user must match is_admin={payload['is_admin']} in token"
            )

    async def test_sub_claim_matches_user_id(self, svc):
        user = _make_user()
        pair = await svc.issue_pair(user, {"user_agent": "test", "ip_address": "127.0.0.1"})
        payload = decode_access_token(pair.access_token)
        assert payload["sub"] == str(user.id)

    async def test_type_claim_is_access(self, svc):
        user = _make_user()
        pair = await svc.issue_pair(user, {"user_agent": "test", "ip_address": "127.0.0.1"})
        payload = decode_access_token(pair.access_token)
        assert payload["type"] == "access"


# ---------------------------------------------------------------------------
# rotate() — is_admin claim from DB lookup
# ---------------------------------------------------------------------------


class TestRotateAdminClaim:
    def _make_valid_refresh_jwt(self, user_id: uuid.UUID) -> str:
        """Build a minimal valid refresh JWT for testing rotate()."""
        from app.core.security import build_refresh_claims
        from app.config import settings
        from jose import jwt

        now = datetime.now(UTC)
        claims = build_refresh_claims(
            user_id=user_id,
            family_id=uuid.uuid4(),
            jti=uuid.uuid4(),
            issued_at=now,
        )
        return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    async def test_rotate_embeds_is_admin_false(self, svc, mock_session, mock_repo, mock_denylist):
        user_id = uuid.uuid4()
        refresh_jwt = self._make_valid_refresh_jwt(user_id)

        row = _make_refresh_token_row(user_id)
        # Override token hash to match the JWT we built
        from app.core.security import hash_token
        row.token_hash = hash_token(refresh_jwt)

        mock_repo.find_by_hash_for_update.return_value = row
        mock_repo.insert.return_value = None
        mock_denylist.contains.return_value = False

        # Mock session.get(UserModel, user_id) → non-admin user
        user_obj = MagicMock()
        user_obj.is_admin = False
        mock_session.get = AsyncMock(return_value=user_obj)

        pair = await svc.rotate(refresh_jwt, {"user_agent": "test", "ip_address": "127.0.0.1"})
        payload = decode_access_token(pair.access_token)
        assert payload["is_admin"] is False

    async def test_rotate_embeds_is_admin_true(self, svc, mock_session, mock_repo, mock_denylist):
        user_id = uuid.uuid4()
        refresh_jwt = self._make_valid_refresh_jwt(user_id)

        row = _make_refresh_token_row(user_id)
        from app.core.security import hash_token
        row.token_hash = hash_token(refresh_jwt)

        mock_repo.find_by_hash_for_update.return_value = row
        mock_repo.insert.return_value = None
        mock_denylist.contains.return_value = False

        # Mock session.get → admin user
        user_obj = MagicMock()
        user_obj.is_admin = True
        mock_session.get = AsyncMock(return_value=user_obj)

        pair = await svc.rotate(refresh_jwt, {"user_agent": "test", "ip_address": "127.0.0.1"})
        payload = decode_access_token(pair.access_token)
        assert payload["is_admin"] is True

    async def test_rotate_defaults_to_false_when_user_not_found(
        self, svc, mock_session, mock_repo, mock_denylist
    ):
        """If user row is missing during rotate, is_admin defaults to False (safe)."""
        user_id = uuid.uuid4()
        refresh_jwt = self._make_valid_refresh_jwt(user_id)

        row = _make_refresh_token_row(user_id)
        from app.core.security import hash_token
        row.token_hash = hash_token(refresh_jwt)

        mock_repo.find_by_hash_for_update.return_value = row
        mock_denylist.contains.return_value = False

        # User not found (e.g. deleted account)
        mock_session.get = AsyncMock(return_value=None)

        pair = await svc.rotate(refresh_jwt, {"user_agent": "test", "ip_address": "127.0.0.1"})
        payload = decode_access_token(pair.access_token)
        assert payload["is_admin"] is False, "Missing user must default is_admin to False"
