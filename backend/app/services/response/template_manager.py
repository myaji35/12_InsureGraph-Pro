"""
Response Template Manager

응답 템플릿을 관리하고 렌더링합니다.
"""
from typing import Dict, List, Optional
from loguru import logger

from app.models.response import ResponseTemplate, AnswerFormat


class ResponseTemplateManager:
    """
    응답 템플릿 관리자

    의도별 응답 템플릿을 관리하고 렌더링합니다.
    """

    def __init__(self):
        """초기화"""
        self.templates: Dict[str, ResponseTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self):
        """기본 템플릿 로드"""
        # 1. 보장 금액 템플릿
        self.add_template(
            ResponseTemplate(
                template_id="coverage_amount",
                intent="coverage_amount",
                template="{disease_name}의 경우 다음과 같이 보장됩니다:\n\n"
                "{coverage_list}\n\n"
                "총 {total_amount}원의 보장을 받으실 수 있습니다.",
                format=AnswerFormat.TEXT,
                required_variables=["disease_name", "coverage_list", "total_amount"],
            )
        )

        # 2. 보장 여부 확인 템플릿
        self.add_template(
            ResponseTemplate(
                template_id="coverage_check_yes",
                intent="coverage_check",
                template="{disease_name}은(는) 보장 대상입니다.\n\n"
                "다음 보장에 포함됩니다:\n{coverage_list}",
                format=AnswerFormat.TEXT,
                required_variables=["disease_name", "coverage_list"],
            )
        )

        self.add_template(
            ResponseTemplate(
                template_id="coverage_check_no",
                intent="coverage_check",
                template="{disease_name}은(는) 현재 보장 대상이 아닙니다.\n\n"
                "보장받으시려면 다른 상품을 확인해보시기 바랍니다.",
                format=AnswerFormat.TEXT,
                required_variables=["disease_name"],
            )
        )

        # 3. 제외 항목 템플릿
        self.add_template(
            ResponseTemplate(
                template_id="exclusions",
                intent="exclusion_check",
                template="다음 질병은 보장에서 제외됩니다:\n\n{exclusion_list}",
                format=AnswerFormat.LIST,
                required_variables=["exclusion_list"],
            )
        )

        # 4. 대기기간 템플릿
        self.add_template(
            ResponseTemplate(
                template_id="waiting_period",
                intent="waiting_period",
                template="{coverage_name}의 대기기간은 {days}일입니다.\n\n"
                "계약일로부터 {days}일 이후에 발생한 사고에 대해 보장받으실 수 있습니다.",
                format=AnswerFormat.TEXT,
                required_variables=["coverage_name", "days"],
                optional_variables=["details"],
            )
        )

        # 5. 나이 제한 템플릿
        self.add_template(
            ResponseTemplate(
                template_id="age_limit",
                intent="age_limit",
                template="가입 가능 연령은 {min_age}세부터 {max_age}세까지입니다.",
                format=AnswerFormat.TEXT,
                required_variables=["min_age", "max_age"],
            )
        )

        # 6. 비교 템플릿
        self.add_template(
            ResponseTemplate(
                template_id="disease_comparison",
                intent="disease_comparison",
                template="{item1_name}과(와) {item2_name}의 보장 비교:\n\n"
                "**공통점:**\n{similarities}\n\n"
                "**차이점:**\n{differences}",
                format=AnswerFormat.COMPARISON,
                required_variables=[
                    "item1_name",
                    "item2_name",
                    "similarities",
                    "differences",
                ],
            )
        )

        # 7. 상품 요약 템플릿
        self.add_template(
            ResponseTemplate(
                template_id="product_summary",
                intent="product_summary",
                template="**{product_name}**\n\n"
                "{description}\n\n"
                "**주요 보장:**\n{main_coverages}",
                format=AnswerFormat.SUMMARY,
                required_variables=["product_name", "description", "main_coverages"],
            )
        )

        # 8. 일반 정보 템플릿
        self.add_template(
            ResponseTemplate(
                template_id="general_info",
                intent="general_info",
                template="{answer}",
                format=AnswerFormat.TEXT,
                required_variables=["answer"],
            )
        )

        # 9. 오류 템플릿
        self.add_template(
            ResponseTemplate(
                template_id="no_results",
                intent="unknown",
                template="죄송합니다. {query}에 대한 정보를 찾을 수 없습니다.\n\n"
                "다른 질문을 해주시거나, 더 구체적으로 질문해주세요.",
                format=AnswerFormat.TEXT,
                required_variables=["query"],
            )
        )

    def add_template(self, template: ResponseTemplate):
        """
        템플릿 추가

        Args:
            template: 응답 템플릿
        """
        self.templates[template.template_id] = template
        logger.debug(f"Added template: {template.template_id}")

    def get_template(self, template_id: str) -> Optional[ResponseTemplate]:
        """
        템플릿 조회

        Args:
            template_id: 템플릿 ID

        Returns:
            템플릿 또는 None
        """
        return self.templates.get(template_id)

    def get_templates_by_intent(self, intent: str) -> List[ResponseTemplate]:
        """
        의도별 템플릿 조회

        Args:
            intent: 질문 의도

        Returns:
            템플릿 리스트
        """
        return [t for t in self.templates.values() if t.intent == intent]

    def render_template(
        self, template_id: str, variables: Dict[str, any]
    ) -> Optional[str]:
        """
        템플릿 렌더링

        Args:
            template_id: 템플릿 ID
            variables: 변수

        Returns:
            렌더링된 텍스트
        """
        template = self.get_template(template_id)

        if not template:
            logger.warning(f"Template not found: {template_id}")
            return None

        try:
            return template.render(variables)
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return None

    def select_best_template(
        self, intent: str, has_results: bool = True
    ) -> Optional[ResponseTemplate]:
        """
        최적 템플릿 선택

        Args:
            intent: 질문 의도
            has_results: 결과 존재 여부

        Returns:
            선택된 템플릿
        """
        if not has_results:
            return self.get_template("no_results")

        # 의도별 템플릿 조회
        templates = self.get_templates_by_intent(intent)

        if templates:
            return templates[0]  # 첫 번째 템플릿 선택

        # 기본 템플릿
        return self.get_template("general_info")

    def list_templates(self) -> List[ResponseTemplate]:
        """모든 템플릿 목록"""
        return list(self.templates.values())


