"""JWT token creation, verification, password hashing, and login attempt tracking."""

import hashlib
import logging
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.config import settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REFRESH_TOKEN_TTL_DAYS: int = 30
"""Default validity window for refresh tokens (days)."""

CLOCK_SKEW_SECONDS: int = 10
"""Grace period (seconds) to tolerate minor clock drift between services."""

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly (avoids passlib/bcrypt version conflicts)."""
    import bcrypt

    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    import bcrypt

    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Access token
# ---------------------------------------------------------------------------


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token.

    Injects ``type="access"`` and ``iat`` (issued-at) automatically so that
    the token can be type-checked at the dependency layer.
    """
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire, "iat": now.timestamp(), "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, audience: str | None = None) -> dict | None:
    """Decode and verify a JWT token. Returns payload or None.

    Args:
        token:    Signed JWT string.
        audience: Expected ``aud`` claim value. Required when the token was
                  issued with an ``aud`` claim (e.g. password-reset tokens) —
                  python-jose 3.x raises ``JWTError`` if ``aud`` is present
                  in the payload but no ``audience`` is supplied here.
    """
    try:
        kwargs: dict = {}
        if audience is not None:
            kwargs["audience"] = audience
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm], **kwargs)
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# Refresh token primitives
# ---------------------------------------------------------------------------


def hash_token(raw: str) -> str:
    """SHA-256 hash of a raw token string, hex-encoded (64 chars).

    Raw refresh tokens are NEVER stored — only their hash. This prevents
    token leakage via DB read access.
    """
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_refresh_claims(
    user_id: uuid.UUID,
    family_id: uuid.UUID,
    jti: uuid.UUID,
    issued_at: datetime,
    ttl_days: int = REFRESH_TOKEN_TTL_DAYS,
) -> dict:
    """Build JWT payload claims for a refresh token.

    Args:
        user_id:   Subject — the user this token belongs to.
        family_id: Token family for rotation theft-detection.
        jti:       Unique token identifier (JWT ID).
        issued_at: Token creation timestamp (must be UTC-aware).
        ttl_days:  Validity window in days.

    Returns:
        Claims dict with sub, jti, family_id, type, iat, exp.
    """
    iat = issued_at.timestamp()
    exp = (issued_at + timedelta(days=ttl_days)).timestamp()
    return {
        "sub": str(user_id),
        "jti": str(jti),
        "family_id": str(family_id),
        "type": "refresh",
        "iat": iat,
        "exp": exp,
    }


def verify_refresh_claims(payload: dict) -> bool:
    """Verify refresh token claims: structure, type marker, and expiry.

    Applies CLOCK_SKEW_SECONDS tolerance so tokens expired within the
    grace window are still accepted (handles minor distributed clock drift).

    Returns:
        True  — claims are structurally valid and not expired.
        False — missing fields, wrong type, or expired beyond skew window.
    """
    required = {"sub", "jti", "family_id", "type", "iat", "exp"}
    if not required.issubset(payload.keys()):
        return False
    if payload["type"] != "refresh":
        return False
    now = datetime.now(UTC).timestamp()
    if payload["exp"] + CLOCK_SKEW_SECONDS < now:
        return False
    return True


def compute_refresh_expires_at(
    issued_at: datetime,
    ttl_days: int = REFRESH_TOKEN_TTL_DAYS,
) -> datetime:
    """Compute the absolute expiry datetime for a refresh token.

    Args:
        issued_at: Token creation timestamp (must be timezone-aware).
        ttl_days:  Validity window in days.

    Returns:
        Timezone-aware datetime representing when the token expires.
    """
    return issued_at + timedelta(days=ttl_days)


# ---------------------------------------------------------------------------
# Login rate limiting
# ---------------------------------------------------------------------------


async def check_login_attempts(ip: str) -> bool:
    """Check if an IP has exceeded the login attempt limit.

    Uses the shared Redis rate limiter with a 15-minute sliding window.
    Each call to this function counts as one attempt — call it before
    verifying credentials so that even invalid-email attempts are counted.

    Returns:
        True  — request is allowed (under the limit or Redis is down).
        False — request must be blocked (limit exceeded).

    Resilience: if Redis is unavailable the function returns True (fail-open)
    to avoid locking users out during infrastructure outages.
    """
    try:
        from app.core.rate_limiter import rate_limiter

        result = await rate_limiter.check_rate_limit(
            f"login:{ip}",
            max_requests=settings.max_login_attempts,
            window_seconds=900,  # 15 minutes
        )
        return result["allowed"]
    except Exception as exc:
        logger.warning("Login rate limiter error (allowing request): %s", exc)
        return True


