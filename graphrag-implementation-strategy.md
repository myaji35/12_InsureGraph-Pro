# GraphRAG 기술 구현 전략

**프로젝트**: InsureGraph Pro
**문서 타입**: Technical Strategy (Brainstorming Output)
**작성일**: 2025-11-25
**작성자**: Business Analyst (Mary)
**버전**: 1.0

---

## 📋 Executive Summary

이 문서는 InsureGraph Pro의 핵심 기술인 GraphRAG(Graph Retrieval-Augmented Generation) 구현 전략을 정의합니다. 보험 약관의 복잡한 구조를 정확하게 파싱하고, Multi-hop Reasoning을 통해 경쟁력 있는 분석 기능을 제공하며, 할루시네이션을 방지하여 치명적 리스크를 완화하는 것을 목표로 합니다.

**핵심 전략**: **하이브리드 접근법 (Rule-based + LLM + 검증)**
- Critical 데이터(금액/날짜)는 Rule-based로 100% 정확도 확보
- 복잡한 조건절은 LLM으로 유연하게 처리
- 4단계 방어선으로 할루시네이션 방지

---

## 🎯 기술적 도전 과제

PRD 분석을 통해 식별한 핵심 과제:

1. **복잡한 약관 문서 파싱**: 수백 페이지의 법률 문서, 표, 플로우차트, 계층 구조 처리
2. **정확한 관계 추출**: "갑상선암 → 면책기간 → 90일" 같은 복합 관계 식별
3. **Multi-hop Reasoning**: "A상품과 B상품 중복 보장?" 같은 복합 추론 수행
4. **할루시네이션 방지**: 치명적 리스크 (오안내 시 배상 책임) 완화
5. **하이브리드 검색**: Vector Search (Local) + Graph Traversal (Global) 최적화

---

## 🏗️ 아키텍처 개요

### 4계층 파이프라인

```
[PDF 약관]
    ↓
[계층 1] 문서 구조 파싱 (Rule-based)
    ↓
[계층 2] 핵심 데이터 추출 (Rule-based)
    ↓
[계층 3] 관계 추출 (LLM + Prompt Engineering)
    ↓
[계층 4] 온톨로지 표준화 (Entity Linking)
    ↓
[Neo4j Knowledge Graph]
    ↓
[하이브리드 검색] Vector + Graph Traversal
    ↓
[4단계 방어선] 할루시네이션 검증
    ↓
[최종 답변 + 근거]
```

---

## 💡 구현 전략: 영역별 상세

### 영역 1: 약관 파싱 파이프라인 (Ingestion)

#### 계층 1: 문서 구조 파싱 (Rule-based)

**기술**: 정규식 + 레이아웃 분석

```python
# 구현 예시
def parse_legal_structure(ocr_text):
    """
    법률 문서의 계층 구조를 파싱
    - "제N조", "①항", "다만", "단서" 등 법률 키워드 인식
    - 들여쓰기/번호 체계로 계층 구조 파악
    - 표/플로우차트 영역 분리
    """
    import re

    patterns = {
        'article': r'제(\d+)조',
        'paragraph': r'[①②③④⑤⑥⑦⑧⑨⑩]',
        'subclause': r'(가|나|다|라|마)',
        'exception': r'(다만|단서|제외)'
    }

    # 계층 구조 트리 생성
    # ...
```

**출력**: 계층적 청크(Chunk) 리스트

---

#### 계층 2: 핵심 데이터 추출 (Rule-based)

**목적**: 100% 정확도가 필요한 수치 데이터 추출

```python
def extract_critical_data(chunk):
    """
    금액, 기간, KCD 코드 등 Critical 데이터 추출
    """
    data = {
        'amounts': extract_amounts(chunk),      # "1억원" → 100000000
        'periods': extract_periods(chunk),      # "90일" → 90
        'kcd_codes': extract_kcd_codes(chunk)   # "C77" → Disease DB 매칭
    }
    return data

def extract_amounts(text):
    """금액 정규화"""
    # "1억원", "100만원" → 숫자 변환
    patterns = {
        '억': 100000000,
        '만': 10000,
        '천': 1000
    }
    # ...

def extract_periods(text):
    """기간 정규화 (일 단위)"""
    # "90일", "3개월" → 일(day) 단위로 통일
    # ...
```

