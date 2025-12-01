"""
Entity Linker Service

추출된 엔티티를 표준 형식으로 정규화하고 연결합니다.

Features:
1. KCD Code Validation - 질병 코드 검증
2. Amount Normalization - 금액 정규화 확인
3. Insurance Type Classification - 보험 유형 분류
4. Disease Name Mapping - 질병명 매핑
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Set
from enum import Enum

from app.services.critical_data_extractor import ExtractionResult, ExtractedKCDCode
from loguru import logger


class InsuranceType(str, Enum):
    """Insurance product types"""
    CANCER = "cancer"  # 암보험
    HEALTH = "health"  # 건강보험
    LIFE = "life"  # 생명보험
    ACCIDENT = "accident"  # 상해보험
    LONG_TERM_CARE = "long_term_care"  # 장기요양보험
    UNKNOWN = "unknown"


class DiseaseCategory(str, Enum):
    """Disease categories based on KCD codes"""
    CANCER = "cancer"  # C00-D48 (신생물)
    CARDIOVASCULAR = "cardiovascular"  # I00-I99 (순환기계)
    CEREBROVASCULAR = "cerebrovascular"  # I60-I69 (뇌혈관질환)
    ENDOCRINE = "endocrine"  # E00-E90 (내분비)
    UNKNOWN = "unknown"


@dataclass
class LinkedEntity:
    """Linked and normalized entity"""
    original_value: str
    normalized_value: str
    entity_type: str  # "kcd_code", "disease_name", "insurance_type"
    category: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class LinkingResult:
    """Result of entity linking"""
    linked_entities: List[LinkedEntity]
    insurance_types: Set[InsuranceType]
    disease_categories: Set[DiseaseCategory]
    total_linked: int


class EntityLinker:
    """
    Links and normalizes extracted entities.

    Features:
    - KCD code validation and categorization
    - Disease name to KCD mapping
    - Insurance type classification
    - Entity normalization
    """

    # KCD code ranges for disease categories
    KCD_CATEGORIES = {
        DiseaseCategory.CANCER: ["C", "D0", "D1", "D2", "D3", "D4"],  # C00-D48
        DiseaseCategory.CARDIOVASCULAR: ["I"],  # I00-I99
        DiseaseCategory.CEREBROVASCULAR: ["I6"],  # I60-I69
        DiseaseCategory.ENDOCRINE: ["E"],  # E00-E90
    }

    # Disease name to KCD mapping (simplified)
    DISEASE_KCD_MAP = {
        "암": ["C"],
        "일반암": ["C"],
        "소액암": ["C77"],
        "유사암": ["D0", "D1", "D2", "D3"],
        "위암": ["C16"],
        "간암": ["C22"],
        "폐암": ["C34"],
        "유방암": ["C50"],
        "심근경색": ["I21", "I22", "I23"],
        "뇌졸중": ["I60", "I61", "I62", "I63", "I64"],
        "뇌출혈": ["I60", "I61", "I62"],
        "뇌경색": ["I63"],
        "당뇨": ["E10", "E11", "E12", "E13", "E14"],
        "고혈압": ["I10", "I11", "I12", "I13", "I15"],
    }

    # Insurance type keywords
    INSURANCE_KEYWORDS = {
        InsuranceType.CANCER: ["암", "암보험", "cancer"],
        InsuranceType.HEALTH: ["건강", "건강보험", "질병"],
        InsuranceType.LIFE: ["생명", "사망", "life"],
        InsuranceType.ACCIDENT: ["상해", "재해", "accident"],
        InsuranceType.LONG_TERM_CARE: ["장기요양", "요양", "간병"],
    }

    def __init__(self):
        """Initialize entity linker"""
        pass

    def link_entities(
        self,
        extracted_data: ExtractionResult,
        policy_name: str = "",
        full_text: str = "",
    ) -> LinkingResult:
        """
        Link and normalize entities.

        Args:
            extracted_data: Extracted data from critical data extractor
            policy_name: Insurance policy name
            full_text: Full document text

        Returns:
            LinkingResult with linked entities
        """
        linked_entities = []
        insurance_types = set()
        disease_categories = set()

        # 1. Link KCD codes
        for kcd in extracted_data.kcd_codes:
            linked = self._link_kcd_code(kcd)
            linked_entities.append(linked)

            # Categorize
            category = self._categorize_kcd(kcd.code)
            if category:
                disease_categories.add(category)

        # 2. Classify insurance type
        insurance_type = self._classify_insurance_type(policy_name, full_text)
        insurance_types.add(insurance_type)

        # 3. Extract disease names from text and link to KCD
        disease_names = self._extract_disease_names(full_text)
        for disease_name in disease_names:
            linked = self._link_disease_name(disease_name)
            if linked:
                linked_entities.append(linked)

        logger.info(
            f"Linked {len(linked_entities)} entities: "
            f"{len(extracted_data.kcd_codes)} KCD codes, "
            f"{len(disease_names)} disease names"
        )

        return LinkingResult(
            linked_entities=linked_entities,
            insurance_types=insurance_types,
            disease_categories=disease_categories,
            total_linked=len(linked_entities),
        )

    def _link_kcd_code(self, kcd: ExtractedKCDCode) -> LinkedEntity:
        """Link a KCD code"""
        category = self._categorize_kcd(kcd.code)

        return LinkedEntity(
            original_value=kcd.code,
            normalized_value=kcd.code.upper(),  # Normalize to uppercase
            entity_type="kcd_code",
            category=category.value if category else None,
            metadata={
                "is_range": kcd.is_range,
                "start_pos": kcd.start_pos,
                "end_pos": kcd.end_pos,
            },
        )

    def _categorize_kcd(self, kcd_code: str) -> Optional[DiseaseCategory]:
        """Categorize a KCD code"""
        for category, prefixes in self.KCD_CATEGORIES.items():
            for prefix in prefixes:
                if kcd_code.startswith(prefix):
                    return category
        return DiseaseCategory.UNKNOWN

    def _classify_insurance_type(self, policy_name: str, full_text: str) -> InsuranceType:
        """Classify insurance product type"""
        text = (policy_name + " " + full_text).lower()

        # Check keywords
        for ins_type, keywords in self.INSURANCE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return ins_type

        return InsuranceType.UNKNOWN

    def _extract_disease_names(self, text: str) -> List[str]:
        """Extract disease names from text"""
        found_names = []

        for disease_name in self.DISEASE_KCD_MAP.keys():
            if disease_name in text:
                found_names.append(disease_name)

        return list(set(found_names))  # Deduplicate

    def _link_disease_name(self, disease_name: str) -> Optional[LinkedEntity]:
        """Link disease name to KCD codes"""
        kcd_codes = self.DISEASE_KCD_MAP.get(disease_name)

        if kcd_codes:
            return LinkedEntity(
                original_value=disease_name,
                normalized_value=disease_name,
                entity_type="disease_name",
                category="kcd_mapping",
                metadata={"kcd_codes": kcd_codes},
            )

        return None


# Singleton instance
_entity_linker: Optional[EntityLinker] = None


def get_entity_linker() -> EntityLinker:
    """Get or create singleton entity linker instance"""
    global _entity_linker
    if _entity_linker is None:
        _entity_linker = EntityLinker()
    return _entity_linker


if __name__ == "__main__":
    # Test entity linker
    from app.services.critical_data_extractor import get_critical_extractor

    sample_text = """제10조 [암보험금 지급]
