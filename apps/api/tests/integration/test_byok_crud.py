"""Integration tests — BYOK LLM key CRUD matrix + cross-tenant isolation.

Sub-batch C.2 of backend-saas-test-coverage.

Covers (8 tests):
  C.2.1  Full CRUD roundtrip: create → list → delete → verify gone
  C.2.2  Hint masking: plaintext never exposed in POST/GET responses
  C.2.3  Duplicate provider guard (xfail — FIX-03b, no unique constraint yet)
  C.2.4  Encryption at rest: round-trip verify encrypt → v1: prefix → decrypt
  C.2.5  Test-connectivity OK: mocked LLM call returns ok:True
  C.2.6  Test-connectivity no key: missing key returns ok:False, not 500
  C.2.7  Cross-tenant list isolation: user B cannot see user A's keys
  C.2.8  Cross-tenant delete isolation: user B cannot delete user A's key

Out of scope:
  - byok-plan-gate (free → 403, pro → 200) — already in test_byok_plan_gate.py
  - Admin / RBAC tests
  - Chat / stream routes
"""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PLAINTEXT_KEY = "sk-test-byok-crud-" + "0" * 24  # 42 chars, safely masked


async def _register(client: AsyncClient, suffix: str | None = None) -> dict:
    """Register a unique user; return Authorization headers dict."""
    tag = suffix or uuid.uuid4().hex[:8]
    res = await client.post(
        "/api/auth/register",
        json={
            "email": f"byok-crud-{tag}@test.com",
            "password": "TestPassword123!",
            "full_name": "CRUD Tester",
        },
    )
    assert res.status_code in (200, 201), res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _byok_open(monkeypatch) -> None:
    """Bypass BYOK plan gate — tests here focus on CRUD, not entitlement."""
    monkeypatch.setattr(
        "app.api.routes.api_keys._byok_allowed",
        AsyncMock(return_value=True),
    )


# ---------------------------------------------------------------------------
# Lightweight two-user pair — no org creation needed (BYOK is user-scoped)
# ---------------------------------------------------------------------------


@dataclass
class _UserPair:
    client_a: AsyncClient
    client_b: AsyncClient


