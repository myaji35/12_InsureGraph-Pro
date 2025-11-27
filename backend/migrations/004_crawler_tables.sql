-- Crawler Tables Migration
-- Created: 2025-11-27
-- Purpose: Store crawler configurations and job results

-- Drop tables if they exist (for development)
DROP TABLE IF EXISTS crawler_job_documents CASCADE;
DROP TABLE IF EXISTS crawler_jobs CASCADE;
DROP TABLE IF EXISTS crawler_configs CASCADE;

-- 크롤러 설정 테이블
CREATE TABLE crawler_configs (
    config_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(100) NOT NULL UNIQUE,
    base_url VARCHAR(500) NOT NULL,
    policy_page_urls JSONB NOT NULL DEFAULT '[]', -- Array of URLs to crawl
    selectors JSONB NOT NULL DEFAULT '{}', -- CSS selectors for scraping
    respect_robots_txt BOOLEAN DEFAULT TRUE,
    enabled BOOLEAN DEFAULT FALSE,
    crawl_schedule VARCHAR(50), -- Cron expression (e.g., "0 2 * * *" for daily at 2am)
    last_crawled_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id UUID -- Will add FK constraint when users table exists
);

-- 크롤러 작업 테이블
CREATE TABLE crawler_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID REFERENCES crawler_configs(config_id) ON DELETE CASCADE,
    company_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, running, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    total_documents_found INTEGER DEFAULT 0,
    documents_downloaded INTEGER DEFAULT 0,
    documents_processed INTEGER DEFAULT 0,
    errors JSONB DEFAULT '[]', -- Array of error messages
    result_summary JSONB, -- Summary of crawl results
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 크롤러가 발견한 문서 목록
CREATE TABLE crawler_job_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES crawler_jobs(job_id) ON DELETE CASCADE,
    doc_hash VARCHAR(32) NOT NULL, -- MD5 hash of URL for deduplication
    url VARCHAR(1000) NOT NULL,
    product_name VARCHAR(200),
    product_code VARCHAR(50),
    description TEXT,
    source_page VARCHAR(1000),
    insurer VARCHAR(100),
    download_status VARCHAR(20) DEFAULT 'pending', -- pending, downloaded, failed
    downloaded_at TIMESTAMP,
    document_id UUID REFERENCES documents(document_id) ON DELETE SET NULL, -- Link to processed document
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint: same URL should not be crawled multiple times in one job
    UNIQUE(job_id, doc_hash)
);

-- Indexes for performance
CREATE INDEX idx_crawler_configs_company ON crawler_configs(company_name);
CREATE INDEX idx_crawler_configs_enabled ON crawler_configs(enabled);
CREATE INDEX idx_crawler_jobs_status ON crawler_jobs(status);
CREATE INDEX idx_crawler_jobs_created_at ON crawler_jobs(created_at DESC);
CREATE INDEX idx_crawler_job_documents_job_id ON crawler_job_documents(job_id);
CREATE INDEX idx_crawler_job_documents_doc_hash ON crawler_job_documents(doc_hash);
CREATE INDEX idx_crawler_job_documents_download_status ON crawler_job_documents(download_status);
CREATE INDEX idx_crawler_job_documents_document_id ON crawler_job_documents(document_id);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_crawler_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_crawler_configs_updated_at
    BEFORE UPDATE ON crawler_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_crawler_updated_at();

CREATE TRIGGER trigger_crawler_jobs_updated_at
    BEFORE UPDATE ON crawler_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_crawler_updated_at();

-- Insert default crawler configurations for major Korean insurance companies
INSERT INTO crawler_configs (company_name, base_url, policy_page_urls, selectors, enabled, notes) VALUES
('삼성화재', 'https://www.samsungfire.com',
 '["https://www.samsungfire.com/personal/product/list.html"]'::jsonb,
 '{"product_links": "a.product-link", "pdf_links": "a[href*=\"약관\"]", "product_name": "h3.product-title"}'::jsonb,
 FALSE,
 '실제 크롤링 전 웹사이트 구조 확인 및 selectors 업데이트 필요'),

('한화생명', 'https://www.hanwhalife.com',
 '["https://www.hanwhalife.com/product/list.do"]'::jsonb,
 '{"pdf_links": "a.btn-terms", "product_name": "div.product-name"}'::jsonb,
 FALSE,
 '실제 크롤링 전 웹사이트 구조 확인 및 selectors 업데이트 필요'),

('교보생명', 'https://www.kyobo.com',
 '["https://www.kyobo.com/product/list"]'::jsonb,
 '{"pdf_links": "a[href$=\".pdf\"]", "product_name": "h2.product-title"}'::jsonb,
 FALSE,
 '실제 크롤링 전 웹사이트 구조 확인 및 selectors 업데이트 필요'),

('KB손해보험', 'https://www.kbinsure.co.kr',
 '["https://www.kbinsure.co.kr/CG302120001.ec"]'::jsonb,
 '{"pdf_links": "a[href*=\"Terms\"]", "product_name": "div.prd-name"}'::jsonb,
 FALSE,
 '실제 크롤링 전 웹사이트 구조 확인 및 selectors 업데이트 필요'),

('현대해상', 'https://www.hi.co.kr',
 '["https://www.hi.co.kr/product/index.do"]'::jsonb,
 '{"pdf_links": "a.pdf-link", "product_name": "strong.product-name"}'::jsonb,
 FALSE,
 '실제 크롤링 전 웹사이트 구조 확인 및 selectors 업데이트 필요');

-- Comments
COMMENT ON TABLE crawler_configs IS '보험사별 크롤러 설정';
COMMENT ON TABLE crawler_jobs IS '크롤러 작업 기록';
COMMENT ON TABLE crawler_job_documents IS '크롤러가 발견한 문서 목록';

COMMENT ON COLUMN crawler_configs.crawl_schedule IS 'Cron 표현식. 예: "0 2 * * *" (매일 새벽 2시)';
COMMENT ON COLUMN crawler_jobs.result_summary IS 'JSON 형식의 크롤 결과 요약';
COMMENT ON COLUMN crawler_job_documents.doc_hash IS 'URL의 MD5 해시값 (중복 체크용)';