**이점**: LLM의 할루시네이션 리스크 제거

---

#### 계층 3: 관계 추출 (LLM + Prompt Engineering)

**목적**: 복잡한 조건절과 관계를 LLM으로 해석

**프롬프트 템플릿**:

```python
RELATION_EXTRACTION_PROMPT = """
당신은 보험 약관 전문가입니다. 다음 약관 조항에서 주체-행위-객체-조건을 추출하세요.

약관 조항:
{clause_text}

추출 지침:
- 주체: 어떤 담보/상품?
- 행위: 보장하다/면책하다/감액하다/요구하다
- 객체: 어떤 질병/상황?
- 조건: 면책기간/감액비율/기타 조건은?

출력 형식 (JSON):
{
  "subject": "암진단특약",
  "action": "면책",
  "object": "갑상선암(C77)",
  "conditions": [
    {"type": "waiting_period", "days": 90}
  ],
  "confidence": 0.95
}

답변:
"""

def extract_relations_with_llm(chunk, critical_data):
    """
    LLM으로 관계 추출
    - critical_data는 계층 2에서 추출한 검증된 수치
    """
    prompt = RELATION_EXTRACTION_PROMPT.format(
        clause_text=chunk.text
    )

    llm_output = llm.generate(prompt)
    relations = parse_json(llm_output)

    # 검증: LLM이 추출한 숫자와 Rule-based 결과 비교
    if relations['conditions']:
        validate_against_critical_data(relations, critical_data)

    return relations
```

**검증 메커니즘**:
- LLM이 추출한 금액/기간을 계층 2의 Rule-based 결과와 대조
- 불일치 시 Rule-based 값 우선 (신뢰성 확보)

---

#### 계층 4: 온톨로지 표준화 (Entity Linking)

**목적**: 동의어/유사어를 표준 용어로 통일

```python
ONTOLOGY_MAPPING = {
    '악성신생물': 'Cancer',
    '암': 'Cancer',
    'Malignant Neoplasm': 'Cancer',

    '뇌출혈': 'CerebralHemorrhage',
    '뇌혈관질환': 'CerebrovascularDisease',
    # ...
}

def standardize_entities(relations):
    """
    Entity를 표준 용어 및 KCD 코드와 매핑
    """
    for relation in relations:
        # Disease Entity 표준화
        if relation['object'] in ONTOLOGY_MAPPING:
            relation['object_standard'] = ONTOLOGY_MAPPING[relation['object']]

        # KCD 코드 연결
        relation['kcd_code'] = kcd_database.match(relation['object'])

    return relations
```

**이점**: 그래프 쿼리 시 검색 정확도 향상

---

### 영역 2: 그래프 스키마 설계 (핵심 경쟁력)

#### 확장된 Neo4j 스키마

PRD의 기본 스키마를 확장하여 **Multi-hop Reasoning 최적화**:

