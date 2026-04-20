"""Admin invoice routes.

Endpoints:
  GET   /admin/invoices           — paginated list (all orgs or filtered by org_id)
  GET   /admin/invoices/{id}      — single invoice detail
  PATCH /admin/invoices/{id}      — refund or void

Defense-in-depth: require_permission(billing:update) enforces RBAC AND
require_admin enforces User.is_admin=True. Both guards must pass.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RateLimitBucket, RateLimitGuard, get_audit_service, get_db, get_invoice_service, require_admin
from app.models.user import User
from app.rbac.audit import AuditService
from app.rbac.dependencies import require_permission
from app.schemas.invoice import InvoiceAdminPatchRequest, InvoiceListResponse, InvoiceOut
from app.services.invoice_service import InvoiceService, InvoiceStateError

router = APIRouter(prefix="/admin", tags=["admin-invoices"])


# ---------------------------------------------------------------------------
# GET /api/admin/invoices
# ---------------------------------------------------------------------------


@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices_admin(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    invoice_status: str | None = Query(default=None, alias="status"),
    org_id: uuid.UUID | None = Query(default=None),
    user: User = Depends(require_admin),
    _perm: User = Depends(require_permission("billing:read")),
    svc: InvoiceService = Depends(get_invoice_service),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> InvoiceListResponse:
    """Return all invoices (admin). Optionally filter by org_id or status."""

    items, total = await svc.list_for_admin(
        page=page,
        per_page=per_page,
        status=invoice_status,
        org_id=org_id,
    )
    return InvoiceListResponse(
        items=[InvoiceOut.model_validate(inv) for inv in items],
        total=total,
        page=page,
        per_page=per_page,
    )


# ---------------------------------------------------------------------------
# GET /api/admin/invoices/{invoice_id}
# ---------------------------------------------------------------------------


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
async def get_invoice_admin(
    invoice_id: uuid.UUID,
    user: User = Depends(require_admin),
    _perm: User = Depends(require_permission("billing:read")),
    svc: InvoiceService = Depends(get_invoice_service),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> InvoiceOut:
    """Return a single invoice by ID (no org scope — admin sees all)."""

    invoice = await svc.get_for_admin(invoice_id=invoice_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    return InvoiceOut.model_validate(invoice)


# ---------------------------------------------------------------------------
# PATCH /api/admin/invoices/{invoice_id}
# ---------------------------------------------------------------------------


@router.patch("/invoices/{invoice_id}", response_model=InvoiceOut)
async def patch_invoice_admin(
    invoice_id: uuid.UUID,
    body: InvoiceAdminPatchRequest,
    user: User = Depends(require_admin),
    _perm: User = Depends(require_permission("billing:update")),
    db: AsyncSession = Depends(get_db),
    svc: InvoiceService = Depends(get_invoice_service),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
) -> InvoiceOut:
    """Refund or void an invoice (admin only).

    Body: {"action": "refund"|"void", "reason": "<optional>"}
    """

    invoice = await svc.get_for_admin(invoice_id=invoice_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    try:
        if body.action == "refund":
            invoice = await svc.mark_refunded(
                invoice_id=invoice.id,
                reason=body.reason,
                actor_id=user.id,
            )
        else:  # body.action == "void"
            invoice = await svc.mark_voided(
                invoice_id=invoice.id,
                reason=body.reason,
                actor_id=user.id,
            )
        await db.commit()
    except InvoiceStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return InvoiceOut.model_validate(invoice)
