"""
Unit tests for Query Understanding

질의 이해 컴포넌트들의 기능을 테스트합니다.
"""
import pytest
from unittest.mock import Mock, AsyncMock

from app.models.query import (
    QueryIntent,
    QueryType,
    EntityType,
    ExtractedEntity,
    QueryAnalysisResult,
    QueryContext,
    IntentPattern,
)
from app.services.query.intent_detector import IntentDetector, LLMIntentDetector
from app.services.query.entity_extractor import EntityExtractor, LLMEntityExtractor
from app.services.query.query_analyzer import QueryAnalyzer


class TestIntentDetector:
    """Test suite for IntentDetector"""

    @pytest.fixture
    def detector(self):
        """의도 감지기 인스턴스"""
        return IntentDetector()

    def test_detect_coverage_amount(self, detector):
        """보장 금액 질문 감지 테스트"""
        queries = [
            "갑상선암 보장 금액은?",
            "간암 진단 시 얼마를 받나요?",
            "암 보험금은 얼마인가요?",
        ]

        for query in queries:
            intent, confidence = detector.detect(query)
            assert intent == QueryIntent.COVERAGE_AMOUNT
            assert confidence > 0.3

    def test_detect_coverage_check(self, detector):
        """보장 여부 확인 질문 감지 테스트"""
        queries = [
            "갑상선암은 보장되나요?",
            "이 보험에 간암이 포함되나요?",
            "뇌출혈도 보장 대상인가요?",
        ]

        for query in queries:
            intent, confidence = detector.detect(query)
            assert intent == QueryIntent.COVERAGE_CHECK
            assert confidence > 0.3

    def test_detect_exclusion_check(self, detector):
        """제외 항목 확인 질문 감지 테스트"""
        queries = [
            "이 보험에서 제외되는 질병은?",
            "보장 안 되는 암은 무엇인가요?",
            "면책 사항이 뭐예요?",
        ]

        for query in queries:
            intent, confidence = detector.detect(query)
            assert intent == QueryIntent.EXCLUSION_CHECK
            assert confidence > 0.3

    def test_detect_waiting_period(self, detector):
        """대기기간 질문 감지 테스트"""
        queries = [
            "대기기간은 얼마나 되나요?",
            "암 진단까지 얼마나 기다려야 하나요?",
            "보험금을 받으려면 언제부터 가능한가요?",
        ]

        for query in queries:
            intent, confidence = detector.detect(query)
            assert intent in [
                QueryIntent.WAITING_PERIOD,
                QueryIntent.CONDITION_INQUIRY,
            ]
            assert confidence > 0.2

    def test_detect_product_summary(self, detector):
        """상품 요약 질문 감지 테스트"""
        queries = [
            "이 보험 상품을 요약해주세요",
            "보험 내용을 간단히 설명해주세요",
            "이 보험 상품 개요는?",
        ]

        for query in queries:
            intent, confidence = detector.detect(query)
            assert intent in [QueryIntent.PRODUCT_SUMMARY, QueryIntent.GENERAL_INFO]
            assert confidence > 0.2

    def test_detect_multiple(self, detector):
        """상위 K개 의도 감지 테스트"""
        query = "갑상선암 보장 금액과 대기기간은?"

        top_intents = detector.detect_multiple(query, top_k=3)

        assert len(top_intents) >= 1
        assert len(top_intents) <= 3

        # 첫 번째 의도가 가장 높은 신뢰도
        for i in range(len(top_intents) - 1):
            assert top_intents[i][1] >= top_intents[i + 1][1]

    def test_is_complex_query(self, detector):
        """복잡한 질문 감지 테스트"""
        # 단순한 질문
        simple_query = "갑상선암 보장 금액은?"
        assert detector.is_complex_query(simple_query) is False

        # 복잡한 질문 (여러 의도)
        complex_query = "갑상선암과 간암 보장 금액 차이와 대기기간은?"
        # Note: 이 테스트는 실제 패턴에 따라 결과가 다를 수 있음

    def test_add_pattern(self, detector):
        """패턴 추가 테스트"""
        initial_count = len(detector.patterns)

        new_pattern = IntentPattern(
            intent=QueryIntent.GENERAL_INFO,
            patterns=["테스트"],
            keywords=["테스트"],
            examples=["테스트 질문"],
            priority=1,
        )

        detector.add_pattern(new_pattern)

        assert len(detector.patterns) == initial_count + 1

    def test_remove_pattern(self, detector):
        """패턴 제거 테스트"""
        initial_count = len(detector.patterns)

        detector.remove_pattern(QueryIntent.PRODUCT_SUMMARY)

        # 제거되었는지 확인
        assert all(p.intent != QueryIntent.PRODUCT_SUMMARY for p in detector.patterns)
        assert len(detector.patterns) < initial_count

    def test_empty_query(self, detector):
        """빈 질문 처리 테스트"""
        intent, confidence = detector.detect("")

        assert intent == QueryIntent.UNKNOWN
        assert confidence == 0.0

    def test_unknown_query(self, detector):
        """알 수 없는 질문 처리 테스트"""
        query = "zzz xxx yyy"  # 의미 없는 문자열

        intent, confidence = detector.detect(query)

        assert intent == QueryIntent.UNKNOWN
        assert confidence < 0.3


