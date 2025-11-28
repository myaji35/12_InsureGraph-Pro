# Epic 1: Data Ingestion & Knowledge Graph Construction

**Epic ID**: EPIC-01
**Priority**: Critical (P0)
**Phase**: Phase 1 (MVP)
**Estimated Duration**: 4-6 weeks
**Team**: Backend Engineers, Data Engineers

---

## Executive Summary

Build the core data ingestion pipeline that transforms insurance policy PDFs into a structured knowledge graph, using a **Human-in-the-Loop metadata curation strategy** to minimize legal risks and optimize learning costs. This is the foundational capability that enables all downstream features - without accurate data ingestion, the entire GraphRAG system fails.

### Business Value

- **Enable Product**: Foundation for all analysis features
- **Competitive Advantage**: Accurate parsing of complex Korean legal documents
- **Legal Risk Mitigation**: Metadata-first approach prevents unauthorized mass crawling issues
- **Cost Optimization**: Filter low-value files before expensive GraphRAG processing
- **Scalability**: Automated pipeline supports 50+ policies in Phase 1, 500+ in Phase 3

### Success Criteria

- ✅ Metadata crawler discovers 100+ policies without legal issues
- ✅ Admin dashboard enables efficient policy selection and queueing
- ✅ Successfully ingest 10 sample cancer insurance policies
- ✅ Achieve 95%+ accuracy on critical data (amounts, periods)
- ✅ Graph construction completes in < 5 minutes per policy
- ✅ Pass validation tests on 100% of ingested policies

---

## User Stories

### Story 1.0: Metadata Crawler & Human Curation Dashboard

**Story ID**: STORY-1.0
**Priority**: Critical (P0)
**Story Points**: 8

#### User Story

```
As an Admin user,
I want to view discovered insurance policies in a curation dashboard and selectively queue them for learning,
So that I can build the knowledge graph strategically while minimizing legal and cost risks.
```

#### Acceptance Criteria

**Given** the metadata crawler has discovered new policies
**When** I access the admin curation dashboard
**Then** the system should:
- Display a filterable list of discovered policies (status: DISCOVERED)
- Show insurer name, category, policy name, publication date, file name
- Allow filtering by: insurer, date range, category, status
- Allow full-text search on policy name and file name
- Display current status with color-coded indicators

**Given** I select one or more policies
**When** I click the [Queue for Learning] button
**Then** the system should:
- Update status from DISCOVERED → QUEUED
- Record my user ID as `queued_by`
- Create ingestion job records in the database
- Trigger the on-demand downloader worker
- Show confirmation message with job IDs

**Given** a policy is already COMPLETED or PROCESSING
**When** I view the dashboard
**Then** the system should:
- Disable the [Queue for Learning] button
- Show completion date and results (nodes/edges created)
- Allow viewing the ingestion log

**Given** I want to ignore a policy
**When** I mark it as IGNORED
**Then** the system should:
- Update status to IGNORED
- Remove from default view (show only in "Ignored" filter)
- Allow adding notes explaining why it was ignored

#### Technical Tasks

**Metadata Crawler**:
- [ ] Implement lightweight web scraper (Python Scrapy or Node.js Puppeteer)
  - [ ] Target: Samsung Life, Hanwha Life, Kyobo Life disclosure pages
  - [ ] Extract: policy name, publication date, download URL
  - [ ] Parse HTML tables/lists only (NO PDF downloads)
  - [ ] Respect robots.txt and crawl delays
- [ ] Create `policy_metadata` table in PostgreSQL
- [ ] Implement crawler scheduler (daily runs via cron/Celery Beat)
- [ ] Add error handling and retry logic
- [ ] Write unit tests for parser

**Admin Curation Dashboard (Frontend)**:
- [ ] Create `/admin/metadata` page (Next.js)
- [ ] Implement policy list table with:
  - [ ] Status column with color badges
  - [ ] Filter controls (insurer, date, category, status)
  - [ ] Search box (debounced full-text search)
  - [ ] Checkbox selection for batch queueing
- [ ] Implement [Queue for Learning] action button
- [ ] Add status detail modal (show ingestion results)
- [ ] Add notes/ignore functionality
- [ ] Write Cypress E2E tests

**Backend API**:
- [ ] Implement `GET /api/v1/metadata/policies` endpoint
  - [ ] Support query params: status, insurer, date_from, date_to, search, limit, offset
  - [ ] Return paginated results
- [ ] Implement `POST /api/v1/metadata/queue` endpoint
  - [ ] Validate policy IDs
  - [ ] Update status to QUEUED
  - [ ] Create ingestion_jobs records
  - [ ] Trigger Celery worker task
