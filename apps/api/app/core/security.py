"""JWT token creation, verification, password hashing, and login attempt tracking."""

import hashlib
import logging
import uuid
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


def decode_access_token(token: str) -> dict | None:
    """Decode and verify a JWT token. Returns payload or None."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
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
