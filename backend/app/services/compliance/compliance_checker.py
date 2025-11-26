"""
Compliance Checker

종합 규제 준수 검증기
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from loguru import logger

from app.services.compliance.citation_validator import CitationValidator
from app.services.compliance.explanation_duty import ExplanationDutyChecker, ExplanationCategory


class ComplianceLevel(str):
    """규제 준수 레벨"""
    PASS = "pass"  # 통과
    WARNING = "warning"  # 경고 (사용 가능하나 주의 필요)
    FAIL = "fail"  # 실패 (사용 불가)


class ComplianceChecker:
    """
    종합 규제 준수 검증기

    Citation, 설명 의무, 할루시네이션 방지 등을 종합적으로 검증합니다.
    """

    def __init__(
        self,
        min_confidence: float = 0.7,
        min_citations: int = 1,
        auto_fix: bool = True
    ):
        """
        Args:
            min_confidence: 최소 Citation confidence
            min_citations: 최소 Citation 개수
            auto_fix: 자동 수정 여부 (면책 고지 자동 추가 등)
        """
        self.min_confidence = min_confidence
        self.min_citations = min_citations
        self.auto_fix = auto_fix

    def check_compliance(
        self,
        query: str,
        answer: str,
        citations: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        종합 규제 준수 검증을 수행합니다.

        Args:
            query: 사용자 질의
            answer: 답변
            citations: Citation 리스트
            metadata: 추가 메타데이터

        Returns:
            Dict[str, Any]: 검증 결과
                {
                    "compliance_level": "pass" | "warning" | "fail",
                    "compliant": bool,
                    "checks": {
                        "citations": {...},
                        "explanation_duty": {...},
                        "hallucination_risk": {...},
                    },
                    "issues": List[str],
                    "warnings": List[str],
                    "recommendations": List[str],
                    "fixed_answer": str (if auto_fix=True),
                    "traceability_report": {...},
                }
        """
        issues = []
        warnings = []
        recommendations = []

        # 1. Citation 검증
        citations_valid, citation_errors = CitationValidator.validate_citations(citations)
        coverage_ok, coverage_warning = CitationValidator.check_citation_coverage(
            answer, citations, min_citations=self.min_citations
        )
        risk_level, risk_warnings = CitationValidator.check_hallucination_risk(
            answer, citations, confidence_threshold=self.min_confidence
        )

        citation_check = {
            "valid": citations_valid,
            "errors": citation_errors,
            "coverage_ok": coverage_ok,
            "coverage_warning": coverage_warning,
            "risk_level": risk_level,
            "risk_warnings": risk_warnings,
        }

        # Citation 이슈 수집
        if not citations_valid:
            issues.extend(citation_errors)

        if not coverage_ok and coverage_warning:
            warnings.append(coverage_warning)

        if risk_level == "high":
            issues.append("할루시네이션 위험도가 높습니다")
        elif risk_level == "medium":
            warnings.append("할루시네이션 위험도가 중간입니다")

        # 2. 설명 의무 검증
        explanation_result = ExplanationDutyChecker.validate_explanation_duty(
            query, answer, auto_fix=self.auto_fix
        )

        explanation_check = {
            "compliant": explanation_result["compliant"],
            "category": explanation_result["category"],
            "issues": explanation_result["issues"],
            "warnings": explanation_result["warnings"],
            "has_disclaimer": explanation_result["has_disclaimer"],
        }

        # 설명 의무 이슈 수집
        if not explanation_result["compliant"]:
            issues.extend(explanation_result["issues"])

        if explanation_result["warnings"]:
            for warning_dict in explanation_result["warnings"]:
                warnings.append(f"{warning_dict['keyword']}: {warning_dict['warning']}")

        # 3. 추가 권장 사항
        if len(citations) < 2 and len(answer) > 300:
            recommendations.append("긴 답변에는 2개 이상의 근거 자료를 추가하는 것이 좋습니다")

        if not explanation_result["has_disclaimer"]:
            recommendations.append("답변에 면책 고지를 추가하는 것이 좋습니다")

        # 4. 전체 Compliance Level 판정
        compliance_level = self._determine_compliance_level(
            issues=issues,
            warnings=warnings,
            risk_level=risk_level,
            citations_valid=citations_valid,
            explanation_compliant=explanation_result["compliant"]
        )

        # 5. 답변 자동 수정 (auto_fix=True인 경우)
        fixed_answer = answer

        if self.auto_fix:
            # 면책 고지 추가
            if explanation_result["fixed_answer"]:
                fixed_answer = explanation_result["fixed_answer"]

            # Citation footer 추가
            fixed_answer = CitationValidator.append_citation_footer(fixed_answer, citations)

        # 6. Traceability Report 생성
        traceability_report = CitationValidator.create_traceability_report(
            query=query,
            answer=answer,
            citations=citations,
            metadata=metadata
        )

        # 결과 조합
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "compliance_level": compliance_level,
            "compliant": compliance_level == ComplianceLevel.PASS,
            "checks": {
                "citations": citation_check,
                "explanation_duty": explanation_check,
            },
            "issues": issues,
            "warnings": warnings,
            "recommendations": recommendations,
            "fixed_answer": fixed_answer if self.auto_fix else None,
            "traceability_report": traceability_report,
        }

        # 로그 출력
        if compliance_level == ComplianceLevel.FAIL:
            logger.warning(
                f"Compliance check FAILED: {len(issues)} issues, "
                f"risk_level={risk_level}"
            )
        elif compliance_level == ComplianceLevel.WARNING:
            logger.info(
                f"Compliance check WARNING: {len(warnings)} warnings"
            )
        else:
            logger.info("Compliance check PASSED")

        return result

    def _determine_compliance_level(
        self,
        issues: List[str],
        warnings: List[str],
        risk_level: str,
        citations_valid: bool,
        explanation_compliant: bool
    ) -> str:
        """
        전체 Compliance Level을 판정합니다.

        Args:
            issues: 이슈 리스트
            warnings: 경고 리스트
            risk_level: 할루시네이션 위험도
            citations_valid: Citation 유효성
            explanation_compliant: 설명 의무 준수 여부

        Returns:
            str: "pass", "warning", or "fail"
        """
        # Fail 조건
        if len(issues) > 0:
            return ComplianceLevel.FAIL

        if risk_level == "high":
            return ComplianceLevel.FAIL

        if not citations_valid:
            return ComplianceLevel.FAIL

        # Warning 조건
        if len(warnings) > 0:
            return ComplianceLevel.WARNING

        if risk_level == "medium":
            return ComplianceLevel.WARNING

        if not explanation_compliant:
            return ComplianceLevel.WARNING

        # Pass
        return ComplianceLevel.PASS

    @staticmethod
    def create_compliance_report_summary(result: Dict[str, Any]) -> str:
        """
        규제 준수 검증 결과를 사람이 읽기 쉬운 요약 보고서로 변환합니다.

        Args:
            result: check_compliance() 결과

        Returns:
            str: 요약 보고서 (마크다운 형식)
        """
        lines = ["# 📋 규제 준수 검증 보고서", ""]

        # 1. 전체 결과
        level = result["compliance_level"]
        level_emoji = {
            "pass": "✅",
            "warning": "⚠️",
            "fail": "❌",
        }.get(level, "❓")

        lines.append(f"## 전체 결과: {level_emoji} {level.upper()}")
        lines.append("")

        # 2. 이슈
        if result["issues"]:
            lines.append("### ❌ 발견된 이슈")
            for issue in result["issues"]:
                lines.append(f"- {issue}")
            lines.append("")

        # 3. 경고
        if result["warnings"]:
            lines.append("### ⚠️ 경고")
            for warning in result["warnings"]:
                lines.append(f"- {warning}")
            lines.append("")

        # 4. 권장 사항
        if result["recommendations"]:
            lines.append("### 💡 권장 사항")
            for rec in result["recommendations"]:
                lines.append(f"- {rec}")
            lines.append("")

        # 5. 상세 검증 결과
        lines.append("### 📊 상세 검증 결과")
        lines.append("")

        # Citation 검증
        citation_check = result["checks"]["citations"]
        lines.append(f"**Citation 검증**:")
        lines.append(f"- 유효성: {'✅' if citation_check['valid'] else '❌'}")
        lines.append(f"- 충분성: {'✅' if citation_check['coverage_ok'] else '❌'}")
        lines.append(f"- 할루시네이션 위험도: {citation_check['risk_level']}")
        lines.append("")

        # 설명 의무 검증
        explanation_check = result["checks"]["explanation_duty"]
        lines.append(f"**설명 의무 검증**:")
        lines.append(f"- 준수 여부: {'✅' if explanation_check['compliant'] else '❌'}")
        lines.append(f"- 카테고리: {explanation_check['category']}")
        lines.append(f"- 면책 고지: {'✅' if explanation_check['has_disclaimer'] else '❌'}")
        lines.append("")

        # 6. Traceability
        if "traceability_report" in result:
            report = result["traceability_report"]
            lines.append("### 🔍 추적 정보")
            lines.append(f"- Citation 개수: {report['citations_count']}")
            lines.append(f"- 답변 길이: {report['answer_length']} 자")
            lines.append("")

        return "\n".join(lines)


# Convenience function
def check_answer_compliance(
    query: str,
    answer: str,
    citations: List[Dict[str, Any]],
    auto_fix: bool = True
) -> Dict[str, Any]:
    """
    답변의 규제 준수 여부를 검증합니다 (편의 함수).

    Args:
        query: 사용자 질의
        answer: 답변
        citations: Citation 리스트
        auto_fix: 자동 수정 여부

    Returns:
        Dict[str, Any]: 검증 결과
    """
    checker = ComplianceChecker(auto_fix=auto_fix)
    return checker.check_compliance(query, answer, citations)
