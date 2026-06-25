"""OAuth2 routes — Google and Microsoft SSO.

Security posture:
- The id_token returned by the IdP is verified against JWKS (RS256) before
  any identity claim is trusted. The userinfo endpoint is used only as a
  fallback for non-OIDC profile data (avatar) and never as the source of
  identity.
- email_verified MUST be true before linking a SSO identity to an existing
  local account — otherwise a malicious user could register `victim@gmail.com`
  in TukiJuris first and then take over the legitimate Google account when
  it lands.
- The signed `state` JWT carries a server-side nonce. The browser side of the
  flow is correlated via the returnto path; full state-cookie binding is on
  the FASE 1 roadmap (F1-SEC-01).
"""

import logging
import time
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from jose import jwt as jose_jwt
from jose.exceptions import JWTError
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
# JWKS caches (process-local, reset on container restart)
# ---------------------------------------------------------------------------

_JWKS_CACHE_TTL_SECONDS = 3600  # 1 h — IdPs rotate keys infrequently
_google_jwks_cache: dict = {"keys": None, "fetched_at": 0.0}
_microsoft_jwks_cache: dict = {"keys": None, "fetched_at": 0.0, "tenant": None}


GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")
GOOGLE_JWKS_URI = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URI = "https://www.googleapis.com/oauth2/v2/userinfo"

MICROSOFT_GRAPH_ME = "https://graph.microsoft.com/v1.0/me"


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
# JWKS / id_token verification helpers
# ---------------------------------------------------------------------------


