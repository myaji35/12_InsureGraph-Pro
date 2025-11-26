"""
Unit tests for CriticalDataExtractor
"""
import pytest
from app.services.ingestion.critical_data_extractor import CriticalDataExtractor


class TestAmountExtraction:
    """Test suite for monetary amount extraction"""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance"""
        return CriticalDataExtractor()

    def test_simple_oku(self, extractor):
        """Test: 1억원 → 100,000,000"""
        text = "보험금은 1억원입니다."
        result = extractor.extract(text)

        assert result.has_amounts()
        assert len(result.amounts) == 1
        assert result.amounts[0].value == 100000000
        assert result.amounts[0].original_text == "1억원"

    def test_multiple_oku(self, extractor):
        """Test: 2억원 → 200,000,000"""
        text = "보험금은 2억원입니다."
        result = extractor.extract(text)

        assert result.amounts[0].value == 200000000

    def test_oku_man(self, extractor):
        """Test: 1억 5만원 → 100,050,000"""
        text = "보험금은 1억 5만원입니다."
        result = extractor.extract(text)

        assert result.amounts[0].value == 100050000

    def test_man_only(self, extractor):
        """Test: 100만원 → 1,000,000"""
        text = "보험금은 100만원입니다."
        result = extractor.extract(text)

        assert result.amounts[0].value == 1000000

    def test_senman(self, extractor):
        """Test: 5천만원 → 50,000,000"""
        text = "보험금은 5천만원입니다."
        result = extractor.extract(text)

        assert result.amounts[0].value == 50000000

    def test_complex_amount(self, extractor):
        """Test: 1억 5천만원 → 150,000,000"""
        text = "보험금은 1억 5천만원입니다."
        result = extractor.extract(text)

        assert result.amounts[0].value == 150000000

    def test_small_amounts(self, extractor):
        """Test: 5천원 → 5,000"""
        text = "수수료는 5천원입니다."
        result = extractor.extract(text)

        assert result.amounts[0].value == 5000

    def test_won_only(self, extractor):
        """Test: 500원 → 500"""
        text = "수수료는 500원입니다."
        result = extractor.extract(text)

        assert result.amounts[0].value == 500

    def test_multiple_amounts_in_text(self, extractor):
        """Test multiple amounts in single text"""
        text = "일반암은 1억원, 소액암은 1천만원, 고액암은 2억원입니다."
        result = extractor.extract(text)

        assert len(result.amounts) == 3
        assert result.amounts[0].value == 100000000  # 1억원
        assert result.amounts[1].value == 10000000   # 1천만원
        assert result.amounts[2].value == 200000000  # 2억원

    def test_amount_with_comma(self, extractor):
        """Test: 1,000만원 → 10,000,000"""
        text = "보험금은 1,000만원입니다."
        result = extractor.extract(text)

        assert result.amounts[0].value == 10000000

    def test_no_amounts(self, extractor):
        """Test text with no amounts"""
        text = "이 약관은 보험금 지급에 관한 것입니다."
        result = extractor.extract(text)

        assert not result.has_amounts()
        assert len(result.amounts) == 0

    def test_amount_position_tracking(self, extractor):
        """Test that position is correctly tracked"""
        text = "일반암은 1억원입니다."
        result = extractor.extract(text)

        assert result.amounts[0].position > 0
        assert text[result.amounts[0].position:].startswith("1억원")

    def test_oku_hyakuman(self, extractor):
        """Test: 1억 5백만원 → 105,000,000"""
        text = "보험금은 1억 5백만원입니다."
        result = extractor.extract(text)

        assert result.amounts[0].value == 105000000


class TestPeriodExtraction:
    """Test suite for time period extraction"""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance"""
        return CriticalDataExtractor()

    def test_days(self, extractor):
        """Test: 90일 → 90 days"""
        text = "면책기간은 90일입니다."
        result = extractor.extract(text)

        assert result.has_periods()
        assert len(result.periods) == 1
        assert result.periods[0].days == 90
        assert result.periods[0].original_unit == "일"

    def test_months(self, extractor):
        """Test: 3개월 → 90 days"""
        text = "대기기간은 3개월입니다."
        result = extractor.extract(text)

        assert result.periods[0].days == 90
        assert result.periods[0].original_unit == "개월"

    def test_years(self, extractor):
        """Test: 1년 → 365 days"""
        text = "보험기간은 1년입니다."
        result = extractor.extract(text)

        assert result.periods[0].days == 365
        assert result.periods[0].original_unit == "년"

    def test_weeks(self, extractor):
        """Test: 2주 → 14 days"""
        text = "대기기간은 2주입니다."
        result = extractor.extract(text)

        assert result.periods[0].days == 14
        assert result.periods[0].original_unit == "주"

    def test_multiple_periods(self, extractor):
        """Test multiple periods in text"""
        text = "면책기간은 90일이며, 보험기간은 1년입니다."
        result = extractor.extract(text)

        assert len(result.periods) == 2
        assert result.periods[0].days == 90
        assert result.periods[1].days == 365

    def test_no_periods(self, extractor):
        """Test text with no periods"""
        text = "보험금을 지급합니다."
        result = extractor.extract(text)

        assert not result.has_periods()
        assert len(result.periods) == 0

    def test_period_position_tracking(self, extractor):
        """Test position tracking"""
        text = "면책기간은 90일입니다."
        result = extractor.extract(text)

        assert result.periods[0].position > 0
        assert text[result.periods[0].position:].startswith("90일")


