# Deep Knowledge Graph Implementation

## 개요

InsureGraph Pro의 지식 그래프를 기존 3단계 얕은 구조(보험사 → 상품타입 → 문서)에서 GraphRAG 스타일의 깊이 있는 보험 도메인 지식 그래프로 확장한 구현입니다.

**구현 목표**: "지금보다 많이 깊게 학습" - 보험 약관에서 보장항목, 보험금액, 지급조건, 면책사항 등 실제 보험 도메인 지식을 추출하여 그래프화

**구현 일자**: 2025-12-03

---

## 아키텍처

```
문서 처리 파이프라인:
보험 PDF/문서
  → ParallelDocumentProcessor (청크 단위 처리)
  → SmartInsuranceLearner (학습)
  → DeepKnowledgeService (엔티티 추출 오케스트레이션)
  → GraphRAGEntityExtractor (Claude API로 엔티티/관계 추출)
  → PostgreSQL (knowledge_entities, knowledge_relationships 테이블에 저장)
  → worker_graph_updater (주기적으로 PostgreSQL → Neo4j 동기화)
  → Neo4j (동적 라벨과 관계 타입으로 시각화 가능한 그래프 생성)
```

---

## 구현된 컴포넌트

### 1. GraphRAG Entity Extractor
**파일**: `app/services/learning/graphrag_entity_extractor.py`

**역할**: Claude API를 사용하여 보험 약관 텍스트에서 도메인 특화 엔티티와 관계 추출

**추출 가능한 엔티티 타입 (10종)**:
- `coverage_item`: 보장항목 (예: 사망보험금, 상해후유장해, 입원일당)
- `benefit_amount`: 보험금액 (예: 1억원, 5,000만원)
- `payment_condition`: 지급조건 (예: 교통사고로 인한 사망, 암진단 시)
- `exclusion`: 면책사항 (예: 고의적 사고, 전쟁, 폭동)
- `deductible`: 자기부담금 (예: 20%, 10만원)
- `rider`: 특약 (예: 암진단특약, 3대질병특약)
- `eligibility`: 가입조건 (예: 만 15세~65세, 건강체)
- `article`: 약관조항 (예: 제1관 제3조)
- `term`: 보험용어 (예: 피보험자, 보험계약자)
- `period`: 기간 (예: 보험기간 10년, 납입기간 20년)

**추출 가능한 관계 타입 (10종)**:
- `provides`: 보장항목 제공
- `has_amount`: 보험금액 설정
- `requires`: 조건 요구
- `excludes`: 면책
- `has_deductible`: 자기부담금 설정
- `includes_rider`: 특약포함
- `defines`: 정의
- `specified_in`: 명시
- `has_eligibility`: 가입조건
- `applies_to`: 적용대상

**주요 메서드**:
```python
async def extract_entities_and_relationships(
    text: str,
    document_info: Dict,
    chunk_id: Optional[str] = None
) -> Dict
```

**반환 형식**:
```json
{
  "entities": [
    {
      "id": "entity_death_benefit_1",
      "label": "사망보험금",
      "type": "coverage_item",
      "description": "교통사고로 인한 사망 시 지급되는 보험금",
      "source_text": "피보험자가 보험기간 중 교통사고로 사망한 경우...",
      "document_info": {...},
      "chunk_id": "chunk_001"
    }
  ],
  "relationships": [
    {
      "source_id": "entity_death_benefit_1",
      "target_id": "entity_amount_100m",
      "type": "has_amount",
      "description": "사망보험금 지급액",
      "chunk_id": "chunk_001"
    }
  ],
  "entity_type_counts": {"coverage_item": 2, "benefit_amount": 1},
  "relationship_type_counts": {"has_amount": 1, "requires": 1}
}
```

---

### 2. PostgreSQL Knowledge Tables
**파일**: `alembic/versions/006_add_knowledge_graph_tables.sql`

