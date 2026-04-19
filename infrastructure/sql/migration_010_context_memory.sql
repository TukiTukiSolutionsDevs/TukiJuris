-- Migration 010: Context Memory
-- Adds user_memories table for persistent cross-conversation context.
-- Each row represents one extracted fact about the user.

CREATE TABLE IF NOT EXISTS user_memories (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category                VARCHAR(50) NOT NULL,
    content                 TEXT NOT NULL,
    source_conversation_id  UUID REFERENCES conversations(id) ON DELETE SET NULL,
    confidence              FLOAT NOT NULL DEFAULT 1.0,
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Fast lookup: "give me all active memories for user X"
CREATE INDEX IF NOT EXISTS idx_user_memories_user_active
    ON user_memories(user_id, is_active);

-- Fast lookup: "give me all memories of category Y for user X"
CREATE INDEX IF NOT EXISTS idx_user_memories_user_category
    ON user_memories(user_id, category);

-- Auto-update updated_at on row changes
CREATE OR REPLACE FUNCTION update_user_memories_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_user_memories_updated_at ON user_memories;
CREATE TRIGGER trg_user_memories_updated_at
    BEFORE UPDATE ON user_memories
    FOR EACH ROW EXECUTE FUNCTION update_user_memories_updated_at();
