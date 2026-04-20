"""Integration tests — Public API v1 (sub-batch B.3).

Spec IDs covered:
  - chat-stream.unit.010  test_v1_query_jwt_happy_path
  - chat-stream.unit.011  test_v1_query_api_key_happy_path
  - chat-stream.unit.012  test_v1_check_scope_missing_scope_raises
  - chat-stream.unit.013  test_v1_usage_quota_calculation
  - chat-stream.unit.014  test_v1_rate_limit_headers_injected

Additional coverage:
  - Missing auth → 401
  - Invalid token → 401
  - Rate limit tiers config (free=30, pro=120, studio=600)

FIX-06 status:
  CONFIRMED REAL. RateLimitGuard only injects X-RateLimit-* headers on the
  429 exception path; authenticated 200 responses receive no headers. Fixed in
  app/api/deps.py — RateLimitGuard now accepts FastAPI Response and injects
  headers on the allowed path.

Run with:
  docker exec tukijuris-api-1 pytest apps/api/tests/integration/test_v1_api.py -v --tb=short
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.api_key import APIKey

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ORCHESTRATOR_PATCH = "app.api.routes.v1.legal_orchestrator"

_MOCK_QUERY_RESULT = {
    "response": "El artículo 22 del Código Civil regula los contratos.",
    "agent_used": "civil",
    "legal_area": "civil",
    "citations": [
        {
            "document": "Código Civil",
            "article": "Art. 22",
            "content": "Los contratos...",
            "score": 0.95,
        }
    ],
    "model_used": "gpt-4o-mini",
    "tokens_used": 55,
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def registered_user(http_client: AsyncClient) -> tuple[str, str, uuid.UUID]:
    """Register a unique user and return (email, access_token, user_id)."""
    from app.core.security import decode_access_token

    email = f"v1-{uuid.uuid4().hex[:8]}@test.com"
    res = await http_client.post(
        "/api/auth/register",
        json={"email": email, "password": "TestPass123!", "full_name": "V1 Tester"},
    )
    assert res.status_code in (200, 201), f"Register failed: {res.status_code} {res.text}"
    token = res.json()["access_token"]

    payload = decode_access_token(token)
    assert payload and "sub" in payload, f"Could not decode token: {payload}"
    user_id = uuid.UUID(payload["sub"])

    return email, token, user_id


async def _create_api_key(
    user_id: uuid.UUID,
    scopes: list[str],
    rate_limit: int = 30,
) -> tuple[str, APIKey]:
    """Insert an API key directly into the DB and return (raw_key, model)."""
    from app.core.database import async_session_factory

    raw_key = f"ak_{uuid.uuid4().hex}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:8]

    api_key_obj = APIKey(
        id=uuid.uuid4(),
        user_id=user_id,
        name="test-key",
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=scopes,
        is_active=True,
        rate_limit_per_minute=rate_limit,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with async_session_factory() as session:
        session.add(api_key_obj)
        await session.commit()

    return raw_key, api_key_obj


# ---------------------------------------------------------------------------
# Unit.010 + Unit.011 — Token authentication
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestV1TokenAuth:
    """Token authentication: JWT + API key + auth failure paths."""

    async def test_v1_query_missing_auth_returns_401(self, http_client: AsyncClient):
        """No credentials → 401."""
        res = await http_client.post(
            "/api/v1/query",
            json={"query": "¿Qué es el habeas corpus?"},
        )
        assert res.status_code == 401

    async def test_v1_query_invalid_token_returns_401(self, http_client: AsyncClient):
        """Garbage Bearer token → 401."""
        res = await http_client.post(
            "/api/v1/query",
            json={"query": "¿Qué es el habeas corpus?"},
            headers={"Authorization": "Bearer this.is.not.valid"},
        )
        assert res.status_code == 401

    async def test_v1_query_jwt_happy_path(
        self,
        http_client: AsyncClient,
        registered_user: tuple[str, str, uuid.UUID],
    ):
        """chat-stream.unit.010 — JWT Bearer → 200 with result payload."""
        _, token, _ = registered_user

        mock_orchestrator = AsyncMock()
        mock_orchestrator.process_query = AsyncMock(return_value=_MOCK_QUERY_RESULT)

        with patch(_ORCHESTRATOR_PATCH, mock_orchestrator):
            res = await http_client.post(
                "/api/v1/query",
                json={"query": "Requisitos del contrato de arrendamiento"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert res.status_code == 200, res.text
        data = res.json()
        assert "answer" in data
        assert "citations" in data
        assert "area_detected" in data
        assert isinstance(data["citations"], list)

    async def test_v1_query_api_key_happy_path(
        self,
        http_client: AsyncClient,
        registered_user: tuple[str, str, uuid.UUID],
    ):
        """chat-stream.unit.011 — API key (X-API-Key header) → 200."""
        _, _, user_id = registered_user
        raw_key, _ = await _create_api_key(user_id, scopes=["query", "search"])

        mock_orchestrator = AsyncMock()
        mock_orchestrator.process_query = AsyncMock(return_value=_MOCK_QUERY_RESULT)

        with patch(_ORCHESTRATOR_PATCH, mock_orchestrator):
            res = await http_client.post(
                "/api/v1/query",
                json={"query": "Derechos del trabajador despedido"},
                headers={"X-API-Key": raw_key},
            )

        assert res.status_code == 200, res.text
        data = res.json()
        assert "answer" in data

    async def test_v1_query_api_key_bearer_prefix(
        self,
        http_client: AsyncClient,
        registered_user: tuple[str, str, uuid.UUID],
    ):
        """API key via Authorization: Bearer ak_... → 200 (alternative auth path)."""
        _, _, user_id = registered_user
        raw_key, _ = await _create_api_key(user_id, scopes=["query", "search"])

        mock_orchestrator = AsyncMock()
        mock_orchestrator.process_query = AsyncMock(return_value=_MOCK_QUERY_RESULT)

        with patch(_ORCHESTRATOR_PATCH, mock_orchestrator):
            res = await http_client.post(
                "/api/v1/query",
                json={"query": "Responsabilidad civil extracontractual"},
                headers={"Authorization": f"Bearer {raw_key}"},
            )

        assert res.status_code == 200, res.text


# ---------------------------------------------------------------------------
# Unit.012 — Scope enforcement
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestV1Scopes:
    """Scope enforcement: missing scope → 403, correct scope → 200."""

    async def test_v1_check_scope_missing_scope_raises(
        self,
        http_client: AsyncClient,
        registered_user: tuple[str, str, uuid.UUID],
    ):
        """chat-stream.unit.012 — API key with only 'search' scope calling /v1/query → 403."""
        _, _, user_id = registered_user
        raw_key, _ = await _create_api_key(user_id, scopes=["search"])

        res = await http_client.post(
            "/api/v1/query",
            json={"query": "¿Qué establece el artículo 1 de la constitución?"},
            headers={"X-API-Key": raw_key},
        )

        assert res.status_code == 403, res.text
        assert "query" in res.json().get("detail", "").lower()

    async def test_v1_query_scope_sufficient_passes(
        self,
        http_client: AsyncClient,
        registered_user: tuple[str, str, uuid.UUID],
    ):
        """API key with 'query' scope → scope check passes, 200."""
        _, _, user_id = registered_user
        raw_key, _ = await _create_api_key(user_id, scopes=["query"])

        mock_orchestrator = AsyncMock()
        mock_orchestrator.process_query = AsyncMock(return_value=_MOCK_QUERY_RESULT)

        with patch(_ORCHESTRATOR_PATCH, mock_orchestrator):
            res = await http_client.post(
                "/api/v1/query",
                json={"query": "Derecho de propiedad en Perú"},
                headers={"X-API-Key": raw_key},
            )

        assert res.status_code == 200, res.text


# ---------------------------------------------------------------------------
# Unit.013 — Usage endpoint
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestV1Usage:
    """Usage endpoint: structure and correctness."""

    async def test_v1_usage_quota_calculation(
        self,
        http_client: AsyncClient,
        registered_user: tuple[str, str, uuid.UUID],
    ):
        """chat-stream.unit.013 — GET /v1/usage returns correct structure."""
        _, _, user_id = registered_user
        raw_key, _ = await _create_api_key(user_id, scopes=["query"], rate_limit=120)

        res = await http_client.get(
            "/api/v1/usage",
            headers={"X-API-Key": raw_key},
        )

        assert res.status_code == 200, res.text
        data = res.json()

        # Structure assertions
        assert "queries_today" in data
        assert "queries_month" in data
        assert "plan" in data
        assert "limit_per_minute" in data
        assert "note" in data

        # Value sanity — fresh user, no prior queries
        assert isinstance(data["queries_today"], int)
        assert isinstance(data["queries_month"], int)
        assert data["queries_today"] >= 0
        assert data["queries_month"] >= 0

        # Rate limit from the key we created (120)
        assert data["limit_per_minute"] == 120


# ---------------------------------------------------------------------------
# Rate limit tier config (no HTTP required)
# ---------------------------------------------------------------------------


class TestRateLimitTiers:
    """Verify rate limit tiers match spec: free=30, pro=120, studio=600."""

    def test_rate_limit_tiers_match_spec(self):
        """Spec requirement: free=30/min, pro=120/min, studio(enterprise)=600/min."""
        from app.core.rate_limiter import RATE_LIMIT_TIERS

        assert RATE_LIMIT_TIERS["free"][0] == 30, "free tier must be 30 req/min"
        assert RATE_LIMIT_TIERS["pro"][0] == 120, "pro tier must be 120 req/min"
        assert RATE_LIMIT_TIERS["studio"][0] == 600, "studio/enterprise tier must be 600 req/min"


# ---------------------------------------------------------------------------
# Unit.014 — Rate-limit headers (FIX-06)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestV1RateLimitHeaders:
    """FIX-06: X-RateLimit-* headers must appear on successful v1 responses."""

    async def test_v1_rate_limit_headers_injected(
        self,
        http_client: AsyncClient,
        registered_user: tuple[str, str, uuid.UUID],
    ):
        """chat-stream.unit.014 — GET /v1/usage response includes X-RateLimit-Limit."""
        _, _, user_id = registered_user
        raw_key, _ = await _create_api_key(user_id, scopes=["query"], rate_limit=30)

        res = await http_client.get(
            "/api/v1/usage",
            headers={"X-API-Key": raw_key},
        )

        assert res.status_code == 200, res.text
        assert "x-ratelimit-limit" in res.headers, (
            "X-RateLimit-Limit header missing from authenticated v1 response. "
            "FIX-06: RateLimitGuard must inject headers on allowed requests."
        )
        assert "x-ratelimit-remaining" in res.headers
        assert "x-ratelimit-reset" in res.headers

        limit_value = int(res.headers["x-ratelimit-limit"])
        assert limit_value == 600, (
            f"Expected READ bucket limit 600, got {limit_value}. "
            "/v1/usage uses RateLimitBucket.READ (flat 600/min)."
        )