```cypher
// ============================================
// 노드 정의
// ============================================

// 기본 노드 (PRD 기반)
(:Product {
  name: STRING,
  insurer: STRING,
  launch_date: DATE,
  version: STRING,
  status: STRING  // 'active', 'deprecated'
})

(:Coverage {
  name: STRING,
  code: STRING,
  amount: INTEGER,
  type: STRING,  // 'life', 'ci', 'disease'
  payment_type: STRING  // 'lump_sum', 'proportional'
})

(:Disease {
  kcd_code: STRING,
  name: STRING,
  severity_level: STRING,  // 'minor', 'general', 'critical'
  category: STRING
})

(:Condition {
  type: STRING,  // 'waiting_period', 'reduction_period', 'age_limit'
  days: INTEGER,
  percentage: FLOAT,
  trigger_event: STRING
})

// 추가 노드 (경쟁력 강화)
(:Clause {
  article_num: STRING,   // "제10조"
  paragraph: STRING,     // "①항"
  raw_text: STRING,      // 원문
  summary: STRING,       // LLM 생성 요약
  page_num: INTEGER
})

(:Exclusion {
  type: STRING,          // 'disease', 'activity', 'period'
  description: STRING,
  priority: INTEGER      // 충돌 시 우선순위
})

(:PaymentRule {
  condition_type: STRING,
  amount_formula: STRING,  // "MIN(actual_cost, coverage_amount)"
  proportional_ratio: FLOAT
})

// ============================================
// 엣지 정의
// ============================================

// 기본 관계
(Product)-[:HAS_COVERAGE]->(Coverage)
(Coverage)-[:COVERS {confidence: FLOAT}]->(Disease)
(Coverage)-[:EXCLUDES {priority: INTEGER}]->(Disease)
(Coverage)-[:REQUIRES {order: INTEGER}]->(Condition)

// 핵심 추가 관계 (경쟁 우위)
(Coverage)-[:CONFLICTS_WITH {
  conflict_type: STRING,     // 'duplicate', 'proportional'
  overlap_pct: FLOAT
}]->(Coverage)

(Condition)-[:REFERENCES]->(Clause)  // 근거 추적용!
(Coverage)-[:DEFINED_IN]->(Clause)
(Exclusion)-[:BASED_ON]->(Clause)

// 메타 관계 (추론 최적화)
(Coverage)-[:OVERLAPS_WITH {overlap_pct: FLOAT}]->(Coverage)
(Product)-[:COMPETES_WITH]->(Product)
(Product)-[:REPLACES {replaced_date: DATE}]->(Product)  // 약관 개정 추적
```

#### 스키마 설계 철학

**1. `:REFERENCES` 엣지의 중요성**
- 모든 답변은 원문 조항(Clause)으로 추적 가능
- "답변 근거 제시" 요구사항 충족
- 할루시네이션 방지의 핵심

**2. `:CONFLICTS_WITH` 엣지**
- "A상품과 B상품 중복 보장?" 쿼리를 단일 Cypher로 해결
- 중복가입 시뮬레이션 가능

**3. Confidence/Priority 속성**
- 애매한 경우 확률적 답변 가능
- "이 질문은 해석이 애매합니다" 응답 자동화

---

### 영역 3: 하이브리드 검색 전략

#### 시나리오별 최적화 전략

**케이스 A: 단순 사실 확인**

**질문 예시**: "갑상선암 보장돼요?"

**검색 전략**:
```cypher
// Step 1: Vector Search로 관련 Coverage 찾기
// (Neo4j Vector Index 사용)
CALL db.index.vector.queryNodes('coverage_embeddings', 5, $query_embedding)
YIELD node AS coverage, score

// Step 2: Graph Hop 1단계 - Coverage → Disease 연결 확인
MATCH (coverage)-[r:COVERS|EXCLUDES]->(d:Disease)
WHERE d.kcd_code STARTS WITH 'C77'  // 갑상선암

// Step 3: Graph Hop 2단계 - Condition 확인
OPTIONAL MATCH (coverage)-[:REQUIRES]->(cond:Condition)

RETURN coverage, r.type AS relation, d.name, cond
```

**예상 성능**: ~300ms

---

**케이스 B: 복합 추론**

**질문 예시**: "2011년 가입 암보험, 갑상선 림프절 전이 청구 가능?"

