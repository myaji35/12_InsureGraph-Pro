# Epic 2: GraphRAG Query Engine

**Epic ID**: EPIC-02
**Priority**: Critical (P0)
**Phase**: Phase 1 (MVP)
**Estimated Duration**: 4-5 weeks
**Team**: Backend Engineers, ML Engineers

---

## Executive Summary

Build the GraphRAG query engine that processes natural language questions and returns accurate, evidence-based answers by combining vector search with graph traversal. This is the core differentiator that enables FPs to answer complex policy questions instantly.

### Business Value

- **Core Product Value**: Enables the main use case - FPs asking policy questions
- **Competitive Advantage**: Multi-hop reasoning that simple vector search cannot achieve
- **User Trust**: Provenance tracking ensures every answer has verifiable sources
- **Revenue Driver**: High-quality answers → user retention → subscription conversion

### Success Criteria

- ✅ Answer simple coverage questions in < 500ms with > 85% accuracy
- ✅ Handle complex multi-hop questions with > 80% accuracy
- ✅ All answers include source clause references (100%)
- ✅ Confidence scoring correctly predicts answer quality (AUC > 0.85)
- ✅ Zero answers with forbidden phrases in production

---

## User Stories

### Story 2.1: Query Classification & Routing

**Story ID**: STORY-2.1
**Priority**: Critical (P0)
**Story Points**: 5

#### User Story

```
As the Query Engine,
I want to classify incoming queries by type and complexity,
So that I can route them to the optimal retrieval strategy.
```

#### Acceptance Criteria

**Given** a user submits a natural language query
**When** the QueryClassifier analyzes the query
**Then** the system should classify it into one of:
- `simple_coverage`: "갑상선암 보장돼요?" → Vector search + 1-hop graph
- `comparison`: "A상품과 B상품 비교" → Pre-computed conflict detection
- `gap_analysis`: "부족한 보장은?" → Customer profile analysis
- `temporal`: "2011년 가입 vs 2024년 차이?" → Temporal graph traversal
- `general`: Fallback for unclassified queries

**Given** a query matches multiple patterns
**When** classification runs
**Then** the system should:
- Return the most specific classification
- Include confidence score for classification
- Log the classification decision for monitoring

#### Technical Tasks

- [ ] Design query classification taxonomy
- [ ] Implement QueryClassifier class
  - [ ] Regex-based pattern matching (fast path)
  - [ ] LLM-based classification (complex queries)
  - [ ] Confidence scoring
- [ ] Create classification pattern library
  - [ ] Korean question patterns (보장돼요, 나와요, etc.)
  - [ ] Comparison patterns (비교, 차이, 중복)
  - [ ] Temporal patterns (년, 개정, 예전)
- [ ] Implement routing logic based on classification
- [ ] Add classification metrics (confusion matrix)
- [ ] Write unit tests (50+ test queries)
- [ ] Benchmark classification accuracy

#### Dependencies

- None (first story in Epic 2)

#### Technical Notes