class TestKCDCodeExtraction:
    """Test suite for KCD code extraction"""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance"""
        return CriticalDataExtractor()

    def test_single_code(self, extractor):
        """Test: C77 (thyroid cancer)"""
        text = "갑상선암(C77)은 소액암으로 분류됩니다."
        result = extractor.extract(text)

        assert result.has_kcd_codes()
        assert len(result.kcd_codes) == 1
        assert result.kcd_codes[0].code == "C77"
        assert result.kcd_codes[0].is_valid
        assert not result.kcd_codes[0].is_range

    def test_code_range_same_prefix(self, extractor):
        """Test: I21-I25 (ischemic heart disease)"""
        text = "허혈성 심질환(I21-I25)에 대해 보장합니다."
        result = extractor.extract(text)

        assert len(result.kcd_codes) == 1
        assert result.kcd_codes[0].code == "I21-I25"
        assert result.kcd_codes[0].is_range
        assert result.kcd_codes[0].start_code == "I21"
        assert result.kcd_codes[0].end_code == "I25"

    def test_code_range_different_prefix(self, extractor):
        """Test: C00-D48 (all neoplasms)"""
        text = "악성신생물(C00-D48)은 보장됩니다."
        result = extractor.extract(text)

        assert len(result.kcd_codes) == 1
        assert result.kcd_codes[0].code == "C00-D48"
        assert result.kcd_codes[0].is_range
        assert result.kcd_codes[0].start_code == "C00"
        assert result.kcd_codes[0].end_code == "D48"

    def test_multiple_codes(self, extractor):
        """Test multiple KCD codes"""
        text = "갑상선암(C77), 간암(C22), 대장암(C18-C20)을 보장합니다."
        result = extractor.extract(text)

        assert len(result.kcd_codes) == 3
        assert result.kcd_codes[0].code == "C77"
        assert result.kcd_codes[1].code == "C22"
        assert result.kcd_codes[2].code == "C18-C20"

    def test_invalid_code_prefix(self, extractor):
        """Test invalid KCD prefix"""
        text = "질병코드 X99는 유효하지 않습니다."
        result = extractor.extract(text)

        # X is valid (External causes), so test with truly invalid prefix
        text2 = "질병코드 Ø99는 유효하지 않습니다."
        result2 = extractor.extract(text2)

        # Should not match invalid patterns
        assert len(result2.kcd_codes) == 0

    def test_no_codes(self, extractor):
        """Test text with no KCD codes"""
        text = "암진단급여금을 지급합니다."
        result = extractor.extract(text)

        assert not result.has_kcd_codes()
        assert len(result.kcd_codes) == 0

    def test_code_position_tracking(self, extractor):
        """Test position tracking"""
        text = "갑상선암(C77)은 소액암입니다."
        result = extractor.extract(text)

        assert result.kcd_codes[0].position > 0
        assert text[result.kcd_codes[0].position:].startswith("C77")

    def test_common_cancer_codes(self, extractor):
        """Test common cancer KCD codes"""
        text = """
        위암(C16), 간암(C22), 대장암(C18-C20), 폐암(C34),
        유방암(C50), 갑상선암(C77), 전립선암(C61)
        """
        result = extractor.extract(text)

        assert len(result.kcd_codes) == 7
        codes = result.get_kcd_code_strings()
        assert "C16" in codes
        assert "C22" in codes
        assert "C18-C20" in codes
        assert "C34" in codes
        assert "C50" in codes
        assert "C77" in codes
        assert "C61" in codes


class TestIntegratedExtraction:
    """Test integrated extraction of all critical data types"""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance"""
        return CriticalDataExtractor()

    def test_real_clause_example_1(self, extractor):
        """Test realistic clause: cancer coverage"""
        text = """
        회사는 피보험자가 보험기간 중 암(C00-C97)으로 진단확정되었을 때
        다음 각 호의 암진단급여금을 지급합니다.
        1. 일반암(C77 제외): 1억원
        2. 소액암(C77): 1천만원
        3. 고액암(C18-C21): 2억원
        다만, 계약일로부터 90일 이내에 진단확정된 경우는 보험금을 지급하지 않습니다.
        """
        result = extractor.extract(text)

        # Check amounts
        assert len(result.amounts) == 3
        assert 100000000 in result.get_amount_values()
        assert 10000000 in result.get_amount_values()
        assert 200000000 in result.get_amount_values()

        # Check periods
        assert len(result.periods) == 1
        assert 90 in result.get_period_days()

        # Check KCD codes
        assert len(result.kcd_codes) >= 3
        codes = result.get_kcd_code_strings()
        assert "C00-C97" in codes
        assert "C77" in codes

    def test_real_clause_example_2(self, extractor):
        """Test realistic clause: cardiovascular coverage"""
        text = """
        회사는 피보험자가 다음 각 호의 질병으로 진단확정된 경우 보험금을 지급합니다.
        1. 급성심근경색증(I21-I23): 5천만원
        2. 허혈성심질환(I24-I25): 3천만원
        보험기간은 1년이며, 면책기간은 30일입니다.
        """
        result = extractor.extract(text)

        # Check amounts
        assert len(result.amounts) == 2
        assert 50000000 in result.get_amount_values()
        assert 30000000 in result.get_amount_values()

        # Check periods
        assert len(result.periods) == 2
        assert 365 in result.get_period_days()
        assert 30 in result.get_period_days()

        # Check KCD codes
        assert len(result.kcd_codes) == 2
        codes = result.get_kcd_code_strings()
        assert "I21-I23" in codes
        assert "I24-I25" in codes

    def test_empty_text(self, extractor):
        """Test empty text"""
        text = ""
        result = extractor.extract(text)

        assert not result.has_amounts()
        assert not result.has_periods()
        assert not result.has_kcd_codes()

    def test_confidence_scores(self, extractor):
        """Test that confidence is always 1.0 for rule-based extraction"""
        text = "보험금 1억원, 면책기간 90일, 암(C77)"
        result = extractor.extract(text)

        # All rule-based extractions should have confidence 1.0
        for amount in result.amounts:
            assert amount.confidence == 1.0

        for period in result.periods:
            assert period.confidence == 1.0

    def test_sorted_by_position(self, extractor):
        """Test that results are sorted by position"""
        text = "90일 면책, 1억원 지급, C77 제외"
        result = extractor.extract(text)

        # Check amounts are sorted
        if len(result.amounts) > 1:
            for i in range(len(result.amounts) - 1):
                assert result.amounts[i].position <= result.amounts[i+1].position

        # Check periods are sorted
        if len(result.periods) > 1:
            for i in range(len(result.periods) - 1):
                assert result.periods[i].position <= result.periods[i+1].position

        # Check KCD codes are sorted
        if len(result.kcd_codes) > 1:
            for i in range(len(result.kcd_codes) - 1):
                assert result.kcd_codes[i].position <= result.kcd_codes[i+1].position


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance"""
        return CriticalDataExtractor()

    def test_ambiguous_amounts(self, extractor):
        """Test: '1억원 또는 2억원'"""
        text = "보험금은 1억원 또는 2억원입니다."
        result = extractor.extract(text)

        # Should extract both
        assert len(result.amounts) == 2
        assert 100000000 in result.get_amount_values()
        assert 200000000 in result.get_amount_values()

    def test_malformed_code(self, extractor):
        """Test malformed KCD codes"""
        text = "질병코드 C7, C777, C 77은 잘못된 형식입니다."
        result = extractor.extract(text)

        # C7 and C777 should not match (need exactly 2 digits)
        # C 77 (with space) should not match
        assert len(result.kcd_codes) == 0

    def test_amount_without_won(self, extractor):
        """Test amounts without '원'"""
        text = "보험금은 1억입니다."
        result = extractor.extract(text)

        # Should still match (원 is optional in regex)
        assert len(result.amounts) == 1
        assert result.amounts[0].value == 100000000

    def test_period_in_sentence(self, extractor):
        """Test period extraction in complex sentence"""
        text = "계약일로부터 90일 이내에 진단확정된 경우, 1년 동안은 50%만 지급합니다."
        result = extractor.extract(text)

        assert len(result.periods) == 2
        assert 90 in result.get_period_days()
        assert 365 in result.get_period_days()