**검색 전략**:
```cypher
// Step 1: Vector Search - 관련 키워드
// "2011년", "갑상선", "림프절 전이"

// Step 2: Multi-hop Graph Traversal
MATCH path = (p:Product)-[:HAS_COVERAGE]->(c:Coverage)
              -[:COVERS]->(d:Disease)
              -[:HAS_SUBTYPE]->(subtype:Disease)
WHERE p.launch_date.year <= 2011
  AND d.kcd_code STARTS WITH 'C77'
  AND subtype.name CONTAINS '림프절'

// Step 3: 약관 개정 이력 확인 (시간 그래프)
OPTIONAL MATCH (p)-[:REPLACES*]->(old_p:Product)
OPTIONAL MATCH (old_p)-[:HAS_COVERAGE]->(old_c:Coverage)
              -[:DEFINED_IN]->(clause:Clause)
WHERE clause.raw_text CONTAINS '소액암'

RETURN path, clause.raw_text AS evidence
```

**LLM 추론 레이어**:
```python
def complex_reasoning(query, graph_paths):
    """
    그래프 경로를 LLM에게 전달하여 최종 판단
    """
    prompt = f"""
    질문: {query}

    그래프 분석 결과:
    - 상품: {graph_paths[0].product.name} (2011년 이전 가입)
    - 담보: {graph_paths[0].coverage.name}
    - 약관 조항: "{graph_paths[0].clause.raw_text}"

    판단:
    1. 갑상선 림프절 전이는 일반암인가 소액암인가?
    2. 해당 약관에서 어떻게 분류되는가?
    3. 청구 가능 여부는?

    근거와 함께 답변하세요.
    """

    answer = llm.generate(prompt)
    return answer
```

**예상 성능**: ~1.5초 (복잡하지만 고부가가치)

---

**케이스 C: 충돌 탐지**

**질문 예시**: "A상품과 B상품 중복 보장돼요?"

**검색 전략**:
```cypher
// 사전 계산된 CONFLICTS_WITH 엣지 활용
MATCH (p1:Product {name: 'A상품'})-[:HAS_COVERAGE]->(c1:Coverage)
MATCH (p2:Product {name: 'B상품'})-[:HAS_COVERAGE]->(c2:Coverage)
MATCH (c1)-[:COVERS]->(d:Disease)<-[:COVERS]-(c2)

// 비례보상 규칙 확인
OPTIONAL MATCH (c1)-[:HAS_PAYMENT_RULE]->(pr1:PaymentRule)
OPTIONAL MATCH (c2)-[:HAS_PAYMENT_RULE]->(pr2:PaymentRule)
WHERE pr1.condition_type = 'proportional'
   OR pr2.condition_type = 'proportional'

RETURN d.name AS overlapping_disease,
       c1.name AS coverage_a,
       c2.name AS coverage_b,
       pr1.proportional_ratio AS ratio_a,
       pr2.proportional_ratio AS ratio_b
```

**답변 생성**:
```
✅ 중복 보장 발견: 갑상선암(C77)

A상품 (암진단특약): 1억원 (비례보상 50%)
B상품 (CI보험): 5천만원 (비례보상 50%)

→ 실제 지급액: (1억 × 50%) + (5천만 × 50%) = 7,500만원

📄 근거: A상품 약관 제12조 ③항, B상품 약관 제8조 ②항
```

**예상 성능**: ~500ms (그래프 쿼리 최적화)

---

### 영역 4: 할루시네이션 방지 메커니즘 (치명적!)

#### 4단계 방어선

**방어선 1: 출처 강제 첨부**

```python
def generate_answer(query, graph_result):
    """
    모든 답변에 원문 조항 참조 강제
    """
    answer = llm.generate(query, context=graph_result)

    # 검증: 원문 조항 참조가 있는지 확인
    if not has_clause_reference(graph_result):
        return {
            'status': 'error',
            'message': '답변 생성 실패: 근거가 되는 약관 조항을 찾을 수 없습니다.'
        }

    # 원문 링크 첨부
    sources = format_sources(graph_result.source_clauses)

    return {
        'status': 'success',
        'answer': answer,
        'sources': sources,
        'confidence': graph_result.confidence
    }

def format_sources(clauses):
    """
    근거 조항 포맷팅
    """
    sources = []
    for clause in clauses:
        sources.append({
            'text': f"📄 {clause.article_num} {clause.paragraph}",
            'page': clause.page_num,
            'excerpt': clause.raw_text[:200] + '...'
        })
    return sources
```

