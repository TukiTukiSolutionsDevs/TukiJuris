"""Backfill User.is_admin from RBAC user_roles.

Aligns the materialized User.is_admin boolean with actual privileged-role membership.
Two drift cases are repaired:

  A) is_admin=FALSE but user has a privileged role  → set TRUE
  B) is_admin=TRUE  but user has no privileged role → set FALSE

Privileged roles: super_admin, admin, support, finance.

IMPORTANT: This migration does NOT revoke any refresh tokens.
Tokens are revoked at runtime by RBACService._sync_is_admin on role boundary changes
from this point forward. Mass-revocation here would force every user to log in at
deploy time and cause a login storm.

Revision ID: 009_backfill_is_admin_from_rbac
Revises: 008_org_seat_pricing
Create Date: 2026-04-18
"""

from alembic import op

revision: str = "009_backfill_is_admin_from_rbac"
down_revision: str = "008_org_seat_pricing"
branch_labels = None
depends_on = None

_PRIVILEGED = "('super_admin', 'admin', 'support', 'finance')"


def upgrade() -> None:
    # Drift A: is_admin=FALSE but user has a privileged role → set TRUE
    op.execute(
        f"""
        UPDATE users u SET is_admin = TRUE
        WHERE u.is_admin = FALSE
          AND EXISTS (
              SELECT 1
              FROM user_roles ur
              JOIN roles r ON ur.role_id = r.id
              WHERE ur.user_id = u.id
                AND r.name IN {_PRIVILEGED}
          );
        """
    )

    # Drift B: is_admin=TRUE but user has no privileged role → set FALSE
    op.execute(
        f"""
        UPDATE users u SET is_admin = FALSE
        WHERE u.is_admin = TRUE
          AND NOT EXISTS (
              SELECT 1
              FROM user_roles ur
              JOIN roles r ON ur.role_id = r.id
              WHERE ur.user_id = u.id
                AND r.name IN {_PRIVILEGED}
          );
        """
    )


def downgrade() -> None:
    # No-op: the pre-backfill is_admin values cannot be reconstructed without a snapshot.
    # Restore from a DB backup if you need the exact prior state.
    pass
