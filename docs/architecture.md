# Architecture Document: InsureGraph Pro

**Project**: InsureGraph Pro
**Document Type**: Technical Architecture (BMAD Method)
**Version**: 1.0
**Date**: 2025-11-25
**Author**: Architect
**Status**: Draft (Pending Review)

---

## 📋 Executive Summary

This document defines the technical architecture for InsureGraph Pro, a GraphRAG-based insurance policy analysis platform. The architecture is designed to support:

- **High Accuracy**: 4-layer defense against LLM hallucination
- **Complex Reasoning**: Multi-hop graph traversal for policy comparison
- **Regulatory Compliance**: Financial sandbox requirements & data privacy
- **Scalability**: Support for 500+ policies and 10,000+ FP users in Phase 3

**Key Architectural Decisions**:
- Hybrid approach: Rule-based + LLM for critical data accuracy
- Neo4j as unified graph + vector database (Phase 1)
- FastAPI + LangGraph for multi-agent orchestration
- AWS EKS for logical network separation compliance

---

## 🏗️ System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
├─────────────────────────────────────────────────────────────────┤
│  Web App (Next.js)  │  Mobile PWA  │  Kakao Integration (Phase2)│
└───────────────┬─────────────────────────────────────────────────┘
                │ HTTPS/JWT
┌───────────────▼─────────────────────────────────────────────────┐
│                     API Gateway (Kong)                           │
│  - Authentication  - Rate Limiting  - Request Routing            │
└───────────────┬─────────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────────┐
│                    Application Layer (FastAPI)                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Ingestion API  │  │   Query API     │  │ Compliance API  │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│           │                    │                     │          │
│  ┌────────▼────────────────────▼─────────────────────▼────────┐ │
│  │           LangGraph Multi-Agent Orchestrator               │ │
│  │  Parser → Extractor → Validator → Reasoner → Formatter    │ │
│  └────────────────────────────┬───────────────────────────────┘ │
└───────────────────────────────┼─────────────────────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        │                                               │
┌───────▼────────┐                             ┌───────▼────────┐
│   Data Layer   │                             │   LLM Layer    │
├────────────────┤                             ├────────────────┤
│  Neo4j Graph   │                             │ Upstage Solar  │
│  + Vector Index│                             │    GPT-4o      │
│                │                             │   (Fallback)   │
│  PostgreSQL    │                             └────────────────┘
│  (Metadata)    │
│                │
│  S3 (Files)    │
└────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| **Web Client** | FP workspace, graph visualization | Next.js 14, Cytoscape.js |
| **API Gateway** | Auth, rate limiting, routing | Kong Gateway |
| **Ingestion Service** | PDF parsing, entity extraction | FastAPI, LangGraph |
| **Query Service** | GraphRAG query execution | FastAPI, LangGraph |
| **Graph Database** | Knowledge graph storage & traversal | Neo4j Enterprise |
| **Vector Search** | Semantic search for clauses | Neo4j Vector Index |
| **Metadata DB** | User, session, audit logs | PostgreSQL 15 |
| **Object Storage** | PDF files, generated reports | AWS S3 |
| **LLM Orchestration** | Model selection, fallback logic | LangChain + custom |

---

## 🔌 API Architecture

### API Design Principles

1. **RESTful** with resource-based URLs
2. **JSON API** standard for error handling
3. **Versioning**: `/api/v1/...` for backward compatibility
4. **Authentication**: JWT with refresh token
5. **Rate Limiting**: Per-user tier limits

### Core API Endpoints

#### 1. Ingestion API

**POST /api/v1/policies/ingest**

Upload and process insurance policy PDF.

```json
Request:
POST /api/v1/policies/ingest
Content-Type: multipart/form-data

{
  "file": <binary>,
  "metadata": {
    "insurer": "Samsung Life",
    "product_name": "Cancer Insurance Premium",
    "launch_date": "2020-03-15",
    "product_code": "SL-CI-001"
  }
}

Response (202 Accepted):
{
  "job_id": "job_12345",
  "status": "processing",
  "estimated_time": 180,  // seconds
  "webhook_url": "https://api.insuregraph.com/webhooks/job_12345"
}
```

**GET /api/v1/policies/ingest/{job_id}/status**

Check ingestion job status.

```json
Response:
{
  "job_id": "job_12345",
  "status": "completed",  // processing, completed, failed
  "progress": 100,
  "results": {
    "product_id": "prod_67890",
    "nodes_created": 1247,
    "edges_created": 3521,
    "clauses_parsed": 89,
    "errors": []
  },
  "created_at": "2025-11-25T10:30:00Z",
  "completed_at": "2025-11-25T10:33:15Z"
}
```

#### 2. Query API

**POST /api/v1/analysis/query**

Execute natural language query against knowledge graph.

```json
Request:
{
  "query": "갑상선암 보장돼요?",
  "context": {
    "product_ids": ["prod_67890"],  // optional: specific products
    "customer_profile": {            // optional: for personalized analysis
      "age": 35,
      "gender": "F",
      "existing_policies": []
    }
  },
  "options": {
    "include_reasoning_path": true,
    "max_hops": 3,
    "confidence_threshold": 0.7
  }
}

Response:
{
  "query_id": "qry_98765",
  "answer": {
    "summary": "갑상선암(C77)은 담보에 포함되나, 90일 면책기간이 적용됩니다.",
    "confidence": 0.92,
    "status": "high_confidence",  // high_confidence, medium, needs_review
    "details": [
      {
        "product": "Cancer Insurance Premium",
        "coverage": "암진단특약",
        "is_covered": true,
        "conditions": [
          {
            "type": "waiting_period",
            "days": 90,
            "description": "계약일로부터 90일 이후 발생한 갑상선암은 보장"
          }
        ],
        "payment_amount": 100000000,
        "exclusions": []
      }
    ]
  },
  "reasoning_path": {
    "graph_visualization": {
      "nodes": [...],
      "edges": [...]
    },
    "cypher_query": "MATCH (p:Product)...",
    "execution_time_ms": 342
  },
  "sources": [
    {
      "clause_id": "clause_123",
      "article": "제10조",
      "paragraph": "①항",
      "page": 15,
      "excerpt": "다만, 갑상선의 악성신생물(C77)은 계약일로부터 90일 이후..."
    }
  ],
  "warnings": [],
  "disclaimer": "본 분석은 참고용이며, 최종 판단은 보험사가 합니다."
}
```

**POST /api/v1/analysis/gap-analysis**

Analyze customer's coverage gaps.