- [ ] Implement `PATCH /api/v1/metadata/policies/{id}` endpoint
  - [ ] Allow status updates (IGNORED, DISCOVERED)
  - [ ] Record notes
- [ ] Write unit tests for all endpoints

**On-demand Downloader Worker**:
- [ ] Implement Celery task `download_and_ingest_policy(job_id)`
  - [ ] Fetch metadata from DB
  - [ ] Download PDF from `download_url`
  - [ ] Store in S3 with versioning
  - [ ] Update status to DOWNLOADING → PROCESSING
  - [ ] Trigger existing ingestion pipeline (Story 1.2+)
- [ ] Add retry logic (max 3 attempts)
- [ ] Implement webhook/notification on completion

#### Dependencies

- PostgreSQL database setup
- Celery worker infrastructure
- AWS S3 bucket provisioned
- Admin user authentication (RBAC)

#### Technical Notes

**Crawler Example (Scrapy)**:

```python
import scrapy

class InsurancePolicyCrawler(scrapy.Spider):
    name = 'samsung_life_crawler'
    start_urls = ['https://www.samsunglife.com/disclosure/policies']

    def parse(self, response):
        for row in response.css('table.policy-list tr'):
            yield {
                'insurer': 'Samsung Life',
                'policy_name': row.css('td.policy-name::text').get(),
                'publication_date': row.css('td.date::text').get(),
                'download_url': response.urljoin(row.css('a.download::attr(href)').get()),
                'status': 'DISCOVERED',
            }
```

**API Response Example**:

```json
GET /api/v1/metadata/policies?status=DISCOVERED&limit=10

{
  "policies": [
    {
      "id": "meta_001",
      "insurer": "Samsung Life",
      "category": "cancer",
      "policy_name": "종합암보험 2.0 약관",
      "file_name": "cancer_insurance_v2_2025.pdf",
      "publication_date": "2025-11-01",
      "download_url": "https://www.samsunglife.com/download?id=12345",
      "status": "DISCOVERED",
      "discovered_at": "2025-11-25T09:00:00Z"
    }
  ],
  "total": 247,
  "page": 1,
  "per_page": 10
}
```

#### Definition of Done

- [ ] Metadata crawler running on schedule (daily)
- [ ] Admin dashboard deployed and accessible
- [ ] Can discover 100+ policies from 3 insurers
- [ ] Can queue and process selected policies end-to-end
- [ ] All API endpoints tested and documented
- [ ] No legal issues reported (robots.txt compliant)
- [ ] Manual QA completed by product manager

---

### Story 1.1: PDF Upload & Job Management

**Story ID**: STORY-1.1
**Priority**: Critical (P0)
**Story Points**: 5

#### User Story

```
As an Admin user,
I want to upload insurance policy PDFs and track ingestion progress,
So that I can build the knowledge graph with minimal manual intervention.
```

#### Acceptance Criteria

**Given** I am logged in as an Admin user
**When** I upload a PDF file with metadata (insurer, product name, launch date)
**Then** the system should:
- Create an ingestion job with unique job_id
- Return 202 Accepted with job_id and estimated completion time
- Store the PDF in S3 with secure access controls
- Update job status in PostgreSQL (pending → processing → completed/failed)

**Given** an ingestion job is in progress
**When** I query the job status endpoint
**Then** the system should return:
- Current status (processing, completed, failed)
- Progress percentage (0-100)
- Detailed results (nodes created, edges created, errors)
- Completion timestamp

#### Technical Tasks

- [ ] Implement `POST /api/v1/policies/ingest` endpoint (FastAPI)
- [ ] Setup S3 bucket with encryption and access policies
- [ ] Create `ingestion_jobs` table in PostgreSQL
- [ ] Implement job status tracking logic
- [ ] Add file validation (PDF format, max size 100MB)
- [ ] Write unit tests for upload endpoint
- [ ] Write integration tests for S3 upload

#### Dependencies

- AWS S3 bucket provisioned
- PostgreSQL database setup
- FastAPI boilerplate ready

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Unit tests passing (coverage > 80%)
- [ ] Integration tests passing
- [ ] API documentation updated (OpenAPI)
- [ ] Deployed to dev environment
- [ ] Manual testing completed

---

### Story 1.2: OCR & Document Preprocessing

**Story ID**: STORY-1.2
**Priority**: Critical (P0)
**Story Points**: 8

#### User Story

```
As the Ingestion Pipeline,
I want to extract text, tables, and layout structure from PDF files,
So that I can parse the document hierarchy accurately.
```

