-- Story 3.4: Customer Portfolio Management
-- Add customers and customer_policies tables

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- FP association
    fp_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Basic info
    name VARCHAR(100) NOT NULL,
    birth_year INTEGER NOT NULL,
    gender VARCHAR(1) CHECK (gender IN ('M', 'F', 'O')),
    phone VARCHAR(20),  -- Masked for privacy
    email VARCHAR(255),
    occupation VARCHAR(100),
    
    -- Metadata
    last_contact_date TIMESTAMP,
    notes TEXT,
    consent_given BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_birth_year CHECK (birth_year BETWEEN 1900 AND EXTRACT(YEAR FROM CURRENT_DATE))
);

-- Customer policies table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS customer_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    
    -- Policy information
    policy_name VARCHAR(255) NOT NULL,
    insurer VARCHAR(100) NOT NULL,
    policy_type VARCHAR(50),  -- life, health, car, etc.
    
    -- Coverage details
    coverage_amount BIGINT,  -- in KRW
    premium_amount INTEGER,  -- monthly premium
    start_date DATE,
    end_date DATE,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled', 'pending')),
    
    -- Metadata
    notes TEXT,
    document_id UUID,  -- Reference to ingested policy document (if applicable)
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_customers_fp_user ON customers(fp_user_id);
CREATE INDEX idx_customers_name ON customers(name);
CREATE INDEX idx_customers_last_contact ON customers(last_contact_date DESC);

CREATE INDEX idx_customer_policies_customer ON customer_policies(customer_id);
CREATE INDEX idx_customer_policies_status ON customer_policies(status);
CREATE INDEX idx_customer_policies_type ON customer_policies(policy_type);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_customer_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_updated_at();

CREATE TRIGGER trigger_customer_policies_updated_at
    BEFORE UPDATE ON customer_policies
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_updated_at();

-- Comments
COMMENT ON TABLE customers IS 'FP customers with basic profile information';
COMMENT ON TABLE customer_policies IS 'Customer-owned insurance policies';
COMMENT ON COLUMN customers.phone IS 'Masked phone number for privacy (e.g., 010-****-1234)';
COMMENT ON COLUMN customers.consent_given IS 'Customer consent for data storage and analysis';