@asynccontextmanager
async def _two_users():
    """Create two independent users with pre-authenticated AsyncClients.

    Intentionally does NOT create organisations — LLM keys are scoped to
    user_id, so org membership is irrelevant for BYOK isolation tests.
    This avoids the make_org/slug issue in the full tenant_pair fixture.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as anon:
        tag_a = uuid.uuid4().hex[:8]
        tag_b = uuid.uuid4().hex[:8]
        for tag in (tag_a, tag_b):
            r = await anon.post(
                "/api/auth/register",
                json={
                    "email": f"iso-{tag}@test.com",
                    "password": "TestPassword123!",
                    "full_name": "Isolation User",
                },
            )
            assert r.status_code in (200, 201), r.text

        r_a = await anon.post(
            "/api/auth/login",
            json={"email": f"iso-{tag_a}@test.com", "password": "TestPassword123!"},
        )
        r_b = await anon.post(
            "/api/auth/login",
            json={"email": f"iso-{tag_b}@test.com", "password": "TestPassword123!"},
        )

    async with (
        AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {r_a.json()['access_token']}"},
        ) as client_a,
        AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {r_b.json()['access_token']}"},
        ) as client_b,
    ):
        yield _UserPair(client_a=client_a, client_b=client_b)


# ---------------------------------------------------------------------------
# C.2.1 — Full CRUD roundtrip
# ---------------------------------------------------------------------------


async def test_llm_key_crud_full_roundtrip(client, monkeypatch):
    """POST → list (key present) → DELETE → list (key gone)."""
    _byok_open(monkeypatch)
    headers = await _register(client)

    # ── Create ──────────────────────────────────────────────────────────────
    post_res = await client.post(
        "/api/keys/llm-keys",
        json={"provider": "openai", "api_key": _PLAINTEXT_KEY, "label": "crud-test"},
        headers=headers,
    )
    assert post_res.status_code == 201, post_res.text
    data = post_res.json()
    key_id = data["id"]
    assert data["provider"] == "openai"
    assert "hint" in data

    # ── List — key must appear ───────────────────────────────────────────────
    list_res = await client.get("/api/keys/llm-keys", headers=headers)
    assert list_res.status_code == 200, list_res.text
    assert key_id in [k["id"] for k in list_res.json()]

    # ── Delete ──────────────────────────────────────────────────────────────
    del_res = await client.delete(f"/api/keys/llm-keys/{key_id}", headers=headers)
    assert del_res.status_code == 204, del_res.text

    # ── List — key must be gone ──────────────────────────────────────────────
    list_res2 = await client.get("/api/keys/llm-keys", headers=headers)
    assert list_res2.status_code == 200, list_res2.text
    assert key_id not in [k["id"] for k in list_res2.json()]


# ---------------------------------------------------------------------------
# C.2.2 — Hint masking (plaintext never in response)
# ---------------------------------------------------------------------------


async def test_llm_key_hint_masks_plaintext(client, monkeypatch):
    """POST and GET responses must never expose the full plaintext key."""
    _byok_open(monkeypatch)
    headers = await _register(client)

    raw_key = "sk-ant-plaintext-check-9999999"
    post_res = await client.post(
        "/api/keys/llm-keys",
        json={"provider": "anthropic", "api_key": raw_key},
        headers=headers,
    )
    assert post_res.status_code == 201, post_res.text
    assert raw_key not in str(post_res.json()), "Plaintext leaked in POST response"

    list_res = await client.get("/api/keys/llm-keys", headers=headers)
    assert list_res.status_code == 200, list_res.text
    assert raw_key not in str(list_res.json()), "Plaintext leaked in GET response"

    # Hint format: first 3 chars + "..." + last 4 chars
    hint = list_res.json()[0]["hint"]
    assert "..." in hint, f"Unexpected hint format: {hint!r}"
    assert hint.startswith(raw_key[:3]), f"Hint prefix mismatch: {hint!r}"
    assert hint.endswith(raw_key[-4:]), f"Hint suffix mismatch: {hint!r}"


# ---------------------------------------------------------------------------
# C.2.3 — Duplicate provider rejection (xfail — FIX-03b)
# ---------------------------------------------------------------------------


async def test_llm_key_duplicate_provider_rejected(client, monkeypatch):
    """Same user adding the same provider twice should return 400 or 409."""
    _byok_open(monkeypatch)
    headers = await _register(client)

    payload = {"provider": "deepseek", "api_key": "sk-dup-00000000000000000000"}

    res1 = await client.post("/api/keys/llm-keys", json=payload, headers=headers)
    assert res1.status_code == 201, res1.text

    res2 = await client.post("/api/keys/llm-keys", json=payload, headers=headers)
    assert res2.status_code in (400, 409), (
        f"Expected 400/409 on duplicate provider, got {res2.status_code}: {res2.text}"
    )


# ---------------------------------------------------------------------------
# C.2.4 — Encryption at rest: round-trip
# ---------------------------------------------------------------------------


async def test_llm_key_encryption_at_rest_round_trip():
    """encrypt_key → v1: prefix → decrypt_key recovers original plaintext."""
    from app.services.llm_key_service import decrypt_key, encrypt_key

    plaintext = "sk-test-roundtrip-" + "A" * 20
    ciphertext = encrypt_key(plaintext)

    assert ciphertext.startswith("v1:"), (
        f"Expected 'v1:' prefix in stored value, got: {ciphertext[:20]!r}"
    )
    assert plaintext not in ciphertext, (
        "Plaintext must not appear verbatim in ciphertext"
    )

    recovered = decrypt_key(ciphertext)
    assert recovered == plaintext, (
        f"Decrypt round-trip failed: {recovered!r} != {plaintext!r}"
    )


# ---------------------------------------------------------------------------
# C.2.5 — Test-connectivity: key present, mocked LLM → ok:True
# ---------------------------------------------------------------------------


async def test_llm_key_test_connectivity_ok(client, monkeypatch):
    """POST /llm-keys/test returns ok:True when provider responds (mocked)."""
    _byok_open(monkeypatch)
    headers = await _register(client)

    # Store a key so the endpoint can resolve it
    await client.post(
        "/api/keys/llm-keys",
        json={"provider": "openai", "api_key": _PLAINTEXT_KEY},
        headers=headers,
    )

    # Mock litellm.acompletion — build minimal response shape
    mock_choice = MagicMock()
    mock_choice.message.content = "OK"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_response
        test_res = await client.post(
            "/api/keys/llm-keys/test",
            json={"provider": "openai"},
            headers=headers,
        )

    assert test_res.status_code == 200, test_res.text
    body = test_res.json()
    assert body["ok"] is True, f"Expected ok:True, got: {body}"
    assert "latency_ms" in body
    mock_llm.assert_called_once()


# ---------------------------------------------------------------------------
# C.2.6 — Test-connectivity: no key configured → ok:False (no 500)
# ---------------------------------------------------------------------------


async def test_llm_key_test_connectivity_no_key_configured(client, monkeypatch):
    """POST /llm-keys/test with no stored key returns ok:False, never 500."""
    _byok_open(monkeypatch)
    headers = await _register(client)

    # No key added for this user/provider — route should handle gracefully
    test_res = await client.post(
        "/api/keys/llm-keys/test",
        json={"provider": "groq"},
        headers=headers,
    )

    assert test_res.status_code == 200, test_res.text
    body = test_res.json()
    assert body["ok"] is False, f"Expected ok:False when no key, got: {body}"
    assert "error" in body


# ---------------------------------------------------------------------------
# C.2.7 — Cross-tenant list isolation
# ---------------------------------------------------------------------------


async def test_llm_key_cross_tenant_list_isolation(monkeypatch):
    """User B's GET /llm-keys must not include any of user A's keys."""
    _byok_open(monkeypatch)

    async with _two_users() as pair:
        # User A stores a key
        add_res = await pair.client_a.post(
            "/api/keys/llm-keys",
            json={"provider": "google", "api_key": "AIzaSy-isolation-user-a-000000"},
        )
        assert add_res.status_code == 201, add_res.text
        key_id_a = add_res.json()["id"]

        # User B lists — must NOT see user A's key
        list_b = await pair.client_b.get("/api/keys/llm-keys")
        assert list_b.status_code == 200, list_b.text
        ids_b = [k["id"] for k in list_b.json()]
        assert key_id_a not in ids_b, (
            f"Cross-tenant leak: user B can see user A's key {key_id_a}"
        )


# ---------------------------------------------------------------------------
# C.2.8 — Cross-tenant delete isolation
# ---------------------------------------------------------------------------


async def test_llm_key_cross_tenant_delete_isolation(monkeypatch):
    """User B DELETE on user A's key must return 404 and leave the key intact."""
    _byok_open(monkeypatch)

    async with _two_users() as pair:
        # User A stores a key
        add_res = await pair.client_a.post(
            "/api/keys/llm-keys",
            json={"provider": "anthropic", "api_key": "sk-ant-isolation-b-deletes-a-000"},
        )
        assert add_res.status_code == 201, add_res.text
        key_id_a = add_res.json()["id"]

        # User B attempts to delete user A's key — must be rejected
        del_res = await pair.client_b.delete(f"/api/keys/llm-keys/{key_id_a}")
        assert del_res.status_code == 404, (
            f"Expected 404 (isolation enforced), got {del_res.status_code}: {del_res.text}"
        )

        # Confirm key is still intact for user A
        list_a = await pair.client_a.get("/api/keys/llm-keys")
        assert list_a.status_code == 200
        ids_a = [k["id"] for k in list_a.json()]
        assert key_id_a in ids_a, "Key was deleted by user B — isolation FAILURE"
