"""Pydantic schemas for the public plans catalog endpoint.

GET /api/plans — returns PlansListResponse with three PlanResponse entries.
No authentication required. All money fields are PEN Decimal(10,2).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field

PlanId = Literal["free", "pro", "studio"]


class PlanResponse(BaseModel):
    """Single plan entry in the public catalog.

    Money fields (base_price, seat_price, subtotal_amount, tax_amount,
    total_amount) are Decimal values quantized to 2 decimal places.
    Pydantic v2 serializes Decimal as JSON string by default (e.g. "70.00").
    """

    id: PlanId
    display_name: str
    currency: Literal["PEN"] = "PEN"

    # Input prices (per plan / per seat). Always non-negative.
    base_price: Decimal = Field(..., ge=0)
    seat_price: Decimal = Field(..., ge=0)
    base_seats_included: int = Field(..., ge=0)

    # Derived amounts from compute_invoice_amounts(plan, base_seats_included).
    # Calling with seats = base_seats_included means seat_amount = 0 and
    # subtotal = base_price on all three plans.
    subtotal_amount: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(..., ge=0)
    total_amount: Decimal = Field(..., ge=0)

    features: list[str] = Field(default_factory=list)
    limits: dict[str, Optional[int]] = Field(default_factory=dict)
    byok_supported: bool

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "pro",
                "display_name": "Profesional",
                "currency": "PEN",
                "base_price": "70.00",
                "seat_price": "0.00",
                "base_seats_included": 1,
                "subtotal_amount": "70.00",
                "tax_amount": "12.60",
                "total_amount": "82.60",
                "features": [
                    "Chat con IA legal",
                    "Exportar conversaciones a PDF",
                    "Subir archivos (PDF, DOCX)",
                    "Trae tu propia API key (BYOK)",
                    "Soporte prioritario",
                ],
                "limits": {"chat_per_day": None},
                "byok_supported": True,
            }
        }
    }


class PlansListResponse(BaseModel):
    """Root response for GET /api/plans."""

    plans: list[PlanResponse]
    beta_mode: bool
    currency_default: Literal["PEN"] = "PEN"

    model_config = {
        "json_schema_extra": {
            "example": {
                "plans": [],
                "beta_mode": True,
                "currency_default": "PEN",
            }
        }
    }
