-- Add processing_step column to crawler_documents table
ALTER TABLE crawler_documents
ADD COLUMN processing_step VARCHAR(100) DEFAULT NULL;

-- Add processing_progress column for percentage
ALTER TABLE crawler_documents
ADD COLUMN processing_progress INTEGER DEFAULT 0;

-- Update existing processing documents to have a step
UPDATE crawler_documents
SET processing_step = 'initializing', processing_progress = 10
WHERE status = 'processing';

-- Comment on columns
COMMENT ON COLUMN crawler_documents.processing_step IS 'Current step in the processing pipeline';
COMMENT ON COLUMN crawler_documents.processing_progress IS 'Processing progress percentage (0-100)';