```json
Request:
{
  "customer_id": "cust_111",
  "current_policies": [
    {
      "product_id": "prod_67890",
      "purchase_date": "2015-06-01",
      "coverages": [...]
    }
  ],
  "target_profile": {
    "age": 35,
    "occupation": "office_worker",
    "health_concerns": ["cancer", "cardiovascular"]
  }
}

Response:
{
  "analysis_id": "gap_222",
  "gaps": [
    {
      "type": "coverage_gap",
      "severity": "high",
      "description": "갑상선 림프절 전이암이 일반암으로 분류되지 않는 2015년 약관",
      "impact": {
        "potential_loss": 50000000,
        "probability": "medium"
      },
      "recommendations": [
        {
          "action": "upgrade_policy",
          "suggested_product_id": "prod_99999",
          "reasoning": "2020년 이후 약관은 림프절 전이를 일반암으로 인정"
        }
      ]
    }
  ],
  "opportunities": [
    {
      "type": "claim_opportunity",
      "description": "기존 보험에서 청구 가능한 항목 발견",
      "estimated_amount": 3000000,
      "required_actions": ["진단서 제출"]
    }
  ],
  "score": {
    "overall": 65,  // 0-100
    "cancer": 70,
    "cardiovascular": 80,
    "disability": 45
  }
}
```

**POST /api/v1/analysis/compare**

Compare multiple insurance products.

```json
Request:
{
  "product_ids": ["prod_67890", "prod_88888"],
  "comparison_criteria": [
    "coverage_overlap",
    "cost_benefit",
    "claim_conditions"
  ]
}

Response:
{
  "comparison_id": "cmp_333",
  "products": [
    {
      "product_id": "prod_67890",
      "name": "Samsung Cancer Insurance",
      "strengths": ["광범위한 소액암 보장"],
      "weaknesses": ["비례보상 50%"]
    },
    {
      "product_id": "prod_88888",
      "name": "Hanwha CI Insurance",
      "strengths": ["비례보상 100%"],
      "weaknesses": ["갑상선암 제외"]
    }
  ],
  "overlaps": [
    {
      "disease": "갑상선암(C77)",
      "overlap_type": "proportional",
      "combined_payout": 75000000,
      "individual_payouts": {
        "prod_67890": 50000000,
        "prod_88888": 25000000
      }
    }
  ],
  "recommendations": {
    "best_for_customer": "prod_67890",
    "reasoning": "고객 프로필 상 소액암 리스크가 높음"
  }
}
```

#### 3. Compliance & Audit API

**POST /api/v1/compliance/validate-script**

Validate sales script for compliance.

```json
Request:
{
  "script": "이 상품은 갑상선암을 100% 보장합니다!",
  "context": {
    "product_id": "prod_67890",
    "fp_id": "fp_123"
  }
}

Response:
{
  "validation_id": "val_444",
  "is_compliant": false,
  "violations": [
    {
      "type": "forbidden_phrase",
      "severity": "critical",
      "found_phrase": "100% 보장합니다",
      "reason": "절대적 단언 표현 금지",
      "suggestion": "'약관에 따라 보장될 수 있습니다'로 수정"
    },
    {
      "type": "missing_disclaimer",
      "severity": "high",
      "required_phrase": "면책기간 90일",
      "reason": "필수 설명 의무 누락"
    }
  ],
  "corrected_script": "이 상품은 약관 제10조에 따라 갑상선암을 보장하며, 계약일로부터 90일 면책기간이 적용됩니다. 자세한 사항은 약관을 확인하시기 바랍니다.",
  "risk_score": 85  // 0-100 (higher = more risky)
}
```

**GET /api/v1/audit/logs**

Retrieve audit logs for compliance reporting.

```json
Request:
GET /api/v1/audit/logs?start_date=2025-11-01&end_date=2025-11-30&fp_id=fp_123

Response:
{
  "logs": [
    {
      "log_id": "log_555",
      "timestamp": "2025-11-25T10:45:23Z",
      "fp_id": "fp_123",
      "action": "query_executed",
      "details": {
        "query": "갑상선암 보장돼요?",
        "products_accessed": ["prod_67890"],
        "customer_id": "cust_111"
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0..."
    }
  ],
  "pagination": {
    "total": 1247,
    "page": 1,
    "per_page": 50
  }
}
```

#### 4. MyData Integration API (Phase 2)

**POST /api/v1/mydata/import**

Import customer's existing policies via MyData.

```json
Request:
{
  "customer_id": "cust_111",
  "mydata_token": "eyJhbGci...",  // OAuth token from MyData provider
  "consent_id": "consent_666"
}

Response:
{
  "import_id": "imp_777",
  "status": "completed",
  "policies_imported": 3,
  "policies": [
    {
      "external_id": "md_policy_001",
      "insurer": "Samsung Life",
      "product_name": "Cancer Insurance",
      "start_date": "2015-06-01",
      "matched_product_id": "prod_67890",  // matched to our knowledge base
      "confidence": 0.95
    }
  ],
  "warnings": [
    {
      "policy": "md_policy_002",
      "issue": "Product not found in knowledge base",
      "action": "Manual review required"
    }
  ]
}
```

### API Authentication & Authorization

**JWT Token Structure**:

```json
{
  "sub": "fp_123",
  "role": "financial_planner",
  "ga_id": "ga_456",
  "tier": "pro",  // free, pro, enterprise
  "permissions": [
    "query:execute",
    "policies:read",
    "customers:manage"
  ],
  "rate_limits": {
    "queries_per_day": 1000,
    "ingestion_per_month": 50
  },
  "iat": 1700900000,
  "exp": 1700986400
}
```

**Role-Based Access Control (RBAC)**:

| Role | Permissions |
|------|-------------|
| `financial_planner` | Query execution, customer management, basic analytics |
| `ga_manager` | All FP permissions + team analytics, compliance monitoring |
| `admin` | All permissions + ingestion, system configuration |
| `end_user` (Phase 3) | Self-service policy analysis (read-only) |

---

## 🗄️ Database Architecture

### Neo4j Graph Schema (Detailed)

#### Node Labels & Properties

