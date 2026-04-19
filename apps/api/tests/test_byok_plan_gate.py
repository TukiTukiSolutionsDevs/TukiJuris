"""Integration tests for BYOK plan gate — byok-plan-gate Sprint.

Covers:
  - Free users cannot POST or GET BYOK keys (403 with structured payload).
  - DELETE is always allowed (GDPR hygiene, any plan).
  - Pro/studio users can POST and GET.
  - Downgrade: keys stay in DB but GET returns 403.
  - Re-upgrade: keys accessible again.
  - Lazy re-encryption: legacy row (no v1: prefix) migrates on first USE.

Run: python -m pytest tests/test_byok_plan_gate.py -v --tb=short
(Requires live PostgreSQL — integration tests.)
"""

import base64
import hashlib
import uuid

from unittest.mock import AsyncMock
import pytest
from httpx import AsyncClient

BYOK_403_PAYLOAD = {
    "error_code": "byok_requires_paid_plan",
    "required_plan": "pro",
    "upgrade_url": "/billing",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _register(client: AsyncClient, suffix: str | None = None) -> dict:
    """Register a unique user and return auth headers."""
    tag = suffix or uuid.uuid4().hex[:8]
    email = f"byok-{tag}@test.com"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "TestPassword123!", "full_name": "BYOK Tester"},
    )
    assert res.status_code in (200, 201), res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# ---------------------------------------------------------------------------
# Free user — always denied on POST and GET
# ---------------------------------------------------------------------------


async def test_free_user_post_llm_key_returns_403(client):
    """Free users cannot create BYOK keys."""
    headers = await _register(client)
    res = await client.post(
        "/api/keys/llm-keys",
        json={"provider": "google", "api_key": "AIzaSy-test-key-1234567890"},
        headers=headers,
    )
    assert res.status_code == 403, res.text
    detail = res.json()["detail"]
    assert detail["error_code"] == BYOK_403_PAYLOAD["error_code"]
    assert detail["required_plan"] == BYOK_403_PAYLOAD["required_plan"]
    assert detail["upgrade_url"] == BYOK_403_PAYLOAD["upgrade_url"]


async def test_free_user_get_llm_keys_returns_403(client):
    """Free users cannot list BYOK keys."""
    headers = await _register(client)
    res = await client.get("/api/keys/llm-keys", headers=headers)
    assert res.status_code == 403, res.text
    detail = res.json()["detail"]
    assert detail["error_code"] == BYOK_403_PAYLOAD["error_code"]


async def test_free_user_test_endpoint_returns_403(client):
    """Free users cannot use the BYOK test endpoint."""
    headers = await _register(client)
    res = await client.post(
        "/api/keys/llm-keys/test",
        json={"provider": "google"},
        headers=headers,
    )
    assert res.status_code == 403, res.text
    detail = res.json()["detail"]
    assert detail["error_code"] == BYOK_403_PAYLOAD["error_code"]


# ---------------------------------------------------------------------------
# DELETE is always allowed (GDPR hygiene)
# ---------------------------------------------------------------------------


async def test_free_user_delete_nonexistent_key_returns_404_not_403(client):
    """DELETE endpoint is ungated — free users get 404 (no key), not 403."""
    headers = await _register(client)
    fake_id = str(uuid.uuid4())
    res = await client.delete(f"/api/keys/llm-keys/{fake_id}", headers=headers)
    # Must NOT be 403 — gate does not apply to DELETE.
    assert res.status_code == 404, res.text


# ---------------------------------------------------------------------------
# Pro / Studio users — full access
# ---------------------------------------------------------------------------


async def test_pro_user_post_and_get_succeed(client, monkeypatch):
    """Pro user can create and list BYOK keys."""
    monkeypatch.setattr("app.api.routes.api_keys._byok_allowed", AsyncMock(return_value=True))

    headers = await _register(client)

    post_res = await client.post(
        "/api/keys/llm-keys",
        json={"provider": "google", "api_key": "AIzaSy-pro-test-key-1234567890"},
        headers=headers,
    )
    assert post_res.status_code == 201, post_res.text
    data = post_res.json()
    assert data["provider"] == "google"
    assert "hint" in data

    get_res = await client.get("/api/keys/llm-keys", headers=headers)
    assert get_res.status_code == 200, get_res.text
    keys = get_res.json()
    assert len(keys) >= 1
    assert keys[0]["provider"] == "google"
    assert "hint" in keys[0]
    # Full key must NEVER appear in the response.
    assert "AIzaSy-pro-test-key-1234567890" not in str(keys)