#### Acceptance Criteria

**Given** a PDF policy file is uploaded
**When** the OCR agent processes the file
**Then** the system should:
- Extract full text with > 95% character accuracy
- Identify tables and extract as structured data
- Detect layout regions (header, body, footer)
- Preserve page numbers for provenance tracking
- Return confidence score for OCR quality

**Given** the OCR confidence is < 80%
**When** the processing completes
**Then** the system should:
- Flag the job for manual review
- Log specific low-confidence regions
- Not proceed to downstream stages automatically

#### Technical Tasks

- [ ] Integrate Upstage Document Parse API
- [ ] Implement OCRAgent class (async processing)
- [ ] Add retry logic for API failures (exponential backoff)
- [ ] Implement confidence score calculation
- [ ] Add table extraction and parsing
- [ ] Handle multi-column layouts
- [ ] Write unit tests with mock PDF samples
- [ ] Benchmark OCR accuracy on 10 sample policies

#### Dependencies

- Upstage API key provisioned
- Story 1.1 completed (job management)

#### Technical Notes

```python
# Expected output structure
{
  "text": "제1조 [목적] 이 보험계약은...",
  "confidence": 0.97,
  "pages": [
    {
      "page_num": 1,
      "text": "...",
      "tables": [
        {
          "bbox": [100, 200, 500, 400],
          "rows": [...],
          "columns": [...]
        }
      ],
      "regions": [
        {"type": "header", "text": "..."},
        {"type": "body", "text": "..."}
      ]
    }
  ]
}
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Upstage API integration tested
- [ ] OCR accuracy benchmarked (> 95% on test set)
- [ ] Error handling implemented and tested
- [ ] Monitoring alerts configured
- [ ] Documentation updated

---

### Story 1.3: Legal Structure Parsing (Rule-based)

**Story ID**: STORY-1.3
**Priority**: Critical (P0)
**Story Points**: 13

#### User Story

```
As the Ingestion Pipeline,
I want to parse Korean legal document structure (제N조, ①항, etc.),
So that I can build a hierarchical tree of clauses with provenance.
```

#### Acceptance Criteria

**Given** OCR text is extracted from a policy
**When** the LegalStructureParser processes the text
**Then** the system should:
- Identify all articles (제1조, 제2조, ...) with titles [보험금 지급]
- Extract paragraphs (①, ②, ③, ...)
- Extract subclauses (1., 2., 가., 나., ...)
- Detect exception clauses ("다만", "단서", "제외하고")
- Build a hierarchical tree structure (article → paragraph → subclause)
- Preserve original text and page number for each clause

**Given** a clause with nested structure
**When** parsing completes
**Then** the system should:
- Correctly establish parent-child relationships
- Maintain traversal order (article 1 before article 2)

#### Technical Tasks

- [ ] Design clause hierarchy data structure
- [ ] Implement regex patterns for Korean legal syntax
  - [ ] Article pattern: `제(\d+)조\s*\[([^\]]+)\]`
  - [ ] Paragraph pattern: `[①②③④⑤⑥⑦⑧⑨⑩]`
  - [ ] Subclause patterns: `(\d+)\.\s`, `([가나다라마])\.\s`
  - [ ] Exception patterns: `(다만|단서|제외하고)`
- [ ] Build hierarchical tree from flat text
- [ ] Handle edge cases (missing paragraphs, orphaned subclauses)
- [ ] Implement validation logic (detect parsing errors)
- [ ] Write comprehensive unit tests (20+ test cases)
- [ ] Benchmark on 10 sample policies

#### Dependencies

- Story 1.2 completed (OCR output available)

#### Technical Notes

**Expected Output Structure**:

```python
{
  "articles": [
    {
      "article_num": "제10조",
      "title": "보험금 지급",
      "page": 15,
      "bbox": [100, 200, 500, 800],
      "paragraphs": [
        {
          "paragraph_num": "①",
          "text": "회사는 피보험자가 보험기간 중 암으로 진단 확정되었을 때...",
          "subclauses": [
            {
              "subclause_num": "1",
              "text": "일반암(C77 제외): 1억원"
            },
            {
              "subclause_num": "2",
              "text": "소액암(C77): 1천만원"
            }
          ]
        },
        {
          "paragraph_num": "②",
          "text": "다만, 계약일로부터 90일 이내 진단 확정된 경우 면책..."
        }
      ]
    }
  ]
}
```

#### Known Challenges

- **Multi-column layouts**: Text order may be scrambled
- **Table interruptions**: Clauses split across table rows
- **Font variations**: Special characters (①, ②) may be images, not text
- **Inconsistent numbering**: Some policies skip paragraph numbers

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Unit tests passing (20+ test cases)
- [ ] Parsing accuracy > 90% on 10 sample policies
- [ ] Edge cases handled with graceful degradation
- [ ] Manual review completed by domain expert
- [ ] Documentation updated with pattern library

---

### Story 1.4: Critical Data Extraction (Rule-based)

**Story ID**: STORY-1.4
**Priority**: Critical (P0)
**Story Points**: 8

#### User Story

```
As the Ingestion Pipeline,
I want to extract critical numerical data (amounts, periods, KCD codes) with 100% accuracy,
So that I can prevent LLM hallucination on financial calculations.
```

#### Acceptance Criteria

**Given** a parsed clause text
**When** the CriticalDataExtractor processes the text
**Then** the system should:
- Extract all monetary amounts (1억원, 100만원, 5천만원) → normalized integers
- Extract all time periods (90일, 3개월, 1년) → normalized to days
- Extract all KCD disease codes (C77, I21-I25, E10-E14) → validated format
- Return original text spans for validation
- Achieve 100% accuracy (no false positives/negatives)

**Given** ambiguous text ("1억원 또는 2억원")
**When** extraction runs
**Then** the system should:
- Extract both values: [100000000, 200000000]
- Tag as "ambiguous" for downstream validation

#### Technical Tasks

- [ ] Implement `extract_amounts()` with regex patterns
  - [ ] Handle "억", "만", "천", "원" units
  - [ ] Handle comma separators (1,000만원)
  - [ ] Normalize to integer (원 units)
- [ ] Implement `extract_periods()` with normalization
  - [ ] Handle "일", "개월", "년" units
  - [ ] Convert all to days (1개월 → 30일, 1년 → 365일)
- [ ] Implement `extract_kcd_codes()` with validation
  - [ ] Match pattern: `[A-Z]\d{2}(?:-[A-Z]?\d{2})?`
  - [ ] Validate against KCD-8 reference database
- [ ] Add confidence scoring for each extraction
- [ ] Write unit tests (100+ test cases)
- [ ] Benchmark extraction accuracy (target: 100%)

#### Dependencies

- Story 1.3 completed (clause text available)
- KCD disease code reference database loaded

#### Technical Notes

**Regex Patterns**:

```python
AMOUNT_PATTERNS = [
    (r'(\d+(?:,\d+)?)\s*억\s*(\d+(?:,\d+)?)?\s*만?\s*원', 'okuok_man'),
    (r'(\d+(?:,\d+)?)\s*억\s*원', 'oku'),
    (r'(\d+(?:,\d+)?)\s*만\s*원', 'man'),
    (r'(\d+(?:,\d+)?)\s*천\s*원', 'sen'),
    (r'(\d+(?:,\d+)?)\s*원', 'won'),
]

