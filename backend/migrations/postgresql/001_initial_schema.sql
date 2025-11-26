-- Migration: 001_initial_schema
-- Description: Initial database schema for InsureGraph Pro
-- Author: Backend Team
-- Date: 2025-11-25

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- User Management Tables
-- ============================================

-- GA (General Agency) Organizations
CREATE TABLE gas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    business_number VARCHAR(50) UNIQUE,
    contract_type VARCHAR(50) NOT NULL DEFAULT 'free',
    max_fps INTEGER,
    contract_start DATE,
    contract_end DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_gas_business_number ON gas(business_number);
CREATE INDEX idx_gas_is_active ON gas(is_active);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'fp',
    tier VARCHAR(50) NOT NULL DEFAULT 'free',
    ga_id UUID REFERENCES gas(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT chk_role CHECK (role IN ('fp', 'ga_manager', 'admin', 'end_user')),
    CONSTRAINT chk_tier CHECK (tier IN ('free', 'pro', 'enterprise'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_ga_id ON users(ga_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);

-- User Permissions
CREATE TABLE user_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission VARCHAR(100) NOT NULL,
    granted_at TIMESTAMP DEFAULT NOW(),
    granted_by UUID REFERENCES users(id),

    UNIQUE(user_id, permission)
);

CREATE INDEX idx_user_permissions_user_id ON user_permissions(user_id);

-- ============================================
-- Customer Management Tables (PII Encrypted)
-- ============================================

CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fp_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- PII fields (encrypted/hashed)
    name_encrypted BYTEA NOT NULL,
    phone_hash VARCHAR(64),  -- SHA-256 hash
    email_encrypted BYTEA,

    -- Non-PII fields
    birth_year INTEGER,
    gender CHAR(1),
    occupation VARCHAR(100),

    -- Consent tracking
    consent_id VARCHAR(100),
    consent_date TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT chk_gender CHECK (gender IN ('M', 'F', 'O')),
    CONSTRAINT chk_birth_year CHECK (birth_year >= 1900 AND birth_year <= EXTRACT(YEAR FROM NOW()))
);

CREATE INDEX idx_customers_fp_id ON customers(fp_id);
CREATE INDEX idx_customers_birth_year ON customers(birth_year);
CREATE INDEX idx_customers_phone_hash ON customers(phone_hash);

-- Customer Policies (many-to-many with products)
CREATE TABLE customer_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    product_id UUID NOT NULL,  -- References Neo4j Product node
    purchase_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    premium_amount INTEGER,
    policy_number VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT chk_status CHECK (status IN ('active', 'expired', 'cancelled')),
    UNIQUE(customer_id, product_id)
);

CREATE INDEX idx_customer_policies_customer_id ON customer_policies(customer_id);
CREATE INDEX idx_customer_policies_product_id ON customer_policies(product_id);

-- ============================================
-- Ingestion Job Management
-- ============================================

CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- File information
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    file_url TEXT NOT NULL,  -- GCS URL
    file_hash VARCHAR(64),  -- SHA-256 for deduplication

    -- Job status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    current_stage VARCHAR(100),

    -- Metadata
    metadata JSONB NOT NULL DEFAULT '{}',

    -- Results
    results JSONB,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    CONSTRAINT chk_status CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    CONSTRAINT chk_progress CHECK (progress >= 0 AND progress <= 100)
);

CREATE INDEX idx_ingestion_jobs_user_id ON ingestion_jobs(user_id);
CREATE INDEX idx_ingestion_jobs_status ON ingestion_jobs(status);
CREATE INDEX idx_ingestion_jobs_created_at ON ingestion_jobs(created_at DESC);
CREATE INDEX idx_ingestion_jobs_file_hash ON ingestion_jobs(file_hash);

-- Ingestion Job Stages (for tracking pipeline progress)
CREATE TABLE ingestion_job_stages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES ingestion_jobs(id) ON DELETE CASCADE,
    stage_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,

    CONSTRAINT chk_status CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    UNIQUE(job_id, stage_name)
);

CREATE INDEX idx_ingestion_job_stages_job_id ON ingestion_job_stages(job_id);

-- ============================================
-- Query Management & Analytics
-- ============================================

CREATE TABLE query_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    customer_id UUID REFERENCES customers(id),

    -- Query details
    query_text TEXT NOT NULL,
    query_type VARCHAR(50),
    classification_confidence FLOAT,

    -- Graph query details
    graph_query TEXT,  -- Cypher query executed
    product_ids UUID[],  -- Array of product IDs queried

    -- Results
    result_confidence FLOAT,
    result_status VARCHAR(50),
    answer_summary TEXT,

    -- Performance
    execution_time_ms INTEGER,
    model_used VARCHAR(50),
    cost_usd DECIMAL(10, 4),

    -- Client info
    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT chk_result_status CHECK (result_status IN ('high_confidence', 'medium_confidence', 'needs_review', 'failed'))
);

CREATE INDEX idx_query_logs_user_id ON query_logs(user_id);
CREATE INDEX idx_query_logs_customer_id ON query_logs(customer_id);
CREATE INDEX idx_query_logs_created_at ON query_logs(created_at DESC);
CREATE INDEX idx_query_logs_query_type ON query_logs(query_type);
CREATE INDEX idx_query_logs_result_status ON query_logs(result_status);

