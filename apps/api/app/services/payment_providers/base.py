"""Payment provider base contract — Protocol, ChargeResult, ProviderError."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict


class ChargeResult(BaseModel):
    """Normalised result from any payment provider charge attempt."""

    success: bool
    provider_charge_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    raw_response: dict = {}

    model_config = ConfigDict(extra="allow")


class ProviderError(Exception):
    """Raised when a provider returns a non-retryable error (invalid card, etc.)."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status: int | None = None,
        raw: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.raw = raw or {}


@runtime_checkable
class PaymentProviderAdapter(Protocol):
    """Symmetric interface for Culqi and MercadoPago adapters.

    All methods are async. Implementations must NOT raise on charge failure —
    return `ChargeResult(success=False, ...)` instead. `ProviderError` is only
    raised for configuration errors (bad credentials, unknown customer, etc.)
    that make the entire operation impossible.
    """

    provider_name: str  # 'culqi' | 'mp'

    async def create_customer(
        self,
        *,
        email: str,
        first_name: str,
        last_name: str,
        phone: str | None = None,
    ) -> str:
        """Create a customer in the provider. Returns the provider customer ID."""
        ...

    async def create_card(
        self,
        customer_id: str,
        token_id: str,
        metadata: dict | None = None,
    ) -> str:
        """Persist a card token as a stored payment method.

        For Culqi: creates a Card resource; returns card.id (permanent).
        For MP: creates a Customer card + Preapproval (paused); returns
                preapproval_id — this is what we store in Trial.provider_card_token.

        `metadata` carries provider-specific context (e.g. MP needs amount/email
        for the preapproval body, since the token is short-lived and must be used
        at card-save time, not at charge time).
        """
        ...

    async def charge_stored_card(
        self,
        *,
        customer_id: str,
        card_id: str,
        amount_cents: int,
        currency: str,
        metadata: dict,
        idempotency_key: str,
    ) -> ChargeResult:
        """Charge a previously stored card / preapproval.

        For Culqi: POST /v2/charges with source_id=card_id +
                   X-Charge-Channel: recurrent header.
        For MP: PUT /preapproval/{card_id} with status=authorized to trigger
                the first billing cycle (card_id holds the preapproval_id).

        Returns ChargeResult — never raises on provider-level failure.
        """
        ...