```python
class QueryClassifier:
    """
    Classify queries for optimal retrieval strategy
    """
    PATTERNS = {
        'simple_coverage': [
            r'(보장|담보).*돼',
            r'나와요',
            r'지급.*되나요',
            r'받을.*수.*있나요'
        ],
        'comparison': [
            r'(비교|차이)',
            r'중복.*보장',
            r'(어느|어떤).*좋',
            r'[AB].*상품.*중'
        ],
        'temporal': [
            r'\d{4}년.*가입',
            r'(예전|이전|옛날).*약관',
            r'(개정|변경).*전',
            r'지금.*과.*다른'
        ],
        'gap_analysis': [
            r'부족.*보장',
            r'추가.*필요',
            r'공백',
            r'더.*필요한'
        ]
    }

    def classify(self, query: str) -> dict:
        """
        Classify query with confidence score
        """
        # Fast path: Regex matching
        for query_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return {
                        'type': query_type,
                        'confidence': 0.90,
                        'method': 'regex'
                    }

        # Slow path: LLM classification
        llm_result = self.llm_classify(query)
        return {
            'type': llm_result['type'],
            'confidence': llm_result['confidence'],
            'method': 'llm'
        }

    def llm_classify(self, query: str) -> dict:
        """
        LLM-based classification for complex queries
        """
        prompt = f"""
        다음 질문의 유형을 분류하세요:

        질문: {query}

        유형:
        - simple_coverage: 단순 보장 여부 질문
        - comparison: 상품 비교
        - gap_analysis: 보장 공백 분석
        - temporal: 시간에 따른 약관 변화
        - general: 기타

        JSON 형식으로 답하세요:
        {{"type": "...", "confidence": 0.0-1.0}}
        """

        response = self.llm.generate(prompt)
        return json.loads(response)
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Classification accuracy > 90% on test set (100 queries)
- [ ] Unit tests passing
- [ ] Classification latency < 50ms (regex), < 200ms (LLM)
- [ ] Monitoring dashboard for classification distribution
- [ ] Documentation updated

---

### Story 2.2: Vector Search Implementation

**Story ID**: STORY-2.2
**Priority**: Critical (P0)
**Story Points**: 8

#### User Story

```
As the Query Engine,
I want to perform semantic search on clause embeddings,
So that I can find relevant clauses even when exact keywords don't match.
```

#### Acceptance Criteria

**Given** a user query
**When** vector search executes
**Then** the system should:
- Generate query embedding (1536-dim vector for OpenAI ada-002)
- Search Neo4j vector index on Clause.embedding
- Return top-k most similar clauses (k=10 default, configurable)
- Include similarity scores (0.0-1.0)
- Return clause metadata (article, page, product)

**Given** query is short (< 5 words)
**When** vector search runs
**Then** the system should:
- Expand query with synonyms/related terms
- Or use hybrid keyword + vector search

**Given** no clauses have similarity > 0.5
**When** search completes
**Then** the system should:
- Return empty result set
- Flag as "no_relevant_clauses_found"
- Suggest query reformulation to user

#### Technical Tasks

- [ ] Integrate embedding model (OpenAI ada-002 or Upstage)
- [ ] Implement VectorSearcher class
  - [ ] Query embedding generation
  - [ ] Neo4j vector index querying
  - [ ] Result formatting
- [ ] Implement query expansion for short queries
- [ ] Add caching for query embeddings (Redis)
- [ ] Optimize Neo4j vector index parameters
  - [ ] Tune similarity function (cosine vs. euclidean)
  - [ ] Tune index size for speed/accuracy tradeoff
- [ ] Write unit tests with mock embeddings
- [ ] Benchmark search latency (target: < 100ms)
- [ ] Benchmark search accuracy (precision@10)

#### Dependencies

- Story 1.7 completed (Neo4j vector index created)
- Clause embeddings generated during ingestion

#### Technical Notes

```python
class VectorSearcher:
    """
    Semantic search using Neo4j vector index
    """
    def __init__(self):
        self.embedder = OpenAIEmbedder()  # or UpstageEmbedder
        self.cache = Redis()
        self.driver = neo4j.GraphDatabase.driver(NEO4J_URI)

    async def search(self, query: str, top_k: int = 10) -> List[dict]:
        """
        Vector search on clause embeddings
        """
        # Check cache first
        cache_key = f"embedding:{hash(query)}"
        query_embedding = self.cache.get(cache_key)

        if not query_embedding:
            query_embedding = await self.embedder.embed(query)
            self.cache.setex(cache_key, 3600, json.dumps(query_embedding))
        else:
            query_embedding = json.loads(query_embedding)

        # Query Neo4j vector index
        cypher = """
        CALL db.index.vector.queryNodes('clause_embeddings', $top_k, $query_embedding)
        YIELD node, score

        MATCH (node)-[:DEFINED_IN|REFERENCES*0..1]-(related)

        RETURN node.id AS clause_id,
               node.article_num AS article,
               node.paragraph AS paragraph,
               node.raw_text AS text,
               node.page_num AS page,
               score,
               collect(DISTINCT related.id) AS related_clauses
        ORDER BY score DESC
        """

        with self.driver.session() as session:
            results = session.run(cypher, top_k=top_k, query_embedding=query_embedding)
            return [dict(record) for record in results]
```

**Neo4j Vector Search Optimization**:

```cypher
// Monitor vector index performance
CALL db.index.vector.queryNodes('clause_embeddings', 10, $embedding)
YIELD node, score

// Explain query plan
PROFILE CALL db.index.vector.queryNodes(...)
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Vector search functional with Neo4j index
- [ ] Embedding cache implemented
- [ ] Search latency < 100ms (p95)
- [ ] Precision@10 > 0.7 on test set
- [ ] Unit and integration tests passing
- [ ] Documentation updated

---

### Story 2.3: Graph Traversal for Multi-hop Reasoning

**Story ID**: STORY-2.3
**Priority**: Critical (P0)
**Story Points**: 13

#### User Story

```
As the Query Engine,
I want to traverse the knowledge graph to find indirect relationships,
So that I can answer complex questions requiring multi-hop reasoning.
```

#### Acceptance Criteria