**knowledge_entities 테이블**:
```sql
CREATE TABLE knowledge_entities (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(255) UNIQUE NOT NULL,  -- 고유 ID
    label VARCHAR(500) NOT NULL,              -- 엔티티 이름
    type VARCHAR(100) NOT NULL,               -- 엔티티 타입
    description TEXT,                          -- 설명
    source_text TEXT,                          -- 원본 텍스트
    document_id VARCHAR(255),                  -- 문서 ID
    chunk_id VARCHAR(255),                     -- 청크 ID
    insurer VARCHAR(100),                      -- 보험사
    product_type VARCHAR(100),                 -- 상품 타입
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**knowledge_relationships 테이블**:
```sql
CREATE TABLE knowledge_relationships (
    id SERIAL PRIMARY KEY,
    source_entity_id VARCHAR(255) NOT NULL,
    target_entity_id VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    description TEXT,
    document_id VARCHAR(255),
    chunk_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_entity_id) REFERENCES knowledge_entities(entity_id) ON DELETE CASCADE,
    FOREIGN KEY (target_entity_id) REFERENCES knowledge_entities(entity_id) ON DELETE CASCADE
);
```

**인덱스**:
- 엔티티: type, document_id, insurer, product_type, label
- 관계: type, source_entity_id, target_entity_id, document_id
- 전문 검색: label, description (pg_trgm)

---

### 3. Deep Knowledge Service
**파일**: `app/services/learning/deep_knowledge_service.py`

**역할**: GraphRAGEntityExtractor와 PostgreSQL을 연결하는 오케스트레이션 레이어

**주요 메서드**:
```python
async def process_and_extract(
    chunk_text: str,
    document_id: str,
    chunk_id: str,
    document_info: Dict
) -> Dict
```

**기능**:
1. 청크 텍스트에서 엔티티 추출 (GraphRAGEntityExtractor 사용)
2. PostgreSQL에 저장 (INSERT ... ON CONFLICT DO UPDATE)
3. 통계 업데이트 및 반환

**통계 추적**:
```python
{
    "total_entities": 0,
    "total_relationships": 0,
    "chunks_processed": 0,
    "errors": 0
}
```

---

### 4. ParallelDocumentProcessor Integration
**파일**: `app/services/parallel_document_processor.py` (lines 19, 44, 294-349)

**변경 사항**:
1. DeepKnowledgeService import 추가 (line 19)
2. 초기화 시 DeepKnowledgeService 인스턴스 생성 (line 44)
3. SmartLearner의 chunk_learning_callback 교체 (lines 294-349)

**기존 (GraphBuilder 사용)**:
```python
async def actual_learning_callback(text_chunk: str) -> Dict:
    return await self.graph_builder.learn_from_chunk(...)
```

**변경 후 (DeepKnowledgeService 사용)**:
```python
async def actual_learning_callback(text_chunk: str) -> Dict:
    chunk_hash = hashlib.md5(text_chunk.encode()).hexdigest()[:8]
    chunk_id = f"{document_id[:8]}_{chunk_hash}"

    document_info = {
        "insurer": insurer,
        "product_type": product_type,
        "title": document.title or f"{insurer} {product_type}"
    }

    result = await self.deep_knowledge_service.process_and_extract(
        chunk_text=text_chunk,
        document_id=document_id,
        chunk_id=chunk_id,
        document_info=document_info
    )

    return {
        "entities": result.get("entities", 0),
        "relationships": result.get("relationships", 0),
        "chunk_length": len(text_chunk),
        "nodes_by_type": result.get("nodes_by_type", {}),
        "relationships_by_type": result.get("relationships_by_type", {})
    }
```

---

### 5. worker_graph_updater 업그레이드
**파일**: `worker_graph_updater.py` (lines 52-396)

**주요 변경 사항**:

#### A. PostgreSQL에서 엔티티 조회 (lines 154-177)
```python
entity_query = text("""
    SELECT entity_id, label, type, description, source_text,
           document_id, insurer, product_type
    FROM knowledge_entities
    ORDER BY created_at DESC
""")
result = await db.execute(entity_query)
entities = result.fetchall()

logger.info(f"📊 Found {len(entities)} entities from knowledge_entities table")
```

#### B. 엔티티 노드 생성 (lines 179-204)
```python
for entity in entities:
    entity_node = {
        "id": entity[0],
        "label": entity[1][:30],
        "type": entity[2],
        "color": entity_colors.get(entity[2], "#64748b"),
        "size": 20,
        "metadata": {
            "description": description[:100] if description else None,
            "source_text": source_text[:100] if source_text else None,
            "insurer": ent_insurer,
            "product_type": ent_product_type,
            "document_id": document_id
        }
    }
    nodes.append(entity_node)
```

#### C. Neo4j 동적 라벨 생성 (lines 287-329)
```python
label_mapping = {
    "insurer": "Insurer",
    "product_type": "ProductType",
    "document": "Document",
    "coverage_item": "CoverageItem",
    "benefit_amount": "BenefitAmount",
    "payment_condition": "PaymentCondition",
    "exclusion": "Exclusion",
    "deductible": "Deductible",
    "rider": "Rider",
    "eligibility": "Eligibility",
    "article": "Article",
    "term": "Term",
    "period": "Period"
}

