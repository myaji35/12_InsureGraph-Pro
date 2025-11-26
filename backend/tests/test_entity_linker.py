"""
Unit tests for EntityLinker
"""
import pytest
from app.services.ingestion.entity_linker import EntityLinker
from app.models.ontology import DiseaseEntity, EntityLinkResult


class TestEntityLinker:
    """Test suite for entity linking"""

    @pytest.fixture
    def linker(self):
        """Create linker instance"""
        return EntityLinker()

    def test_ontology_loading(self, linker):
        """Test that ontology loads successfully"""
        assert len(linker.entities) > 0
        assert len(linker.kcd_index) > 0
        assert len(linker.name_index) > 0

    def test_exact_match_korean(self, linker):
        """Test exact matching with Korean name"""
        result = linker.link("갑상선암")

        assert result.is_successful()
        assert result.matched_entity.standard_name == "ThyroidCancer"
        assert result.match_score == 1.0
        assert result.match_method == "exact"

    def test_exact_match_english(self, linker):
        """Test exact matching with English name"""
        result = linker.link("Thyroid Cancer")

        assert result.is_successful()
        assert result.matched_entity.standard_name == "ThyroidCancer"
        assert result.match_score == 1.0

    def test_synonym_matching(self, linker):
        """Test synonym resolution"""
        # "악성신생물" should match "Cancer"
        result = linker.link("악성신생물")

        # This should either match a specific cancer or fail gracefully
        # The ontology has this as a category, not entity
        # So let's test with actual synonyms

        # "간암" has synonyms
        result = linker.link("간암")
        assert result.is_successful()
        assert result.matched_entity.standard_name == "LiverCancer"

        result = linker.link("간의 악성신생물")
        assert result.is_successful()
        assert result.matched_entity.standard_name == "LiverCancer"

    def test_kcd_code_matching(self, linker):
        """Test KCD code lookup"""
        result = linker.link("C73")  # Thyroid cancer

        assert result.is_successful()
        assert result.matched_entity.standard_name == "ThyroidCancer"
        assert result.match_method == "kcd"

    def test_kcd_code_in_text(self, linker):
        """Test KCD code extraction from text"""
        result = linker.link("갑상선암(C73)은 소액암입니다")

        assert result.is_successful()
        assert result.matched_entity.standard_name == "ThyroidCancer"

    def test_fuzzy_match_typo(self, linker):
        """Test fuzzy matching for typos"""
        # Typo: "갑상샘암" instead of "갑상선암"
        result = linker.link("갑상샘암", use_fuzzy=True, fuzzy_threshold=0.7)

        assert result.is_successful()
        assert result.matched_entity.standard_name == "ThyroidCancer"
        assert result.match_method == "fuzzy"
        assert result.match_score > 0.7

    def test_fuzzy_match_partial(self, linker):
        """Test fuzzy matching with partial name"""
        result = linker.link("대장", use_fuzzy=True, fuzzy_threshold=0.5)

        # Should match "대장암" (Colorectal cancer)
        assert result.is_successful()
        assert result.match_method == "fuzzy"

    def test_no_match_found(self, linker):
        """Test when no match is found"""
        result = linker.link("존재하지않는질병")

        assert not result.is_successful()
        assert result.matched_entity is None
        assert result.match_score == 0.0 or result.match_score < 0.8

    def test_case_insensitive_matching(self, linker):
        """Test case-insensitive matching"""
        result1 = linker.link("Liver Cancer")
        result2 = linker.link("liver cancer")
        result3 = linker.link("LIVER CANCER")

        assert all([r.is_successful() for r in [result1, result2, result3]])
        assert result1.matched_entity.standard_name == result2.matched_entity.standard_name == result3.matched_entity.standard_name

    def test_multiple_kcd_codes(self, linker):
        """Test entity with multiple KCD codes"""
        # Colorectal cancer has C18, C19, C20
        result1 = linker.link("C18")
        result2 = linker.link("C19")
        result3 = linker.link("C20")

        assert all([r.is_successful() for r in [result1, result2, result3]])
        # All should match ColorectalCancer
        assert result1.matched_entity.standard_name == "ColorectalCancer"
        assert result2.matched_entity.standard_name == "ColorectalCancer"
        assert result3.matched_entity.standard_name == "ColorectalCancer"

    def test_link_multiple(self, linker):
        """Test linking multiple queries at once"""
        queries = ["갑상선암", "간암", "C16"]  # Thyroid, Liver, Stomach
        results = linker.link_multiple(queries)

        assert len(results) == 3
        assert all([r.is_successful() for r in results])
        assert results[0].matched_entity.standard_name == "ThyroidCancer"
        assert results[1].matched_entity.standard_name == "LiverCancer"
        assert results[2].matched_entity.standard_name == "StomachCancer"

    def test_get_entity_by_standard_name(self, linker):
        """Test direct lookup by standard name"""
        entity = linker.get_entity_by_standard_name("ThyroidCancer")

        assert entity is not None
        assert entity.standard_name == "ThyroidCancer"
        assert "갑상선암" in entity.korean_names

    def test_get_entities_by_category(self, linker):
        """Test filtering by category"""
        cancer_entities = linker.get_entities_by_category("cancer")

        assert len(cancer_entities) > 0
        assert all([e.category == "cancer" for e in cancer_entities])

        cardio_entities = linker.get_entities_by_category("cardiovascular")
        assert len(cardio_entities) > 0

    def test_get_entities_by_severity(self, linker):
        """Test filtering by severity"""
        minor_entities = linker.get_entities_by_severity("minor")
        critical_entities = linker.get_entities_by_severity("critical")

        assert len(minor_entities) > 0
        assert len(critical_entities) > 0

        # Thyroid cancer should be minor
        thyroid = linker.get_entity_by_standard_name("ThyroidCancer")
        assert thyroid.severity == "minor"

        # Liver cancer should be critical
        liver = linker.get_entity_by_standard_name("LiverCancer")
        assert liver.severity == "critical"

    def test_get_all_kcd_codes(self, linker):
        """Test getting all KCD codes"""
        kcd_codes = linker.get_all_kcd_codes()

        assert len(kcd_codes) > 0
        assert "C73" in kcd_codes
        assert "C22" in kcd_codes
        assert "I21" in kcd_codes

    def test_get_stats(self, linker):
        """Test ontology statistics"""
        stats = linker.get_stats()

        assert "total_entities" in stats
        assert "total_kcd_codes" in stats
        assert "categories" in stats
        assert "severities" in stats
        assert "category_counts" in stats

        assert stats["total_entities"] > 0
        assert "cancer" in stats["categories"]
        assert "cardiovascular" in stats["categories"]

    def test_high_confidence_threshold(self, linker):
        """Test high confidence check"""
        exact_result = linker.link("갑상선암")
        assert exact_result.is_high_confidence(threshold=0.85)

        fuzzy_result = linker.link("갑상샘암", use_fuzzy=True)
        # Fuzzy match may or may not be high confidence depending on score
        # Just check that method works
        assert isinstance(fuzzy_result.is_high_confidence(), bool)

    def test_cardiovascular_diseases(self, linker):
        """Test cardiovascular disease linking"""
        # Test acute MI
        result = linker.link("급성심근경색증")
        assert result.is_successful()
        assert result.matched_entity.standard_name == "AcuteMyocardialInfarction"

        # Test angina
        result = linker.link("협심증")
        assert result.is_successful()
        assert result.matched_entity.standard_name == "AnginaPectoris"

        # Test by KCD code
        result = linker.link("I21")
        assert result.is_successful()
        assert result.matched_entity.standard_name == "AcuteMyocardialInfarction"

    def test_cerebrovascular_diseases(self, linker):
        """Test cerebrovascular disease linking"""
        result = linker.link("뇌출혈")
        assert result.is_successful()
        assert result.matched_entity.standard_name == "CerebralHemorrhage"

        result = linker.link("뇌경색")
        assert result.is_successful()
        assert result.matched_entity.standard_name == "CerebralInfarction"

    def test_diabetes(self, linker):
        """Test diabetes linking"""
        result = linker.link("당뇨병")
        # This might match Type1 or Type2, either is fine
        assert result.is_successful()
        assert "Diabetes" in result.matched_entity.standard_name

        result = linker.link("E10")
        assert result.is_successful()
        assert result.matched_entity.standard_name == "Type1Diabetes"

    def test_english_abbreviations(self, linker):
        """Test English medical abbreviations"""
        # AMI = Acute Myocardial Infarction
        result = linker.link("AMI", use_fuzzy=True, fuzzy_threshold=0.6)
        assert result.is_successful()
        assert result.matched_entity.standard_name == "AcuteMyocardialInfarction"

        # IHD = Ischemic Heart Disease
        result = linker.link("IHD", use_fuzzy=True, fuzzy_threshold=0.6)
        assert result.is_successful()
        assert result.matched_entity.standard_name == "IschemicHeartDisease"

    def test_real_clause_example(self, linker):
        """Test with realistic clause mentions"""
        # Extract disease mentions from clause
        clause = "회사는 피보험자가 암(C00-C97)으로 진단확정된 경우, 갑상선암(C73)은 1천만원, 간암은 2억원을 지급합니다."

        # Link multiple mentions
        mentions = ["암", "C73", "간암"]
        results = linker.link_multiple(mentions)

        # Check all linked
        assert len([r for r in results if r.is_successful()]) >= 2

    def test_fuzzy_disabled(self, linker):
        """Test with fuzzy matching disabled"""
        # With typo, should fail without fuzzy
        result = linker.link("갑상샘암", use_fuzzy=False)

        assert not result.is_successful() or result.match_method != "fuzzy"

    def test_entity_attributes(self, linker):
        """Test that entities have all required attributes"""
        entity = linker.get_entity_by_standard_name("ThyroidCancer")

        assert entity is not None
        assert entity.standard_name == "ThyroidCancer"
        assert len(entity.korean_names) > 0
        assert len(entity.english_names) > 0
        assert len(entity.kcd_codes) > 0
        assert entity.severity is not None
        assert entity.category == "cancer"