PERIOD_PATTERNS = [
    (r'(\d+)\s*년', 365),
    (r'(\d+)\s*개월', 30),
    (r'(\d+)\s*주', 7),
    (r'(\d+)\s*일', 1),
]

KCD_PATTERN = r'\b([A-Z]\d{2}(?:-[A-Z]?\d{2})?)\b'
```

**Expected Output**:

```python
{
  "amounts": [
    {
      "value": 100000000,
      "original_text": "1억원",
      "position": (45, 50),
      "confidence": 1.0
    }
  ],
  "periods": [
    {
      "days": 90,
      "original_text": "90일",
      "position": (120, 124),
      "confidence": 1.0
    }
  ],
  "kcd_codes": [
    {
      "code": "C77",
      "original_text": "C77",
      "position": (200, 203),
      "is_valid": true
    }
  ]
}
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] 100% accuracy on validation test set (50+ samples)
- [ ] Unit tests passing (100+ test cases)
- [ ] Validation against manual annotations completed
- [ ] Edge cases documented
- [ ] Performance benchmarked (< 100ms per clause)

---

### Story 1.5: LLM Relationship Extraction with Validation

**Story ID**: STORY-1.5
**Priority**: Critical (P0)
**Story Points**: 13

#### User Story

```
As the Ingestion Pipeline,
I want to use LLM to extract relationships (COVERS, EXCLUDES, REQUIRES) from clauses,
So that I can build the knowledge graph automatically while maintaining accuracy.
```

#### Acceptance Criteria

