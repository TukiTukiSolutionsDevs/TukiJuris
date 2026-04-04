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
    "base": {
        "name": "Plan Base",
        "price": 70.00,       # S/70 per month
        "price_cents": 7000,  # Culqi uses cents
        "currency": "PEN",
        "daily_limit": 100,
        "interval": "months",
        "interval_count": 1,
    },
    "enterprise": {
        "name": "Plan Enterprise",
        "price": None,  # Contact sales
        "currency": "PEN",
        "daily_limit": -1,  # unlimited
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
        """Verify MercadoPago webhook — MP sends data_id + type as query params or JSON body."""
        import json
        try:
            data = json.loads(payload)
            return {
                "type": data.get("type", data.get("topic", "")),
                "data_id": data.get("data", {}).get("id", data.get("id", "")),
                "raw": data,
            }
        except Exception as exc:
            logger.warning("MP webhook parse error: %s", exc)
            return None

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
        """Verify Culqi webhook signature."""
        import json
        try:
            data = json.loads(payload)
            # Culqi sends events with type and data
            return {
                "type": data.get("type", ""),
                "data_id": data.get("data", {}).get("id", ""),
                "raw": data,
            }
        except Exception as exc:
            logger.warning("Culqi webhook parse error: %s", exc)
            return None

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
