"""Payment provider adapter tests (TB.5).

Tests CulqiAdapter and MPAdapter using httpx.MockTransport (no live API calls).
Verifies:
  - create_customer / create_card / charge_stored_card happy paths
  - X-Charge-Channel: recurrent header on Culqi charges (MANDATORY)
  - X-Culqi-Idempotency-Key header on Culqi charges
  - X-Idempotency-Key header on MP preapproval activation
  - Provider error responses mapped to ChargeResult(success=False)
  - ProviderError raised for customer/card creation failures
  - Network failures return ChargeResult(success=False, error_code=network_error)

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_payment_providers.py -v
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import httpx
import pytest

from app.services.payment_providers.base import ChargeResult, ProviderError
from app.services.payment_providers.culqi_adapter import CulqiAdapter
from app.services.payment_providers.mp_adapter import MPAdapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_transport(responses: list[dict]) -> httpx.MockTransport:
    """Build a MockTransport that returns responses in sequence."""
    response_iter = iter(responses)

    def _handler(request: httpx.Request) -> httpx.Response:
        try:
            spec = next(response_iter)
        except StopIteration:
            raise RuntimeError("MockTransport: more requests made than responses configured")
        return httpx.Response(
            status_code=spec.get("status", 200),
            headers={"content-type": "application/json"},
            content=json.dumps(spec.get("body", {})).encode(),
        )

    return httpx.MockTransport(_handler)


def _culqi(responses: list[dict]) -> CulqiAdapter:
    client = httpx.AsyncClient(transport=_mock_transport(responses))
    return CulqiAdapter(secret_key="sk_test_xxx", client=client)


def _mp(responses: list[dict]) -> MPAdapter:
    client = httpx.AsyncClient(transport=_mock_transport(responses))
    return MPAdapter(access_token="TEST-xxx", client=client)


# ---------------------------------------------------------------------------
# CulqiAdapter tests
# ---------------------------------------------------------------------------


class TestCulqiAdapterCreateCustomer:
    async def test_happy_path_returns_customer_id(self):
        adapter = _culqi([{"status": 201, "body": {"id": "cus_test_123"}}])
        customer_id = await adapter.create_customer(
            email="test@tuki.pe",
            first_name="Juan",
            last_name="Pérez",
        )
        assert customer_id == "cus_test_123"

    async def test_with_phone(self):
        """Phone is passed when provided."""
        captured: list[httpx.Request] = []

        async def _capture(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(200, json={"id": "cus_abc"})

        client = httpx.AsyncClient(transport=httpx.MockTransport(_capture))
        adapter = CulqiAdapter(secret_key="sk_test", client=client)
        await adapter.create_customer(
            email="a@b.com", first_name="A", last_name="B", phone="987654321"
        )
        body = json.loads(captured[0].content)
        assert body["phone_number"] == "987654321"

    async def test_api_error_raises_provider_error(self):
        adapter = _culqi([{
            "status": 400,
            "body": {"code": "invalid_email", "merchant_message": "Invalid email format"},
        }])
        with pytest.raises(ProviderError) as exc_info:
            await adapter.create_customer(
                email="bad", first_name="X", last_name="Y"
            )
        assert exc_info.value.code == "invalid_email"


class TestCulqiAdapterCreateCard:
    async def test_happy_path_returns_card_id(self):
        adapter = _culqi([{"status": 201, "body": {"id": "crd_test_456"}}])
        card_id = await adapter.create_card("cus_123", "tkn_xxx")
        assert card_id == "crd_test_456"

    async def test_api_error_raises_provider_error(self):
        adapter = _culqi([{
            "status": 402,
            "body": {"code": "card_declined", "merchant_message": "Card was declined"},
        }])
        with pytest.raises(ProviderError) as exc_info:
            await adapter.create_card("cus_123", "tkn_bad")
        assert exc_info.value.code == "card_declined"
        assert exc_info.value.status == 402


class TestCulqiAdapterChargeStoredCard:
    async def test_happy_path_returns_success(self):
        adapter = _culqi([{
            "status": 201,
            "body": {"id": "chr_test_789", "outcome": {"type": "venta_exitosa"}},
        }])
        result = await adapter.charge_stored_card(
            customer_id="cus_123",
            card_id="crd_456",
            amount_cents=7000,
            currency="PEN",
            metadata={"trial_id": "t-1", "plan_code": "pro", "email": "a@b.com"},
            idempotency_key="t-1:scheduler:0",
        )
        assert result.success is True
        assert result.provider_charge_id == "chr_test_789"

    async def test_x_charge_channel_recurrent_header_is_present(self):
        """MANDATORY: X-Charge-Channel: recurrent must be sent on every charge."""
        captured: list[httpx.Request] = []

        async def _capture(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(201, json={"id": "chr_hdr_test"})

        client = httpx.AsyncClient(transport=httpx.MockTransport(_capture))
        adapter = CulqiAdapter(secret_key="sk_test", client=client)
        await adapter.charge_stored_card(
            customer_id="cus_1",
            card_id="crd_1",
            amount_cents=7000,
            currency="PEN",
            metadata={"trial_id": "t-1"},
            idempotency_key="t-1:0",
        )
        assert captured[0].headers["X-Charge-Channel"] == "recurrent"

    async def test_idempotency_key_header_is_present(self):
        captured: list[httpx.Request] = []

        async def _capture(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(201, json={"id": "chr_idem"})

        client = httpx.AsyncClient(transport=httpx.MockTransport(_capture))
        adapter = CulqiAdapter(secret_key="sk_test", client=client)
        await adapter.charge_stored_card(
            customer_id="cus_1",
            card_id="crd_1",
            amount_cents=7000,
            currency="PEN",
            metadata={},
            idempotency_key="my-unique-key-123",
        )
        assert captured[0].headers["X-Culqi-Idempotency-Key"] == "my-unique-key-123"

    async def test_provider_error_returns_charge_result_failure(self):
        """402/400 provider errors return ChargeResult(success=False), not exception."""
        adapter = _culqi([{
            "status": 402,
            "body": {
                "code": "insufficient_funds",
                "merchant_message": "Insufficient funds",
            },
        }])
        result = await adapter.charge_stored_card(
            customer_id="cus_1",
            card_id="crd_1",
            amount_cents=7000,
            currency="PEN",
            metadata={"trial_id": "t-1"},
            idempotency_key="t-1:0",
        )
        assert result.success is False
        assert result.error_code == "insufficient_funds"
        assert "Insufficient" in (result.error_message or "")

    async def test_network_failure_returns_charge_result_failure(self):
        """Network errors return ChargeResult(success=False) — never raise."""
        async def _raise(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        client = httpx.AsyncClient(transport=httpx.MockTransport(_raise))
        adapter = CulqiAdapter(secret_key="sk_test", client=client)
        result = await adapter.charge_stored_card(
            customer_id="cus_1",
            card_id="crd_1",
            amount_cents=7000,
            currency="PEN",
            metadata={},
            idempotency_key="t-1:0",
        )
        assert result.success is False
        assert result.error_code == "network_error"

    async def test_source_id_is_card_id_not_token(self):
        """Verify source_id in payload uses card_id (crd_xxx), not the original token."""
        captured: list[httpx.Request] = []

        async def _capture(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(201, json={"id": "chr_src"})

        client = httpx.AsyncClient(transport=httpx.MockTransport(_capture))
        adapter = CulqiAdapter(secret_key="sk", client=client)
        await adapter.charge_stored_card(
            customer_id="cus_1",
            card_id="crd_permanent_456",
            amount_cents=7000,
            currency="PEN",
            metadata={},
            idempotency_key="k",
        )
        body = json.loads(captured[0].content)
        assert body["source_id"] == "crd_permanent_456"


# ---------------------------------------------------------------------------
# MPAdapter tests
# ---------------------------------------------------------------------------


class TestMPAdapterCreateCustomer:
    async def test_happy_path_returns_customer_id(self):
        adapter = _mp([{"status": 201, "body": {"id": 123456789}}])
        customer_id = await adapter.create_customer(
            email="test@tuki.pe",
            first_name="María",
            last_name="García",
        )
        assert customer_id == "123456789"

    async def test_api_error_raises_provider_error(self):
        adapter = _mp([{
            "status": 400,
            "body": {"error": "invalid_email", "message": "Invalid email"},
        }])
        with pytest.raises(ProviderError) as exc_info:
            await adapter.create_customer(
                email="bad", first_name="X", last_name="Y"
            )
        assert exc_info.value.code == "invalid_email"


class TestMPAdapterCreateCard:
    async def test_happy_path_returns_preapproval_id(self):
        """MP create_card returns preapproval_id (not card.id)."""
        # Response 1: save card; Response 2: create preapproval
        adapter = _mp([
            {"status": 201, "body": {"id": "card_mp_123"}},
            {"status": 201, "body": {"id": "preapproval_789"}},
        ])
        result = await adapter.create_card(
            "customer_mp_1",
            "tkn_mp_fresh",
            metadata={
                "email": "a@b.com",
                "amount_cents": 7000,
                "plan_code": "pro",
                "currency": "PEN",
            },
        )
        assert result == "preapproval_789"

    async def test_card_save_failure_raises_provider_error(self):
        adapter = _mp([{
            "status": 400,
            "body": {"error": "invalid_token", "message": "Token expired"},
        }])
        with pytest.raises(ProviderError) as exc_info:
            await adapter.create_card("cus_1", "tkn_expired")
        assert exc_info.value.code == "invalid_token"

    async def test_preapproval_creation_failure_raises_provider_error(self):
        adapter = _mp([
            {"status": 201, "body": {"id": "card_ok"}},
            {"status": 400, "body": {"error": "preapproval_error", "message": "Bad config"}},
        ])
        with pytest.raises(ProviderError):
            await adapter.create_card(
                "cus_1", "tkn_ok",
                metadata={"email": "a@b.com", "amount_cents": 7000, "plan_code": "pro"},
            )


class TestMPAdapterChargeStoredCard:
    async def test_happy_path_activates_preapproval(self):
        adapter = _mp([{"status": 200, "body": {"id": "preapproval_789", "status": "authorized"}}])
        result = await adapter.charge_stored_card(
            customer_id="cus_mp_1",
            card_id="preapproval_789",
            amount_cents=7000,
            currency="PEN",
            metadata={"trial_id": "t-1"},
            idempotency_key="t-1:0",
        )
        assert result.success is True
        assert result.provider_charge_id == "preapproval_789"

    async def test_idempotency_key_header_is_present(self):
        captured: list[httpx.Request] = []

        async def _capture(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(200, json={"id": "pre_idem"})

        client = httpx.AsyncClient(transport=httpx.MockTransport(_capture))
        adapter = MPAdapter(access_token="TEST", client=client)
        await adapter.charge_stored_card(
            customer_id="cus_1",
            card_id="pre_idem",
            amount_cents=7000,
            currency="PEN",
            metadata={},
            idempotency_key="unique-key-mp-456",
        )
        assert captured[0].headers["X-Idempotency-Key"] == "unique-key-mp-456"

    async def test_provider_error_returns_charge_result_failure(self):
        adapter = _mp([{
            "status": 400,
            "body": {"error": "preapproval_not_found", "message": "Preapproval not found"},
        }])
        result = await adapter.charge_stored_card(
            customer_id="cus_1",
            card_id="pre_bad",
            amount_cents=7000,
            currency="PEN",
            metadata={"trial_id": "t-1"},
            idempotency_key="t-1:0",
        )
        assert result.success is False
        assert result.error_code == "preapproval_not_found"

    async def test_network_failure_returns_charge_result_failure(self):
        async def _raise(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("No route to host")

        client = httpx.AsyncClient(transport=httpx.MockTransport(_raise))
        adapter = MPAdapter(access_token="TEST", client=client)
        result = await adapter.charge_stored_card(
            customer_id="cus_1",
            card_id="pre_1",
            amount_cents=7000,
            currency="PEN",
            metadata={},
            idempotency_key="t-1:0",
        )
        assert result.success is False
        assert result.error_code == "network_error"


# ---------------------------------------------------------------------------
# Import / protocol smoke test
# ---------------------------------------------------------------------------


class TestProviderProtocol:
    def test_adapters_importable(self):
        from app.services.payment_providers import (
            ChargeResult,
            CulqiAdapter,
            MPAdapter,
            PaymentProviderAdapter,
            ProviderError,
        )
        assert CulqiAdapter.provider_name == "culqi"
        assert MPAdapter.provider_name == "mp"

    def test_charge_result_model(self):
        r = ChargeResult(success=True, provider_charge_id="chr_abc")
        assert r.success is True
        assert r.error_code is None

    def test_provider_error_attributes(self):
        e = ProviderError("card_declined", "Card was declined", status=402)
        assert e.code == "card_declined"
        assert e.status == 402
        assert str(e) == "Card was declined"
