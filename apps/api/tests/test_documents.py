"""
Tests for document and knowledge-base endpoints.

GET /api/documents/              — list all documents
GET /api/documents/search?q=...  — full-text BM25 search
GET /api/documents/stats         — KB statistics
GET /api/documents/{id}/chunks   — chunks for a specific document

These are read-only endpoints. They do not require authentication and
work whether the DB has seeded data or not (they return empty results
rather than errors when the KB is empty).
"""

import uuid

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# List documents
# ---------------------------------------------------------------------------


async def test_list_documents_returns_200(client: AsyncClient):
    """GET /api/documents/ returns 200 with a list."""
    res = await client.get("/api/documents/")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


async def test_list_documents_area_filter(client: AsyncClient):
    """GET /api/documents/?area=laboral returns only laboral documents."""
    res = await client.get("/api/documents/?area=laboral")
    assert res.status_code == 200
    docs = res.json()
    for doc in docs:
        assert doc["legal_area"] == "laboral"


async def test_list_documents_unknown_area_returns_empty(client: AsyncClient):
    """Filtering by a non-existent area returns an empty list (not an error)."""
    res = await client.get("/api/documents/?area=nonexistent_area_xyz")
    assert res.status_code == 200
    assert res.json() == []


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


async def test_search_returns_200(client: AsyncClient):
    """GET /api/documents/search?q=despido returns 200 with a list."""
    res = await client.get("/api/documents/search?q=despido")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


async def test_search_results_have_required_fields(client: AsyncClient):
    """Each search result has content, legal_area, score, and document_title."""
    res = await client.get("/api/documents/search?q=constitucion")
    assert res.status_code == 200
    for result in res.json():
        assert "content" in result
        assert "legal_area" in result
        assert "score" in result
        assert "document_title" in result


async def test_search_with_area_filter(client: AsyncClient):
    """Search can be filtered by legal area."""
    res = await client.get("/api/documents/search?q=contrato&area=civil")
    assert res.status_code == 200
    for result in res.json():
        assert result["legal_area"] == "civil"


async def test_search_with_custom_limit(client: AsyncClient):
    """Search respects the limit parameter."""
    res = await client.get("/api/documents/search?q=ley&limit=3")
    assert res.status_code == 200
    results = res.json()
    assert len(results) <= 3


async def test_search_query_too_short_returns_422(client: AsyncClient):
    """Query shorter than 2 characters is rejected with 422."""
    res = await client.get("/api/documents/search?q=a")
    assert res.status_code == 422


async def test_search_missing_query_returns_422(client: AsyncClient):
    """Calling /api/documents/search without q returns 422."""
    res = await client.get("/api/documents/search")
    assert res.status_code == 422


async def test_search_limit_too_large_returns_422(client: AsyncClient):
    """limit > 50 is rejected with 422."""
    res = await client.get("/api/documents/search?q=ley&limit=100")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


async def test_stats_returns_200(client: AsyncClient):
    """GET /api/documents/stats returns 200."""
    res = await client.get("/api/documents/stats")
    assert res.status_code == 200


async def test_stats_has_required_fields(client: AsyncClient):
    """Stats response includes total_documents, total_chunks, chunks_by_area."""
    res = await client.get("/api/documents/stats")
    data = res.json()
    assert "total_documents" in data
    assert "total_chunks" in data
    assert "chunks_by_area" in data


async def test_stats_chunks_by_area_is_dict(client: AsyncClient):
    """chunks_by_area is a dictionary."""
    res = await client.get("/api/documents/stats")
    assert isinstance(res.json()["chunks_by_area"], dict)


# ---------------------------------------------------------------------------
# Chunks by document ID
# ---------------------------------------------------------------------------


async def test_chunks_invalid_uuid_returns_400(client: AsyncClient):
    """GET /api/documents/not-a-uuid/chunks returns 400."""
    res = await client.get("/api/documents/not-a-valid-uuid/chunks")
    assert res.status_code == 400


async def test_chunks_nonexistent_document_returns_404(client: AsyncClient):
    """GET /api/documents/{random_uuid}/chunks returns 404."""
    fake_id = uuid.uuid4()
    res = await client.get(f"/api/documents/{fake_id}/chunks")
    assert res.status_code == 404