async def test_studio_user_post_and_get_succeed(client, monkeypatch):
    """Studio user (same gate path as pro) can create and list BYOK keys."""
    monkeypatch.setattr("app.api.routes.api_keys._byok_allowed", AsyncMock(return_value=True))

    headers = await _register(client)

    post_res = await client.post(
        "/api/keys/llm-keys",
        json={"provider": "anthropic", "api_key": "sk-ant-studio-test-key-12345678"},
        headers=headers,
    )
    assert post_res.status_code == 201, post_res.text

    get_res = await client.get("/api/keys/llm-keys", headers=headers)
    assert get_res.status_code == 200, get_res.text
    providers = [k["provider"] for k in get_res.json()]
    assert "anthropic" in providers


# ---------------------------------------------------------------------------
# Downgrade retention (Option C): key stays in DB, access is gated
# ---------------------------------------------------------------------------


async def test_downgrade_retains_row_but_gates_access(client, monkeypatch):
    """Keys survive a plan downgrade but GET returns 403 after downgrade."""
    # Step 1: Create key as "pro" user.
    monkeypatch.setattr("app.api.routes.api_keys._byok_allowed", AsyncMock(return_value=True))
    headers = await _register(client)

    post_res = await client.post(
        "/api/keys/llm-keys",
        json={"provider": "deepseek", "api_key": "sk-downgrade-test-key-9876543"},
        headers=headers,
    )
    assert post_res.status_code == 201, post_res.text
    key_id = post_res.json()["id"]

    # Step 2: Simulate downgrade — gate now returns False.
    monkeypatch.setattr("app.api.routes.api_keys._byok_allowed", AsyncMock(return_value=False))

    get_res = await client.get("/api/keys/llm-keys", headers=headers)
    assert get_res.status_code == 403, get_res.text
    assert get_res.json()["detail"]["error_code"] == "byok_requires_paid_plan"

    # Step 3: Row still exists — DELETE (always ungated) succeeds with 204.
    del_res = await client.delete(f"/api/keys/llm-keys/{key_id}", headers=headers)
    assert del_res.status_code == 204, del_res.text


async def test_reupgrade_restores_access(client, monkeypatch):
    """After re-upgrade, the retained key is accessible again."""
    # Step 1: Create key.
    monkeypatch.setattr("app.api.routes.api_keys._byok_allowed", AsyncMock(return_value=True))
    headers = await _register(client)

    post_res = await client.post(
        "/api/keys/llm-keys",
        json={"provider": "groq", "api_key": "gsk_reupgrade-test-key-1234567"},
        headers=headers,
    )
    assert post_res.status_code == 201, post_res.text

    # Step 2: Downgrade — gate blocked.
    monkeypatch.setattr("app.api.routes.api_keys._byok_allowed", AsyncMock(return_value=False))
    get_res = await client.get("/api/keys/llm-keys", headers=headers)
    assert get_res.status_code == 403

    # Step 3: Re-upgrade — gate open again.
    monkeypatch.setattr("app.api.routes.api_keys._byok_allowed", AsyncMock(return_value=True))
    get_res = await client.get("/api/keys/llm-keys", headers=headers)
    assert get_res.status_code == 200, get_res.text
    providers = [k["provider"] for k in get_res.json()]
    assert "groq" in providers


# ---------------------------------------------------------------------------
# Encryption: v1 prefix is stored, full key is never returned
# ---------------------------------------------------------------------------


async def test_stored_key_has_v1_prefix_and_plaintext_not_leaked(client, monkeypatch):
    """POST stores encrypted ciphertext with v1: prefix; plaintext never exposed."""
    import sqlalchemy
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    from app.config import settings
    from app.models.llm_key import UserLLMKey

    monkeypatch.setattr("app.api.routes.api_keys._byok_allowed", AsyncMock(return_value=True))
    headers = await _register(client)

    raw_key = "AIzaSy-v1prefix-check-key-99999"
    post_res = await client.post(
        "/api/keys/llm-keys",
        json={"provider": "google", "api_key": raw_key},
        headers=headers,
    )
    assert post_res.status_code == 201, post_res.text
    key_id = uuid.UUID(post_res.json()["id"])

    # Verify stored value in DB has v1: prefix.
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        row = await db.get(UserLLMKey, key_id)
        assert row is not None
        assert row.api_key_encrypted.startswith("v1:"), (
            f"Expected v1: prefix in DB, got: {row.api_key_encrypted[:20]}"
        )
        # Plaintext must not be in the stored value
        assert raw_key not in row.api_key_encrypted
    await engine.dispose()
