"""RBAC Service — permission queries, role assignment/revocation.

Depends on:
  - PermissionCache      (apps/api/app/rbac/cache.py)
  - AuditService         (apps/api/app/rbac/audit.py) — optional
  - RefreshTokenService  (apps/api/app/services/refresh_token_service.py) — optional
  - SQLAlchemy models: Role, RolePermission, UserRole (apps/api/app/rbac/models.py)

Dual-write boundary
-------------------
User.is_admin is a materialized projection of privileged RBAC roles.
It MUST be set ONLY via _sync_is_admin inside this service.
Do NOT write User.is_admin directly anywhere outside RBACService.
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.rbac.cache import PermissionCache
from app.rbac.constants import PRIVILEGED_ROLE_NAMES, SystemRole
from app.rbac.models import Permission, Role, RolePermission, UserRole

if TYPE_CHECKING:
    from app.rbac.audit import AuditService
    from app.services.refresh_token_service import RefreshTokenService

logger = logging.getLogger(__name__)


class RBACService:
    """Core RBAC operations: permission resolution, role assignment."""

    def __init__(
        self,
        db: AsyncSession,
        cache: PermissionCache,
        audit: AuditService | None = None,
        refresh_tokens: RefreshTokenService | None = None,
    ) -> None:
        self._db = db
        self._cache = cache
        self._audit = audit
        self._refresh_tokens = refresh_tokens

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

        await self._sync_is_admin(user_id, actor_id=assigned_by, trigger_role_id=role_id)

        return user_role

    async def revoke_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        revoked_by: uuid.UUID | None = None,
    ) -> None:
        """Delete the UserRole record, invalidate cache, and emit an audit entry.

        Args:
            user_id: The user whose role is being revoked.
            role_id: The role to revoke.
            revoked_by: The acting admin's user ID. MUST be supplied by route handlers.
                If omitted, audit log records user_id=None (degrades observability).

        Raises:
            HTTPException 409 CANNOT_REVOKE_OWN_ADMIN: When the actor would remove
                their own last privileged role. Ask another admin to perform this.
        """
        # Self-revoke guard: block if this revocation would flip is_admin True→False
        # for the actor themselves.
        if revoked_by is not None and user_id == revoked_by:
            flip = await self._preview_admin_flip(user_id, role_id)
            if flip:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "CANNOT_REVOKE_OWN_ADMIN",
                        "message": "Cannot revoke your own admin role — ask another admin.",
                    },
                )

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
                user_id=revoked_by,
                action="role.revoke",
                resource_type="user_role",
                before_state=before_state,
            )

        await self._sync_is_admin(user_id, actor_id=revoked_by, trigger_role_id=role_id)

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

    # ------------------------------------------------------------------
    # Private: dual-write helpers
    # Admin status is maintained via dual-write from RBACService.
    # Do NOT set User.is_admin directly outside this service.
    # ------------------------------------------------------------------

    async def _preview_admin_flip(self, user_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        """Return True iff removing role_id would flip is_admin from True to False.

        Used by revoke_role to detect the self-revoke scenario before any mutation.
        """
        # Roles remaining after hypothetical removal
        stmt = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id, UserRole.role_id != role_id)
        )
        result = await self._db.execute(stmt)
        remaining = {name for (name,) in result.all()}
        would_be_admin = bool(remaining & PRIVILEGED_ROLE_NAMES)

        current_stmt = select(User.is_admin).where(User.id == user_id)
        current = (await self._db.execute(current_stmt)).scalar_one_or_none()
        return bool(current) and not would_be_admin

    async def _sync_is_admin(
        self,
        user_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        trigger_role_id: uuid.UUID,
    ) -> None:
        """Recompute is_admin from user_roles; if flipped, update users + revoke tokens + audit.

        This is a no-op when the boolean has not changed (D4 — prevents gratuitous
        revocations for multi-role admins receiving a second privileged role).
        """
        role_names_stmt = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        role_names = {n for (n,) in (await self._db.execute(role_names_stmt)).all()}
        should_be_admin = bool(role_names & PRIVILEGED_ROLE_NAMES)

        current_stmt = select(User.is_admin).where(User.id == user_id)
        current = (await self._db.execute(current_stmt)).scalar_one_or_none()
        if current is None or current == should_be_admin:
            return  # no-op — boolean unchanged

        await self._db.execute(
            update(User).where(User.id == user_id).values(is_admin=should_be_admin)
        )

        if self._refresh_tokens is not None:
            await self._refresh_tokens.revoke_all(user_id, reason="admin_role_change")
        else:
            logger.warning(
                "sync_is_admin: refresh_tokens not injected; tokens NOT revoked for user %s",
                user_id,
            )

        if self._audit is not None:
            await self._audit.log_action(
                user_id=actor_id,
                action="user.admin_status_changed",
                resource_type="user",
                resource_id=str(user_id),
                before_state={"is_admin": bool(current)},
                after_state={
                    "is_admin": should_be_admin,
                    "trigger_role_id": str(trigger_role_id),
                },
            )
