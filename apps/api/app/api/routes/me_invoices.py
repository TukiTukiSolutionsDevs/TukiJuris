"""User-facing invoice routes.

Endpoints:
  GET /billing/{org_id}/invoices        — paginated list for the authenticated user
  GET /billing/{org_id}/invoices/{id}   — single invoice detail

Both endpoints require the caller to be a member of the target org.
The router is mounted under the /billing prefix in main.py, matching the
existing billing/{org_id}/... convention (usage, subscription, etc.).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_invoice_service
from app.core.database import get_db
from app.models.organization import OrgMembership
from app.models.user import User
from app.rbac.audit import AuditService
from app.schemas.invoice import InvoiceListResponse, InvoiceOut
from app.services.invoice_service import InvoiceService
from sqlalchemy import select

router = APIRouter(tags=["invoices"])


# ---------------------------------------------------------------------------
# Auth helper (mirrors _require_org_member in billing.py)
# ---------------------------------------------------------------------------


async def _require_org_member(
    org_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> None:
    result = await db.execute(
        select(OrgMembership).where(
            OrgMembership.organization_id == org_id,
            OrgMembership.user_id == current_user.id,
            OrgMembership.is_active == True,  # noqa: E712
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/{org_id}/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    org_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    invoice_status: str | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: InvoiceService = Depends(get_invoice_service),
) -> InvoiceListResponse:
    """Return paginated invoices for an organization (member-only)."""
    await _require_org_member(org_id, current_user, db)

    items, total = await svc.list_for_org(
        org_id=org_id,
        page=page,
        per_page=per_page,
        status=invoice_status,
    )
    return InvoiceListResponse(
        items=[InvoiceOut.model_validate(inv) for inv in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{org_id}/invoices/{invoice_id}", response_model=InvoiceOut)
async def get_invoice(
    org_id: uuid.UUID,
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: InvoiceService = Depends(get_invoice_service),
) -> InvoiceOut:
    """Return a single invoice by ID (member-only, org-scoped)."""
    await _require_org_member(org_id, current_user, db)

    invoice = await svc.get_for_org(invoice_id=invoice_id, org_id=org_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    return InvoiceOut.model_validate(invoice)
