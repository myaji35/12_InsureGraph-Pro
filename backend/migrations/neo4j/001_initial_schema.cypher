// Migration: 001_initial_schema
// Description: Initial Neo4j graph schema for InsureGraph Pro
// Author: Backend Team
// Date: 2025-11-25

// ============================================
// Constraints (Unique identifiers)
// ============================================

// Product constraints
CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT product_code IF NOT EXISTS FOR (p:Product) REQUIRE p.product_code IS UNIQUE;

// Coverage constraints
CREATE CONSTRAINT coverage_id IF NOT EXISTS FOR (c:Coverage) REQUIRE c.id IS UNIQUE;

// Disease constraints
CREATE CONSTRAINT disease_id IF NOT EXISTS FOR (d:Disease) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT disease_kcd IF NOT EXISTS FOR (d:Disease) REQUIRE d.kcd_code IS UNIQUE;

// Condition constraints
CREATE CONSTRAINT condition_id IF NOT EXISTS FOR (c:Condition) REQUIRE c.id IS UNIQUE;

// Clause constraints
CREATE CONSTRAINT clause_id IF NOT EXISTS FOR (c:Clause) REQUIRE c.id IS UNIQUE;

// Exclusion constraints
CREATE CONSTRAINT exclusion_id IF NOT EXISTS FOR (e:Exclusion) REQUIRE e.id IS UNIQUE;

// PaymentRule constraints
CREATE CONSTRAINT payment_rule_id IF NOT EXISTS FOR (pr:PaymentRule) REQUIRE pr.id IS UNIQUE;

// ============================================
// Indexes (for performance)
// ============================================

// Product indexes
CREATE INDEX product_insurer IF NOT EXISTS FOR (p:Product) ON (p.insurer);
CREATE INDEX product_launch_date IF NOT EXISTS FOR (p:Product) ON (p.launch_date);
CREATE INDEX product_status IF NOT EXISTS FOR (p:Product) ON (p.status);

// Coverage indexes
CREATE INDEX coverage_type IF NOT EXISTS FOR (c:Coverage) ON (c.type);
CREATE INDEX coverage_name IF NOT EXISTS FOR (c:Coverage) ON (c.name);

// Disease indexes
CREATE INDEX disease_name_ko IF NOT EXISTS FOR (d:Disease) ON (d.name_ko);
CREATE INDEX disease_category IF NOT EXISTS FOR (d:Disease) ON (d.category);
CREATE INDEX disease_severity IF NOT EXISTS FOR (d:Disease) ON (d.severity_level);

// Clause indexes
CREATE INDEX clause_product_id IF NOT EXISTS FOR (c:Clause) ON (c.product_id);
CREATE INDEX clause_article_num IF NOT EXISTS FOR (c:Clause) ON (c.article_num);

// Condition indexes
CREATE INDEX condition_type IF NOT EXISTS FOR (c:Condition) ON (c.type);

// ============================================
// Full-text Search Indexes
// ============================================

// Disease full-text search (for Korean names)
CREATE FULLTEXT INDEX disease_search IF NOT EXISTS
FOR (d:Disease)
ON EACH [d.name_ko, d.name_en, d.synonyms];

// Clause full-text search
CREATE FULLTEXT INDEX clause_text_search IF NOT EXISTS
FOR (c:Clause)
ON EACH [c.raw_text, c.summary];

// ============================================
// Vector Index (for semantic search)
// ============================================

// Vector index for clause embeddings (1536-dim for OpenAI ada-002)
CREATE VECTOR INDEX clause_embeddings IF NOT EXISTS
FOR (c:Clause) ON (c.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }
};

// ============================================
// Sample Data Structure (Template)
// ============================================

