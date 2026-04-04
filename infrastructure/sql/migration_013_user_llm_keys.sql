-- Migration 013: User LLM Keys (BYOK — Bring Your Own Key)
-- Users provide their own API keys for LLM providers.
-- TukiJuris does NOT resell AI model usage.

CREATE TABLE IF NOT EXISTS user_llm_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    api_key_hint VARCHAR(20) NOT NULL,
    label VARCHAR(200),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_llm_keys_user ON user_llm_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_user_llm_keys_provider ON user_llm_keys(user_id, provider);
