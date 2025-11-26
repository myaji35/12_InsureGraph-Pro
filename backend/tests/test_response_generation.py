"""
Tests for Response Generation

Story 2.4: Response Generation 관련 테스트
"""
import pytest
from typing import List, Dict, Any

from app.models.response import (
    AnswerFormat,
    Citation,
    CitationType,
    Table,
    TableRow,
    Comparison,
    ComparisonItem,
    AnswerSegment,
    GeneratedResponse,
    ResponseTemplate,
    ResponseGenerationRequest,
    ConversationTurn,
    ConversationContext,
    ResponseQuality,
)
from app.services.response.template_manager import (
    ResponseTemplateManager,
    AdvancedTemplateRenderer,
)
from app.services.response.response_generator import ResponseGenerator


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_search_results():
    """샘플 검색 결과"""
    return [
        {
            "disease_name": "급성심근경색증",
            "coverage_name": "급성심근경색증 진단비",
            "amount": 50000000,
            "clause_id": "clause_001",
            "clause_text": "급성심근경색증 진단 시 5천만원 지급",
            "article_num": "제10조",
            "score": 0.95,
        },
        {
            "disease_name": "급성심근경색증",
            "coverage_name": "입원비",
            "amount": 1000000,
            "clause_id": "clause_002",
            "score": 0.85,
        },
    ]


@pytest.fixture
def sample_coverage_check_results():
    """보장 여부 확인 결과"""
    return [
        {
            "disease_name": "당뇨병",
            "is_covered": True,
            "coverages": [
                {"coverage_name": "당뇨병 진단비"},
                {"coverage_name": "합병증 치료비"},
            ],
        }
    ]


@pytest.fixture
def sample_comparison_results():
    """비교 결과"""
    return [
        {
            "disease1_name": "암",
            "disease2_name": "뇌졸중",
            "cov1": [
                {"name": "진단비"},
                {"name": "수술비"},
                {"name": "입원비"},
            ],
            "cov2": [
                {"name": "진단비"},
                {"name": "재활치료비"},
            ],
        }
    ]


@pytest.fixture
def template_manager():
    """템플릿 관리자"""
    return ResponseTemplateManager()


@pytest.fixture
def response_generator():
    """응답 생성기"""
    return ResponseGenerator()


# ============================================================================
# Test Response Models
# ============================================================================


class TestCitation:
    """Citation 모델 테스트"""

    def test_citation_creation(self):
        """Citation 생성"""
        citation = Citation(
            citation_type=CitationType.CLAUSE,
            source_id="clause_001",
            source_text="급성심근경색증 진단 시 지급",
            article_num="제10조",
            relevance_score=0.95,
        )

        assert citation.citation_type == CitationType.CLAUSE
        assert citation.source_id == "clause_001"
        assert citation.article_num == "제10조"
        assert citation.relevance_score == 0.95

    def test_citation_format(self):
        """Citation 포맷팅"""
        citation = Citation(
            citation_type=CitationType.CLAUSE,
            source_id="clause_001",
            source_text="Test",
            article_num="제10조",
            relevance_score=0.95,
        )

        formatted = citation.format_citation()
        assert formatted == "[제10조]"

    def test_citation_format_without_article(self):
        """조 번호 없는 Citation 포맷팅"""
        citation = Citation(
            citation_type=CitationType.CLAUSE,
            source_id="clause_001",
            source_text="Test",
            relevance_score=0.95,
        )

        formatted = citation.format_citation()
        assert formatted == "[clause:clause_001]"


