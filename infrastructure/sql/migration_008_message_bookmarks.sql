-- Migration 008: Message bookmarks
-- Adds bookmark support to assistant/user messages.

ALTER TABLE messages
    ADD COLUMN IF NOT EXISTS is_bookmarked BOOLEAN DEFAULT FALSE NOT NULL;

CREATE INDEX IF NOT EXISTS idx_messages_bookmarked
    ON messages(conversation_id, is_bookmarked)
    WHERE is_bookmarked = TRUE;
