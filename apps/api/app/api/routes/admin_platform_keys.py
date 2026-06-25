"""Admin endpoints — Platform LLM provider keys (operator-managed).

These endpoints let the TukiJuris operator (super_admin / admin) configure
the API keys that back the free/pro tiers. They are NEVER exposed to
regular users.

Routes (mounted under /api/admin):
    GET    /admin/platform-keys           — list configured providers (no key material)
    POST   /admin/platform-keys           — upsert a provider key
    DELETE /admin/platform-keys/{prov}    — remove a provider key
    POST   /admin/platform-keys/{prov}/test — connectivity ping using stored key

Security:
    All routes require permission `platform_keys:write` (granted to
    super_admin and admin in migration 018). Permission failure → 403.
"""

from __future__ import annotations

import logging
from typing import Any

import litellm
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RateLimitBucket, RateLimitGuard, get_db
from app.models.user import User
from app.rbac.dependencies import require_permission
from app.services import platform_llm_key_service as svc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/platform-keys", tags=["admin", "platform-keys"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PlatformKeyOut(BaseModel):
    """Public view of a platform key — never includes plaintext."""
    provider: str
    label: str | None = None
    api_key_hint: str
    is_active: bool
    updated_at: str

    model_config = {"from_attributes": True}


class PlatformKeyUpsert(BaseModel):
    provider: str = Field(..., description="Lowercase provider id, e.g. 'openai', 'anthropic', 'google'")
    api_key: str = Field(..., min_length=4, description="Full provider API key (will be encrypted)")
    label: str | None = Field(None, max_length=200)


class PlatformKeyTestResult(BaseModel):
    provider: str
    ok: bool
    message: str


# ---------------------------------------------------------------------------
# GET — list
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[PlatformKeyOut])
async def list_platform_keys(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("platform_keys:write")),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> list[PlatformKeyOut]:
    """List configured platform keys. Plaintext is never returned."""
    rows = await svc.list_platform_keys(db)
    return [
        PlatformKeyOut(
            provider=r.provider,
            label=r.label,
            api_key_hint=r.api_key_hint,
            is_active=r.is_active,
            updated_at=r.updated_at.isoformat(),
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# POST — upsert
# ---------------------------------------------------------------------------

@router.post("/", response_model=PlatformKeyOut, status_code=status.HTTP_200_OK)
async def upsert_platform_key(
    body: PlatformKeyUpsert,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("platform_keys:write")),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> PlatformKeyOut:
    """Insert or update the platform key for a provider.

    The unique constraint on `provider` means there is at most one active
    key per provider. Posting again replaces the previous key in place.
    """
    if body.provider not in svc.SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider. Allowed: {sorted(svc.SUPPORTED_PROVIDERS)}",
        )
    try:
        row = await svc.upsert_platform_key(
            provider=body.provider,
            api_key=body.api_key,
            label=body.label,
            actor_id=user.id,
            db=db,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        await db.rollback()
        logger.exception("admin.platform_keys.upsert_failed: provider=%s", body.provider)
        raise HTTPException(status_code=500, detail="Failed to save platform key")

    logger.info(
        "admin.platform_keys.upserted: provider=%s actor=%s",
        body.provider,
        user.email,
    )
    return PlatformKeyOut(
        provider=row.provider,
        label=row.label,
        api_key_hint=row.api_key_hint,
        is_active=row.is_active,
        updated_at=row.updated_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# DELETE — remove
# ---------------------------------------------------------------------------

@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_platform_key(
    provider: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("platform_keys:write")),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> None:
    """Remove the platform key for a provider."""
    deleted = await svc.delete_platform_key(provider, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="No platform key for that provider")
    await db.commit()
    logger.info(
        "admin.platform_keys.deleted: provider=%s actor=%s", provider, user.email
    )


# ---------------------------------------------------------------------------
# POST — test
# ---------------------------------------------------------------------------

@router.post("/{provider}/test", response_model=PlatformKeyTestResult)
async def test_platform_key(
    provider: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("platform_keys:write")),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> PlatformKeyTestResult:
    """Ping the provider with the stored key using a 1-token completion.

    A simple smoke test that does not consume any meaningful quota.
    Returns `ok=true` if the provider accepts the key, `ok=false` with a
    short message otherwise.
    """
    if provider not in svc.SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    key = await svc.get_platform_key(provider, db)
    if not key:
        return PlatformKeyTestResult(
            provider=provider, ok=False, message="No key configured for this provider"
        )

    # Minimal probe per provider — 1 message, max_tokens=1.
    # Model selection mirrors the cheapest/fastest known model per provider so
    # the ping is essentially free.
    probe_models = {
        "openai": "openai/gpt-4o-mini",
        "anthropic": "anthropic/claude-haiku-4-5",
        "google": "gemini/gemini-2.5-flash",
        "deepseek": "deepseek/deepseek-chat",
        "groq": "groq/llama-3.1-8b-instant",
        "xai": "xai/grok-4-fast-non-reasoning",
        "openrouter": "openrouter/openai/gpt-4o-mini",
    }
    model = probe_models.get(provider)
    if not model:
        return PlatformKeyTestResult(
            provider=provider, ok=False, message="No probe model defined for this provider"
        )
    try:
        await litellm.acompletion(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
            api_key=key,
        )
        return PlatformKeyTestResult(provider=provider, ok=True, message="Connection OK")
    except Exception as e:  # noqa: BLE001
        return PlatformKeyTestResult(
            provider=provider, ok=False, message=str(e)[:200]
        )
