-- Migration 003 — API Keys table for public developer API
-- Run after migration_002_multi_tenant.sql

CREATE TABLE IF NOT EXISTS api_keys (
    id                   UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id      UUID         REFERENCES organizations(id) ON DELETE SET NULL,
    name                 VARCHAR(255) NOT NULL,
    -- First 8 chars of the full key shown to the user after creation
    key_prefix           VARCHAR(8)   NOT NULL,
    -- SHA-256 hex digest of the full key — raw key is never stored
    key_hash             VARCHAR(128) NOT NULL UNIQUE,
    -- Allowed operations: query, search, analyze, documents
    scopes               JSONB        NOT NULL DEFAULT '["query", "search"]',
    is_active            BOOLEAN      NOT NULL DEFAULT TRUE,
    last_used_at         TIMESTAMPTZ,
    expires_at           TIMESTAMPTZ,
    rate_limit_per_minute INTEGER     NOT NULL DEFAULT 30,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Fast lookup by hash (used on every authenticated request)
CREATE INDEX IF NOT EXISTS idx_api_keys_hash   ON api_keys(key_hash);
-- Fast listing of keys per user
CREATE INDEX IF NOT EXISTS idx_api_keys_user   ON api_keys(user_id);
-- Partial index for active keys only (reduces index size)
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active) WHERE is_active = TRUE;

-- Auto-update updated_at via trigger (mirrors pattern from migration_002)
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_api_keys_updated_at ON api_keys;
CREATE TRIGGER trg_api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