```cypher
// ============================================
// Core Business Entities
// ============================================

(:Product {
  id: STRING (PRIMARY),
  name: STRING,
  insurer: STRING,
  product_code: STRING,
  launch_date: DATE,
  version: STRING,
  status: STRING,  // 'active', 'deprecated', 'replaced'
  pdf_url: STRING,
  created_at: DATETIME,
  updated_at: DATETIME
})
CREATE INDEX product_id FOR (p:Product) ON (p.id)
CREATE INDEX product_insurer FOR (p:Product) ON (p.insurer)

(:Coverage {
  id: STRING (PRIMARY),
  name: STRING,
  code: STRING,
  type: STRING,  // 'cancer', 'cardiovascular', 'disability', 'death'
  category: STRING,  // 'life', 'health', 'annuity'
  base_amount: INTEGER,
  max_amount: INTEGER,
  min_amount: INTEGER,
  payment_type: STRING,  // 'lump_sum', 'installment', 'proportional'
  created_at: DATETIME
})
CREATE INDEX coverage_id FOR (c:Coverage) ON (c.id)
CREATE INDEX coverage_type FOR (c:Coverage) ON (c.type)

(:Disease {
  id: STRING (PRIMARY),
  kcd_code: STRING,  // Korean Classification of Disease
  kcd_version: STRING,  // 'KCD-8', 'KCD-9'
  name_ko: STRING,
  name_en: STRING,
  severity_level: STRING,  // 'minor', 'general', 'critical'
  category: STRING,  // 'cancer', 'cardiovascular', 'neurological'
  synonyms: LIST<STRING>,
  created_at: DATETIME
})
CREATE INDEX disease_kcd FOR (d:Disease) ON (d.kcd_code)
CREATE FULLTEXT INDEX disease_search FOR (d:Disease) ON EACH [d.name_ko, d.name_en, d.synonyms]

(:Condition {
  id: STRING (PRIMARY),
  type: STRING,  // 'waiting_period', 'reduction_period', 'age_limit', 'diagnosis_requirement'
  days: INTEGER,
  percentage: FLOAT,
  min_age: INTEGER,
  max_age: INTEGER,
  description: STRING,
  trigger_event: STRING
})

(:Clause {
  id: STRING (PRIMARY),
  product_id: STRING (FK),
  article_num: STRING,  // "제10조"
  paragraph: STRING,    // "①항"
  subclause: STRING,    // "가목"
  raw_text: STRING,
  summary: STRING,  // LLM-generated
  page_num: INTEGER,
  parent_clause_id: STRING,  // For hierarchical structure
  created_at: DATETIME
})
CREATE INDEX clause_product FOR (c:Clause) ON (c.product_id)
CREATE FULLTEXT INDEX clause_text FOR (c:Clause) ON EACH [c.raw_text, c.summary]

(:Exclusion {
  id: STRING (PRIMARY),
  type: STRING,  // 'disease', 'activity', 'pre_existing', 'intentional'
  description: STRING,
  priority: INTEGER,  // For conflict resolution
  effective_date: DATE,
  expiry_date: DATE
})

(:PaymentRule {
  id: STRING (PRIMARY),
  condition_type: STRING,  // 'duplicate_coverage', 'multiple_claims'
  formula: STRING,  // "MIN(actual_cost, coverage_amount)"
  proportional_ratio: FLOAT,
  max_payout: INTEGER,
  description: STRING
})

// ============================================
// Metadata & Audit Entities
// ============================================

(:Entity {
  id: STRING (PRIMARY),
  text: STRING,
  standard_form: STRING,  // Ontology-mapped term
  entity_type: STRING,  // 'disease', 'treatment', 'condition'
  confidence: FLOAT,
  source_clause_id: STRING
})

// ============================================
// Vector Embeddings (Neo4j Vector Index)
// ============================================

// Embeddings stored as node properties, indexed by vector index
ALTER TABLE Clause ADD PROPERTY embedding VECTOR(1536);  // For OpenAI ada-002
CREATE VECTOR INDEX clause_embeddings FOR (c:Clause) ON (c.embedding)
  OPTIONS {indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }}
```

#### Relationship Types & Properties

```cypher
// ============================================
// Core Relationships
// ============================================

(Product)-[:HAS_COVERAGE {
  order: INTEGER,
  is_optional: BOOLEAN,
  premium_rate: FLOAT
}]->(Coverage)

(Coverage)-[:COVERS {
  confidence: FLOAT,  // LLM extraction confidence
  extraction_method: STRING,  // 'rule_based', 'llm_extracted'
  verified_by_expert: BOOLEAN,
  verified_date: DATE
}]->(Disease)

(Coverage)-[:EXCLUDES {
  priority: INTEGER,
  override_covers: BOOLEAN,  // True if exclusion overrides coverage
  effective_period: STRING
}]->(Disease)

(Coverage)-[:REQUIRES {
  order: INTEGER,  // Sequence of conditions
  is_mandatory: BOOLEAN
}]->(Condition)

(Coverage)-[:APPLIES_RULE]->(PaymentRule)

// ============================================
// Conflict & Overlap Detection (Key Differentiator)
// ============================================

(Coverage)-[:CONFLICTS_WITH {
  conflict_type: STRING,  // 'duplicate', 'proportional', 'exclusive'
  overlap_percentage: FLOAT,
  resolution_rule: STRING,
  detected_date: DATE
}]->(Coverage)

(Product)-[:COMPETES_WITH {
  similarity_score: FLOAT,
  comparison_criteria: LIST<STRING>
}]->(Product)

// ============================================
// Provenance & Traceability (Critical for Trust)
// ============================================

(Coverage)-[:DEFINED_IN {
  is_primary_definition: BOOLEAN
}]->(Clause)

(Condition)-[:REFERENCES]->(Clause)

(Exclusion)-[:BASED_ON]->(Clause)

(Disease)-[:MENTIONED_IN]->(Clause)

// ============================================
// Temporal Relationships (Version Control)
// ============================================

(Product)-[:REPLACES {
  replaced_date: DATE,
  reason: STRING,  // 'regulation_change', 'product_update'
  migration_path: STRING
}]->(Product)

(Clause)-[:AMENDED_BY {
  amendment_date: DATE,
  change_summary: STRING
}]->(Clause)

// ============================================
// Reasoning & Inference Relationships
// ============================================

(Disease)-[:SUBTYPE_OF]->(Disease)  // e.g., 갑상선 림프절 전이 -> 갑상선암

(Condition)-[:DEPENDS_ON]->(Condition)  // Sequential conditions

(Clause)-[:RELATED_TO {
  relation_type: STRING,  // 'exception', 'clarification', 'cross_reference'
  strength: FLOAT
}]->(Clause)
```

### PostgreSQL Metadata Schema

```sql
-- ============================================
-- User Management
-- ============================================

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,  -- 'fp', 'ga_manager', 'admin', 'end_user'
  tier VARCHAR(50) NOT NULL DEFAULT 'free',
  ga_id UUID REFERENCES gas(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  last_login TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_ga_id ON users(ga_id);

-- ============================================
-- GA (General Agency) Organizations
-- ============================================

CREATE TABLE gas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  business_number VARCHAR(50) UNIQUE,
  contract_type VARCHAR(50),  -- 'free', 'pro', 'enterprise'
  max_fps INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  contract_start DATE,
  contract_end DATE
);

-- ============================================
-- Customers (PII Masked)
-- ============================================

CREATE TABLE customers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fp_id UUID REFERENCES users(id),
  name_encrypted BYTEA,  -- AES-256 encrypted
  birth_year INTEGER,  -- Only year, not full DOB
  gender CHAR(1),
  phone_hash VARCHAR(64),  -- SHA-256 hashed
  consent_date TIMESTAMP,
  consent_id VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_customers_fp_id ON customers(fp_id);

-- ============================================
-- Query History & Analytics
-- ============================================

CREATE TABLE query_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  customer_id UUID REFERENCES customers(id),
  query_text TEXT,
  query_type VARCHAR(50),  -- 'simple', 'comparison', 'gap_analysis'
  graph_query TEXT,  -- Cypher query executed
  result_confidence FLOAT,
  execution_time_ms INTEGER,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_query_logs_user_id ON query_logs(user_id);
CREATE INDEX idx_query_logs_created_at ON query_logs(created_at);

-- ============================================
-- Ingestion Jobs
-- ============================================

CREATE TABLE ingestion_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  file_name VARCHAR(255),
  file_size BIGINT,
  file_url TEXT,  -- S3 URL
  status VARCHAR(50),  -- 'pending', 'processing', 'completed', 'failed'
  progress INTEGER DEFAULT 0,
  error_message TEXT,
  metadata JSONB,
  results JSONB,  -- {nodes_created, edges_created, etc.}
  created_at TIMESTAMP DEFAULT NOW(),
  started_at TIMESTAMP,
  completed_at TIMESTAMP
);

CREATE INDEX idx_ingestion_jobs_user_id ON ingestion_jobs(user_id);
CREATE INDEX idx_ingestion_jobs_status ON ingestion_jobs(status);

-- ============================================
-- Expert Review Queue (Phase 1 MVP)
-- ============================================

CREATE TABLE expert_reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_log_id UUID REFERENCES query_logs(id),
  llm_answer TEXT,
  graph_paths JSONB,
  confidence FLOAT,
  status VARCHAR(50),  -- 'pending', 'approved', 'rejected'
  reviewer_id UUID REFERENCES users(id),
  review_notes TEXT,
  correct_answer TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  reviewed_at TIMESTAMP
);

CREATE INDEX idx_expert_reviews_status ON expert_reviews(status);

-- ============================================
-- Audit Logs (Compliance)
-- ============================================

CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  action VARCHAR(100),
  resource_type VARCHAR(50),
  resource_id VARCHAR(255),
  details JSONB,
  ip_address INET,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
```

