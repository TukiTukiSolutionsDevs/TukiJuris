-- ============================================================
-- TUKIJURIS — Migration 006: Advanced Search
-- ============================================================
-- Creates saved_searches and search_history tables.
-- Safe to re-run: all statements use IF NOT EXISTS.

-- Saved searches — named, reusable queries per user
CREATE TABLE IF NOT EXISTS saved_searches (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    query       TEXT NOT NULL,
    filters     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_saved_searches_user_id
    ON saved_searches(user_id);

CREATE INDEX IF NOT EXISTS idx_saved_searches_created_at
    ON saved_searches(user_id, created_at DESC);

-- Search history — auto-logged on every search execution
CREATE TABLE IF NOT EXISTS search_history (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query          TEXT NOT NULL,
    filters        JSONB,
    results_count  INTEGER NOT NULL DEFAULT 0,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_search_history_user_id
    ON search_history(user_id);

CREATE INDEX IF NOT EXISTS idx_search_history_created_at
    ON search_history(user_id, created_at DESC);

-- Index for fast suggestion lookups (prefix search on query text)
CREATE INDEX IF NOT EXISTS idx_search_history_query_text
    ON search_history USING gin(to_tsvector('spanish', query));
