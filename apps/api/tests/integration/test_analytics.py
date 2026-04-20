"""Integration tests — analytics access-gate + aggregation + export (sub-batch D.2).

Spec IDs covered:
  observability.unit.001  test_analytics_overview_requires_org_admin
  observability.unit.002  test_analytics_system_admin_sees_all
  observability.unit.003  test_analytics_free_user_access_own_data_only
  observability.unit.004  test_analytics_queries_org_admin_only
  observability.unit.005  test_analytics_areas_breakdown
  observability.unit.006  test_analytics_top_queries_isolation
  observability.unit.007  test_analytics_export_csv_generation

Routes exercised:
  GET /api/analytics/{org_id}/overview
  GET /api/analytics/{org_id}/queries
  GET /api/analytics/{org_id}/areas
  GET /api/analytics/{org_id}/top-queries
  GET /api/analytics/{org_id}/export

NOTE: Analytics endpoints require org admin/owner role. Global system admins
(is_admin=True) bypass org-role gating via _assert_org_access in analytics.py.

Data seeding for aggregation tests (005-007): rows inserted directly via
db_session to avoid LLM mock complexity. Each test uses isolated tenant pairs
(fresh org UUIDs) so counts are always exact — no cross-test contamination.

Requirements: live Postgres + Redis (docker-compose up).

Run with:
  docker exec tukijuris-api-1 pytest tests/integration/test_analytics.py -v --tb=short
"""

from __future__ import annotations

import uuid

from sqlalchemy import select, update

from app.models.conversation import Conversation, Message
from app.models.user import User
from tests.factories.org import add_member


# ---------------------------------------------------------------------------
# observability.unit.001 — overview requires org admin role
# ---------------------------------------------------------------------------


async def test_analytics_overview_requires_org_admin(tenant_pair):
    """Org member (not admin) → 403 on /overview.

    Spec: observability.unit.001
    User B is explicitly invited as 'member' of Org A. The analytics overview
    endpoint requires admin or owner role — member role must be rejected with 403.
    """
    pair = tenant_pair
    org_a_id = pair.org_a["org_id"]

    # Invite owner_b as a plain member of org_a
    await add_member(pair.client_a, org_id=org_a_id, email=pair.owner_b["email"], role="member")

    res = await pair.client_b.get(f"/api/analytics/{org_a_id}/overview")
    assert res.status_code == 403, (
        f"Expected 403 for org member on analytics/overview, got {res.status_code}: {res.text[:200]}"
    )


# ---------------------------------------------------------------------------
# observability.unit.002 — global system admin bypasses org_role
# ---------------------------------------------------------------------------


async def test_analytics_system_admin_sees_all(tenant_pair, db_session):
    """Global is_admin=True bypasses org-role gating for any org.

    Spec: observability.unit.002
    User B has no membership in Org A. After elevating B to is_admin=True via
    the DB, B must receive 200 because _assert_org_access short-circuits on
    is_admin before calling require_org_role.
    """
    pair = tenant_pair
    org_a_id = pair.org_a["org_id"]

    # Elevate owner_b to global system admin (no org membership in org_a)
    await db_session.execute(
        update(User).where(User.email == pair.owner_b["email"]).values(is_admin=True)
    )
    await db_session.commit()

    # System admin (not a member of org_a) must access analytics without 403
    res = await pair.client_b.get(f"/api/analytics/{org_a_id}/overview")
    assert res.status_code == 200, (
        f"Expected 200 for system admin on analytics/overview, got {res.status_code}: {res.text[:200]}"
    )


# ---------------------------------------------------------------------------
# observability.unit.003 — free user: own org 200, foreign org 403
# ---------------------------------------------------------------------------


async def test_analytics_free_user_access_own_data_only(tenant_pair):
    """Org owner → 200 for own org; 403 for any org they don't belong to.

    Spec: observability.unit.003
    tenant_pair gives each user ownership of their own org (owner rank ≥ admin rank).
    The same user must be denied access to the other tenant's org.
    """
    pair = tenant_pair

    # Owner of org_a → 200 (owner role passes the admin-rank threshold)
    res_self = await pair.client_a.get(f"/api/analytics/{pair.org_a['org_id']}/overview")
    assert res_self.status_code == 200, (
        f"Expected 200 for org owner on own analytics, got {res_self.status_code}: {res_self.text[:200]}"
    )

    # Same user → 403 for org_b (no membership)
    res_other = await pair.client_a.get(f"/api/analytics/{pair.org_b['org_id']}/overview")
    assert res_other.status_code == 403, (
        f"Expected 403 for non-member on foreign analytics, got {res_other.status_code}: {res_other.text[:200]}"
    )


