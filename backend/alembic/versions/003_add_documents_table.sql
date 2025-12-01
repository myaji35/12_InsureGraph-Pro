-- Migration: Add documents table for MVP search
-- Version: 003
-- Created: 2025-12-01
-- Description: Documents table with full-text search support for parsed insurance policies

-- ============================================================================
-- CREATE TABLE: documents
-- ============================================================================

CREATE TABLE IF NOT EXISTS documents (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Policy Information
    policy_name VARCHAR(500) NOT NULL,
    insurer VARCHAR(200) NOT NULL,
    policy_id UUID,  -- Reference to policy_metadata if applicable

    -- Content
    full_text TEXT NOT NULL,

    -- Parsed Structure (JSONB for flexible querying)
    parsed_structure JSONB NOT NULL,  -- ParsedDocument from legal parser
    critical_data JSONB NOT NULL,     -- ExtractionResult from critical data extractor

    -- Metadata
    total_pages INTEGER DEFAULT 0,
    total_chars INTEGER DEFAULT 0,
    total_articles INTEGER DEFAULT 0,
    total_paragraphs INTEGER DEFAULT 0,
    total_subclauses INTEGER DEFAULT 0,
    total_amounts INTEGER DEFAULT 0,
    total_periods INTEGER DEFAULT 0,
    total_kcd_codes INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Full-text search vector (auto-generated)
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('simple', coalesce(policy_name, '')), 'A') ||
        setweight(to_tsvector('simple', coalesce(insurer, '')), 'B') ||
        setweight(to_tsvector('simple', coalesce(full_text, '')), 'C')
    ) STORED
);

-- ============================================================================
-- CREATE INDEXES
-- ============================================================================

-- Full-text search index (GIN for tsvector)
CREATE INDEX IF NOT EXISTS idx_documents_search_vector
    ON documents USING GIN(search_vector);

-- Insurer filter
CREATE INDEX IF NOT EXISTS idx_documents_insurer
    ON documents(insurer);

-- Policy name search
CREATE INDEX IF NOT EXISTS idx_documents_policy_name
    ON documents(policy_name);

-- JSONB indexes for critical data queries
CREATE INDEX IF NOT EXISTS idx_documents_critical_data
    ON documents USING GIN(critical_data);

CREATE INDEX IF NOT EXISTS idx_documents_parsed_structure
    ON documents USING GIN(parsed_structure);

-- Timestamp indexes
CREATE INDEX IF NOT EXISTS idx_documents_created_at
    ON documents(created_at DESC);

-- Policy ID reference
CREATE INDEX IF NOT EXISTS idx_documents_policy_id
    ON documents(policy_id)
    WHERE policy_id IS NOT NULL;

-- ============================================================================
-- CREATE TRIGGER: Auto-update updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_documents_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_documents_updated_at();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE documents IS 'Parsed insurance policy documents with full-text search';
COMMENT ON COLUMN documents.id IS 'Document unique identifier';
COMMENT ON COLUMN documents.policy_name IS 'Insurance policy name';
COMMENT ON COLUMN documents.insurer IS 'Insurance company name';
COMMENT ON COLUMN documents.policy_id IS 'Reference to policy_metadata table';
COMMENT ON COLUMN documents.full_text IS 'Full extracted text from PDF';
COMMENT ON COLUMN documents.parsed_structure IS 'Hierarchical legal structure (articles, paragraphs, subclauses)';
COMMENT ON COLUMN documents.critical_data IS 'Extracted critical data (amounts, periods, KCD codes)';
COMMENT ON COLUMN documents.search_vector IS 'Auto-generated full-text search vector';

-- ============================================================================
-- GRANT PERMISSIONS (adjust as needed)
-- ============================================================================

-- Grant SELECT to all authenticated users
-- Grant INSERT/UPDATE/DELETE to application role
-- (Adjust based on your authentication setup)

COMMENT ON INDEX idx_documents_search_vector IS 'GIN index for full-text search performance';
COMMENT ON INDEX idx_documents_critical_data IS 'GIN index for JSONB queries on amounts, periods, codes';