class TestTable:
    """Table 모델 테스트"""

    def test_table_creation(self):
        """Table 생성"""
        table = Table(
            headers=["보장명", "금액"],
            rows=[
                TableRow(cells=["진단비", "5,000만원"]),
                TableRow(cells=["수술비", "1,000만원"]),
            ],
            caption="보장 내역",
        )

        assert len(table.headers) == 2
        assert len(table.rows) == 2
        assert table.caption == "보장 내역"

    def test_table_to_markdown(self):
        """Table을 마크다운으로 변환"""
        table = Table(
            headers=["보장명", "금액"],
            rows=[
                TableRow(cells=["진단비", "5,000만원"]),
                TableRow(cells=["수술비", "1,000만원"]),
            ],
        )

        markdown = table.to_markdown()
        assert "| 보장명 | 금액 |" in markdown
        assert "| --- | --- |" in markdown
        assert "| 진단비 | 5,000만원 |" in markdown


class TestComparison:
    """Comparison 모델 테스트"""

    def test_comparison_creation(self):
        """Comparison 생성"""
        comparison = Comparison(
            item1=ComparisonItem(name="암", attributes={"type": "질병"}),
            item2=ComparisonItem(name="뇌졸중", attributes={"type": "질병"}),
            differences=[{"text": "암은 수술비 보장"}],
            similarities=[{"text": "둘 다 진단비 보장"}],
        )

        assert comparison.item1.name == "암"
        assert comparison.item2.name == "뇌졸중"
        assert len(comparison.differences) == 1
        assert len(comparison.similarities) == 1

    def test_comparison_to_text(self):
        """Comparison을 텍스트로 변환"""
        comparison = Comparison(
            item1=ComparisonItem(name="암", attributes={}),
            item2=ComparisonItem(name="뇌졸중", attributes={}),
            differences=[{"text": "차이점1"}],
            similarities=[{"text": "공통점1"}],
        )

        text = comparison.to_text()
        assert "# 암 vs 뇌졸중" in text
        assert "## 공통점" in text
        assert "## 차이점" in text


class TestGeneratedResponse:
    """GeneratedResponse 모델 테스트"""

    def test_generated_response_creation(self):
        """GeneratedResponse 생성"""
        response = GeneratedResponse(
            answer="테스트 답변입니다.",
            format=AnswerFormat.TEXT,
            confidence_score=0.9,
        )

        assert response.answer == "테스트 답변입니다."
        assert response.format == AnswerFormat.TEXT
        assert response.confidence_score == 0.9
        assert len(response.citations) == 0

    def test_generated_response_with_table(self):
        """테이블이 있는 GeneratedResponse"""
        table = Table(
            headers=["항목", "값"],
            rows=[TableRow(cells=["A", "1"])],
        )

        response = GeneratedResponse(
            answer="테스트",
            format=AnswerFormat.TABLE,
            table=table,
            confidence_score=0.9,
        )

        assert response.table is not None
        assert len(response.table.headers) == 2

    def test_get_full_answer(self):
        """전체 답변 생성"""
        citation = Citation(
            citation_type=CitationType.CLAUSE,
            source_id="clause_001",
            source_text="Test",
            article_num="제10조",
            relevance_score=0.95,
        )

        response = GeneratedResponse(
            answer="기본 답변",
            format=AnswerFormat.TEXT,
            citations=[citation],
            follow_up_suggestions=["추가 질문1"],
            confidence_score=0.9,
        )

        full_answer = response.get_full_answer(include_citations=True)
        assert "기본 답변" in full_answer
        assert "**출처:**" in full_answer
        assert "**관련 질문:**" in full_answer

    def test_get_full_answer_without_citations(self):
        """출처 없이 전체 답변 생성"""
        response = GeneratedResponse(
            answer="기본 답변",
            format=AnswerFormat.TEXT,
            confidence_score=0.9,
        )

        full_answer = response.get_full_answer(include_citations=False)
        assert "기본 답변" in full_answer
        assert "**출처:**" not in full_answer


