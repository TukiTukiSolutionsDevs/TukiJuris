"""Document and DocumentChunk models — legal knowledge base."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Document(Base):
    """A legal document: law, decree, resolution, ruling, etc."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    document_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # ley, decreto_supremo, resolucion, sentencia, casacion, etc.
    document_number: Mapped[str | None] = mapped_column(String(200))  # Ley 26887, DS 003-97-TR
    legal_area: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # civil, penal, laboral, tributario, etc.
    hierarchy: Mapped[str | None] = mapped_column(
        String(50)
    )  # constitucional, legal, reglamentario
    source: Mapped[str] = mapped_column(String(200), nullable=False)  # spij, el_peruano, tc, etc.
    source_url: Mapped[str | None] = mapped_column(Text)
    publication_date: Mapped[datetime | None] = mapped_column(Date)
    modification_date: Mapped[datetime | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # Still in force?
    raw_text: Mapped[str | None] = mapped_column(Text)  # Full document text
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB)  # Additional structured metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """A chunk of a legal document, ready for RAG retrieval."""

    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    legal_area: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    article_number: Mapped[str | None] = mapped_column(String(50))
    section_path: Mapped[str | None] = mapped_column(
        Text
    )  # e.g. "Libro VII > Título IX > Cap I"
    token_count: Mapped[int | None] = mapped_column(Integer)
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB)

    # Vector embedding — stored via pgvector
    # The actual vector column is created in the migration with:
    #   Column("embedding", Vector(1536))
    # We keep it as raw SQL in alembic since SQLAlchemy pgvector
    # support needs the extension registered first.

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    document = relationship("Document", back_populates="chunks")
