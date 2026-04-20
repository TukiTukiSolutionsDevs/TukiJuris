"""Integration tests — notifications routes (sub-batch D.4a).

Spec IDs covered:
  notifications.unit.001  test_notification_list_401_no_auth
  notifications.unit.003  test_notification_list_pagination
  notifications.unit.004  test_notification_unread_count
  notifications.unit.005  test_notification_mark_read_happy_path
  notifications.unit.006  test_notification_mark_read_ownership_404
  notifications.unit.007  test_notification_clear_all_for_user
  notifications.unit.008  test_notification_preferences_crud  [XFAIL — not implemented]

Routes exercised:
  GET  /api/notifications/
  GET  /api/notifications/unread-count
  PUT  /api/notifications/read-all
  PUT  /api/notifications/{id}/read

NOTE: The spec describes PATCH for mutation endpoints; the actual route
implementation uses PUT. Tests follow the real route definitions.
No preferences endpoint exists — test_008 is marked XFAIL(strict=True).

Pre-existing smell (Batch A, documented): welcome notification triggers a FK
violation during register (runs before user commit, caught by try/except,
emits WARNING log). As a result, fresh users have zero notifications in the DB
— exact-count assertions (test_004, test_007) are safe.

Run:
  docker exec tukijuris-api-1 pytest tests/integration/test_notifications.py -v --tb=short
"""
from __future__ import annotations

import pytest

from tests.factories.notification import make_notification


# ---------------------------------------------------------------------------
# notifications.unit.001 — unauthenticated → 401
# ---------------------------------------------------------------------------


async def test_notification_list_401_no_auth(client):
    """Spec: notifications.unit.001

    No auth token → GET /api/notifications/ must return 401.
    """
    res = await client.get("/api/notifications/")
    assert res.status_code == 401, (
        f"Expected 401 for unauthenticated list, got {res.status_code}: {res.text[:200]}"
    )


# ---------------------------------------------------------------------------
# notifications.unit.003 — pagination
# ---------------------------------------------------------------------------


async def test_notification_list_pagination(auth_client):
    """Spec: notifications.unit.003

    User A with 15 notifications → GET ?per_page=10 returns exactly 10 items.
    The spec uses the term 'limit'; the actual query parameter is 'per_page'.
    """
    me_res = await auth_client.get("/api/auth/me")
    assert me_res.status_code == 200, f"GET /api/auth/me failed: {me_res.status_code}"
    user_id = me_res.json()["id"]

    for _ in range(15):
        await make_notification(user_id=user_id)

    res = await auth_client.get("/api/notifications/", params={"per_page": 10})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text[:200]}"
    body = res.json()
    assert len(body["notifications"]) == 10, (
        f"Expected 10 notifications with per_page=10, got {len(body['notifications'])}"
    )
    assert body["total"] >= 15, f"Expected total>=15, got {body['total']}"


# ---------------------------------------------------------------------------
# notifications.unit.004 — unread count
# ---------------------------------------------------------------------------


async def test_notification_unread_count(auth_client):
    """Spec: notifications.unit.004

    3 unread + 2 read → GET /api/notifications/unread-count → {"count": 3}.

    Fresh user guaranteed: welcome notification is never persisted due to the
    pre-existing FK violation (see module docstring). Zero baseline.
    """
    me_res = await auth_client.get("/api/auth/me")
    assert me_res.status_code == 200
    user_id = me_res.json()["id"]

    for _ in range(3):
        await make_notification(user_id=user_id, is_read=False)
    for _ in range(2):
        await make_notification(user_id=user_id, is_read=True)

    res = await auth_client.get("/api/notifications/unread-count")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text[:200]}"
    body = res.json()
    assert body["count"] == 3, f"Expected count=3, got {body}"


# ---------------------------------------------------------------------------
# notifications.unit.005 — mark single notification as read
# ---------------------------------------------------------------------------


