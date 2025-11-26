"""
Entity Linker

Links disease entity mentions to standardized ontology.
Handles:
- Exact matching
- Synonym resolution
- Fuzzy matching for typos
- KCD code lookup
"""
import os
import yaml
from typing import List, Optional, Dict, Any
from difflib import SequenceMatcher
from pathlib import Path

from app.models.ontology import DiseaseEntity, EntityLinkResult


class EntityLinker:
    """Links disease mentions to ontology"""

    def __init__(self, ontology_path: Optional[str] = None):
        """
        Initialize entity linker

        Args:
            ontology_path: Path to ontology YAML file. If None, uses default.
        """
        if ontology_path is None:
            # Default path
            ontology_path = Path(__file__).parent.parent.parent / "data" / "disease_ontology.yaml"

        self.ontology_path = ontology_path
        self.entities: List[DiseaseEntity] = []
        self.kcd_index: Dict[str, DiseaseEntity] = {}
        self.name_index: Dict[str, DiseaseEntity] = {}

        # Load ontology
        self._load_ontology()

    def _load_ontology(self):
        """Load ontology from YAML file"""
        with open(self.ontology_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        diseases = data.get('diseases', {})

        for category_name, category_data in diseases.items():
            subtypes = category_data.get('subtypes', {})

            for subtype_name, subtype_data in subtypes.items():
                # Create DiseaseEntity
                entity = DiseaseEntity(
                    standard_name=subtype_data['standard'],
                    korean_names=subtype_data.get('korean_names', []),
                    english_names=subtype_data.get('english_names', []),
                    kcd_codes=subtype_data.get('kcd_codes', []),
                    severity=subtype_data.get('severity'),
                    category=category_name,
                    description=subtype_data.get('description'),
                )

                self.entities.append(entity)

                # Build indexes
                # KCD index
                for kcd in entity.kcd_codes:
                    self.kcd_index[kcd] = entity

                # Name index (for fast exact lookup)
                for name in entity.get_all_names():
                    self.name_index[name.lower()] = entity

    def link(
        self,
        query: str,
        use_fuzzy: bool = True,
        fuzzy_threshold: float = 0.8,
    ) -> EntityLinkResult:
        """
        Link query term to ontology entity

        Args:
            query: Disease term to link
            use_fuzzy: Whether to use fuzzy matching
            fuzzy_threshold: Minimum similarity for fuzzy match (0.0-1.0)

        Returns:
            EntityLinkResult with match information
        """
        # Step 1: Try exact match
        result = self._exact_match(query)
        if result.is_successful():
            return result

        # Step 2: Try KCD code match
        result = self._kcd_match(query)
        if result.is_successful():
            return result

        # Step 3: Try fuzzy match (if enabled)
        if use_fuzzy:
            result = self._fuzzy_match(query, threshold=fuzzy_threshold)
            if result.is_successful():
                return result

        # No match found
        return EntityLinkResult(
            query=query,
            matched_entity=None,
            match_score=0.0,
            match_method="none",
        )

    def link_by_kcd(self, kcd_code: str) -> EntityLinkResult:
        """Link by KCD code only"""
        return self._kcd_match(kcd_code)

    def _exact_match(self, query: str) -> EntityLinkResult:
        """Try exact name matching"""
        query_lower = query.lower()

        # Check name index
        entity = self.name_index.get(query_lower)
        if entity:
            return EntityLinkResult(
                query=query,
                matched_entity=entity,
                match_score=1.0,
                match_method="exact",
                matched_name=query,
            )

        # No exact match
        return EntityLinkResult(
            query=query,
            matched_entity=None,
            match_score=0.0,
            match_method="exact_failed",
        )

    def _kcd_match(self, query: str) -> EntityLinkResult:
        """Try KCD code matching"""
        # Extract potential KCD code (e.g., "C77", "I21")
        import re
        kcd_pattern = r'\b([A-Z]\d{2})\b'
        match = re.search(kcd_pattern, query)

        if not match:
            return EntityLinkResult(
                query=query,
                matched_entity=None,
                match_score=0.0,
                match_method="kcd_failed",
            )

        kcd_code = match.group(1)
        entity = self.kcd_index.get(kcd_code)

        if entity:
            return EntityLinkResult(
                query=query,
                matched_entity=entity,
                match_score=1.0,
                match_method="kcd",
                matched_name=kcd_code,
            )

        return EntityLinkResult(
            query=query,
            matched_entity=None,
            match_score=0.0,
            match_method="kcd_failed",
        )

    def _fuzzy_match(self, query: str, threshold: float = 0.8) -> EntityLinkResult:
        """Try fuzzy string matching for typos"""
        query_lower = query.lower()
        best_match = None
        best_score = 0.0
        best_name = None

        for entity in self.entities:
            for name in entity.get_all_names():
                name_lower = name.lower()

                # Calculate similarity using SequenceMatcher
                similarity = SequenceMatcher(None, query_lower, name_lower).ratio()

                if similarity > best_score:
                    best_score = similarity
                    best_match = entity
                    best_name = name

        # Check if best score meets threshold
        if best_score >= threshold:
            return EntityLinkResult(
                query=query,
                matched_entity=best_match,
                match_score=best_score,
                match_method="fuzzy",
                matched_name=best_name,
            )

        return EntityLinkResult(
            query=query,
            matched_entity=None,
            match_score=best_score,
            match_method="fuzzy_failed",
        )

    def link_multiple(
        self,
        queries: List[str],
        use_fuzzy: bool = True,
        fuzzy_threshold: float = 0.8,
    ) -> List[EntityLinkResult]:
        """Link multiple queries"""
        return [self.link(q, use_fuzzy, fuzzy_threshold) for q in queries]

    def get_entity_by_standard_name(self, standard_name: str) -> Optional[DiseaseEntity]:
        """Get entity by standard name"""
        for entity in self.entities:
            if entity.standard_name == standard_name:
                return entity
        return None

    def get_entities_by_category(self, category: str) -> List[DiseaseEntity]:
        """Get all entities in a category"""
        return [e for e in self.entities if e.category == category]

    def get_entities_by_severity(self, severity: str) -> List[DiseaseEntity]:
        """Get all entities with specific severity"""
        return [e for e in self.entities if e.severity == severity]

    def get_all_kcd_codes(self) -> List[str]:
        """Get all KCD codes in ontology"""
        return list(self.kcd_index.keys())

    def get_stats(self) -> Dict[str, Any]:
        """Get ontology statistics"""
        categories = set(e.category for e in self.entities)
        severities = set(e.severity for e in self.entities if e.severity)

        return {
            "total_entities": len(self.entities),
            "total_kcd_codes": len(self.kcd_index),
            "categories": list(categories),
            "severities": list(severities),
            "category_counts": {
                cat: len(self.get_entities_by_category(cat))
                for cat in categories
            },
        }
