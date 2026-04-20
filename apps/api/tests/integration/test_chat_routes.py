"""Integration tests — chat POST route (sub-batch B.1).

Spec IDs covered:
  - chat-stream.unit.001  test_chat_post_happy_path_llm_mock
  - chat-stream.unit.003  test_chat_byok_fallback_platform_key
  + 4 additional tests for model resolution paths not covered elsewhere.

NOT covered here (other files / batches):
  - unit.002  429 boundary → already in test_chat_quota.py::test_ac2_429_when_at_limit
  - unit.004–014  stream / v1 → sub-batches B.2 and B.3

Requirements:
  - Live PostgreSQL + Redis (docker-compose up)
  - Mock orchestrator to avoid real LLM calls

Run with:
  docker exec tukijuris-api-1 pytest apps/api/tests/integration/test_chat_routes.py -v --tb=short
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


# ── Shared fixtures ───────────────────────────────────────────────────────────

_MOCK_RESULT = {
    "response": "La Constitución peruana garantiza el habeas corpus.",
    "agent_used": "constitucional",
    "legal_area": "constitucional",
    "citations": [],
    "model_used": "gpt-4o-mini",
    "tokens_used": 42,
}

_ORCHESTRATOR_PATH = "app.agents.orchestrator.legal_orchestrator.process_query"


@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def auth_user(http_client: AsyncClient) -> tuple[AsyncClient, str]:
    """Register a unique free-plan user and return (client, access_token)."""
    email = f"chat-{uuid.uuid4().hex[:8]}@test.com"
    res = await http_client.post(
        "/api/auth/register",
        json={"email": email, "password": "TestPass123!", "full_name": "Chat Tester"},
    )
    assert res.status_code in (200, 201), f"Register failed: {res.status_code} {res.text}"
    token = res.json()["access_token"]
    return http_client, token


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.integration
class TestChatRoutes:

    # ------------------------------------------------------------------
    # chat-stream.unit.001
    # ------------------------------------------------------------------

    async def test_chat_post_happy_path_llm_mock(
        self, auth_user: tuple[AsyncClient, str]
    ):
        """200 OK — full ChatResponse JSON schema validated.

        Spec: chat-stream.unit.001
        Ensures /api/chat/query succeeds and returns every field declared
        in ChatResponse with correct types. Uses mocked orchestrator so no
        real LLM is invoked.
        """
        client, token = auth_user

        with patch(_ORCHESTRATOR_PATH, new=AsyncMock(return_value=_MOCK_RESULT)):
            res = await client.post(
                "/api/chat/query",
                json={"message": "¿Qué es el habeas corpus?"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert res.status_code == 200
        data = res.json()

        # Required fields — must all be present
        for field in ("conversation_id", "message", "agent_used", "legal_area", "model_used", "latency_ms"):
            assert field in data, f"Missing field: {field}"

        assert data["message"] == _MOCK_RESULT["response"]
        assert data["agent_used"] == "constitucional"
        assert data["legal_area"] == "constitucional"
        assert data["model_used"] == "gpt-4o-mini"
        assert data["tokens_used"] == 42
        assert isinstance(data["latency_ms"], int)
        # conversation_id must be a parseable UUID
        uuid.UUID(data["conversation_id"])

    # ------------------------------------------------------------------
    # chat-stream.unit.003
    # ------------------------------------------------------------------

    async def test_chat_byok_fallback_platform_key(
        self, auth_user: tuple[AsyncClient, str]
    ):
        """Free-plan user + explicit model → BYOK disabled → platform key used → 200.

        Spec: chat-stream.unit.003
        Asserts:
        - get_user_keys_for_model is NOT called (byok_enabled=False on free plan)
        - orchestrator receives the resolved platform api_key (not None)
        """
        client, token = auth_user

        mock_orch = AsyncMock(return_value=_MOCK_RESULT)

        with (
            patch(
                "app.api.routes.chat.usage_service.check_tier_limit",
                new=AsyncMock(
                    return_value={
                        "allowed": True,
                        "tier": 1,
                        "limit": 50,
                        "used": 0,
                        "period": "day",
                    }
                ),
            ),
            patch(
                "app.api.routes.chat.llm_service.resolve_free_tier",
                return_value=("gpt-4o-mini", "sk-platform-test-key"),
            ),
            patch(
                "app.api.routes.chat.get_user_keys_for_model",
                new=AsyncMock(return_value=None),
            ) as mock_byok_lookup,
            patch(_ORCHESTRATOR_PATH, new=mock_orch),
        ):
            res = await client.post(
                "/api/chat/query",
                json={"message": "Analiza este contrato.", "model": "gpt-4o-mini"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert res.status_code == 200
        # Free plan → byok_enabled=False → BYOK key lookup must be skipped
        mock_byok_lookup.assert_not_called()
        # Orchestrator received the platform key (non-None) injected by the route
        assert mock_orch.called
        call_kwargs = mock_orch.call_args.kwargs
        assert call_kwargs.get("user_api_key") == "sk-platform-test-key"

    # ------------------------------------------------------------------
    # Additional coverage — model resolution paths
    # ------------------------------------------------------------------

    async def test_chat_model_unavailable_on_plan_403(
        self, auth_user: tuple[AsyncClient, str]
    ):
        """Model gated at tier 0 on current plan → 403 Forbidden.

        Covers the `tier_check["limit"] == 0` branch in chat.py.
        No orchestrator call is made — the gate fires first.
        """
        client, token = auth_user

        with patch(
            "app.api.routes.chat.usage_service.check_tier_limit",
            new=AsyncMock(
                return_value={
                    "allowed": False,
                    "limit": 0,
                    "tier": 2,
                    "used": 0,
                    "period": "day",
                }
            ),
        ):
            res = await client.post(
                "/api/chat/query",
                json={"message": "Dame análisis avanzado.", "model": "gpt-4-turbo"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert res.status_code == 403
        detail = res.json()["detail"]
        # Route embeds the plan name and tier in the Spanish-language detail string
        assert "plan" in detail.lower() or "Tier" in detail

    async def test_chat_tier_limit_exhausted_429(
        self, auth_user: tuple[AsyncClient, str]
    ):
        """Model tier quota exhausted (limit > 0, all used) → 429.

        Covers the `not allowed and limit > 0` branch in chat.py.
        Distinct from daily quota: this is per-tier usage, not daily total.
        """
        client, token = auth_user

        with patch(
            "app.api.routes.chat.usage_service.check_tier_limit",
            new=AsyncMock(
                return_value={
                    "allowed": False,
                    "limit": 5,
                    "tier": 1,
                    "used": 5,
                    "period": "day",
                }
            ),
        ):
            res = await client.post(
                "/api/chat/query",
                json={"message": "Consulta legal.", "model": "gpt-4o-mini"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert res.status_code == 429
        detail = res.json()["detail"]
        # Route embeds "límite" and usage numbers in the detail string
        assert "5" in detail

    async def test_chat_no_model_uses_free_tier_default(
        self, auth_user: tuple[AsyncClient, str]
    ):
        """No model param → resolve_free_tier() called with no args → default model → 200.

        Covers the `else` (no body.model) branch in chat.py line ~178.
        """
        client, token = auth_user

        with (
            patch(
                "app.api.routes.chat.llm_service.resolve_free_tier",
                return_value=("gpt-4o-mini", "sk-platform-default"),
            ) as mock_resolve,
            patch(_ORCHESTRATOR_PATH, new=AsyncMock(return_value=_MOCK_RESULT)),
        ):
            res = await client.post(
                "/api/chat/query",
                json={"message": "¿Cuál es la diferencia entre dolo y culpa?"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert res.status_code == 200
        # Must be called with no positional args (default free-tier resolution)
        mock_resolve.assert_called_once_with()

    async def test_chat_unauthenticated_skips_quota_200(
        self, http_client: AsyncClient
    ):
        """Unauthenticated request: quota gate entirely skipped → 200.

        Validates anonymous access is permitted and usage_service is never
        consulted when current_user is None.
        """
        with (
            patch(_ORCHESTRATOR_PATH, new=AsyncMock(return_value=_MOCK_RESULT)),
            patch(
                "app.api.routes.chat.usage_service.check_daily_limit",
                new=AsyncMock(side_effect=AssertionError("quota check must not be called for anonymous")),
            ),
        ):
            res = await http_client.post(
                "/api/chat/query",
                json={"message": "¿Qué es la prescripción extintiva?"},
            )

        assert res.status_code == 200
        assert res.json()["message"] == _MOCK_RESULT["response"]
