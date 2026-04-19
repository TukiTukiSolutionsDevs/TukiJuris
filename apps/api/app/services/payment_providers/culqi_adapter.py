"""Culqi v2 payment adapter — stored-card on-demand charges."""

from __future__ import annotations

import logging

import httpx

from app.services.payment_providers.base import ChargeResult, ProviderError

logger = logging.getLogger(__name__)


class CulqiAdapter:
    """Culqi v2 API adapter for customer/card/charge lifecycle.

    Key constraint: `X-Charge-Channel: recurrent` MUST be present on every
    stored-card charge (marks charge as recurring, suppresses 3DS, reduces
    fraud-engine friction). Without it, stored-card charges may be silently
    declined. See: tukijuris/culqi-stored-token-api engram observation.
    """

    provider_name = "culqi"
    BASE_URL = "https://api.culqi.com/v2"

    def __init__(
        self,
        *,
        secret_key: str,
        client: httpx.AsyncClient,
        timeout: float = 10.0,
    ) -> None:
        self._secret = secret_key
        self._client = client
        self._timeout = timeout

    # ── Private helpers ────────────────────────────────────────────────────

    def _headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        h: dict[str, str] = {
            "Authorization": f"Bearer {self._secret}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            h["X-Culqi-Idempotency-Key"] = idempotency_key
        return h

    @staticmethod
    def _safe_json(r: httpx.Response) -> dict:
        try:
            return r.json()
        except Exception:
            return {}

    def _require_id(self, r: httpx.Response) -> str:
        """Assert a 2xx response and extract the 'id' field."""
        if r.status_code not in (200, 201):
            body = self._safe_json(r)
            raise ProviderError(
                code=body.get("code") or f"http_{r.status_code}",
                message=(
                    body.get("merchant_message")
                    or body.get("user_message")
                    or r.text[:500]
                ),
                status=r.status_code,
                raw=body,
            )
        data = r.json()
        if "id" not in data:
            raise ProviderError(
                code="missing_id",
                message=f"Culqi response missing 'id' field: {r.text[:200]}",
                raw=data,
            )
        return data["id"]

    # ── Protocol implementation ────────────────────────────────────────────

    async def create_customer(
        self,
        *,
        email: str,
        first_name: str,
        last_name: str,
        phone: str | None = None,
    ) -> str:
        """POST /v2/customers → returns customer.id."""
        payload: dict = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }
        if phone:
            payload["phone_number"] = phone

        r = await self._client.post(
            f"{self.BASE_URL}/customers",
            json=payload,
            headers=self._headers(),
            timeout=self._timeout,
        )
        customer_id = self._require_id(r)
        logger.debug("Culqi: created customer %s for %s", customer_id, email)
        return customer_id

    async def create_card(
        self,
        customer_id: str,
        token_id: str,
        metadata: dict | None = None,
    ) -> str:
        """POST /v2/cards → returns card.id (permanent stored reference).

        The token_id here is a short-lived Culqi card token (tkn_xxx) from the
        frontend. The returned card.id (crd_xxx) is permanent and safe to store.
        """
        payload = {"customer_id": customer_id, "token_id": token_id}
        r = await self._client.post(
            f"{self.BASE_URL}/cards",
            json=payload,
            headers=self._headers(),
            timeout=self._timeout,
        )
        card_id = self._require_id(r)
        logger.debug("Culqi: saved card %s for customer %s", card_id, customer_id)
        return card_id

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
        """POST /v2/charges with X-Charge-Channel: recurrent.

        X-Charge-Channel: recurrent is MANDATORY — marks the charge as a
        recurring/card-on-file transaction. Without it, Culqi's fraud engine
        may block the charge with a 3DS challenge even for stored cards.
        """
        headers = {
            **self._headers(idempotency_key),
            "X-Charge-Channel": "recurrent",
        }
        payload = {
            "amount": amount_cents,
            "currency_code": currency,
            "email": metadata.get("email", "noreply@tukijuris.pe"),
            "source_id": card_id,
            "description": (
                f"TukiJuris {metadata.get('plan_code', 'plan')} — "
                "primer cargo post-trial"
            ),
            "metadata": {k: str(v) for k, v in metadata.items()},
        }

        try:
            r = await self._client.post(
                f"{self.BASE_URL}/charges",
                json=payload,
                headers=headers,
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            logger.warning("Culqi: network error during charge: %s", exc)
            return ChargeResult(
                success=False,
                error_code="network_error",
                error_message=str(exc),
            )

        if r.status_code in (200, 201):
            body = r.json()
            logger.info(
                "Culqi: charge success %s for trial %s",
                body.get("id"),
                metadata.get("trial_id"),
            )
            return ChargeResult(
                success=True,
                provider_charge_id=body.get("id"),
                raw_response=body,
            )

        body = self._safe_json(r)
        error_code = body.get("code") or f"http_{r.status_code}"
        error_message = (
            body.get("merchant_message")
            or body.get("user_message")
            or r.text[:500]
        )
        logger.warning(
            "Culqi: charge failed [%s] %s for trial %s",
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
