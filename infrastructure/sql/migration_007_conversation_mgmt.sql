-- Migration 007: Conversation Management (pin, archive, share)
-- Adds columns for organizing and sharing conversations.

ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS share_id VARCHAR(20) UNIQUE;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_shared BOOLEAN DEFAULT FALSE NOT NULL;

-- Partial index: quickly fetch pinned conversations per user
CREATE INDEX IF NOT EXISTS idx_conversations_pinned ON conversations(user_id, is_pinned)
    WHERE is_pinned = TRUE;

-- Index for fast share_id lookups (public endpoint, no auth)
CREATE INDEX IF NOT EXISTS idx_conversations_share_id ON conversations(share_id)
    WHERE share_id IS NOT NULL;

-- Index for archived filter
CREATE INDEX IF NOT EXISTS idx_conversations_archived ON conversations(user_id, is_archived);
