"""
Explanation Duty Checker

보험 설명 의무 준수 검증
"""

from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from loguru import logger


class ExplanationCategory(str, Enum):
    """설명 의무 카테고리"""
    COVERAGE = "coverage"  # 보장 내용
    EXCLUSION = "exclusion"  # 면책 사항
    WAITING_PERIOD = "waiting_period"  # 대기 기간
    REDUCTION_PERIOD = "reduction_period"  # 감액 기간
    PREMIUM = "premium"  # 보험료
    CANCELLATION = "cancellation"  # 해지 환급금
    RENEWAL = "renewal"  # 갱신
    OTHER = "other"  # 기타


class ExplanationDutyChecker:
    """
    설명 의무 준수 검증 클래스

    금융감독원의 보험 설명 의무 규정을 준수하는지 검증합니다.
    """

    # 필수 설명 키워드 (카테고리별)
    REQUIRED_KEYWORDS = {
        ExplanationCategory.COVERAGE: {
            "keywords": ["보장", "지급", "담보"],
            "description": "보장 내용 설명 필요"
        },
        ExplanationCategory.EXCLUSION: {
            "keywords": ["면책", "제외", "보상하지 않", "보장하지 않"],
            "description": "면책 사항 명시 필요"
        },
        ExplanationCategory.WAITING_PERIOD: {
            "keywords": ["대기기간", "대기 기간", "면책기간", "면책 기간"],
            "description": "대기기간 설명 필요"
        },
        ExplanationCategory.REDUCTION_PERIOD: {
            "keywords": ["감액기간", "감액 기간", "50%"],
            "description": "감액기간 설명 필요"
        },
        ExplanationCategory.PREMIUM: {
            "keywords": ["보험료", "납입", "월납"],
            "description": "보험료 정보 포함 필요"
        },
        ExplanationCategory.CANCELLATION: {
            "keywords": ["해지", "환급금", "해약"],
            "description": "해지 환급금 정보 포함 필요"
        },
    }

    # 주의 필요 키워드 (사용 시 상세 설명 필요)
    CAUTION_KEYWORDS = {
        "전액": "전액 지급 여부는 약관 조건에 따라 다를 수 있습니다",
        "100%": "100% 보장 여부는 약관 조건을 확인해야 합니다",
        "무조건": "무조건적인 표현은 오해를 유발할 수 있습니다",
        "반드시": "반드시 지급되는 것은 아닐 수 있습니다",
        "모든": "모든 경우에 해당되지 않을 수 있습니다",
    }

    # 금지 키워드 (사용 불가)
    PROHIBITED_KEYWORDS = [
        "무조건 가입",
        "100% 수익",
        "손해 없음",
        "위험 전혀 없음",
    ]

    @staticmethod
    def detect_explanation_category(query: str, answer: str) -> ExplanationCategory:
        """
        질의와 답변에서 설명 의무 카테고리를 감지합니다.

        Args:
            query: 사용자 질의
            answer: 답변

        Returns:
            ExplanationCategory: 감지된 카테고리
        """
        combined_text = f"{query} {answer}".lower()

        # 키워드 매칭으로 카테고리 감지
        if any(keyword in combined_text for keyword in ["면책", "제외", "안 되", "보장하지"]):
            return ExplanationCategory.EXCLUSION

        if any(keyword in combined_text for keyword in ["대기기간", "대기 기간", "면책기간"]):
            return ExplanationCategory.WAITING_PERIOD

        if any(keyword in combined_text for keyword in ["감액", "50%"]):
            return ExplanationCategory.REDUCTION_PERIOD

        if any(keyword in combined_text for keyword in ["보험료", "납입", "월납"]):
            return ExplanationCategory.PREMIUM

        if any(keyword in combined_text for keyword in ["해지", "환급", "해약"]):
            return ExplanationCategory.CANCELLATION

        if any(keyword in combined_text for keyword in ["보장", "지급", "담보"]):
            return ExplanationCategory.COVERAGE

        return ExplanationCategory.OTHER

    @staticmethod
    def check_required_keywords(
        answer: str,
        category: ExplanationCategory
    ) -> Tuple[bool, List[str]]:
        """
        답변에 필수 설명 키워드가 포함되어 있는지 확인합니다.

        Args:
            answer: 답변 텍스트
            category: 설명 의무 카테고리

        Returns:
            Tuple[bool, List[str]]: (키워드 포함 여부, 누락된 설명 리스트)
        """
        if category not in ExplanationDutyChecker.REQUIRED_KEYWORDS:
            return True, []

        required_info = ExplanationDutyChecker.REQUIRED_KEYWORDS[category]
        keywords = required_info["keywords"]
        description = required_info["description"]

        # 키워드 중 하나라도 포함되어 있으면 OK
        has_keyword = any(keyword in answer for keyword in keywords)

        if not has_keyword:
            return False, [description]

        return True, []

    @staticmethod
    def check_caution_keywords(answer: str) -> List[Dict[str, str]]:
        """
        주의가 필요한 키워드를 확인합니다.

        Args:
            answer: 답변 텍스트

        Returns:
            List[Dict[str, str]]: 발견된 주의 키워드와 경고 메시지
        """
        warnings = []

        for keyword, warning in ExplanationDutyChecker.CAUTION_KEYWORDS.items():
            if keyword in answer:
                warnings.append({
                    "keyword": keyword,
                    "warning": warning,
                })

        return warnings

    @staticmethod
    def check_prohibited_keywords(answer: str) -> List[str]:
        """
        금지된 키워드를 확인합니다.

        Args:
            answer: 답변 텍스트

        Returns:
            List[str]: 발견된 금지 키워드 리스트
        """
        found_prohibited = []

        for keyword in ExplanationDutyChecker.PROHIBITED_KEYWORDS:
            if keyword in answer:
                found_prohibited.append(keyword)

        return found_prohibited

    @staticmethod
    def check_disclaimer_present(answer: str) -> bool:
        """
        답변에 면책 고지가 포함되어 있는지 확인합니다.

        Args:
            answer: 답변 텍스트

        Returns:
            bool: 면책 고지 포함 여부
        """
        disclaimer_keywords = [
            "약관을 확인",
            "약관 참조",
            "실제 약관",
            "상세 내용은",
            "자세한 사항",
        ]

        return any(keyword in answer for keyword in disclaimer_keywords)

    @staticmethod
    def generate_disclaimer(category: ExplanationCategory) -> str:
        """
        카테고리에 맞는 면책 고지를 생성합니다.

        Args:
            category: 설명 의무 카테고리

        Returns:
            str: 면책 고지 문구
        """
        disclaimers = {
            ExplanationCategory.COVERAGE: (
                "보장 내용은 약관에 따라 달라질 수 있으며, "
                "실제 보장 여부는 가입하신 상품의 약관을 반드시 확인하시기 바랍니다."
            ),
            ExplanationCategory.EXCLUSION: (
                "면책 사항은 약관에 상세히 명시되어 있으며, "
                "보장받지 못하는 경우가 있을 수 있으니 반드시 약관을 확인하시기 바랍니다."
            ),
            ExplanationCategory.WAITING_PERIOD: (
                "대기기간은 상품마다 다르며, 대기기간 중 발생한 사고는 보장받지 못할 수 있습니다. "
                "자세한 내용은 약관을 확인하시기 바랍니다."
            ),
            ExplanationCategory.REDUCTION_PERIOD: (
                "감액기간은 상품마다 다르며, 감액기간 중에는 보장금액이 감소합니다. "
                "자세한 내용은 약관을 확인하시기 바랍니다."
            ),
            ExplanationCategory.PREMIUM: (
                "보험료는 가입 조건에 따라 달라질 수 있으며, "
                "정확한 보험료는 실제 가입 시 확인하시기 바랍니다."
            ),
            ExplanationCategory.CANCELLATION: (
                "해지 환급금은 납입 기간 및 약관 조건에 따라 달라지며, "
                "자세한 내용은 약관을 확인하시기 바랍니다."
            ),
        }

        return disclaimers.get(
            category,
            "상세 내용은 실제 약관을 반드시 확인하시기 바랍니다."
        )

    @staticmethod
    def append_disclaimer_if_needed(
        answer: str,
        category: ExplanationCategory
    ) -> str:
        """
        필요시 답변에 면책 고지를 추가합니다.

        Args:
            answer: 원본 답변
            category: 설명 의무 카테고리

        Returns:
            str: 면책 고지가 추가된 답변
        """
        # 이미 면책 고지가 있으면 추가하지 않음
        if ExplanationDutyChecker.check_disclaimer_present(answer):
            return answer

        disclaimer = ExplanationDutyChecker.generate_disclaimer(category)
        return f"{answer}\n\n**ℹ️ 유의사항**: {disclaimer}"

    @staticmethod
    def validate_explanation_duty(
        query: str,
        answer: str,
        auto_fix: bool = False
    ) -> Dict[str, Any]:
        """
        설명 의무 준수 여부를 종합적으로 검증합니다.

        Args:
            query: 사용자 질의
            answer: 답변
            auto_fix: True이면 자동으로 면책 고지 추가

        Returns:
            Dict[str, Any]: 검증 결과
                {
                    "compliant": bool,
                    "category": str,
                    "issues": List[str],
                    "warnings": List[Dict],
                    "fixed_answer": str (if auto_fix=True),
                }
        """
        # 1. 카테고리 감지
        category = ExplanationDutyChecker.detect_explanation_category(query, answer)

        # 2. 필수 키워드 확인
        has_required, missing_explanations = ExplanationDutyChecker.check_required_keywords(
            answer, category
        )

        # 3. 주의 키워드 확인
        caution_warnings = ExplanationDutyChecker.check_caution_keywords(answer)

        # 4. 금지 키워드 확인
        prohibited_keywords = ExplanationDutyChecker.check_prohibited_keywords(answer)

        # 5. 면책 고지 확인
        has_disclaimer = ExplanationDutyChecker.check_disclaimer_present(answer)

        # Issues 수집
        issues = []

        if not has_required:
            issues.extend(missing_explanations)

        if prohibited_keywords:
            issues.append(f"금지된 표현 사용: {', '.join(prohibited_keywords)}")

        if not has_disclaimer and category != ExplanationCategory.OTHER:
            issues.append("면책 고지 누락")

        # Compliance 판정
        compliant = len(issues) == 0 and len(prohibited_keywords) == 0

        # Auto-fix: 면책 고지 자동 추가
        fixed_answer = answer
        if auto_fix and not has_disclaimer:
            fixed_answer = ExplanationDutyChecker.append_disclaimer_if_needed(
                answer, category
            )

        result = {
            "compliant": compliant,
            "category": category.value,
            "issues": issues,
            "warnings": caution_warnings,
            "has_disclaimer": has_disclaimer,
            "fixed_answer": fixed_answer if auto_fix else None,
        }

        return result
