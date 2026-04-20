"""Integration tests — folder CRUD + cross-tenant isolation (sub-batch E.1b).

Spec IDs covered:
  - conversations.unit.012  test_folder_crud_isolation

Routes exercised:
  POST   /api/folders/           — create folder
  GET    /api/folders/           — list folders
  PUT    /api/folders/{id}       — update (cross-tenant probe → 404)

Run with:
  docker exec tukijuris-api-1 pytest tests/integration/test_folders.py -v --tb=short
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# conversations.unit.012 — folder CRUD + isolation
# ---------------------------------------------------------------------------


async def test_folder_crud_isolation(tenant_pair):
    """User A folder invisible and inaccessible to User B. (012)"""
    ca, cb = tenant_pair.client_a, tenant_pair.client_b

    # User A creates a folder
    create_res = await ca.post("/api/folders/", json={"name": "Carpeta de A", "icon": "folder"})
    assert create_res.status_code == 201, (
        f"Create failed: {create_res.status_code} {create_res.text[:200]}"
    )
    folder_a_id = create_res.json()["id"]

    # User A can see their own folder
    list_a = await ca.get("/api/folders/")
    assert list_a.status_code == 200
    assert folder_a_id in [f["id"] for f in list_a.json()], "Owner cannot see own folder"

    # User B list must NOT include folder_a
    list_b = await cb.get("/api/folders/")
    assert list_b.status_code == 200
    b_ids = [f["id"] for f in list_b.json()]
    assert folder_a_id not in b_ids, "Cross-tenant leak: User B sees User A's folder"

    # User B PUT on folder_a must return 404
    put_b = await cb.put(f"/api/folders/{folder_a_id}", json={"name": "Hacked"})
    assert put_b.status_code == 404, (
        f"Isolation breach on PUT: got {put_b.status_code}"
    )
