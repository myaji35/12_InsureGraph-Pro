"""
Answer Validation Service

LLM이 생성한 답변의 품질과 정확성을 검증합니다.

4-Stage Defense System:
1. Source Verification - 답변이 제공된 문서에 근거하는지 검증
2. Factual Consistency - 답변이 원본 조문과 일치하는지 검증
3. Completeness Check - 중요 정보가 누락되지 않았는지 검증
4. Hallucination Detection - LLM이 없는 정보를 만들어내지 않았는지 검증
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
import re

from app.services.llm_reasoning import ReasoningResult
from app.services.local_search import SearchResult
from loguru import logger


class ValidationLevel(str, Enum):
    """Validation severity level"""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


class ValidationStage(str, Enum):
    """Validation stage"""
    SOURCE_VERIFICATION = "source_verification"
    FACTUAL_CONSISTENCY = "factual_consistency"
    COMPLETENESS = "completeness"
    HALLUCINATION_DETECTION = "hallucination_detection"


@dataclass
class ValidationIssue:
    """A validation issue found"""
    stage: ValidationStage
    level: ValidationLevel
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """Result of answer validation"""
    passed: bool
    overall_level: ValidationLevel
    issues: List[ValidationIssue]
    confidence: float  # 0.0 - 1.0
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "overall_level": self.overall_level.value,
            "confidence": self.confidence,
            "issues": [
                {
                    "stage": issue.stage.value,
                    "level": issue.level.value,
                    "message": issue.message,
                    "details": issue.details,
                }
                for issue in self.issues
            ],
            "recommendations": self.recommendations,
        }


class AnswerValidator:
    """
    Validates LLM-generated answers using 4-stage defense system.

    Features:
    - Source verification (답변 근거 확인)
    - Factual consistency (사실 일치성)
    - Completeness check (완전성)
    - Hallucination detection (환각 감지)
    """

    def __init__(
        self,
        min_sources: int = 1,
        min_answer_length: int = 50,
        max_answer_length: int = 5000,
    ):
        """
        Initialize answer validator.

        Args:
            min_sources: Minimum number of sources required
            min_answer_length: Minimum answer length in characters
            max_answer_length: Maximum answer length in characters
        """
        self.min_sources = min_sources
        self.min_answer_length = min_answer_length
        self.max_answer_length = max_answer_length

    def validate(
        self,
        reasoning_result: ReasoningResult,
        search_results: List[SearchResult],
    ) -> ValidationResult:
        """
        Validate a reasoning result.

        Args:
            reasoning_result: LLM reasoning result to validate
            search_results: Original search results used

        Returns:
            ValidationResult with all issues
        """
        issues = []

        # Stage 1: Source Verification
        source_issues = self._verify_sources(reasoning_result, search_results)
        issues.extend(source_issues)

        # Stage 2: Factual Consistency
        factual_issues = self._check_factual_consistency(reasoning_result, search_results)
        issues.extend(factual_issues)

        # Stage 3: Completeness
        completeness_issues = self._check_completeness(reasoning_result, search_results)
        issues.extend(completeness_issues)

        # Stage 4: Hallucination Detection
        hallucination_issues = self._detect_hallucinations(reasoning_result, search_results)
        issues.extend(hallucination_issues)

        # Determine overall result
        has_fail = any(issue.level == ValidationLevel.FAIL for issue in issues)
        has_warning = any(issue.level == ValidationLevel.WARNING for issue in issues)

        if has_fail:
            overall_level = ValidationLevel.FAIL
            passed = False
        elif has_warning:
            overall_level = ValidationLevel.WARNING
            passed = True  # Still usable but with warnings
        else:
            overall_level = ValidationLevel.PASS
            passed = True

        # Calculate adjusted confidence
        confidence = self._calculate_adjusted_confidence(
            reasoning_result.confidence,
            issues,
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(issues)

        result = ValidationResult(
            passed=passed,
            overall_level=overall_level,
            issues=issues,
            confidence=confidence,
            recommendations=recommendations,
        )

        logger.info(
            f"Validation result: {overall_level.value} "
            f"(confidence: {confidence:.2f}, issues: {len(issues)})"
        )

        return result

    def _verify_sources(
        self,
        reasoning_result: ReasoningResult,
        search_results: List[SearchResult],
    ) -> List[ValidationIssue]:
        """Stage 1: Verify that answer is based on provided sources"""
        issues = []

        # Check if sources exist
        if not reasoning_result.sources:
            issues.append(ValidationIssue(
                stage=ValidationStage.SOURCE_VERIFICATION,
                level=ValidationLevel.FAIL,
                message="No sources cited in answer",
            ))
            return issues

        # Check minimum sources
        if len(reasoning_result.sources) < self.min_sources:
            issues.append(ValidationIssue(
                stage=ValidationStage.SOURCE_VERIFICATION,
                level=ValidationLevel.WARNING,
                message=f"Only {len(reasoning_result.sources)} sources cited (minimum: {self.min_sources})",
                details={"sources_count": len(reasoning_result.sources)},
            ))

        # Check if cited sources exist in search results
        search_node_ids = {result.node_id for result in search_results}
        cited_node_ids = {source["node_id"] for source in reasoning_result.sources}

        invalid_citations = cited_node_ids - search_node_ids
        if invalid_citations:
            issues.append(ValidationIssue(
                stage=ValidationStage.SOURCE_VERIFICATION,
                level=ValidationLevel.FAIL,
                message=f"Answer cites sources not in search results: {invalid_citations}",
                details={"invalid_citations": list(invalid_citations)},
            ))

        return issues

    def _check_factual_consistency(
        self,
        reasoning_result: ReasoningResult,
        search_results: List[SearchResult],
    ) -> List[ValidationIssue]:
        """Stage 2: Check if answer is factually consistent with sources"""
        issues = []

        answer = reasoning_result.answer.lower()

        # Extract amounts from answer
        answer_amounts = self._extract_amounts(answer)

        # Extract amounts from search results
        source_amounts = set()
        for result in search_results:
            source_amounts.update(self._extract_amounts(result.text.lower()))

        # Check if answer amounts exist in sources
        invalid_amounts = set(answer_amounts) - source_amounts
        if invalid_amounts:
            issues.append(ValidationIssue(
                stage=ValidationStage.FACTUAL_CONSISTENCY,
                level=ValidationLevel.WARNING,
                message=f"Answer mentions amounts not found in sources: {invalid_amounts}",
                details={"invalid_amounts": list(invalid_amounts)},
            ))

        # Check answer length
        if len(reasoning_result.answer) < self.min_answer_length:
            issues.append(ValidationIssue(
                stage=ValidationStage.FACTUAL_CONSISTENCY,
                level=ValidationLevel.WARNING,
                message=f"Answer too short: {len(reasoning_result.answer)} chars (minimum: {self.min_answer_length})",
            ))

        if len(reasoning_result.answer) > self.max_answer_length:
            issues.append(ValidationIssue(
                stage=ValidationStage.FACTUAL_CONSISTENCY,
                level=ValidationLevel.WARNING,
                message=f"Answer too long: {len(reasoning_result.answer)} chars (maximum: {self.max_answer_length})",
            ))

        return issues

    def _check_completeness(
        self,
        reasoning_result: ReasoningResult,
        search_results: List[SearchResult],
    ) -> List[ValidationIssue]:
        """Stage 3: Check if answer includes all important information"""
        issues = []

        answer = reasoning_result.answer.lower()

        # Check for important keywords in sources that should be in answer
        important_keywords = ["면책", "제외", "단", "다만", "except", "exclusion"]

        source_text = " ".join([result.text.lower() for result in search_results[:5]])

        # If sources mention exclusions, answer should too
        has_exclusion_in_source = any(kw in source_text for kw in important_keywords)
        has_exclusion_in_answer = any(kw in answer for kw in important_keywords)

        if has_exclusion_in_source and not has_exclusion_in_answer:
            issues.append(ValidationIssue(
                stage=ValidationStage.COMPLETENESS,
                level=ValidationLevel.WARNING,
                message="Sources mention exclusions/exceptions but answer does not address them",
                details={"missing_topic": "exclusions"},
            ))

        # Check if answer addresses the query
        query_lower = reasoning_result.query.lower()
        query_keywords = self._extract_keywords(query_lower)

        # Answer should mention at least some query keywords
        mentioned_keywords = [kw for kw in query_keywords if kw in answer]
        if not mentioned_keywords and len(query_keywords) > 0:
            issues.append(ValidationIssue(
                stage=ValidationStage.COMPLETENESS,
                level=ValidationLevel.WARNING,
                message="Answer does not address query keywords",
                details={"query_keywords": query_keywords},
            ))

        return issues

    def _detect_hallucinations(
        self,
        reasoning_result: ReasoningResult,
        search_results: List[SearchResult],
    ) -> List[ValidationIssue]:
        """Stage 4: Detect if LLM generated information not in sources"""
        issues = []

        answer = reasoning_result.answer

        # Build source content
        source_text = " ".join([result.text for result in search_results])

        # Extract specific claims from answer (amounts, periods, diseases)
        answer_amounts = self._extract_amounts(answer)
        answer_periods = self._extract_periods(answer)
        answer_kcds = self._extract_kcd_codes(answer)

        source_amounts = self._extract_amounts(source_text)
        source_periods = self._extract_periods(source_text)
        source_kcds = self._extract_kcd_codes(source_text)

        # Check for hallucinated amounts
        hallucinated_amounts = set(answer_amounts) - set(source_amounts)
        if hallucinated_amounts:
            issues.append(ValidationIssue(
                stage=ValidationStage.HALLUCINATION_DETECTION,
                level=ValidationLevel.FAIL,
                message=f"Answer contains amounts not in sources: {hallucinated_amounts}",
                details={"hallucinated_amounts": list(hallucinated_amounts)},
            ))

        # Check for hallucinated KCD codes
        hallucinated_kcds = set(answer_kcds) - set(source_kcds)
        if hallucinated_kcds:
            issues.append(ValidationIssue(
                stage=ValidationStage.HALLUCINATION_DETECTION,
                level=ValidationLevel.FAIL,
                message=f"Answer contains KCD codes not in sources: {hallucinated_kcds}",
                details={"hallucinated_codes": list(hallucinated_kcds)},
            ))

        # Check for vague/uncertain language (which might indicate hallucination)
        uncertain_phrases = ["아마도", "대략", "~것 같습니다", "추측", "가능성"]
        if any(phrase in answer for phrase in uncertain_phrases):
            issues.append(ValidationIssue(
                stage=ValidationStage.HALLUCINATION_DETECTION,
                level=ValidationLevel.WARNING,
                message="Answer contains uncertain/vague language",
                details={"uncertain_phrases": [p for p in uncertain_phrases if p in answer]},
            ))

        return issues

    def _calculate_adjusted_confidence(
        self,
        original_confidence: float,
        issues: List[ValidationIssue],
    ) -> float:
        """Adjust confidence score based on validation issues"""
        confidence = original_confidence

        # Reduce confidence for each issue
        for issue in issues:
            if issue.level == ValidationLevel.FAIL:
                confidence *= 0.5
            elif issue.level == ValidationLevel.WARNING:
                confidence *= 0.9

        return max(confidence, 0.0)

    def _generate_recommendations(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate recommendations based on issues"""
        recommendations = []

        if not issues:
            recommendations.append("답변이 모든 검증을 통과했습니다.")
            return recommendations

        # Group issues by stage
        by_stage = {}
        for issue in issues:
            if issue.stage not in by_stage:
                by_stage[issue.stage] = []
            by_stage[issue.stage].append(issue)

        # Generate stage-specific recommendations
        if ValidationStage.SOURCE_VERIFICATION in by_stage:
            recommendations.append("답변에 더 많은 조문 출처를 명시하세요.")

        if ValidationStage.FACTUAL_CONSISTENCY in by_stage:
            recommendations.append("답변의 금액이나 기간 정보를 조문과 다시 확인하세요.")

        if ValidationStage.COMPLETENESS in by_stage:
            recommendations.append("면책 사항이나 예외 조건을 추가로 안내하세요.")

        if ValidationStage.HALLUCINATION_DETECTION in by_stage:
            recommendations.append("답변에 원본 조문에 없는 정보가 포함되어 있습니다. 답변을 다시 생성하세요.")

        return recommendations

    # Helper methods for extraction

    def _extract_amounts(self, text: str) -> List[str]:
        """Extract amount mentions from text"""
        patterns = [
            r'\d+억\s*\d*만?\s*원',
            r'\d+억\s*원',
            r'\d+천\s*만\s*원',
            r'\d+만\s*원',
            r'\d+천\s*원',
            r'\d+원',
        ]

        amounts = []
        for pattern in patterns:
            amounts.extend(re.findall(pattern, text))

        return amounts

    def _extract_periods(self, text: str) -> List[str]:
        """Extract period mentions from text"""
        patterns = [
            r'\d+년',
            r'\d+개월',
            r'\d+주',
            r'\d+일',
        ]

        periods = []
        for pattern in patterns:
            periods.extend(re.findall(pattern, text))

        return periods

    def _extract_kcd_codes(self, text: str) -> List[str]:
        """Extract KCD code mentions from text"""
        # Matches C00, I21, D00-D09, etc.
        pattern = r'[A-Z]\d{2,3}(?:-[A-Z]?\d{2,3})?'
        return re.findall(pattern, text)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove common words
        stopwords = {'은', '는', '이', '가', '을', '를', '의', '에', '와', '과', '도', '만'}

        words = re.findall(r'\w+', text)
        keywords = [w for w in words if w not in stopwords and len(w) > 1]

        return keywords