**Given** a query requires multi-hop reasoning (e.g., "갑상선 림프절 전이 보장?")
**When** graph traversal executes
**Then** the system should:
- Start from coverage/disease entities identified by vector search
- Traverse relationships (COVERS, EXCLUDES, REQUIRES, REFERENCES) up to N hops
- Follow provenance links (DEFINED_IN) to source clauses
- Return all paths that satisfy the query
- Include confidence scores based on path length and edge weights

**Given** multiple paths exist to the same answer
**When** traversal completes
**Then** the system should:
- Return all paths for transparency
- Rank paths by confidence (shorter path = higher confidence)
- Highlight conflicting paths (one says COVERS, another says EXCLUDES)

**Given** a path exceeds max_hops limit
**When** traversal runs
**Then** the system should:
- Stop traversal at max_hops (default: 3)
- Log truncated paths for monitoring
- Return partial results with warning

#### Technical Tasks

- [ ] Design Cypher query templates for common patterns
  - [ ] Simple coverage: Product → Coverage → Disease
  - [ ] With conditions: Product → Coverage → Disease ← Condition
  - [ ] With exclusions: Coverage → Disease, Coverage → Exclusion
  - [ ] Temporal: Product → REPLACES → Product → Coverage
- [ ] Implement GraphTraverser class
  - [ ] Dynamic Cypher query generation
  - [ ] Path ranking algorithm
  - [ ] Conflict detection (COVERS vs. EXCLUDES)
- [ ] Implement path confidence scoring
  - [ ] Shorter paths = higher confidence
  - [ ] Direct edges > indirect edges
  - [ ] Validated edges > unvalidated edges
- [ ] Optimize traversal performance
  - [ ] Limit result set size (max 100 paths)
  - [ ] Use query hints (INDEX, USING SCAN)
  - [ ] Monitor query execution time
- [ ] Write unit tests with test graph data
- [ ] Benchmark traversal latency (target: < 500ms)

#### Dependencies

- Story 2.2 completed (vector search identifies starting nodes)
- Neo4j graph fully populated (Epic 1 completed)

#### Technical Notes

**Cypher Query Templates**:

```cypher
// Template 1: Simple coverage check
MATCH path = (p:Product {id: $product_id})-[:HAS_COVERAGE]->(cov:Coverage)
             -[r:COVERS|EXCLUDES]->(d:Disease)
WHERE d.kcd_code STARTS WITH $kcd_prefix
  OR d.name_ko CONTAINS $disease_term

OPTIONAL MATCH (cov)-[:REQUIRES]->(cond:Condition)
OPTIONAL MATCH (cov)-[:DEFINED_IN]->(clause:Clause)

RETURN path, r.type AS relation_type, cond, clause,
       length(path) AS path_length
ORDER BY path_length ASC
LIMIT 50

// Template 2: Conflict detection (중복 보장)
MATCH (p1:Product {id: $product_id_1})-[:HAS_COVERAGE]->(c1:Coverage)
      -[:COVERS]->(d:Disease)<-[:COVERS]-(c2:Coverage)
      <-[:HAS_COVERAGE]-(p2:Product {id: $product_id_2})

OPTIONAL MATCH (c1)-[:APPLIES_RULE]->(pr1:PaymentRule)
OPTIONAL MATCH (c2)-[:APPLIES_RULE]->(pr2:PaymentRule)

RETURN d.name_ko AS disease,
       c1.name AS coverage_1,
       c2.name AS coverage_2,
       pr1.proportional_ratio AS ratio_1,
       pr2.proportional_ratio AS ratio_2

// Template 3: Temporal comparison
MATCH path = (current:Product {id: $product_id})
             -[:REPLACES*0..5]->(old:Product)
WHERE old.launch_date < date($reference_date)

MATCH (old)-[:HAS_COVERAGE]->(cov:Coverage)
      -[:DEFINED_IN]->(clause:Clause)
WHERE clause.raw_text CONTAINS $search_term

RETURN path, old.launch_date, clause.raw_text
ORDER BY old.launch_date ASC
```

**Path Confidence Scoring**:

