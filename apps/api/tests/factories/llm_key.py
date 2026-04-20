"""LLM key factory — creates UserLLMKey rows via the service encryption layer."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_key import UserLLMKey
from app.services.llm_key_service import encrypt_key, make_hint

_DUMMY_KEY = "sk-test-" + "0" * 40  # noqa: S105 — plaintext only in test factory


async def make_llm_key(
    db: AsyncSession,
    *,
    user_id: str,
    provider: str = "openai",
    api_key: str = _DUMMY_KEY,
    label: str | None = None,
    is_active: bool = True,
) -> UserLLMKey:
    """Insert an encrypted LLM key for a user.

    Uses the real encryption/hint helpers so the row matches production shape.
    Returns the flushed UserLLMKey — caller must commit the session.
    """
    key = UserLLMKey(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
        provider=provider,
        api_key_encrypted=encrypt_key(api_key),
        api_key_hint=make_hint(api_key),
        label=label or f"{provider} test key",
        is_active=is_active,
    )
    db.add(key)
    await db.flush()
    return key
