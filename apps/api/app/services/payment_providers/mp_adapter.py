"""MercadoPago payment adapter — stored-card via Preapproval (Subscriptions) API.

Key architectural constraint:
  MP's /v1/payments endpoint always requires a FRESH card token for every
  charge request. There is no equivalent to Culqi's X-Charge-Channel: recurrent
  for server-side stored-card auto-charges. The only reliable server-side path
  is the Preapproval (Subscriptions) API:

  1. create_card: saves card to customer + creates a PAUSED preapproval using
     the fresh token (available at add-card time). Returns preapproval_id.
  2. charge_stored_card: activates the preapproval by setting status=authorized.
     MP triggers the first billing cycle immediately.

  Trial.provider_card_token stores preapproval_id for MP (not a card.id).

See: tukijuris/mp-stored-token-api engram observation for research findings.
"""

from __future__ import annotations

import logging

import httpx

from app.services.payment_providers.base import ChargeResult, ProviderError

logger = logging.getLogger(__name__)


class MPAdapter:
    """MercadoPago adapter for customer/card/preapproval charge lifecycle."""

    provider_name = "mp"
    BASE_URL = "https://api.mercadopago.com"

    def __init__(
        self,
        *,
        access_token: str,
        client: httpx.AsyncClient,
        timeout: float = 10.0,
    ) -> None:
        self._token = access_token
        self._client = client
        self._timeout = timeout

    # ── Private helpers ────────────────────────────────────────────────────

    def _headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        h: dict[str, str] = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            # MP requires X-Idempotency-Key for all payment operations
            h["X-Idempotency-Key"] = idempotency_key
        return h

    @staticmethod
    def _safe_json(r: httpx.Response) -> dict:
        try:
            return r.json()
        except Exception:
            return {}

    def _require_id(self, r: httpx.Response, field: str = "id") -> str:
        if r.status_code not in (200, 201):
            body = self._safe_json(r)
            raise ProviderError(
                code=body.get("error") or f"http_{r.status_code}",
                message=(
                    body.get("message")
                    or body.get("cause", [{}])[0].get("description", "")
                    or r.text[:500]
                ),
                status=r.status_code,
                raw=body,
            )
        data = r.json()
        if field not in data:
            raise ProviderError(
                code="missing_id",
                message=f"MP response missing '{field}' field: {r.text[:200]}",
                raw=data,
            )
        return str(data[field])

    # ── Protocol implementation ────────────────────────────────────────────

    async def create_customer(
        self,
        *,
        email: str,
        first_name: str,
        last_name: str,
        phone: str | None = None,
    ) -> str:
        """POST /v1/customers → returns customer.id."""
        payload: dict = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }
        if phone:
            # MP phone format: {area_code, number}. We store the full number
            # and split on the first 2 digits as area code (Peru: 51 prefix).
            digits = "".join(c for c in phone if c.isdigit())
            payload["phone"] = {
                "area_code": digits[:2] if len(digits) >= 6 else "51",
                "number": digits[2:] if len(digits) >= 6 else digits,
            }

        r = await self._client.post(
            f"{self.BASE_URL}/v1/customers",
            json=payload,
            headers=self._headers(),
            timeout=self._timeout,
        )
        customer_id = self._require_id(r)
        logger.debug("MP: created customer %s for %s", customer_id, email)
        return customer_id

    async def create_card(
        self,
        customer_id: str,
        token_id: str,
        metadata: dict | None = None,
    ) -> str:
        """Save card to customer + create PAUSED preapproval → returns preapproval_id.

        For MP, we cannot charge a stored card_id server-side later — MP always
        requires a fresh token at /v1/payments time. Instead, we:
        1. Save card to customer (permanent reference for bookkeeping).
        2. Create a preapproval (paused) using the fresh token now while it's valid.
        3. Return the preapproval_id as the stored "card token" for charge time.

        `metadata` should contain: email, amount_cents, plan_code, currency.
        """
        meta = metadata or {}
        email = meta.get("email", "")
        amount_cents = int(meta.get("amount_cents", 0))
        plan_code = meta.get("plan_code", "plan")
        currency = meta.get("currency", "PEN")

        # Step 1: Save card to customer (for bookkeeping / card last4 display)
        card_r = await self._client.post(
            f"{self.BASE_URL}/v1/customers/{customer_id}/cards",
            json={"token": token_id},
            headers=self._headers(),
            timeout=self._timeout,
        )
        if card_r.status_code not in (200, 201):
            body = self._safe_json(card_r)
            raise ProviderError(
                code=body.get("error") or f"http_{card_r.status_code}",
                message=body.get("message") or card_r.text[:500],
                status=card_r.status_code,
                raw=body,
            )
        logger.debug(
            "MP: saved card for customer %s", customer_id
        )

        # Step 2: Create PAUSED preapproval with the fresh token.
        # Amount is in currency units (not cents) for MP.
        amount_decimal = amount_cents / 100.0
        preapproval_payload = {
            "payer_email": email,
            "card_token_id": token_id,
            "reason": f"TukiJuris {plan_code} — auto-cargo post-trial",
            "auto_recurring": {
                "frequency": 1,
                "frequency_type": "months",
                "transaction_amount": amount_decimal,
                "currency_id": currency,
            },
            "back_url": "https://tukijuris.net.pe/billing",
            "status": "paused",
        }

        preapproval_r = await self._client.post(
            f"{self.BASE_URL}/preapproval",
            json=preapproval_payload,
            headers=self._headers(),
            timeout=self._timeout,
        )
        preapproval_id = self._require_id(preapproval_r)
        logger.debug(
            "MP: created paused preapproval %s for customer %s",
            preapproval_id,
            customer_id,
        )
        return preapproval_id

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
        """Activate the paused preapproval to trigger immediate billing.

        `card_id` here holds the preapproval_id stored at create_card time.
        MP triggers the first payment cycle when status transitions to 'authorized'.
        """
        payload = {"status": "authorized"}

        try:
            r = await self._client.put(
                f"{self.BASE_URL}/preapproval/{card_id}",
                json=payload,
                headers=self._headers(idempotency_key),
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            logger.warning("MP: network error during preapproval activation: %s", exc)
            return ChargeResult(
                success=False,
                error_code="network_error",
                error_message=str(exc),
            )

        if r.status_code in (200, 201):
            body = r.json()
            # MP preapproval activation doesn't return a payment id immediately;
            # the payment.created webhook arrives asynchronously.
            logger.info(
                "MP: preapproval %s activated for trial %s",
                card_id,
                metadata.get("trial_id"),
            )
            return ChargeResult(
                success=True,
                provider_charge_id=card_id,  # preapproval_id as reference
                raw_response=body,
            )

        body = self._safe_json(r)
        error_code = body.get("error") or f"http_{r.status_code}"
        error_message = body.get("message") or r.text[:500]
        logger.warning(
            "MP: preapproval activation failed [%s] %s for trial %s",
            error_code,
            error_message,
            metadata.get("trial_id"),
        )
        return ChargeResult(
            success=False,
            error_code=error_code,
            error_message=error_message,
            raw_response=body,
        )