class TestResponseTemplate:
    """ResponseTemplate 모델 테스트"""

    def test_template_creation(self):
        """템플릿 생성"""
        template = ResponseTemplate(
            template_id="test_template",
            intent="coverage_amount",
            template="질병: {disease_name}, 금액: {amount}",
            format=AnswerFormat.TEXT,
            required_variables=["disease_name", "amount"],
        )

        assert template.template_id == "test_template"
        assert template.intent == "coverage_amount"
        assert len(template.required_variables) == 2

    def test_template_render(self):
        """템플릿 렌더링"""
        template = ResponseTemplate(
            template_id="test",
            intent="test",
            template="{name}은(는) {amount}원 보장됩니다.",
            format=AnswerFormat.TEXT,
            required_variables=["name", "amount"],
        )

        result = template.render({"name": "암", "amount": "5,000만"})
        assert result == "암은(는) 5,000만원 보장됩니다."

    def test_template_render_missing_variable(self):
        """필수 변수 누락 시 에러"""
        template = ResponseTemplate(
            template_id="test",
            intent="test",
            template="{name}은(는) {amount}원",
            format=AnswerFormat.TEXT,
            required_variables=["name", "amount"],
        )

        with pytest.raises(ValueError, match="Required variable missing"):
            template.render({"name": "암"})


class TestConversationContext:
    """ConversationContext 테스트"""

    def test_conversation_creation(self):
        """대화 컨텍스트 생성"""
        context = ConversationContext(
            conversation_id="conv_001",
            current_topic="보험",
        )

        assert context.conversation_id == "conv_001"
        assert context.current_topic == "보험"
        assert len(context.turns) == 0

    def test_add_turn(self):
        """대화 턴 추가"""
        context = ConversationContext(conversation_id="conv_001")

        response = GeneratedResponse(
            answer="답변", format=AnswerFormat.TEXT, confidence_score=0.9
        )

        context.add_turn("질문", response)

        assert len(context.turns) == 1
        assert context.turns[0].user_query == "질문"
        assert context.turns[0].turn_id == 1

    def test_get_last_turn(self):
        """마지막 턴 조회"""
        context = ConversationContext(conversation_id="conv_001")
        response = GeneratedResponse(
            answer="답변", format=AnswerFormat.TEXT, confidence_score=0.9
        )

        context.add_turn("질문1", response)
        context.add_turn("질문2", response)

        last_turn = context.get_last_turn()
        assert last_turn.user_query == "질문2"
        assert last_turn.turn_id == 2

    def test_get_recent_turns(self):
        """최근 N개 턴 조회"""
        context = ConversationContext(conversation_id="conv_001")
        response = GeneratedResponse(
            answer="답변", format=AnswerFormat.TEXT, confidence_score=0.9
        )

        for i in range(5):
            context.add_turn(f"질문{i+1}", response)

        recent = context.get_recent_turns(n=3)
        assert len(recent) == 3
        assert recent[0].user_query == "질문3"
        assert recent[-1].user_query == "질문5"


class TestResponseQuality:
    """ResponseQuality 테스트"""

    def test_quality_creation(self):
        """품질 평가 생성"""
        quality = ResponseQuality(
            completeness=0.9,
            accuracy=0.85,
            relevance=0.88,
            clarity=0.92,
            overall_score=0.0,
        )

        assert quality.completeness == 0.9
        assert quality.accuracy == 0.85

    def test_calculate_overall(self):
        """종합 점수 계산"""
        quality = ResponseQuality(
            completeness=0.9,
            accuracy=0.8,
            relevance=0.85,
            clarity=0.9,
            overall_score=0.0,
        )

        quality.calculate_overall()
        # 0.9*0.3 + 0.8*0.3 + 0.85*0.25 + 0.9*0.15 = 0.2625 + 0.24 + 0.2125 + 0.135 = 0.85
        assert quality.overall_score == pytest.approx(0.85, rel=0.01)

    def test_get_grade(self):
        """등급 반환"""
        quality = ResponseQuality(
            completeness=0.9,
            accuracy=0.9,
            relevance=0.9,
            clarity=0.9,
            overall_score=0.9,
        )

        assert quality.get_grade() == "A"

        quality.overall_score = 0.75
        assert quality.get_grade() == "C"


# ============================================================================
# Test Template Manager
# ============================================================================


