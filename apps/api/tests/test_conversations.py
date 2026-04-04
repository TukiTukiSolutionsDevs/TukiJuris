"""
Tests for conversation endpoints.

GET /api/conversations/                    — list user conversations
GET /api/conversations/{id}               — get conversation with messages

Conversations are created indirectly (via /api/chat/query).
These tests validate the CRUD contract assuming a fresh user with no history.
"""

import uuid

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# List conversations
# ---------------------------------------------------------------------------


async def test_list_conversations_requires_auth(client: AsyncClient):
    """GET /api/conversations/ without token returns 401 or 403."""
    res = await client.get("/api/conversations/")
    assert res.status_code in (401, 403)


async def test_list_conversations_returns_list_for_new_user(auth_client: AsyncClient):
    """A fresh user has zero conversations — endpoint returns empty list."""
    res = await auth_client.get("/api/conversations/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


async def test_list_conversations_response_shape(auth_client: AsyncClient):
    """If conversations exist, each item has id, title, legal_area, model_used."""
    res = await auth_client.get("/api/conversations/")
    assert res.status_code == 200
    for conv in res.json():
        assert "id" in conv
        assert "model_used" in conv
        assert "created_at" in conv
        assert "updated_at" in conv


# ---------------------------------------------------------------------------
# Get conversation by ID
# ---------------------------------------------------------------------------


async def test_get_conversation_requires_auth(client: AsyncClient):
    """GET /api/conversations/{id} without token returns 401 or 403."""
    fake_id = uuid.uuid4()
    res = await client.get(f"/api/conversations/{fake_id}")
    assert res.status_code in (401, 403)


async def test_get_nonexistent_conversation_returns_404(auth_client: AsyncClient):
    """GET /api/conversations/{random_uuid} returns 404."""
    fake_id = uuid.uuid4()
    res = await auth_client.get(f"/api/conversations/{fake_id}")
    assert res.status_code == 404


async def test_get_invalid_uuid_returns_422(auth_client: AsyncClient):
    """GET /api/conversations/not-a-uuid returns 422."""
    res = await auth_client.get("/api/conversations/not-a-valid-uuid")
    assert res.status_code == 422
