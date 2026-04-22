"""UserLLMKey model — BYOK (Bring Your Own Key) for LLM providers.

Users provide their own API keys for LLM providers.
TukiJuris does NOT resell AI model usage — it charges only for platform access.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserLLMKey(Base):
    __tablename__ = "user_llm_keys"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_llm_keys_user_provider"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # openai, anthropic, google
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)  # encrypted with Fernet
    api_key_hint: Mapped[str] = mapped_column(String(20), nullable=False)  # "sk-...3kF2" last 4 chars
    label: Mapped[str | None] = mapped_column(String(200))  # user-friendly name
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