---

## 🔄 Data Ingestion Pipeline Architecture

### Pipeline Stages (LangGraph Orchestration)

```python
# LangGraph State Definition
from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END

class IngestionState(TypedDict):
    job_id: str
    file_path: str
    metadata: dict

    # Stage 1: OCR
    ocr_text: str
    ocr_confidence: float

    # Stage 2: Structure Parsing
    parsed_chunks: List[dict]
    document_hierarchy: dict

    # Stage 3: Critical Data Extraction (Rule-based)
    critical_data: List[dict]

    # Stage 4: Relationship Extraction (LLM)
    extracted_relations: List[dict]

    # Stage 5: Entity Linking
    standardized_entities: List[dict]

    # Stage 6: Graph Construction
    neo4j_nodes: List[dict]
    neo4j_edges: List[dict]

    # Stage 7: Validation
    validation_results: dict
    errors: List[str]
    warnings: List[str]
```

### Stage 1: OCR & Document Preprocessing

```python
class OCRAgent:
    """
    Upstage Document Parse integration
    """
    def __init__(self):
        self.client = UpstageDocumentParse(api_key=UPSTAGE_API_KEY)

    async def process(self, state: IngestionState) -> IngestionState:
        """
        Extract text, tables, and structure from PDF
        """
        result = await self.client.parse(
            file_path=state['file_path'],
            options={
                'ocr_lang': 'ko',
                'extract_tables': True,
                'extract_images': True,
                'layout_analysis': True
            }
        )

        state['ocr_text'] = result.text
        state['ocr_confidence'] = result.confidence
        state['parsed_chunks'] = result.chunks  # Pre-chunked by layout

        return state
```

### Stage 2: Legal Structure Parsing (Rule-based)

```python
class LegalStructureParser:
    """
    Parse Korean legal document structure
    """
    PATTERNS = {
        'article': r'제(\d+)조\s*\[([^\]]+)\]',  # 제10조 [보험금 지급]
        'paragraph': r'[①②③④⑤⑥⑦⑧⑨⑩]',
        'subclause': r'(\d+)\.\s',
        'exception': r'(다만|단서|제외하고)',
    }

    def parse(self, chunks: List[dict]) -> dict:
        """
        Build hierarchical tree of clauses
        """
        hierarchy = {
            'articles': []
        }

        current_article = None
        current_paragraph = None

        for chunk in chunks:
            text = chunk['text']

            # Match article
            if match := re.search(self.PATTERNS['article'], text):
                article_num = match.group(1)
                article_title = match.group(2)

                current_article = {
                    'article_num': f'제{article_num}조',
                    'title': article_title,
                    'paragraphs': [],
                    'page': chunk['page'],
                    'bbox': chunk['bbox']
                }
                hierarchy['articles'].append(current_article)

            # Match paragraph
            elif match := re.search(self.PATTERNS['paragraph'], text):
                if current_article:
                    paragraph = {
                        'paragraph_num': match.group(0),
                        'text': text[match.end():].strip(),
                        'subclauses': []
                    }
                    current_article['paragraphs'].append(paragraph)
                    current_paragraph = paragraph

        return hierarchy
```

### Stage 3: Critical Data Extraction (Rule-based)

```python
class CriticalDataExtractor:
    """
    Extract critical data with 100% accuracy requirement
    """
    def extract_amounts(self, text: str) -> List[int]:
        """
        Extract monetary amounts: 1억원, 100만원 -> normalized integers
        """
        patterns = [
            (r'(\d+(?:,\d+)?)\s*억\s*원', 100_000_000),
            (r'(\d+(?:,\d+)?)\s*만\s*원', 10_000),
            (r'(\d+(?:,\d+)?)\s*천\s*원', 1_000),
            (r'(\d+(?:,\d+)?)\s*원', 1),
        ]

        amounts = []
        for pattern, multiplier in patterns:
            for match in re.finditer(pattern, text):
                num_str = match.group(1).replace(',', '')
                amount = int(num_str) * multiplier
                amounts.append({
                    'value': amount,
                    'original_text': match.group(0),
                    'position': match.span()
                })

        return amounts

    def extract_periods(self, text: str) -> List[dict]:
        """
        Extract time periods: 90일, 3개월 -> normalized to days
        """
        patterns = [
            (r'(\d+)\s*일', 1),
            (r'(\d+)\s*개월', 30),  # Approximate
            (r'(\d+)\s*년', 365),
        ]

        periods = []
        for pattern, multiplier in patterns:
            for match in re.finditer(pattern, text):
                num = int(match.group(1))
                days = num * multiplier
                periods.append({
                    'days': days,
                    'original_text': match.group(0),
                    'position': match.span()
                })

        return periods

    def extract_kcd_codes(self, text: str) -> List[str]:
        """
        Extract KCD disease codes: C77, I21-I25
        """
        pattern = r'\b([A-Z]\d{2}(?:-[A-Z]?\d{2})?)\b'
        return re.findall(pattern, text)
```

### Stage 4: Relationship Extraction (LLM)

