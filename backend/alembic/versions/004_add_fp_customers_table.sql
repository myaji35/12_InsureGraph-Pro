-- FP 고객 관리 테이블CREATE TABLE IF NOT EXISTS fp_customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,  -- Clerk user ID
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(255),
    birth_date DATE,
    gender VARCHAR(10),
    address TEXT,
    tags TEXT[],  -- PostgreSQL array for tags
    status VARCHAR(50) DEFAULT 'prospect',  -- active, inactive, prospect
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 상담 이력 테이블
CREATE TABLE IF NOT EXISTS fp_consultations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES fp_customers(id) ON DELETE CASCADE,
    consultation_date TIMESTAMP WITH TIME ZONE NOT NULL,
    consultation_type VARCHAR(50),  -- phone, meeting, email, etc.
    subject VARCHAR(255),
    content TEXT,
    next_action VARCHAR(255),
    next_action_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 판매 상품 테이블
CREATE TABLE IF NOT EXISTS fp_customer_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES fp_customers(id) ON DELETE CASCADE,
    product_name VARCHAR(255) NOT NULL,
    product_type VARCHAR(100),  -- life, health, property, etc.
    insurer VARCHAR(255),
    policy_number VARCHAR(100),
    start_date DATE,
    end_date DATE,
    premium DECIMAL(12, 2),
    coverage_amount DECIMAL(15, 2),
    status VARCHAR(50) DEFAULT 'active',  -- active, expired, cancelled
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_fp_customers_user_id ON fp_customers(user_id);
CREATE INDEX IF NOT EXISTS idx_fp_customers_status ON fp_customers(status);
CREATE INDEX IF NOT EXISTS idx_fp_consultations_customer_id ON fp_consultations(customer_id);
CREATE INDEX IF NOT EXISTS idx_fp_consultations_date ON fp_consultations(consultation_date);
CREATE INDEX IF NOT EXISTS idx_fp_customer_products_customer_id ON fp_customer_products(customer_id);
