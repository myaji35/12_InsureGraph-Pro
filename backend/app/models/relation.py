"""
Relation extraction data models
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# Relation action types
RelationAction = Literal[
    "COVERS",      # 보장하다
    "EXCLUDES",    # 면책하다
    "REQUIRES",    # 조건을 요하다
    "REDUCES",     # 감액하다
    "LIMITS",      # 제한하다
    "REFERENCES",  # 참조하다
]


class RelationCondition(BaseModel):
    """Condition for a relation (e.g., waiting period, reduction ratio)"""
    type: str = Field(..., description="Condition type (waiting_period, reduction_period, age_limit, etc.)")
    value: Optional[int] = Field(None, description="Numeric value (days, amount, percentage)")
    description: str = Field(..., description="Human-readable description")


class ExtractedRelation(BaseModel):
    """A single extracted relation from a clause"""
    subject: str = Field(..., description="Subject entity (coverage name, product name)")
    action: RelationAction = Field(..., description="Relation action type")
    object: str = Field(..., description="Object entity (disease name, condition)")
    conditions: List[RelationCondition] = Field(default_factory=list, description="Conditions for this relation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="LLM confidence score")
    reasoning: str = Field(..., description="LLM reasoning for this extraction")
    source_clause_text: str = Field(..., description="Original clause text this was extracted from")


class RelationExtractionResult(BaseModel):
    """Result of relation extraction from a clause"""
    relations: List[ExtractedRelation] = Field(default_factory=list, description="All extracted relations")
    llm_model: str = Field(..., description="LLM model used (solar-pro or gpt-4o)")
    extraction_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall extraction confidence")
    validation_passed: bool = Field(..., description="Whether validation against critical_data passed")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors if any")
    validation_warnings: List[str] = Field(default_factory=list, description="Validation warnings")

    def get_relations_by_action(self, action: RelationAction) -> List[ExtractedRelation]:
        """Get all relations with specific action"""
        return [r for r in self.relations if r.action == action]

    def has_high_confidence(self, threshold: float = 0.85) -> bool:
        """Check if extraction has high confidence"""
        return self.extraction_confidence >= threshold

    def requires_review(self) -> bool:
        """Check if result requires human review"""
        return not self.validation_passed or not self.has_high_confidence()