---

**방어선 2: Confidence Threshold**

```python
CONFIDENCE_THRESHOLDS = {
    'high': 0.90,      # 자신 있게 답변
    'medium': 0.75,    # 주의 문구 첨부
    'low': 0.60,       # 전문가 확인 권장
    'reject': 0.60     # 답변 거부
}

def check_confidence(graph_result):
    """
    신뢰도 기반 답변 필터링
    """
    if graph_result.confidence >= CONFIDENCE_THRESHOLDS['high']:
        return 'proceed'

    elif graph_result.confidence >= CONFIDENCE_THRESHOLDS['medium']:
        return 'warning', '⚠️ 이 답변은 약관 해석이 복잡합니다. 보험사에 확인하시기를 권장합니다.'

    elif graph_result.confidence >= CONFIDENCE_THRESHOLDS['low']:
        return 'expert_review', '이 질문은 전문가 검토가 필요합니다.'

    else:
        return 'reject', '죄송합니다. 이 질문은 현재 시스템으로 정확히 답변하기 어렵습니다. 보험사에 직접 문의해주세요.'
```

---

**방어선 3: Human-in-the-loop (Phase 1 MVP)**

```python
class ExpertReviewQueue:
    """
    애매한 답변을 전문가 검토 대기열에 추가
    """
    def __init__(self):
        self.queue = []

    def add_to_queue(self, query, graph_result, llm_answer):
        """
        전문가 검토 요청
        """
        review_item = {
            'id': generate_id(),
            'timestamp': datetime.now(),
            'query': query,
            'graph_paths': graph_result.paths,
            'llm_answer': llm_answer,
            'confidence': graph_result.confidence,
            'status': 'pending',
            'reviewer': None,
            'review_result': None
        }

        self.queue.append(review_item)

        # GA 지점장에게 알림
        notify_reviewer(review_item)

    def approve(self, item_id, reviewer_id):
        """
        승인 시 학습 데이터로 활용
        """
        item = self.get_item(item_id)
        item['status'] = 'approved'
        item['reviewer'] = reviewer_id

        # Positive sample로 학습 데이터 추가
        add_to_training_data(item, label='correct')

    def reject(self, item_id, reviewer_id, correct_answer):
        """
        거부 시 올바른 답변으로 재학습
        """
        item = self.get_item(item_id)
        item['status'] = 'rejected'
        item['reviewer'] = reviewer_id
        item['correct_answer'] = correct_answer

        # Negative sample + 정답으로 학습
        add_to_training_data(item, label='incorrect', correct=correct_answer)
```

**이점**: Active Learning으로 정확도 점진적 향상

---

**방어선 4: 금지 단어 필터**

```python
FORBIDDEN_PHRASES = [
    # 절대 단언 금지
    '100% 보장됩니다',
    '무조건 나옵니다',
    '절대 안 나옵니다',
    '확실히 보장됩니다',

    # 오해 소지 표현
    '당연히',
    '항상',
    '절대',
    '보장받을 수 있습니다'  # → '보장받을 수 있는 것으로 해석됩니다'
]

RECOMMENDED_PHRASES = [
    '약관 제X조에 따르면',
    '~한 경우 보장되는 것으로 해석됩니다',
    '다만, 최종 판단은 보험사가 합니다',
    '구체적인 사항은 보험사 확인이 필요합니다'
]

def validate_answer_text(answer):
    """
    답변 텍스트 검증
    """
    for phrase in FORBIDDEN_PHRASES:
        if phrase in answer:
            raise ValueError(f"금지된 표현 발견: '{phrase}'")

    # 권장 표현 포함 확인
    has_recommended = any(phrase in answer for phrase in RECOMMENDED_PHRASES)
    if not has_recommended:
        warnings.warn("권장 표현이 포함되지 않았습니다.")

    return True
```

