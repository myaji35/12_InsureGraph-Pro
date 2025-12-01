# 다음 구축 계획 - InsureGraph Pro

**현재 진행 상황**: 24/150 스토리 포인트 완료 (16%)
**완료 스프린트**: Sprint 1, 2, 3 (연속 100%)
**날짜**: 2025-12-01

---

## 🎯 현재 상태 요약

### ✅ 완료된 기능 (Epic 1: 5/10 스토리)
1. Story 1.0: Metadata Crawler (5 pts)
2. Story 1.1: PDF Upload (3 pts)
3. Story 1.2: Text Extraction (3 pts)
4. Story 1.3: Legal Parsing (5 pts)
5. Story 1.4: Critical Data Extraction (8 pts)

### 🔧 구현된 핵심 파이프라인
```
PDF → 텍스트 추출 → 법률 구조 파싱 → 중요 데이터 추출
```

### ⚠️ 현재 제약사항
- Neo4j 인증 실패 (설정 필요)
- 그래프 DB 미구축
- LLM API 미통합

---

## 🎯 추천 구축 경로

### 경로 A: MVP 최소 기능 완성 (추천) ⭐

**목표**: 실제 사용 가능한 최소 기능 제품 완성
**예상 소요 시간**: 4-6시간

#### Phase 1: 파이프라인 통합 (2-3시간)
1. **Ingestion Workflow 통합**
   - 현재 분리된 서비스들을 LangGraph workflow로 통합
   - PDF 업로드 → 전체 파이프라인 자동 실행
   - 진행 상태 실시간 업데이트

2. **간단한 저장소 구현**
   - PostgreSQL에 파싱 결과 저장
   - JSON 형태로 구조화된 데이터 보관
   - 검색 가능한 형태로 인덱싱

#### Phase 2: 기본 검색 기능 (2-3시간)
3. **Simple Query Engine**
   - 키워드 기반 검색 (금액, 기간, 조항)
   - PostgreSQL Full-Text Search 활용
   - REST API 엔드포인트 구현

4. **검색 결과 UI**
   - 프론트엔드 검색 페이지
   - 결과 하이라이팅
   - 필터링 (금액 범위, 보험사 등)

**완성 시 가능한 기능**:
- ✅ PDF 업로드
- ✅ 자동 텍스트 추출 및 구조 파싱
- ✅ 중요 데이터 추출 및 저장
- ✅ 키워드 검색
- ✅ 검색 결과 표시

---

### 경로 B: Epic 1 완성 (그래프 중심)

**목표**: Neo4j 그래프 DB 구축 완료
**예상 소요 시간**: 6-8시간
**선행 작업**: Neo4j 설정 필요

#### Sprint 3 (원래 계획) 완료
1. **Story 1.7: Neo4j Graph Construction** (5 pts)
   - Neo4j 인증 문제 해결
   - 그래프 스키마 설계
   - 파싱 결과 → Neo4j 노드/관계 변환
   - Cypher 쿼리 최적화

2. **Story 1.5: Embedding Generation** (3 pts)
   - OpenAI/Azure API 통합
   - 각 조항 임베딩 생성
   - 벡터 저장 (Neo4j 또는 별도 DB)

#### Sprint 4A (분할)
3. **Story 1.8: Pipeline Orchestration** (일부)
   - LangGraph workflow 완성
   - 에러 핸들링
   - 재시도 로직

**완성 시 가능한 기능**:
- ✅ Neo4j 지식 그래프
- ✅ 그래프 기반 쿼리
- ✅ 관계 추론
- ✅ 의미 기반 검색 (임베딩)

---

### 경로 C: Epic 2 시작 (Query Engine)

**목표**: GraphRAG 쿼리 엔진 구현
**예상 소요 시간**: 4-5시간
**선행 조건**: Epic 1 완료 또는 Mock 데이터 사용

