"""
Citation Validator

답변의 근거(Citation) 검증 및 출처 추적
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from loguru import logger


class CitationValidator:
    """
    Citation 검증 클래스

    답변에 포함된 인용(Citation)의 유효성을 검증하고,
    할루시네이션을 방지합니다.
    """

    @staticmethod
    def validate_citation(citation: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        단일 Citation을 검증합니다.

        Args:
            citation: Citation 데이터
                {
                    "document_id": "...",
                    "article_num": "제1조",
                    "title": "용어의 정의",
                    "page": 5,
                    "text": "...",
                    "confidence": 0.92
                }

        Returns:
            Tuple[bool, Optional[str]]: (유효 여부, 에러 메시지)
        """
        required_fields = ["document_id", "text"]

        # 필수 필드 확인
        for field in required_fields:
            if field not in citation or not citation[field]:
                return False, f"Missing required field: {field}"

        # Confidence 확인 (있는 경우)
        if "confidence" in citation:
            confidence = citation["confidence"]
            if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
                return False, f"Invalid confidence score: {confidence}"

            # Confidence가 너무 낮으면 경고
            if confidence < 0.7:
                logger.warning(
                    f"Low confidence citation: {confidence} for document {citation['document_id']}"
                )

        # Text 길이 확인 (너무 짧거나 긴 경우 의심)
        text = citation["text"]
        if len(text) < 10:
            return False, "Citation text too short (< 10 characters)"
        if len(text) > 5000:
            return False, "Citation text too long (> 5000 characters)"

        return True, None

    @staticmethod
    def validate_citations(citations: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        여러 Citations를 검증합니다.

        Args:
            citations: Citation 리스트

        Returns:
            Tuple[bool, List[str]]: (모두 유효 여부, 에러 메시지 리스트)
        """
        if not citations:
            return False, ["No citations provided"]

        errors = []

        for idx, citation in enumerate(citations):
            valid, error = CitationValidator.validate_citation(citation)
            if not valid:
                errors.append(f"Citation {idx + 1}: {error}")

        all_valid = len(errors) == 0
        return all_valid, errors

    @staticmethod
    def check_citation_coverage(
        answer: str,
        citations: List[Dict[str, Any]],
        min_citations: int = 1
    ) -> Tuple[bool, Optional[str]]:
        """
        답변이 충분한 근거(Citation)를 가지고 있는지 확인합니다.

        Args:
            answer: 답변 텍스트
            citations: Citation 리스트
            min_citations: 최소 필요한 Citation 개수

        Returns:
            Tuple[bool, Optional[str]]: (충분 여부, 경고 메시지)
        """
        if len(citations) < min_citations:
            return False, f"Insufficient citations: {len(citations)} < {min_citations}"

        # 답변 길이 대비 Citation 비율 확인
        answer_length = len(answer)
        if answer_length > 500 and len(citations) < 2:
            return False, "Long answer requires multiple citations (>= 2)"

        if answer_length > 1000 and len(citations) < 3:
            return False, "Very long answer requires multiple citations (>= 3)"

        return True, None

    @staticmethod
    def extract_source_reference(citation: Dict[str, Any]) -> str:
        """
        Citation에서 출처 참조 문자열을 생성합니다.

        Args:
            citation: Citation 데이터

        Returns:
            str: 출처 참조 (예: "약관 제1조 제3항 (5페이지)")
        """
        parts = []

        # 조항 번호
        if "article_num" in citation and citation["article_num"]:
            parts.append(f"{citation['article_num']}")

        # 조항 제목
        if "title" in citation and citation["title"]:
            parts.append(f"({citation['title']})")

        # 페이지
        if "page" in citation and citation["page"]:
            parts.append(f"{citation['page']}페이지")

        # Document ID (간략화)
        if "document_id" in citation:
            doc_id_short = str(citation["document_id"])[:8]
            parts.append(f"[문서: {doc_id_short}...]")

        reference = " ".join(parts) if parts else "출처 정보 없음"
        return reference

    @staticmethod
    def format_citations_for_display(citations: List[Dict[str, Any]]) -> str:
        """
        Citations를 사용자에게 표시할 형식으로 변환합니다.

        Args:
            citations: Citation 리스트

        Returns:
            str: 포맷된 출처 문자열
        """
        if not citations:
            return "근거 자료 없음"

        formatted_lines = ["## 📚 근거 자료"]
        formatted_lines.append("")

        for idx, citation in enumerate(citations, 1):
            reference = CitationValidator.extract_source_reference(citation)
            formatted_lines.append(f"{idx}. {reference}")

            # Confidence score (있는 경우)
            if "confidence" in citation:
                confidence_pct = int(citation["confidence"] * 100)
                formatted_lines.append(f"   - 신뢰도: {confidence_pct}%")

        return "\n".join(formatted_lines)

    @staticmethod
    def append_citation_footer(answer: str, citations: List[Dict[str, Any]]) -> str:
        """
        답변에 Citation footer를 추가합니다.

        Args:
            answer: 원본 답변
            citations: Citation 리스트

        Returns:
            str: Citation footer가 추가된 답변
        """
        if not citations:
            # Citation이 없는 경우 경고 추가
            footer = "\n\n---\n⚠️ **주의**: 이 답변은 약관 근거가 부족할 수 있습니다. 반드시 실제 약관을 확인하시기 바랍니다."
            return answer + footer

        # Citation footer 추가
        citations_display = CitationValidator.format_citations_for_display(citations)
        footer = f"\n\n---\n{citations_display}\n\n**ℹ️ 안내**: 위 답변은 실제 약관 조항에 근거합니다. 자세한 내용은 해당 약관을 참고하시기 바랍니다."

        return answer + footer

    @staticmethod
    def check_hallucination_risk(
        answer: str,
        citations: List[Dict[str, Any]],
        confidence_threshold: float = 0.7
    ) -> Tuple[str, List[str]]:
        """
        할루시네이션 위험도를 평가합니다.

        Args:
            answer: 답변 텍스트
            citations: Citation 리스트
            confidence_threshold: Confidence 임계값

        Returns:
            Tuple[str, List[str]]: (위험도 레벨, 경고 메시지 리스트)
                위험도: "low", "medium", "high"
        """
        warnings = []
        risk_score = 0

        # 1. Citation 개수 확인
        if len(citations) == 0:
            risk_score += 40
            warnings.append("답변에 근거 자료가 없습니다")
        elif len(citations) == 1 and len(answer) > 300:
            risk_score += 20
            warnings.append("긴 답변에 비해 근거 자료가 부족합니다")

        # 2. Confidence score 확인
        if citations:
            low_confidence_count = sum(
                1 for c in citations
                if "confidence" in c and c["confidence"] < confidence_threshold
            )
            if low_confidence_count > 0:
                risk_score += 15 * low_confidence_count
                warnings.append(f"{low_confidence_count}개의 근거 자료가 낮은 신뢰도를 보입니다")

        # 3. 답변 내 수치 확인 (금액, 날짜 등)
        import re
        numbers = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?', answer)
        if len(numbers) > 3 and len(citations) < 2:
            risk_score += 15
            warnings.append("구체적인 수치가 많지만 근거 자료가 부족합니다")

        # 4. 단정적 표현 확인
        definitive_keywords = ["반드시", "절대", "100%", "전액", "무조건"]
        definitive_count = sum(1 for keyword in definitive_keywords if keyword in answer)
        if definitive_count > 0:
            risk_score += 10
            warnings.append("단정적 표현이 포함되어 있습니다 - 주의가 필요합니다")

        # 위험도 판정
        if risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "medium"
        else:
            risk_level = "low"

        return risk_level, warnings

    @staticmethod
    def create_traceability_report(
        query: str,
        answer: str,
        citations: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        추적 가능성 보고서를 생성합니다.

        Args:
            query: 사용자 질의
            answer: 답변
            citations: Citation 리스트
            metadata: 추가 메타데이터

        Returns:
            Dict[str, Any]: 추적 가능성 보고서
        """
        # Citation 검증
        citations_valid, citation_errors = CitationValidator.validate_citations(citations)
        coverage_ok, coverage_warning = CitationValidator.check_citation_coverage(answer, citations)
        risk_level, risk_warnings = CitationValidator.check_hallucination_risk(answer, citations)

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "answer_length": len(answer),
            "citations_count": len(citations),
            "validation": {
                "citations_valid": citations_valid,
                "citation_errors": citation_errors,
                "coverage_ok": coverage_ok,
                "coverage_warning": coverage_warning,
            },
            "risk_assessment": {
                "level": risk_level,
                "warnings": risk_warnings,
            },
            "citations": [
                {
                    "reference": CitationValidator.extract_source_reference(c),
                    "confidence": c.get("confidence", 0.0),
                    "document_id": c.get("document_id"),
                    "article": c.get("article_num"),
                }
                for c in citations
            ],
            "compliance_status": "pass" if (citations_valid and coverage_ok and risk_level != "high") else "fail",
            "metadata": metadata or {},
        }

        return report