---

## 🚀 Phase별 구현 로드맵

### Phase 1: MVP (개월 1-3)

**목표**: 핵심 기능 검증 및 베타 테스트

**구현 범위**:
- ✅ **데이터셋**: 암보험 50종 (주요 5개 보험사)
- ✅ **파싱 파이프라인**: 계층 1~2 (Rule-based 중심)
- ✅ **그래프 스키마**: 기본 노드/엣지 (Product-Coverage-Disease-Condition)
- ✅ **검색 기능**: 케이스 A (단순 사실 확인) 위주
- ✅ **방어선**: 1, 2, 3 구현 (출처 강제, Confidence, Human-in-the-loop)
- ✅ **UI**: 모바일 최적화된 기본 인터페이스

**성공 지표**:
- 정확도: 85% (전문가 검토 기준)
- 응답 속도: 단순 쿼리 < 500ms
- 베타 테스터: 100명 FP 참여

**위험 요소**:
- OCR 정확도 (표/플로우차트 인식 실패 시)
- 초기 학습 데이터 부족

---

### Phase 2: 상용화 (개월 4-6)

**목표**: 전체 기능 구현 및 상용 런칭

**추가 구현**:
- ✅ **파싱 파이프라인**: 계층 3~4 (LLM 관계 추출 + 온톨로지)
- ✅ **검색 기능**: 케이스 B, C (복합 추론, 충돌 탐지)
- ✅ **데이터셋 확장**: 뇌심혈관, 실손, 연금 등 전 보험사
- ✅ **MyData 연동**: 내보험다보여 API 통합
- ✅ **고객용 리포트**: 카카오톡 공유 기능
- ✅ **Active Learning**: 전문가 피드백 자동 학습

**성공 지표**:
- 정확도: 92% 이상
- 응답 속도: 복합 쿼리 < 2초
- 약관 커버리지: 200+ 상품

**가격 모델**:
- Freemium: 월 10회 무료 분석
- Pro: 월 3만원 (무제한 분석 + 고객 리포트)
- Enterprise: 협의 (GA 단위 계약)

---

### Phase 3: 차별화 (개월 7+)

**목표**: 시장 리더십 확보

**혁신 기능**:
- ✅ **시간 그래프**: 약관 개정 이력 추적 ("2011년 가입 vs 2024년 가입 차이는?")
- ✅ **예측 분석**: "이 고객 프로필에 필요한 담보는?" (Recommendation Engine)
- ✅ **자동 스크립트 생성**: FP 상담 스크립트 AI 생성 (준법 검증 내장)
- ✅ **B2C 확장**: 일반 고객이 직접 보험 진단 → FP 역경매 매칭

**차별화 포인트**:
- 업계 유일의 시간 축 분석
- 실시간 리스크 모니터링 (약관 변경 알림)

---

## 🛠️ 기술 스택 최종 권장사항

| 레이어 | 기술 | 선택 근거 | 대안 |
|--------|------|-----------|------|
| **LLM** | **Upstage Solar Pro** | 한국어 약관 특화, 표/서식 이해 우수 | GPT-4o (복합 추론 백업) |
| **Graph DB** | **Neo4j Enterprise** | Vector Index + Graph Algorithm 하이브리드, Cypher 강력 | - |
| **Vector DB** | **Neo4j Vector Index** | 별도 DB 불필요, Latency 감소 | Pinecone (Phase 2 성능 이슈 시) |
| **OCR** | **Upstage Document Parse** | 한국어 표/서식 인식률 최고 | Naver Clova OCR |
| **Backend** | **FastAPI + LangGraph** | LangGraph: Multi-agent orchestration (파싱→추출→검증) | - |
| **Frontend** | **Next.js + Cytoscape.js** | Cytoscape: 그래프 시각화 성능 우수 | D3.js (커스터마이징 필요 시) |
| **Infra** | **AWS (EKS + RDS + S3)** | 금융규제 샌드박스 망분리 요건 충족 가능 | GCP, Azure |

