"""
Response Generator

검색 결과를 자연어 응답으로 변환합니다.
"""
import time
from typing import List, Dict, Any, Optional
from loguru import logger

from app.models.query import QueryAnalysisResult
from app.models.graph_query import GraphQueryResponse
from app.models.vector_search import SearchResponse
from app.models.response import (
    ResponseGenerationRequest,
    GeneratedResponse,
    AnswerFormat,
    Citation,
    CitationType,
    Table,
    TableRow,
    Comparison,
    ComparisonItem,
    AnswerSegment,
)
from app.services.response.template_manager import (
    ResponseTemplateManager,
    AdvancedTemplateRenderer,
)


class ResponseGenerator:
    """
    응답 생성기

    검색 결과를 사용자 친화적인 자연어 응답으로 변환합니다.
    """

    def __init__(self, template_manager: Optional[ResponseTemplateManager] = None):
        """
        Args:
            template_manager: 템플릿 관리자
        """
        self.template_manager = template_manager or ResponseTemplateManager()
        self.renderer = AdvancedTemplateRenderer()

    async def generate(
        self, request: ResponseGenerationRequest
    ) -> GeneratedResponse:
        """
        응답 생성

        Args:
            request: 응답 생성 요청

        Returns:
            생성된 응답
        """
        start_time = time.time()

        # 결과 확인
        has_results = bool(request.search_results)

        # 템플릿 선택
        template = self.template_manager.select_best_template(
            intent=request.intent, has_results=has_results
        )

        if not template:
            logger.warning(f"No template found for intent: {request.intent}")
            return self._generate_fallback_response(request)

        # 의도별 응답 생성
        if request.intent == "coverage_amount":
            response = self._generate_coverage_amount_response(request, template)
        elif request.intent == "coverage_check":
            response = self._generate_coverage_check_response(request, template)
        elif request.intent == "disease_comparison":
            response = self._generate_comparison_response(request, template)
        elif request.intent == "coverage_comparison":
            response = self._generate_comparison_response(request, template)
        elif request.intent == "exclusion_check":
            response = self._generate_exclusions_response(request, template)
        elif request.intent == "waiting_period":
            response = self._generate_waiting_period_response(request, template)
        elif request.intent == "age_limit":
            response = self._generate_age_limit_response(request, template)
        elif request.intent == "product_summary":
            response = self._generate_product_summary_response(request, template)
        else:
            response = self._generate_general_response(request, template)

        # 출처 추가
        if request.include_citations:
            response.citations = self._extract_citations(request.search_results)

        # 후속 질문 제안
        if request.include_follow_ups:
            response.follow_up_suggestions = self._generate_follow_ups(
                request.intent, request.query
            )

        # 생성 시간
        response.generation_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Generated response in {response.generation_time_ms:.2f}ms "
            f"(format: {response.format})"
        )

        return response

    def _generate_coverage_amount_response(
        self, request: ResponseGenerationRequest, template
    ) -> GeneratedResponse:
        """보장 금액 응답 생성"""
        results = request.search_results

        if not results:
            return self._generate_no_results_response(request)

        # 질병명 추출 (첫 번째 결과에서)
        disease_name = results[0].get("disease_name", "해당 질병")

        # 보장 목록 생성
        coverages = []
        total_amount = 0

        for result in results:
            coverage_name = result.get("coverage_name", "")
            amount = result.get("amount", 0)

            if coverage_name and amount:
                coverages.append({"coverage_name": coverage_name, "amount": amount})
                total_amount += amount

        # 보장 목록 렌더링
        coverage_list = self.renderer.render_coverage_list(coverages)

        # 템플릿 변수
        variables = {
            "disease_name": disease_name,
            "coverage_list": coverage_list,
            "total_amount": self.renderer.format_amount(total_amount),
        }

        # 응답 생성
        answer = template.render(variables)

        # 테이블 생성
        table = self._create_coverage_table(coverages)

        return GeneratedResponse(
            answer=answer,
            format=AnswerFormat.TABLE,
            table=table,
            confidence_score=0.9,
        )

    def _generate_coverage_check_response(
        self, request: ResponseGenerationRequest, template
    ) -> GeneratedResponse:
        """보장 여부 확인 응답 생성"""
        results = request.search_results

        if not results:
            return self._generate_no_results_response(request)

        result = results[0]
        disease_name = result.get("disease_name", "해당 질병")
        is_covered = result.get("is_covered", False)
        coverages = result.get("coverages", [])

        # 보장 여부에 따라 템플릿 선택
        if is_covered and coverages:
            template = self.template_manager.get_template("coverage_check_yes")
            coverage_list = self.renderer.render_list(
                [c.get("coverage_name", "") for c in coverages if c.get("coverage_name")]
            )
            variables = {"disease_name": disease_name, "coverage_list": coverage_list}
        else:
            template = self.template_manager.get_template("coverage_check_no")
            variables = {"disease_name": disease_name}

        answer = template.render(variables)

        return GeneratedResponse(
            answer=answer, format=AnswerFormat.TEXT, confidence_score=0.95
        )

    def _generate_comparison_response(
        self, request: ResponseGenerationRequest, template
    ) -> GeneratedResponse:
        """비교 응답 생성"""
        results = request.search_results

        if not results or len(results) == 0:
            return self._generate_no_results_response(request)

        result = results[0]

        # 비교 데이터 추출
        item1_name = result.get("disease1_name") or result.get("coverage1_name", "항목1")
        item2_name = result.get("disease2_name") or result.get("coverage2_name", "항목2")

        # 공통점과 차이점
        similarities = []
        differences = []

        # 질병 비교인 경우
        if "cov1" in result and "cov2" in result:
            cov1 = result["cov1"]
            cov2 = result["cov2"]

            cov1_names = {c.get("name") for c in cov1 if c.get("name")}
            cov2_names = {c.get("name") for c in cov2 if c.get("name")}

            common = cov1_names & cov2_names
            only1 = cov1_names - cov2_names
            only2 = cov2_names - cov1_names

            if common:
                similarities.append(f"공통 보장: {', '.join(common)}")

            if only1:
                differences.append(f"{item1_name}만 해당: {', '.join(only1)}")
            if only2:
                differences.append(f"{item2_name}만 해당: {', '.join(only2)}")

        # 보장 비교인 경우
        if "coverage1_diseases" in result and "coverage2_diseases" in result:
            dis1 = result["coverage1_diseases"]
            dis2 = result["coverage2_diseases"]

            dis1_names = {d.get("name") for d in dis1 if d.get("name")}
            dis2_names = {d.get("name") for d in dis2 if d.get("name")}

            common = dis1_names & dis2_names
            only1 = dis1_names - dis2_names
            only2 = dis2_names - dis1_names

            if common:
                similarities.append(f"공통 질병: {', '.join(common)}")

            if only1:
                differences.append(f"{item1_name}만 보장: {', '.join(only1)}")
            if only2:
                differences.append(f"{item2_name}만 보장: {', '.join(only2)}")

        # 템플릿 렌더링
        variables = {
            "item1_name": item1_name,
            "item2_name": item2_name,
            "similarities": "\n".join(f"- {s}" for s in similarities)
            if similarities
            else "없음",
            "differences": "\n".join(f"- {d}" for d in differences)
            if differences
            else "없음",
        }

        answer = template.render(variables)

        # Comparison 객체 생성
        comparison = Comparison(
            item1=ComparisonItem(name=item1_name, attributes=result),
            item2=ComparisonItem(name=item2_name, attributes=result),
            differences=[{"text": d} for d in differences],
            similarities=[{"text": s} for s in similarities],
        )

        return GeneratedResponse(
            answer=answer,
            format=AnswerFormat.COMPARISON,
            comparison=comparison,
            confidence_score=0.85,
        )

    def _generate_exclusions_response(
        self, request: ResponseGenerationRequest, template
    ) -> GeneratedResponse:
        """제외 항목 응답 생성"""
        results = request.search_results

        if not results:
            return GeneratedResponse(
                answer="제외되는 질병 정보를 찾을 수 없습니다.",
                format=AnswerFormat.TEXT,
                confidence_score=0.5,
            )

        # 제외 질병 목록
        exclusions = [r.get("disease_name", "") for r in results if r.get("disease_name")]

        exclusion_list = self.renderer.render_list(exclusions)

        variables = {"exclusion_list": exclusion_list}

        answer = template.render(variables)

        return GeneratedResponse(
            answer=answer,
            format=AnswerFormat.LIST,
            list_items=exclusions,
            confidence_score=0.9,
        )

    def _generate_waiting_period_response(
        self, request: ResponseGenerationRequest, template
    ) -> GeneratedResponse:
        """대기기간 응답 생성"""
        results = request.search_results

        if not results:
            return self._generate_no_results_response(request)

        result = results[0]
        coverage_name = result.get("coverage_name", "해당 보장")
        days = result.get("waiting_period_days", 0)

        variables = {
            "coverage_name": coverage_name,
            "days": days,
        }

        answer = template.render(variables)

        return GeneratedResponse(
            answer=answer, format=AnswerFormat.TEXT, confidence_score=0.95
        )

    def _generate_age_limit_response(
        self, request: ResponseGenerationRequest, template
    ) -> GeneratedResponse:
        """나이 제한 응답 생성"""
        results = request.search_results

        if not results:
            return self._generate_no_results_response(request)

        result = results[0]
        min_age = result.get("min_age", 0)
        max_age = result.get("max_age", 100)

        variables = {"min_age": min_age, "max_age": max_age}

        answer = template.render(variables)

        return GeneratedResponse(
            answer=answer, format=AnswerFormat.TEXT, confidence_score=0.95
        )

    def _generate_product_summary_response(
        self, request: ResponseGenerationRequest, template
    ) -> GeneratedResponse:
        """상품 요약 응답 생성"""
        results = request.search_results

        if not results:
            return self._generate_no_results_response(request)

        result = results[0]
        product_name = result.get("product_name", "보험 상품")
        coverages = result.get("main_coverages", [])

        # 주요 보장 렌더링
        main_coverages = self.renderer.render_coverage_list(coverages)

        variables = {
            "product_name": product_name,
            "description": f"{product_name}은(는) 다양한 보장을 제공하는 보험 상품입니다.",
            "main_coverages": main_coverages,
        }

        answer = template.render(variables)

        return GeneratedResponse(
            answer=answer, format=AnswerFormat.SUMMARY, confidence_score=0.85
        )

    def _generate_general_response(
        self, request: ResponseGenerationRequest, template
    ) -> GeneratedResponse:
        """일반 응답 생성"""
        results = request.search_results

        if not results:
            return self._generate_no_results_response(request)

        # 첫 번째 결과의 텍스트 내용 추출
        result = results[0]
        answer_text = result.get("clause_text") or result.get("text", "정보를 찾았습니다.")

        variables = {"answer": answer_text}

        answer = template.render(variables)

        return GeneratedResponse(
            answer=answer, format=AnswerFormat.TEXT, confidence_score=0.7
        )

    def _generate_no_results_response(
        self, request: ResponseGenerationRequest
    ) -> GeneratedResponse:
        """결과 없음 응답 생성"""
        template = self.template_manager.get_template("no_results")

        variables = {"query": request.query}

        answer = template.render(variables)

        return GeneratedResponse(
            answer=answer, format=AnswerFormat.TEXT, confidence_score=0.0
        )

    def _generate_fallback_response(
        self, request: ResponseGenerationRequest
    ) -> GeneratedResponse:
        """폴백 응답 생성"""
        answer = f"'{request.query}'에 대한 정보를 처리하고 있습니다."

        return GeneratedResponse(
            answer=answer, format=AnswerFormat.TEXT, confidence_score=0.3
        )

    def _create_coverage_table(self, coverages: List[Dict]) -> Table:
        """보장 테이블 생성"""
        headers = ["보장명", "보장 금액"]
        rows = []

        for coverage in coverages:
            name = coverage.get("coverage_name", "")
            amount = coverage.get("amount", 0)
            formatted_amount = self.renderer.format_amount(amount)

            rows.append(TableRow(cells=[name, formatted_amount]))

        return Table(headers=headers, rows=rows, caption="보장 내역")

    def _extract_citations(self, results: List[Dict]) -> List[Citation]:
        """출처 추출"""
        citations = []

        for result in results:
            # 조항 출처
            if "clause_id" in result:
                citation = Citation(
                    citation_type=CitationType.CLAUSE,
                    source_id=result["clause_id"],
                    source_text=result.get("clause_text", "")[:100],
                    article_num=result.get("article_num"),
                    relevance_score=result.get("score", 0.8),
                )
                citations.append(citation)

        return citations[:5]  # 최대 5개

    def _generate_follow_ups(self, intent: str, query: str) -> List[str]:
        """후속 질문 제안 생성"""
        follow_ups = []

        if intent == "coverage_amount":
            follow_ups = [
                "대기기간은 얼마나 되나요?",
                "보장 조건이 있나요?",
                "다른 질병의 보장 금액도 알려주세요",
            ]
        elif intent == "coverage_check":
            follow_ups = [
                "보장 금액은 얼마인가요?",
                "언제부터 보장받을 수 있나요?",
                "제외되는 경우는 무엇인가요?",
            ]
        elif intent == "waiting_period":
            follow_ups = [
                "보장 금액은 얼마인가요?",
                "나이 제한이 있나요?",
            ]

        return follow_ups[:3]  # 최대 3개