class TestResponseTemplateManager:
    """ResponseTemplateManager 테스트"""

    def test_template_manager_initialization(self, template_manager):
        """템플릿 관리자 초기화"""
        templates = template_manager.list_templates()
        assert len(templates) >= 9  # 기본 템플릿 9개

    def test_get_template(self, template_manager):
        """템플릿 조회"""
        template = template_manager.get_template("coverage_amount")
        assert template is not None
        assert template.intent == "coverage_amount"

    def test_get_nonexistent_template(self, template_manager):
        """존재하지 않는 템플릿 조회"""
        template = template_manager.get_template("nonexistent")
        assert template is None

    def test_get_templates_by_intent(self, template_manager):
        """의도별 템플릿 조회"""
        templates = template_manager.get_templates_by_intent("coverage_check")
        assert len(templates) == 2  # coverage_check_yes, coverage_check_no

    def test_add_custom_template(self, template_manager):
        """커스텀 템플릿 추가"""
        custom_template = ResponseTemplate(
            template_id="custom_test",
            intent="test_intent",
            template="테스트 {var}",
            format=AnswerFormat.TEXT,
            required_variables=["var"],
        )

        template_manager.add_template(custom_template)
        retrieved = template_manager.get_template("custom_test")

        assert retrieved is not None
        assert retrieved.intent == "test_intent"

    def test_render_template(self, template_manager):
        """템플릿 렌더링"""
        result = template_manager.render_template(
            "age_limit", {"min_age": 20, "max_age": 65}
        )

        assert result is not None
        assert "20세" in result
        assert "65세" in result

    def test_render_nonexistent_template(self, template_manager):
        """존재하지 않는 템플릿 렌더링"""
        result = template_manager.render_template("nonexistent", {})
        assert result is None

    def test_select_best_template(self, template_manager):
        """최적 템플릿 선택"""
        template = template_manager.select_best_template(
            intent="coverage_amount", has_results=True
        )

        assert template is not None
        assert template.intent == "coverage_amount"

    def test_select_template_no_results(self, template_manager):
        """결과 없을 때 템플릿 선택"""
        template = template_manager.select_best_template(
            intent="coverage_amount", has_results=False
        )

        assert template is not None
        assert template.template_id == "no_results"


# ============================================================================
# Test Advanced Template Renderer
# ============================================================================


class TestAdvancedTemplateRenderer:
    """AdvancedTemplateRenderer 테스트"""

    def test_render_list_bullet(self):
        """불릿 리스트 렌더링"""
        items = ["항목1", "항목2", "항목3"]
        result = AdvancedTemplateRenderer.render_list(items, format="bullet")

        assert "- 항목1" in result
        assert "- 항목2" in result
        assert "- 항목3" in result

    def test_render_list_numbered(self):
        """번호 리스트 렌더링"""
        items = ["항목1", "항목2"]
        result = AdvancedTemplateRenderer.render_list(items, format="numbered")

        assert "1. 항목1" in result
        assert "2. 항목2" in result

    def test_render_coverage_list(self):
        """보장 목록 렌더링"""
        coverages = [
            {"coverage_name": "진단비", "amount": 50000000},
            {"coverage_name": "수술비", "amount": 10000000},
        ]

        result = AdvancedTemplateRenderer.render_coverage_list(coverages)

        assert "- 진단비:" in result
        assert "- 수술비:" in result

    def test_render_coverage_list_without_amount(self):
        """금액 없는 보장 목록 렌더링"""
        coverages = [{"coverage_name": "기타 보장"}]

        result = AdvancedTemplateRenderer.render_coverage_list(coverages)
        assert "- 기타 보장" in result

    def test_format_amount_in_billions(self):
        """억 단위 금액 포맷팅"""
        # 1억
        assert AdvancedTemplateRenderer.format_amount(100000000) == "1억원"

        # 5억
        assert AdvancedTemplateRenderer.format_amount(500000000) == "5억원"

        # 1억 5천만
        assert AdvancedTemplateRenderer.format_amount(150000000) == "1억 5000만원"

    def test_format_amount_in_ten_thousands(self):
        """만 단위 금액 포맷팅"""
        # 1만원
        assert AdvancedTemplateRenderer.format_amount(10000) == "1만원"

        # 500만원
        assert AdvancedTemplateRenderer.format_amount(5000000) == "500만원"

    def test_format_amount_small(self):
        """작은 금액 포맷팅"""
        assert AdvancedTemplateRenderer.format_amount(5000) == "5,000원"

    def test_format_period_in_years(self):
        """년 단위 기간 포맷팅"""
        assert AdvancedTemplateRenderer.format_period(365) == "1년"
        assert AdvancedTemplateRenderer.format_period(730) == "2년"

    def test_format_period_in_months(self):
        """월 단위 기간 포맷팅"""
        assert AdvancedTemplateRenderer.format_period(30) == "1개월"
        assert AdvancedTemplateRenderer.format_period(90) == "3개월"

    def test_format_period_in_days(self):
        """일 단위 기간 포맷팅"""
        assert AdvancedTemplateRenderer.format_period(7) == "7일"
        assert AdvancedTemplateRenderer.format_period(15) == "15일"


