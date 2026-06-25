"""PlatformLLMKey — provider keys owned by the TukiJuris operator.

These keys power the platform-provided free/pro tiers: when a user does
NOT have their own BYOK configured, the orchestrator falls back to the
platform key for the requested provider.

CRITICAL SECURITY RULE (mirrors `llm_adapter._get_platform_key` doc):
Platform keys live in their OWN table, separated from `user_llm_keys`.
Cross-tenant key reuse is forbidden — one user's provider account must
never pay for another user's traffic, and the platform's account must
never silently fall through to a user's key when the platform key is
missing.

Schema notes:
- `provider` is unique → one platform key per provider at a time. Replacing
  a key is an UPDATE on the existing row, not an INSERT.
- `api_key_encrypted` is Fernet-encrypted using BYOK_ENCRYPTION_KEY (same
  cipher as user keys).
- `api_key_hint` stores a non-sensitive tail (e.g. "sk-...3kF2") for UI
  display — never the full key.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PlatformLLMKey(Base):
    __tablename__ = "platform_llm_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    provider: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    api_key_hint: Mapped[str] = mapped_column(String(20), nullable=False)
    label: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Audit: who set this key (NULL allowed — initial seed migrations have no user)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