-- Query Sources (which clauses were used)
CREATE TABLE query_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_log_id UUID NOT NULL REFERENCES query_logs(id) ON DELETE CASCADE,
    clause_id UUID NOT NULL,  -- References Neo4j Clause node
    relevance_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_query_sources_query_log_id ON query_sources(query_log_id);
CREATE INDEX idx_query_sources_clause_id ON query_sources(clause_id);

-- ============================================
-- Compliance & Audit Logs
-- ============================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    user_id UUID REFERENCES users(id),
    role VARCHAR(50),

    -- Action details
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),

    -- Result
    result VARCHAR(20) NOT NULL DEFAULT 'success',

    -- Additional context
    details JSONB,

    -- Client info
    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT chk_result CHECK (result IN ('success', 'failure'))
);

CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- Expert Review Queue (for low-confidence answers)
CREATE TABLE expert_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_log_id UUID NOT NULL REFERENCES query_logs(id) ON DELETE CASCADE,

    -- Original response
    llm_answer TEXT NOT NULL,
    graph_paths JSONB,
    confidence FLOAT,

    -- Review
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    reviewer_id UUID REFERENCES users(id),
    review_notes TEXT,
    correct_answer TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,

    CONSTRAINT chk_status CHECK (status IN ('pending', 'approved', 'rejected'))
);

CREATE INDEX idx_expert_reviews_status ON expert_reviews(status);
CREATE INDEX idx_expert_reviews_created_at ON expert_reviews(created_at DESC);
CREATE INDEX idx_expert_reviews_reviewer_id ON expert_reviews(reviewer_id);

-- Script Compliance Validations
CREATE TABLE script_validations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- Script details
    original_script TEXT NOT NULL,
    corrected_script TEXT,

    -- Validation results
    is_compliant BOOLEAN NOT NULL,
    risk_score INTEGER,
    violations JSONB,

    -- Context
    product_id UUID,
    customer_id UUID REFERENCES customers(id),

    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT chk_risk_score CHECK (risk_score >= 0 AND risk_score <= 100)
);

CREATE INDEX idx_script_validations_user_id ON script_validations(user_id);
CREATE INDEX idx_script_validations_is_compliant ON script_validations(is_compliant);
CREATE INDEX idx_script_validations_created_at ON script_validations(created_at DESC);

-- ============================================
-- Analytics & Reporting
-- ============================================

-- Daily Analytics (pre-aggregated for performance)
CREATE TABLE daily_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL,
    user_id UUID REFERENCES users(id),
    ga_id UUID REFERENCES gas(id),

    -- Metrics
    total_queries INTEGER DEFAULT 0,
    successful_queries INTEGER DEFAULT 0,
    failed_queries INTEGER DEFAULT 0,
    avg_confidence FLOAT,
    avg_execution_time_ms INTEGER,
    total_cost_usd DECIMAL(10, 4),

    -- Customer activity
    active_customers INTEGER DEFAULT 0,
    new_customers INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(date, user_id)
);

CREATE INDEX idx_daily_analytics_date ON daily_analytics(date DESC);
CREATE INDEX idx_daily_analytics_user_id ON daily_analytics(user_id);
CREATE INDEX idx_daily_analytics_ga_id ON daily_analytics(ga_id);

-- ============================================
-- System Configuration
-- ============================================

CREATE TABLE system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_system_config_key ON system_config(key);

-- ============================================
-- Rate Limiting
-- ============================================

CREATE TABLE rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(100) NOT NULL,
    request_count INTEGER DEFAULT 0,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, endpoint, window_start)
);

CREATE INDEX idx_rate_limits_user_id ON rate_limits(user_id);
CREATE INDEX idx_rate_limits_window_end ON rate_limits(window_end);

-- ============================================
-- Triggers for updated_at
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_gas_updated_at BEFORE UPDATE ON gas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Seed Data (Optional)
-- ============================================

-- Insert default system admin user (password: Admin123! - CHANGE THIS!)
INSERT INTO users (id, email, password_hash, role, tier, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'admin@insuregraph.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lWn0hJJe/Rhi',  -- bcrypt hash of "Admin123!"
    'admin',
    'enterprise',
    TRUE
);

-- Insert default system configuration
INSERT INTO system_config (key, value, description)
VALUES
    ('confidence_thresholds', '{"high": 0.85, "medium": 0.70, "low": 0.60}', 'Confidence score thresholds'),
    ('rate_limits', '{"free": {"queries_per_day": 50}, "pro": {"queries_per_day": 1000}, "enterprise": {"queries_per_day": -1}}', 'Rate limits by tier'),
    ('llm_config', '{"primary_model": "solar-pro", "fallback_model": "gpt-4o", "cascade_threshold": 0.7}', 'LLM configuration');

-- ============================================
-- Comments
-- ============================================

COMMENT ON TABLE users IS 'User accounts (FPs, GA managers, admins)';
COMMENT ON TABLE customers IS 'Customer records with encrypted PII';
COMMENT ON TABLE ingestion_jobs IS 'Policy PDF ingestion job tracking';
COMMENT ON TABLE query_logs IS 'Query execution logs for analytics';
COMMENT ON TABLE audit_logs IS 'Comprehensive audit trail for compliance';
COMMENT ON TABLE expert_reviews IS 'Expert review queue for low-confidence answers';

-- ============================================
-- Grants (adjust based on your user setup)
-- ============================================

-- Grant permissions to application user
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO insuregraph_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO insuregraph_app;

-- Migration complete
SELECT 'Migration 001_initial_schema completed successfully' AS status;
