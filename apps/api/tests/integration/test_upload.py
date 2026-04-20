"""Integration tests — upload route isolation (sub-batch E.2b).

Spec IDs covered:
  - documents-search.unit.014  test_upload_ownership_isolation  [PASS]

Route exercised:
  POST /api/upload/        — upload a document (requires auth)
  GET  /api/upload/{id}    — retrieve uploaded document (owner only → 404 for non-owner)

Isolation pattern: GET /{doc_id} filters by UploadedDocument.user_id == current_user.id
→ returns 404 (not 403) for non-owners, consistent with project convention (no existence leak).

Run with:
  docker exec tukijuris-api-1 pytest apps/api/tests/integration/test_upload.py -v --tb=short
"""

from __future__ import annotations

import pytest


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