**Given** a parsed clause with critical data extracted
**When** the RelationExtractionAgent processes the clause
**Then** the system should:
- Extract subject (Coverage name)
- Extract action (COVERS, EXCLUDES, REQUIRES, REDUCES)
- Extract object (Disease name/KCD code)
- Extract conditions (waiting_period, reduction_period, etc.)
- Return confidence score (0.0-1.0)
- Use critical_data to validate LLM outputs (override if mismatch)

**Given** LLM confidence < 0.7
**When** Solar Pro returns low-confidence result
**Then** the system should:
- Retry with GPT-4o (cascade strategy)
- Log both responses for comparison
- Use higher-confidence result

**Given** LLM extracts a number that differs from critical_data
**When** validation runs
**Then** the system should:
- Override LLM value with rule-based value
- Log the discrepancy for model improvement
- Flag for expert review

#### Technical Tasks

- [ ] Design relation extraction prompt template
- [ ] Implement RelationExtractionAgent class
  - [ ] Integrate Upstage Solar Pro API
  - [ ] Integrate OpenAI GPT-4o API (fallback)
  - [ ] Implement cascade logic (confidence-based)
- [ ] Implement validation logic
  - [ ] Cross-check LLM amounts vs. critical_data
  - [ ] Cross-check LLM periods vs. critical_data
  - [ ] Flag mismatches for review
- [ ] Implement JSON parsing with error handling
- [ ] Add retry logic for API failures
- [ ] Write unit tests with mock LLM responses
- [ ] Benchmark accuracy on 50 sample clauses

#### Dependencies

- Story 1.4 completed (critical_data available)
- Upstage Solar Pro API key
- OpenAI API key

#### Technical Notes

**Prompt Template**:

```python
RELATION_EXTRACTION_PROMPT = """
당신은 보험 약관 전문가입니다. 다음 약관 조항에서 관계를 추출하세요.

[약관 조항]
{clause_text}

[추출된 Critical Data]
금액: {amounts}
기간: {periods}
질병코드: {kcd_codes}

[지침]
1. 주체(Subject): 어떤 담보/상품?
2. 행위(Action): COVERS, EXCLUDES, REQUIRES, REDUCES 중 선택
3. 객체(Object): 어떤 질병/상황?
4. 조건(Conditions): 면책기간, 감액비율 등

**중요**: Critical Data가 제공되었다면 반드시 그 값을 사용하세요. 새로운 숫자를 생성하지 마세요.

[출력 형식 - JSON]
{{
  "relations": [
    {{
      "subject": "암진단특약",
      "action": "COVERS",
      "object": "일반암",
      "conditions": [
        {{"type": "waiting_period", "days": 90}},
        {{"type": "payment_amount", "amount": 100000000}}
      ],
      "confidence": 0.95,
      "reasoning": "제10조 ①항에서 명시"
    }}
  ]
}}
"""
```

**Validation Logic**:

```python
def validate_relation(relation, critical_data):
    """
    Validate LLM output against rule-based critical data
    """
    is_valid = True

    for condition in relation.get('conditions', []):
        if condition['type'] == 'waiting_period':
            llm_days = condition['days']
            extracted_periods = [p['days'] for p in critical_data.get('periods', [])]

            if llm_days not in extracted_periods:
                # Override with rule-based value
                if extracted_periods:
                    condition['days'] = extracted_periods[0]
                    is_valid = False
                    log_discrepancy(relation, 'waiting_period', llm_days, extracted_periods[0])

    return is_valid, relation
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Solar Pro + GPT-4o cascade implemented
- [ ] Validation logic tested (50+ samples)
- [ ] Accuracy > 85% on validation set
- [ ] API costs monitored and optimized
- [ ] Error handling comprehensive
- [ ] Documentation updated

---

### Story 1.6: Entity Linking & Ontology Mapping

**Story ID**: STORY-1.6
**Priority**: High (P1)
**Story Points**: 5

#### User Story

```
As the Ingestion Pipeline,
I want to standardize disease terms to a unified ontology,
So that graph queries can match synonyms (악성신생물 = 암 = Cancer).
```

#### Acceptance Criteria

**Given** extracted relations contain disease terms
**When** the EntityLinker processes the relations
**Then** the system should:
- Map Korean disease terms to standard English terms (악성신생물 → Cancer)
- Link disease terms to KCD codes (갑상선암 → C77)
- Handle synonyms (암 = 악성신생물 = Malignant Neoplasm)
- Preserve original terms for display purposes

**Given** a disease term not in the ontology
**When** entity linking runs
**Then** the system should:
- Flag the term as "unrecognized"
- Log for manual ontology expansion
- Continue processing (don't block pipeline)

#### Technical Tasks

- [ ] Design ontology data structure (JSON/YAML)
- [ ] Populate initial ontology (50+ common diseases)
  - [ ] Cancer types (C00-C99)
  - [ ] Cardiovascular diseases (I00-I99)
  - [ ] Endocrine diseases (E00-E99)
- [ ] Implement EntityLinker class
  - [ ] Fuzzy matching for typos
  - [ ] Synonym resolution
  - [ ] KCD code validation
- [ ] Add versioning for ontology updates
- [ ] Write unit tests for entity linking
- [ ] Document ontology expansion process

#### Dependencies

- Story 1.5 completed (relations extracted)
- KCD reference database

#### Technical Notes

**Ontology Structure** (YAML):

```yaml
diseases:
  cancer:
    standard: Cancer
    kcd_prefix: C
    synonyms:
      - 악성신생물
      - 암
      - Malignant Neoplasm
    subtypes:
      thyroid_cancer:
        standard: ThyroidCancer
        kcd_code: C77
        synonyms:
          - 갑상선암
          - 갑상선의 악성신생물
      liver_cancer:
        standard: LiverCancer
        kcd_code: C22
        synonyms:
          - 간암
          - 간의 악성신생물

  cardiovascular:
    standard: CardiovascularDisease
    kcd_prefix: I
    subtypes:
      cerebral_hemorrhage:
        standard: CerebralHemorrhage
        kcd_code: I61
        synonyms:
          - 뇌출혈
          - 뇌내출혈
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Ontology file created and versioned
- [ ] 90%+ entity linking success rate on test set
- [ ] Unrecognized terms logged for review
- [ ] Unit tests passing
- [ ] Documentation updated

