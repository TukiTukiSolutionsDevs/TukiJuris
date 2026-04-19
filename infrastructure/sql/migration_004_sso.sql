-- ============================================================
-- AGENTE DERECHO — Migration 004: SSO / OAuth2 fields
-- ============================================================
-- Run ONCE against an existing database.
-- Safe to re-run: all statements use IF NOT EXISTS / IF EXISTS.

-- Add SSO fields to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider    VARCHAR(50)  DEFAULT 'local';
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url       TEXT;

-- Allow hashed_password to be empty for SSO-only accounts
-- (column already exists — just ensure it has a sensible default)
ALTER TABLE users ALTER COLUMN hashed_password SET DEFAULT '';

-- Indexes for fast SSO lookups
CREATE INDEX IF NOT EXISTS idx_users_auth_provider    ON users(auth_provider);
CREATE INDEX IF NOT EXISTS idx_users_auth_provider_id ON users(auth_provider, auth_provider_id);
