"""Password reset routes — request and confirm via time-limited JWT."""

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import RateLimitBucket, RateLimitGuard
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, decode_access_token, hash_password
from app.core.validators import validate_password
from app.models.user import User
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_RESET_TOKEN_EXPIRE_MINUTES = 15
_RESET_TOKEN_AUDIENCE = "password-reset"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class MessageResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_reset_token(user_id: str, email: str) -> str:
    """Create a short-lived JWT intended only for password resets."""
    return create_access_token(
        data={"sub": user_id, "email": email, "aud": _RESET_TOKEN_AUDIENCE},
        expires_delta=timedelta(minutes=_RESET_TOKEN_EXPIRE_MINUTES),
    )


def _decode_reset_token(token: str) -> dict | None:
    """Decode and validate a password-reset JWT. Returns payload or None."""
    payload = decode_access_token(token)
    if not payload:
        return None
    if payload.get("aud") != _RESET_TOKEN_AUDIENCE:
        return None
    return payload


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/password-reset",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_password_reset(
    body: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """
    Request a password reset link.

    Always returns 202 regardless of whether the email exists —
    this prevents user enumeration attacks.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        token = _create_reset_token(str(user.id), user.email)
        reset_url = (
            f"{settings.frontend_url}/auth/reset-password?token={token}"
        )
        try:
            await email_service.send_password_reset(to=user.email, reset_url=reset_url)
        except Exception as exc:
            # Log but never expose internal errors to the caller
            logger.warning("Password reset email failed for %s: %s", user.email, exc)

    return MessageResponse(
        message="Si existe una cuenta con ese email, recibirás un enlace para restablecer tu contraseña."
    )


@router.post(
    "/password-reset/confirm",
    response_model=MessageResponse,
)
async def confirm_password_reset(
    body: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """
    Confirm a password reset using the token from the email link.

    The token is a 15-minute JWT with `aud: password-reset`.
    """
    payload = _decode_reset_token(body.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido o expirado",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no encontrado o inactivo",
        )

    is_valid, error = validate_password(body.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error,
        )

    user.hashed_password = hash_password(body.new_password)
    await db.flush()

    logger.info("Password reset completed for user %s", user_id)
    return MessageResponse(message="Contrasena restablecida correctamente")