class AdvancedTemplateRenderer:
    """
    고급 템플릿 렌더러

    조건부 렌더링, 반복 등을 지원합니다.
    """

    @staticmethod
    def render_list(items: List[str], format: str = "bullet") -> str:
        """
        리스트 렌더링

        Args:
            items: 항목 리스트
            format: 형식 (bullet, numbered)

        Returns:
            렌더링된 리스트
        """
        if format == "bullet":
            return "\n".join(f"- {item}" for item in items)
        elif format == "numbered":
            return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))
        else:
            return "\n".join(items)

    @staticmethod
    def render_coverage_list(coverages: List[Dict]) -> str:
        """
        보장 목록 렌더링

        Args:
            coverages: 보장 정보 리스트

        Returns:
            렌더링된 보장 목록
        """
        lines = []
        for coverage in coverages:
            name = coverage.get("coverage_name", "알 수 없음")
            amount = coverage.get("amount", 0)

            if amount:
                formatted_amount = f"{amount:,}원"
                lines.append(f"- {name}: {formatted_amount}")
            else:
                lines.append(f"- {name}")

        return "\n".join(lines)

    @staticmethod
    def render_comparison(
        item1: Dict, item2: Dict, differences: List[Dict], similarities: List[Dict]
    ) -> str:
        """
        비교 렌더링

        Args:
            item1: 항목 1
            item2: 항목 2
            differences: 차이점
            similarities: 공통점

        Returns:
            렌더링된 비교
        """
        lines = []

        # 헤더
        lines.append(f"# {item1.get('name')} vs {item2.get('name')}\n")

        # 공통점
        if similarities:
            lines.append("## 공통점")
            for sim in similarities:
                if isinstance(sim, dict):
                    if "common" in sim:
                        for item in sim["common"]:
                            lines.append(f"- {item}")
                else:
                    lines.append(f"- {sim}")

        # 차이점
        if differences:
            lines.append("\n## 차이점")
            for diff in differences:
                if isinstance(diff, dict):
                    field = diff.get("field", "")
                    if "item1_only" in diff:
                        item1_only = diff["item1_only"]
                        lines.append(
                            f"- {item1.get('name')}만 해당: {', '.join(map(str, item1_only))}"
                        )
                    if "item2_only" in diff:
                        item2_only = diff["item2_only"]
                        lines.append(
                            f"- {item2.get('name')}만 해당: {', '.join(map(str, item2_only))}"
                        )
                    if "item1_value" in diff and "item2_value" in diff:
                        lines.append(
                            f"- {field}: {item1.get('name')} {diff['item1_value']:,}원 "
                            f"vs {item2.get('name')} {diff['item2_value']:,}원"
                        )

        return "\n".join(lines)

    @staticmethod
    def format_amount(amount: int) -> str:
        """금액 포맷팅"""
        if amount >= 100_000_000:  # 1억 이상
            billions = amount // 100_000_000
            remainder = amount % 100_000_000
            if remainder == 0:
                return f"{billions}억원"
            else:
                millions = remainder // 10_000
                return f"{billions}억 {millions}만원"
        elif amount >= 10_000:  # 1만 이상
            millions = amount // 10_000
            return f"{millions}만원"
        else:
            return f"{amount:,}원"

    @staticmethod
    def format_period(days: int) -> str:
        """기간 포맷팅"""
        if days >= 365:
            years = days // 365
            return f"{years}년"
        elif days >= 30:
            months = days // 30
            return f"{months}개월"
        else:
            return f"{days}일"
