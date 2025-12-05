-- Create crawler_urls table
-- Migration 004: Add crawler URLs management table

CREATE TABLE IF NOT EXISTS crawler_urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insurer VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on insurer for faster queries
CREATE INDEX IF NOT EXISTS idx_crawler_urls_insurer ON crawler_urls(insurer);

-- Create index on enabled status
CREATE INDEX IF NOT EXISTS idx_crawler_urls_enabled ON crawler_urls(enabled);

-- Insert default URLs for 메트라이프생명
INSERT INTO crawler_urls (insurer, url, description, enabled) VALUES
('메트라이프생명', 'https://www.metlife.co.kr/products', '상품 목록 페이지', true),
('메트라이프생명', 'https://www.metlife.co.kr/terms', '약관 다운로드 페이지', true);
