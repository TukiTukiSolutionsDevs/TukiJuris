"""API Key management routes — create, list, update, revoke developer keys.

Also manages LLM provider keys for BYOK (Bring Your Own Key).
Users supply their own keys for OpenAI, Anthropic, Google, DeepSeek, etc.
TukiJuris does NOT resell AI model usage — it charges only for platform access.
"""

import hashlib
import os
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.api_key import APIKey
from app.models.llm_key import UserLLMKey
from app.models.user import User

router = APIRouter(prefix="/keys", tags=["api-keys"])

# Valid scope values — enforced on create and update
VALID_SCOPES = {"query", "search", "analyze", "documents"}


# --- Helpers ---


def _generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.

    Returns:
        (full_key, prefix, sha256_hash)
        full_key  — ak_ + 40 random hex chars
        prefix    — first 8 chars of full_key ("ak_xxxxx" — 8 chars total)
        key_hash  — SHA-256 hex digest of full_key
    """
    raw = os.urandom(20).hex()  # 40 hex chars
    full_key = f"ak_{raw}"
    prefix = full_key[:8]
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, prefix, key_hash


def _validate_scopes(scopes: list[str]) -> None:
    invalid = set(scopes) - VALID_SCOPES
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid scopes: {sorted(invalid)}. Valid: {sorted(VALID_SCOPES)}",
        )


# --- Schemas ---


class APIKeyCreate(BaseModel):
    name: str
    scopes: list[str] = ["query", "search"]
    expires_in_days: int | None = None  # None = never expires


class APIKeyUpdate(BaseModel):
    name: str | None = None
    scopes: list[str] | None = None


class APIKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    scopes: list[str]
    is_active: bool
    last_used_at: datetime | None
    expires_at: datetime | None
    rate_limit_per_minute: int
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyCreated(APIKeyResponse):
    """Extends APIKeyResponse — includes full_key ONLY on creation."""

    full_key: str


# --- Routes ---


@router.post("/", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new API key.

    The full key is returned ONCE here. After this, only the key_prefix is
    accessible — the raw key is never stored.
    """
    _validate_scopes(body.scopes)

    # Deduplicate scopes, preserve order
    scopes = list(dict.fromkeys(body.scopes))

    full_key, prefix, key_hash = _generate_api_key()

    expires_at: datetime | None = None
    if body.expires_in_days is not None:
        expires_at = datetime.now(UTC) + timedelta(days=body.expires_in_days)

    api_key = APIKey(
        user_id=current_user.id,
        name=body.name,
        key_prefix=prefix,
        key_hash=key_hash,
        scopes=scopes,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.flush()

    return APIKeyCreated(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        created_at=api_key.created_at,
        full_key=full_key,
    )


@router.get("/", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys for the current user (active and revoked)."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [APIKeyResponse.model_validate(k) for k in keys]


@router.put("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: uuid.UUID,
    body: APIKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the name and/or scopes of an API key."""
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    if body.name is not None:
        api_key.name = body.name

    if body.scopes is not None:
        _validate_scopes(body.scopes)
        api_key.scopes = list(dict.fromkeys(body.scopes))

    api_key.updated_at = datetime.now(UTC)
    await db.flush()

    return APIKeyResponse.model_validate(api_key)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke (soft-delete) an API key by setting is_active=False."""
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    api_key.is_active = False
    api_key.updated_at = datetime.now(UTC)
    await db.flush()


# ===========================================================================
# LLM Provider Keys (BYOK — Bring Your Own Key)
# ===========================================================================
# These endpoints manage the user's OWN keys for external LLM providers.
# TukiJuris does NOT proxy or resell AI model calls — users pay their
# providers directly. This is separate from the developer API keys above.
# ===========================================================================


class AddLLMKeyBody(BaseModel):
    provider: str  # openai, anthropic, google, deepseek
    api_key: str
    label: str | None = None


@router.get("/llm-keys", summary="List LLM provider keys")
async def list_llm_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """
    List the user's configured LLM provider keys.

    Returns hints only — the full key is NEVER returned after creation.
    """
    result = await db.execute(
        select(UserLLMKey)
        .where(UserLLMKey.user_id == current_user.id)
        .order_by(UserLLMKey.created_at)
    )
    keys = result.scalars().all()
    return [
        {
            "id": str(k.id),
            "provider": k.provider,
            "hint": k.api_key_hint,
            "label": k.label,
            "is_active": k.is_active,
            "created_at": k.created_at.isoformat(),
        }
        for k in keys
    ]


@router.post("/llm-keys", status_code=status.HTTP_201_CREATED, summary="Add LLM provider key")
async def add_llm_key(
    body: AddLLMKeyBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Store an LLM provider API key encrypted at rest.

    The full key is never returned after this call — only the hint is stored.
    Supported providers: openai, anthropic, google, deepseek.
    """
    from app.services.llm_key_service import encrypt_key, make_hint

    if not body.api_key or not body.api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="api_key no puede estar vacío",
        )

    key = UserLLMKey(
        user_id=current_user.id,
        provider=body.provider.lower().strip(),
        api_key_encrypted=encrypt_key(body.api_key.strip()),
        api_key_hint=make_hint(body.api_key.strip()),
        label=body.label,
    )
    db.add(key)
    await db.flush()
    return {
        "id": str(key.id),
        "provider": key.provider,
        "hint": key.api_key_hint,
        "label": key.label,
    }


@router.delete("/llm-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete LLM provider key")
async def delete_llm_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an LLM provider key. Only the owner can delete their own keys."""
    try:
        key_uuid = uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="key_id inválido")

    key = await db.scalar(
        select(UserLLMKey).where(
            UserLLMKey.id == key_uuid,
            UserLLMKey.user_id == current_user.id,
        )
    )
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key no encontrada")

    await db.delete(key)


@router.get("/llm-providers", summary="List supported LLM providers")
async def list_llm_providers() -> list[dict]:
    """
    List LLM providers supported for BYOK, with their available models and docs URLs.

    Use this to populate the UI's provider selector and guide users to generate their keys.
    """
    from app.services.llm_key_service import get_available_providers

    return get_available_providers()


@router.get("/free-models", summary="List platform-provided free tier models")
async def list_free_models() -> dict:
    """
    Return models available for free tier users (no BYOK key required).

    These models are provided by the platform at zero cost.
    Used by the frontend to populate the model selector for free plan users.
    """
    from app.services.llm_adapter import llm_service
    from app.services.usage import PLAN_LIMITS

    models = llm_service.get_free_tier_models()
    limits = PLAN_LIMITS.get("free", {})
    return {
        "models": models,
        "daily_limit": limits.get("queries_day", 10),
        "enabled": settings.free_tier_enabled,
    }


class TestKeyBody(BaseModel):
    provider: str


@router.post("/llm-keys/test", summary="Test LLM provider key connectivity")
async def test_llm_key(
    body: TestKeyBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Test connectivity for the user's configured API key of a given provider.

    Sends a minimal completion request (1 token) to verify the key works.
    Returns ``{"ok": true, "latency_ms": N}`` on success or
    ``{"ok": false, "error": "..."}`` on failure.

    Use this to show a green/red dot next to each provider in the settings UI.
    """
    import time

    from app.services.llm_key_service import get_user_key_for_provider

    # Resolve the user's key for this provider
    api_key = await get_user_key_for_provider(current_user.id, body.provider, db)
    if not api_key:
        return {"ok": False, "error": "No tenés una API key configurada para este proveedor."}

    # Pick a minimal model for each provider to test connectivity cheaply
    _test_models: dict[str, str] = {
        "google": "gemini/gemini-2.5-flash",
        "groq": "groq/llama-3.1-8b-instant",
        "deepseek": "deepseek/deepseek-chat",
        "openai": "openai/gpt-5.4-nano",
        "anthropic": "anthropic/claude-haiku-4-5",
        "xai": "xai/grok-3-mini-fast-latest",
    }
    test_model = _test_models.get(body.provider)
    if not test_model:
        return {"ok": False, "error": f"Proveedor '{body.provider}' no soportado para test."}

    import litellm

    start = time.time()
    try:
        response = await litellm.acompletion(
            model=test_model,
            messages=[{"role": "user", "content": "Responde solo 'OK'."}],
            max_tokens=5,
            temperature=0.0,
            api_key=api_key,
        )
        latency_ms = int((time.time() - start) * 1000)
        content = response.choices[0].message.content or ""
        return {"ok": True, "latency_ms": latency_ms, "response": content[:50]}
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        error_msg = str(e)
        # Trim long error messages
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        return {"ok": False, "error": error_msg, "latency_ms": latency_ms}
