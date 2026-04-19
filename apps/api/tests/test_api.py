"""
Legacy smoke tests — kept for backwards compatibility.

These are the original integration tests. The comprehensive suite has been
split into dedicated modules:
  - test_health.py
  - test_auth.py
  - test_organizations.py
  - test_billing.py
  - test_documents.py
  - test_feedback.py
  - test_conversations.py
  - test_rate_limiting.py

The tests below now use the shared fixtures from conftest.py.
"""

import pytest
from httpx import AsyncClient


# === Root ===


async def test_root(client: AsyncClient):
    r = await client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "Agente Derecho"


async def test_health(client: AsyncClient):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# === Auth ===


async def test_register_and_login(client: AsyncClient):
    """Register a fresh user and immediately log in."""
    import uuid
    email = f"smoke-{uuid.uuid4().hex[:8]}@test.com"
    password = "SmokePw123!"

    r = await client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Smoke Test User",
    })
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    r = await client.post("/api/auth/login", json={
        "email": email,
        "password": password,
    })
    assert r.status_code == 200
    assert "access_token" in r.json()


async def test_login_wrong_password(client: AsyncClient):
    """Login with wrong password returns 401 or 500 (no DB = 500 is ok)."""
    r = await client.post("/api/auth/login", json={
        "email": "pytest@test.com",
        "password": "wrong_password",
    })
    assert r.status_code in (401, 500)


# === Agents ===


async def test_list_agents(client: AsyncClient):
    r = await client.get("/api/chat/agents")
    assert r.status_code == 200
    agents = r.json()["agents"]
    assert len(agents) == 11
    ids = [a["id"] for a in agents]
    for expected_id in [
        "civil", "penal", "laboral", "tributario", "constitucional",
        "administrativo", "corporativo", "registral", "competencia",
        "compliance", "comercio_exterior",
    ]:
        assert expected_id in ids


# === Documents ===


async def test_document_search(client: AsyncClient):
    r = await client.get("/api/documents/search?q=despido+arbitrario&limit=3")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


async def test_list_documents(client: AsyncClient):
    r = await client.get("/api/documents/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


async def test_document_stats(client: AsyncClient):
    r = await client.get("/api/documents/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_documents" in data
    assert "total_chunks" in data
    assert "chunks_by_area" in data


# === Feedback ===


async def test_feedback_stats(client: AsyncClient):
    r = await client.get("/api/feedback/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_feedback" in data
    assert "thumbs_up" in data
    assert "thumbs_down" in data
