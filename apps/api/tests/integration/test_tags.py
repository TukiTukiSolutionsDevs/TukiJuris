"""Integration tests — tag CRUD + assign/unassign (sub-batch E.1b).

Spec IDs covered:
  - conversations.unit.010  test_tag_crud_happy_path
  - conversations.unit.011  test_tag_assign_unassign

Routes exercised:
  POST   /api/tags/                                   — create tag
  GET    /api/tags/                                   — list tags
  POST   /api/conversations/{conv_id}/tags/{tag_id}   — assign tag
  GET    /api/conversations/{conv_id}/tags            — list conv tags
  DELETE /api/conversations/{conv_id}/tags/{tag_id}   — unassign tag

Run with:
  docker exec tukijuris-api-1 pytest tests/integration/test_tags.py -v --tb=short
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from tests.factories.conversation import make_conversation

_MOCK_RESULT = {
    "response": "Respuesta simulada para pruebas de etiquetas.",
    "agent_used": "general",
    "legal_area": "general",
    "citations": [],
    "model_used": "mock-model",
    "tokens_used": 5,
}
_ORCHESTRATOR_PATH = "app.agents.orchestrator.legal_orchestrator.process_query"


# ---------------------------------------------------------------------------
# conversations.unit.010 — tag CRUD happy path
# ---------------------------------------------------------------------------


async def test_tag_crud_happy_path(auth_client):
    """POST creates tag; GET list includes it. (010)"""
    res = await auth_client.post("/api/tags/", json={"name": "urgente", "color": "#ef4444"})
    assert res.status_code == 201, f"POST failed: {res.status_code} {res.text[:200]}"
    tag = res.json()
    assert tag["name"] == "urgente"
    assert tag["color"] == "#ef4444"
    tag_id = tag["id"]

    list_res = await auth_client.get("/api/tags/")
    assert list_res.status_code == 200
    ids = [t["id"] for t in list_res.json()]
    assert tag_id in ids, "Created tag not found in list"


# ---------------------------------------------------------------------------
# conversations.unit.011 — tag assign / unassign
# ---------------------------------------------------------------------------


async def test_tag_assign_unassign(auth_client):
    """Assign tag → verify via GET; unassign → verify removed. (011)"""
    tag_res = await auth_client.post("/api/tags/", json={"name": "importante"})
    assert tag_res.status_code == 201
    tag_id = tag_res.json()["id"]

    with patch(_ORCHESTRATOR_PATH, new=AsyncMock(return_value=_MOCK_RESULT)):
        conv_id, _ = await make_conversation(auth_client, messages=("Consulta de prueba.",))

    assign = await auth_client.post(f"/api/conversations/{conv_id}/tags/{tag_id}")
    assert assign.status_code == 201, f"Assign failed: {assign.status_code} {assign.text[:200]}"

    tags_on_conv = await auth_client.get(f"/api/conversations/{conv_id}/tags")
    assert tags_on_conv.status_code == 200
    assert tag_id in [t["id"] for t in tags_on_conv.json()], "Assigned tag not found on conv"

    unassign = await auth_client.delete(f"/api/conversations/{conv_id}/tags/{tag_id}")
    assert unassign.status_code == 204, f"Unassign failed: {unassign.status_code} {unassign.text[:200]}"

    tags_after = await auth_client.get(f"/api/conversations/{conv_id}/tags")
    assert tags_after.status_code == 200
    assert all(t["id"] != tag_id for t in tags_after.json()), "Tag still linked after unassign"