---

### Story 1.7: Neo4j Graph Construction

**Story ID**: STORY-1.7
**Priority**: Critical (P0)
**Story Points**: 13

#### User Story

```
As the Ingestion Pipeline,
I want to create nodes and relationships in Neo4j from extracted data,
So that the knowledge graph is ready for GraphRAG queries.
```

#### Acceptance Criteria

**Given** standardized entities and relations are ready
**When** the GraphConstructor builds the graph
**Then** the system should:
- Create Product node with metadata
- Create Coverage nodes with properties
- Create Disease nodes with KCD codes
- Create Condition nodes with time/amount constraints
- Create Clause nodes with original text and page numbers
- Create relationships: COVERS, EXCLUDES, REQUIRES, DEFINED_IN, REFERENCES
- Generate vector embeddings for Clause.summary
- Store embeddings in Neo4j vector index

**Given** a node/relationship already exists
**When** graph construction runs
**Then** the system should:
- Use MERGE to avoid duplicates
- Update properties if values differ
- Log merge operations for audit

#### Technical Tasks

- [ ] Setup Neo4j connection (neo4j-driver)
- [ ] Implement GraphConstructor class
  - [ ] `create_product()` method
  - [ ] `create_coverage()` method
  - [ ] `create_disease()` method
  - [ ] `create_condition()` method
  - [ ] `create_clause()` method with provenance
  - [ ] `create_relationships()` method
- [ ] Implement vector embedding generation
  - [ ] Integrate OpenAI ada-002 or Upstage embeddings
  - [ ] Generate embeddings for clause summaries
  - [ ] Store in Clause.embedding property
- [ ] Create Neo4j vector index (clause_embeddings)
- [ ] Implement batch insertion for performance
- [ ] Add transaction handling (rollback on error)
- [ ] Write integration tests with test Neo4j instance
- [ ] Benchmark ingestion speed (target: < 5 min per policy)

#### Dependencies

- Story 1.6 completed (entities standardized)
- Neo4j database provisioned
- Neo4j vector index enabled

#### Technical Notes

**Cypher Queries**:

```cypher
// Create Product
MERGE (p:Product {id: $product_id})
ON CREATE SET
  p.name = $name,
  p.insurer = $insurer,
  p.launch_date = date($launch_date),
  p.created_at = datetime()
ON MATCH SET
  p.updated_at = datetime()
RETURN p

// Create Coverage with Disease relationship
MERGE (cov:Coverage {name: $coverage_name})
ON CREATE SET
  cov.id = randomUUID(),
  cov.type = $type,
  cov.created_at = datetime()

MERGE (dis:Disease {kcd_code: $kcd_code})
ON CREATE SET
  dis.id = randomUUID(),
  dis.name_ko = $disease_name,
  dis.created_at = datetime()

MERGE (cov)-[r:COVERS]->(dis)
SET r.confidence = $confidence,
    r.extraction_method = $method

// Link to source Clause (provenance)
WITH cov
MATCH (clause:Clause {id: $clause_id})
MERGE (cov)-[:DEFINED_IN]->(clause)
```