```python
class RelationExtractionAgent:
    """
    LLM-based relationship extraction with validation
    """
    PROMPT_TEMPLATE = """
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

[중요] Critical Data가 제공되었다면 반드시 그 값을 사용하세요. 새로운 숫자를 생성하지 마세요.

[출력 형식 - JSON]
{{
  "relations": [
    {{
      "subject": "암진단특약",
      "action": "EXCLUDES",
      "object": "갑상선암(C77)",
      "conditions": [
        {{"type": "waiting_period", "days": 90}}
      ],
      "confidence": 0.95,
      "reasoning": "제10조 ①항에서 명시"
    }}
  ]
}}
"""

    async def extract(self, chunk: dict, critical_data: dict) -> List[dict]:
        """
        Extract relationships with LLM + validation
        """
        prompt = self.PROMPT_TEMPLATE.format(
            clause_text=chunk['text'],
            amounts=critical_data.get('amounts', []),
            periods=critical_data.get('periods', []),
            kcd_codes=critical_data.get('kcd_codes', [])
        )

        # Try Solar Pro first (cost-effective)
        response = await self.solar_llm.generate(prompt)
        relations = json.loads(response)

        # Validate: Check if LLM's numbers match critical_data
        validated_relations = []
        for rel in relations['relations']:
            is_valid, corrected_rel = self.validate_relation(rel, critical_data)

            if not is_valid:
                # Low confidence, retry with GPT-4o
                if rel['confidence'] < 0.7:
                    gpt4_response = await self.gpt4_llm.generate(prompt)
                    rel = json.loads(gpt4_response)['relations'][0]

            validated_relations.append(corrected_rel)

        return validated_relations

    def validate_relation(self, relation: dict, critical_data: dict) -> tuple:
        """
        Validate LLM output against rule-based critical data
        """
        is_valid = True

        # Check if LLM's period matches critical_data
        for condition in relation.get('conditions', []):
            if condition['type'] == 'waiting_period':
                llm_days = condition['days']

                # Find matching period in critical_data
                extracted_periods = [p['days'] for p in critical_data.get('periods', [])]

                if llm_days not in extracted_periods:
                    # Override with rule-based value
                    if extracted_periods:
                        condition['days'] = extracted_periods[0]
                        is_valid = False

        return is_valid, relation
```

### Stage 5: Entity Linking & Ontology Mapping

```python
class EntityLinker:
    """
    Standardize entities to ontology
    """
    ONTOLOGY = {
        'diseases': {
            '악성신생물': {'standard': 'Cancer', 'kcd_prefix': 'C'},
            '암': {'standard': 'Cancer', 'kcd_prefix': 'C'},
            '갑상선암': {'standard': 'ThyroidCancer', 'kcd_code': 'C77'},
            '뇌출혈': {'standard': 'CerebralHemorrhage', 'kcd_code': 'I61'},
            # ...
        }
    }

    def link_entities(self, relations: List[dict]) -> List[dict]:
        """
        Map entities to standard ontology
        """
        for relation in relations:
            # Standardize disease object
            obj = relation['object']

            for disease_term, mapping in self.ONTOLOGY['diseases'].items():
                if disease_term in obj:
                    relation['object_standard'] = mapping['standard']
                    relation['kcd_code'] = mapping.get('kcd_code')
                    break

        return relations
```

### Stage 6: Neo4j Graph Construction

```python
class GraphConstructor:
    """
    Build Neo4j graph from extracted relations
    """
    def __init__(self):
        self.driver = neo4j.GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

    async def construct_graph(self, state: IngestionState) -> IngestionState:
        """
        Create nodes and relationships in Neo4j
        """
        with self.driver.session() as session:
            # Create Product node
            product_id = self.create_product(session, state['metadata'])

            # Create Clause nodes
            clause_mapping = {}
            for article in state['document_hierarchy']['articles']:
                clause_id = self.create_clause(session, product_id, article)
                clause_mapping[article['article_num']] = clause_id

            # Create Coverage, Disease, Condition nodes + relationships
            for relation in state['standardized_entities']:
                self.create_relation_graph(session, relation, clause_mapping)

            state['neo4j_nodes'] = session.run("MATCH (n) RETURN count(n)").single()[0]
            state['neo4j_edges'] = session.run("MATCH ()-[r]->() RETURN count(r)").single()[0]

        return state

    def create_relation_graph(self, session, relation: dict, clause_mapping: dict):
        """
        Create coverage-disease relationship with provenance
        """
        query = """
        // Create or match Coverage
        MERGE (cov:Coverage {name: $coverage_name})
        ON CREATE SET cov.id = randomUUID(), cov.created_at = datetime()

        // Create or match Disease
        MERGE (dis:Disease {kcd_code: $kcd_code})
        ON CREATE SET dis.id = randomUUID(),
                      dis.name_ko = $disease_name,
                      dis.created_at = datetime()

        // Create relationship
        MERGE (cov)-[r:COVERS]->(dis)
        SET r.confidence = $confidence,
            r.extraction_method = 'llm_extracted'

        // Link to source Clause (provenance!)
        WITH cov
        MATCH (clause:Clause {id: $clause_id})
        MERGE (cov)-[:DEFINED_IN]->(clause)
        """

        session.run(
            query,
            coverage_name=relation['subject'],
            kcd_code=relation['kcd_code'],
            disease_name=relation['object'],
            confidence=relation['confidence'],
            clause_id=clause_mapping.get(relation['article_ref'])
        )
```

### LangGraph Pipeline Orchestration

```python
def create_ingestion_pipeline() -> StateGraph:
    """
    Orchestrate ingestion stages with LangGraph
    """
    workflow = StateGraph(IngestionState)

    # Add nodes
    workflow.add_node("ocr", OCRAgent().process)
    workflow.add_node("parse_structure", LegalStructureParser().parse)
    workflow.add_node("extract_critical", CriticalDataExtractor().extract)
    workflow.add_node("extract_relations", RelationExtractionAgent().extract)
    workflow.add_node("link_entities", EntityLinker().link_entities)
    workflow.add_node("construct_graph", GraphConstructor().construct_graph)
    workflow.add_node("validate", ValidationAgent().validate)

    # Define edges
    workflow.add_edge("ocr", "parse_structure")
    workflow.add_edge("parse_structure", "extract_critical")
    workflow.add_edge("extract_critical", "extract_relations")
    workflow.add_edge("extract_relations", "link_entities")
    workflow.add_edge("link_entities", "construct_graph")
    workflow.add_edge("construct_graph", "validate")
    workflow.add_edge("validate", END)

    # Set entry point
    workflow.set_entry_point("ocr")

    return workflow.compile()

# Usage
pipeline = create_ingestion_pipeline()
result = await pipeline.ainvoke({
    'job_id': 'job_123',
    'file_path': '/tmp/policy.pdf',
    'metadata': {...}
})
```

---

## 🔍 GraphRAG Query Engine Architecture

### Query Processing Flow

```
User Query (NL)
    ↓
[Query Classification]
    ├─ Simple Fact → Vector Search + 1-hop Graph
    ├─ Complex Reasoning → Multi-hop Graph Traversal + LLM
    └─ Comparison → Pre-computed CONFLICTS_WITH + Analysis
    ↓
[Hybrid Retrieval]
    ├─ Vector Search (Neo4j Vector Index)
    └─ Graph Traversal (Cypher)
    ↓
[LLM Reasoning Layer]
    ├─ Context: Graph paths + Source clauses
    └─ Model: Solar Pro → GPT-4o (cascade)
    ↓
[4-Stage Validation]
    ├─ Source attachment check
    ├─ Confidence thresholding
    ├─ Forbidden phrase filtering
    └─ Expert review queue (if needed)
    ↓
[Response Formatting]
```

