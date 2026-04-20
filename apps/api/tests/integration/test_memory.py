"""Integration tests — memory CRUD + isolation (sub-batch E.1b).

Spec IDs covered:
  - conversations.unit.013  test_memory_crud_happy_path  [XFAIL — no POST endpoint]
  - conversations.unit.014  test_memory_isolation

Routes exercised:
  GET    /api/memory/   — list memories (grouped by category)

Run with:
  docker exec tukijuris-api-1 pytest tests/integration/test_memory.py -v --tb=short
"""
from __future__ import annotations

import uuid

import pytest


# ---------------------------------------------------------------------------
# conversations.unit.013 — memory CRUD happy path
# XFAIL: no POST /memory/ endpoint exists in V1 (auto-extraction only)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "No POST /memory/ endpoint; facts are auto-extracted from conversations only. "
        "Missing feature, not bug — direct memory creation not in V1 spec."
    ),
)
async def test_memory_crud_happy_path(auth_client):
    """POST saves fact → GET lists it. XFAIL: no direct POST endpoint. (013)"""
    res = await auth_client.post(
        "/api/memory/",
        json={"category": "profession", "content": "Abogado especialista en derecho laboral"},
    )
    assert res.status_code == 201, f"Expected 201, got {res.status_code}"
    fact_id = res.json()["id"]

    list_res = await auth_client.get("/api/memory/")
    assert list_res.status_code == 200
    all_ids = [m["id"] for g in list_res.json()["groups"] for m in g["memories"]]
    assert fact_id in all_ids, "Saved fact not found in list"


# ---------------------------------------------------------------------------
# conversations.unit.014 — memory isolation
# Seed via service (no HTTP POST); verify User B cannot see User A's memories.
# ---------------------------------------------------------------------------


async def test_memory_isolation(tenant_pair, db_session):
    """User B GET /memory/ returns 0 items from User A's seeded memory. (014)"""
    ca, cb = tenant_pair.client_a, tenant_pair.client_b

    # Resolve User A's ID via /api/auth/me
    me_res = await ca.get("/api/auth/me")
    assert me_res.status_code == 200, f"GET /api/auth/me failed: {me_res.status_code} {me_res.text[:200]}"
    user_a_id = uuid.UUID(me_res.json()["id"])

    # Seed a memory for User A directly via service (no POST /memory/ endpoint)
    from app.services.memory_service import memory_service

    saved = await memory_service.save_memories(
        user_id=user_a_id,
        memories=[{"category": "profession", "content": "Abogado corporativo en Lima"}],
        conversation_id=None,
        db=db_session,
    )
    assert saved >= 1, "Service failed to seed memory for User A"

    # User A sees their own memory
    mem_a = await ca.get("/api/memory/")
    assert mem_a.status_code == 200
    assert mem_a.json()["total"] >= 1, "User A's seeded memory not visible to themselves"

    # User B must see 0 (isolation)
    mem_b = await cb.get("/api/memory/")
    assert mem_b.status_code == 200
    total_b = mem_b.json()["total"]
    assert total_b == 0, f"Cross-tenant leak: User B sees {total_b} of User A's memories"