neo4j_label = label_mapping.get(node_type, "Entity")

query = f"""
    CREATE (n:{neo4j_label} {{
        id: $id,
        label: $label,
        type: $type,
        color: $color,
        size: $size,
        metadata: $metadata
    }})
"""
```

#### D. Neo4j 동적 관계 타입 생성 (lines 331-370)
```python
rel_type_mapping = {
    "provides": "PROVIDES",
    "contains": "CONTAINS",
    "has_amount": "HAS_AMOUNT",
    "requires": "REQUIRES",
    "excludes": "EXCLUDES",
    "has_deductible": "HAS_DEDUCTIBLE",
    "includes_rider": "INCLUDES_RIDER",
    "defines": "DEFINES",
    "specified_in": "SPECIFIED_IN",
    "has_eligibility": "HAS_ELIGIBILITY",
    "applies_to": "APPLIES_TO",
    "from_document": "FROM_DOCUMENT"
}

neo4j_rel_type = rel_type_mapping.get(edge_type, "RELATES")

query = f"""
    MATCH (source {{id: $source_id}})
    MATCH (target {{id: $target_id}})
    CREATE (source)-[r:{neo4j_rel_type} {{
        id: $id,
        label: $label,
        type: $type
    }}]->(target)
"""
```

#### E. 향상된 로깅 (lines 384-396)
```python
logger.info(f"✅ Graph updated:")
logger.info(f"  - Total Nodes: {len(nodes)}")
logger.info(f"    - Insurers: {len(insurers)}")
logger.info(f"    - Product Types: {len(product_types)}")
logger.info(f"    - Documents: {len(completed_docs)}")
logger.info(f"    - Entities (GraphRAG): {len(entities)}")
logger.info(f"    - Entity Breakdown:")
for etype, count in sorted(entity_type_counts.items()):
    if etype not in ["insurer", "product_type", "document"]:
        logger.info(f"      * {etype}: {count}")
logger.info(f"  - Total Edges: {len(edges)}")
```

---

## 테스트 및 검증

### 1. 단위 테스트
**파일**: `test_deep_knowledge.py`

**실행 방법**:
```bash
cd /Users/gangseungsig/Documents/02_GitHub/12_InsureGraph\ Pro/backend
source venv/bin/activate
python test_deep_knowledge.py
```

**테스트 데이터**:
```python
test_text = """
제1관 제3조 (보험금의 지급사유)

1. 사망보험금
피보험자가 보험기간 중 교통사고로 사망한 경우 보험가입금액의 100%인 1억원을 지급합니다.

2. 후유장해보험금
피보험자가 보험기간 중 교통사고로 장해지급률 3% 이상의 후유장해를 입은 경우
보험가입금액에 해당 장해지급률을 곱한 금액을 지급합니다.

3. 자기부담금
상해 치료비의 경우 20%의 자기부담금이 적용됩니다.

제2관 제5조 (면책사항)
다음의 사유로 인한 손해는 보상하지 않습니다.
1. 피보험자의 고의적 사고
2. 전쟁, 혁명, 내란, 폭동
3. 핵연료 물질에 의한 사고
"""
```

**예상 출력**:
```
================================================================================
Deep Knowledge Service 테스트 시작
================================================================================

📝 테스트 텍스트 길이: XXX 자
📄 문서 정보: {'insurer': '테스트보험', 'product_type': '자동차보험', ...}

🔍 엔티티 추출 중...

✅ 추출 완료!
   - 엔티티: 7개
   - 관계: 5개

📊 엔티티 타입별 분포:
   - coverage_item: 2개
   - benefit_amount: 1개
   - payment_condition: 1개
   - deductible: 1개
   - exclusion: 2개

🔗 관계 타입별 분포:
   - has_amount: 1개
   - requires: 1개
   - has_deductible: 1개
   - excludes: 2개

✅ PostgreSQL에 저장된 엔티티: 7개

📋 엔티티 샘플 (최대 5개):
   - [coverage_item] 사망보험금
     설명: 교통사고로 인한 사망 시 지급되는 보험금
   - [benefit_amount] 1억원
     설명: 사망보험금 지급액
   ...