**Vector Index Creation**:

```cypher
CREATE VECTOR INDEX clause_embeddings
FOR (c:Clause) ON (c.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }
}
```

#### Performance Optimization

- Use batch transactions (100 nodes per transaction)
- Use UNWIND for bulk inserts
- Create indexes before bulk loading
- Monitor memory usage during ingestion

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Neo4j schema created (nodes, relationships, indexes)
- [ ] Vector index operational
- [ ] Integration tests passing
- [ ] Ingestion speed < 5 min per policy (50-page policy)
- [ ] Transaction handling tested (rollback scenarios)
- [ ] Monitoring dashboards configured
- [ ] Documentation updated

---

### Story 1.8: Ingestion Pipeline Orchestration (LangGraph)

**Story ID**: STORY-1.8
**Priority**: Critical (P0)
**Story Points**: 8

#### User Story

```
As the System,
I want to orchestrate all ingestion stages using LangGraph,
So that the pipeline runs reliably with proper error handling and state management.
```

#### Acceptance Criteria

**Given** a new ingestion job is triggered
**When** the LangGraph pipeline executes
**Then** the system should:
- Execute stages in order: OCR → Parse → Extract → LLM → Link → Graph
- Pass state between stages (IngestionState object)
- Handle errors gracefully (retry transient errors, fail on critical errors)
- Update job status in PostgreSQL at each stage
- Log progress and errors to CloudWatch/logs
- Complete successfully for valid policies

**Given** a stage fails (e.g., OCR API timeout)
**When** error occurs
**Then** the system should:
- Retry up to 3 times with exponential backoff
- If still failing, mark job as "failed"
- Preserve partial results for debugging
- Send alert to monitoring system

#### Technical Tasks

- [ ] Define IngestionState TypedDict with all stage data
- [ ] Implement LangGraph workflow
  - [ ] Add nodes for each stage (ocr, parse, extract, llm, link, graph)
  - [ ] Define edges between stages
  - [ ] Set entry point and end point
- [ ] Implement state persistence (PostgreSQL)
- [ ] Add error handling and retry logic
- [ ] Implement progress tracking (0-100%)
- [ ] Add logging at each stage
- [ ] Create monitoring dashboards
- [ ] Write integration tests (end-to-end)
- [ ] Test failure scenarios

#### Dependencies

- All previous stories (1.1-1.7) completed
- LangGraph library installed

#### Technical Notes

**LangGraph Workflow**:

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class IngestionState(TypedDict):
    job_id: str
    file_path: str
    metadata: dict

    # Stage outputs
    ocr_text: str
    parsed_chunks: list
    critical_data: list
    extracted_relations: list
    standardized_entities: list
    neo4j_results: dict

    # Status tracking
    current_stage: str
    progress: int
    errors: list
    warnings: list

def create_ingestion_pipeline():
    workflow = StateGraph(IngestionState)

    # Add nodes
    workflow.add_node("ocr", ocr_agent.process)
    workflow.add_node("parse", parser.parse)
    workflow.add_node("extract_critical", extractor.extract)
    workflow.add_node("extract_relations", llm_agent.extract)
    workflow.add_node("link_entities", linker.link)
    workflow.add_node("construct_graph", graph_constructor.construct)
    workflow.add_node("validate", validator.validate)

    # Define edges
    workflow.add_edge("ocr", "parse")
    workflow.add_edge("parse", "extract_critical")
    workflow.add_edge("extract_critical", "extract_relations")
    workflow.add_edge("extract_relations", "link_entities")
    workflow.add_edge("link_entities", "construct_graph")
    workflow.add_edge("construct_graph", "validate")
    workflow.add_edge("validate", END)

    workflow.set_entry_point("ocr")

    return workflow.compile()
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] LangGraph pipeline implemented
- [ ] End-to-end tests passing (10 sample policies)
- [ ] Error handling tested (API failures, timeouts)
- [ ] State persistence working
- [ ] Monitoring alerts configured
- [ ] Performance benchmarked
- [ ] Documentation updated

---

### Story 1.9: Validation & Quality Assurance

**Story ID**: STORY-1.9
**Priority**: High (P1)
**Story Points**: 5

#### User Story

```
As a QA Engineer,
I want automated validation of ingested policies,
So that I can catch errors before they impact users.
```

#### Acceptance Criteria

