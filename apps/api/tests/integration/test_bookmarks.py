"""Integration tests — bookmarks CRUD + isolation (sub-batch E.1a).

Spec IDs covered:
  - conversations.unit.008  test_bookmark_crud_happy_path
  - conversations.unit.009  test_bookmark_isolation

Routes exercised:
  PUT    /api/bookmarks/{message_id}  — toggle bookmark (True/False)
  GET    /api/bookmarks/              — list bookmarked messages for current user
  DELETE /api/bookmarks/{message_id}  — remove bookmark

Run with:
  docker exec tukijuris-api-1 pytest tests/integration/test_bookmarks.py -v --tb=short
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from tests.factories.conversation import make_conversation

_MOCK_RESULT = {
    "response": "Respuesta simulada para pruebas de marcadores.",
    "agent_used": "general",
    "legal_area": "general",
    "citations": [],
    "model_used": "mock-model",
    "tokens_used": 5,
}
_ORCHESTRATOR_PATH = "app.agents.orchestrator.legal_orchestrator.process_query"


# ---------------------------------------------------------------------------
# conversations.unit.008 — CRUD happy path
# ---------------------------------------------------------------------------


async def test_bookmark_crud_happy_path(auth_client):
    """PUT → bookmarked; GET lists it; DELETE → removed from list. (008)"""
    with patch(_ORCHESTRATOR_PATH, new=AsyncMock(return_value=_MOCK_RESULT)):
        conv_id, _ = await make_conversation(auth_client, messages=("Consulta de prueba.",))

    detail = await auth_client.get(f"/api/conversations/{conv_id}")
    assert detail.status_code == 200
    messages = detail.json()["messages"]
    assert messages, "Expected at least one message after make_conversation"
    message_id = messages[0]["id"]

    # Create bookmark: PUT toggles to True
    put_res = await auth_client.put(f"/api/bookmarks/{message_id}")
    assert put_res.status_code == 200, f"PUT failed: {put_res.status_code} {put_res.text[:200]}"
    assert put_res.json()["is_bookmarked"] is True

    # List: message appears
    list_res = await auth_client.get("/api/bookmarks/")
    assert list_res.status_code == 200
    bookmarked_ids = [m["id"] for m in list_res.json()]
    assert message_id in bookmarked_ids, "Bookmarked message not found in list"

    # Remove via DELETE
    del_res = await auth_client.delete(f"/api/bookmarks/{message_id}")
    assert del_res.status_code == 200, f"DELETE failed: {del_res.status_code} {del_res.text[:200]}"
    assert del_res.json()["is_bookmarked"] is False

    # List: no longer present
    list_res2 = await auth_client.get("/api/bookmarks/")
    assert message_id not in [m["id"] for m in list_res2.json()]


# ---------------------------------------------------------------------------
# conversations.unit.009 — cross-user isolation
# ---------------------------------------------------------------------------


async def test_bookmark_isolation(tenant_pair):
    """User B: GET sees 0 bookmarks; DELETE on User A's message → 404. (009)"""
    pair = tenant_pair

    with patch(_ORCHESTRATOR_PATH, new=AsyncMock(return_value=_MOCK_RESULT)):
        conv_id, _ = await make_conversation(pair.client_a, messages=("Consulta legal.",))

    detail = await pair.client_a.get(f"/api/conversations/{conv_id}")
    assert detail.status_code == 200
    message_id = detail.json()["messages"][0]["id"]

    # User A bookmarks the message
    put_res = await pair.client_a.put(f"/api/bookmarks/{message_id}")
    assert put_res.status_code == 200
    assert put_res.json()["is_bookmarked"] is True

    # User B: list returns empty (read isolation)
    list_b = await pair.client_b.get("/api/bookmarks/")
    assert list_b.status_code == 200
    assert list_b.json() == [], f"User B should see 0 bookmarks, got: {list_b.json()}"

    # User B: DELETE on User A's message → 404 (ownership gate)
    del_b = await pair.client_b.delete(f"/api/bookmarks/{message_id}")
    assert del_b.status_code == 404, (
        f"Expected 404 for cross-user DELETE, got {del_b.status_code} — "
        "bookmark ownership isolation may be missing"
    )
