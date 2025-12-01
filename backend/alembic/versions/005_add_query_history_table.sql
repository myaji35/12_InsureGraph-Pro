-- Add query_history table for tracking user queries
-- Migration: 005_add_query_history_table
-- Created: 2025-12-01

CREATE TABLE IF NOT EXISTS query_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    customer_id UUID NULL,
    query_text TEXT NOT NULL,
    intent VARCHAR(100),
    answer TEXT,
    confidence DECIMAL(3,2),
    source_documents JSONB,
    reasoning_path JSONB,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT fk_query_history_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_query_history_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(id)
        ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX idx_query_history_user_id ON query_history(user_id);
CREATE INDEX idx_query_history_customer_id ON query_history(customer_id);
CREATE INDEX idx_query_history_created_at ON query_history(created_at DESC);
CREATE INDEX idx_query_history_user_created ON query_history(user_id, created_at DESC);

-- Comments
COMMENT ON TABLE query_history IS 'Stores history of all user queries for analytics and audit';
COMMENT ON COLUMN query_history.user_id IS 'FP or GA user who made the query';
COMMENT ON COLUMN query_history.customer_id IS 'Optional customer context if query was made in customer context';
COMMENT ON COLUMN query_history.query_text IS 'Original natural language query from user';
COMMENT ON COLUMN query_history.intent IS 'Parsed intent from query parser';
COMMENT ON COLUMN query_history.answer IS 'Generated answer text';
COMMENT ON COLUMN query_history.confidence IS 'Confidence score (0.00 to 1.00)';
COMMENT ON COLUMN query_history.source_documents IS 'JSON array of source document references';
COMMENT ON COLUMN query_history.reasoning_path IS 'JSON representation of graph reasoning path';
COMMENT ON COLUMN query_history.execution_time_ms IS 'Query execution time in milliseconds';
