"""
Tests for feedback endpoints.

POST /api/feedback/       — submit thumbs_up / thumbs_down on a message
GET  /api/feedback/stats  — aggregated feedback counts

Note: The submit endpoint writes to an existing Message row (by message_id).
When tested without seeded data, the UPDATE is a no-op (affects 0 rows)
but the endpoint still returns 200 with status "ok". Invalid feedback
types return status "error" in the body (HTTP 200) — this is by design.
"""

import uuid

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# POST /api/feedback/
# ---------------------------------------------------------------------------


async def test_submit_feedback_thumbs_up_returns_200(auth_client: AsyncClient):
    """Submitting thumbs_up for any message_id returns 200 with status ok."""
    res = await auth_client.post(
        "/api/feedback/",
        json={
            "message_id": str(uuid.uuid4()),
            "feedback": "thumbs_up",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["feedback"] == "thumbs_up"


async def test_submit_feedback_thumbs_down_returns_200(auth_client: AsyncClient):
    """Submitting thumbs_down returns 200 with status ok."""
    res = await auth_client.post(
        "/api/feedback/",
        json={
            "message_id": str(uuid.uuid4()),
            "feedback": "thumbs_down",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["feedback"] == "thumbs_down"


async def test_submit_feedback_invalid_type_returns_error_in_body(auth_client: AsyncClient):
    """
    Invalid feedback value ('love', 'hate', etc.) returns HTTP 200 but
    status 'error' and feedback 'invalid' in the response body.
    This is the current API contract (soft validation, not HTTP error).
    """
    res = await auth_client.post(
        "/api/feedback/",
        json={
            "message_id": str(uuid.uuid4()),
            "feedback": "love",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "error"
    assert data["feedback"] == "invalid"


async def test_submit_feedback_with_comment(auth_client: AsyncClient):
    """Feedback with an optional comment is accepted."""
    res = await auth_client.post(
        "/api/feedback/",
        json={
            "message_id": str(uuid.uuid4()),
            "feedback": "thumbs_down",
            "comment": "La respuesta fue incorrecta sobre el plazo de prescripcion",
        },
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


async def test_submit_feedback_missing_message_id_returns_422(auth_client: AsyncClient):
    """Missing message_id field returns 422."""
    res = await auth_client.post(
        "/api/feedback/",
        json={"feedback": "thumbs_up"},
    )
    assert res.status_code == 422


async def test_submit_feedback_invalid_uuid_returns_422(auth_client: AsyncClient):
    """Non-UUID message_id returns 422."""
    res = await auth_client.post(
        "/api/feedback/",
        json={"message_id": "not-a-uuid", "feedback": "thumbs_up"},
    )
    assert res.status_code == 422


async def test_submit_feedback_missing_feedback_field_returns_422(auth_client: AsyncClient):
    """Missing feedback field returns 422."""
    res = await auth_client.post(
        "/api/feedback/",
        json={"message_id": str(uuid.uuid4())},
    )
    assert res.status_code == 422


async def test_submit_feedback_response_echoes_message_id(auth_client: AsyncClient):
    """The response body echoes back the submitted message_id."""
    msg_id = str(uuid.uuid4())
    res = await auth_client.post(
        "/api/feedback/",
        json={"message_id": msg_id, "feedback": "thumbs_up"},
    )
    assert res.status_code == 200
    assert res.json()["message_id"] == msg_id


# ---------------------------------------------------------------------------
# GET /api/feedback/stats
# ---------------------------------------------------------------------------


async def test_feedback_stats_returns_200(client: AsyncClient):
    """GET /api/feedback/stats returns 200."""
    res = await client.get("/api/feedback/stats")
    assert res.status_code == 200


async def test_feedback_stats_has_required_keys(client: AsyncClient):
    """Stats response has total_feedback, thumbs_up, thumbs_down."""
    res = await client.get("/api/feedback/stats")
    data = res.json()
    assert "total_feedback" in data
    assert "thumbs_up" in data
    assert "thumbs_down" in data


async def test_feedback_stats_counts_are_non_negative(client: AsyncClient):
    """All count values in stats are non-negative integers."""
    res = await client.get("/api/feedback/stats")
    data = res.json()
    assert data["total_feedback"] >= 0
    assert data["thumbs_up"] >= 0
    assert data["thumbs_down"] >= 0


async def test_feedback_stats_satisfaction_rate_type(client: AsyncClient):
    """satisfaction_rate is either None (no data) or a float 0-100."""
    res = await client.get("/api/feedback/stats")
    rate = res.json().get("satisfaction_rate")
    if rate is not None:
        assert isinstance(rate, float)
        assert 0.0 <= rate <= 100.0


# ---------------------------------------------------------------------------
# Cross-tenant isolation
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "feedback route does not enforce message ownership — "
        "any authenticated user can submit feedback on any message_id. "
        "Route does UPDATE Message WHERE id=? with no user_id join. "
        "Cross-tenant write allowed. Deferred to wave-2 fix (T-D-11 territory). "
        "See engram: tukijuris/conversations-feedback-ownership-bug."
    ),
)
async def test_feedback_submit_cross_tenant_isolation(tenant_pair):
    """User B cannot submit feedback on a message owned by User A.

    Spec: conversations.unit.015
    Seeds a real message via the HTTP chat flow (User A → POST /api/chat/query →
    conversation + messages persisted to DB), then asserts that User B's POST
    to /api/feedback/ on that message_id returns 403 or 404.

    XFAIL (strict): the current submit_feedback route has no ownership check.
    It does UPDATE Message SET feedback=? WHERE id=? — no join to conversations
    or users. Any authenticated user can rate any message. Bug is pinned here;
    fix is deferred.
    """
    from unittest.mock import AsyncMock, patch

    from tests.factories.conversation import make_conversation

    pair = tenant_pair

    _MOCK = {
        "response": "Respuesta simulada.",
        "agent_used": "general",
        "legal_area": "general",
        "citations": [],
        "model_used": "mock-model",
        "tokens_used": 5,
    }
    _ORCH = "app.agents.orchestrator.legal_orchestrator.process_query"

    # Seed: User A creates a conversation — persists real message rows to DB
    with patch(_ORCH, new=AsyncMock(return_value=_MOCK)):
        conv_id, _ = await make_conversation(pair.client_a)

    # Fetch the conversation detail to obtain a real persisted message ID
    res = await pair.client_a.get(f"/api/conversations/{conv_id}")
    assert res.status_code == 200, f"Failed to fetch seeded conversation: {res.text[:200]}"
    messages = res.json()["messages"]
    assert messages, "No messages found in seeded conversation — seed may have failed"
    message_id = messages[0]["id"]

    # Cross-tenant probe: User B attempts to submit feedback on User A's message
    res_b = await pair.client_b.post(
        "/api/feedback/",
        json={"message_id": message_id, "feedback": "thumbs_down"},
    )
    # DESIRED behavior: 403 (not your resource) or 404 (existence hidden)
    # ACTUAL behavior (bug): 200 — route has no ownership check → xfail fires
    assert res_b.status_code in (403, 404), (
        f"Expected 403/404 for cross-tenant feedback, got {res_b.status_code}: {res_b.text[:200]}"
    )