# Singleton instance
_answer_validator: Optional[AnswerValidator] = None


def get_answer_validator(**kwargs) -> AnswerValidator:
    """Get or create singleton answer validator instance"""
    global _answer_validator
    if _answer_validator is None:
        _answer_validator = AnswerValidator(**kwargs)
    return _answer_validator


if __name__ == "__main__":
    # Test answer validator
    from app.services.llm_reasoning import ReasoningResult, LLMProvider

    print("=" * 70)
    print("🧪 Answer Validator Test")
    print("=" * 70)

    # Mock reasoning result
    mock_reasoning = ReasoningResult(
        query="암보험 1억원 이상 보장되는 경우는?",
        answer="""# 답변:
일반암으로 진단 확정되었을 때 1억원이 보장됩니다.

## 근거 조문:
제10조에 따르면, 일반암(C77 제외)의 경우 1억원을 지급합니다.

## 추가 참고사항:
다만, 계약일로부터 90일 이내 진단된 경우 면책됩니다.""",
        confidence=0.85,
        sources=[
            {
                "node_id": "policy_123_article_제10조",
                "node_type": "Article",
                "text": "제10조 [암보험금 지급] 일반암(C77 제외): 1억원",
                "relevance_score": 0.95,
            }
        ],
        reasoning_steps=["Parsed query", "Found sources", "Generated answer"],
        provider=LLMProvider.MOCK,
    )

    # Mock search results
    mock_search = [
        SearchResult(
            node_type="Article",
            node_id="policy_123_article_제10조",
            text="제10조 [암보험금 지급] 일반암(C77 제외): 1억원. 다만, 계약일로부터 90일 이내 면책.",
            relevance_score=0.95,
            metadata={},
        )
    ]

    # Validate
    print("\n🔍 Validating answer...")
    validator = get_answer_validator()
    result = validator.validate(mock_reasoning, mock_search)

    print(f"\n{'='*70}")
    print(f"📊 Validation Result")
    print(f"{'='*70}")
    print(f"Passed: {result.passed}")
    print(f"Overall Level: {result.overall_level.value}")
    print(f"Confidence: {result.confidence:.2f}")

    if result.issues:
        print(f"\n⚠️  Issues ({len(result.issues)}):")
        for i, issue in enumerate(result.issues, 1):
            icon = {
                ValidationLevel.PASS: "✅",
                ValidationLevel.WARNING: "⚠️",
                ValidationLevel.FAIL: "❌",
            }[issue.level]
            print(f"{i}. {icon} [{issue.stage.value}] {issue.message}")
            if issue.details:
                print(f"   Details: {issue.details}")
    else:
        print("\n✅ No issues found!")

    if result.recommendations:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"{i}. {rec}")

    print("\n" + "=" * 70)
    print("✅ Answer validator test complete!")
    print("=" * 70)
