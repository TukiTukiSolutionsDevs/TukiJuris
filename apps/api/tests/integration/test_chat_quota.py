"""Integration tests — daily chat quota boundary.

Covers spec AC1, AC2, AC3, AC5.

Requirements:
  - Live PostgreSQL + Redis (docker-compose up)
  - Migration 006 applied (alembic upgrade head)

Run with:
  cd apps/api && python -m pytest tests/integration/test_chat_quota.py -v -m integration

Skipped automatically if DB is unreachable.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.config import settings
from app.main import app


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _register_free_user(client: AsyncClient) -> tuple[str, uuid.UUID]:
    """Register a unique free-plan user. Returns (access_token, user_id)."""
    email = f"quota-{uuid.uuid4().hex[:8]}@test.com"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "TestPass123!", "full_name": "Quota Tester"},
    )
    assert res.status_code in (200, 201), f"Register failed: {res.status_code} {res.text}"
    data = res.json()
    token = data["access_token"]
    # Decode without verification to extract sub (user_id)
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    user_id = uuid.UUID(payload["sub"])
    return token, user_id


async def _seed_usage(user_id: uuid.UUID, query_count: int) -> None:
    """Insert (or overwrite) a usage record for today directly via asyncpg."""
    import asyncpg

    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    today = datetime.now(UTC).date()
    try:
        await conn.execute(
            """
            INSERT INTO usage_records
                (id, user_id, organization_id, day, query_count, token_count,
                 created_at, updated_at)
            VALUES (gen_random_uuid(), $1, NULL, $2, $3, 0, NOW(), NOW())
            ON CONFLICT (user_id, day) DO UPDATE SET query_count = $3
            """,
            user_id,
            today,
            query_count,
        )
    finally:
        await conn.close()


# ── Mock LLM response ─────────────────────────────────────────────────────────

_MOCK_ORCHESTRATOR_RESULT = {
    "response": "El habeas corpus es una garantía constitucional.",
    "agent_used": "constitucional",
    "legal_area": "constitucional",
    "citations": [],
    "model_used": "gpt-4o-mini",
    "tokens_used": 80,
}


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.integration
class TestChatQuotaBoundary:
    async def test_ac2_429_when_at_limit(self, http_client: AsyncClient):
        """AC2: user with 10 queries already used gets HTTP 429 with spec payload."""
        token, user_id = await _register_free_user(http_client)
        await _seed_usage(user_id, query_count=10)

        res = await http_client.post(
            "/api/chat/query",
            json={"message": "¿Qué es el habeas corpus?"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert res.status_code == 429
        detail = res.json()["detail"]
        assert detail["code"] == "quota_exceeded"
        assert detail["plan"] == "free"
        assert detail["used"] == 10
        assert detail["limit"] == 10
        # reset_at must be a valid ISO 8601 UTC timestamp
        reset_str = detail["reset_at"]
        assert reset_str.endswith("Z") or "+00:00" in reset_str

    async def test_ac1_200_at_ninth_query(self, http_client: AsyncClient):
        """AC1: user with 9 queries used is allowed through (quota not exceeded)."""
        token, user_id = await _register_free_user(http_client)
        await _seed_usage(user_id, query_count=9)

        with patch(
            "app.agents.orchestrator.legal_orchestrator.process_query",
            new=AsyncMock(return_value=_MOCK_ORCHESTRATOR_RESULT),
        ):
            res = await http_client.post(
                "/api/chat/query",
                json={"message": "¿Qué es el habeas corpus?"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert res.status_code == 200

    async def test_payload_shape_matches_spec(self, http_client: AsyncClient):
        """Spec §4: 429 detail must have code, plan, used, limit, reset_at."""
        token, user_id = await _register_free_user(http_client)
        await _seed_usage(user_id, query_count=10)

        res = await http_client.post(
            "/api/chat/query",
            json={"message": "test"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert res.status_code == 429
        detail = res.json()["detail"]
        required_keys = {"code", "plan", "used", "limit", "reset_at"}
        assert required_keys.issubset(detail.keys()), (
            f"Missing keys: {required_keys - set(detail.keys())}"
        )

    async def test_ac5_free_user_without_org_can_be_tracked(self, http_client: AsyncClient):
        """AC5: free user without an organisation can have usage tracked (org_id=None)."""
        token, user_id = await _register_free_user(http_client)
        # Seed 9 with org_id=NULL — already done by _seed_usage (uses NULL)
        await _seed_usage(user_id, query_count=9)

        with patch(
            "app.agents.orchestrator.legal_orchestrator.process_query",
            new=AsyncMock(return_value=_MOCK_ORCHESTRATOR_RESULT),
        ):
            res = await http_client.post(
                "/api/chat/query",
                json={"message": "¿Qué es el habeas corpus?"},
                headers={"Authorization": f"Bearer {token}"},
            )

        # Should succeed — free user tracked without org
        assert res.status_code == 200

    async def test_unauthenticated_request_skips_quota(self, http_client: AsyncClient):
        """Unauthenticated requests are not quota-checked."""
        with patch(
            "app.agents.orchestrator.legal_orchestrator.process_query",
            new=AsyncMock(return_value=_MOCK_ORCHESTRATOR_RESULT),
        ):
            res = await http_client.post(
                "/api/chat/query",
                json={"message": "¿Qué es el habeas corpus?"},
            )

        # No auth = no quota check; may 200 or fail on other guards, but NOT 429
        assert res.status_code != 429
