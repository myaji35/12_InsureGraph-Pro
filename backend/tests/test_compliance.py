"""
Tests for Compliance Checking

규제 준수 검증 테스트
"""

import pytest

from app.services.compliance.citation_validator import CitationValidator
from app.services.compliance.explanation_duty import (
    ExplanationDutyChecker,
    ExplanationCategory
)
from app.services.compliance.compliance_checker import (
    ComplianceChecker,
    check_answer_compliance
)


class TestCitationValidator:
    """CitationValidator 테스트"""

    def test_validate_citation_success(self):
        """Citation 검증 - 성공"""
        citation = {
            "document_id": "doc_123",
            "article_num": "제1조",
            "title": "용어의 정의",
            "page": 5,
            "text": "이 약관에서 사용하는 용어의 정의는 다음과 같습니다.",
            "confidence": 0.92,
        }

        valid, error = CitationValidator.validate_citation(citation)

        assert valid is True
        assert error is None

    def test_validate_citation_missing_required_field(self):
        """Citation 검증 - 필수 필드 누락"""
        citation = {
            "article_num": "제1조",
            # document_id 누락
        }

        valid, error = CitationValidator.validate_citation(citation)

        assert valid is False
        assert "Missing required field" in error

    def test_validate_citation_low_confidence(self):
        """Citation 검증 - 낮은 confidence (경고만, 통과)"""
        citation = {
            "document_id": "doc_123",
            "text": "Some text here",
            "confidence": 0.5,  # Low but valid
        }

        valid, error = CitationValidator.validate_citation(citation)

        # 낮은 confidence여도 검증은 통과 (경고만 출력)
        assert valid is True

    def test_validate_citation_text_too_short(self):
        """Citation 검증 - 텍스트 너무 짧음"""
        citation = {
            "document_id": "doc_123",
            "text": "Too short",  # < 10 characters
        }

        valid, error = CitationValidator.validate_citation(citation)

        assert valid is False
        assert "too short" in error

    def test_validate_citations_multiple(self):
        """여러 Citations 검증"""
        citations = [
            {
                "document_id": "doc_1",
                "text": "Valid citation text here.",
                "confidence": 0.9,
            },
            {
                "document_id": "doc_2",
                "text": "Another valid citation text.",
                "confidence": 0.85,
            },
        ]

        all_valid, errors = CitationValidator.validate_citations(citations)

        assert all_valid is True
        assert len(errors) == 0

    def test_validate_citations_empty(self):
        """빈 Citations 검증"""
        all_valid, errors = CitationValidator.validate_citations([])

        assert all_valid is False
        assert len(errors) > 0

    def test_check_citation_coverage_sufficient(self):
        """Citation 충분성 검증 - 충분함"""
        answer = "Short answer"
        citations = [
            {"document_id": "doc_1", "text": "Citation 1"},
        ]

        sufficient, warning = CitationValidator.check_citation_coverage(
            answer, citations, min_citations=1
        )

        assert sufficient is True
        assert warning is None

    def test_check_citation_coverage_insufficient(self):
        """Citation 충분성 검증 - 부족함"""
        answer = "Short answer"
        citations = []

        sufficient, warning = CitationValidator.check_citation_coverage(
            answer, citations, min_citations=1
        )

        assert sufficient is False
        assert "Insufficient citations" in warning

    def test_check_citation_coverage_long_answer(self):
        """긴 답변에 대한 Citation 충분성 검증"""
        answer = "A" * 600  # Long answer
        citations = [
            {"document_id": "doc_1", "text": "Only one citation"},
        ]

        sufficient, warning = CitationValidator.check_citation_coverage(
            answer, citations
        )

        assert sufficient is False
        assert "requires multiple citations" in warning

    def test_extract_source_reference(self):
        """출처 참조 추출"""
        citation = {
            "document_id": "123e4567-e89b-12d3",
            "article_num": "제1조",
            "title": "용어의 정의",
            "page": 5,
        }

        reference = CitationValidator.extract_source_reference(citation)

        assert "제1조" in reference
        assert "용어의 정의" in reference
        assert "5페이지" in reference

    def test_format_citations_for_display(self):
        """Citations 표시 형식 변환"""
        citations = [
            {
                "document_id": "doc_1",
                "article_num": "제1조",
                "confidence": 0.9,
            },
            {
                "document_id": "doc_2",
                "article_num": "제2조",
                "confidence": 0.85,
            },
        ]

        formatted = CitationValidator.format_citations_for_display(citations)

        assert "근거 자료" in formatted
        assert "제1조" in formatted
        assert "제2조" in formatted
        assert "90%" in formatted

    def test_append_citation_footer(self):
        """Citation footer 추가"""
        answer = "This is an answer."
        citations = [
            {"document_id": "doc_1", "article_num": "제1조", "text": "..."},
        ]

        answer_with_footer = CitationValidator.append_citation_footer(answer, citations)

        assert "This is an answer." in answer_with_footer
        assert "근거 자료" in answer_with_footer
        assert "제1조" in answer_with_footer

    def test_append_citation_footer_no_citations(self):
        """Citation이 없는 경우 footer 추가"""
        answer = "This is an answer."
        citations = []

        answer_with_footer = CitationValidator.append_citation_footer(answer, citations)

        assert "주의" in answer_with_footer
        assert "약관 근거가 부족" in answer_with_footer

    def test_check_hallucination_risk_low(self):
        """할루시네이션 위험도 - 낮음"""
        answer = "Simple answer"
        citations = [
            {"document_id": "doc_1", "text": "...", "confidence": 0.9},
        ]

        risk_level, warnings = CitationValidator.check_hallucination_risk(
            answer, citations
        )

        assert risk_level == "low"

    def test_check_hallucination_risk_high_no_citations(self):
        """할루시네이션 위험도 - 높음 (Citation 없음)"""
        answer = "Answer without any citations"
        citations = []

        risk_level, warnings = CitationValidator.check_hallucination_risk(
            answer, citations
        )

        assert risk_level in ["medium", "high"]
        assert len(warnings) > 0

    def test_check_hallucination_risk_definitive_expression(self):
        """할루시네이션 위험도 - 단정적 표현"""
        answer = "이 상품은 반드시 100% 전액 보장됩니다."
        citations = [
            {"document_id": "doc_1", "text": "...", "confidence": 0.9},
        ]

        risk_level, warnings = CitationValidator.check_hallucination_risk(
            answer, citations
        )

        assert len(warnings) > 0
        assert any("단정적 표현" in w for w in warnings)

    def test_create_traceability_report(self):
        """추적 가능성 보고서 생성"""
        query = "갑상선암 보장되나요?"
        answer = "네, 보장됩니다."
        citations = [
            {
                "document_id": "doc_1",
                "article_num": "제5조",
                "text": "갑상선암은 일반암으로 보장됩니다.",
                "confidence": 0.9,
            }
        ]

        report = CitationValidator.create_traceability_report(
            query, answer, citations
        )

        assert "timestamp" in report
        assert report["query"] == query
        assert report["citations_count"] == 1
        assert "validation" in report
        assert "risk_assessment" in report
        assert "compliance_status" in report


