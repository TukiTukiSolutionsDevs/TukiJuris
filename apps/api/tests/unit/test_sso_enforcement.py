"""Unit tests — SSO enforcement on email/password login (RED: T5.5)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_user(user_id: uuid.UUID | None = None, is_active: bool = True) -> MagicMock:
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.email = "user@example.com"
    user.hashed_password = "hashed_pw"
    user.is_active = is_active
    return user


def make_request(ip: str = "127.0.0.1") -> MagicMock:
    req = MagicMock()
    req.client.host = ip
    req.headers.get.return_value = "TestAgent/1.0"
    return req


def make_login_body(email: str = "user@example.com", password: str = "Password1"):
    from app.api.routes.auth import LoginRequest

    return LoginRequest(email=email, password=password)


def make_db_returning_user(user: MagicMock) -> AsyncMock:
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    db.execute = AsyncMock(return_value=result)
    return db


def make_token_pair_mock() -> MagicMock:
    pair = MagicMock()
    pair.access_token = "access_tok"
    pair.refresh_token = "refresh_tok"
    pair.expires_in = 900
    return pair


# ---------------------------------------------------------------------------
# T5.5 — _has_privileged_role helper
# ---------------------------------------------------------------------------


class TestHasPrivilegedRole:
    async def test_returns_true_for_admin(self):
        from app.api.routes.auth import _has_privileged_role

        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value = ["admin"]
        db.execute = AsyncMock(return_value=result)

        assert await _has_privileged_role(db, uuid.uuid4()) is True

    async def test_returns_true_for_super_admin(self):
        from app.api.routes.auth import _has_privileged_role

        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value = ["super_admin"]
        db.execute = AsyncMock(return_value=result)

        assert await _has_privileged_role(db, uuid.uuid4()) is True

    async def test_returns_true_for_support(self):
        from app.api.routes.auth import _has_privileged_role

        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value = ["support"]
        db.execute = AsyncMock(return_value=result)

        assert await _has_privileged_role(db, uuid.uuid4()) is True

    async def test_returns_true_for_finance(self):
        from app.api.routes.auth import _has_privileged_role

        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value = ["finance"]
        db.execute = AsyncMock(return_value=result)

        assert await _has_privileged_role(db, uuid.uuid4()) is True

    async def test_returns_false_for_viewer(self):
        from app.api.routes.auth import _has_privileged_role

        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value = ["viewer"]
        db.execute = AsyncMock(return_value=result)

        assert await _has_privileged_role(db, uuid.uuid4()) is False

    async def test_returns_false_for_user_with_no_role(self):
        from app.api.routes.auth import _has_privileged_role

        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value = []
        db.execute = AsyncMock(return_value=result)

        assert await _has_privileged_role(db, uuid.uuid4()) is False

    async def test_returns_true_when_one_privileged_role_among_many(self):
        from app.api.routes.auth import _has_privileged_role

        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value = ["viewer", "admin"]
        db.execute = AsyncMock(return_value=result)

        assert await _has_privileged_role(db, uuid.uuid4()) is True


# ---------------------------------------------------------------------------
# T5.5 — Login endpoint: SSO enforcement
# ---------------------------------------------------------------------------


class TestLoginSSOEnforcement:
    async def test_privileged_user_blocked_returns_403(self):
        from app.api.routes.auth import login

        user = make_user()
        db = make_db_returning_user(user)
        service = AsyncMock()

        with patch("app.api.routes.auth.check_login_attempts", return_value=True):
            with patch("app.api.routes.auth.verify_password", return_value=True):
                with patch(
                    "app.api.routes.auth._has_privileged_role",
                    new=AsyncMock(return_value=True),
                ):
                    with pytest.raises(HTTPException) as exc_info:
                        await login(
                            body=make_login_body(),
                            request=make_request(),
                            response=Response(),
                            db=db,
                            service=service,
                        )

        assert exc_info.value.status_code == 403

    async def test_privileged_user_blocked_detail_mentions_sso(self):
        from app.api.routes.auth import login

        user = make_user()
        db = make_db_returning_user(user)
        service = AsyncMock()

        with patch("app.api.routes.auth.check_login_attempts", return_value=True):
            with patch("app.api.routes.auth.verify_password", return_value=True):
                with patch(
                    "app.api.routes.auth._has_privileged_role",
                    new=AsyncMock(return_value=True),
                ):
                    with pytest.raises(HTTPException) as exc_info:
                        await login(
                            body=make_login_body(),
                            request=make_request(),
                            response=Response(),
                            db=db,
                            service=service,
                        )

        assert exc_info.value.detail == "Privileged accounts must use Google SSO"

    async def test_regular_user_allowed_through(self):
        from app.api.routes.auth import login

        user = make_user()
        db = make_db_returning_user(user)
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair_mock()

        with patch("app.api.routes.auth.check_login_attempts", return_value=True):
            with patch("app.api.routes.auth.verify_password", return_value=True):
                with patch(
                    "app.api.routes.auth._has_privileged_role",
                    new=AsyncMock(return_value=False),
                ):
                    result = await login(
                        body=make_login_body(),
                        request=make_request(),
                        response=Response(),
                        db=db,
                        service=service,
                    )

        assert result.access_token == "access_tok"

    async def test_sso_check_called_with_correct_user_id(self):
        from app.api.routes.auth import login

        user = make_user()
        db = make_db_returning_user(user)
        service = AsyncMock()
        service.issue_pair.return_value = make_token_pair_mock()
        mock_check = AsyncMock(return_value=False)

        with patch("app.api.routes.auth.check_login_attempts", return_value=True):
            with patch("app.api.routes.auth.verify_password", return_value=True):
                with patch("app.api.routes.auth._has_privileged_role", new=mock_check):
                    await login(
                        body=make_login_body(),
                        request=make_request(),
                        response=Response(),
                        db=db,
                        service=service,
                    )

        mock_check.assert_called_once_with(db, user.id)

    async def test_sso_check_not_called_for_invalid_credentials(self):
        """SSO enforcement must not run if credentials are wrong (user is None)."""
        from app.api.routes.auth import login

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None  # user not found
        db.execute = AsyncMock(return_value=result_mock)

        service = AsyncMock()
        mock_check = AsyncMock(return_value=False)

        with patch("app.api.routes.auth.check_login_attempts", return_value=True):
            with patch("app.api.routes.auth._has_privileged_role", new=mock_check):
                with pytest.raises(HTTPException) as exc_info:
                    await login(
                        body=make_login_body(),
                        request=make_request(),
                        response=Response(),
                        db=db,
                        service=service,
                    )

        assert exc_info.value.status_code == 401
        mock_check.assert_not_called()

    async def test_sso_check_not_called_for_disabled_account(self):
        """Disabled account check (403) must run before SSO check."""
        from app.api.routes.auth import login

        user = make_user(is_active=False)
        db = make_db_returning_user(user)
        service = AsyncMock()
        mock_check = AsyncMock(return_value=False)

        with patch("app.api.routes.auth.check_login_attempts", return_value=True):
            with patch("app.api.routes.auth.verify_password", return_value=True):
                with patch("app.api.routes.auth._has_privileged_role", new=mock_check):
                    with pytest.raises(HTTPException) as exc_info:
                        await login(
                            body=make_login_body(),
                            request=make_request(),
                            response=Response(),
                            db=db,
                            service=service,
                        )

        assert exc_info.value.status_code == 403
        assert "disabled" in exc_info.value.detail.lower()
        mock_check.assert_not_called()
