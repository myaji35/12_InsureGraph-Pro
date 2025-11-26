"""
Unit tests for RelationExtractor

Uses mocks for LLM API calls since we can't make real API calls in tests
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.ingestion.relation_extractor import RelationExtractor
from app.models.critical_data import CriticalData, AmountData, PeriodData, KCDCodeData
from app.models.relation import ExtractedRelation


class TestRelationExtractor:
    """Test suite for relation extraction"""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance"""
        return RelationExtractor()

    @pytest.fixture
    def sample_critical_data(self):
        """Sample critical data for testing"""
        return CriticalData(
            amounts=[
                AmountData(value=100000000, original_text="1억원", position=50, confidence=1.0),
                AmountData(value=10000000, original_text="1천만원", position=80, confidence=1.0),
            ],
            periods=[
                PeriodData(days=90, original_text="90일", original_unit="일", position=120, confidence=1.0),
            ],
            kcd_codes=[
                KCDCodeData(code="C77", original_text="C77", position=30, is_valid=True, is_range=False),
                KCDCodeData(code="C00-C97", original_text="C00-C97", position=10, is_valid=True, is_range=True,
                           start_code="C00", end_code="C97"),
            ],
        )

    @pytest.fixture
    def mock_llm_response_valid(self):
        """Valid LLM response"""
        return {
            "text": '''
```json
{
  "relations": [
    {
      "subject": "암진단특약",
      "action": "COVERS",
      "object": "일반암",
      "conditions": [
        {"type": "waiting_period", "value": 90, "description": "계약일로부터 90일"},
        {"type": "payment_amount", "value": 100000000, "description": "1억원"}
      ],
      "confidence": 0.95,
      "reasoning": "제10조 ①항에서 명시",
      "source_clause_text": "Test clause"
    },
    {
      "subject": "암진단특약",
      "action": "EXCLUDES",
      "object": "소액암(C77)",
      "conditions": [
        {"type": "payment_amount", "value": 10000000, "description": "1천만원"}
      ],
      "confidence": 0.92,
      "reasoning": "제10조 ②항에서 명시",
      "source_clause_text": "Test clause"
    }
  ]
}
```
            ''',
            "model": "solar-pro",
            "confidence": 0.90,
        }

    @pytest.mark.asyncio
    async def test_extract_with_valid_response(self, extractor, sample_critical_data, mock_llm_response_valid):
        """Test extraction with valid LLM response"""
        # Mock the LLM client
        with patch.object(extractor.upstage_client, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_llm_response_valid

            clause_text = "회사는 피보험자가 암으로 진단확정된 경우 1억원을 지급합니다."
            result = await extractor.extract(clause_text, sample_critical_data, use_cascade=False)

            # Check result
            assert len(result.relations) == 2
            assert result.llm_model == "solar-pro"
            assert result.extraction_confidence > 0.8
            assert result.validation_passed

            # Check first relation
            rel1 = result.relations[0]
            assert rel1.subject == "암진단특약"
            assert rel1.action == "COVERS"
            assert rel1.object == "일반암"
            assert len(rel1.conditions) == 2

    @pytest.mark.asyncio
    async def test_cascade_on_low_confidence(self, extractor, sample_critical_data):
        """Test cascade to GPT-4o when Solar Pro confidence is low"""
        # Mock Solar Pro with low confidence
        solar_response = {
            "text": '''{"relations": [{"subject": "test", "action": "COVERS", "object": "test",
                        "conditions": [], "confidence": 0.5, "reasoning": "unclear"}]}''',
            "model": "solar-pro",
            "confidence": 0.65,  # Below retry threshold
        }

        # Mock GPT-4o with high confidence
        gpt_response = {
            "text": '''{"relations": [{"subject": "암진단특약", "action": "COVERS", "object": "일반암",
                        "conditions": [{"type": "payment_amount", "value": 100000000, "description": "1억원"}],
                        "confidence": 0.95, "reasoning": "clear"}]}''',
            "model": "gpt-4o",
            "confidence": 0.90,
        }

        with patch.object(extractor.upstage_client, 'generate', new_callable=AsyncMock) as mock_solar, \
             patch.object(extractor.openai_client, 'generate', new_callable=AsyncMock) as mock_gpt:

            mock_solar.return_value = solar_response
            mock_gpt.return_value = gpt_response

            clause_text = "Test clause"
            result = await extractor.extract(clause_text, sample_critical_data, use_cascade=True)

            # Should have called both Solar and GPT
            assert mock_solar.call_count == 1
            assert mock_gpt.call_count == 1

            # Should use GPT response
            assert result.llm_model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_validation_override_period(self, extractor, sample_critical_data, mock_llm_response_valid):
        """Test validation overrides LLM period with rule-based value"""
        # Modify mock response to have wrong period
        wrong_response = mock_llm_response_valid.copy()
        wrong_response["text"] = '''
{
  "relations": [
    {
      "subject": "test",
      "action": "COVERS",
      "object": "test",
      "conditions": [{"type": "waiting_period", "value": 60, "description": "60일"}],
      "confidence": 0.95,
      "reasoning": "test"
    }
  ]
}
        '''

        with patch.object(extractor.upstage_client, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = wrong_response

            result = await extractor.extract("Test", sample_critical_data, use_cascade=False)

            # Should have warning about override
            assert len(result.validation_warnings) > 0
            assert "Override" in result.validation_warnings[0]

            # Value should be overridden to 90 (from critical_data)
            assert result.relations[0].conditions[0].value == 90

    @pytest.mark.asyncio
    async def test_validation_override_amount(self, extractor, sample_critical_data, mock_llm_response_valid):
        """Test validation overrides LLM amount with rule-based value"""
        # Modify mock response to have close but wrong amount
        wrong_response = mock_llm_response_valid.copy()
        wrong_response["text"] = '''
{
  "relations": [
    {
      "subject": "test",
      "action": "COVERS",
      "object": "test",
      "conditions": [{"type": "payment_amount", "value": 105000000, "description": "1억 5백만원"}],
      "confidence": 0.95,
      "reasoning": "test"
    }
  ]
}
        '''

        with patch.object(extractor.upstage_client, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = wrong_response

            result = await extractor.extract("Test", sample_critical_data, use_cascade=False)

            # Should have warning about override
            assert len(result.validation_warnings) > 0

            # Value should be overridden to closest match (100000000)
            assert result.relations[0].conditions[0].value == 100000000

    @pytest.mark.asyncio
    async def test_parse_json_with_markdown(self, extractor, sample_critical_data):
        """Test parsing JSON wrapped in markdown code blocks"""
        response_with_markdown = {
            "text": '''
Here is the JSON:
```json
{
  "relations": [
    {"subject": "test", "action": "COVERS", "object": "test", "conditions": [],
     "confidence": 0.9, "reasoning": "test"}
  ]
}
```
            ''',
            "model": "solar-pro",
            "confidence": 0.90,
        }

        with patch.object(extractor.upstage_client, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = response_with_markdown

            result = await extractor.extract("Test", sample_critical_data, use_cascade=False)

            assert len(result.relations) == 1

    @pytest.mark.asyncio
    async def test_invalid_json_response(self, extractor, sample_critical_data):
        """Test handling of invalid JSON response"""
        invalid_response = {
            "text": "This is not JSON at all",
            "model": "solar-pro",
            "confidence": 0.90,
        }

        with patch.object(extractor.upstage_client, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = invalid_response

            result = await extractor.extract("Test", sample_critical_data, use_cascade=False)

            assert len(result.relations) == 0
            assert not result.validation_passed
            assert len(result.validation_errors) > 0
            assert "parse" in result.validation_errors[0].lower()

    @pytest.mark.asyncio
    async def test_no_relations_found(self, extractor, sample_critical_data):
        """Test when LLM returns no relations"""
        empty_response = {
            "text": '{"relations": []}',
            "model": "solar-pro",
            "confidence": 0.90,
        }

        with patch.object(extractor.upstage_client, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = empty_response

            result = await extractor.extract("Test", sample_critical_data, use_cascade=False)

            assert len(result.relations) == 0
            assert result.extraction_confidence == 0.0

    @pytest.mark.asyncio
    async def test_multiple_relation_actions(self, extractor, sample_critical_data):
        """Test extraction of different relation types"""
        multi_action_response = {
            "text": '''
{
  "relations": [
    {"subject": "암특약", "action": "COVERS", "object": "일반암", "conditions": [],
     "confidence": 0.9, "reasoning": "test"},
    {"subject": "암특약", "action": "EXCLUDES", "object": "C77", "conditions": [],
     "confidence": 0.9, "reasoning": "test"},
    {"subject": "암특약", "action": "REQUIRES", "object": "90일 면책", "conditions": [],
     "confidence": 0.9, "reasoning": "test"}
  ]
}
            ''',
            "model": "solar-pro",
            "confidence": 0.90,
        }

        with patch.object(extractor.upstage_client, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = multi_action_response

            result = await extractor.extract("Test", sample_critical_data, use_cascade=False)

            assert len(result.relations) == 3

            # Check we have all action types
            actions = [r.action for r in result.relations]
            assert "COVERS" in actions
            assert "EXCLUDES" in actions
            assert "REQUIRES" in actions

    @pytest.mark.asyncio
    async def test_confidence_calculation(self, extractor, sample_critical_data, mock_llm_response_valid):
        """Test overall confidence calculation"""
        with patch.object(extractor.upstage_client, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_llm_response_valid

            result = await extractor.extract("Test", sample_critical_data, use_cascade=False)

            # Confidence should be between 0 and 1
            assert 0.0 <= result.extraction_confidence <= 1.0

            # Should have high confidence for valid response
            assert result.extraction_confidence > 0.85

    @pytest.mark.asyncio
    async def test_requires_review_flag(self, extractor, sample_critical_data):
        """Test requires_review flag for low confidence or validation errors"""
        low_confidence_response = {
            "text": '''
{
  "relations": [
    {"subject": "test", "action": "COVERS", "object": "test", "conditions": [],
     "confidence": 0.6, "reasoning": "unclear"}
  ]
}
            ''',
            "model": "solar-pro",
            "confidence": 0.65,
        }

        with patch.object(extractor.upstage_client, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = low_confidence_response

            result = await extractor.extract("Test", sample_critical_data, use_cascade=False)

            # Should require review due to low confidence
            assert result.requires_review()

    @pytest.mark.asyncio
    async def test_real_clause_example(self, extractor, sample_critical_data):
        """Test with realistic clause text"""
        real_clause = """
        회사는 피보험자가 보험기간 중 암(C00-C97)으로 진단확정되었을 때
        다음 각 호의 암진단급여금을 지급합니다.
        1. 일반암(C77 제외): 1억원
        2. 소액암(C77): 1천만원
        다만, 계약일로부터 90일 이내에 진단확정된 경우는 보험금을 지급하지 않습니다.
        """

        realistic_response = {
            "text": '''
{
  "relations": [
    {
      "subject": "암진단급여금",
      "action": "COVERS",
      "object": "일반암(C77 제외)",
      "conditions": [
        {"type": "payment_amount", "value": 100000000, "description": "1억원"},
        {"type": "waiting_period", "value": 90, "description": "계약일로부터 90일"}
      ],
      "confidence": 0.95,
      "reasoning": "조항에서 명시적으로 보장 내용과 금액, 면책기간 기술"
    },
    {
      "subject": "암진단급여금",
      "action": "COVERS",
      "object": "소액암(C77)",
      "conditions": [
        {"type": "payment_amount", "value": 10000000, "description": "1천만원"}
      ],
      "confidence": 0.93,
      "reasoning": "소액암에 대한 별도 보장 금액 명시"
    },
    {
      "subject": "암진단급여금",
      "action": "EXCLUDES",
      "object": "90일 이내 진단",
      "conditions": [
        {"type": "waiting_period", "value": 90, "description": "계약일로부터 90일 이내"}
      ],
      "confidence": 0.94,
      "reasoning": "다만 조항에서 면책 조건 명시"
    }
  ]
}
            ''',
            "model": "solar-pro",
            "confidence": 0.92,
        }

        with patch.object(extractor.upstage_client, 'generate', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = realistic_response

            result = await extractor.extract(real_clause, sample_critical_data, use_cascade=False)

            # Should extract 3 relations
            assert len(result.relations) == 3

            # Should have high confidence
            assert result.extraction_confidence > 0.85

            # Should pass validation
            assert result.validation_passed

            # Check relation types
            covers_relations = result.get_relations_by_action("COVERS")
            excludes_relations = result.get_relations_by_action("EXCLUDES")
            assert len(covers_relations) == 2
            assert len(excludes_relations) == 1
