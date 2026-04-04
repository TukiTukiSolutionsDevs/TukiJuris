-- ============================================
-- AGENTE DERECHO — Database Initialization
-- ============================================
-- This runs on first container startup only.

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";       -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS "pg_trgm";      -- Trigram for fuzzy text search

-- ============================================
-- USERS
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(320) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    plan VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================
-- CONVERSATIONS & MESSAGES
-- ============================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    legal_area VARCHAR(100),
    model_used VARCHAR(100) DEFAULT 'gpt-4o-mini',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    agent_used VARCHAR(100),
    citations JSONB,
    tokens_used INTEGER,
    latency_ms INTEGER,
    feedback VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);

-- ============================================
-- LEGAL DOCUMENTS (Knowledge Base)
-- ============================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(1000) NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    document_number VARCHAR(200),
    legal_area VARCHAR(100) NOT NULL,
    hierarchy VARCHAR(50),
    source VARCHAR(200) NOT NULL,
    source_url TEXT,
    publication_date DATE,
    modification_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    raw_text TEXT,
    metadata_extra JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_area ON documents(legal_area);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_number ON documents(document_number);

-- Full-text search index for BM25-like retrieval
CREATE INDEX IF NOT EXISTS idx_documents_fts ON documents
    USING GIN (to_tsvector('spanish', COALESCE(title, '') || ' ' || COALESCE(raw_text, '')));

-- ============================================
-- DOCUMENT CHUNKS (for RAG / vector search)
-- ============================================
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    legal_area VARCHAR(100) NOT NULL,
    article_number VARCHAR(50),
    section_path TEXT,
    token_count INTEGER,
    metadata_extra JSONB,
    embedding vector(1536),  -- pgvector column for embeddings
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_area ON document_chunks(legal_area);
CREATE INDEX IF NOT EXISTS idx_chunks_article ON document_chunks(article_number);

-- HNSW index for fast vector similarity search
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON document_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);

-- Full-text search on chunks for hybrid retrieval
CREATE INDEX IF NOT EXISTS idx_chunks_fts ON document_chunks
    USING GIN (to_tsvector('spanish', content));

-- ============================================
-- LEGAL AREAS (Reference table)
-- ============================================
CREATE TABLE IF NOT EXISTS legal_areas (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    parent_area VARCHAR(50) REFERENCES legal_areas(id),
    icon VARCHAR(50),
    sort_order INTEGER DEFAULT 0
);

INSERT INTO legal_areas (id, name, description, sort_order) VALUES
    ('civil', 'Derecho Civil', 'Código Civil, CPC, Familia, Sucesiones, Contratos, Obligaciones, Reales', 1),
    ('penal', 'Derecho Penal', 'Código Penal, NCPP, Ejecución Penal, Delitos especiales', 2),
    ('laboral', 'Derecho Laboral', 'LPCL, CTS, Gratificaciones, SST, Relaciones Colectivas', 3),
    ('tributario', 'Derecho Tributario', 'Código Tributario, IR, IGV, SUNAT, Tribunal Fiscal', 4),
    ('administrativo', 'Derecho Administrativo', 'LPAG, Contrataciones del Estado, Silencio Administrativo', 5),
    ('corporativo', 'Derecho Corporativo', 'LGS, Mercado de Valores, MYPE, Código de Comercio', 6),
    ('constitucional', 'Derecho Constitucional', 'Constitución 1993, Procesos Constitucionales, TC', 7),
    ('registral', 'Derecho Registral', 'SUNARP, Registros Públicos, Procedimientos registrales', 8),
    ('competencia', 'Competencia y PI', 'INDECOPI, Marcas, Patentes, Consumidor, Publicidad', 9),
    ('compliance', 'Compliance', 'Datos Personales, Anticorrupción, Lavado de Activos', 10),
    ('comercio_exterior', 'Comercio Exterior', 'Aduanas, TLC, MINCETUR, Regímenes aduaneros', 11)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- Helper function: Hybrid search (BM25 + Vector)