// Example Product node structure
// (:Product {
//   id: "prod_uuid",
//   name: "Cancer Insurance Premium",
//   insurer: "Samsung Life",
//   product_code: "SL-CI-001",
//   launch_date: date("2023-03-15"),
//   version: "2.0",
//   status: "active",
//   description: "Comprehensive cancer coverage",
//   created_at: datetime(),
//   updated_at: datetime()
// })

// Example Coverage node structure
// (:Coverage {
//   id: "cov_uuid",
//   name: "암진단특약",
//   code: "CI-001",
//   type: "cancer",
//   category: "health",
//   base_amount: 100000000,
//   max_amount: 200000000,
//   min_amount: 50000000,
//   payment_type: "lump_sum",
//   created_at: datetime()
// })

// Example Disease node structure
// (:Disease {
//   id: "dis_uuid",
//   kcd_code: "C77",
//   kcd_version: "KCD-8",
//   name_ko: "갑상선암",
//   name_en: "Thyroid Cancer",
//   severity_level: "minor",
//   category: "cancer",
//   synonyms: ["갑상선의 악성신생물", "갑상선 악성종양"],
//   created_at: datetime()
// })

// Example Condition node structure
// (:Condition {
//   id: "cond_uuid",
//   type: "waiting_period",
//   days: 90,
//   percentage: null,
//   min_age: null,
//   max_age: null,
//   description: "계약일로부터 90일 면책기간",
//   trigger_event: "diagnosis"
// })

// Example Clause node structure
// (:Clause {
//   id: "clause_uuid",
//   product_id: "prod_uuid",
//   article_num: "제10조",
//   title: "보험금 지급",
//   paragraph: "②항",
//   subclause: null,
//   raw_text: "다만, 갑상선의 악성신생물(C77)...",
//   summary: "갑상선암은 소액암으로 분류되어 보장금액의 10% 지급",
//   page_num: 15,
//   parent_clause_id: null,
//   embedding: [0.123, 0.456, ...],  // 1536-dim vector
//   created_at: datetime()
// })

// Example Exclusion node structure
// (:Exclusion {
//   id: "excl_uuid",
//   type: "pre_existing",
//   description: "계약 전 발병한 질환 면책",
//   priority: 1,
//   effective_date: date("2023-03-15"),
//   expiry_date: null
// })

// Example PaymentRule node structure
// (:PaymentRule {
//   id: "rule_uuid",
//   condition_type: "duplicate_coverage",
//   formula: "MIN(actual_cost, coverage_amount)",
//   proportional_ratio: 0.5,
//   max_payout: 100000000,
//   description: "중복가입 시 비례보상 50%"
// })

// ============================================
// Relationship Examples
// ============================================

// Product-Coverage relationship
// (p:Product)-[:HAS_COVERAGE {
//   order: 1,
//   is_optional: false,
//   premium_rate: 0.05
// }]->(c:Coverage)

// Coverage-Disease relationship (COVERS)
// (c:Coverage)-[:COVERS {
//   confidence: 0.95,
//   extraction_method: "llm_extracted",
//   verified_by_expert: false,
//   verified_date: null
// }]->(d:Disease)

// Coverage-Disease relationship (EXCLUDES)
// (c:Coverage)-[:EXCLUDES {
//   priority: 1,
//   override_covers: true,
//   effective_period: "contract_start"
// }]->(d:Disease)

// Coverage-Condition relationship
// (c:Coverage)-[:REQUIRES {
//   order: 1,
//   is_mandatory: true
// }]->(cond:Condition)

// Coverage-PaymentRule relationship
// (c:Coverage)-[:APPLIES_RULE]->(pr:PaymentRule)

// Coverage-Clause relationship (provenance)
// (c:Coverage)-[:DEFINED_IN {
//   is_primary_definition: true
// }]->(clause:Clause)

// Condition-Clause relationship
// (cond:Condition)-[:REFERENCES]->(clause:Clause)

// Exclusion-Clause relationship
// (e:Exclusion)-[:BASED_ON]->(clause:Clause)

