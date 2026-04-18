"""RBAC Pydantic v2 schemas — request/response models for RBAC endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class RoleResponse(BaseModel):
    """Public representation of a Role."""

    id: uuid.UUID
    name: str
    display_name: str
    description: str | None
    is_system: bool

    model_config = {"from_attributes": True}


class PermissionResponse(BaseModel):
    """Public representation of a Permission."""

    id: uuid.UUID
    resource: str
    action: str
    description: str | None

    model_config = {"from_attributes": True}


class UserRoleAssign(BaseModel):
    """Request body for assigning a role to a user."""

    role_id: uuid.UUID


class UserRoleResponse(BaseModel):
    """Public representation of a user ↔ role assignment."""

    role_id: uuid.UUID
    role_name: str
    assigned_at: datetime
    assigned_by: uuid.UUID | None
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class PermissionSetResponse(BaseModel):
    """The full set of permission strings for a user."""

    permissions: list[str]


class AuditLogEntry(BaseModel):
    """Single audit log record."""

    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    resource_type: str
    resource_id: str | None
    before_state: dict | None
    after_state: dict | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogPage(BaseModel):
    """Paginated list of audit log entries."""

    items: list[AuditLogEntry]
    total: int
    page: int
    page_size: int