# ---------------------------------------------------------------------------
# observability.unit.004 — /queries endpoint: member 403, admin 200
# ---------------------------------------------------------------------------


async def test_analytics_queries_org_admin_only(tenant_pair):
    """Member role → 403; org owner → 200 on /queries.

    Spec: observability.unit.004
    Mirrors obs.unit.001 but targets the /queries time-series endpoint.
    Uses owner_a (owner rank) for the 200 case to avoid a separate admin invite.
    """
    pair = tenant_pair
    org_a_id = pair.org_a["org_id"]

    # Invite owner_b as a plain member of org_a
    await add_member(pair.client_a, org_id=org_a_id, email=pair.owner_b["email"], role="member")

    # Member → 403
    res_member = await pair.client_b.get(f"/api/analytics/{org_a_id}/queries")
    assert res_member.status_code == 403, (
        f"Expected 403 for member on analytics/queries, got {res_member.status_code}: {res_member.text[:200]}"
    )

    # Owner → 200
    res_owner = await pair.client_a.get(f"/api/analytics/{org_a_id}/queries")
    assert res_owner.status_code == 200, (
        f"Expected 200 for org owner on analytics/queries, got {res_owner.status_code}: {res_owner.text[:200]}"
    )


# ---------------------------------------------------------------------------
# observability.unit.005 — /areas breakdown: 5 labor + 2 civil
# ---------------------------------------------------------------------------


async def test_analytics_areas_breakdown(tenant_pair, db_session):
    """Org admin on /areas: grouped counts match seeded messages.

    Spec: observability.unit.005
    Seeds 5 assistant messages with legal_area='labor' and 2 with legal_area='civil'
    directly via db_session. Queries /areas and asserts grouped counts are exact.
    Fresh org UUID ensures no cross-test data pollution.
    """
    pair = tenant_pair
    org_a_id = uuid.UUID(pair.org_a["org_id"])

    # Resolve user_a UUID (org owner — satisfies the org_memberships JOIN)
    result = await db_session.execute(select(User).where(User.email == pair.owner_a["email"]))
    user_a = result.scalar_one()

    # Seed: 1 conversation + 5 labor + 2 civil assistant messages
    conv = Conversation(
        id=uuid.uuid4(),
        user_id=user_a.id,
        title="Areas test conv",
        model_used="test",
    )
    db_session.add(conv)

    for i in range(5):
        db_session.add(Message(
            conversation_id=conv.id,
            role="assistant",
            content=f"Respuesta laboral {i}.",
            legal_area="labor",
            model="test-model",
            latency_ms=100,
        ))
    for i in range(2):
        db_session.add(Message(
            conversation_id=conv.id,
            role="assistant",
            content=f"Respuesta civil {i}.",
            legal_area="civil",
            model="test-model",
            latency_ms=100,
        ))

    await db_session.commit()

    # Query /areas — use days=1 (all seeded messages have created_at = now)
    res = await pair.client_a.get(f"/api/analytics/{org_a_id}/areas?days=1")
    assert res.status_code == 200, (
        f"Expected 200 for org owner on analytics/areas, got {res.status_code}: {res.text[:200]}"
    )

    areas = {a["area"]: a["count"] for a in res.json()["areas"]}
    assert areas.get("labor") == 5, f"Expected 5 labor queries, got {areas}"
    assert areas.get("civil") == 2, f"Expected 2 civil queries, got {areas}"


# ---------------------------------------------------------------------------
# observability.unit.006 — top-queries isolation (cross-tenant)
# ---------------------------------------------------------------------------


