-- Migration 011: Add legal_area and model columns to messages, preferences to users
-- These columns are referenced by analytics queries but were missing from the schema.

ALTER TABLE messages ADD COLUMN IF NOT EXISTS legal_area VARCHAR(100);
ALTER TABLE messages ADD COLUMN IF NOT EXISTS model VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_messages_legal_area ON messages(legal_area) WHERE legal_area IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_messages_model ON messages(model) WHERE model IS NOT NULL;

-- User preferences JSONB column for persistent memory/UX settings
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}';