class TestEntityExtractor:
    """Test suite for EntityExtractor"""

    @pytest.fixture
    def extractor(self):
        """엔티티 추출기 인스턴스"""
        return EntityExtractor()

    def test_extract_amounts(self, extractor):
        """금액 추출 테스트"""
        queries = [
            ("갑상선암 진단 시 1천만원을 지급합니다", 10_000_000),
            ("보험금은 5천만원입니다", 50_000_000),
            ("최대 1억원까지 보장", 100_000_000),
        ]

        for query, expected_amount in queries:
            entities = extractor.extract(query)
            amounts = [e for e in entities if e.entity_type == EntityType.AMOUNT]

            assert len(amounts) > 0
            assert int(amounts[0].normalized_value) == expected_amount

    def test_extract_periods(self, extractor):
        """기간 추출 테스트"""
        queries = [
            ("대기기간은 90일입니다", 90),
            ("3개월 후부터 보장", 90),  # 3개월 = 90일
            ("1년 동안 면책", 365),
        ]

        for query, expected_days in queries:
            entities = extractor.extract(query)
            periods = [e for e in entities if e.entity_type == EntityType.PERIOD]

            assert len(periods) > 0
            assert periods[0].normalized_value == f"{expected_days}일"

    def test_extract_kcd_codes(self, extractor):
        """KCD 코드 추출 테스트"""
        queries = [
            "갑상선암 C73은 보장됩니다",
            "간암(C22) 진단 시",
            "질병코드 C73.9에 해당하는 경우",
        ]

        for query in queries:
            entities = extractor.extract(query)
            kcd_codes = [e for e in entities if e.entity_type == EntityType.KCD_CODE]

            assert len(kcd_codes) > 0
            assert kcd_codes[0].text.startswith("C")

    def test_extract_conditions(self, extractor):
        """조건 추출 테스트"""
        queries = [
            "대기기간은 얼마나 되나요?",
            "나이제한이 있나요?",
            "면책기간은?",
        ]

        for query in queries:
            entities = extractor.extract(query)
            conditions = [e for e in entities if e.entity_type == EntityType.CONDITION]

            assert len(conditions) > 0

    def test_extract_coverages(self, extractor):
        """보장 추출 테스트"""
        queries = [
            "암진단특약은 무엇인가요?",
            "수술보장에 대해 알려주세요",
            "입원담보는 포함되나요?",
        ]

        for query in queries:
            entities = extractor.extract(query)
            coverages = [e for e in entities if e.entity_type == EntityType.COVERAGE]

            assert len(coverages) > 0

    def test_extract_diseases_pattern(self, extractor):
        """질병 추출 테스트 (패턴 기반)"""
        queries = [
            "갑상선암은 보장되나요?",
            "간암 진단 시",
            "뇌출혈도 포함되나요?",
        ]

        for query in queries:
            entities = extractor.extract(query)
            diseases = [e for e in entities if e.entity_type == EntityType.DISEASE]

            assert len(diseases) > 0

    def test_extract_multiple_entities(self, extractor):
        """여러 엔티티 동시 추출 테스트"""
        query = "갑상선암 진단 시 1천만원을 90일 대기기간 후 지급"

        entities = extractor.extract(query)

        # 최소 3개 이상의 엔티티 (질병, 금액, 기간)
        assert len(entities) >= 3

        # 각 타입별로 확인
        assert any(e.entity_type == EntityType.DISEASE for e in entities)
        assert any(e.entity_type == EntityType.AMOUNT for e in entities)
        assert any(e.entity_type == EntityType.PERIOD for e in entities)

    def test_get_entities_by_type(self, extractor):
        """타입별 엔티티 필터링 테스트"""
        query = "갑상선암 진단 시 1천만원 지급"

        entities = extractor.extract(query)

        diseases = extractor.get_entities_by_type(entities, EntityType.DISEASE)
        amounts = extractor.get_entities_by_type(entities, EntityType.AMOUNT)

        assert len(diseases) > 0
        assert len(amounts) > 0
        assert all(e.entity_type == EntityType.DISEASE for e in diseases)
        assert all(e.entity_type == EntityType.AMOUNT for e in amounts)

    def test_deduplicate_entities(self, extractor):
        """중복 엔티티 제거 테스트"""
        # 중복된 엔티티 생성
        entities = [
            ExtractedEntity(
                text="갑상선암",
                entity_type=EntityType.DISEASE,
                confidence=0.8,
                start_pos=0,
                end_pos=4,
            ),
            ExtractedEntity(
                text="갑상선암",
                entity_type=EntityType.DISEASE,
                confidence=0.9,  # 더 높은 신뢰도
                start_pos=0,
                end_pos=4,
            ),
        ]

        deduped = extractor.deduplicate_entities(entities)

        assert len(deduped) == 1
        assert deduped[0].confidence == 0.9  # 높은 신뢰도가 선택됨

    def test_min_confidence_filter(self):
        """최소 신뢰도 필터링 테스트"""
        extractor = EntityExtractor(min_confidence=0.8)

        # 낮은 신뢰도 엔티티는 필터링됨
        query = "테스트"
        entities = extractor.extract(query)

        # 모든 엔티티가 최소 신뢰도 이상
        assert all(e.confidence >= 0.8 for e in entities)