### Query Classification

```python
class QueryClassifier:
    """
    Classify query type for optimal strategy
    """
    PATTERNS = {
        'simple_coverage': [
            r'(보장|담보).*돼',
            r'나와요',
            r'지급.*되나요'
        ],
        'comparison': [
            r'(비교|차이)',
            r'중복.*보장',
            r'어느.*좋아요'
        ],
        'temporal': [
            r'\d{4}년.*가입',
            r'예전.*약관',
            r'개정.*전'
        ],
        'gap_analysis': [
            r'부족한.*보장',
            r'추가.*필요',
            r'공백'
        ]
    }

    def classify(self, query: str) -> str:
        """
        Classify query into strategy type
        """
        for query_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return query_type

        return 'general'
```

### Hybrid Retrieval Strategy

```python
class HybridRetriever:
    """
    Combine vector search + graph traversal
    """
    async def retrieve(self, query: str, options: dict) -> dict:
        """
        Execute hybrid retrieval
        """
        # Step 1: Vector search for relevant clauses
        vector_results = await self.vector_search(query, top_k=10)

        # Step 2: Extract coverage/disease entities from top results
        relevant_entities = self.extract_entities(vector_results)

        # Step 3: Graph traversal from entities
        graph_paths = await self.graph_traversal(
            relevant_entities,
            max_hops=options.get('max_hops', 3)
        )

        # Step 4: Merge and rank results
        combined = self.merge_results(vector_results, graph_paths)

        return combined

    async def vector_search(self, query: str, top_k: int) -> List[dict]:
        """
        Neo4j vector search on clause embeddings
        """
        # Generate query embedding
        query_embedding = await self.embedder.embed(query)

        # Search Neo4j vector index
        cypher = """
        CALL db.index.vector.queryNodes('clause_embeddings', $top_k, $query_embedding)
        YIELD node, score
        RETURN node.id AS clause_id,
               node.raw_text AS text,
               node.article_num AS article,
               score
        ORDER BY score DESC
        """

        with self.driver.session() as session:
            results = session.run(cypher, top_k=top_k, query_embedding=query_embedding)
            return [dict(record) for record in results]

    async def graph_traversal(self, entities: dict, max_hops: int) -> List[dict]:
        """
        Multi-hop graph traversal
        """
        cypher = """
        // Start from Coverage entities
        MATCH (cov:Coverage)
        WHERE cov.name IN $coverage_names

        // Traverse to Disease
        MATCH path = (cov)-[r:COVERS|EXCLUDES*1..{max_hops}]->(d:Disease)
        WHERE d.kcd_code IN $kcd_codes OR d.name_ko IN $disease_names

        // Optional: Get Conditions
        OPTIONAL MATCH (cov)-[:REQUIRES]->(cond:Condition)

        // Optional: Get source Clause (provenance)
        OPTIONAL MATCH (cov)-[:DEFINED_IN]->(clause:Clause)

        RETURN path, cond, clause
        LIMIT 50
        """.format(max_hops=max_hops)

        with self.driver.session() as session:
            results = session.run(
                cypher,
                coverage_names=entities.get('coverages', []),
                kcd_codes=entities.get('kcd_codes', []),
                disease_names=entities.get('diseases', [])
            )
            return [dict(record) for record in results]
```

### LLM Reasoning Layer

```python
class ReasoningAgent:
    """
    LLM-based reasoning over graph results
    """
    REASONING_PROMPT = """
당신은 보험 약관 전문가입니다. 다음 정보를 바탕으로 사용자 질문에 답변하세요.

[사용자 질문]
{query}

[그래프 분석 결과]
{graph_context}

[원문 조항]
{source_clauses}

[지침]
1. 반드시 제공된 원문 조항을 근거로 답변하세요
2. 약관에 명시되지 않은 내용은 "확인이 필요합니다"라고 답하세요
3. 절대적 단언("100% 보장", "무조건")은 사용하지 마세요
4. "약관 제X조에 따르면"과 같은 표현을 포함하세요

[출력 형식]
{{
  "summary": "2-3문장 요약",
  "details": [
    {{
      "coverage": "담보명",
      "is_covered": true/false,
      "conditions": [],
      "reasoning": "판단 근거"
    }}
  ],
  "confidence": 0.0-1.0,
  "sources": ["clause_id_1", "clause_id_2"]
}}
"""

    async def reason(self, query: str, graph_results: dict) -> dict:
        """
        Generate answer with reasoning
        """
        # Format graph results for LLM
        graph_context = self.format_graph_context(graph_results)
        source_clauses = self.format_source_clauses(graph_results)

        prompt = self.REASONING_PROMPT.format(
            query=query,
            graph_context=graph_context,
            source_clauses=source_clauses
        )

        # Cascade: Solar Pro → GPT-4o if low confidence
        response = await self.solar_llm.generate(prompt)
        answer = json.loads(response)

        if answer['confidence'] < 0.7:
            response = await self.gpt4_llm.generate(prompt)
            answer = json.loads(response)

        return answer
```

### 4-Stage Validation Pipeline

```python
class AnswerValidator:
    """
    4-stage validation to prevent hallucination
    """
    def validate(self, answer: dict, graph_results: dict) -> dict:
        """
        Run all validation stages
        """
        # Stage 1: Source attachment check
        if not self.check_sources(answer, graph_results):
            return self.reject_no_source()

        # Stage 2: Confidence thresholding
        status = self.check_confidence(answer['confidence'])
        if status == 'reject':
            return self.reject_low_confidence()

        # Stage 3: Forbidden phrase filtering
        violations = self.check_forbidden_phrases(answer['summary'])
        if violations:
            return self.reject_forbidden_phrases(violations)

        # Stage 4: Expert review queue (if medium confidence)
        if status == 'expert_review':
            self.add_to_review_queue(answer, graph_results)

        return {
            'status': status,
            'answer': answer,
            'warnings': self.generate_warnings(status)
        }

    def check_sources(self, answer: dict, graph_results: dict) -> bool:
        """
        Ensure all claims have source clauses
        """
        referenced_clauses = set(answer.get('sources', []))
        available_clauses = set(c['clause_id'] for c in graph_results.get('source_clauses', []))

        return referenced_clauses.issubset(available_clauses)

    FORBIDDEN_PHRASES = [
        '100% 보장',
        '무조건',
        '절대',
        '확실히',
        '당연히',
    ]

    def check_forbidden_phrases(self, text: str) -> List[str]:
        """
        Detect forbidden phrases
        """
        violations = []
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase in text:
                violations.append(phrase)
        return violations
```

---

## 🏢 Infrastructure & Deployment Architecture