# ============================================================================
# Test Response Generator
# ============================================================================


class TestResponseGenerator:
    """ResponseGenerator 테스트"""

    @pytest.mark.asyncio
    async def test_generate_coverage_amount_response(
        self, response_generator, sample_search_results
    ):
        """보장 금액 응답 생성"""
        request = ResponseGenerationRequest(
            query="급성심근경색증 보장 금액은?",
            intent="coverage_amount",
            search_results=sample_search_results,
        )

        response = await response_generator.generate(request)

        assert response.answer is not None
        assert "급성심근경색증" in response.answer
        assert response.format == AnswerFormat.TABLE
        assert response.table is not None
        assert response.confidence_score > 0.8

    @pytest.mark.asyncio
    async def test_generate_coverage_check_response(
        self, response_generator, sample_coverage_check_results
    ):
        """보장 여부 확인 응답 생성"""
        request = ResponseGenerationRequest(
            query="당뇨병은 보장되나요?",
            intent="coverage_check",
            search_results=sample_coverage_check_results,
        )

        response = await response_generator.generate(request)

        assert response.answer is not None
        assert "당뇨병" in response.answer
        assert "보장 대상" in response.answer
        assert response.format == AnswerFormat.TEXT
        assert response.confidence_score > 0.9

    @pytest.mark.asyncio
    async def test_generate_comparison_response(
        self, response_generator, sample_comparison_results
    ):
        """비교 응답 생성"""
        request = ResponseGenerationRequest(
            query="암과 뇌졸중 비교",
            intent="disease_comparison",
            search_results=sample_comparison_results,
        )

        response = await response_generator.generate(request)

        assert response.answer is not None
        assert "암" in response.answer
        assert "뇌졸중" in response.answer
        assert response.format == AnswerFormat.COMPARISON
        assert response.comparison is not None

    @pytest.mark.asyncio
    async def test_generate_exclusions_response(self, response_generator):
        """제외 항목 응답 생성"""
        exclusion_results = [
            {"disease_name": "선천성 질환"},
            {"disease_name": "자해"},
        ]

        request = ResponseGenerationRequest(
            query="제외되는 질병은?",
            intent="exclusion_check",
            search_results=exclusion_results,
        )

        response = await response_generator.generate(request)

        assert response.answer is not None
        assert "제외" in response.answer
        assert response.format == AnswerFormat.LIST
        assert len(response.list_items) == 2

    @pytest.mark.asyncio
    async def test_generate_waiting_period_response(self, response_generator):
        """대기기간 응답 생성"""
        waiting_results = [{"coverage_name": "암 진단비", "waiting_period_days": 90}]

        request = ResponseGenerationRequest(
            query="대기기간은?",
            intent="waiting_period",
            search_results=waiting_results,
        )

        response = await response_generator.generate(request)

        assert response.answer is not None
        assert "90일" in response.answer
        assert response.format == AnswerFormat.TEXT

    @pytest.mark.asyncio
    async def test_generate_age_limit_response(self, response_generator):
        """나이 제한 응답 생성"""
        age_results = [{"min_age": 20, "max_age": 65}]

        request = ResponseGenerationRequest(
            query="가입 가능 나이는?",
            intent="age_limit",
            search_results=age_results,
        )

        response = await response_generator.generate(request)

        assert response.answer is not None
        assert "20세" in response.answer
        assert "65세" in response.answer

    @pytest.mark.asyncio
    async def test_generate_product_summary_response(self, response_generator):
        """상품 요약 응답 생성"""
        summary_results = [
            {
                "product_name": "종합보험",
                "main_coverages": [
                    {"coverage_name": "사망보장", "amount": 100000000},
                    {"coverage_name": "암진단비", "amount": 50000000},
                ],
            }
        ]

        request = ResponseGenerationRequest(
            query="상품 설명해주세요",
            intent="product_summary",
            search_results=summary_results,
        )

        response = await response_generator.generate(request)

        assert response.answer is not None
        assert "종합보험" in response.answer
        assert response.format == AnswerFormat.SUMMARY

    @pytest.mark.asyncio
    async def test_generate_no_results_response(self, response_generator):
        """결과 없음 응답 생성"""
        request = ResponseGenerationRequest(
            query="테스트 질문",
            intent="coverage_amount",
            search_results=[],
        )

        response = await response_generator.generate(request)

        assert response.answer is not None
        assert "찾을 수 없습니다" in response.answer
        assert response.confidence_score == 0.0

    @pytest.mark.asyncio
    async def test_generate_with_citations(
        self, response_generator, sample_search_results
    ):
        """출처 포함 응답 생성"""
        request = ResponseGenerationRequest(
            query="급성심근경색증 보장",
            intent="coverage_amount",
            search_results=sample_search_results,
            include_citations=True,
        )

        response = await response_generator.generate(request)

        assert len(response.citations) > 0
        assert response.citations[0].citation_type == CitationType.CLAUSE

    @pytest.mark.asyncio
    async def test_generate_with_follow_ups(
        self, response_generator, sample_search_results
    ):
        """후속 질문 포함 응답 생성"""
        request = ResponseGenerationRequest(
            query="급성심근경색증 보장",
            intent="coverage_amount",
            search_results=sample_search_results,
            include_follow_ups=True,
        )

        response = await response_generator.generate(request)

        assert len(response.follow_up_suggestions) > 0
        assert isinstance(response.follow_up_suggestions[0], str)

    @pytest.mark.asyncio
    async def test_generate_general_response(self, response_generator):
        """일반 응답 생성"""
        general_results = [{"clause_text": "보험 약관에 따라 보장됩니다."}]

        request = ResponseGenerationRequest(
            query="일반 질문",
            intent="general_info",
            search_results=general_results,
        )

        response = await response_generator.generate(request)

        assert response.answer is not None
        assert response.format == AnswerFormat.TEXT

    @pytest.mark.asyncio
    async def test_generate_fallback_response(self, response_generator):
        """폴백 응답 생성 (템플릿 없음)"""
        request = ResponseGenerationRequest(
            query="알 수 없는 질문",
            intent="unknown_intent",
            search_results=[{"test": "data"}],
        )

        response = await response_generator.generate(request)

        assert response.answer is not None
        assert response.confidence_score == 0.7  # general_info template is used

    @pytest.mark.asyncio
    async def test_generation_time_tracking(
        self, response_generator, sample_search_results
    ):
        """생성 시간 추적"""
        request = ResponseGenerationRequest(
            query="테스트",
            intent="coverage_amount",
            search_results=sample_search_results,
        )

        response = await response_generator.generate(request)

        assert response.generation_time_ms > 0

    @pytest.mark.asyncio
    async def test_extract_citations(self, response_generator):
        """출처 추출"""
        results = [
            {
                "clause_id": "clause_001",
                "clause_text": "약관 내용",
                "article_num": "제10조",
                "score": 0.95,
            },
            {
                "clause_id": "clause_002",
                "clause_text": "약관 내용2",
                "article_num": "제11조",
                "score": 0.85,
            },
        ]

        citations = response_generator._extract_citations(results)

        assert len(citations) == 2
        assert citations[0].source_id == "clause_001"
        assert citations[0].article_num == "제10조"

    @pytest.mark.asyncio
    async def test_generate_follow_ups_for_coverage_amount(self, response_generator):
        """보장 금액 의도 후속 질문 생성"""
        follow_ups = response_generator._generate_follow_ups("coverage_amount", "암 보장")

        assert len(follow_ups) > 0
        assert len(follow_ups) <= 3

    @pytest.mark.asyncio
    async def test_generate_follow_ups_for_coverage_check(self, response_generator):
        """보장 여부 의도 후속 질문 생성"""
        follow_ups = response_generator._generate_follow_ups(
            "coverage_check", "당뇨병 보장?"
        )

        assert len(follow_ups) > 0
        assert len(follow_ups) <= 3

    @pytest.mark.asyncio
    async def test_create_coverage_table(self, response_generator):
        """보장 테이블 생성"""
        coverages = [
            {"coverage_name": "진단비", "amount": 50000000},
            {"coverage_name": "수술비", "amount": 10000000},
        ]

        table = response_generator._create_coverage_table(coverages)

        assert len(table.headers) == 2
        assert len(table.rows) == 2
        assert table.caption == "보장 내역"


