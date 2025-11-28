-- Migration: Add policy_metadata table for Human-in-the-Loop data collection
-- Created: 2025-11-28
-- Epic: Epic 1, Story 1.0

-- ============================================
-- Policy Metadata Table (Human-in-the-Loop)
-- ============================================

CREATE TABLE IF NOT EXISTS policy_metadata (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Source Information
  insurer VARCHAR(255) NOT NULL,
  category VARCHAR(100),  -- 'cancer', 'life', 'annuity', 'disability', etc.
  policy_name VARCHAR(500) NOT NULL,
  file_name VARCHAR(500),
  publication_date DATE,
  download_url TEXT NOT NULL,  -- Original source URL from insurer website

  -- Lifecycle Status
  status VARCHAR(50) DEFAULT 'DISCOVERED' NOT NULL,
  -- Status values: 'DISCOVERED', 'QUEUED', 'DOWNLOADING', 'PROCESSING', 'COMPLETED', 'FAILED', 'IGNORED'

  -- Curation Information
  queued_by UUID REFERENCES users(id) ON DELETE SET NULL,  -- Admin who queued this for learning
  queued_at TIMESTAMP,

  -- Timestamps
  discovered_at TIMESTAMP DEFAULT NOW() NOT NULL,
  last_updated TIMESTAMP DEFAULT NOW() NOT NULL,

  -- Manual Review
  notes TEXT,  -- Manual review notes

  -- Additional Metadata (flexible JSON storage)
  metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- Indexes for Performance
-- ============================================

-- Status-based filtering (most common query)
CREATE INDEX IF NOT EXISTS idx_policy_metadata_status
ON policy_metadata(status);

-- Insurer-based filtering
CREATE INDEX IF NOT EXISTS idx_policy_metadata_insurer
ON policy_metadata(insurer);

-- Publication date for chronological sorting
CREATE INDEX IF NOT EXISTS idx_policy_metadata_publication_date
ON policy_metadata(publication_date DESC);

-- Discovery date for recent items
CREATE INDEX IF NOT EXISTS idx_policy_metadata_discovered_at
ON policy_metadata(discovered_at DESC);

-- Category-based filtering
CREATE INDEX IF NOT EXISTS idx_policy_metadata_category
ON policy_metadata(category) WHERE category IS NOT NULL;

-- Full-text search on policy name and file name
CREATE INDEX IF NOT EXISTS idx_policy_metadata_search
ON policy_metadata USING GIN (to_tsvector('english', policy_name || ' ' || COALESCE(file_name, '')));

-- Composite index for common query pattern (status + insurer)
CREATE INDEX IF NOT EXISTS idx_policy_metadata_status_insurer
ON policy_metadata(status, insurer);

-- ============================================
-- Update ingestion_jobs to link with policy_metadata
-- ============================================

ALTER TABLE ingestion_jobs
ADD COLUMN IF NOT EXISTS policy_metadata_id UUID REFERENCES policy_metadata(id) ON DELETE SET NULL;

-- Index for foreign key
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_policy_metadata_id
ON ingestion_jobs(policy_metadata_id);

-- Add download_url to track original source
ALTER TABLE ingestion_jobs
ADD COLUMN IF NOT EXISTS download_url TEXT;

-- ============================================
-- Trigger to update last_updated timestamp
-- ============================================

CREATE OR REPLACE FUNCTION update_policy_metadata_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.last_updated = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_policy_metadata_timestamp
BEFORE UPDATE ON policy_metadata
FOR EACH ROW
EXECUTE FUNCTION update_policy_metadata_timestamp();

-- ============================================
-- Constraints and Validations
-- ============================================

-- Check constraint for valid status values
ALTER TABLE policy_metadata
ADD CONSTRAINT check_policy_metadata_status
CHECK (status IN ('DISCOVERED', 'QUEUED', 'DOWNLOADING', 'PROCESSING', 'COMPLETED', 'FAILED', 'IGNORED'));

-- Ensure download_url is valid URL format
ALTER TABLE policy_metadata
ADD CONSTRAINT check_policy_metadata_download_url
CHECK (download_url ~ '^https?://');

-- ============================================
-- Comments for Documentation
-- ============================================

COMMENT ON TABLE policy_metadata IS 'Metadata catalog for discovered insurance policies. Supports Human-in-the-Loop curation workflow.';
COMMENT ON COLUMN policy_metadata.status IS 'Lifecycle status: DISCOVERED (crawler found) → QUEUED (admin selected) → DOWNLOADING/PROCESSING → COMPLETED/FAILED/IGNORED';
COMMENT ON COLUMN policy_metadata.download_url IS 'Original source URL from insurer website. Used by on-demand downloader.';
COMMENT ON COLUMN policy_metadata.queued_by IS 'Admin user who approved this policy for learning';
COMMENT ON COLUMN policy_metadata.notes IS 'Manual review notes (e.g., why ignored, special handling needed)';
