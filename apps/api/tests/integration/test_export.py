"""Integration tests — export routes (sub-batch E.2b).

Spec IDs covered:
  - documents-search.unit.011  test_export_pdf_bytes_shape              [PASS]
  - documents-search.unit.012  test_export_consultation_ownership_403   [XFAIL — no GET route with msg_id]
  - documents-search.unit.013  test_export_conversation_ownership_404   [PASS]

Routes exercised:
  POST /api/export/conversation/pdf  — export conversation as PDF (body: {conversation_id})
  POST /api/export/consultation/pdf  — export raw consultation data as PDF

NOTE on spec vs reality:
  - Spec 011 references GET /api/export/conversation/{id} — actual route is
    POST /api/export/conversation/pdf with body {conversation_id: uuid}.
  - Spec 012 references GET /api/export/consultation/{message_id} — actual route is
    POST /api/export/consultation/pdf accepting raw payload with NO ownership gate.
    → test_012 is XFAIL(strict=True); wave-3 placeholder for T-E-15.

Run with:
  docker exec tukijuris-api-1 pytest apps/api/tests/integration/test_export.py -v --tb=short
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from tests.factories.conversation import make_conversation

# ---------------------------------------------------------------------------
# Orchestrator mock (needed only for conversation creation via POST /api/chat/query)
# Export route itself does NOT call the LLM.
# ---------------------------------------------------------------------------

_ORCHESTRATOR_PATH = "app.agents.orchestrator.legal_orchestrator.process_query"

_MOCK_RESULT = {
    "response": "Respuesta simulada para prueba de exportación.",
    "agent_used": "general",
    "legal_area": "general",
    "citations": [],
    "model_used": "mock-model",
    "tokens_used": 5,
}


# ---------------------------------------------------------------------------
# documents-search.unit.011 — PDF bytes shape
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_export_pdf_bytes_shape(auth_client):
    """POST /api/export/conversation/pdf → 200 + application/pdf + non-empty bytes.

    Spec: documents-search.unit.011
    Creates a real conversation (orchestrator patched), then exports it as PDF.
    Verifies content-type header and that the response body contains bytes
    (reportlab-generated PDF).
    """
    # Step 1: create a conversation (side-effect of chat query)
    with patch(_ORCHESTRATOR_PATH, AsyncMock(return_value=_MOCK_RESULT)):
        conv_id, _ = await make_conversation(auth_client, messages=("Tengo una consulta laboral.",))

    # Step 2: export the conversation as PDF — no LLM call needed here
    res = await auth_client.post(
        "/api/export/conversation/pdf",
        json={"conversation_id": conv_id},
    )

    assert res.status_code == 200, f"Expected 200, got {res.status_code}. Body: {res.text[:400]}"

    content_type = res.headers.get("content-type", "")
    assert "application/pdf" in content_type, (
        f"Expected application/pdf content-type, got: {content_type!r}"
    )
    assert len(res.content) > 0, "PDF response body must not be empty"


# ---------------------------------------------------------------------------
# documents-search.unit.012 — consultation ownership gate
# XFAIL: no GET /api/export/consultation/{message_id} route exists.
# POST /api/export/consultation/pdf accepts raw consultation payload (query +
# answer + metadata) without any message_id ownership check. Any authenticated
# user can export any data they supply themselves — no per-message gate.
# Wave-3 placeholder for T-E-15 ownership redesign.
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "No GET /api/export/consultation/{message_id} route; "
        "POST /api/export/consultation/pdf accepts raw JSON payload with no "
        "message ownership gate. Cross-tenant isolation N/A for this endpoint shape. "
        "Wave-3 placeholder; requires T-E-15 route redesign."
    ),
)
async def test_export_consultation_ownership_403(tenant_pair):
    """User B should NOT be able to export User A's consultation by message ID.

    Spec: documents-search.unit.012
    XFAIL: The actual route is POST /api/export/consultation/pdf which accepts
    a raw payload (query, answer, area, etc.) with no message_id reference.
    There is no ownership surface to guard — anyone can render any text as PDF.
    """
    assert False, (
        "GET /api/export/consultation/{message_id} route does not exist; "
        "POST /api/export/consultation/pdf has no ownership gate"
    )


# ---------------------------------------------------------------------------
# documents-search.unit.013 — conversation export ownership: 404 for non-owner
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_export_conversation_ownership_404(tenant_pair):
    """User B POSTs User A's conversation_id to /export/conversation/pdf → 404.

    Spec: documents-search.unit.013
    The route calls get_conversation_with_messages(db, conv_id, current_user.id)
    which filters by user_id — returns None for non-owners → 404.
    Verifies the isolation is enforced at the DB query level (no existence leak).
    """
    # Step 1: User A creates a conversation
    with patch(_ORCHESTRATOR_PATH, AsyncMock(return_value=_MOCK_RESULT)):
        conv_a_id, _ = await make_conversation(
            tenant_pair.client_a,
            messages=("Consulta sobre contrato de trabajo.",),
        )

    # Step 2: User B tries to export User A's conversation
    res = await tenant_pair.client_b.post(
        "/api/export/conversation/pdf",
        json={"conversation_id": conv_a_id},
    )

    assert res.status_code in (403, 404), (
        f"Expected 403 or 404 for cross-tenant export, got {res.status_code}. "
        f"Body: {res.text[:300]}"
    )