```

### 2. 테스트 데이터 삽입
**수동으로 PostgreSQL에 테스트 데이터 삽입**:

```bash
psql -U gangseungsig -d insuregraph
```

```sql
-- 엔티티 삽입
INSERT INTO knowledge_entities (entity_id, label, type, description, source_text, document_id, chunk_id, insurer, product_type, metadata) VALUES
('entity_death_benefit_1', '사망보험금', 'coverage_item', '교통사고로 인한 사망 시 지급되는 보험금', '피보험자가 보험기간 중 교통사고로 사망한 경우 보험가입금액의 100%인 1억원을 지급합니다.', 'test_doc_001', 'chunk_001', '테스트보험', '자동차보험', '{}'),
('entity_amount_100m', '1억원', 'benefit_amount', '사망보험금 지급액', '보험가입금액의 100%인 1억원', 'test_doc_001', 'chunk_001', '테스트보험', '자동차보험', '{}'),
('entity_condition_traffic', '교통사고로 사망', 'payment_condition', '사망보험금 지급 조건', '교통사고로 사망한 경우', 'test_doc_001', 'chunk_001', '테스트보험', '자동차보험', '{}'),
('entity_disability', '후유장해보험금', 'coverage_item', '장해지급률 3% 이상의 후유장해 발생 시 지급', '장해지급률 3% 이상의 후유장해를 입은 경우', 'test_doc_001', 'chunk_001', '테스트보험', '자동차보험', '{}'),
('entity_deduct_20', '20% 자기부담금', 'deductible', '상해 치료비 자기부담금', '상해 치료비의 경우 20%의 자기부담금이 적용됩니다', 'test_doc_001', 'chunk_002', '테스트보험', '자동차보험', '{}'),
('entity_exclusion_war', '전쟁/폭동', 'exclusion', '전쟁, 혁명, 내란, 폭동으로 인한 손해', '전쟁, 혁명, 내란, 폭동', 'test_doc_001', 'chunk_002', '테스트보험', '자동차보험', '{}'),
('entity_exclusion_intent', '고의적사고', 'exclusion', '피보험자의 고의적 사고', '피보험자의 고의적 사고', 'test_doc_001', 'chunk_002', '테스트보험', '자동차보험', '{}');

-- 관계 삽입
INSERT INTO knowledge_relationships (source_entity_id, target_entity_id, type, description, document_id, chunk_id, metadata) VALUES
('entity_death_benefit_1', 'entity_amount_100m', 'has_amount', '사망보험금 지급액', 'test_doc_001', 'chunk_001', '{}'),
('entity_death_benefit_1', 'entity_condition_traffic', 'requires', '사망보험금 지급 조건', 'test_doc_001', 'chunk_001', '{}'),
('entity_disability', 'entity_deduct_20', 'has_deductible', '후유장해보험금 자기부담금', 'test_doc_001', 'chunk_001', '{}'),
('entity_death_benefit_1', 'entity_exclusion_war', 'excludes', '전쟁/폭동은 면책', 'test_doc_001', 'chunk_002', '{}'),
('entity_death_benefit_1', 'entity_exclusion_intent', 'excludes', '고의적 사고는 면책', 'test_doc_001', 'chunk_002', '{}');
```

**검증**:
```sql
-- 엔티티 수 확인
SELECT COUNT(*) FROM knowledge_entities;
-- Expected: 7

-- 관계 수 확인
SELECT COUNT(*) FROM knowledge_relationships;
-- Expected: 5

-- 엔티티 타입별 분포
SELECT type, COUNT(*) as count
FROM knowledge_entities
GROUP BY type
ORDER BY count DESC;

-- 관계 타입별 분포
SELECT type, COUNT(*) as count
FROM knowledge_relationships
GROUP BY type
ORDER BY count DESC;
```

### 3. worker_graph_updater 실행 및 검증

**Worker 실행**:
```bash
cd /Users/gangseungsig/Documents/02_GitHub/12_InsureGraph\ Pro/backend
source venv/bin/activate
python worker_graph_updater.py 10
```

**예상 로그 출력**:
```
================================================================================
🔄 Graph Updater Worker Started
  - Check Interval: 10s
  - Output Path: /Users/gangseungsig/.../sample_graph.json
================================================================================

📊 Found 7 entities from knowledge_entities table
🔗 Found 5 relationships from knowledge_relationships table

✅ Neo4j updated successfully

✅ Graph updated:
  - Total Nodes: 85
    - Insurers: 2
    - Product Types: 5
    - Documents: 71
    - Entities (GraphRAG): 7
    - Entity Breakdown:
      * benefit_amount: 1
      * coverage_item: 2
      * deductible: 1
      * exclusion: 2
      * payment_condition: 1
  - Total Edges: 88
  - Last update: 2025-12-03 15:00:15