### AWS Architecture (Financial Compliance)

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              CloudFront (CDN) + WAF                          │
│  - DDoS protection  - Geo-blocking  - SSL/TLS termination   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  VPC (Logically Isolated)                    │
│ ┌──────────────────────────────────────────────────────────┐│
│ │           Public Subnet (NAT Gateway)                    ││
│ └──────────────────────────────────────────────────────────┘│
│ ┌──────────────────────────────────────────────────────────┐│
│ │           Private Subnet - Application Tier              ││
│ │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ││
│ │  │   EKS Pod    │  │   EKS Pod    │  │   EKS Pod    │  ││
│ │  │  (FastAPI)   │  │  (Worker)    │  │  (Worker)    │  ││
│ │  └──────────────┘  └──────────────┘  └──────────────┘  ││
│ └──────────────────────────────────────────────────────────┘│
│ ┌──────────────────────────────────────────────────────────┐│
│ │           Private Subnet - Data Tier                     ││
│ │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ││
│ │  │   Neo4j      │  │  PostgreSQL  │  │   Redis      │  ││
│ │  │   (RDS/EC2)  │  │   (RDS)      │  │ (ElastiCache)│  ││
│ │  └──────────────┘  └──────────────┘  └──────────────┘  ││
│ └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              External Services (Outside VPC)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │      S3      │  │   Upstage    │  │   OpenAI     │      │
│  │  (Policies)  │  │  (LLM/OCR)   │  │   (GPT-4o)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### EKS (Kubernetes) Deployment

```yaml
# kubernetes/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: insuregraph-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: insuregraph-api
  template:
    metadata:
      labels:
        app: insuregraph-api
    spec:
      containers:
      - name: fastapi
        image: insuregraph/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: NEO4J_URI
          valueFrom:
            secretKeyRef:
              name: neo4j-credentials
              key: uri
        - name: POSTGRES_URI
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: uri
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: insuregraph-api-service
spec:
  type: LoadBalancer
  selector:
    app: insuregraph-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: insuregraph-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: insuregraph-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Background Workers (Celery)

```yaml
# kubernetes/worker-deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: insuregraph-worker
spec:
  replicas: 5
  selector:
    matchLabels:
      app: insuregraph-worker
  template:
    metadata:
      labels:
        app: insuregraph-worker
    spec:
      containers:
      - name: celery-worker
        image: insuregraph/worker:latest
        command: ["celery", "-A", "app.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
        env:
        - name: CELERY_BROKER_URL
          value: "redis://redis-service:6379/0"
        - name: CELERY_RESULT_BACKEND
          value: "redis://redis-service:6379/1"
        resources:
          requests:
            memory: "1Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "4000m"
```

---

## 🔒 Security & Compliance Architecture

### Data Flow & Compliance Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                  PUBLIC ZONE (외부 접근)                     │
│  - CloudFront CDN                                            │
│  - WAF (Web Application Firewall)                            │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS Only
┌──────────────────────▼──────────────────────────────────────┐
│              DMZ (Kong API Gateway)                          │
│  - JWT Validation                                            │
│  - Rate Limiting                                             │
│  - Request Logging (Audit)                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal TLS
┌──────────────────────▼──────────────────────────────────────┐
│          APPLICATION ZONE (논리적 망분리)                    │
│  - FastAPI Application (Private Subnet)                      │
│  - No direct internet access                                 │
│  - All external API calls via NAT Gateway                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ Encrypted Connection
┌──────────────────────▼──────────────────────────────────────┐
│              DATA ZONE (최고 보안 수준)                      │
│  - Neo4j (Encrypted at rest + in transit)                    │
│  - PostgreSQL (TDE enabled)                                  │
│  - PII Encryption (AES-256)                                  │
│  - No direct external access                                 │
└─────────────────────────────────────────────────────────────┘
```

### PII (Personal Identifiable Information) Protection

```python
# Security module for PII handling

from cryptography.fernet import Fernet
import hashlib

class PIIProtector:
    """
    Encrypt/decrypt PII data
    """
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)

    def encrypt_name(self, name: str) -> bytes:
        """
        Encrypt customer name (AES-256)
        """
        return self.cipher.encrypt(name.encode('utf-8'))

    def decrypt_name(self, encrypted_name: bytes) -> str:
        """
        Decrypt customer name (only for authorized access)
        """
        return self.cipher.decrypt(encrypted_name).decode('utf-8')

    @staticmethod
    def hash_phone(phone: str) -> str:
        """
        One-way hash for phone number (for deduplication)
        """
        return hashlib.sha256(phone.encode('utf-8')).hexdigest()

    @staticmethod
    def mask_birth_date(birth_date: str) -> dict:
        """
        Extract only year, discard month/day
        """
        year = birth_date.split('-')[0]
        return {
            'birth_year': int(year),
            'original_masked': True
        }

# PostgreSQL PII storage
INSERT INTO customers (
    name_encrypted,  -- AES-256 encrypted
    birth_year,      -- Only year, not full date
    phone_hash       -- SHA-256 hashed
) VALUES (
    %s, %s, %s
);
```

### Audit Logging

```python
class AuditLogger:
    """
    Comprehensive audit logging for compliance
    """
    def log_query_access(self, user_id: str, query: str, customer_id: str):
        """
        Log all query accesses for audit trail
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'action': 'query_executed',
            'resource_type': 'customer_data',
            'resource_id': customer_id,
            'query_text': self.sanitize_query(query),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent')
        }

        # Write to PostgreSQL audit_logs table
        db.execute(
            "INSERT INTO audit_logs (...) VALUES (...)",
            log_entry
        )

        # Also send to CloudWatch for real-time monitoring
        cloudwatch.put_log_events(
            logGroupName='/insuregraph/audit',
            logStreamName=f'{user_id}/{datetime.now().date()}',
            logEvents=[{
                'timestamp': int(datetime.now().timestamp() * 1000),
                'message': json.dumps(log_entry)
            }]
        )
```

### Financial Sandbox Compliance Checklist

| Requirement | Implementation | Status |
|-------------|---------------|--------|
| **논리적 망분리** | Private VPC subnets, no direct internet access | ✅ Phase 1 |
| **PII 암호화** | AES-256 encryption at rest, TLS in transit | ✅ Phase 1 |
| **접근 로그 기록** | All API calls logged to audit_logs table | ✅ Phase 1 |
| **권한 관리** | RBAC with JWT, role-based access control | ✅ Phase 1 |
| **데이터 최소화** | Only birth year stored, phone hashed | ✅ Phase 1 |
| **보안 취약점 점검** | Monthly penetration testing | 🔄 Phase 2 |
| **사고 대응 계획** | Incident response playbook | 🔄 Phase 2 |

---

## 📊 Performance & Scalability

### Performance Targets

| Metric | Phase 1 (MVP) | Phase 2 (Commercial) | Phase 3 (Scale) |
|--------|---------------|----------------------|-----------------|
| **Simple Query Latency** | < 500ms | < 300ms | < 200ms |
| **Complex Query Latency** | < 3s | < 2s | < 1.5s |
| **Ingestion Speed** | 50 pages/min | 100 pages/min | 200 pages/min |
| **Concurrent Users** | 100 | 1,000 | 10,000 |
| **Policy Knowledge Base** | 50 products | 200 products | 500+ products |
| **Graph Size** | ~50K nodes | ~200K nodes | ~500K nodes |

### Caching Strategy

```python
class QueryCache:
    """
    Multi-layer caching for performance
    """
    def __init__(self):
        self.redis = Redis(host='redis-service', port=6379)
        self.local_cache = {}  # In-memory LRU cache

    async def get_or_compute(self, query: str, compute_fn: callable) -> dict:
        """
        3-tier cache: Memory → Redis → Compute
        """
        cache_key = self.generate_cache_key(query)

        # Layer 1: Local memory cache (fastest)
        if cache_key in self.local_cache:
            return self.local_cache[cache_key]

        # Layer 2: Redis cache (fast)
        cached = self.redis.get(cache_key)
        if cached:
            result = json.loads(cached)
            self.local_cache[cache_key] = result
            return result

        # Layer 3: Compute (slow)
        result = await compute_fn()

        # Store in both caches
        self.redis.setex(cache_key, 3600, json.dumps(result))  # 1 hour TTL
        self.local_cache[cache_key] = result

        return result

    def invalidate_product(self, product_id: str):
        """
        Invalidate all caches for a product (e.g., after update)
        """
        pattern = f"query:*:product:{product_id}:*"
        for key in self.redis.scan_iter(match=pattern):
            self.redis.delete(key)
```

### Database Indexing Strategy

```cypher
// Neo4j Indexes for optimal query performance

// Primary key indexes (already defined in schema)
CREATE INDEX product_id FOR (p:Product) ON (p.id);
CREATE INDEX coverage_id FOR (c:Coverage) ON (c.id);
CREATE INDEX disease_kcd FOR (d:Disease) ON (d.kcd_code);

// Composite indexes for common queries
CREATE INDEX coverage_product FOR (c:Coverage) ON (c.product_id, c.type);
CREATE INDEX clause_product_article FOR (c:Clause) ON (c.product_id, c.article_num);

// Full-text search indexes
CREATE FULLTEXT INDEX disease_search FOR (d:Disease) ON EACH [d.name_ko, d.name_en, d.synonyms];
CREATE FULLTEXT INDEX clause_text FOR (c:Clause) ON EACH [c.raw_text, c.summary];

// Vector index for semantic search
CREATE VECTOR INDEX clause_embeddings FOR (c:Clause) ON (c.embedding)
  OPTIONS {indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }};
```

### Monitoring & Observability

```python
# Prometheus metrics

from prometheus_client import Counter, Histogram, Gauge

# API Metrics
api_requests_total = Counter(
    'insuregraph_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

api_request_duration = Histogram(
    'insuregraph_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

# Query Metrics
query_execution_time = Histogram(
    'insuregraph_query_execution_seconds',
    'GraphRAG query execution time',
    ['query_type']
)

graph_traversal_hops = Histogram(
    'insuregraph_graph_hops',
    'Number of graph hops per query',
    ['query_type']
)

# LLM Metrics
llm_token_usage = Counter(
    'insuregraph_llm_tokens_total',
    'Total LLM tokens used',
    ['model', 'operation']
)

llm_confidence_score = Histogram(
    'insuregraph_llm_confidence',
    'LLM confidence scores',
    ['model']
)

# Database Metrics
neo4j_nodes_count = Gauge(
    'insuregraph_neo4j_nodes_total',
    'Total nodes in Neo4j'
)

neo4j_relationships_count = Gauge(
    'insuregraph_neo4j_relationships_total',
    'Total relationships in Neo4j'
)
```

---

## 🎯 Technology Decisions & Rationale

### Decision Log

#### Decision 1: Neo4j Vector Index vs. Dedicated Vector DB

**Context**: Need both graph traversal and vector search.

**Options Considered**:
- A) Neo4j Vector Index (unified)
- B) Neo4j + Pinecone (separate)

