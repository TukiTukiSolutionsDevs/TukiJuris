-- Migration 005: In-App Notification Center
-- Creates the notifications table with indexes optimised for the
-- two most common access patterns:
--   1. List notifications for a user (idx_notifications_user)
--   2. Count / list unread notifications (idx_notifications_unread — partial index)

CREATE TABLE IF NOT EXISTS notifications (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type        VARCHAR(50)  NOT NULL,
    title       VARCHAR(255) NOT NULL,
    message     TEXT         NOT NULL,
    is_read     BOOLEAN      NOT NULL DEFAULT FALSE,
    action_url  VARCHAR(500),
    metadata    JSONB,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- General lookup by user (list all notifications)
CREATE INDEX IF NOT EXISTS idx_notifications_user
    ON notifications(user_id);

-- Partial index — only unread rows; keeps the badge-count query O(1)
CREATE INDEX IF NOT EXISTS idx_notifications_unread
    ON notifications(user_id, is_read)
    WHERE is_read = FALSE;

-- Ordering by recency (DESC matches default sort in the API)
CREATE INDEX IF NOT EXISTS idx_notifications_created
    ON notifications(created_at DESC);
