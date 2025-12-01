-- Migration: Add ingestion_jobs table for PDF upload and job tracking
-- Created: 2025-11-30
-- Epic: Epic 1, Story 1.1

-- ============================================
-- Ingestion Jobs Table (Job Management)
-- ============================================

CREATE TABLE IF NOT EXISTS ingestion_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),

  -- Policy Information
  policy_name VARCHAR(500) NOT NULL,
  insurer VARCHAR(200) NOT NULL,
  launch_date VARCHAR(50),  -- ISO 8601 date string

  -- File Storage
  s3_key VARCHAR(1000) NOT NULL,  -- GCS object key

  -- Job Status
  status VARCHAR(50) DEFAULT 'pending' NOT NULL,
  -- Status values: 'pending', 'processing', 'completed', 'failed'

  -- Progress Tracking
  progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),

  -- Results (JSON)
  results JSONB DEFAULT NULL,
  -- Structure: {"nodes_created": 0, "edges_created": 0, "errors": [], "processing_time_seconds": 0.0}

  -- Error Handling
  error_message TEXT DEFAULT NULL,

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
  completed_at TIMESTAMP DEFAULT NULL,

  -- Constraints
  CONSTRAINT check_status_values CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  CONSTRAINT check_progress_range CHECK (progress >= 0 AND progress <= 100)
);

-- ============================================
-- Indexes for Performance
-- ============================================

-- Job ID lookup (most common query)
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_job_id
ON ingestion_jobs(job_id);

-- Status-based filtering
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status
ON ingestion_jobs(status);

-- Created date for sorting/filtering
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_created_at
ON ingestion_jobs(created_at DESC);

-- ============================================
-- Auto-update timestamp trigger
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_ingestion_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
DROP TRIGGER IF EXISTS trigger_update_ingestion_jobs_updated_at ON ingestion_jobs;
CREATE TRIGGER trigger_update_ingestion_jobs_updated_at
BEFORE UPDATE ON ingestion_jobs
FOR EACH ROW
EXECUTE FUNCTION update_ingestion_jobs_updated_at();

-- ============================================
-- Comments for documentation
-- ============================================

COMMENT ON TABLE ingestion_jobs IS 'Tracks PDF ingestion jobs with status and progress';
COMMENT ON COLUMN ingestion_jobs.job_id IS 'Public-facing job identifier for API responses';
COMMENT ON COLUMN ingestion_jobs.s3_key IS 'Google Cloud Storage object key for uploaded PDF';
COMMENT ON COLUMN ingestion_jobs.status IS 'Current job status: pending, processing, completed, failed';
COMMENT ON COLUMN ingestion_jobs.progress IS 'Job completion percentage (0-100)';
COMMENT ON COLUMN ingestion_jobs.results IS 'JSON object with processing results (nodes, edges, errors)';
