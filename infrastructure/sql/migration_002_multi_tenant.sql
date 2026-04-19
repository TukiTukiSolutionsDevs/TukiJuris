-- ============================================================
-- AGENTE DERECHO — Migration 002: Multi-tenant + Billing
-- ============================================================
-- Run ONCE against an existing database that already has the
-- schema produced by init.sql (migration_001 baseline).
--
-- Safe to run with psql:
--   psql $DATABASE_URL -f migration_002_multi_tenant.sql
-- ============================================================

BEGIN;

-- ============================================================
-- 1. ORGANIZATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS organizations (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                    VARCHAR(255) NOT NULL,
    slug                    VARCHAR(100) NOT NULL,
    plan                    VARCHAR(50)  NOT NULL DEFAULT 'free',
    plan_queries_limit      INTEGER      NOT NULL DEFAULT 100,
    plan_models_allowed     JSONB        NOT NULL DEFAULT '["gpt-4o-mini"]',
    is_active               BOOLEAN      NOT NULL DEFAULT TRUE,
    -- Stripe placeholders (populated when beta ends)
    stripe_customer_id      VARCHAR(100),
    stripe_subscription_id  VARCHAR(100),
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_organizations_slug UNIQUE (slug)
);

CREATE INDEX IF NOT EXISTS idx_organizations_slug   ON organizations(slug);
CREATE INDEX IF NOT EXISTS idx_organizations_plan   ON organizations(plan);
CREATE INDEX IF NOT EXISTS idx_organizations_active ON organizations(is_active);

-- ============================================================
-- 2. ORG_MEMBERSHIPS
-- ============================================================
CREATE TABLE IF NOT EXISTS org_memberships (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id)         ON DELETE CASCADE,
    organization_id UUID        NOT NULL REFERENCES organizations(id)  ON DELETE CASCADE,
    role            VARCHAR(50) NOT NULL DEFAULT 'member',   -- owner, admin, member
    invited_by      UUID        REFERENCES users(id)         ON DELETE SET NULL,
    invited_at      TIMESTAMPTZ,
    joined_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_membership UNIQUE (user_id, organization_id)
);

CREATE INDEX IF NOT EXISTS idx_memberships_user         ON org_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_memberships_organization ON org_memberships(organization_id);
CREATE INDEX IF NOT EXISTS idx_memberships_role         ON org_memberships(role);
CREATE INDEX IF NOT EXISTS idx_memberships_active       ON org_memberships(is_active);

-- ============================================================
-- 3. SUBSCRIPTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id         UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    plan                    VARCHAR(50) NOT NULL,
    status                  VARCHAR(50) NOT NULL DEFAULT 'active',
        -- active, canceled, past_due, trialing
    current_period_start    TIMESTAMPTZ,
    current_period_end      TIMESTAMPTZ,
    -- Stripe placeholders
    stripe_subscription_id  VARCHAR(100),
    stripe_price_id         VARCHAR(100),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_organization ON subscriptions(organization_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status       ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_plan         ON subscriptions(plan);

-- ============================================================
-- 4. USAGE_RECORDS
-- ============================================================
CREATE TABLE IF NOT EXISTS usage_records (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id         UUID        NOT NULL REFERENCES users(id)         ON DELETE CASCADE,
    month           VARCHAR(7)  NOT NULL,   -- "YYYY-MM"
    queries_used    INTEGER     NOT NULL DEFAULT 0,
    tokens_used     INTEGER     NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_usage_record UNIQUE (organization_id, user_id, month)
);

CREATE INDEX IF NOT EXISTS idx_usage_organization ON usage_records(organization_id);
CREATE INDEX IF NOT EXISTS idx_usage_user         ON usage_records(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_month        ON usage_records(month);
-- Composite index for the most common query: org + month aggregation
CREATE INDEX IF NOT EXISTS idx_usage_org_month    ON usage_records(organization_id, month);

-- ============================================================
-- 5. ALTER USERS — add default_org_id FK
-- ============================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'users'
          AND column_name = 'default_org_id'
    ) THEN
        ALTER TABLE users
            ADD COLUMN default_org_id UUID
                REFERENCES organizations(id) ON DELETE SET NULL;
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS idx_users_default_org ON users(default_org_id)
    WHERE default_org_id IS NOT NULL;

-- ============================================================
-- 6. updated_at trigger helper (reuse for new tables)
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'trg_organizations_updated_at'
    ) THEN
        CREATE TRIGGER trg_organizations_updated_at
            BEFORE UPDATE ON organizations
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'trg_subscriptions_updated_at'
    ) THEN
        CREATE TRIGGER trg_subscriptions_updated_at
            BEFORE UPDATE ON subscriptions
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    END IF;
END;
$$;

COMMIT;