async def test_analytics_top_queries_isolation(tenant_pair, db_session):
    """Org A top-queries must not contain Org B's query data.

    Spec: observability.unit.006 (seed for FIX-03b wave 2)
    Seeds a unique user message in each org. Queries Org A's /top-queries and
    asserts Org B's signature string is absent. The SQL filter is correct in
    production, so this test passes and acts as an isolation regression guard.
    """
    pair = tenant_pair
    org_a_id = uuid.UUID(pair.org_a["org_id"])

    # Resolve both user UUIDs
    result_a = await db_session.execute(select(User).where(User.email == pair.owner_a["email"]))
    user_a = result_a.scalar_one()
    result_b = await db_session.execute(select(User).where(User.email == pair.owner_b["email"]))
    user_b = result_b.scalar_one()

    # Unique query strings — must not overlap in any prefix
    ORG_A_QUERY = "pregunta alfa única para organización uno"
    ORG_B_QUERY = "pregunta beta única para organización dos"

    # Seed org A: 1 conversation + 1 user message
    conv_a = Conversation(id=uuid.uuid4(), user_id=user_a.id, title="TopQ A", model_used="test")
    db_session.add(conv_a)
    db_session.add(Message(conversation_id=conv_a.id, role="user", content=ORG_A_QUERY))

    # Seed org B: 1 conversation + 1 user message
    conv_b = Conversation(id=uuid.uuid4(), user_id=user_b.id, title="TopQ B", model_used="test")
    db_session.add(conv_b)
    db_session.add(Message(conversation_id=conv_b.id, role="user", content=ORG_B_QUERY))

    await db_session.commit()

    # Org A top-queries — days=1 to catch freshly seeded messages
    res = await pair.client_a.get(f"/api/analytics/{org_a_id}/top-queries?days=1")
    assert res.status_code == 200, (
        f"Expected 200 for org owner on top-queries, got {res.status_code}: {res.text[:200]}"
    )

    # The SQL groups by LOWER(TRIM(LEFT(content, 100))) — previews are lowercased
    previews = [q["query_preview"] for q in res.json()["queries"]]

    # Org B's signature word must be absent from Org A's results
    assert not any("beta" in p for p in previews), (
        f"Cross-tenant leak detected: Org B query found in Org A top-queries.\n"
        f"Previews: {previews}"
    )

    # Org A's own query must be present
    assert any("alfa" in p for p in previews), (
        f"Org A's own query missing from top-queries.\nPreviews: {previews}"
    )


# ---------------------------------------------------------------------------
# observability.unit.007 — CSV export: content-type + header row + data row
# ---------------------------------------------------------------------------


async def test_analytics_export_csv_generation(tenant_pair, db_session):
    """CSV export returns text/csv with proper header columns and at least one data row.

    Spec: observability.unit.007
    Seeds 1 user message + 1 assistant message. The export query joins them via
    LATERAL to produce one data row. Validates Content-Type and all required CSV
    column headers.
    """
    pair = tenant_pair
    org_a_id = uuid.UUID(pair.org_a["org_id"])

    # Resolve user_a UUID
    result = await db_session.execute(select(User).where(User.email == pair.owner_a["email"]))
    user_a = result.scalar_one()

    # Seed: 1 conversation with user + assistant message pair
    conv = Conversation(
        id=uuid.uuid4(),
        user_id=user_a.id,
        title="Export test conv",
        model_used="test-model",
    )
    db_session.add(conv)
    db_session.add(Message(
        conversation_id=conv.id,
        role="user",
        content="Pregunta de exportación.",
    ))
    db_session.add(Message(
        conversation_id=conv.id,
        role="assistant",
        content="Respuesta de exportación.",
        legal_area="labor",
        model="test-model",
        latency_ms=150,
        tokens_used=42,
    ))
    await db_session.commit()

    res = await pair.client_a.get(f"/api/analytics/{org_a_id}/export?days=1")
    assert res.status_code == 200, (
        f"Expected 200 for CSV export, got {res.status_code}: {res.text[:200]}"
    )

    # Verify Content-Type
    content_type = res.headers.get("content-type", "")
    assert "text/csv" in content_type, (
        f"Expected text/csv content-type, got: {content_type}"
    )

    # Parse CSV — at least header row + 1 data row
    lines = [ln for ln in res.text.splitlines() if ln.strip()]
    assert len(lines) >= 2, (
        f"Expected header + at least 1 data row, got {len(lines)} lines:\n{res.text[:500]}"
    )

    # Validate required header columns
    header = lines[0].lower()
    for col in ("date", "user_email", "legal_area", "model", "latency_ms", "tokens_used"):
        assert col in header, f"Missing column '{col}' in CSV header: {header}"
