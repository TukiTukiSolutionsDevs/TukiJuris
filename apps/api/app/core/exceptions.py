"""Domain-level auth exceptions.

Raised by the service layer; converted to HTTP 401 by the routes
(via JSONResponse) or a registered exception handler.
"""


class AuthError(Exception):
    """Base class for all authentication domain errors.

    Subclasses carry an ``error_code`` for structured logging and a
    ``detail_msg`` that is safe to expose publicly (no token-state leakage).
    """

    error_code: str = "auth_error"
    detail_msg: str = "Autenticación inválida"


class InvalidRefreshToken(AuthError):
    """Invalid signature, wrong type, or absent from DB."""

    error_code = "invalid_refresh_token"
    detail_msg = "Token inválido"


class ExpiredRefreshToken(AuthError):
    """Past its expiry window (JWT exp or DB expires_at)."""

    error_code = "expired_refresh_token"
    detail_msg = "Token expirado"


class RevokedRefreshToken(AuthError):
    """Explicitly revoked (single-device logout) — not a reuse attempt."""

    error_code = "revoked_refresh_token"
    detail_msg = "Token revocado"


class ReuseDetected(AuthError):
    """A previously-rotated token was reused — entire family killed."""

    error_code = "reuse_detected"
    detail_msg = "Sesión comprometida, reautenticar"
