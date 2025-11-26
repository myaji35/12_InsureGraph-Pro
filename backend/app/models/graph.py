"""
Graph data models for Neo4j knowledge graph

Defines node and relationship schemas for insurance policy graph.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class NodeType(str, Enum):
    """Graph node types"""
    PRODUCT = "Product"
    COVERAGE = "Coverage"
    DISEASE = "Disease"
    CONDITION = "Condition"
    CLAUSE = "Clause"


class RelationType(str, Enum):
    """Graph relationship types"""
    COVERS = "COVERS"
    EXCLUDES = "EXCLUDES"
    REQUIRES = "REQUIRES"
    REDUCES = "REDUCES"
    LIMITS = "LIMITS"
    DEFINED_IN = "DEFINED_IN"
    REFERENCES = "REFERENCES"
    HAS_COVERAGE = "HAS_COVERAGE"
    HAS_CONDITION = "HAS_CONDITION"


# ============================================================================
# Node Models
# ============================================================================

class ProductNode(BaseModel):
    """Insurance product node"""
    product_id: str = Field(..., description="Unique product identifier")
    product_name: str = Field(..., description="Product name")
    company: str = Field(..., description="Insurance company name")
    product_type: str = Field(..., description="Type (암보험, 실손보험, etc.)")
    version: Optional[str] = Field(None, description="Product version")
    effective_date: Optional[str] = Field(None, description="Effective date")

    # Metadata
    document_id: Optional[str] = Field(None, description="Original document ID")
    total_pages: Optional[int] = Field(None, description="Total pages in document")
    created_at: Optional[str] = Field(None, description="Graph creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "product_001",
                "product_name": "무배당 ABC암보험",
                "company": "ABC생명",
                "product_type": "암보험",
                "version": "2023.1",
            }
        }


class CoverageNode(BaseModel):
    """Coverage benefit node"""
    coverage_id: str = Field(..., description="Unique coverage identifier")
    coverage_name: str = Field(..., description="Coverage name (암진단특약, etc.)")
    coverage_type: str = Field(..., description="Type (특약, 주계약, etc.)")

    # Benefit amounts
    benefit_amount: Optional[int] = Field(None, description="Benefit amount in KRW")
    min_amount: Optional[int] = Field(None, description="Minimum benefit amount")
    max_amount: Optional[int] = Field(None, description="Maximum benefit amount")

    # Coverage details
    description: Optional[str] = Field(None, description="Coverage description")

    class Config:
        json_schema_extra = {
            "example": {
                "coverage_id": "coverage_001",
                "coverage_name": "암진단특약",
                "coverage_type": "특약",
                "benefit_amount": 100000000,
            }
        }


class DiseaseNode(BaseModel):
    """Disease entity node"""
    disease_id: str = Field(..., description="Unique disease identifier")
    standard_name: str = Field(..., description="Standard English name")

    # Names
    korean_names: List[str] = Field(default_factory=list, description="Korean names")
    english_names: List[str] = Field(default_factory=list, description="English names")

    # Codes
    kcd_codes: List[str] = Field(default_factory=list, description="KCD disease codes")

    # Classification
    category: str = Field(..., description="Disease category (cancer, cardiovascular, etc.)")
    severity: Optional[str] = Field(None, description="Severity (minor, general, critical)")

    # Description
    description: Optional[str] = Field(None, description="Disease description")

    class Config:
        json_schema_extra = {
            "example": {
                "disease_id": "disease_thyroid_cancer",
                "standard_name": "ThyroidCancer",
                "korean_names": ["갑상선암", "갑상선의 악성신생물"],
                "kcd_codes": ["C73"],
                "category": "cancer",
                "severity": "minor",
            }
        }


class ConditionNode(BaseModel):
    """Condition/requirement node"""
    condition_id: str = Field(..., description="Unique condition identifier")
    condition_type: str = Field(..., description="Type (waiting_period, age_limit, etc.)")

    # Condition details
    description: str = Field(..., description="Condition description")

    # Temporal conditions
    waiting_period_days: Optional[int] = Field(None, description="Waiting period in days")
    coverage_period_days: Optional[int] = Field(None, description="Coverage period in days")

    # Age conditions
    min_age: Optional[int] = Field(None, description="Minimum age")
    max_age: Optional[int] = Field(None, description="Maximum age")

    # Amount conditions
    amount_limit: Optional[int] = Field(None, description="Amount limit in KRW")

    class Config:
        json_schema_extra = {
            "example": {
                "condition_id": "condition_001",
                "condition_type": "waiting_period",
                "description": "암 진단 시 90일 대기기간",
                "waiting_period_days": 90,
            }
        }


class ClauseNode(BaseModel):
    """Legal clause node with embeddings"""
    clause_id: str = Field(..., description="Unique clause identifier")

    # Clause structure
    article_num: str = Field(..., description="Article number (제1조)")
    article_title: Optional[str] = Field(None, description="Article title")
    paragraph_num: Optional[str] = Field(None, description="Paragraph number (①)")
    subclause_num: Optional[str] = Field(None, description="Subclause number (1./가.)")

    # Content
    clause_text: str = Field(..., description="Full clause text")
    clause_summary: Optional[str] = Field(None, description="LLM-generated summary")

    # Vector embedding for semantic search
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    embedding_model: Optional[str] = Field(None, description="Embedding model used")

    # Critical data
    has_amounts: bool = Field(default=False, description="Contains amount data")
    has_periods: bool = Field(default=False, description="Contains period data")
    has_kcd_codes: bool = Field(default=False, description="Contains KCD codes")

    # Metadata
    page: Optional[int] = Field(None, description="Page number")
    confidence: Optional[float] = Field(None, description="Extraction confidence")

    class Config:
        json_schema_extra = {
            "example": {
                "clause_id": "clause_001",
                "article_num": "제1조",
                "article_title": "보험금의 지급사유",
                "paragraph_num": "①",
                "clause_text": "회사는 피보험자가 암으로 진단확정된 경우 보험금을 지급합니다.",
                "has_amounts": True,
            }
        }


# ============================================================================
# Relationship Models
# ============================================================================

class GraphRelationship(BaseModel):
    """Base relationship model"""
    relation_id: str = Field(..., description="Unique relationship identifier")
    relation_type: RelationType = Field(..., description="Relationship type")

    source_node_id: str = Field(..., description="Source node ID")
    target_node_id: str = Field(..., description="Target node ID")

    # Relationship properties
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")

    # Metadata
    confidence: Optional[float] = Field(None, description="Relationship confidence")
    extracted_by: Optional[str] = Field(None, description="Extraction method (llm/rule)")
    reasoning: Optional[str] = Field(None, description="LLM reasoning")


class CoversRelationship(GraphRelationship):
    """COVERS relationship: Coverage → Disease"""
    relation_type: RelationType = Field(default=RelationType.COVERS, frozen=True)

    # Coverage details
    benefit_amount: Optional[int] = Field(None, description="Benefit amount in KRW")
    conditions: List[str] = Field(default_factory=list, description="Condition IDs")


class ExcludesRelationship(GraphRelationship):
    """EXCLUDES relationship: Coverage → Disease"""
    relation_type: RelationType = Field(default=RelationType.EXCLUDES, frozen=True)

    # Exclusion details
    exclusion_reason: Optional[str] = Field(None, description="Reason for exclusion")


class RequiresRelationship(GraphRelationship):
    """REQUIRES relationship: Coverage → Condition"""
    relation_type: RelationType = Field(default=RelationType.REQUIRES, frozen=True)

    # Requirement details
    is_mandatory: bool = Field(default=True, description="Is this requirement mandatory")


class DefinedInRelationship(GraphRelationship):
    """DEFINED_IN relationship: Coverage/Condition/Disease → Clause"""
    relation_type: RelationType = Field(default=RelationType.DEFINED_IN, frozen=True)

    # Source location
    position_in_clause: Optional[int] = Field(None, description="Character position in clause")


class ReferencesRelationship(GraphRelationship):
    """REFERENCES relationship: Clause → Clause"""
    relation_type: RelationType = Field(default=RelationType.REFERENCES, frozen=True)

    # Reference details
    reference_type: Optional[str] = Field(None, description="Type of reference")


# ============================================================================
# Graph Construction Models
# ============================================================================

class GraphBatch(BaseModel):
    """Batch of nodes and relationships for bulk insertion"""
    products: List[ProductNode] = Field(default_factory=list)
    coverages: List[CoverageNode] = Field(default_factory=list)
    diseases: List[DiseaseNode] = Field(default_factory=list)
    conditions: List[ConditionNode] = Field(default_factory=list)
    clauses: List[ClauseNode] = Field(default_factory=list)

    relationships: List[GraphRelationship] = Field(default_factory=list)

    def total_nodes(self) -> int:
        """Count total nodes"""
        return (
            len(self.products)
            + len(self.coverages)
            + len(self.diseases)
            + len(self.conditions)
            + len(self.clauses)
        )

    def total_relationships(self) -> int:
        """Count total relationships"""
        return len(self.relationships)


class GraphStats(BaseModel):
    """Graph construction statistics"""
    total_nodes: int = 0
    total_relationships: int = 0

    nodes_by_type: Dict[str, int] = Field(default_factory=dict)
    relationships_by_type: Dict[str, int] = Field(default_factory=dict)

    construction_time_seconds: Optional[float] = None
    errors: List[str] = Field(default_factory=list)
