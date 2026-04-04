"""JWT token creation, verification, password hashing, and login attempt tracking."""

import hashlib
import logging
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)


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


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """Decode and verify a JWT token. Returns payload or None."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


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