**Decision**: **A) Neo4j Vector Index** for Phase 1, migrate to B if performance issues.

**Rationale**:
- ✅ Reduced latency (no inter-service calls)
- ✅ Simpler architecture
- ✅ Lower operational cost
- ⚠️ Risk: Performance at scale (mitigated by benchmarking)

---

#### Decision 2: Upstage Solar Pro vs. GPT-4o

**Context**: LLM for relation extraction and reasoning.

**Decision**: **Cascade strategy** - Solar Pro primary, GPT-4o fallback.

**Rationale**:
- ✅ Cost-effective (Solar Pro ~30% cheaper)
- ✅ Korean language specialization
- ✅ Table/form recognition superior
- ✅ GPT-4o backup ensures quality

---

#### Decision 3: LangGraph vs. Custom Orchestration

**Context**: Multi-agent workflow orchestration.

**Decision**: **LangGraph**

**Rationale**:
- ✅ Built-in state management
- ✅ Easy to visualize and debug
- ✅ Active community and support
- ✅ Integrates well with LangChain ecosystem

---

#### Decision 4: AWS vs. GCP vs. Azure

**Context**: Cloud infrastructure provider.

**Decision**: **AWS**

**Rationale**:
- ✅ Best support for Neo4j (AWS Marketplace)
- ✅ Strong financial compliance tools (CloudHSM, KMS)
- ✅ Team expertise
- ✅ Korean region availability (ap-northeast-2)

---

## 📁 Project Structure

```
insuregraph-pro/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── ingestion.py
│   │   │   │   ├── query.py
│   │   │   │   ├── compliance.py
│   │   │   │   └── mydata.py
│   │   │   └── dependencies.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   │   ├── ocr_agent.py
│   │   │   │   ├── parser.py
│   │   │   │   ├── extractor.py
│   │   │   │   └── graph_constructor.py
│   │   │   ├── query/
│   │   │   │   ├── classifier.py
│   │   │   │   ├── retriever.py
│   │   │   │   ├── reasoner.py
│   │   │   │   └── validator.py
│   │   │   └── compliance/
│   │   │       └── script_validator.py
│   │   ├── models/
│   │   │   ├── graph_models.py
│   │   │   └── db_models.py
│   │   └── main.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── styles/
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── infrastructure/
│   ├── terraform/
│   │   ├── vpc.tf
│   │   ├── eks.tf
│   │   ├── rds.tf
│   │   └── s3.tf
│   └── kubernetes/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── ingress.yaml
├── docs/
│   ├── prd.md
│   ├── graphrag-implementation-strategy.md
│   └── architecture.md  ← This document
└── README.md
```

---

## 🚀 Next Steps

1. **Review & Approval**: Architect → CTO → PM
2. **Create Epic & Stories**: Break down into implementable user stories
3. **Setup Development Environment**:
   - Provision Neo4j instance
   - Setup FastAPI boilerplate
   - Configure LLM API keys
4. **Prototype Core Pipeline**: Implement one complete ingestion flow (PDF → Graph)
5. **Benchmark Performance**: Validate query latency assumptions

---

**Document Status**: ✅ Draft Complete → Pending Review
**Next Reviewer**: CTO / Tech Lead
**Estimated Review Time**: 2-3 days
