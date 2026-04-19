"""SQLAlchemy ORM models for Agente Derecho."""

from app.models.invoice import Invoice
from app.models.trial import Trial
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.document import Document, DocumentChunk
from app.models.api_key import APIKey
from app.models.notification import Notification
from app.models.tag import Tag, Folder, ConversationTag
from app.models.memory import UserMemory
from app.models.uploaded_document import UploadedDocument
from app.models.llm_key import UserLLMKey
from app.models.refresh_token import RefreshToken

__all__ = [
    "Invoice",
    "Trial",
    "User",
    "Conversation",
    "Message",
    "Document",
    "DocumentChunk",
    "APIKey",
    "Notification",
    "Tag",
    "Folder",
    "ConversationTag",
    "UserMemory",
    "UploadedDocument",
    "UserLLMKey",
    "RefreshToken",
]

# RBAC models — Batch 1
from app.rbac.models import AuditLog, Permission, Role, RolePermission, UserRole  # noqa: E402

__all__ += ["Role", "Permission", "RolePermission", "UserRole", "AuditLog"]