# ---------------------------------------------------------------------------
# OAuth state JWT
# ---------------------------------------------------------------------------

OAUTH_STATE_TYPE: str = "oauth_state"
"""Claim value that distinguishes state JWTs from access/refresh tokens."""

OAUTH_STATE_MAX_AGE_SECONDS: int = 600
"""State JWT validity window (10 minutes)."""

OAUTH_NONCE_BYTES: int = 24
"""Byte length for nonce; secrets.token_urlsafe(24) → 32-char URL-safe string."""


class InvalidStateTokenError(Exception):
    """Raised when an OAuth state JWT fails verification.

    Mapped to HTTP 401 by the route layer. Never includes token material in
    the message string — only developer-facing reason codes.
    """


@dataclass(frozen=True)
class OAuthState:
    """Decoded, verified OAuth state JWT payload."""

    nonce: str
    returnto: str | None
    iat: int
    exp: int


def create_oauth_state_jwt(*, returnto: str | None) -> str:
    """Build and sign an OAuth state JWT (HS256, ``settings.jwt_secret``).

    Args:
        returnto: Pre-validated relative path or None.
                  Callers MUST validate via ``validate_relative_path`` first;
                  this function stores the value verbatim.

    Returns:
        Signed JWT string.
    """
    now = datetime.now(UTC)
    iat = int(now.timestamp())
    exp = iat + OAUTH_STATE_MAX_AGE_SECONDS
    nonce = secrets.token_urlsafe(OAUTH_NONCE_BYTES)
    payload: dict = {
        "nonce": nonce,
        "returnto": returnto,
        "iat": iat,
        "exp": exp,
        "type": OAUTH_STATE_TYPE,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_oauth_state_jwt(token: str) -> OAuthState:
    """Decode and verify an OAuth state JWT.

    Raises:
        InvalidStateTokenError: on any of:
            - invalid or tampered signature
            - token expired (exp < now)
            - ``type`` claim missing or != ``OAUTH_STATE_TYPE``
            - ``iat`` claim is in the future
            - ``nonce`` claim is missing or empty
            - any other JWTError (malformed token, alg=none, etc.)

    Returns:
        :class:`OAuthState` with verified claims.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise InvalidStateTokenError("JWT decode failed") from exc

    # Type guard: prevents access/refresh token confusion attacks.
    if payload.get("type") != OAUTH_STATE_TYPE:
        raise InvalidStateTokenError("Invalid token type claim")

    # Nonce must be present and non-empty.
    nonce = payload.get("nonce")
    if not nonce:
        raise InvalidStateTokenError("Missing or empty nonce claim")

    # iat must not be in the future (prevents pre-generation / clock-skew abuse).
    iat = payload.get("iat", 0)
    now_ts = datetime.now(UTC).timestamp()
    if iat > now_ts:
        raise InvalidStateTokenError("Token issued in the future")

    exp = payload.get("exp", 0)

    return OAuthState(
        nonce=str(nonce),
        returnto=payload.get("returnto"),
        iat=int(iat),
        exp=int(exp),
    )


# Matches exactly one leading '/' (not '//') with no control characters.
# Uses \Z (not $) so a trailing \n does NOT count as end-of-string.
_RELATIVE_PATH_RE = re.compile(r"^/(?!/)[^\x00-\x1f]*\Z")
_RELATIVE_PATH_MAX_LENGTH: int = 2048


def validate_relative_path(
    path: str | None,
    *,
    max_length: int = _RELATIVE_PATH_MAX_LENGTH,
) -> bool:
    """Return ``True`` if *path* is a safe same-origin relative URL.

    Rules (ALL must hold):
    - Not ``None`` and not empty string.
    - ``len(path) <= max_length``.
    - Starts with exactly one ``/`` (rejects ``//`` protocol-relative URLs).
    - Contains no control characters (``\\x00``–``\\x1f``).
    - Contains no ``://`` substring (defence-in-depth: blocks
      ``/redirect?next=https://evil.com`` style open-redirect tricks).

    Returns ``False`` for any violation. Never raises.
    """
    if not path:
        return False
    if len(path) > max_length:
        return False
    if "://" in path:
        return False
    return bool(_RELATIVE_PATH_RE.match(path))
