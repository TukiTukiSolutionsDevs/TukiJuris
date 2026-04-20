"""Integration tests — documents admin-mutation guard (sub-batch E.2b).

Spec IDs covered:
  - documents-search.unit.015  test_document_metadata_crud_admin_only  [XFAIL — read-only route]

Route exercised:
  POST /api/documents/  — attempted mutation (does not exist — route is read-only)

NOTE: The documents route (app/api/routes/documents.py) exposes only GET endpoints:
  GET /api/documents/            — list documents
  GET /api/documents/search      — full-text search
  GET /api/documents/stats       — KB statistics
  GET /api/documents/{id}/chunks — chunks for a document

There are NO POST/PUT/DELETE mutation endpoints and NO require_admin dependency.
This test is XFAIL(strict=True) as a wave-3 placeholder for T-E-15 / FIX-02.

Root tests file (tests/test_documents.py) covers the GET surface.
This integration/ file covers the admin-mutation guard which is a missing feature.

Run with:
  docker exec tukijuris-api-1 pytest apps/api/tests/integration/test_documents.py -v --tb=short
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# documents-search.unit.015 — admin-only mutation guard
# XFAIL: documents route is read-only; no POST/PUT/DELETE endpoints; no
# require_admin dependency attached to any mutation. Missing feature, not bug.
# Wave-3 placeholder for T-E-15 / FIX-02 implementation.
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "documents route (app/api/routes/documents.py) is read-only — "
        "no POST/PUT/DELETE mutation endpoints exist and no require_admin guard is "
        "attached. Admin-gated document metadata CRUD is a missing feature (not a bug). "
        "Wave-3 placeholder; requires T-E-15 / FIX-02 implementation."
    ),
)
async def test_document_metadata_crud_admin_only(auth_client):
    """Non-admin user POSTs to /api/documents/ → must receive 403.

    Spec: documents-search.unit.015
    XFAIL: The route has no POST endpoint. A non-admin attempting to create a
    document should receive 403 (require_admin dep). Currently receives 405
    (Method Not Allowed) because the endpoint does not exist at all.
    Test will PASS (and become XPASS error) once the mutation endpoint + admin
    guard are implemented per FIX-02.
    """
    # Attempt to create a document as a regular (non-admin) user.
    # Once the feature is implemented this should return 403.
    # Currently returns 405 — causing this assertion to fail → xfail as expected.
    res = await auth_client.post(
        "/api/documents/",
        json={"title": "Ley de Prueba", "legal_area": "civil", "document_type": "ley"},
    )
    assert res.status_code == 403, (
        f"Expected 403 (require_admin), got {res.status_code}. "
        f"POST /api/documents/ endpoint likely does not exist yet."
    )
