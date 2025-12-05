-- Add processing_detail column to crawler_documents table
-- This will store detailed information about the extraction process in JSON format
ALTER TABLE crawler_documents
ADD COLUMN processing_detail JSONB DEFAULT NULL;

-- Comment on column
COMMENT ON COLUMN crawler_documents.processing_detail IS 'Detailed processing information including sub-steps, pages processed, OCR progress, etc.';