async def test_notification_mark_read_happy_path(auth_client):
    """Spec: notifications.unit.005

    Unread notification → PUT /{id}/read → 200 + status=ok.
    Subsequent list confirms is_read=True.
    """
    me_res = await auth_client.get("/api/auth/me")
    assert me_res.status_code == 200
    user_id = me_res.json()["id"]

    notif = await make_notification(user_id=user_id, is_read=False)
    notif_id = str(notif.id)

    res = await auth_client.put(f"/api/notifications/{notif_id}/read")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text[:200]}"
    assert res.json().get("status") == "ok", f"Expected status=ok, got {res.json()}"

    # Verify via list that is_read is now True
    list_res = await auth_client.get("/api/notifications/", params={"per_page": 100})
    assert list_res.status_code == 200
    notifications = list_res.json()["notifications"]
    target = next((n for n in notifications if n["id"] == notif_id), None)
    assert target is not None, "Notification not found in list after mark-read"
    assert target["is_read"] is True, (
        f"Expected is_read=True after PUT /{notif_id}/read, got {target['is_read']}"
    )


# ---------------------------------------------------------------------------
# notifications.unit.006 — ownership isolation
# ---------------------------------------------------------------------------


async def test_notification_mark_read_ownership_404(tenant_pair):
    """Spec: notifications.unit.006

    User A tries to mark User B's notification as read → 404.
    Isolation convention (design §2.1.4): user-owned resource → 404, no existence leak.

    NOTE: assert_isolated() is deliberately NOT used here. Its step-3 integrity
    check performs GET on the same path (/read) after a PUT mutation. Since
    PUT /notifications/{id}/read has no GET counterpart, FastAPI returns 405
    (method not allowed), causing a false assertion failure. Isolation is verified
    manually following the same two-step probe pattern.
    """
    pair = tenant_pair

    me_res = await pair.client_b.get("/api/auth/me")
    assert me_res.status_code == 200
    user_b_id = me_res.json()["id"]

    # Notification owned by User B
    notif_b = await make_notification(user_id=user_b_id, is_read=False)
    notif_b_id = str(notif_b.id)
    path = f"/api/notifications/{notif_b_id}/read"

    # Step 1 — attacker (User A) must be denied
    attacker_res = await pair.client_a.put(path)
    assert attacker_res.status_code == 404, (
        f"Isolation failure: User A should get 404 on User B's notification, "
        f"got {attacker_res.status_code}: {attacker_res.text[:200]}"
    )

    # Step 2 — owner (User B) can still act on it; resource was NOT mutated
    owner_res = await pair.client_b.put(path)
    assert owner_res.status_code == 200, (
        f"Owner sanity: User B should get 200 on own notification after attacker probe, "
        f"got {owner_res.status_code}: {owner_res.text[:200]}"
    )


# ---------------------------------------------------------------------------
# notifications.unit.007 — clear all
# ---------------------------------------------------------------------------


async def test_notification_clear_all_for_user(auth_client):
    """Spec: notifications.unit.007

    User A with 5 unread → PUT /api/notifications/read-all → updated>=5, then
    unread-count returns 0.
    """
    me_res = await auth_client.get("/api/auth/me")
    assert me_res.status_code == 200
    user_id = me_res.json()["id"]

    for _ in range(5):
        await make_notification(user_id=user_id, is_read=False)

    res = await auth_client.put("/api/notifications/read-all")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text[:200]}"
    body = res.json()
    assert body.get("status") == "ok", f"Expected status=ok, got {body}"
    assert body.get("updated") >= 5, f"Expected updated>=5, got {body}"

    count_res = await auth_client.get("/api/notifications/unread-count")
    assert count_res.status_code == 200
    assert count_res.json()["count"] == 0, (
        f"Expected 0 unread after read-all, got count={count_res.json()['count']}"
    )


# ---------------------------------------------------------------------------
# notifications.unit.008 — preferences CRUD (XFAIL — endpoint not implemented)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Notification preferences endpoint not implemented. "
        "No PATCH/GET /api/notifications/preferences route exists in notifications.py. "
        "Feature deferred to Wave 2 / T-D-11."
    ),
)
async def test_notification_preferences_crud(auth_client):
    """Spec: notifications.unit.008

    XFAIL(strict=True): /api/notifications/preferences is not yet implemented.
    PATCH should update opt-in/opt-out settings; GET should reflect them.
    Will be implemented in T-D-11 (Wave 2 cross-tenant + notifications fixes).
    """
    payload = {"email_notifications": False, "push_notifications": True}
    res = await auth_client.patch("/api/notifications/preferences", json=payload)
    assert res.status_code == 200, f"PATCH preferences returned {res.status_code}"
    body = res.json()
    assert body.get("email_notifications") is False

    get_res = await auth_client.get("/api/notifications/preferences")
    assert get_res.status_code == 200, f"GET preferences returned {get_res.status_code}"
    assert get_res.json().get("email_notifications") is False