[2025-12-03 15:00:16] Completed documents: 71 (previous: 71)
⏸️  No new documents, skipping update
```

### 4. Neo4j 검증

**Cypher 쿼리로 검증**:

```bash
cypher-shell -u neo4j -p 'test1234' -a bolt://localhost:7687
```

```cypher
-- 전체 노드 라벨 확인
MATCH (n)
RETURN labels(n)[0] as label, count(*) as count
ORDER BY count DESC;

-- Expected output:
-- Document: 71
-- CoverageItem: 2
-- ProductType: 5
-- Insurer: 2
-- Exclusion: 2
-- BenefitAmount: 1
-- PaymentCondition: 1
-- Deductible: 1

-- 전체 관계 타입 확인
MATCH ()-[r]->()
RETURN DISTINCT type(r) as relationship_type, count(*) as count
ORDER BY count DESC;

-- Expected output:
-- CONTAINS: ~76
-- PROVIDES: ~5
-- EXCLUDES: 2
-- HAS_AMOUNT: 1
-- REQUIRES: 1
-- HAS_DEDUCTIBLE: 1
-- FROM_DOCUMENT: ~7

-- 엔티티 노드 상세 확인
MATCH (c:CoverageItem)
RETURN c.id, c.label, c.type;

-- Expected output:
-- entity_death_benefit_1, 사망보험금, coverage_item
-- entity_disability, 후유장해보험금, coverage_item

-- 관계 그래프 확인 (사망보험금 중심)
MATCH (c:CoverageItem {label: '사망보험금'})-[r]-(m)
RETURN c.label, type(r), labels(m)[0], m.label;

-- Expected output:
-- 사망보험금, EXCLUDES, Exclusion, 전쟁/폭동
-- 사망보험금, EXCLUDES, Exclusion, 고의적사고
-- 사망보험금, HAS_AMOUNT, BenefitAmount, 1억원
-- 사망보험금, REQUIRES, PaymentCondition, 교통사고로 사망
-- 사망보험금, FROM_DOCUMENT, Document, ...
```

---

## 현재 상태

### 구현 완료 사항
✅ GraphRAG Entity Extractor 구현 (276 lines)
✅ PostgreSQL knowledge tables 생성 (70 lines SQL)
✅ DeepKnowledgeService 구현 (201 lines)
✅ ParallelDocumentProcessor 통합 (57 lines modified)
✅ worker_graph_updater 업그레이드 (145 lines modified)
✅ 테스트 데이터로 검증 완료

### 그래프 현황

**Before (구현 전)**:
- 78 nodes (모두 "Node" 라벨)
- 3 types: insurer (2), product_type (5), document (71)
- 2 relationship types
- 도메인 지식 없음

**After (구현 후)**:
- **85 nodes total**
- **8 distinct labels**: Insurer, ProductType, Document, CoverageItem, Exclusion, BenefitAmount, PaymentCondition, Deductible
- **6 relationship types**: CONTAINS, PROVIDES, EXCLUDES, HAS_AMOUNT, REQUIRES, HAS_DEDUCTIBLE, FROM_DOCUMENT
- **실제 보험 도메인 지식 포함**:
  - 사망보험금 -[HAS_AMOUNT]→ 1억원
  - 사망보험금 -[REQUIRES]→ 교통사고로 사망
  - 사망보험금 -[EXCLUDES]→ 전쟁/폭동
  - 사망보험금 -[EXCLUDES]→ 고의적사고

### 알려진 제약사항

1. **ANTHROPIC_API_KEY 미설정**
   - 현재: `.env` 파일에 placeholder 값 ("your-anthropic-api-key")
   - 영향: 실제 엔티티 추출 불가
   - 해결: 실제 Claude API 키 설정 필요

2. **테스트 데이터만 존재**
   - 현재: 7개 엔티티, 5개 관계 (수동 삽입)
   - API 키 설정 후 실제 보험 문서 처리 시 자동 추출 가능

3. **Backend 연결 문제** (별도 이슈)
   - Frontend에서 `ERR_NETWORK` 발생
   - GraphRAG 구현과는 무관

---

## Production 배포 가이드

### 1. 환경 설정

```bash
# .env 파일에 실제 API 키 설정
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx  # 실제 키로 교체
```

### 2. Database Migration

```bash
cd backend
source venv/bin/activate

# PostgreSQL에 knowledge tables 생성
psql -U gangseungsig -d insuregraph -f alembic/versions/006_add_knowledge_graph_tables.sql