---

## ⚠️ 핵심 리스크 & 완화 전략

### 리스크 1: "Neo4j 벡터 인덱스만으로 충분한가?"

**우려사항**:
- 대규모 벡터 검색 시 성능 저하 가능성
- 전문 벡터 DB 대비 기능 제한

**완화 전략**:
- Phase 1에서 Neo4j Vector Index로 시작 (개발 속도 우선)
- 성능 벤치마크 지속 모니터링
- 이슈 발생 시 Pinecone 추가 (마이그레이션 비용 낮음)
- **판단 기준**: 쿼리 응답 시간 > 1초 지속 시 전환

---

### 리스크 2: "Upstage Solar Pro의 추론 능력 한계"

**우려사항**:
- 복잡한 Multi-hop 추론 실패 가능성
- GPT-4o 대비 논리적 추론 능력 부족

**완화 전략**:
- **Cascade 전략**:
  1. Solar Pro로 1차 시도 (비용 효율적)
  2. Confidence < 0.7 시 GPT-4o로 재시도
  3. 비용은 높지만 정확도 우선
- **예상 비용**: 전체 쿼리의 15% → GPT-4o 사용 (월 $500 추가)

---

### 리스크 3: "Rule-based 파서 유지보수 부담"

**우려사항**:
- 보험사별로 약관 포맷이 달라 규칙 폭발
- 신규 보험사 추가 시마다 수동 작업

**완화 전략**:
- **템플릿 라이브러리**: 보험사별 파싱 템플릿 저장
- **Few-shot Learning**: 새 보험사 추가 시 5~10개 샘플로 학습
- **자동화 로드맵**: Phase 3에서 LLM Fine-tuning으로 완전 자동화

---

### 리스크 4: "할루시네이션 발생 시 법적 책임"

**우려사항**:
- AI가 잘못된 답변 → FP가 오안내 → 배상 책임

**완화 전략**:
- **4단계 방어선** 엄격 적용
- **면책 조항**:
  - 모든 답변 하단에 "본 분석은 참고용이며, 최종 판단은 보험사가 합니다" 명시
  - 서비스 약관에 AI 답변의 법적 책임 한계 명시
- **보험 가입**: E&O 보험 (전문가 배상책임보험) 가입 검토

---

## 📊 성능 목표 & KPI

| 지표 | Phase 1 (MVP) | Phase 2 (상용) | Phase 3 (차별화) |
|------|---------------|----------------|------------------|
| **정확도** | 85% | 92% | 96% |
| **단순 쿼리 응답** | < 500ms | < 300ms | < 200ms |
| **복합 쿼리 응답** | < 3초 | < 2초 | < 1.5초 |
| **약관 커버리지** | 50종 | 200종 | 500종 |
| **사용자 만족도** | - | NPS 40+ | NPS 60+ |

---

## 🎓 참고 자료

### 학술 논문
- "Graph Retrieval-Augmented Generation: A Survey" (2024)
- "Knowledge Graphs for Legal Document Analysis" (2023)

### 기술 문서
- Neo4j Vector Index Documentation
- LangGraph Multi-Agent Patterns
- Upstage Document Parse API Reference

### 경쟁 분석
- (추후 Competitor Analysis 문서 참조)

---

## 📝 다음 단계

이 전략 문서를 기반으로:

1. **Architect에게 전달**: 상세 기술 스펙 작성 (API 설계, DB 스키마, 인프라)
2. **PM에게 전달**: Epic & User Story 구체화
3. **추가 브레인스토밍**: UX 설계, 비즈니스 모델, 규제 대응

---

**승인자**: (추후 Architect/CTO 검토)
**상태**: Draft → Pending Review
