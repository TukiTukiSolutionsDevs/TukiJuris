"""User model — authentication and profile."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False, default="")
    full_name: Mapped[str | None] = mapped_column(String(255))

    # SSO / OAuth2 fields
    auth_provider: Mapped[str] = mapped_column(String(50), default="local")  # local, google, microsoft
    auth_provider_id: Mapped[str | None] = mapped_column(String(255))  # provider's user ID
    avatar_url: Mapped[str | None] = mapped_column(Text)  # profile picture URL
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    plan: Mapped[str] = mapped_column(String(50), default="free")  # free, pro, enterprise
    preferences: Mapped[dict | None] = mapped_column(JSONB, default=dict)  # user UX/feature settings
    default_org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    memberships = relationship(
        "OrgMembership",
        back_populates="user",
        foreign_keys="OrgMembership.user_id",
    )
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="user", cascade="all, delete-orphan")
    folders = relationship("Folder", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("UserMemory", back_populates="user", cascade="all, delete-orphan")


    # Trial relationship — cascade delete when user is deleted
    trials = relationship("Trial", back_populates="user", cascade="all, delete-orphan")

    # RBAC relationship (lazy="noload" to avoid N+1; load explicitly when needed)
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", foreign_keys="UserRole.user_id", lazy="noload"
    )