class TestExplanationDutyChecker:
    """ExplanationDutyChecker 테스트"""

    def test_detect_explanation_category_exclusion(self):
        """설명 의무 카테고리 감지 - 면책"""
        query = "갑상선암은 보장되지 않나요?"
        answer = "네, 면책 사항입니다."

        category = ExplanationDutyChecker.detect_explanation_category(query, answer)

        assert category == ExplanationCategory.EXCLUSION

    def test_detect_explanation_category_waiting_period(self):
        """설명 의무 카테고리 감지 - 대기기간"""
        query = "대기기간이 있나요?"
        answer = "90일의 대기기간이 있습니다."

        category = ExplanationDutyChecker.detect_explanation_category(query, answer)

        assert category == ExplanationCategory.WAITING_PERIOD

    def test_detect_explanation_category_coverage(self):
        """설명 의무 카테고리 감지 - 보장"""
        query = "급성심근경색증 보장 금액은?"
        answer = "5,000만원이 보장됩니다."

        category = ExplanationDutyChecker.detect_explanation_category(query, answer)

        assert category == ExplanationCategory.COVERAGE

    def test_check_required_keywords_present(self):
        """필수 키워드 확인 - 포함됨"""
        answer = "이 상품은 급성심근경색증에 대해 5,000만원을 보장합니다."
        category = ExplanationCategory.COVERAGE

        has_keyword, missing = ExplanationDutyChecker.check_required_keywords(
            answer, category
        )

        assert has_keyword is True
        assert len(missing) == 0

    def test_check_required_keywords_missing(self):
        """필수 키워드 확인 - 누락됨"""
        answer = "이 상품은 좋은 상품입니다."  # 보장 관련 키워드 없음
        category = ExplanationCategory.COVERAGE

        has_keyword, missing = ExplanationDutyChecker.check_required_keywords(
            answer, category
        )

        assert has_keyword is False
        assert len(missing) > 0

    def test_check_caution_keywords(self):
        """주의 키워드 확인"""
        answer = "이 상품은 무조건 전액 보장됩니다."

        warnings = ExplanationDutyChecker.check_caution_keywords(answer)

        assert len(warnings) >= 2  # "무조건", "전액"
        assert any(w["keyword"] == "무조건" for w in warnings)
        assert any(w["keyword"] == "전액" for w in warnings)

    def test_check_prohibited_keywords(self):
        """금지 키워드 확인"""
        answer = "이 상품은 무조건 가입하세요. 손해 없음!"

        prohibited = ExplanationDutyChecker.check_prohibited_keywords(answer)

        assert len(prohibited) >= 1
        assert any("무조건 가입" in p for p in prohibited)

    def test_check_disclaimer_present(self):
        """면책 고지 확인 - 있음"""
        answer = "보장됩니다. 자세한 사항은 약관을 확인하시기 바랍니다."

        has_disclaimer = ExplanationDutyChecker.check_disclaimer_present(answer)

        assert has_disclaimer is True

    def test_check_disclaimer_absent(self):
        """면책 고지 확인 - 없음"""
        answer = "보장됩니다."

        has_disclaimer = ExplanationDutyChecker.check_disclaimer_present(answer)

        assert has_disclaimer is False

    def test_generate_disclaimer(self):
        """면책 고지 생성"""
        disclaimer = ExplanationDutyChecker.generate_disclaimer(
            ExplanationCategory.COVERAGE
        )

        assert "약관" in disclaimer
        assert "확인" in disclaimer

    def test_append_disclaimer_if_needed(self):
        """필요시 면책 고지 추가"""
        answer = "5,000만원이 보장됩니다."
        category = ExplanationCategory.COVERAGE

        answer_with_disclaimer = ExplanationDutyChecker.append_disclaimer_if_needed(
            answer, category
        )

        assert "5,000만원이 보장됩니다." in answer_with_disclaimer
        assert "유의사항" in answer_with_disclaimer

    def test_append_disclaimer_already_present(self):
        """이미 면책 고지가 있으면 추가하지 않음"""
        answer = "보장됩니다. 약관을 확인하시기 바랍니다."
        category = ExplanationCategory.COVERAGE

        answer_with_disclaimer = ExplanationDutyChecker.append_disclaimer_if_needed(
            answer, category
        )

        # 변경 없음
        assert answer_with_disclaimer == answer

    def test_validate_explanation_duty_compliant(self):
        """설명 의무 검증 - 준수"""
        query = "보장 내용이 뭔가요?"
        answer = "5,000만원이 보장됩니다. 자세한 내용은 약관을 확인하세요."

        result = ExplanationDutyChecker.validate_explanation_duty(query, answer)

        assert result["compliant"] is True
        assert result["category"] == ExplanationCategory.COVERAGE.value
        assert len(result["issues"]) == 0

    def test_validate_explanation_duty_non_compliant(self):
        """설명 의무 검증 - 미준수"""
        query = "보장 내용이 뭔가요?"
        answer = "무조건 가입하세요!"  # 금지 키워드 + 보장 키워드 없음

        result = ExplanationDutyChecker.validate_explanation_duty(query, answer)

        assert result["compliant"] is False
        assert len(result["issues"]) > 0

    def test_validate_explanation_duty_auto_fix(self):
        """설명 의무 검증 - 자동 수정"""
        query = "보장되나요?"
        answer = "네, 보장됩니다."

        result = ExplanationDutyChecker.validate_explanation_duty(
            query, answer, auto_fix=True
        )

        assert result["fixed_answer"] is not None
        assert "유의사항" in result["fixed_answer"]