// Disease-Clause relationship
// (d:Disease)-[:MENTIONED_IN]->(clause:Clause)

// Coverage-Coverage conflict relationship
// (c1:Coverage)-[:CONFLICTS_WITH {
//   conflict_type: "proportional",
//   overlap_percentage: 0.8,
//   resolution_rule: "비례보상",
//   detected_date: date()
// }]->(c2:Coverage)

// Product versioning relationship
// (new:Product)-[:REPLACES {
//   replaced_date: date("2024-01-01"),
//   reason: "약관 개정",
//   migration_path: "automatic"
// }]->(old:Product)

// Disease hierarchy relationship
// (subtype:Disease)-[:SUBTYPE_OF]->(parent:Disease)
// Example: 갑상선 림프절 전이 -> 갑상선암

// ============================================
// Seed Data: Common Diseases (KCD-8)
// ============================================

// Create common cancer diseases
CREATE (:Disease {
  id: "dis_c00_c97",
  kcd_code: "C00-C97",
  kcd_version: "KCD-8",
  name_ko: "악성신생물",
  name_en: "Malignant neoplasms",
  severity_level: "critical",
  category: "cancer",
  synonyms: ["암", "악성종양"],
  created_at: datetime()
});

CREATE (:Disease {
  id: "dis_c77",
  kcd_code: "C77",
  kcd_version: "KCD-8",
  name_ko: "갑상선암",
  name_en: "Thyroid cancer",
  severity_level: "minor",
  category: "cancer",
  synonyms: ["갑상선의 악성신생물", "갑상선 악성종양"],
  created_at: datetime()
});

CREATE (:Disease {
  id: "dis_c44",
  kcd_code: "C44",
  kcd_version: "KCD-8",
  name_ko: "기타 피부암",
  name_en: "Other skin cancers",
  severity_level: "minor",
  category: "cancer",
  synonyms: ["피부의 악성신생물"],
  created_at: datetime()
});

// Create disease hierarchy
MATCH (child:Disease {kcd_code: "C77"})
MATCH (parent:Disease {kcd_code: "C00-C97"})
CREATE (child)-[:SUBTYPE_OF]->(parent);

MATCH (child:Disease {kcd_code: "C44"})
MATCH (parent:Disease {kcd_code: "C00-C97"})
CREATE (child)-[:SUBTYPE_OF]->(parent);

// Create common cardiovascular diseases
CREATE (:Disease {
  id: "dis_i21",
  kcd_code: "I21",
  kcd_version: "KCD-8",
  name_ko: "급성심근경색증",
  name_en: "Acute myocardial infarction",
  severity_level: "critical",
  category: "cardiovascular",
  synonyms: ["심근경색", "심장마비"],
  created_at: datetime()
});

CREATE (:Disease {
  id: "dis_i61",
  kcd_code: "I61",
  kcd_version: "KCD-8",
  name_ko: "뇌내출혈",
  name_en: "Intracerebral hemorrhage",
  severity_level: "critical",
  category: "cardiovascular",
  synonyms: ["뇌출혈"],
  created_at: datetime()
});

CREATE (:Disease {
  id: "dis_i63",
  kcd_code: "I63",
  kcd_version: "KCD-8",
  name_ko: "뇌경색증",
  name_en: "Cerebral infarction",
  severity_level: "critical",
  category: "cardiovascular",
  synonyms: ["뇌경색"],
  created_at: datetime()
});

// ============================================
// Verification Queries
// ============================================

// Verify constraints
SHOW CONSTRAINTS;

// Verify indexes
SHOW INDEXES;

// Count seed data
MATCH (d:Disease)
RETURN count(d) AS disease_count;

// Verify disease hierarchy
MATCH (child:Disease)-[:SUBTYPE_OF]->(parent:Disease)
RETURN child.name_ko AS child, parent.name_ko AS parent;

// Migration complete
RETURN "Migration 001_initial_schema completed successfully" AS status;
