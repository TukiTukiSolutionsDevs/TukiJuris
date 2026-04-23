"""Integration tests — upload route isolation (sub-batch E.2b) + list endpoint.

Spec IDs covered:
  - documents-search.unit.014  test_upload_ownership_isolation        [PASS]
  - BE-UPLOAD-LIST             test_list_uploads_populated            [new]
  - BE-UPLOAD-LIST             test_list_uploads_empty                [new]
  - BE-UPLOAD-LIST             test_list_uploads_excludes_private_fields [new]

Routes exercised:
  POST /api/upload/        — upload a document (requires auth)
  GET  /api/upload/        — list user documents (newest-first, safe fields only)
  GET  /api/upload/{id}    — retrieve uploaded document (owner only → 404 for non-owner)

Run with:
  docker exec tukijuris-api-1 pytest apps/api/tests/integration/test_upload.py -v --tb=short
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# BE-UPLOAD-LIST — GET /api/upload/ list endpoint tests
# ---------------------------------------------------------------------------

_TXT_A = ("doc-alpha.txt", b"Contenido del documento alfa.", "text/plain")
_TXT_B = ("doc-beta.txt", b"Contenido del documento beta.", "text/plain")

_ALLOWED_FIELDS = {"id", "filename", "file_type", "file_size", "page_count", "conversation_id", "created_at"}
_PRIVATE_FIELDS = {"storage_path", "extracted_text"}


@pytest.mark.integration
async def test_list_uploads_populated(auth_client):
    """GET /api/upload/ returns uploads newest-first with only the 7 whitelisted fields.

    Spec: BE-UPLOAD-LIST
    Uploads two text documents sequentially; expects the second to appear first
    in the response (created_at DESC ordering) and verifies the response shape.
    """
    # Upload doc A first, then doc B (B has a later created_at)
    res_a = await auth_client.post("/api/upload/", files={"file": _TXT_A})
    assert res_a.status_code == 200, f"Upload A failed: {res_a.text[:200]}"
    id_a = res_a.json()["id"]

    res_b = await auth_client.post("/api/upload/", files={"file": _TXT_B})
    assert res_b.status_code == 200, f"Upload B failed: {res_b.text[:200]}"
    id_b = res_b.json()["id"]

    list_res = await auth_client.get("/api/upload/")
    assert list_res.status_code == 200, f"List failed: {list_res.text[:200]}"

    items = list_res.json()
    assert isinstance(items, list)
    assert len(items) >= 2

    ids = [item["id"] for item in items]
    assert id_b in ids and id_a in ids, "Both uploaded docs must appear in the list"

    # Newest-first: B was uploaded after A, so B must appear before A
    assert ids.index(id_b) < ids.index(id_a), (
        f"Expected newest-first ordering: id_b={id_b} should precede id_a={id_a}. "
        f"Got order: {ids}"
    )

    # Shape check on first item
    first = items[0]
    assert set(first.keys()) == _ALLOWED_FIELDS, (
        f"Response keys mismatch. Expected: {_ALLOWED_FIELDS}, got: {set(first.keys())}"
    )


@pytest.mark.integration
async def test_list_uploads_empty(auth_client):
    """GET /api/upload/ returns [] when the user has no uploaded documents.

    Spec: BE-UPLOAD-LIST — empty-list branch.
    Uses a fresh auth_client (unique user per test) so no prior uploads exist.
    """
    list_res = await auth_client.get("/api/upload/")
    assert list_res.status_code == 200, f"List failed: {list_res.text[:200]}"
    items = list_res.json()
    assert items == [], f"Expected empty list, got: {items}"


@pytest.mark.integration
async def test_list_uploads_excludes_private_fields(auth_client):
    """GET /api/upload/ MUST NOT include storage_path or extracted_text.

    Spec: BE-UPLOAD-LIST — security assertion (critical).
    Verifies the explicit field-whitelist in UploadedDocumentListItem prevents
    leaking the on-disk path and raw extracted text to clients.
    """
    res = await auth_client.post("/api/upload/", files={"file": _TXT_A})
    assert res.status_code == 200, f"Upload failed: {res.text[:200]}"

    list_res = await auth_client.get("/api/upload/")
    assert list_res.status_code == 200

    items = list_res.json()
    assert len(items) >= 1

    for item in items:
        for private_field in _PRIVATE_FIELDS:
            assert private_field not in item, (
                f"SECURITY VIOLATION: '{private_field}' must never appear in "
                f"GET /api/upload/ response. Found in item: {item}"
            )


# ---------------------------------------------------------------------------
# documents-search.unit.014 — upload ownership isolation
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_upload_ownership_isolation(tenant_pair):
    """User B GET /api/upload/{doc_a_id} → 404 (User A's document not accessible).

    Spec: documents-search.unit.014
    Uploads a text file as User A, then verifies User B receives 404 when
    attempting to retrieve it. The GET handler filters by user_id at the DB
    query level — non-owners get 404 (no existence leak), not 403.
    """
    # Step 1: User A uploads a text document
    upload_res = await tenant_pair.client_a.post(
        "/api/upload/",
        files={"file": ("prueba-aislamiento.txt", b"Contenido de prueba para test de aislamiento.", "text/plain")},
    )
    assert upload_res.status_code == 200, (
        f"User A upload failed: {upload_res.status_code} {upload_res.text[:300]}"
    )
    doc_a_id = upload_res.json()["id"]
    assert doc_a_id, "Upload response must include an 'id' field"

    # Step 2: User A can access their own document (owner sanity check)
    owner_res = await tenant_pair.client_a.get(f"/api/upload/{doc_a_id}")
    assert owner_res.status_code == 200, (
        f"Owner should get 200 on GET /api/upload/{doc_a_id}, got {owner_res.status_code}"
    )

    # Step 3: User B must NOT access User A's document
    attacker_res = await tenant_pair.client_b.get(f"/api/upload/{doc_a_id}")
    assert attacker_res.status_code == 404, (
        f"Expected 404 for cross-tenant upload access, got {attacker_res.status_code}. "
        f"Body: {attacker_res.text[:300]}"
    )
