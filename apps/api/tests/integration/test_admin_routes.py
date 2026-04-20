"""Integration tests — admin route non-admin 403 guards.

Spec IDs: admin-rbac.int.001, admin-rbac.int.002, admin-rbac.int.003
Layer: integration

Standard users (no RBAC roles) get 403 on /api/admin/users, /activity, /knowledge.
No FIX-02 required — require_permission() fires before _ensure_admin() for users
that have no RBAC roles at all.

Run: docker exec tukijuris-api-1 pytest apps/api/tests/integration/test_admin_routes.py -v
"""
from __future__ import annotations


class TestAdminRoutesNonAdminRejected:
    """admin-rbac.int.001..003 — standard user → 403 on admin-only routes."""

    async def test_admin_users_non_admin_403(self, auth_client):
        """admin-rbac.int.001: GET /api/admin/users rejects non-admin with 403."""
        res = await auth_client.get("/api/admin/users")
        assert res.status_code == 403, res.text

    async def test_admin_activity_non_admin_403(self, auth_client):
        """admin-rbac.int.002: GET /api/admin/activity rejects non-admin with 403."""
        res = await auth_client.get("/api/admin/activity")
        assert res.status_code == 403, res.text

    async def test_admin_knowledge_non_admin_403(self, auth_client):
        """admin-rbac.int.003: GET /api/admin/knowledge rejects non-admin with 403."""
        res = await auth_client.get("/api/admin/knowledge")
        assert res.status_code == 403, res.text
