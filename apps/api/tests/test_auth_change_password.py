"""
Tests for POST /api/auth/change-password.

Test matrix (T-01 .. T-09) per spec §3:
  T-01  No Authorization header              → 401
  T-02  Wrong current_password               → 401, detail=invalid_credentials
  T-03  Weak new_password                    → 422
  T-04  OAuth user (hashed_password=None)    → 400, code=oauth_password_unsupported
  T-05  new_password == current_password     → 400, detail=new_password_same_as_current
  T-06  Happy path                           → 204; new password verifies in DB
  T-07  Active refresh tokens revoked        → 204; 0 active tokens remain in DB
  T-08  Audit event emitted                  → log_action called with auth.change_password
  T-09  Rate limit exhausted                 → 429

Pattern: AsyncClient + ASGITransport (same as tests/test_auth.py).
No class wrappers — one async function per scenario.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import verify_password

_URL = "/api/auth/change-password"
_CURRENT_PASSWORD = "TestPassword123!"  # matches auth_client fixture password
_NEW_PASSWORD = "NewSecure456!"


def _unique_email() -> str:
    return f"chpwd-{uuid.uuid4().hex[:10]}@test.com"


# ---------------------------------------------------------------------------
# T-01: No Authorization header → 401
# ---------------------------------------------------------------------------


async def test_no_auth_header_returns_401(client: AsyncClient):
    """T-01: Missing Bearer token → 401 (raised by get_current_user dep)."""
    res = await client.post(
        _URL,
        json={"current_password": _CURRENT_PASSWORD, "new_password": _NEW_PASSWORD},
    )
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# T-02: Wrong current_password → 401 invalid_credentials
# ---------------------------------------------------------------------------


async def test_wrong_current_password_returns_401(auth_client: AsyncClient):
    """T-02: Correct token but wrong current_password → 401, detail=invalid_credentials."""
    res = await auth_client.post(
        _URL,
        json={"current_password": "WrongPassword99!", "new_password": _NEW_PASSWORD},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "invalid_credentials"


# ---------------------------------------------------------------------------
# T-03: Weak new_password → 422
# ---------------------------------------------------------------------------


async def test_weak_new_password_returns_422(auth_client: AsyncClient):
    """T-03: new_password fails validate_password policy → 422.

    'alllower1' is ≥8 chars (passes Pydantic min_length) but has no uppercase letter,
    so validate_password() rejects it with a 422.
    """
    res = await auth_client.post(
        _URL,
        json={"current_password": _CURRENT_PASSWORD, "new_password": "alllower1"},
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# T-04a: OAuth user branch coverage (hashed_password=None via mock) → 400
# ---------------------------------------------------------------------------


async def test_change_password_oauth_user_branch_coverage(client: AsyncClient):
    """T-04a: Branch-coverage test — mocked user with hashed_password=None → 400.

    Strategy: the DB has a NOT NULL constraint on hashed_password, so we cannot
    set it to None via SQL UPDATE. Override get_current_user to return a mock user
    that covers the None branch of `not current_user.hashed_password`.
    The handler raises 400 immediately — before any DB/session/audit deps are used.
    """
    from unittest.mock import MagicMock

    from app.api.deps import get_current_user
    from app.main import app

    mock_user = MagicMock()
    mock_user.hashed_password = None
    mock_user.auth_provider = "microsoft"

    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        res = await client.post(
            _URL,
            json={"current_password": "Irrelevant1!", "new_password": _NEW_PASSWORD},
        )
        assert res.status_code == 400
        detail = res.json()["detail"]
        assert detail["code"] == "oauth_password_unsupported"
        assert detail["auth_provider"] == "microsoft"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# T-04b: OAuth user real DB (hashed_password="" per NOT NULL constraint) → 400
# ---------------------------------------------------------------------------


async def test_change_password_oauth_user_real_db(client: AsyncClient, db_session):
    """T-04b: Real DB OAuth user with hashed_password='' → 400, code=oauth_password_unsupported.

    Production OAuth-only users are stored with hashed_password="" (empty string)
    because the column has a NOT NULL constraint. FIX-1 changed the guard from
    `is None` to `not hashed_password` so both None and "" are caught correctly.
    This test exercises the actual production representation.
    """
    from app.core.security import create_access_token
    from app.models.user import User

    oauth_user = User(
        id=uuid.uuid4(),
        email=f"oauth-real-{uuid.uuid4().hex[:10]}@test.com",
        hashed_password="",  # real OAuth users: NOT NULL → empty string, not None
        auth_provider="microsoft",
        auth_provider_id="ms-test-id",
    )
    db_session.add(oauth_user)
    await db_session.commit()  # visible to the handler's own DB session

    token = create_access_token({"sub": str(oauth_user.id)})

    res = await client.post(
        _URL,
        json={"current_password": "Irrelevant1!", "new_password": _NEW_PASSWORD},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert detail["code"] == "oauth_password_unsupported"
    assert detail["auth_provider"] == "microsoft"


# ---------------------------------------------------------------------------
# T-05: new_password == current_password → 400 new_password_same_as_current
# ---------------------------------------------------------------------------


async def test_same_password_returns_400(auth_client: AsyncClient):
    """T-05: Sending the same value for current and new password → 400."""
    res = await auth_client.post(
        _URL,
        json={
            "current_password": _CURRENT_PASSWORD,
            "new_password": _CURRENT_PASSWORD,
        },
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "new_password_same_as_current"


# ---------------------------------------------------------------------------
# T-06: Happy path → 204; new password verifiable in DB
# ---------------------------------------------------------------------------


async def test_happy_path_returns_204_and_updates_password(client: AsyncClient, db_session):
    """T-06: Valid request → 204; subsequent verify_password(new, hash) is True."""
    from app.models.user import User

    email = _unique_email()
    old_pw = "OldSecure123!"
    new_pw = "NewSecure456!"

    reg = await client.post(
        "/api/auth/register",
        json={"email": email, "password": old_pw},
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    res = await client.post(
        _URL,
        json={"current_password": old_pw, "new_password": new_pw},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 204

    # Verify the new hash is persisted — DB committed by the handler
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    assert verify_password(new_pw, user.hashed_password), (
        "new_password should verify against the stored hash"
    )
    assert not verify_password(old_pw, user.hashed_password), "old_password must no longer verify"


# ---------------------------------------------------------------------------
# T-07: Active refresh tokens revoked after password change
# ---------------------------------------------------------------------------


async def test_refresh_tokens_revoked_after_change(client: AsyncClient, db_session):
    """T-07: User has 2 extra active refresh tokens; after change all are revoked."""
    from app.models.refresh_token import RefreshToken
    from app.models.user import User

    email = _unique_email()
    old_pw = "OldSecure123!"
    new_pw = "NewSecure456!"

    reg = await client.post(
        "/api/auth/register",
        json={"email": email, "password": old_pw},
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    # Fetch the user created by the registration
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalar_one()

    # Insert 2 extra active refresh tokens so we can assert they're all revoked
    now = datetime.now(UTC)
    for _ in range(2):
        rt = RefreshToken(
            id=uuid.uuid4(),
            jti=str(uuid.uuid4()),
            user_id=user.id,
            family_id=str(uuid.uuid4()),
            token_hash="b" * 64,
            expires_at=now + timedelta(days=30),
            revoked_at=None,
            created_at=now,
        )
        db_session.add(rt)
    await db_session.commit()  # must commit so the app's session sees these rows

    res = await client.post(
        _URL,
        json={"current_password": old_pw, "new_password": new_pw},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 204

    # No active refresh tokens must remain for this user
    active = await db_session.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    remaining = active.scalars().all()
    assert remaining == [], f"Expected 0 active refresh tokens, found {len(remaining)}"


# ---------------------------------------------------------------------------
# T-08: Audit event emitted with correct action, no password material
# ---------------------------------------------------------------------------


async def test_audit_event_emitted(client: AsyncClient):
    """T-08: AuditService.log_action is called once with action='auth.change_password'.

    The call args must NOT contain plaintext or hashed password material.
    """
    from app.api.deps import get_audit_service
    from app.main import app

    email = _unique_email()
    old_pw = "OldSecure123!"
    new_pw = "NewSecure456!"

    reg = await client.post(
        "/api/auth/register",
        json={"email": email, "password": old_pw},
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    mock_audit = AsyncMock()
    mock_audit.log_action = AsyncMock(return_value=None)

    app.dependency_overrides[get_audit_service] = lambda: mock_audit
    try:
        res = await client.post(
            _URL,
            json={"current_password": old_pw, "new_password": new_pw},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 204

        mock_audit.log_action.assert_called_once()
        call_kwargs = mock_audit.log_action.call_args.kwargs
        assert call_kwargs.get("action") == "auth.change_password", (
            f"Expected action='auth.change_password', got {call_kwargs.get('action')!r}"
        )
        assert "user_id" in call_kwargs

        # NFR-1: No password material in audit payload
        call_repr = str(mock_audit.log_action.call_args)
        assert old_pw not in call_repr, "Plaintext current_password leaked into audit call"
        assert new_pw not in call_repr, "Plaintext new_password leaked into audit call"
    finally:
        app.dependency_overrides.pop(get_audit_service, None)


# ---------------------------------------------------------------------------
# T-09: Rate limit exhausted → 429
# ---------------------------------------------------------------------------


async def test_rate_limit_returns_429(auth_client: AsyncClient):
    """T-09: When WRITE bucket is exhausted, the guard returns 429.

    Patches rate_limiter.check_rate_limit to simulate an already-exhausted bucket
    — same pattern as tests/unit/test_rate_limit_guard.py.
    """
    import time

    denied = {
        "allowed": False,
        "limit": 30,
        "remaining": 0,
        "reset_at": int(time.time()) + 60,
    }

    with patch(
        "app.core.rate_limiter.rate_limiter.check_rate_limit",
        new=AsyncMock(return_value=denied),
    ):
        res = await auth_client.post(
            _URL,
            json={"current_password": _CURRENT_PASSWORD, "new_password": _NEW_PASSWORD},
        )

    assert res.status_code == 429
