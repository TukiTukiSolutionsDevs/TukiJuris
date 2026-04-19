"""Payment service — MercadoPago + Culqi dual-provider support."""

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Plan definitions — single source of truth for pricing
# ---------------------------------------------------------------------------

PLAN_PRICING = {
    "pro": {
        "name": "Plan Profesional",
        "price": 70.00,        # S/70 per month
        "price_cents": 7000,   # Culqi uses cents
        "currency": "PEN",
        "daily_limit": -1,     # unlimited
        "interval": "months",
        "interval_count": 1,
    },
    "studio": {
        "name": "Plan Estudio",
        "price": 299.00,       # S/299 per month base (+ seat overage)
        "price_cents": 29900,  # Culqi uses cents
        "currency": "PEN",
        "daily_limit": -1,     # unlimited
        "interval": "months",
        "interval_count": 1,
    },
}


# ---------------------------------------------------------------------------
# Abstract provider
# ---------------------------------------------------------------------------

class PaymentProvider(ABC):
    """Interface for payment providers."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    async def create_checkout(
        self,
        plan: str,
        org_id: str,
        payer_email: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        """Create checkout and return redirect URL."""
        ...

    @abstractmethod
    async def verify_webhook(self, payload: bytes, headers: dict) -> dict | None:
        """Verify webhook signature and return parsed event data, or None if invalid."""
        ...

    @abstractmethod
    async def cancel_subscription(self, subscription_id: str) -> dict:
        """Cancel a subscription."""
        ...


# ---------------------------------------------------------------------------
# MercadoPago provider
# ---------------------------------------------------------------------------

class MercadoPagoProvider(PaymentProvider):
    """MercadoPago integration for Peru (PEN)."""

    @property
    def name(self) -> str:
        return "mercadopago"

    @property
    def is_available(self) -> bool:
        return bool(settings.mp_access_token)

    async def create_checkout(
        self,
        plan: str,
        org_id: str,
        payer_email: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        import mercadopago
        sdk = mercadopago.SDK(settings.mp_access_token)

        plan_info = PLAN_PRICING.get(plan)
        if not plan_info or not plan_info["price"]:
            raise ValueError(f"Plan '{plan}' is not available for checkout")

        preference_data = {
            "items": [{
                "title": plan_info["name"],
                "description": f"Suscripción mensual - TukiJuris {plan_info['name']}",
                "quantity": 1,
                "unit_price": plan_info["price"],
                "currency_id": plan_info["currency"],
            }],
            "payer": {"email": payer_email},
            "back_urls": {
                "success": success_url,
                "failure": cancel_url,
                "pending": cancel_url,
            },
            "auto_return": "approved",
            "metadata": {"org_id": org_id, "plan": plan, "provider": "mercadopago"},
            "notification_url": f"{settings.app_base_url}/api/billing/webhook/mp",
            "statement_descriptor": "TUKIJURIS",
        }

        result = sdk.preference().create(preference_data)
        response = result.get("response", {})
        checkout_url = response.get("init_point", "")

        if not checkout_url:
            logger.error("MercadoPago create_checkout failed: %s", result)
            raise RuntimeError("Failed to create MercadoPago checkout session")

        logger.info("mp.create_checkout: org=%s plan=%s", org_id, plan)
        return checkout_url

    async def verify_webhook(self, payload: bytes, headers: dict) -> dict | None:
        """
        Verify MercadoPago webhook signature (HMAC-SHA256).

        MP sends x-signature header with format: "ts=<ts>,v1=<hash>"
        The hash is HMAC-SHA256 of: "id:<data_id>;request-id:<x-request-id>;ts:<ts>;"
        signed with the webhook secret (mp_webhook_secret).

        If no webhook secret is configured, falls back to parse-only (dev mode).
        """
        import json
        import hashlib
        import hmac

        try:
            data = json.loads(payload)
        except Exception as exc:
            logger.warning("MP webhook parse error: %s", exc)
            return None

        # If webhook secret is configured, verify HMAC signature
        webhook_secret = settings.mp_webhook_secret
        if webhook_secret:
            x_signature = headers.get("x-signature", "")
            x_request_id = headers.get("x-request-id", "")

            if not x_signature:
                logger.warning("MP webhook: missing x-signature header")
                return None

            # Parse ts and v1 from x-signature
            parts = {}
            for part in x_signature.split(","):
                key_val = part.strip().split("=", 1)
                if len(key_val) == 2:
                    parts[key_val[0]] = key_val[1]

            ts = parts.get("ts", "")
            received_hash = parts.get("v1", "")

            if not ts or not received_hash:
                logger.warning("MP webhook: malformed x-signature: %s", x_signature)
                return None

            # Build the signed message
            data_id = data.get("data", {}).get("id", data.get("id", ""))
            manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"

            # Compute expected HMAC-SHA256
            expected_hash = hmac.new(
                webhook_secret.encode("utf-8"),
                manifest.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            if not hmac.compare_digest(expected_hash, received_hash):
                logger.warning("MP webhook: HMAC mismatch — rejecting")
                return None

            logger.debug("MP webhook: HMAC verified OK")
        else:
            logger.warning("MP webhook: no mp_webhook_secret configured — skipping signature verification (DEV MODE)")

        return {
            "type": data.get("type", data.get("topic", "")),
            "data_id": data.get("data", {}).get("id", data.get("id", "")),
            "raw": data,
        }

    async def cancel_subscription(self, subscription_id: str) -> dict:
        import mercadopago
        sdk = mercadopago.SDK(settings.mp_access_token)
        result = sdk.preapproval().update(subscription_id, {"status": "cancelled"})
        logger.info("mp.cancel_subscription: %s", subscription_id)
        return {"status": "cancelled", "provider": "mercadopago"}


# ---------------------------------------------------------------------------
# Culqi provider
# ---------------------------------------------------------------------------

class CulqiProvider(PaymentProvider):
    """Culqi integration for Peru (PEN)."""

    @property
    def name(self) -> str:
        return "culqi"

    @property
    def is_available(self) -> bool:
        return bool(settings.culqi_secret_key)

    async def create_checkout(
        self,
        plan: str,
        org_id: str,
        payer_email: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        """
        Culqi Checkout v4 — generates a checkout URL.
        The frontend will use Culqi.js or redirect to Culqi's hosted checkout.

        For now, returns a special URL that the frontend handles by opening
        the Culqi modal with the encrypted order.
        """
        import time
        import httpx

        plan_info = PLAN_PRICING.get(plan)
        if not plan_info or not plan_info["price"]:
            raise ValueError(f"Plan '{plan}' is not available for checkout")

        # Create an order via Culqi API
        order_data = {
            "amount": plan_info["price_cents"],
            "currency_code": plan_info["currency"],
            "description": f"Suscripción {plan_info['name']} - TukiJuris",
            "order_number": f"ORD-{org_id[:8]}-{int(time.time())}",
            "metadata": {"org_id": org_id, "plan": plan, "provider": "culqi"},
            "client_details": {"email": payer_email},
            "confirm": False,
            "expiration_date": int(time.time()) + 3600,  # 1 hour
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                "https://api.culqi.com/v2/orders",
                json=order_data,
                headers={
                    "Authorization": f"Bearer {settings.culqi_secret_key}",
                    "Content-Type": "application/json",
                },
            )

        if res.status_code not in (200, 201):
            logger.error("Culqi create_checkout failed: %s %s", res.status_code, res.text)
            raise RuntimeError("Failed to create Culqi order")

        response_data = res.json()
        order_id = response_data.get("id", "")

        # Return a special URL that the frontend will intercept
        # to open Culqi Checkout modal with this order
        checkout_url = (
            f"{settings.frontend_url}/billing/checkout"
            f"?provider=culqi&order_id={order_id}&plan={plan}&org_id={org_id}"
        )

        logger.info("culqi.create_checkout: org=%s plan=%s order=%s", org_id, plan, order_id)
        return checkout_url

    async def verify_webhook(self, payload: bytes, headers: dict) -> dict | None:
        """
        Verify Culqi webhook signature (HMAC-SHA256).

        Culqi sends a x-culqi-signature header with the HMAC-SHA256
        of the raw body, signed with the merchant's webhook secret.

        If no webhook secret is configured, falls back to parse-only (dev mode).
        """
        import json
        import hashlib
        import hmac

        try:
            data = json.loads(payload)
        except Exception as exc:
            logger.warning("Culqi webhook parse error: %s", exc)
            return None

        webhook_secret = settings.culqi_webhook_secret
        if webhook_secret:
            received_sig = headers.get("x-culqi-signature", "")
            if not received_sig:
                logger.warning("Culqi webhook: missing x-culqi-signature header")
                return None

            expected_sig = hmac.new(
                webhook_secret.encode("utf-8"),
                payload,
                hashlib.sha256,
            ).hexdigest()

            if not hmac.compare_digest(expected_sig, received_sig):
                logger.warning("Culqi webhook: HMAC mismatch — rejecting")
                return None

            logger.debug("Culqi webhook: HMAC verified OK")
        else:
            logger.warning("Culqi webhook: no culqi_webhook_secret configured — skipping verification (DEV MODE)")

        return {
            "type": data.get("type", ""),
            "data_id": data.get("data", {}).get("id", ""),
            "raw": data,
        }

    async def cancel_subscription(self, subscription_id: str) -> dict:
        import httpx
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.delete(
                f"https://api.culqi.com/v2/subscriptions/{subscription_id}",
                headers={"Authorization": f"Bearer {settings.culqi_secret_key}"},
            )
        logger.info("culqi.cancel_subscription: %s status=%s", subscription_id, res.status_code)
        return {"status": "cancelled", "provider": "culqi"}


# ---------------------------------------------------------------------------
# Service facade — auto-detects configured providers
# ---------------------------------------------------------------------------

class PaymentService:
    """Multi-provider payment facade. Uses whichever providers are configured."""

    def __init__(self) -> None:
        self._mp = MercadoPagoProvider()
        self._culqi = CulqiProvider()

    @property
    def providers(self) -> list[PaymentProvider]:
        """Return list of available (configured) providers."""
        return [p for p in [self._mp, self._culqi] if p.is_available]

    @property
    def is_available(self) -> bool:
        return len(self.providers) > 0

    @property
    def primary(self) -> PaymentProvider | None:
        """Return the primary (first available) provider. Prefers MercadoPago."""
        providers = self.providers
        return providers[0] if providers else None

    def get_provider(self, name: str) -> PaymentProvider | None:
        """Get a specific provider by name."""
        for p in [self._mp, self._culqi]:
            if p.name == name and p.is_available:
                return p
        return None

    @property
    def plan_pricing(self) -> dict:
        return PLAN_PRICING


# Module-level singleton
payment_service = PaymentService()
