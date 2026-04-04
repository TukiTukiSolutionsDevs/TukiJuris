"""Authentication routes — register, login, JWT."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import (
    check_login_attempts,
    create_access_token,
    hash_password,
    verify_password,
)
from app.core.validators import validate_password
from app.models.user import User
from app.services.email_service import email_service
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={
        422: {"description": "Validation error — invalid request body"},
    },
)


# --- Schemas ---


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    plan: str
    is_active: bool

    model_config = {"from_attributes": True}


class UpdateProfileBody(BaseModel):
    full_name: str | None = None
    default_org_id: uuid.UUID | None = None


# --- Routes ---


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
    description=(
        "Create a new user account with email and password. "
        "Password must be at least 8 characters and include uppercase, lowercase, and a digit. "
        "On success, returns a JWT access token valid for 60 minutes. "
        "A welcome email is sent asynchronously (non-blocking)."
    ),
    response_description="JWT access token for the newly created account",
    responses={
        201: {"description": "Account created — JWT returned"},
        409: {"description": "Email already registered"},
        422: {"description": "Password does not meet policy requirements"},
    },
)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Enforce password policy before touching the database
    is_valid, error = validate_password(body.password)
    if not is_valid:
        raise HTTPException(status_code=422, detail=error)

    # Check if email exists
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    await db.flush()

    # Fire-and-forget: send welcome email (never block the response)
    try:
        await email_service.send_welcome(
            to=user.email,
            name=user.full_name or user.email,
        )
    except Exception as exc:
        logger.warning("Welcome email failed for %s: %s", user.email, exc)

    # Fire-and-forget: in-app welcome notification
    try:
        await notification_service.welcome(
            user_id=user.id,
            name=user.full_name or user.email,
        )
    except Exception as exc:
        logger.warning("Welcome notification failed for %s: %s", user.id, exc)

    token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return TokenResponse(access_token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    description=(
        "Authenticate with email and password. Returns a JWT Bearer token on success. "
        "Include it in subsequent requests as `Authorization: Bearer <token>`. "
        "Login attempts are rate-limited per IP to prevent brute-force attacks — "
        "after too many failures the endpoint returns 429."
    ),
    response_description="JWT access token",
    responses={
        200: {"description": "Login successful — JWT returned"},
        401: {"description": "Invalid email or password"},
        403: {"description": "Account is disabled"},
        429: {"description": "Too many login attempts from this IP — try again later"},
    },
)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    client_ip = request.client.host if request.client else "unknown"

    # Block IPs that have exceeded the brute-force threshold.
    # If Redis is down, check_login_attempts returns True (fail-open).
    if not await check_login_attempts(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Try again later.",
        )

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    summary="Get current user profile",
    description="Returns the authenticated user's profile data.",
)
async def get_current_profile(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return the current user's profile."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "avatar_url": current_user.avatar_url,
        "plan": current_user.plan,
        "is_admin": current_user.is_admin,
        "auth_provider": current_user.auth_provider,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }


@router.put(
    "/me",
    summary="Update current user profile",
    description="Update mutable profile fields: full_name and default_org_id.",
)
async def update_profile(
    body: UpdateProfileBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update the current user's profile fields."""
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.default_org_id is not None:
        current_user.default_org_id = body.default_org_id
    await db.flush()
    return {"status": "updated"}
