-- 005: Add crawler_documents table for storing crawled PDF documents
-- Created: 2025-12-02

-- Create crawler_documents table
CREATE TABLE IF NOT EXISTS crawler_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insurer VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    pdf_url TEXT NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,  -- '약관' or '특약'
    product_type VARCHAR(100),  -- 상품 유형 (예: 종신보험, 정기보험 등)
    source_url TEXT,  -- 크롤링한 원본 URL
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'downloaded', 'processed', 'failed'
    file_path TEXT,  -- 다운로드한 파일 경로
    error_message TEXT,  -- 에러 메시지 (있는 경우)
    metadata JSONB DEFAULT '{}',  -- 추가 메타데이터
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_crawler_documents_insurer ON crawler_documents(insurer);
CREATE INDEX IF NOT EXISTS idx_crawler_documents_status ON crawler_documents(status);
CREATE INDEX IF NOT EXISTS idx_crawler_documents_category ON crawler_documents(category);
CREATE INDEX IF NOT EXISTS idx_crawler_documents_product_type ON crawler_documents(product_type);
CREATE INDEX IF NOT EXISTS idx_crawler_documents_created_at ON crawler_documents(created_at DESC);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_crawler_documents_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_crawler_documents_updated_at
    BEFORE UPDATE ON crawler_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_crawler_documents_updated_at();

-- Add comments
COMMENT ON TABLE crawler_documents IS '크롤링으로 수집한 보험약관 문서 정보';
COMMENT ON COLUMN crawler_documents.id IS '문서 고유 ID';
COMMENT ON COLUMN crawler_documents.insurer IS '보험사명';
COMMENT ON COLUMN crawler_documents.title IS '문서 제목';
COMMENT ON COLUMN crawler_documents.pdf_url IS 'PDF 파일 URL';
COMMENT ON COLUMN crawler_documents.category IS '문서 카테고리 (약관/특약)';
COMMENT ON COLUMN crawler_documents.product_type IS '상품 유형';
COMMENT ON COLUMN crawler_documents.source_url IS '크롤링한 원본 페이지 URL';
COMMENT ON COLUMN crawler_documents.status IS '처리 상태 (pending, downloaded, processed, failed)';
COMMENT ON COLUMN crawler_documents.file_path IS '다운로드한 파일 경로';
COMMENT ON COLUMN crawler_documents.error_message IS '에러 메시지';
COMMENT ON COLUMN crawler_documents.metadata IS '추가 메타데이터 (JSON)';