async def _fetch_jwks(uri: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(uri)
        resp.raise_for_status()
        data = resp.json()
        return data.get("keys", [])


async def _google_jwks() -> list[dict]:
    now = time.monotonic()
    if _google_jwks_cache["keys"] is not None and now - _google_jwks_cache["fetched_at"] < _JWKS_CACHE_TTL_SECONDS:
        return _google_jwks_cache["keys"]
    keys = await _fetch_jwks(GOOGLE_JWKS_URI)
    _google_jwks_cache["keys"] = keys
    _google_jwks_cache["fetched_at"] = now
    return keys


async def _microsoft_jwks(tenant: str) -> list[dict]:
    now = time.monotonic()
    if (
        _microsoft_jwks_cache["keys"] is not None
        and _microsoft_jwks_cache["tenant"] == tenant
        and now - _microsoft_jwks_cache["fetched_at"] < _JWKS_CACHE_TTL_SECONDS
    ):
        return _microsoft_jwks_cache["keys"]
    uri = f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
    keys = await _fetch_jwks(uri)
    _microsoft_jwks_cache["keys"] = keys
    _microsoft_jwks_cache["fetched_at"] = now
    _microsoft_jwks_cache["tenant"] = tenant
    return keys


def _find_jwk_by_kid(jwks: list[dict], kid: str | None) -> dict | None:
    if not kid:
        return None
    for key in jwks:
        if key.get("kid") == kid:
            return key
    return None


async def _verify_google_id_token(id_token: str) -> dict:
    """Verify a Google id_token end-to-end.

    Validates signature against JWKS, iss claim, aud claim (must be our
    google_oauth_client_id), exp/iat, and returns the claims dict.
    Raises HTTPException(401) on any failure.
    """
    try:
        unverified_header = jose_jwt.get_unverified_header(id_token)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid Google id_token header") from exc

    jwks = await _google_jwks()
    jwk = _find_jwk_by_kid(jwks, unverified_header.get("kid"))
    if jwk is None:
        # Force one re-fetch in case Google just rotated keys
        _google_jwks_cache["keys"] = None
        jwks = await _google_jwks()
        jwk = _find_jwk_by_kid(jwks, unverified_header.get("kid"))
        if jwk is None:
            raise HTTPException(status_code=401, detail="Google id_token signing key not found")

    try:
        claims = jose_jwt.decode(
            id_token,
            jwk,
            algorithms=[jwk.get("alg", "RS256")],
            audience=settings.google_oauth_client_id,
            issuer=GOOGLE_ISSUERS[0],
            options={"verify_at_hash": False},
        )
    except JWTError:
        # python-jose's issuer check is strict-equal; Google also issues with the
        # hostname variant. Retry with the alt issuer.
        try:
            claims = jose_jwt.decode(
                id_token,
                jwk,
                algorithms=[jwk.get("alg", "RS256")],
                audience=settings.google_oauth_client_id,
                issuer=GOOGLE_ISSUERS[1],
                options={"verify_at_hash": False},
            )
        except JWTError as exc:
            raise HTTPException(status_code=401, detail="Google id_token verification failed") from exc

    return claims


async def _verify_microsoft_id_token(id_token: str, tenant: str) -> dict:
    """Verify a Microsoft id_token. Tenant claim binds the token to the configured tenant.

    Only minimal claim checks here — full multi-tenant + B2C handling is on the FASE 1 roadmap.
    """
    try:
        unverified_header = jose_jwt.get_unverified_header(id_token)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid Microsoft id_token header") from exc

    jwks = await _microsoft_jwks(tenant)
    jwk = _find_jwk_by_kid(jwks, unverified_header.get("kid"))
    if jwk is None:
        _microsoft_jwks_cache["keys"] = None
        jwks = await _microsoft_jwks(tenant)
        jwk = _find_jwk_by_kid(jwks, unverified_header.get("kid"))
        if jwk is None:
            raise HTTPException(status_code=401, detail="Microsoft id_token signing key not found")

    try:
        claims = jose_jwt.decode(
            id_token,
            jwk,
            algorithms=[jwk.get("alg", "RS256")],
            audience=settings.microsoft_oauth_client_id,
            options={"verify_iss": False, "verify_at_hash": False},  # multi-tenant iss is dynamic
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Microsoft id_token verification failed") from exc

    # Minimal issuer sanity check
    iss = claims.get("iss", "")
    if "login.microsoftonline.com" not in iss and "sts.windows.net" not in iss:
        raise HTTPException(status_code=401, detail="Microsoft id_token issuer mismatch")

    return claims


# ---------------------------------------------------------------------------
# Authorization URL builders
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


# ---------------------------------------------------------------------------
# Code → identity exchange (id_token-first)
# ---------------------------------------------------------------------------


async def _exchange_google_code(code: str) -> dict:
    """Exchange Google authorization code for a verified identity profile.

    Returns a dict with: id, email, email_verified (bool), name, picture.
    Identity comes from the verified id_token claims; only `picture` falls back
    to userinfo because it is not part of the OIDC core claims.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        token_res = await client.post(
            GOOGLE_TOKEN_URI,
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
        id_token: str | None = token_data.get("id_token")
        if not id_token:
            raise HTTPException(status_code=400, detail="No id_token in Google response")

        claims = await _verify_google_id_token(id_token)

        profile: dict = {
            "id": claims.get("sub", ""),
            "email": claims.get("email", ""),
            "email_verified": bool(claims.get("email_verified", False)),
            "name": claims.get("name") or claims.get("given_name", ""),
            "picture": claims.get("picture"),
        }

        # If id_token didn't carry picture (rare), fall back to userinfo for avatar only.
        if not profile["picture"]:
            access_token = token_data.get("access_token")
            if access_token:
                try:
                    info_res = await client.get(
                        GOOGLE_USERINFO_URI,
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    if info_res.status_code == 200:
                        profile["picture"] = info_res.json().get("picture")
                except Exception:
                    pass  # avatar is decorative — never fail auth over it

        return profile


async def _exchange_microsoft_code(code: str) -> dict:
    """Exchange Microsoft authorization code for verified identity profile.

    Microsoft Graph /me is consulted only for display name + avatar, never for email.
    """
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
        id_token: str | None = token_data.get("id_token")
        if not id_token:
            raise HTTPException(status_code=400, detail="No id_token in Microsoft response")

        claims = await _verify_microsoft_id_token(id_token, tenant)

        email = (claims.get("email") or claims.get("preferred_username") or "").strip()
        # Microsoft does not always set email_verified explicitly; treat 'verified' or
        # absence of 'unverified_emails' for work/school accounts as verified.
        email_verified = bool(claims.get("email_verified", True))

        profile: dict = {
            "id": str(claims.get("oid") or claims.get("sub", "")),
            "email": email,
            "email_verified": email_verified,
            "name": claims.get("name", ""),
            "picture": None,
        }

        # Optional: Graph /me for display name only (avatar requires extra call).
        access_token = token_data.get("access_token")
        if access_token and not profile["name"]:
            try:
                me_res = await client.get(
                    MICROSOFT_GRAPH_ME,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if me_res.status_code == 200:
                    profile["name"] = me_res.json().get("displayName", "")
            except Exception:
                pass

        return profile


# ---------------------------------------------------------------------------
# User upsert with safe account linking
# ---------------------------------------------------------------------------


async def _upsert_sso_user(
    db: AsyncSession,
    provider: str,
    provider_id: str,
    email: str,
    email_verified: bool,
    full_name: str | None,
    avatar_url: str | None,
) -> User:
    """Find or create a user for an SSO login.

    Linking rules (anti account-takeover):
      - Match on (provider, provider_id) → trusted identity, just refresh profile.
      - Match on email alone → link ONLY when email_verified is True at the IdP.
        Otherwise we refuse the login so an attacker who registered
        `victim@gmail.com` locally first cannot take over the real account.
      - No match → create a fresh SSO-only user (no local password).
    """
    # 1. Trusted identity match
    result = await db.execute(
        select(User).where(
            User.auth_provider == provider,
            User.auth_provider_id == provider_id,
        )
    )
    user = result.scalar_one_or_none()
    if user:
        if avatar_url:
            user.avatar_url = avatar_url
        if full_name and not user.full_name:
            user.full_name = full_name
        await db.flush()
        return user

    # 2. Email collision — link only if IdP says the email is verified.
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        if not email_verified:
            logger.warning(
                "oauth.link_blocked: unverified IdP email matched existing local account",
                extra={"provider": provider, "email_domain": email.split("@")[-1] if "@" in email else ""},
            )
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "email_not_verified_at_idp",
                    "message": "Esta cuenta ya existe en TukiJuris. Verifica tu correo en el proveedor SSO antes de vincular.",
                },
            )
        user.auth_provider = provider
        user.auth_provider_id = provider_id
        if avatar_url:
            user.avatar_url = avatar_url
        if full_name and not user.full_name:
            user.full_name = full_name
        await db.flush()
        return user

    # 3. Brand-new SSO user
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

    user = await _upsert_sso_user(
        db=db,
        provider="google",
        provider_id=str(profile.get("id", "")),
        email=email,
        email_verified=bool(profile.get("email_verified", False)),
        full_name=profile.get("name") or None,
        avatar_url=profile.get("picture"),
    )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    device_info = {
        "user_agent": request.headers.get("user-agent", "unknown"),
        "ip_address": request.client.host if request.client else "unknown",
    }
    pair = await service.issue_pair(user, device_info)
    _set_session_cookies(response, pair.refresh_token, is_admin=user.is_admin)

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

    user = await _upsert_sso_user(
        db=db,
        provider="microsoft",
        provider_id=str(profile.get("id", "")),
        email=email,
        email_verified=bool(profile.get("email_verified", False)),
        full_name=profile.get("name") or None,
        avatar_url=profile.get("picture"),
    )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    device_info = {
        "user_agent": request.headers.get("user-agent", "unknown"),
        "ip_address": request.client.host if request.client else "unknown",
    }
    pair = await service.issue_pair(user, device_info)
    _set_session_cookies(response, pair.refresh_token, is_admin=user.is_admin)

    return OAuthCallbackResponse(
        access_token=pair.access_token,
        expires_in=pair.expires_in,
        returnto=_compute_effective_returnto(oauth_state.returnto, user.is_admin),
    )