# pg_trgm extension 활성화 (전문 검색용)
psql -U gangseungsig -d insuregraph -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
```

### 3. Worker 시작

```bash
# Graph Updater Worker (10초 간격)
nohup python worker_graph_updater.py 10 > graph_updater.log 2>&1 &

# Auto Learner Worker
nohup python worker_auto_learner.py 10 50 30 > worker.log 2>&1 &
```

### 4. 모니터링

**PostgreSQL 엔티티 성장 모니터링**:
```sql
-- 시간별 엔티티 증가 추세
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as entities_created
FROM knowledge_entities
GROUP BY hour
ORDER BY hour DESC
LIMIT 24;

-- 엔티티 타입별 분포
SELECT type, COUNT(*) as count
FROM knowledge_entities
GROUP BY type
ORDER BY count DESC;

-- 문서별 엔티티 수
SELECT
    document_id,
    insurer,
    product_type,
    COUNT(*) as entity_count
FROM knowledge_entities
GROUP BY document_id, insurer, product_type
ORDER BY entity_count DESC
LIMIT 10;
```

**Neo4j 그래프 성장 모니터링**:
```cypher
// 라벨별 노드 수
MATCH (n)
RETURN labels(n)[0] as label, count(*) as count
ORDER BY count DESC;

// 관계 타입별 수
MATCH ()-[r]->()
RETURN type(r) as rel_type, count(*) as count
ORDER BY count DESC;

// 가장 많은 연결을 가진 노드 (허브)
MATCH (n)
RETURN labels(n)[0] as label, n.label,
       size((n)--()) as degree
ORDER BY degree DESC
LIMIT 10;
```

### 5. 성능 최적화

**대량 문서 처리 시**:
```python
# parallel_document_processor.py에서 배치 크기 조정
max_workers = 10  # CPU 코어에 맞게 조정
chunk_size = 2000  # 청크 크기 조정
```

**PostgreSQL 인덱스 튜닝**:
```sql
-- 느린 쿼리 확인
SELECT * FROM pg_stat_statements
WHERE query LIKE '%knowledge%'
ORDER BY total_time DESC;

-- 필요시 추가 인덱스 생성
CREATE INDEX idx_entities_created_at ON knowledge_entities(created_at);
CREATE INDEX idx_relationships_created_at ON knowledge_relationships(created_at);
```

---

## 향후 개선 사항

### 1. 엔티티 추출 품질 향상
- [ ] 프롬프트 엔지니어링 개선
- [ ] Few-shot learning 예제 추가
- [ ] 도메인 특화 용어 사전 구축

### 2. 관계 추론 강화
- [ ] 암묵적 관계 추론
- [ ] 다단계 관계 추출
- [ ] 시간적 관계 모델링

### 3. 그래프 분석 기능
- [ ] PageRank로 중요 엔티티 식별
- [ ] Community Detection으로 보험 상품군 클러스터링
- [ ] Shortest Path로 보장 항목 간 연관성 분석

### 4. Frontend 통합
- [ ] Frontend query 수정 (새 Neo4j 라벨 대응)
- [ ] 엔티티 타입별 필터링 UI
- [ ] 관계 중심 시각화
- [ ] 엔티티 상세 정보 표시

### 5. 비용 최적화
- [ ] 청크당 API 호출 비용 모니터링
- [ ] 캐싱 전략 (중복 청크 처리 방지)
- [ ] Batch processing (여러 청크 한번에 처리)

---

## 참고 자료

### 관련 파일
- `app/services/learning/graphrag_entity_extractor.py`
- `app/services/learning/deep_knowledge_service.py`
- `app/services/parallel_document_processor.py`
- `worker_graph_updater.py`
- `alembic/versions/006_add_knowledge_graph_tables.sql`
- `test_deep_knowledge.py`

### 의존성
- anthropic>=0.18.0
- neo4j>=5.0.0
- sqlalchemy>=2.0.0
- asyncpg>=0.29.0

### 외부 링크
- [GraphRAG 논문](https://arxiv.org/abs/2404.16130)
- [Claude API 문서](https://docs.anthropic.com/claude/reference)
- [Neo4j 그래프 데이터 모델링](https://neo4j.com/docs/getting-started/data-modeling/)

---

## 문의 및 지원

구현 관련 문의사항이나 개선 제안이 있으시면 이슈를 생성해주세요.

**작성자**: Claude AI Assistant
**일자**: 2025-12-03
**버전**: 1.0.0
