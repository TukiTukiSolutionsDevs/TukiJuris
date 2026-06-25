"""Platform LLM Key Service — operator-owned provider keys.

This service manages the keys that back the free/pro tiers. They are
distinct from user BYOK keys: see PlatformLLMKey docstring for the
security rationale.

API surface (mirrors llm_key_service for consistency):
    - get_platform_key(provider, db) -> str | None
    - list_platform_keys(db) -> list[PlatformLLMKey]   (no plaintext)
    - upsert_platform_key(provider, api_key, label, actor_id, db) -> PlatformLLMKey
    - delete_platform_key(provider, db) -> bool

Encryption mirrors the BYOK path: versioned Fernet via `llm_key_crypto`.
Legacy rows (pre-v1) are lazily migrated on read.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_llm_key import PlatformLLMKey
from app.services.llm_key_encryption import llm_key_crypto
from app.services.llm_key_service import make_hint

logger = logging.getLogger(__name__)


SUPPORTED_PROVIDERS = (
    "openai",
    "anthropic",
    "google",
    "deepseek",
    "groq",
    "xai",
    "openrouter",
)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


async def get_platform_key(provider: str, db: AsyncSession) -> str | None:
    """Return the decrypted platform key for a provider, or None.

    Lazily re-encrypts legacy (pre-v1) rows. Uses SELECT FOR UPDATE to
    prevent concurrent re-encryption of the same row.
    """
    result = await db.execute(
        select(PlatformLLMKey)
        .where(
            PlatformLLMKey.provider == provider,
            PlatformLLMKey.is_active == True,  # noqa: E712
        )
        .limit(1)
        .with_for_update()
    )
    row = result.scalar_one_or_none()
    if not row:
        return None
    try:
        plaintext, needs_reencrypt = llm_key_crypto.decrypt(row.api_key_encrypted)
    except Exception:
        logger.warning(
            "platform_llm_key.decrypt_failed: provider=%s — key may be corrupted",
            provider,
        )
        return None
    if needs_reencrypt:
        row.api_key_encrypted = llm_key_crypto.encrypt(plaintext)
        row.updated_at = datetime.now(UTC)
        await db.flush()
        logger.info(
            "platform_llm_key.lazy_migration: provider=%s — key migrated to v1",
            provider,
        )
    return plaintext


async def list_platform_keys(db: AsyncSession) -> list[PlatformLLMKey]:
    """Return all platform keys WITHOUT decrypted material — for admin listing."""
    result = await db.execute(
        select(PlatformLLMKey).order_by(PlatformLLMKey.provider.asc())
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------


async def upsert_platform_key(
    *,
    provider: str,
    api_key: str,
    label: str | None,
    actor_id: uuid.UUID,
    db: AsyncSession,
) -> PlatformLLMKey:
    """Insert or update the platform key for a provider.

    The unique constraint on `provider` means we either update an existing
    row in place (replacing the encrypted material and audit fields) or
    insert a new one. We do NOT keep history of prior keys — once replaced,
    the previous key cannot be recovered (this is intentional: rotated
    keys must be revoked at the provider side anyway).
    """
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    if not api_key or not api_key.strip():
        raise ValueError("api_key cannot be empty")

    encrypted = llm_key_crypto.encrypt(api_key.strip())
    hint = make_hint(api_key.strip())
    now = datetime.now(UTC)

    existing = await db.execute(
        select(PlatformLLMKey)
        .where(PlatformLLMKey.provider == provider)
        .with_for_update()
    )
    row = existing.scalar_one_or_none()

    if row is None:
        row = PlatformLLMKey(
            id=uuid.uuid4(),
            provider=provider,
            api_key_encrypted=encrypted,
            api_key_hint=hint,
            label=label,
            is_active=True,
            created_by=actor_id,
            updated_by=actor_id,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    else:
        row.api_key_encrypted = encrypted
        row.api_key_hint = hint
        row.label = label
        row.is_active = True
        row.updated_by = actor_id
        row.updated_at = now

    await db.flush()
    return row


async def delete_platform_key(provider: str, db: AsyncSession) -> bool:
    """Delete the platform key for a provider. Returns True if deleted, False if not found."""
    result = await db.execute(
        select(PlatformLLMKey)
        .where(PlatformLLMKey.provider == provider)
        .with_for_update()
    )
    row = result.scalar_one_or_none()
    if row is None:
        return False
    await db.delete(row)
    await db.flush()
    return True
