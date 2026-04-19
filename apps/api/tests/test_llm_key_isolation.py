import uuid
from unittest.mock import AsyncMock


async def _register_user(client, email: str):
    password = "TestPassword123!"
    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Isolation Test"},
    )
    assert res.status_code in (200, 201), res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_free_models_do_not_leak_other_users_byok_keys(client, monkeypatch):
    monkeypatch.setattr("app.config.settings.google_api_key", "")
    monkeypatch.setattr("app.config.settings.groq_api_key", "")
    monkeypatch.setattr("app.config.settings.openai_api_key", "")
    monkeypatch.setattr("app.config.settings.deepseek_api_key", "")
    monkeypatch.setattr("app.config.settings.anthropic_api_key", "")
    monkeypatch.setattr("app.config.settings.xai_api_key", "")
    monkeypatch.setattr("app.config.settings.openrouter_api_key", "")
    monkeypatch.setattr("app.config.settings.free_tier_enabled", True)
    # Bypass BYOK plan gate — this test focuses on key isolation, not plan gating.
    monkeypatch.setattr("app.api.routes.api_keys._byok_allowed", AsyncMock(return_value=True))

    headers_1 = await _register_user(client, f"owner-{uuid.uuid4().hex[:8]}@test.com")
    headers_2 = await _register_user(client, f"other-{uuid.uuid4().hex[:8]}@test.com")

    add_key = await client.post(
        "/api/keys/llm-keys",
        json={"provider": "google", "api_key": "AIzaSy-test-owner-key-1234567890"},
        headers=headers_1,
    )
    assert add_key.status_code == 201, add_key.text

    free_models = await client.get("/api/keys/free-models", headers=headers_2)
    assert free_models.status_code == 200, free_models.text

    payload = free_models.json()
    assert payload["enabled"] is True
    assert payload["models"] == []


async def test_chat_stream_rejects_cross_tenant_free_tier_fallback(client, monkeypatch):
    monkeypatch.setattr("app.config.settings.google_api_key", "")
    monkeypatch.setattr("app.config.settings.groq_api_key", "")
    monkeypatch.setattr("app.config.settings.openai_api_key", "")
    monkeypatch.setattr("app.config.settings.deepseek_api_key", "")
    monkeypatch.setattr("app.config.settings.anthropic_api_key", "")
    monkeypatch.setattr("app.config.settings.xai_api_key", "")
    monkeypatch.setattr("app.config.settings.openrouter_api_key", "")
    monkeypatch.setattr("app.config.settings.free_tier_enabled", True)
    # Bypass BYOK plan gate — this test focuses on key isolation, not plan gating.
    monkeypatch.setattr("app.api.routes.api_keys._byok_allowed", AsyncMock(return_value=True))

    headers_1 = await _register_user(client, f"owner-{uuid.uuid4().hex[:8]}@test.com")
    headers_2 = await _register_user(client, f"other-{uuid.uuid4().hex[:8]}@test.com")

    add_key = await client.post(
        "/api/keys/llm-keys",
        json={"provider": "google", "api_key": "AIzaSy-test-owner-key-1234567890"},
        headers=headers_1,
    )
    assert add_key.status_code == 201, add_key.text

    stream_res = await client.post(
        "/api/chat/stream",
        json={
            "message": "Necesito orientación laboral",
            "model": "gemini/gemini-2.5-flash",
        },
        headers=headers_2,
    )

    assert stream_res.status_code == 400, stream_res.text
    # Error copy updated: model unavailable on platform (no platform key + no BYOK) —
    # verifies rejection without cross-tenant key leakage.
    assert "no disponible en la plataforma" in stream_res.json()["detail"]
