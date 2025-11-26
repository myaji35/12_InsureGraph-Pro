"""
Ontology data models for disease entity linking
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DiseaseEntity(BaseModel):
    """A disease entity in the ontology"""
    standard_name: str = Field(..., description="Standard English name")
    korean_names: List[str] = Field(default_factory=list, description="Korean synonyms")
    english_names: List[str] = Field(default_factory=list, description="English synonyms")
    kcd_codes: List[str] = Field(default_factory=list, description="KCD disease codes")
    severity: Optional[str] = Field(None, description="Disease severity (minor/general/critical)")
    category: str = Field(..., description="Top-level category (cancer, cardiovascular, etc.)")
    description: Optional[str] = Field(None, description="Description")

    def matches_name(self, query: str, case_sensitive: bool = False) -> bool:
        """Check if query matches any name (exact match)"""
        if not case_sensitive:
            query = query.lower()
            all_names = [n.lower() for n in self.korean_names + self.english_names + [self.standard_name]]
        else:
            all_names = self.korean_names + self.english_names + [self.standard_name]

        return query in all_names

    def matches_kcd_code(self, kcd_code: str) -> bool:
        """Check if KCD code matches"""
        return kcd_code in self.kcd_codes

    def get_all_names(self) -> List[str]:
        """Get all names (Korean + English + Standard)"""
        return self.korean_names + self.english_names + [self.standard_name]


class EntityLinkResult(BaseModel):
    """Result of entity linking"""
    query: str = Field(..., description="Original query term")
    matched_entity: Optional[DiseaseEntity] = Field(None, description="Matched disease entity")
    match_score: float = Field(0.0, ge=0.0, le=1.0, description="Match confidence score")
    match_method: str = Field(..., description="Method used (exact/synonym/fuzzy/kcd)")
    matched_name: Optional[str] = Field(None, description="Specific name that matched")

    def is_successful(self) -> bool:
        """Check if linking was successful"""
        return self.matched_entity is not None

    def is_high_confidence(self, threshold: float = 0.85) -> bool:
        """Check if match has high confidence"""
        return self.match_score >= threshold
