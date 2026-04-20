"""Integration tests — conversation write paths (sub-batch D.1).

Spec IDs covered:
  - conversations.unit.001  test_conversation_rename_owner_only
  - conversations.unit.002  test_conversation_pin_toggle
  - conversations.unit.003  test_conversation_archive_owner_only
  - conversations.unit.004  test_conversation_delete_cascades

Routes exercised:
  PUT /api/conversations/{id}/rename   — owner-only rename
  PUT /api/conversations/{id}/pin      — idempotent toggle
  PUT /api/conversations/{id}/archive  — owner-only archive
  DELETE /api/conversations/{id}       — hard delete + cascade

NOTE: routes use PUT (not PATCH) — confirmed from conversations.py route definitions.

LLM calls are patched at the orchestrator level (same pattern as test_chat_routes.py)
because the chat route calls legal_orchestrator.process_query(), not get_adapter().

Requirements: live Postgres + Redis (docker-compose up).

Run with:
  docker exec tukijuris-api-1 pytest tests/integration/test_conversations_write.py -v --tb=short
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

from tests.factories.conversation import make_conversation

# ---------------------------------------------------------------------------
# Shared orchestrator mock — mirrors the result contract from test_chat_routes.py
# ---------------------------------------------------------------------------

_MOCK_RESULT = {
    "response": "Respuesta simulada para pruebas de rutas de conversación.",
    "agent_used": "general",
    "legal_area": "general",
    "citations": [],
    "model_used": "mock-model",
    "tokens_used": 5,
}
_ORCHESTRATOR_PATH = "app.agents.orchestrator.legal_orchestrator.process_query"


# ---------------------------------------------------------------------------
# conversations.unit.001 — rename: owner-only write gate
# ---------------------------------------------------------------------------


async def test_conversation_rename_owner_only(tenant_pair):
    """PUT /rename: cross-tenant user → 404; owner → 200 + title persisted.

    Spec: conversations.unit.001
    Two independent orgs. User A owns the conversation; User B must receive 404
    (no existence leak). After the rejected cross-tenant attempt the title must
    be unchanged. Owner can rename successfully.
    """
    pair = tenant_pair

    with patch(_ORCHESTRATOR_PATH, new=AsyncMock(return_value=_MOCK_RESULT)):
        conv_id, _ = await make_conversation(pair.client_a)

    rename_path = f"/api/conversations/{conv_id}/rename"
    attacker_title = "Título del intruso"
    owner_title = "Contrato de compraventa — revisión inicial"

    # 1. Cross-tenant probe: User B cannot rename User A's conversation
    res_b = await pair.client_b.put(rename_path, json={"title": attacker_title})
    assert res_b.status_code == 404, (
        f"Expected 404 for cross-tenant rename, got {res_b.status_code}: {res_b.text[:200]}"
    )

    # 2. Integrity: attacker's title must NOT have leaked through
    res_check = await pair.client_a.get(f"/api/conversations/{conv_id}")
    assert res_check.status_code == 200
    assert res_check.json()["title"] != attacker_title, (
        "Attacker's title was persisted despite 404 — write-before-auth-check bug"
    )

    # 3. Owner renames successfully
    res_a = await pair.client_a.put(rename_path, json={"title": owner_title})
    assert res_a.status_code == 200, (
        f"Owner rename failed: {res_a.status_code}: {res_a.text[:200]}"
    )
    assert res_a.json()["title"] == owner_title


# ---------------------------------------------------------------------------
# conversations.unit.002 — pin: idempotent toggle
# ---------------------------------------------------------------------------


async def test_conversation_pin_toggle(auth_client):
    """PUT /pin: first call → is_pinned=True; second call → is_pinned=False.

    Spec: conversations.unit.002
    The pin endpoint is a toggle. Successive calls on the same conversation
    alternate between pinned and unpinned state.
    """
    with patch(_ORCHESTRATOR_PATH, new=AsyncMock(return_value=_MOCK_RESULT)):
        conv_id, _ = await make_conversation(auth_client)

    pin_path = f"/api/conversations/{conv_id}/pin"

    # First toggle: pin the conversation
    res_pin = await auth_client.put(pin_path)
    assert res_pin.status_code == 200, (
        f"First pin call failed: {res_pin.status_code}: {res_pin.text[:200]}"
    )
    assert res_pin.json()["is_pinned"] is True, (
        "Expected is_pinned=True after first toggle"
    )

    # Second toggle: unpin the conversation
    res_unpin = await auth_client.put(pin_path)
    assert res_unpin.status_code == 200, (
        f"Second pin call failed: {res_unpin.status_code}: {res_unpin.text[:200]}"
    )
    assert res_unpin.json()["is_pinned"] is False, (
        "Expected is_pinned=False after second toggle"
    )


# ---------------------------------------------------------------------------
# conversations.unit.003 — archive: owner-only write gate
# ---------------------------------------------------------------------------


async def test_conversation_archive_owner_only(tenant_pair):
    """PUT /archive: cross-tenant user → 404; owner → 200 + is_archived=True.

    Spec: conversations.unit.003
    Mirrors the rename isolation pattern. Verifies that cross-tenant archive
    attempts are rejected and the archive state is properly set for the owner.
    """
    pair = tenant_pair

    with patch(_ORCHESTRATOR_PATH, new=AsyncMock(return_value=_MOCK_RESULT)):
        conv_id, _ = await make_conversation(pair.client_a)

    archive_path = f"/api/conversations/{conv_id}/archive"

    # 1. Cross-tenant probe: User B cannot archive User A's conversation
    res_b = await pair.client_b.put(archive_path)
    assert res_b.status_code == 404, (
        f"Expected 404 for cross-tenant archive, got {res_b.status_code}: {res_b.text[:200]}"
    )

    # 2. Integrity: conversation must still be non-archived after rejected attempt
    res_check = await pair.client_a.get(f"/api/conversations/{conv_id}")
    assert res_check.status_code == 200
    assert res_check.json()["is_archived"] is False, (
        "Conversation was archived despite attacker receiving 404 — write-before-auth-check bug"
    )

    # 3. Owner archives successfully
    res_a = await pair.client_a.put(archive_path)
    assert res_a.status_code == 200, (
        f"Owner archive failed: {res_a.status_code}: {res_a.text[:200]}"
    )
    assert res_a.json()["is_archived"] is True


# ---------------------------------------------------------------------------
# conversations.unit.004 — delete: hard delete + cascade
# ---------------------------------------------------------------------------


async def test_conversation_delete_cascades(auth_client, db_session):
    """DELETE: 204 → GET 404 → DB message count drops to 0.

    Spec: conversations.unit.004
    Seeds a conversation with two chat turns (4 DB message rows: 2 user + 2 assistant),
    hard-deletes via the API, then verifies both the HTTP surface and the DB row count.
    Cascade delete is enforced at the DB level — this test pins that contract.
    """
    from sqlalchemy import func, select

    from app.models.conversation import Message

    # Seed: two chat turns → 4 messages (user+assistant × 2)
    with patch(_ORCHESTRATOR_PATH, new=AsyncMock(return_value=_MOCK_RESULT)):
        conv_id, _ = await make_conversation(
            auth_client,
            messages=("Primera consulta legal.", "Segunda consulta legal."),
        )

    conv_uuid = uuid.UUID(conv_id)

    # Pre-condition: messages exist in DB before deletion
    count_before = (
        await db_session.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conv_uuid)
        )
    ).scalar()
    assert count_before > 0, (
        f"Expected messages before delete, found {count_before} — seed may have failed"
    )

    # DELETE: hard delete via API
    res_delete = await auth_client.delete(f"/api/conversations/{conv_id}")
    assert res_delete.status_code == 204, (
        f"Expected 204 for delete, got {res_delete.status_code}: {res_delete.text[:200]}"
    )

    # HTTP surface: conversation no longer accessible after deletion
    res_get = await auth_client.get(f"/api/conversations/{conv_id}")
    assert res_get.status_code == 404, (
        f"Expected 404 after delete, got {res_get.status_code}: {res_get.text[:200]}"
    )

    # DB surface: all message rows for this conversation are gone (CASCADE DELETE)
    count_after = (
        await db_session.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conv_uuid)
        )
    ).scalar()
    assert count_after == 0, (
        f"Expected 0 messages after delete, found {count_after} — "
        "DB cascade may be missing or not committed"
    )