class TestComplianceChecker:
    """ComplianceChecker 테스트"""

    def test_check_compliance_pass(self):
        """종합 규제 준수 검증 - 통과"""
        checker = ComplianceChecker(auto_fix=False)

        query = "급성심근경색증 보장 금액은?"
        answer = "5,000만원이 보장됩니다. 자세한 내용은 약관을 확인하세요."
        citations = [
            {
                "document_id": "doc_123",
                "article_num": "제5조",
                "text": "급성심근경색증 진단 시 5,000만원을 지급합니다.",
                "confidence": 0.92,
            }
        ]

        result = checker.check_compliance(query, answer, citations)

        assert result["compliance_level"] in ["pass", "warning"]
        assert len(result["issues"]) == 0

    def test_check_compliance_fail_no_citations(self):
        """종합 규제 준수 검증 - 실패 (Citation 없음)"""
        checker = ComplianceChecker()

        query = "보장되나요?"
        answer = "네, 보장됩니다."
        citations = []

        result = checker.check_compliance(query, answer, citations)

        assert result["compliance_level"] == "fail"
        assert len(result["issues"]) > 0

    def test_check_compliance_fail_prohibited_keywords(self):
        """종합 규제 준수 검증 - 실패 (금지 키워드)"""
        checker = ComplianceChecker()

        query = "가입해야 하나요?"
        answer = "무조건 가입하세요!"
        citations = [
            {"document_id": "doc_1", "text": "...", "confidence": 0.9}
        ]

        result = checker.check_compliance(query, answer, citations)

        assert result["compliance_level"] == "fail"
        assert any("금지된 표현" in issue for issue in result["issues"])

    def test_check_compliance_auto_fix(self):
        """종합 규제 준수 검증 - 자동 수정"""
        checker = ComplianceChecker(auto_fix=True)

        query = "보장되나요?"
        answer = "네, 5,000만원이 보장됩니다."
        citations = [
            {
                "document_id": "doc_1",
                "article_num": "제5조",
                "text": "5,000만원 지급",
                "confidence": 0.9,
            }
        ]

        result = checker.check_compliance(query, answer, citations)

        assert result["fixed_answer"] is not None
        assert len(result["fixed_answer"]) > len(answer)  # Footer added
        assert "근거 자료" in result["fixed_answer"]

    def test_check_compliance_warning_level(self):
        """종합 규제 준수 검증 - 경고 레벨"""
        checker = ComplianceChecker()

        query = "보장 금액은?"
        answer = "전액 보장됩니다."  # 주의 키워드
        citations = [
            {"document_id": "doc_1", "text": "...", "confidence": 0.9}
        ]

        result = checker.check_compliance(query, answer, citations)

        # 주의 키워드가 있어서 warning 또는 fail
        assert result["compliance_level"] in ["warning", "fail"]

    def test_create_compliance_report_summary(self):
        """규제 준수 보고서 요약 생성"""
        checker = ComplianceChecker()

        query = "보장되나요?"
        answer = "네, 보장됩니다. 약관을 확인하세요."
        citations = [
            {
                "document_id": "doc_1",
                "article_num": "제5조",
                "text": "보장 내용",
                "confidence": 0.9,
            }
        ]

        result = checker.check_compliance(query, answer, citations)
        summary = ComplianceChecker.create_compliance_report_summary(result)

        assert "규제 준수 검증 보고서" in summary
        assert "전체 결과" in summary

    def test_check_answer_compliance_convenience_function(self):
        """check_answer_compliance 편의 함수"""
        query = "보장되나요?"
        answer = "네, 보장됩니다."
        citations = [
            {"document_id": "doc_1", "text": "...", "confidence": 0.9}
        ]

        result = check_answer_compliance(query, answer, citations, auto_fix=True)

        assert "compliance_level" in result
        assert "fixed_answer" in result