```python
def calculate_path_confidence(path: dict) -> float:
    """
    Score path based on length, edge types, validation status
    """
    base_score = 1.0

    # Penalize longer paths
    length_penalty = 0.1 * path['path_length']

    # Boost for validated edges
    validation_boost = 0.0
    for edge in path['edges']:
        if edge.get('verified_by_expert'):
            validation_boost += 0.1

    # Penalize LLM-extracted edges
    extraction_penalty = 0.0
    for edge in path['edges']:
        if edge.get('extraction_method') == 'llm_extracted':
            extraction_penalty += 0.05

    confidence = base_score - length_penalty + validation_boost - extraction_penalty
    return max(0.0, min(1.0, confidence))
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Cypher templates for 5+ common patterns
- [ ] Graph traversal functional for multi-hop queries
- [ ] Path ranking implemented
- [ ] Conflict detection working
- [ ] Traversal latency < 500ms (p95)
- [ ] Unit and integration tests passing
- [ ] Documentation with query examples

---

### Story 2.4: LLM Reasoning Layer

**Story ID**: STORY-2.4
**Priority**: Critical (P0)
**Story Points**: 13

#### User Story

```
As the Query Engine,
I want to use LLM to synthesize graph results into natural language answers,
So that users receive clear, interpretable responses with reasoning.
```

#### Acceptance Criteria

**Given** vector search and graph traversal return results
**When** the LLM reasoning layer processes the results
**Then** the system should:
- Generate a 2-3 sentence summary answer
- Explain the reasoning (which paths were followed)
- Reference specific clauses (제N조 ①항)
- Include confidence score
- Use professional, cautious language ("약관에 따르면", "해석됩니다")

**Given** graph results are conflicting (COVERS and EXCLUDES both exist)
**When** LLM generates answer
**Then** the system should:
- Clearly state the conflict
- Explain both sides
- Recommend consulting the insurer
- Lower confidence score

**Given** LLM confidence < 0.7
**When** Solar Pro returns low-confidence answer
**Then** the system should:
- Retry with GPT-4o (cascade strategy)
- Use the higher-confidence result
- Log both responses for analysis

#### Technical Tasks

- [ ] Design reasoning prompt template
  - [ ] System role: 보험 약관 전문가
  - [ ] Input: Graph paths + source clauses
  - [ ] Output format: JSON with summary, details, confidence
- [ ] Implement ReasoningAgent class
  - [ ] Integrate Solar Pro API
  - [ ] Integrate GPT-4o API (fallback)
  - [ ] Cascade logic (confidence-based)
- [ ] Implement context formatting
  - [ ] Graph paths → readable text
  - [ ] Clause references → formatted citations
- [ ] Implement answer parsing and validation
  - [ ] JSON parsing with error handling
  - [ ] Confidence score normalization
- [ ] Add response caching (Redis)
- [ ] Write unit tests with mock LLM responses
- [ ] Benchmark LLM latency and cost

#### Dependencies

- Story 2.2, 2.3 completed (retrieval results available)

#### Technical Notes

**Reasoning Prompt Template**:

```python
REASONING_PROMPT = """
당신은 보험 약관 전문가입니다. 다음 정보를 바탕으로 사용자 질문에 답변하세요.

[사용자 질문]
{query}

[그래프 분석 결과]
경로 1:
- 상품: {product_name}
- 담보: {coverage_name}
- 관계: {relation_type} (COVERS/EXCLUDES)
- 대상: {disease_name} ({kcd_code})
- 조건: {conditions}

{additional_paths}

[원문 조항]
제{article_num}조 [{title}] {paragraph}
"{clause_text}"

[지침]
1. 반드시 제공된 원문 조항을 근거로 답변하세요
2. 약관에 명시되지 않은 내용은 "확인이 필요합니다"라고 답하세요
3. 절대적 단언("100% 보장", "무조건")은 사용하지 마세요
4. "약관 제X조에 따르면"과 같은 표현을 포함하세요
5. 충돌이 있다면 명확히 언급하세요

[출력 형식 - JSON]
{{
  "summary": "2-3문장 요약 답변",
  "details": [
    {{
      "product": "상품명",
      "coverage": "담보명",
      "is_covered": true/false,
      "conditions": [
        {{"type": "waiting_period", "days": 90, "description": "..."}}
      ],
      "amount": 100000000,
      "reasoning": "판단 근거 설명"
    }}
  ],
  "confidence": 0.0-1.0,
  "sources": ["clause_id_1", "clause_id_2"],
  "warnings": ["충돌 사항 또는 주의사항"]
}}

답변:
"""
```

**Cascade Strategy**:

```python
class ReasoningAgent:
    """
    LLM-based reasoning with cascade fallback
    """
    CONFIDENCE_THRESHOLD = 0.7

    async def reason(self, query: str, graph_results: dict) -> dict:
        """
        Generate answer with reasoning
        """
        context = self.format_context(graph_results)
        prompt = REASONING_PROMPT.format(query=query, **context)

        # Try Solar Pro first (cost-effective)
        solar_response = await self.solar_llm.generate(prompt)
        solar_answer = json.loads(solar_response)

        if solar_answer['confidence'] >= self.CONFIDENCE_THRESHOLD:
            return {
                'answer': solar_answer,
                'model': 'solar-pro',
                'cost': 0.002  # approximate
            }

        # Fallback to GPT-4o
        gpt4_response = await self.gpt4_llm.generate(prompt)
        gpt4_answer = json.loads(gpt4_response)

        # Use whichever is more confident
        if gpt4_answer['confidence'] > solar_answer['confidence']:
            return {
                'answer': gpt4_answer,
                'model': 'gpt-4o',
                'cost': 0.015  # approximate
            }
        else:
            return {
                'answer': solar_answer,
                'model': 'solar-pro-fallback',
                'cost': 0.002
            }
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Solar Pro + GPT-4o cascade implemented
- [ ] Answer quality > 85% on test set (manual evaluation)
- [ ] LLM latency < 2s (p95)
- [ ] Cost per query < $0.02
- [ ] Unit tests passing
- [ ] Documentation updated