① 회사는 피보험자가 보험기간 중 암으로 진단 확정되었을 때 다음과 같이 보험금을 지급합니다.
1. 일반암(C77 제외): 1억원
2. 소액암(C77): 1천만원
3. 유사암(D00-D09): 500만원

제11조 [심근경색 진단 시]
① 심근경색(I21)으로 진단 확정 시 3천만원을 지급합니다.

제12조 [뇌졸중 진단 시]
① 뇌출혈(I60-I62) 또는 뇌경색(I63)으로 진단 시 3천만원을 지급합니다.
"""

    print("=" * 70)
    print("🧪 Entity Linker Test")
    print("=" * 70)

    # Extract data
    print("\n📊 Extracting entities...")
    extractor = get_critical_extractor()
    extracted = extractor.extract_all(sample_text)

    print(f"  Found: {len(extracted.kcd_codes)} KCD codes")
    for kcd in extracted.kcd_codes:
        print(f"    - {kcd.code}")

    # Link entities
    print("\n🔗 Linking entities...")
    linker = get_entity_linker()
    result = linker.link_entities(
        extracted_data=extracted,
        policy_name="암보험 약관",
        full_text=sample_text,
    )

    print(f"\n✅ Linked {result.total_linked} entities")

    print(f"\n📋 Linked Entities:")
    for entity in result.linked_entities:
        print(f"  - {entity.original_value} → {entity.normalized_value} ({entity.entity_type})")
        if entity.category:
            print(f"    Category: {entity.category}")
        if entity.metadata:
            print(f"    Metadata: {entity.metadata}")

    print(f"\n🏥 Insurance Types Detected:")
    for ins_type in result.insurance_types:
        print(f"  - {ins_type.value}")

    print(f"\n🦠 Disease Categories:")
    for category in result.disease_categories:
        print(f"  - {category.value}")

    print("\n" + "=" * 70)
    print("✅ Entity linker test complete!")
    print("=" * 70)
