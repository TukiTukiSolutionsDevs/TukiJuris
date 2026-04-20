"""Integration tests — shared conversation public access (sub-batch E.1a).

Spec IDs covered:
  - conversations.unit.005  test_conversation_share_creates_link
  - conversations.unit.006  test_shared_conversation_public_access
  - conversations.unit.007  test_shared_conversation_revocation

Routes exercised:
  POST /api/conversations/{id}/share   — authenticated; generates share link
  GET  /shared/{share_id}              — PUBLIC; no Authorization header

NOTE: There is no HTTP revoke endpoint yet. T-007 manipulates `is_shared`
directly via DB session to test the route's access gate (Conversation.is_shared
must be True for the public GET to return 200).

Run with:
  docker exec tukijuris-api-1 pytest tests/integration/test_shared.py -v --tb=short
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient
from sqlalchemy import update

from app.main import app
from app.models.conversation import Conversation
from tests.factories.conversation import make_conversation

_MOCK_RESULT = {
    "response": "Respuesta simulada para pruebas de rutas compartidas.",
    "agent_used": "general",
    "legal_area": "general",
    "citations": [],
    "model_used": "mock-model",
    "tokens_used": 5,
}
_ORCHESTRATOR_PATH = "app.agents.orchestrator.legal_orchestrator.process_query"


# ---------------------------------------------------------------------------
# conversations.unit.005 — share creates link
# ---------------------------------------------------------------------------


async def test_conversation_share_creates_link(auth_client):
    """POST /share → share_id (12-char alphanumeric); is_shared=True in DB.

    Spec: conversations.unit.005
    """
    with patch(_ORCHESTRATOR_PATH, new=AsyncMock(return_value=_MOCK_RESULT)):
        conv_id, _ = await make_conversation(auth_client)

    res = await auth_client.post(f"/api/conversations/{conv_id}/share")
    assert res.status_code == 200, f"Share failed: {res.status_code} {res.text[:200]}"

    data = res.json()
    share_id = data.get("share_id", "")
    assert len(share_id) == 12, f"Expected 12-char share_id, got {share_id!r}"
    assert share_id.isalnum(), f"share_id not alphanumeric: {share_id!r}"

    detail = await auth_client.get(f"/api/conversations/{conv_id}")
    assert detail.status_code == 200
    assert detail.json()["is_shared"] is True, "is_shared should be True after share"


# ---------------------------------------------------------------------------
# conversations.unit.006 — public access (no auth)
# ---------------------------------------------------------------------------


async def test_shared_conversation_public_access(auth_client):
    """Shared conv accessible via GET /shared/{id} without Authorization. (006)"""
    with patch(_ORCHESTRATOR_PATH, new=AsyncMock(return_value=_MOCK_RESULT)):
        conv_id, _ = await make_conversation(auth_client, messages=("¿Qué es un contrato?",))

    share_res = await auth_client.post(f"/api/conversations/{conv_id}/share")
    assert share_res.status_code == 200
    share_id = share_res.json()["share_id"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as public:
        res = await public.get(f"/api/shared/{share_id}")

    assert res.status_code == 200, f"Public GET failed: {res.status_code} {res.text[:200]}"
    body = res.json()
    assert "messages" in body, "Response missing 'messages' key"
    assert len(body["messages"]) > 0, "Expected at least one message in shared conversation"


# ---------------------------------------------------------------------------
# conversations.unit.007 — revocation
# ---------------------------------------------------------------------------


async def test_shared_conversation_revocation(auth_client, db_session):
    """After is_shared=False, public GET /shared/{id} → 404. (007)

    No HTTP revoke endpoint exists yet (missing route — flagged separately).
    DB manipulation tests the route's own access gate.
    """
    with patch(_ORCHESTRATOR_PATH, new=AsyncMock(return_value=_MOCK_RESULT)):
        conv_id, _ = await make_conversation(auth_client)

    share_res = await auth_client.post(f"/api/conversations/{conv_id}/share")
    assert share_res.status_code == 200
    share_id = share_res.json()["share_id"]

    # Simulate revocation: set is_shared=False directly (no revoke route yet)
    await db_session.execute(
        update(Conversation)
        .where(Conversation.id == uuid.UUID(conv_id))
        .values(is_shared=False)
    )
    await db_session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as public:
        res = await public.get(f"/api/shared/{share_id}")

    assert res.status_code == 404, (
        f"Expected 404 after revocation, got {res.status_code} — "
        "route may not be checking is_shared flag"
    )