#### Sprint 5: Query Foundation
1. **Story 2.1: Query Parser** (5 pts)
   - 자연어 쿼리 파싱
   - 의도 분류 (검색/비교/분석)
   - LLM 기반 쿼리 이해

2. **Story 2.2: Local Search** (3 pts)
   - 단일 약관 내 검색
   - 조항 매칭
   - 관련도 점수

**완성 시 가능한 기능**:
- ✅ 자연어 질문 입력
- ✅ 쿼리 의도 파악
- ✅ 관련 조항 검색
- ✅ 답변 생성

---

## 💡 제 추천: 경로 A (MVP 최소 기능)

### 이유
1. **즉시 사용 가능**: Neo4j 설정 없이 바로 구현 가능
2. **점진적 개선**: 기본 기능부터 시작해서 고도화
3. **사용자 피드백**: 실제 사용하며 개선점 파악
4. **빠른 검증**: 2-3시간 내 작동하는 시스템

### 구현 순서

#### 1단계: Workflow 통합 (1시간)
```python
# backend/app/workflows/simple_ingestion.py
class SimpleIngestionWorkflow:
    async def process_pdf(self, pdf_path):
        # 1. 텍스트 추출
        text_result = pdf_extractor.extract_text(pdf_path)
        
        # 2. 법률 구조 파싱
        parsed = legal_parser.parse_text(text_result.full_text)
        
        # 3. 데이터 추출
        critical_data = data_extractor.extract_all(text_result.full_text)
        
        # 4. PostgreSQL 저장
        await db.save_parsed_document(parsed, critical_data)
        
        return result
```

#### 2단계: 검색 API (1-2시간)
```python
# backend/app/api/v1/endpoints/search.py
@router.get("/search")
async def search_policies(
    query: str,
    amount_min: int = None,
    amount_max: int = None,
):
    # PostgreSQL Full-Text Search
    results = await db.search(query, amount_min, amount_max)
    return results
```

#### 3단계: 검색 UI (1-2시간)
```typescript
// frontend/src/app/search/page.tsx
export default function SearchPage() {
    return (
        <div>
            <SearchInput />
            <FilterPanel />
            <ResultsList />
        </div>
    )
}
```

---

## 📋 상세 구현 계획 (경로 A)

### Task 1: Simple Ingestion Workflow
**파일**: `backend/app/workflows/simple_ingestion.py`
**소요 시간**: 30분

**기능**:
- PDF → Text → Parse → Extract → Save
- 진행 상태 업데이트
- 에러 핸들링

**코드 예시**:
```python
async def run_ingestion(job_id: UUID, pdf_path: str):
    try:
        # Update: Processing
        await update_job_status(job_id, "processing", 0)
        
        # Step 1: Extract text
        text_result = pdf_extractor.extract_text_from_file(pdf_path)
        await update_job_status(job_id, "processing", 25)
        
        # Step 2: Parse structure
        parsed = legal_parser.parse_text(text_result.full_text)
        await update_job_status(job_id, "processing", 50)
        
        # Step 3: Extract data
        critical_data = data_extractor.extract_all(text_result.full_text)
        await update_job_status(job_id, "processing", 75)
        
        # Step 4: Save to DB
        doc_id = await save_document(parsed, critical_data)
        await update_job_status(job_id, "completed", 100, {
            "document_id": doc_id,
            "articles": parsed.total_articles,
        })
        
    except Exception as e:
        await update_job_status(job_id, "failed", 0, error=str(e))
```

---

### Task 2: Document Storage Schema
**파일**: `backend/alembic/versions/003_documents_table.sql`
**소요 시간**: 20분

**스키마**:
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    policy_name VARCHAR(255),
    insurer VARCHAR(100),
    full_text TEXT,
    parsed_structure JSONB,  -- 파싱된 구조
    critical_data JSONB,      -- 추출된 데이터
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Full-text search index
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('korean', full_text)
    ) STORED
);

