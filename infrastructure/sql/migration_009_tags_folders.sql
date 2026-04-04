-- Migration 009: Tags and Folders for Conversations
-- Adds tag, folder, and conversation_tag tables.
-- Adds folder_id to conversations.

-- -------------------------------------------------------------------------
-- 1. Folders table
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS folders (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(200) NOT NULL,
    icon        VARCHAR(50) NOT NULL DEFAULT 'folder',
    position    INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_folders_user_name UNIQUE (user_id, name)
);

CREATE INDEX IF NOT EXISTS idx_folders_user_id
    ON folders(user_id);

-- -------------------------------------------------------------------------
-- 2. Tags table
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tags (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    color       VARCHAR(7) NOT NULL DEFAULT '#3b82f6',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_tags_user_name UNIQUE (user_id, name)
);

CREATE INDEX IF NOT EXISTS idx_tags_user_id
    ON tags(user_id);

-- -------------------------------------------------------------------------
-- 3. Conversation-Tag junction table
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversation_tags (
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    tag_id          UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (conversation_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_conversation_tags_conversation_id
    ON conversation_tags(conversation_id);

CREATE INDEX IF NOT EXISTS idx_conversation_tags_tag_id
    ON conversation_tags(tag_id);

-- -------------------------------------------------------------------------
-- 4. Add folder_id to conversations
-- -------------------------------------------------------------------------
ALTER TABLE conversations
    ADD COLUMN IF NOT EXISTS folder_id UUID REFERENCES folders(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_conversations_folder_id
    ON conversations(folder_id)
    WHERE folder_id IS NOT NULL;