**Given** a policy is fully ingested
**When** the validation stage runs
**Then** the system should check:
- All articles have at least 1 paragraph
- All relationships have source Clause references
- All amounts/periods match critical_data (no LLM overrides)
- All KCD codes are valid (exist in reference database)
- No orphaned nodes (nodes without relationships)
- Graph is connected (Product → Coverage → Disease paths exist)

**Given** validation fails
**When** errors are detected
**Then** the system should:
- Mark job as "needs_review"
- Generate detailed error report
- Flag specific clauses/relationships for manual review
- Not allow the policy to be used in queries

#### Technical Tasks

- [ ] Implement ValidationAgent class
  - [ ] `validate_hierarchy()` - check clause tree structure
  - [ ] `validate_relationships()` - check provenance links
  - [ ] `validate_critical_data()` - verify accuracy
  - [ ] `validate_graph_connectivity()` - check graph completeness
- [ ] Create validation report template
- [ ] Implement manual review queue UI (Phase 2)
- [ ] Write unit tests for validators
- [ ] Test on 10 sample policies

#### Dependencies

- Story 1.8 completed (full pipeline operational)

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Validation tests implemented
- [ ] Validation report generated for all test policies
- [ ] Manual review process documented
- [ ] Integration with pipeline tested

---

## Epic Dependencies

```
Story 1.0 (Metadata Crawler & Dashboard)
    ↓
    ├─→ Story 1.1 (Upload & Job Management)
    │       ↓
    └─────→ Story 1.2 (OCR)
                ↓
            Story 1.3 (Parse)
                ↓
            Story 1.4 (Extract) ←─┐
                ↓                  │
            Story 1.5 (LLM) ──────┘ (validation)
                ↓
            Story 1.6 (Link)
                ↓
            Story 1.7 (Graph)
                ↓
            Story 1.8 (Orchestration)
                ↓
            Story 1.9 (Validation)
```

---

## Technical Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Legal issues from crawling** | Critical | Medium | Human-in-the-Loop metadata approach; NO auto PDF downloads; robots.txt compliance; crawl rate limiting |
| **Crawler blocked by insurers** | High | Medium | Rotate user agents; use delays; switch to manual upload if blocked |
| **OCR accuracy < 95%** | Critical | Medium | Use Upstage Document Parse (best Korean OCR); manual review for low confidence |
| **LLM hallucination** | Critical | High | 4-layer validation; rule-based override for critical data |
| **Parsing fails on complex layouts** | High | Medium | Graceful degradation; flag for manual review; iteratively improve patterns |
| **Neo4j performance** | Medium | Low | Batch inserts; proper indexing; monitor query performance |
| **API costs exceed budget** | Medium | Medium | Cache embeddings; use Solar Pro over GPT-4o; selective learning via curation |

---

## Sprint Recommendations

### Sprint 0 (2 weeks) - NEW: Human-in-the-Loop Foundation
- Story 1.0 (Metadata Crawler & Admin Dashboard)
  - Backend: policy_metadata table, crawler implementation
  - Frontend: admin dashboard UI
  - Integration: crawler → DB → dashboard → queue

### Sprint 1 (2 weeks)
- Story 1.0 (Complete & Test with real insurers)
- Story 1.1 (Upload & Job Management - integrate with metadata queue)
- Story 1.2 (OCR) - Start

### Sprint 2 (2 weeks)
- Story 1.2 (OCR) - Complete
- Story 1.3 (Parsing)
- Story 1.4 (Critical Data Extraction) - Start

### Sprint 3 (2 weeks)
- Story 1.4 (Critical Data Extraction) - Complete
- Story 1.5 (LLM Extraction)
- Story 1.6 (Entity Linking)

### Sprint 4 (2 weeks)
- Story 1.7 (Graph Construction)
- Story 1.8 (Orchestration)
- Story 1.9 (Validation)

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Metadata Discovery Rate** | 100+ policies/week | Crawler logs |
| **Legal Compliance** | 0 robots.txt violations | Crawler audit logs |
| **Curation Efficiency** | Admin can review 50+ policies in < 10 min | User testing |
| **Queue-to-Complete Time** | < 10 min/policy | End-to-end pipeline monitoring |
| **Ingestion Accuracy** | > 95% | Manual validation on 10 test policies |
| **Ingestion Speed** | < 5 min/policy (processing time) | Automated benchmarking |
| **API Cost** | < $50/policy | CloudWatch cost monitoring |
| **Critical Data Accuracy** | 100% | Automated validation tests |
| **LLM Confidence** | > 0.85 avg | Logged in database |

---

**Epic Owner**: Backend Tech Lead
**Stakeholders**: Product Manager, QA Engineer, DevOps
**Next Review**: After Sprint 2 completion
