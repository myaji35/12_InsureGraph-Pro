-- 지식 그래프 테이블 추가
-- GraphRAG 스타일 엔티티 및 관계 저장

-- 엔티티 테이블
CREATE TABLE IF NOT EXISTS knowledge_entities (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(255) UNIQUE NOT NULL,  -- 고유 엔티티 ID (entity_coverage_item_1 등)
    label VARCHAR(500) NOT NULL,             -- 엔티티 이름 (예: "사망보험금", "교통사고")
    type VARCHAR(100) NOT NULL,              -- 엔티티 타입 (coverage_item, benefit_amount 등)
    description TEXT,                         -- 엔티티 설명
    source_text TEXT,                         -- 원본 텍스트 발췌

    -- 문서 연결 정보
    document_id VARCHAR(255),                 -- crawler_documents.id
    chunk_id VARCHAR(255),                    -- 청크 ID

    -- 문서 메타데이터
    insurer VARCHAR(100),                     -- 보험사
    product_type VARCHAR(100),                -- 상품 타입

    -- 메타데이터
    metadata JSONB DEFAULT '{}',              -- 추가 메타데이터

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 관계 테이블
CREATE TABLE IF NOT EXISTS knowledge_relationships (
    id SERIAL PRIMARY KEY,
    relationship_id VARCHAR(255),             -- 고유 관계 ID (선택)
    source_entity_id VARCHAR(255) NOT NULL,   -- 소스 엔티티 ID
    target_entity_id VARCHAR(255) NOT NULL,   -- 타겟 엔티티 ID
    type VARCHAR(100) NOT NULL,               -- 관계 타입 (provides, requires 등)
    description TEXT,                          -- 관계 설명

    -- 문서 연결 정보
    document_id VARCHAR(255),                  -- crawler_documents.id
    chunk_id VARCHAR(255),                     -- 청크 ID

    -- 메타데이터
    metadata JSONB DEFAULT '{}',               -- 추가 메타데이터

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 외래 키 (엔티티 테이블 참조)
    FOREIGN KEY (source_entity_id) REFERENCES knowledge_entities(entity_id) ON DELETE CASCADE,
    FOREIGN KEY (target_entity_id) REFERENCES knowledge_entities(entity_id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_entities_type ON knowledge_entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_document_id ON knowledge_entities(document_id);
CREATE INDEX IF NOT EXISTS idx_entities_insurer ON knowledge_entities(insurer);
CREATE INDEX IF NOT EXISTS idx_entities_product_type ON knowledge_entities(product_type);
CREATE INDEX IF NOT EXISTS idx_entities_label ON knowledge_entities(label);

CREATE INDEX IF NOT EXISTS idx_relationships_type ON knowledge_relationships(type);
CREATE INDEX IF NOT EXISTS idx_relationships_source ON knowledge_relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON knowledge_relationships(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_document_id ON knowledge_relationships(document_id);

-- 전문 검색 인덱스
CREATE INDEX IF NOT EXISTS idx_entities_label_trgm ON knowledge_entities USING gin(label gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_entities_description_trgm ON knowledge_entities USING gin(description gin_trgm_ops);

COMMENT ON TABLE knowledge_entities IS 'GraphRAG 스타일 지식 그래프 엔티티 (보장항목, 보험금, 조건 등)';
COMMENT ON TABLE knowledge_relationships IS 'GraphRAG 스타일 엔티티 간 관계';