---

### Story 2.5: Answer Validation (4-Stage Defense)

**Story ID**: STORY-2.5
**Priority**: Critical (P0)
**Story Points**: 8

#### User Story

```
As the Query Engine,
I want to validate all answers through multiple checks,
So that I prevent hallucinations and ensure answer quality.
```

#### Acceptance Criteria

**Given** LLM generates an answer
**When** validation runs
**Then** the system should check:
1. **Source attachment**: All claims have clause references
2. **Confidence threshold**: Confidence meets minimum requirements
3. **Forbidden phrases**: No absolute claims ("100% 보장")
4. **Consistency**: Answer matches graph results (no contradictions)

**Given** validation fails at any stage
**When** the check fails
**Then** the system should:
- Reject the answer (do not return to user)
- Log the failure reason
- Return error message or queue for expert review

**Given** confidence is medium (0.7-0.85)
**When** validation completes
**Then** the system should:
- Attach warning message to answer
- Add to expert review queue
- Still return answer to user (with disclaimer)

#### Technical Tasks

- [ ] Implement AnswerValidator class
  - [ ] `check_sources()` - verify clause references exist
  - [ ] `check_confidence()` - apply thresholds
  - [ ] `check_forbidden_phrases()` - regex matching
  - [ ] `check_consistency()` - compare answer vs. graph
- [ ] Define confidence thresholds
  - [ ] High: > 0.85 (proceed)
  - [ ] Medium: 0.7-0.85 (proceed with warning)
  - [ ] Low: 0.6-0.7 (expert review)
  - [ ] Reject: < 0.6 (do not return)
- [ ] Create forbidden phrase library (Korean)
- [ ] Implement consistency checker
  - [ ] If graph says EXCLUDES, answer should say "면책"
  - [ ] If conditions exist, answer must mention them
- [ ] Add expert review queue (PostgreSQL table)
- [ ] Write unit tests for each validation stage
- [ ] Benchmark validation latency (< 50ms)

#### Dependencies

- Story 2.4 completed (LLM answers available)

#### Technical Notes