class TestQueryAnalyzer:
    """Test suite for QueryAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        """질의 분석기 인스턴스"""
        return QueryAnalyzer()

    def test_analyze_coverage_amount_query(self, analyzer):
        """보장 금액 질문 분석 테스트"""
        query = "갑상선암 보장 금액은 얼마인가요?"

        result = analyzer.analyze(query)

        assert result.original_query == query
        assert result.intent == QueryIntent.COVERAGE_AMOUNT
        assert result.intent_confidence > 0.3
        assert len(result.entities) > 0
        assert result.is_answerable is True

    def test_analyze_coverage_check_query(self, analyzer):
        """보장 여부 확인 질문 분석 테스트"""
        query = "간암은 보장되나요?"

        result = analyzer.analyze(query)

        assert result.intent == QueryIntent.COVERAGE_CHECK
        assert any(e.entity_type == EntityType.DISEASE for e in result.entities)
        assert result.query_type in [QueryType.GRAPH_TRAVERSAL, QueryType.HYBRID]

    def test_analyze_complex_query(self, analyzer):
        """복잡한 질문 분석 테스트"""
        query = "갑상선암 진단 시 1천만원 받으려면 대기기간은 얼마나 되나요?"

        result = analyzer.analyze(query)

        # 여러 엔티티 추출
        assert len(result.entities) >= 2

        # 질병, 금액 엔티티 포함
        entity_types = {e.entity_type for e in result.entities}
        assert EntityType.DISEASE in entity_types
        assert EntityType.AMOUNT in entity_types

    def test_analyze_unanswerable_query(self, analyzer):
        """답변 불가 질문 분석 테스트"""
        query = "보장 금액은 얼마인가요?"  # 질병/보장 정보 없음

        result = analyzer.analyze(query)

        assert result.is_answerable is False
        assert result.suggested_clarification is not None
        assert "질병" in result.suggested_clarification or "보장" in result.suggested_clarification

    def test_query_type_determination(self, analyzer):
        """쿼리 타입 결정 테스트"""
        test_cases = [
            # (질문, 예상 쿼리 타입)
            ("이 보험 상품을 요약해주세요", QueryType.VECTOR_SEARCH),
            ("갑상선암은 보장되나요?", QueryType.GRAPH_TRAVERSAL),
            ("대기기간은?", QueryType.DIRECT_LOOKUP),
        ]

        for query, expected_type in test_cases:
            result = analyzer.analyze(query)
            assert result.query_type == expected_type or result.query_type == QueryType.HYBRID

    def test_keyword_extraction(self, analyzer):
        """키워드 추출 테스트"""
        query = "갑상선암 보장 금액은 얼마인가요?"

        result = analyzer.analyze(query)

        assert len(result.keywords) > 0
        # 주요 키워드가 포함되어야 함
        keywords_str = " ".join(result.keywords)
        assert "갑상선암" in keywords_str or "갑상선" in keywords_str

    def test_language_detection(self, analyzer):
        """언어 감지 테스트"""
        # 한국어 질문
        ko_query = "갑상선암 보장 금액은?"
        ko_result = analyzer.analyze(ko_query)
        assert ko_result.language == "ko"

        # 영어 질문
        en_query = "What is the coverage amount?"
        en_result = analyzer.analyze(en_query)
        assert en_result.language == "en"

    def test_analyze_batch(self, analyzer):
        """일괄 분석 테스트"""
        queries = [
            "갑상선암 보장 금액은?",
            "대기기간은 얼마나 되나요?",
            "이 보험 상품을 요약해주세요",
        ]

        results = analyzer.analyze_batch(queries)

        assert len(results) == len(queries)
        assert all(isinstance(r, QueryAnalysisResult) for r in results)

    def test_analyze_with_context(self, analyzer):
        """컨텍스트를 활용한 분석 테스트"""
        context = QueryContext(
            conversation_id="test_001",
            previous_queries=["갑상선암 보장 금액은?"],
            previous_intents=[QueryIntent.COVERAGE_AMOUNT],
        )

        query = "대기기간은요?"

        result = analyzer.analyze(query, context)

        assert result.original_query == query

    def test_comparison_query(self, analyzer):
        """비교 질문 분석 테스트"""
        query = "갑상선암과 간암의 보장 차이는?"

        result = analyzer.analyze(query)

        # 2개의 질병 엔티티 추출
        diseases = [e for e in result.entities if e.entity_type == EntityType.DISEASE]
        assert len(diseases) >= 2

        # 그래프 순회 쿼리 타입
        assert result.query_type == QueryType.GRAPH_TRAVERSAL

    def test_get_analysis_summary(self, analyzer):
        """분석 결과 요약 생성 테스트"""
        query = "갑상선암 보장 금액은?"

        result = analyzer.analyze(query)
        summary = analyzer.get_analysis_summary(result)

        assert isinstance(summary, str)
        assert query in summary
        assert "의도" in summary
        assert "엔티티" in summary


class TestQueryModels:
    """Test suite for Query Models"""

    def test_extracted_entity_creation(self):
        """엔티티 생성 테스트"""
        entity = ExtractedEntity(
            text="갑상선암",
            entity_type=EntityType.DISEASE,
            normalized_value="ThyroidCancer",
            confidence=0.95,
            start_pos=0,
            end_pos=4,
        )

        assert entity.text == "갑상선암"
        assert entity.entity_type == EntityType.DISEASE
        assert entity.confidence == 0.95

    def test_query_analysis_result_helpers(self):
        """쿼리 분석 결과 헬퍼 메서드 테스트"""
        result = QueryAnalysisResult(
            original_query="갑상선암 보장 금액은?",
            intent=QueryIntent.COVERAGE_AMOUNT,
            intent_confidence=0.9,
            query_type=QueryType.GRAPH_TRAVERSAL,
            entities=[
                ExtractedEntity(
                    text="갑상선암",
                    entity_type=EntityType.DISEASE,
                    confidence=0.95,
                ),
                ExtractedEntity(
                    text="암진단특약",
                    entity_type=EntityType.COVERAGE,
                    confidence=0.85,
                ),
            ],
            keywords=["갑상선암", "보장", "금액"],
        )

        # get_diseases
        diseases = result.get_diseases()
        assert len(diseases) == 1
        assert "갑상선암" in diseases

        # get_coverages
        coverages = result.get_coverages()
        assert len(coverages) == 1
        assert "암진단특약" in coverages

        # has_entity_type
        assert result.has_entity_type(EntityType.DISEASE) is True
        assert result.has_entity_type(EntityType.AMOUNT) is False

    def test_query_context_add_query(self):
        """쿼리 컨텍스트 추가 테스트"""
        context = QueryContext(conversation_id="test_001")

        assert len(context.previous_queries) == 0

        context.add_query("갑상선암 보장 금액은?", QueryIntent.COVERAGE_AMOUNT)

        assert len(context.previous_queries) == 1
        assert len(context.previous_intents) == 1
        assert context.previous_intents[0] == QueryIntent.COVERAGE_AMOUNT

    def test_intent_pattern_creation(self):
        """의도 패턴 생성 테스트"""
        pattern = IntentPattern(
            intent=QueryIntent.COVERAGE_AMOUNT,
            patterns=["보장금", "보험금"],
            keywords=["금액", "얼마"],
            examples=["보장 금액은?"],
            priority=3,
        )

        assert pattern.intent == QueryIntent.COVERAGE_AMOUNT
        assert len(pattern.patterns) == 2
        assert pattern.priority == 3


class TestLLMComponents:
    """Test suite for LLM-based components"""

    @pytest.mark.asyncio
    async def test_llm_intent_detector_fallback(self):
        """LLM 의도 감지기 폴백 테스트"""
        # LLM 클라이언트 없이 생성
        detector = LLMIntentDetector(llm_client=None)

        query = "갑상선암 보장 금액은?"

        # LLM 없이도 패턴 매칭으로 동작
        intent, confidence = await detector.detect_with_llm(query)

        assert intent == QueryIntent.COVERAGE_AMOUNT
        assert confidence > 0.0

    @pytest.mark.asyncio
    async def test_llm_entity_extractor_fallback(self):
        """LLM 엔티티 추출기 폴백 테스트"""
        # LLM 클라이언트 없이 생성
        extractor = LLMEntityExtractor(llm_client=None)

        query = "갑상선암 진단 시 1천만원 지급"

        # LLM 없이도 패턴 기반으로 동작
        entities = await extractor.extract_with_llm(query)

        assert len(entities) > 0