CREATE INDEX idx_documents_search ON documents USING GIN(search_vector);
CREATE INDEX idx_documents_insurer ON documents(insurer);
```

---

### Task 3: Search API
**파일**: `backend/app/api/v1/endpoints/search.py`
**소요 시간**: 40분

**엔드포인트**:
```python
@router.get("/search/policies")
async def search_policies(
    q: str,                          # 검색어
    insurer: str = None,             # 보험사 필터
    amount_min: int = None,          # 최소 금액
    amount_max: int = None,          # 최대 금액
    limit: int = 20,
    offset: int = 0,
):
    """
    보험 약관 검색
    
    - Full-text search
    - 금액 범위 필터
    - 보험사 필터
    """
    # Build query
    conditions = []
    
    if q:
        conditions.append(f"search_vector @@ plainto_tsquery('korean', '{q}')")
    
    if insurer:
        conditions.append(f"insurer = '{insurer}'")
    
    if amount_min or amount_max:
        # JSONB 쿼리로 금액 필터
        conditions.append(
            f"EXISTS (SELECT 1 FROM jsonb_array_elements(critical_data->'amounts') AS amt "
            f"WHERE (amt->>'normalized_value')::int BETWEEN {amount_min or 0} AND {amount_max or 999999999})"
        )
    
    # Execute
    results = await db.execute(
        f"SELECT * FROM documents WHERE {' AND '.join(conditions)} "
        f"LIMIT {limit} OFFSET {offset}"
    )
    
    return results
```

---

### Task 4: Search Frontend
**파일**: `frontend/src/app/search/page.tsx`
**소요 시간**: 1시간

**UI 구성**:
```typescript
'use client'

export default function SearchPage() {
    const [query, setQuery] = useState("")
    const [results, setResults] = useState([])
    
    const handleSearch = async () => {
        const res = await fetch(
            `/api/v1/search/policies?q=${query}`
        )
        const data = await res.json()
        setResults(data)
    }
    
    return (
        <div className="container">
            {/* Search Bar */}
            <SearchInput 
                value={query}
                onChange={setQuery}
                onSubmit={handleSearch}
            />
            
            {/* Filters */}
            <FilterPanel />
            
            {/* Results */}
            <ResultsList results={results} />
        </div>
    )
}
```

---

## 📅 구현 일정 (경로 A)

### Day 1 (2-3시간)
- ✅ Task 1: Simple Ingestion Workflow
- ✅ Task 2: Document Storage Schema
- ✅ Task 3: Search API (기본)

### Day 2 (2-3시간)
- ✅ Task 4: Search Frontend
- ✅ 통합 테스트
- ✅ 버그 수정

**총 예상 시간**: 4-6시간

---

## 🎯 완성 시 데모 시나리오

1. **PDF 업로드**
   - 사용자가 보험 약관 PDF 업로드
   - 자동으로 파이프라인 실행
   - 진행 상태 실시간 표시

2. **검색 실행**
   - "암보험 보험금 1억원" 검색
   - 관련 조항 목록 표시
   - 금액 하이라이팅

3. **결과 확인**
   - 조항 내용 확인
   - 금액, 기간, 질병 코드 표시
   - 원본 PDF 참조

---

## 💬 다음 단계 선택

어떤 경로로 진행하시겠습니까?

**A. MVP 최소 기능 완성** (추천) ⭐
- 4-6시간 소요
- 즉시 사용 가능한 시스템
- 점진적 개선 가능

**B. Epic 1 완성 (Neo4j)**
- 6-8시간 소요
- Neo4j 설정 필요
- 그래프 DB 활용

**C. Epic 2 시작 (Query Engine)**
- 4-5시간 소요
- LLM 통합 필요
- 자연어 쿼리

**D. 커스텀 계획**
- 원하는 기능 우선순위 지정
- 맞춤형 구현 계획

선택하신 경로를 알려주시면 바로 시작하겠습니다!