# ============================================================================
# Integration Tests
# ============================================================================


class TestResponseGenerationIntegration:
    """통합 테스트"""

    @pytest.mark.asyncio
    async def test_end_to_end_coverage_amount(self, response_generator):
        """E2E: 보장 금액 질의"""
        # 검색 결과 시뮬레이션
        search_results = [
            {
                "disease_name": "암",
                "coverage_name": "암 진단비",
                "amount": 100000000,
                "clause_id": "clause_001",
                "clause_text": "암 진단 시 1억원 지급",
                "article_num": "제5조",
                "score": 0.98,
            }
        ]

        request = ResponseGenerationRequest(
            query="암에 걸리면 얼마 받나요?",
            intent="coverage_amount",
            search_results=search_results,
            include_citations=True,
            include_follow_ups=True,
        )

        response = await response_generator.generate(request)

        # 검증
        assert response.answer is not None
        assert "암" in response.answer
        assert response.format == AnswerFormat.TABLE
        assert response.table is not None
        assert len(response.citations) > 0
        assert len(response.follow_up_suggestions) > 0
        assert response.confidence_score > 0.8
        assert response.generation_time_ms > 0

        # 전체 답변 확인
        full_answer = response.get_full_answer(include_citations=True)
        assert "**출처:**" in full_answer
        assert "**관련 질문:**" in full_answer

    @pytest.mark.asyncio
    async def test_end_to_end_comparison(self, response_generator):
        """E2E: 질병 비교"""
        search_results = [
            {
                "disease1_name": "암",
                "disease2_name": "당뇨병",
                "cov1": [
                    {"name": "진단비"},
                    {"name": "수술비"},
                    {"name": "항암치료비"},
                ],
                "cov2": [
                    {"name": "진단비"},
                    {"name": "합병증 치료비"},
                ],
            }
        ]

        request = ResponseGenerationRequest(
            query="암과 당뇨병 보장 비교해주세요",
            intent="disease_comparison",
            search_results=search_results,
        )

        response = await response_generator.generate(request)

        assert response.format == AnswerFormat.COMPARISON
        assert response.comparison is not None
        assert response.comparison.item1.name == "암"
        assert response.comparison.item2.name == "당뇨병"
        assert len(response.comparison.similarities) > 0 or len(
            response.comparison.differences
        ) > 0