```python
class AnswerValidator:
    """
    4-stage validation pipeline
    """
    CONFIDENCE_THRESHOLDS = {
        'high': 0.85,
        'medium': 0.70,
        'low': 0.60,
        'reject': 0.60
    }

    FORBIDDEN_PHRASES = [
        '100% 보장',
        '무조건',
        '절대',
        '확실히',
        '당연히',
        '항상',
        '반드시 나옵니다'
    ]

    def validate(self, answer: dict, graph_results: dict) -> dict:
        """
        Run all validation stages
        """
        # Stage 1: Source attachment
        if not self.check_sources(answer, graph_results):
            return {
                'status': 'rejected',
                'reason': 'no_source_reference',
                'message': '답변 생성 실패: 근거가 되는 약관 조항을 찾을 수 없습니다.'
            }

        # Stage 2: Confidence threshold
        confidence_status = self.check_confidence(answer['confidence'])
        if confidence_status == 'reject':
            return {
                'status': 'rejected',
                'reason': 'low_confidence',
                'message': '죄송합니다. 이 질문은 현재 시스템으로 정확히 답변하기 어렵습니다.'
            }

        # Stage 3: Forbidden phrases
        violations = self.check_forbidden_phrases(answer['summary'])
        if violations:
            return {
                'status': 'rejected',
                'reason': 'forbidden_phrase',
                'violations': violations,
                'message': '답변에 부적절한 표현이 포함되어 있습니다.'
            }

        # Stage 4: Consistency check
        if not self.check_consistency(answer, graph_results):
            return {
                'status': 'needs_review',
                'reason': 'inconsistent',
                'message': '그래프 결과와 답변이 일치하지 않아 전문가 검토가 필요합니다.'
            }

        # All checks passed
        warnings = []
        if confidence_status == 'medium':
            warnings.append('⚠️ 이 답변은 약관 해석이 복잡합니다. 보험사에 확인하시기를 권장합니다.')
        elif confidence_status == 'low':
            self.add_to_review_queue(answer, graph_results)
            warnings.append('⚠️ 전문가 검토가 필요한 질문입니다.')

        return {
            'status': 'approved',
            'answer': answer,
            'warnings': warnings
        }

    def check_consistency(self, answer: dict, graph_results: dict) -> bool:
        """
        Check if answer matches graph results
        """
        for detail in answer.get('details', []):
            # Find corresponding graph path
            matching_path = self.find_matching_path(detail, graph_results)

            if not matching_path:
                return False

            # Check if answer's is_covered matches graph's relation_type
            graph_relation = matching_path['relation_type']
            answer_covered = detail['is_covered']

            if graph_relation == 'COVERS' and not answer_covered:
                return False
            if graph_relation == 'EXCLUDES' and answer_covered:
                return False

        return True
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] All 4 validation stages implemented
- [ ] Validation catches 100% of test violations
- [ ] Validation latency < 50ms
- [ ] Expert review queue functional
- [ ] Unit tests passing (50+ test cases)
- [ ] Documentation updated

---

### Story 2.6: Query API Implementation

**Story ID**: STORY-2.6
**Priority**: Critical (P0)
**Story Points**: 5

#### User Story

```
As an FP user,
I want to submit natural language queries via API,
So that I can get answers to policy questions in my application.
```

#### Acceptance Criteria

**Given** I am authenticated as an FP user
**When** I POST to `/api/v1/analysis/query` with a query
**Then** the system should:
- Accept the query and optional context (product_ids, customer_profile)
- Execute the full query pipeline (classify → retrieve → reason → validate)
- Return formatted answer with summary, details, sources, confidence
- Include reasoning path (graph visualization data) if requested
- Complete in < 3 seconds for complex queries, < 500ms for simple

**Given** my query is invalid (empty, too long, etc.)
**When** I submit the query
**Then** the system should:
- Return 400 Bad Request with error details
- Not consume LLM API credits

**Given** the system is under heavy load
**When** I submit a query
**Then** the system should:
- Queue the request if necessary
- Return 503 Service Unavailable if queue is full
- Log the event for capacity planning

#### Technical Tasks

- [ ] Implement `POST /api/v1/analysis/query` endpoint
- [ ] Integrate full query pipeline
  - [ ] QueryClassifier (Story 2.1)
  - [ ] VectorSearcher (Story 2.2)
  - [ ] GraphTraverser (Story 2.3)
  - [ ] ReasoningAgent (Story 2.4)
  - [ ] AnswerValidator (Story 2.5)
- [ ] Implement request validation
  - [ ] Query length limits (5-500 characters)
  - [ ] Product IDs validation
  - [ ] Customer profile schema validation
- [ ] Add rate limiting (per user tier)
- [ ] Implement query logging (audit trail)
- [ ] Add performance monitoring (latency, success rate)
- [ ] Write integration tests (end-to-end)
- [ ] Update OpenAPI documentation

#### Dependencies

- Stories 2.1-2.5 completed (full pipeline ready)

#### Technical Notes

**API Endpoint**:

```python
@router.post("/api/v1/analysis/query")
async def execute_query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute GraphRAG query
    """
    # Validate request
    if not request.query or len(request.query) < 5:
        raise HTTPException(400, "Query too short")
    if len(request.query) > 500:
        raise HTTPException(400, "Query too long")

    # Check rate limits
    if not check_rate_limit(current_user.id, tier=current_user.tier):
        raise HTTPException(429, "Rate limit exceeded")

    # Log query
    query_log = log_query(
        user_id=current_user.id,
        query_text=request.query,
        context=request.context
    )

    try:
        # Execute pipeline
        start_time = time.time()

        classification = query_classifier.classify(request.query)
        vector_results = await vector_searcher.search(request.query, top_k=10)
        graph_results = await graph_traverser.traverse(
            query=request.query,
            starting_nodes=vector_results,
            max_hops=request.options.get('max_hops', 3)
        )

        llm_answer = await reasoning_agent.reason(request.query, graph_results)
        validation_result = answer_validator.validate(llm_answer['answer'], graph_results)

        execution_time = (time.time() - start_time) * 1000  # ms

        # Handle validation result
        if validation_result['status'] == 'rejected':
            return JSONResponse(
                status_code=200,
                content={
                    'query_id': query_log.id,
                    'status': 'failed',
                    'message': validation_result['message'],
                    'execution_time_ms': execution_time
                }
            )

        # Format response
        response = {
            'query_id': query_log.id,
            'answer': validation_result['answer'],
            'reasoning_path': format_reasoning_path(graph_results),
            'sources': format_sources(graph_results.get('source_clauses', [])),
            'warnings': validation_result.get('warnings', []),
            'disclaimer': '본 분석은 참고용이며, 최종 판단은 보험사가 합니다.',
            'execution_time_ms': execution_time,
            'model_used': llm_answer['model'],
            'cost': llm_answer['cost']
        }

        # Update query log
        update_query_log(query_log.id, response)

        # Update metrics
        metrics.query_execution_time.observe(execution_time)
        metrics.query_confidence.observe(validation_result['answer']['confidence'])

        return response

    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        update_query_log(query_log.id, {'status': 'error', 'error': str(e)})
        raise HTTPException(500, "Query execution failed")
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] API endpoint functional and tested
- [ ] End-to-end tests passing (20+ scenarios)
- [ ] Rate limiting working
- [ ] Query logging complete
- [ ] Performance < 3s (p95) for complex queries
- [ ] OpenAPI docs updated
- [ ] Deployed to dev environment

---

### Story 2.7: Gap Analysis Feature

**Story ID**: STORY-2.7
**Priority**: High (P1)
**Story Points**: 13

#### User Story

```
As an FP user,
I want to analyze a customer's coverage gaps,
So that I can identify opportunities to recommend additional policies.
```

#### Acceptance Criteria

**Given** I provide a customer's current policies and profile
**When** gap analysis runs
**Then** the system should:
- Identify missing coverages (e.g., no cancer coverage)
- Identify outdated policies (old terms vs. new)
- Identify insufficient amounts (coverage < recommended)
- Return scored gaps (high/medium/low severity)
- Recommend specific products to fill gaps

**Given** a customer has no critical gaps
**When** analysis completes
**Then** the system should:
- Return positive feedback ("Well covered!")
- Suggest optional enhancements if any
- Provide overall coverage score (0-100)

#### Technical Tasks

- [ ] Design gap analysis algorithm
  - [ ] Define coverage categories (cancer, cardiovascular, disability, etc.)
  - [ ] Define recommended coverage by age/occupation
  - [ ] Identify gap types (missing, insufficient, outdated)
- [ ] Implement GapAnalyzer class
  - [ ] Parse customer's current policies
  - [ ] Match policies to graph entities
  - [ ] Compare current vs. recommended
  - [ ] Score gap severity
- [ ] Implement product recommendation engine
  - [ ] Find products that fill identified gaps
  - [ ] Rank by suitability score
- [ ] Implement `POST /api/v1/analysis/gap-analysis` endpoint
- [ ] Write unit tests with test customer profiles
- [ ] Manual testing with real policy data

#### Dependencies

- Epic 1 completed (knowledge graph populated)
- Story 2.6 completed (API infrastructure ready)

#### Technical Notes

**Gap Analysis Algorithm**:

```python
class GapAnalyzer:
    """
    Analyze customer coverage gaps
    """
    RECOMMENDED_COVERAGE = {
        'cancer': {
            'age_20_39': 50000000,
            'age_40_59': 100000000,
            'age_60_plus': 100000000
        },
        'cardiovascular': {
            'age_20_39': 30000000,
            'age_40_59': 50000000,
            'age_60_plus': 100000000
        },
        # ...
    }

    def analyze(self, customer: dict) -> dict:
        """
        Identify coverage gaps
        """
        gaps = []

        # Get recommended coverage for customer profile
        age = calculate_age(customer['birth_year'])
        recommended = self.get_recommended_coverage(age, customer['occupation'])

        # Parse current policies
        current_coverage = self.parse_current_policies(customer['policies'])

        # Compare
        for category, rec_amount in recommended.items():
            current_amount = current_coverage.get(category, 0)

            if current_amount == 0:
                gaps.append({
                    'type': 'missing_coverage',
                    'category': category,
                    'severity': 'high',
                    'description': f'{category} 담보가 전혀 없습니다',
                    'impact': {
                        'potential_loss': rec_amount,
                        'probability': 'medium'
                    }
                })
            elif current_amount < rec_amount * 0.5:
                gaps.append({
                    'type': 'insufficient_coverage',
                    'category': category,
                    'severity': 'medium',
                    'current_amount': current_amount,
                    'recommended_amount': rec_amount,
                    'gap_amount': rec_amount - current_amount
                })

        # Check for outdated policies
        for policy in customer['policies']:
            if policy['purchase_date'] < '2015-01-01':
                outdated_issues = self.check_outdated_terms(policy)
                if outdated_issues:
                    gaps.append({
                        'type': 'outdated_policy',
                        'severity': 'medium',
                        'policy_id': policy['product_id'],
                        'issues': outdated_issues
                    })

        return {
            'gaps': gaps,
            'score': self.calculate_coverage_score(current_coverage, recommended),
            'recommendations': self.generate_recommendations(gaps)
        }
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Gap analysis algorithm implemented
- [ ] API endpoint functional
- [ ] Product recommendations generated
- [ ] Unit tests passing
- [ ] Manual testing completed
- [ ] Documentation updated

---

### Story 2.8: Product Comparison Feature

**Story ID**: STORY-2.8
**Priority**: High (P1)
**Story Points**: 8

#### User Story

```
As an FP user,
I want to compare multiple insurance products side-by-side,
So that I can recommend the best option to my customer.
```

#### Acceptance Criteria

**Given** I provide 2-3 product IDs
**When** comparison runs
**Then** the system should:
- Extract key coverages from each product
- Identify overlapping coverages
- Highlight unique coverages (only in product A)
- Compare payment conditions (waiting periods, amounts)
- Detect conflicts (proportional payment rules)
- Provide recommendation based on criteria

**Given** products have overlapping cancer coverage
**When** comparison runs
**Then** the system should:
- Calculate combined payout with proportional rules
- Warn if overlap is inefficient (paying double premium)

#### Technical Tasks

- [ ] Design comparison matrix data structure
- [ ] Implement ProductComparer class
  - [ ] Extract comparable attributes from graph
  - [ ] Align coverages across products
  - [ ] Detect overlaps using CONFLICTS_WITH edges
- [ ] Implement `POST /api/v1/analysis/compare` endpoint
- [ ] Create comparison visualization data format
- [ ] Write unit tests with test products
- [ ] Manual testing with real products

#### Dependencies

- Story 2.6 completed (API infrastructure)
- Neo4j CONFLICTS_WITH relationships populated

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Comparison algorithm implemented
- [ ] API endpoint functional
- [ ] Unit tests passing
- [ ] Documentation updated

---

## Epic Dependencies

```
Story 2.1 (Classification)
    ↓
Story 2.2 (Vector Search) ──┐
    ↓                        │
Story 2.3 (Graph Traversal) ─┤
    ↓                        │
Story 2.4 (LLM Reasoning) ◄──┘
    ↓
Story 2.5 (Validation)
    ↓
Story 2.6 (Query API)
    ↓
Story 2.7 (Gap Analysis)
Story 2.8 (Comparison)
```

---

## Technical Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Vector search recall < 70%** | High | Medium | Tune embedding model; hybrid keyword+vector search |
| **Graph traversal timeout** | High | Medium | Limit max_hops; optimize Cypher queries; add indexes |
| **LLM hallucination** | Critical | Medium | 4-stage validation; expert review queue |
| **High LLM costs** | Medium | High | Cache responses; use Solar Pro over GPT-4o; batch processing |
| **Low answer quality** | Critical | Low | Active learning from expert reviews; continuous prompt tuning |

---

## Sprint Recommendations

### Sprint 5 (2 weeks)
- Story 2.1 (Classification)
- Story 2.2 (Vector Search)

### Sprint 6 (2 weeks)
- Story 2.3 (Graph Traversal)
- Story 2.4 (LLM Reasoning) - Start

### Sprint 7 (2 weeks)
- Story 2.4 (LLM Reasoning) - Complete
- Story 2.5 (Validation)
- Story 2.6 (Query API)

### Sprint 8 (1-2 weeks)
- Story 2.7 (Gap Analysis)
- Story 2.8 (Comparison)

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Answer Accuracy** | > 85% | Manual evaluation on test set |
| **Simple Query Latency** | < 500ms | p95 monitoring |
| **Complex Query Latency** | < 3s | p95 monitoring |
| **Answer Confidence** | > 0.80 avg | Logged in database |
| **Validation Rejection Rate** | < 10% | Monitoring dashboard |
| **LLM Cost per Query** | < $0.02 | Cost monitoring |

---

**Epic Owner**: ML Engineer / Backend Tech Lead
**Stakeholders**: Product Manager, FP Users (Beta Testers)
**Next Review**: After Sprint 7 completion