class TestComplianceIntegration:
    """Compliance 통합 테스트"""

    def test_full_compliance_workflow(self):
        """전체 규제 준수 워크플로우"""
        # 1. 사용자 질의 및 답변 생성 (가정)
        query = "급성심근경색증으로 5,000만원 받을 수 있나요?"
        answer = "네, 급성심근경색증 진단 시 5,000만원이 보장됩니다."
        citations = [
            {
                "document_id": "doc_12345",
                "article_num": "제5조",
                "title": "급성심근경색증 진단비",
                "page": 12,
                "text": "피보험자가 급성심근경색증으로 진단확정된 경우 5,000만원을 지급합니다.",
                "confidence": 0.95,
            }
        ]

        # 2. Compliance 검증
        result = check_answer_compliance(
            query, answer, citations, auto_fix=True
        )

        # 3. 검증 결과 확인
        assert result["compliance_level"] in ["pass", "warning"]
        assert result["fixed_answer"] is not None

        # 4. 고정된 답변에 Citation footer 포함 확인
        fixed_answer = result["fixed_answer"]
        assert "5,000만원이 보장됩니다" in fixed_answer
        assert "근거 자료" in fixed_answer
        assert "제5조" in fixed_answer

        # 5. Traceability report 확인
        assert "traceability_report" in result
        assert result["traceability_report"]["citations_count"] == 1

    def test_compliance_with_multiple_issues(self):
        """여러 이슈가 있는 경우"""
        query = "보장되나요?"
        answer = "무조건 100% 전액 보장됩니다!"  # 금지 키워드 + 주의 키워드
        citations = []  # Citation 없음

        result = check_answer_compliance(query, answer, citations)

        # 여러 이슈 발생
        assert result["compliance_level"] == "fail"
        assert len(result["issues"]) > 0
        assert len(result["warnings"]) > 0