-- ============================================
CREATE OR REPLACE FUNCTION hybrid_search(
    query_text TEXT,
    query_embedding vector(1536),
    area_filter VARCHAR(100) DEFAULT NULL,
    match_limit INTEGER DEFAULT 10,
    bm25_weight FLOAT DEFAULT 0.4,
    vector_weight FLOAT DEFAULT 0.6
)
RETURNS TABLE (
    chunk_id UUID,
    content TEXT,
    legal_area VARCHAR(100),
    article_number VARCHAR(50),
    section_path TEXT,
    document_title VARCHAR(1000),
    document_number VARCHAR(200),
    combined_score FLOAT
)
LANGUAGE sql STABLE
AS $$
    WITH bm25_results AS (
        SELECT
            dc.id,
            dc.content,
            dc.legal_area,
            dc.article_number,
            dc.section_path,
            d.title AS document_title,
            d.document_number,
            ts_rank_cd(to_tsvector('spanish', dc.content), plainto_tsquery('spanish', query_text)) AS score
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE
            (area_filter IS NULL OR dc.legal_area = area_filter)
            AND to_tsvector('spanish', dc.content) @@ plainto_tsquery('spanish', query_text)
        ORDER BY score DESC
        LIMIT match_limit * 2
    ),
    vector_results AS (
        SELECT
            dc.id,
            dc.content,
            dc.legal_area,
            dc.article_number,
            dc.section_path,
            d.title AS document_title,
            d.document_number,
            1 - (dc.embedding <=> query_embedding) AS score
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE
            (area_filter IS NULL OR dc.legal_area = area_filter)
            AND dc.embedding IS NOT NULL
        ORDER BY dc.embedding <=> query_embedding
        LIMIT match_limit * 2
    ),
    combined AS (
        SELECT
            COALESCE(b.id, v.id) AS id,
            COALESCE(b.content, v.content) AS content,
            COALESCE(b.legal_area, v.legal_area) AS legal_area,
            COALESCE(b.article_number, v.article_number) AS article_number,
            COALESCE(b.section_path, v.section_path) AS section_path,
            COALESCE(b.document_title, v.document_title) AS document_title,
            COALESCE(b.document_number, v.document_number) AS document_number,
            (COALESCE(b.score, 0) * bm25_weight + COALESCE(v.score, 0) * vector_weight) AS combined_score
        FROM bm25_results b
        FULL OUTER JOIN vector_results v ON b.id = v.id
    )
    SELECT
        c.id AS chunk_id,
        c.content,
        c.legal_area,
        c.article_number,
        c.section_path,
        c.document_title,
        c.document_number,
        c.combined_score
    FROM combined c
    ORDER BY c.combined_score DESC
    LIMIT match_limit;
$$;

-- ============================================
-- ORGANIZATIONS (Multi-tenant)
-- ============================================
CREATE TABLE IF NOT EXISTS organizations (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                    VARCHAR(255) NOT NULL,
    slug                    VARCHAR(100) NOT NULL UNIQUE,
    plan                    VARCHAR(50)  NOT NULL DEFAULT 'free',
    plan_queries_limit      INTEGER      NOT NULL DEFAULT 100,
    plan_models_allowed     JSONB        NOT NULL DEFAULT '["gpt-4o-mini"]',
    is_active               BOOLEAN      NOT NULL DEFAULT TRUE,
    stripe_customer_id      VARCHAR(100),
    stripe_subscription_id  VARCHAR(100),
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_organizations_slug   ON organizations(slug);
CREATE INDEX IF NOT EXISTS idx_organizations_plan   ON organizations(plan);

-- Add optional org FK to users
ALTER TABLE users ADD COLUMN IF NOT EXISTS default_org_id UUID REFERENCES organizations(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_users_default_org ON users(default_org_id) WHERE default_org_id IS NOT NULL;

-- ============================================
-- ORG MEMBERSHIPS
-- ============================================
CREATE TABLE IF NOT EXISTS org_memberships (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID        NOT NULL REFERENCES users(id)         ON DELETE CASCADE,
    organization_id UUID        NOT NULL REFERENCES organizations(id)  ON DELETE CASCADE,
    role            VARCHAR(50) NOT NULL DEFAULT 'member',
    invited_by      UUID        REFERENCES users(id)         ON DELETE SET NULL,
    invited_at      TIMESTAMPTZ,
    joined_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_membership UNIQUE (user_id, organization_id)
);

CREATE INDEX IF NOT EXISTS idx_memberships_user         ON org_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_memberships_organization ON org_memberships(organization_id);

-- ============================================
-- SUBSCRIPTIONS (Billing skeleton)
-- ============================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id                      UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id         UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    plan                    VARCHAR(50) NOT NULL,
    status                  VARCHAR(50) NOT NULL DEFAULT 'active',
    current_period_start    TIMESTAMPTZ,
    current_period_end      TIMESTAMPTZ,
    stripe_subscription_id  VARCHAR(100),
    stripe_price_id         VARCHAR(100),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_organization ON subscriptions(organization_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status       ON subscriptions(status);

-- ============================================
-- USAGE RECORDS (Query tracking per org)
-- ============================================
CREATE TABLE IF NOT EXISTS usage_records (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id         UUID        NOT NULL REFERENCES users(id)         ON DELETE CASCADE,
    month           VARCHAR(7)  NOT NULL,
    queries_used    INTEGER     NOT NULL DEFAULT 0,
    tokens_used     INTEGER     NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_usage_record UNIQUE (organization_id, user_id, month)
);

CREATE INDEX IF NOT EXISTS idx_usage_org_month ON usage_records(organization_id, month);

-- ============================================
-- updated_at trigger (for new tables)
-- ============================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
