"""OAuth2 routes — Google and Microsoft SSO."""

import logging
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_refresh_service
from app.api.routes.auth import AccessTokenResponse, _set_session_cookies
from app.config import settings
from app.core.database import get_db
from app.core.security import (
    InvalidStateTokenError,
    create_oauth_state_jwt,
    validate_relative_path,
    verify_oauth_state_jwt,
)
from app.models.user import User
from app.services.refresh_token_service import RefreshTokenService

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/auth/oauth", tags=["oauth"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str


class TokenResponse(BaseModel):
    """Deprecated — use AccessTokenResponse from auth.py for new code.

    Kept for backward compatibility with existing tests that import it directly.
    The refresh token is now delivered via httpOnly cookie, not JSON body.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class OAuthCallbackResponse(BaseModel):
    """Response from the OAuth callback endpoint, including the post-auth destination."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900
    returnto: str


class OAuthProvider(BaseModel):
    id: str
    name: str
    enabled: bool


class ProvidersResponse(BaseModel):
    providers: list[OAuthProvider]


class AuthorizeResponse(BaseModel):
    url: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_google_auth_url(state: str) -> str:
    """Build the Google OAuth2 authorization URL."""
    params = {
        "client_id": settings.google_oauth_client_id,
        "redirect_uri": settings.google_oauth_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"


def _build_microsoft_auth_url(state: str) -> str:
    """Build the Microsoft OAuth2 authorization URL."""
    tenant = settings.microsoft_oauth_tenant_id
    params = {
        "client_id": settings.microsoft_oauth_client_id,
        "redirect_uri": settings.microsoft_oauth_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile User.Read",
        "response_mode": "query",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?{query}"


async def _exchange_google_code(code: str) -> dict:
    """Exchange Google authorization code for tokens + user profile."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "redirect_uri": settings.google_oauth_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange Google code")

        token_data = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access_token in Google response")

        profile_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch Google user info")

        return profile_res.json()


async def _exchange_microsoft_code(code: str) -> dict:
    """Exchange Microsoft authorization code for tokens + user profile."""
    tenant = settings.microsoft_oauth_tenant_id
    async with httpx.AsyncClient(timeout=10.0) as client:
        token_res = await client.post(
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
            data={
                "code": code,
                "client_id": settings.microsoft_oauth_client_id,
                "client_secret": settings.microsoft_oauth_client_secret,
                "redirect_uri": settings.microsoft_oauth_redirect_uri,
                "grant_type": "authorization_code",
                "scope": "openid email profile User.Read",
            },
        )
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange Microsoft code")

        token_data = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access_token in Microsoft response")

        profile_res = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch Microsoft user info")

        profile = profile_res.json()

        # Microsoft Graph returns mail or userPrincipalName for the email
        email = profile.get("mail") or profile.get("userPrincipalName") or ""
        return {
            "id": profile.get("id", ""),
            "email": email,
            "name": profile.get("displayName", ""),
            "picture": None,  # Graph /me does not return picture URL directly
        }


async def _upsert_sso_user(
    db: AsyncSession,
    provider: str,
    provider_id: str,
    email: str,
    full_name: str | None,
    avatar_url: str | None,
) -> User:
    """
    Find or create a user for an SSO login.

    Rules:
    - If a user with the same (provider, provider_id) exists, return it.
    - If a user with the same email exists (local or another provider), LINK
      it by updating auth_provider and auth_provider_id.
    - Otherwise, create a new user.
    """
    # 1. Try to find by provider + provider_id
    result = await db.execute(
        select(User).where(
            User.auth_provider == provider,
            User.auth_provider_id == provider_id,
        )
    )
    user = result.scalar_one_or_none()
    if user:
        # Update profile fields that may have changed
        if avatar_url:
            user.avatar_url = avatar_url
        if full_name and not user.full_name:
            user.full_name = full_name
        await db.flush()
        return user

    # 2. Try to find by email (account linking)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        # Link the existing account to this SSO provider
        user.auth_provider = provider
        user.auth_provider_id = provider_id
        if avatar_url:
            user.avatar_url = avatar_url
        if full_name and not user.full_name:
            user.full_name = full_name
        await db.flush()
        return user

    # 3. Create new user
    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password="",  # SSO users have no local password
        full_name=full_name,
        auth_provider=provider,
        auth_provider_id=provider_id,
        avatar_url=avatar_url,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


def _compute_effective_returnto(oauth_state_returnto: str | None, is_admin: bool) -> str:
    """Determine the effective post-login destination.

    Precedence:
      1. oauth_state.returnto if present AND passes validate_relative_path
      2. /admin  if user.is_admin
      3. /chat   default
    """
    if oauth_state_returnto and validate_relative_path(oauth_state_returnto):
        return oauth_state_returnto
    return "/admin" if is_admin else "/chat"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/providers", response_model=ProvidersResponse)
async def list_providers():
    """Return available OAuth providers and whether they are configured."""
    return ProvidersResponse(
        providers=[
            OAuthProvider(
                id="google",
                name="Google",
                enabled=bool(settings.google_oauth_client_id and settings.google_oauth_client_secret),
            ),
            OAuthProvider(
                id="microsoft",
                name="Microsoft",
                enabled=bool(
                    settings.microsoft_oauth_client_id and settings.microsoft_oauth_client_secret
                ),
            ),
        ]
    )


@router.get("/google/authorize", response_model=AuthorizeResponse)
async def google_authorize(
    returnto: str | None = Query(default=None, description="Relative path to return to after auth"),
) -> AuthorizeResponse:
    """Return the Google OAuth2 authorization URL with a signed state JWT."""
    if not settings.google_oauth_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")

    validated_returnto: str | None = None
    if returnto is not None:
        if validate_relative_path(returnto):
            validated_returnto = returnto
        else:
            logger.warning(
                "oauth.authorize: invalid returnto rejected",
                extra={"provider": "google", "length": len(returnto)},
            )

    state_token = create_oauth_state_jwt(returnto=validated_returnto)
    return AuthorizeResponse(url=_build_google_auth_url(state_token))


@router.post("/google/callback", response_model=OAuthCallbackResponse)
async def google_callback(
    body: OAuthCallbackRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    service: RefreshTokenService = Depends(get_refresh_service),
) -> OAuthCallbackResponse:
    """Exchange Google code for tokens; set refresh cookie; return effective returnto."""
    try:
        oauth_state = verify_oauth_state_jwt(body.state)
    except InvalidStateTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired OAuth state")

    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")

    profile = await _exchange_google_code(body.code)

    email: str = profile.get("email", "")
    if not email:
        raise HTTPException(status_code=400, detail="Could not retrieve email from Google")

    provider_id: str = str(profile.get("id", ""))
    full_name: str | None = profile.get("name") or profile.get("given_name")
    avatar_url: str | None = profile.get("picture")

    user = await _upsert_sso_user(
        db=db,
        provider="google",
        provider_id=provider_id,
        email=email,
        full_name=full_name,
        avatar_url=avatar_url,
    )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    device_info = {
        "user_agent": request.headers.get("user-agent", "unknown"),
        "ip_address": request.client.host if request.client else "unknown",
    }
    pair = await service.issue_pair(user, device_info)
    _set_session_cookies(response, pair.refresh_token)

    return OAuthCallbackResponse(
        access_token=pair.access_token,
        expires_in=pair.expires_in,
        returnto=_compute_effective_returnto(oauth_state.returnto, user.is_admin),
    )


@router.get("/microsoft/authorize", response_model=AuthorizeResponse)
async def microsoft_authorize(
    returnto: str | None = Query(default=None, description="Relative path to return to after auth"),
) -> AuthorizeResponse:
    """Return the Microsoft OAuth2 authorization URL with a signed state JWT."""
    if not settings.microsoft_oauth_client_id:
        raise HTTPException(status_code=503, detail="Microsoft OAuth is not configured")

    validated_returnto: str | None = None
    if returnto is not None:
        if validate_relative_path(returnto):
            validated_returnto = returnto
        else:
            logger.warning(
                "oauth.authorize: invalid returnto rejected",
                extra={"provider": "microsoft", "length": len(returnto)},
            )

    state_token = create_oauth_state_jwt(returnto=validated_returnto)
    return AuthorizeResponse(url=_build_microsoft_auth_url(state_token))


@router.post("/microsoft/callback", response_model=OAuthCallbackResponse)
async def microsoft_callback(
    body: OAuthCallbackRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    service: RefreshTokenService = Depends(get_refresh_service),
) -> OAuthCallbackResponse:
    """Exchange Microsoft code for tokens; set refresh cookie; return effective returnto."""
    try:
        oauth_state = verify_oauth_state_jwt(body.state)
    except InvalidStateTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired OAuth state")

    if not settings.microsoft_oauth_client_id or not settings.microsoft_oauth_client_secret:
        raise HTTPException(status_code=503, detail="Microsoft OAuth is not configured")

    profile = await _exchange_microsoft_code(body.code)

    email: str = profile.get("email", "")
    if not email:
        raise HTTPException(status_code=400, detail="Could not retrieve email from Microsoft")

    provider_id: str = str(profile.get("id", ""))
    full_name: str | None = profile.get("name")
    avatar_url: str | None = profile.get("picture")

    user = await _upsert_sso_user(
        db=db,
        provider="microsoft",
        provider_id=provider_id,
        email=email,
        full_name=full_name,
        avatar_url=avatar_url,
    )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    device_info = {
        "user_agent": request.headers.get("user-agent", "unknown"),
        "ip_address": request.client.host if request.client else "unknown",
    }
    pair = await service.issue_pair(user, device_info)
    _set_session_cookies(response, pair.refresh_token)

    return OAuthCallbackResponse(
        access_token=pair.access_token,
        expires_in=pair.expires_in,
        returnto=_compute_effective_returnto(oauth_state.returnto, user.is_admin),
    )
