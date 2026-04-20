"""
Tests for health-check endpoints.

All health endpoints are exempt from rate limiting and do not require
authentication. They should always return 200 regardless of DB state
(degraded DB returns {"status": "degraded"} rather than an HTTP error).
"""

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# /api/health
# ---------------------------------------------------------------------------


async def test_health_basic(client: AsyncClient):
    """GET /api/health returns 200 with status ok."""
    res = await client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "service" in data


# ---------------------------------------------------------------------------
# /api/health/db
# ---------------------------------------------------------------------------


async def test_health_db_returns_200(client: AsyncClient):
    """GET /api/health/db always returns HTTP 200 (DB errors are in body)."""
    res = await client.get("/api/health/db")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["status"] in ("ok", "error")


async def test_health_db_has_database_key(client: AsyncClient):
    """GET /api/health/db response includes a 'database' key."""
    res = await client.get("/api/health/db")
    assert "database" in res.json()


# ---------------------------------------------------------------------------
# /api/health/ready
# ---------------------------------------------------------------------------


async def test_health_ready_returns_200(client: AsyncClient):
    """GET /api/health/ready always returns HTTP 200."""
    res = await client.get("/api/health/ready")
    assert res.status_code == 200


async def test_health_ready_has_checks(client: AsyncClient):
    """GET /api/health/ready includes a checks dict."""
    res = await client.get("/api/health/ready")
    data = res.json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded", "error")
    assert "checks" in data


# ---------------------------------------------------------------------------
# /api/health/knowledge
# ---------------------------------------------------------------------------


async def test_health_knowledge_returns_200(client: AsyncClient):
    """GET /api/health/knowledge always returns HTTP 200."""
    res = await client.get("/api/health/knowledge")
    assert res.status_code == 200


async def test_health_knowledge_has_status(client: AsyncClient):
    """GET /api/health/knowledge response has a status field."""
    res = await client.get("/api/health/knowledge")
    data = res.json()
    assert "status" in data


# ---------------------------------------------------------------------------
# / (root)
# ---------------------------------------------------------------------------


async def test_root_returns_app_info(client: AsyncClient):
    """GET / returns app name, version, and documentation links."""
    res = await client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Agente Derecho"
    assert "version" in data
    assert "docs" in data
    assert "health" in data


async def test_root_version_format(client: AsyncClient):
    """GET / returns a non-empty version string."""
    res = await client.get("/")
    version = res.json()["version"]
    assert isinstance(version, str)
    assert len(version) > 0


# ---------------------------------------------------------------------------
# Agents listing (part of chat router, tested here as a smoke check)
# ---------------------------------------------------------------------------


async def test_list_agents_returns_all_11_domains(client: AsyncClient):
    """GET /api/chat/agents returns all 11 legal domain agents."""
    res = await client.get("/api/chat/agents")
    assert res.status_code == 200
    data = res.json()
    assert "agents" in data
    agent_ids = [a["id"] for a in data["agents"]]
    expected = {
        "civil", "penal", "laboral", "tributario", "constitucional",
        "administrativo", "corporativo", "registral", "competencia",
        "compliance", "comercio_exterior",
    }
    assert expected.issubset(set(agent_ids)), (
        f"Missing agents: {expected - set(agent_ids)}"
    )
    assert len(data["agents"]) == 11


# ---------------------------------------------------------------------------
# D.3 — Health probe coverage cluster (observability.unit.010–014)
# ---------------------------------------------------------------------------


async def test_health_liveness_probe(client: AsyncClient):
    """observability.unit.010 — /api/health returns 200 with status: ok."""
    res = await client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data.get("service") is not None


async def test_health_readiness_probe(client: AsyncClient):
    """observability.unit.011 — /api/health/ready + /api/health/db both 200 + active DB."""
    res_ready = await client.get("/api/health/ready")
    assert res_ready.status_code == 200
    ready = res_ready.json()
    assert ready["status"] in ("ok", "degraded")
    assert "checks" in ready
    assert ready["checks"].get("database") is not None

    res_db = await client.get("/api/health/db")
    assert res_db.status_code == 200
    db = res_db.json()
    assert db["status"] == "ok"
    assert db.get("database") == "connected"


async def test_health_metrics_endpoint_shape(client: AsyncClient):
    """observability.unit.012 — /api/health/metrics shape is valid (no crash, no host values)."""
    res = await client.get("/api/health/metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    m = data["metrics"]
    assert isinstance(m["total_requests"], int)
    assert isinstance(m["total_errors"], int)
    assert isinstance(m["error_rate_pct"], (int, float))
    assert isinstance(m["avg_latency_ms"], (int, float))
    assert isinstance(m["slow_requests"], int)
    assert isinstance(m["status_codes"], dict)
    assert isinstance(m["slowest_endpoints"], list)


async def test_health_cache_redis_stats(client: AsyncClient):
    """observability.unit.013 — /api/health/cache returns Redis PING success."""
    res = await client.get("/api/health/cache")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "keys" in data
    assert "memory_used" in data
    assert "memory_peak" in data


async def test_health_rate_limit_bucket_observation(client: AsyncClient):
    """observability.unit.014 — /api/health hammered 100× must never yield 429."""
    for _ in range(100):
        res = await client.get("/api/health")
        assert res.status_code != 429, (
            f"/api/health returned 429 — endpoint must be rate-limit exempt. "
            f"body={res.text}"
        )
