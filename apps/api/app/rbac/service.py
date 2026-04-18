"""RBAC Service — permission queries, role assignment/revocation.

Depends on:
  - PermissionCache  (apps/api/app/rbac/cache.py)
  - AuditService     (apps/api/app/rbac/audit.py) — optional
  - SQLAlchemy models: Role, RolePermission, UserRole (apps/api/app/rbac/models.py)
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.rbac.cache import PermissionCache
from app.rbac.constants import SystemRole
from app.rbac.models import Permission, Role, RolePermission, UserRole

if TYPE_CHECKING:
    from app.rbac.audit import AuditService

logger = logging.getLogger(__name__)


class RBACService:
    """Core RBAC operations: permission resolution, role assignment."""

    def __init__(
        self,
        db: AsyncSession,
        cache: PermissionCache,
        audit: AuditService | None = None,
    ) -> None:
        self._db = db
        self._cache = cache
        self._audit = audit

    # ------------------------------------------------------------------
    # Permission resolution
    # ------------------------------------------------------------------

    async def get_user_permissions(self, user_id: uuid.UUID) -> set[str]:
        """Return the full set of permission strings for a user.

        Flow:
          1. Cache hit → return immediately.
          2. Cache miss (or cache error) → query DB.
          3. Store result in cache.
          4. Return set of "resource:action" strings.
        """
        # 1. Try cache (fail-open — returns None on any error)
        try:
            cached = await self._cache.get_permissions(user_id)
            if cached is not None:
                return cached
        except Exception:
            logger.warning("cache.get_permissions raised for user %s — falling back to DB", user_id)

        # 2. Query DB: user_roles → roles → role_permissions → permissions
        stmt = (
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
            .options(
                selectinload(Role.role_permissions).selectinload(RolePermission.permission)
            )
        )
        result = await self._db.execute(stmt)
        roles = result.scalars().all()

        perms: set[str] = set()
        for role in roles:
            for rp in role.role_permissions:
                perms.add(f"{rp.permission.resource}:{rp.permission.action}")

        # 3. Store in cache (fail-open inside set_permissions)
        await self._cache.set_permissions(user_id, perms)

        return perms

    async def check_permission(self, user_id: uuid.UUID, *required: str) -> bool:
        """Return True if the user has ALL required permissions.

        super_admin bypasses the check (implicitly has every permission via
        the seed matrix which assigns all 19 permissions).
        No required permissions → always True.
        """
        if not required:
            return True

        perms = await self.get_user_permissions(user_id)
        return all(p in perms for p in required)

    # ------------------------------------------------------------------
    # Role management
    # ------------------------------------------------------------------

    async def assign_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        assigned_by: uuid.UUID | None,
    ) -> UserRole:
        """Create a UserRole record, invalidate cache, and emit an audit entry."""
        # Fetch role name for audit (skipped when audit is disabled)
        role_name: str | None = None
        if self._audit is not None:
            role_result = await self._db.execute(select(Role).where(Role.id == role_id))
            role = role_result.scalar_one_or_none()
            role_name = role.name if role else str(role_id)

        user_role = UserRole(user_id=user_id, role_id=role_id, assigned_by=assigned_by)
        self._db.add(user_role)
        await self._db.flush()
        await self._cache.invalidate(user_id)

        if self._audit is not None:
            await self._audit.log_action(
                user_id=assigned_by,
                action="role.assign",
                resource_type="user_role",
                after_state={
                    "user_id": str(user_id),
                    "role_id": str(role_id),
                    "role_name": role_name,
                    "assigned_by": str(assigned_by) if assigned_by else None,
                },
            )

        return user_role

    async def revoke_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        """Delete the UserRole record, invalidate cache, and emit an audit entry."""
        # Fetch role name for audit before_state (skipped when audit is disabled)
        before_state: dict | None = None
        if self._audit is not None:
            role_result = await self._db.execute(select(Role).where(Role.id == role_id))
            role = role_result.scalar_one_or_none()
            before_state = {
                "user_id": str(user_id),
                "role_id": str(role_id),
                "role_name": role.name if role else str(role_id),
            }

        stmt = delete(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
        )
        await self._db.execute(stmt)
        await self._cache.invalidate(user_id)

        if self._audit is not None:
            await self._audit.log_action(
                user_id=None,
                action="role.revoke",
                resource_type="user_role",
                before_state=before_state,
            )

    async def get_user_roles(self, user_id: uuid.UUID) -> list[Role]:
        """Return all Role objects currently assigned to the user."""
        stmt = select(Role).join(UserRole, UserRole.role_id == Role.id).where(
            UserRole.user_id == user_id
        )
        result = await self._db.execute(stmt)
        return result.scalars().all()

    async def get_all_roles(self) -> list[Role]:
        """Return all Role objects in the system."""
        result = await self._db.execute(select(Role))
        return result.scalars().all()

    async def get_role_by_id(self, role_id: uuid.UUID) -> Role | None:
        """Return a single Role by primary key, or None."""
        result = await self._db.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    async def get_role_permissions(self, role_id: uuid.UUID) -> list[Permission]:
        """Return all Permission objects assigned to the given role."""
        stmt = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        result = await self._db.execute(stmt)
        return result.scalars().all()
