"""Indexes for billing hot paths + SUNAT invoice fields.

Revision ID: 020_indexes_and_sunat_prep
Revises: 019_reasoning_quota
Create Date: 2026-05-31

This migration is **additive and reversible** — it does not change column types
or drop data. It bundles three lightweight changes that the pre-prod audit flagged:

1. **Hot-path indexes** — `invoices.org_id`, `organizations.payment_subscription_id`,
   `organizations.payment_customer_id`. These columns are filtered constantly by the
   webhook handler and the invoice list endpoint; without the index the query falls
   back to seq-scan as the table grows.

2. **OrgMembership.role check constraint** — DB-level safety net so a buggy code
   path cannot persist an arbitrary role string. Mirrors the Pydantic validation
   already present on the invite endpoint.

3. **Invoice SUNAT fields** — `series`, `correlativo`, `tipo_documento`,
   `ruc_emisor`, `tipo_documento_cliente`, `numero_documento_cliente`. They are
   added as NULLABLE so existing rows remain valid; the invoice_service will
   populate them once the SUNAT PSE integration ships (F2-SUNAT).
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "020_indexes_and_sunat_prep"
down_revision = "019_reasoning_quota"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1) Hot-path indexes ─────────────────────────────────────────────────
    op.create_index(
        "ix_invoices_org_id",
        "invoices",
        ["org_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_organizations_payment_subscription_id",
        "organizations",
        ["payment_subscription_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_organizations_payment_customer_id",
        "organizations",
        ["payment_customer_id"],
        if_not_exists=True,
    )

    # ── 2) OrgMembership.role check constraint ──────────────────────────────
    # Drop any stray non-standard roles first so the constraint creation succeeds.
    op.execute(
        "UPDATE org_memberships SET role = 'member' "
        "WHERE role NOT IN ('owner', 'admin', 'member')"
    )
    op.create_check_constraint(
        "ck_org_memberships_role",
        "org_memberships",
        "role IN ('owner', 'admin', 'member')",
    )

    # ── 3) SUNAT invoice fields — additive, nullable ────────────────────────
    op.add_column("invoices", sa.Column("series", sa.String(length=4), nullable=True))
    op.add_column("invoices", sa.Column("correlativo", sa.Integer(), nullable=True))
    op.add_column(
        "invoices",
        sa.Column("tipo_documento", sa.String(length=2), nullable=True),
        # 01 = Factura, 03 = Boleta, 07 = Nota de crédito, 08 = Nota de débito
    )
    op.add_column("invoices", sa.Column("ruc_emisor", sa.String(length=11), nullable=True))
    op.add_column(
        "invoices",
        sa.Column("tipo_documento_cliente", sa.String(length=1), nullable=True),
        # 1 = DNI, 4 = Carnet de extranjería, 6 = RUC, 7 = Pasaporte
    )
    op.add_column(
        "invoices",
        sa.Column("numero_documento_cliente", sa.String(length=20), nullable=True),
    )

    # Combined uniqueness for series+correlativo. Nullable rows are excluded
    # by Postgres (NULL is distinct from NULL in unique indexes).
    op.create_index(
        "ux_invoices_series_correlativo",
        "invoices",
        ["series", "correlativo"],
        unique=True,
        postgresql_where=sa.text("series IS NOT NULL AND correlativo IS NOT NULL"),
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ux_invoices_series_correlativo", table_name="invoices", if_exists=True)
    op.drop_column("invoices", "numero_documento_cliente")
    op.drop_column("invoices", "tipo_documento_cliente")
    op.drop_column("invoices", "ruc_emisor")
    op.drop_column("invoices", "tipo_documento")
    op.drop_column("invoices", "correlativo")
    op.drop_column("invoices", "series")

    op.drop_constraint("ck_org_memberships_role", "org_memberships", type_="check")

    op.drop_index("ix_organizations_payment_customer_id", table_name="organizations", if_exists=True)
    op.drop_index("ix_organizations_payment_subscription_id", table_name="organizations", if_exists=True)
    op.drop_index("ix_invoices_org_id", table_name="invoices", if_exists=True)
