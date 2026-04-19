"""Tests for refresh token security primitives — T-3.0 RED.

Verifies:
- hash_token: SHA-256, deterministic, 64-char hex.
- build_refresh_claims: required JWT claims for refresh tokens.
- verify_refresh_claims: structure + expiry + clock-skew tolerance.
- compute_refresh_expires_at: correct TTL math with timezone-aware datetime.
"""

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.security import (
    CLOCK_SKEW_SECONDS,
    REFRESH_TOKEN_TTL_DAYS,
    build_refresh_claims,
    compute_refresh_expires_at,
    hash_token,
    verify_refresh_claims,
)


# ---------------------------------------------------------------------------
# hash_token
# ---------------------------------------------------------------------------


class TestHashToken:
    """hash_token must produce a deterministic SHA-256 hex digest."""

    def test_returns_64_char_hex_string(self):
        result = hash_token("my-raw-token")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 = 32 bytes = 64 hex chars

    def test_deterministic(self):
        raw = "some-token-value"
        assert hash_token(raw) == hash_token(raw)

    def test_different_inputs_produce_different_hashes(self):
        assert hash_token("token-a") != hash_token("token-b")

    def test_empty_string_matches_known_sha256(self):
        expected = hashlib.sha256(b"").hexdigest()
        assert hash_token("") == expected

    def test_result_is_lowercase_hex(self):
        result = hash_token("test")
        assert result == result.lower()
        int(result, 16)  # raises ValueError if not valid hex


# ---------------------------------------------------------------------------
# build_refresh_claims
# ---------------------------------------------------------------------------


class TestBuildRefreshClaims:
    """build_refresh_claims must return a complete JWT claims dict."""

    def setup_method(self):
        self.user_id = uuid.uuid4()
        self.family_id = uuid.uuid4()
        self.jti = uuid.uuid4()
        self.issued_at = datetime.now(UTC)

    def _claims(self, **kwargs):
        return build_refresh_claims(
            user_id=kwargs.get("user_id", self.user_id),
            family_id=kwargs.get("family_id", self.family_id),
            jti=kwargs.get("jti", self.jti),
            issued_at=kwargs.get("issued_at", self.issued_at),
        )

    def test_returns_dict(self):
        assert isinstance(self._claims(), dict)

    def test_sub_is_str_user_id(self):
        assert self._claims()["sub"] == str(self.user_id)

    def test_jti_is_str_jti(self):
        assert self._claims()["jti"] == str(self.jti)

    def test_family_id_is_str_family_id(self):
        assert self._claims()["family_id"] == str(self.family_id)

    def test_type_is_refresh(self):
        assert self._claims().get("type") == "refresh"

    def test_iat_present_as_numeric(self):
        claims = self._claims()
        assert "iat" in claims
        assert isinstance(claims["iat"], (int, float))

    def test_exp_after_iat(self):
        claims = self._claims()
        assert "exp" in claims
        assert claims["exp"] > claims["iat"]

    def test_exp_uses_default_ttl(self):
        now = datetime.now(UTC)
        claims = build_refresh_claims(
            user_id=self.user_id,
            family_id=self.family_id,
            jti=self.jti,
            issued_at=now,
        )
        expected_exp = (now + timedelta(days=REFRESH_TOKEN_TTL_DAYS)).timestamp()
        assert abs(claims["exp"] - expected_exp) < 1  # 1-second tolerance


# ---------------------------------------------------------------------------
# verify_refresh_claims
# ---------------------------------------------------------------------------


class TestVerifyRefreshClaims:
    """verify_refresh_claims must validate structure, type, and expiry."""

    def _valid_claims(self) -> dict:
        now = datetime.now(UTC)
        return {
            "sub": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "family_id": str(uuid.uuid4()),
            "type": "refresh",
            "iat": now.timestamp(),
            "exp": (now + timedelta(days=30)).timestamp(),
        }

    def test_valid_claims_return_true(self):
        assert verify_refresh_claims(self._valid_claims()) is True

    def test_missing_sub_returns_false(self):
        claims = self._valid_claims()
        del claims["sub"]
        assert verify_refresh_claims(claims) is False

    def test_missing_jti_returns_false(self):
        claims = self._valid_claims()
        del claims["jti"]
        assert verify_refresh_claims(claims) is False

    def test_missing_family_id_returns_false(self):
        claims = self._valid_claims()
        del claims["family_id"]
        assert verify_refresh_claims(claims) is False

    def test_wrong_type_returns_false(self):
        claims = self._valid_claims()
        claims["type"] = "access"
        assert verify_refresh_claims(claims) is False

    def test_clearly_expired_returns_false(self):
        """Token expired 1 day ago — well beyond any clock skew window."""
        claims = self._valid_claims()
        claims["exp"] = (datetime.now(UTC) - timedelta(days=1)).timestamp()
        assert verify_refresh_claims(claims) is False

    def test_clock_skew_tolerance_within_window(self):
        """Token expired within CLOCK_SKEW_SECONDS must still be considered valid."""
        claims = self._valid_claims()
        half_skew = max(1, CLOCK_SKEW_SECONDS // 2)
        claims["exp"] = (datetime.now(UTC) - timedelta(seconds=half_skew)).timestamp()
        assert verify_refresh_claims(claims) is True

    def test_empty_payload_returns_false(self):
        assert verify_refresh_claims({}) is False


# ---------------------------------------------------------------------------
# compute_refresh_expires_at
# ---------------------------------------------------------------------------


class TestComputeRefreshExpiresAt:
    """compute_refresh_expires_at must return a tz-aware datetime in the future."""

    def test_returns_datetime_with_timezone(self):
        result = compute_refresh_expires_at(datetime.now(UTC))
        assert isinstance(result, datetime)
        assert result.tzinfo is not None

    def test_expires_in_future(self):
        now = datetime.now(UTC)
        assert compute_refresh_expires_at(now) > now

    def test_uses_refresh_token_ttl_days(self):
        now = datetime.now(UTC)
        result = compute_refresh_expires_at(now)
        expected = now + timedelta(days=REFRESH_TOKEN_TTL_DAYS)
        assert abs((result - expected).total_seconds()) < 1

    def test_custom_ttl_override(self):
        now = datetime.now(UTC)
        result = compute_refresh_expires_at(now, ttl_days=7)
        expected = now + timedelta(days=7)
        assert abs((result - expected).total_seconds()) < 1
