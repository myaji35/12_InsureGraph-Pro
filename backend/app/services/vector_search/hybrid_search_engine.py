"""
Hybrid Search Engine

그래프 검색과 벡터 검색을 결합합니다.
"""
import time
from typing import List, Dict, Any, Optional
from loguru import logger

from app.models.query import QueryAnalysisResult, QueryType
from app.models.vector_search import (
    SearchRequest,
    SearchResponse,
    SearchStrategy,
    VectorSearchResult,
    HybridSearchResult,
    FusionMethod,
    ReciprocalRankFusion,
    SearchMetrics,
)
from app.services.graph_query.query_executor import GraphQueryExecutor
from app.services.vector_search.vector_search_engine import VectorSearchEngine


class HybridSearchEngine:
    """
    하이브리드 검색 엔진

    그래프 검색 (Neo4j Cypher)와 벡터 검색 (Vector Index)을 결합합니다.
    """

    def __init__(
        self,
        graph_executor: GraphQueryExecutor,
        vector_engine: VectorSearchEngine,
    ):
        """
        Args:
            graph_executor: 그래프 쿼리 실행기
            vector_engine: 벡터 검색 엔진
        """
        self.graph_executor = graph_executor
        self.vector_engine = vector_engine

    async def search(
        self, request: SearchRequest, analysis: QueryAnalysisResult
    ) -> SearchResponse:
        """
        하이브리드 검색 수행

        Args:
            request: 검색 요청
            analysis: 쿼리 분석 결과

        Returns:
            검색 응답
        """
        start_time = time.time()
        metrics = SearchMetrics()

        # 전략에 따른 검색
        if request.strategy == SearchStrategy.VECTOR_ONLY:
            results, metrics = await self._vector_only_search(request, metrics)
            graph_results = None
            vector_results_raw = results

        elif request.strategy == SearchStrategy.GRAPH_ONLY:
            results, graph_results, metrics = await self._graph_only_search(
                analysis, metrics
            )
            vector_results_raw = None

        elif request.strategy in [SearchStrategy.HYBRID, SearchStrategy.RERANKED]:
            results, graph_results, vector_results_raw, metrics = (
                await self._hybrid_search(request, analysis, metrics)
            )

        else:
            raise ValueError(f"Unknown search strategy: {request.strategy}")

        # 재랭킹
        reranked = False
        if request.reranking and request.reranking.enabled:
            rerank_start = time.time()
            results = self._rerank_results(results, request.query, request.reranking)
            metrics.reranking_time_ms = (time.time() - rerank_start) * 1000
            reranked = True

        # 최종 메트릭
        metrics.total_time_ms = (time.time() - start_time) * 1000
        metrics.final_results_count = len(results)

        # 통계 계산
        if results:
            scores = [r.score for r in results]
            metrics.avg_score = sum(scores) / len(scores)
            metrics.max_score = max(scores)
            metrics.min_score = min(scores)

        # 설명 생성
        explanation = self._generate_explanation(
            request.strategy, len(results), metrics
        )

        return SearchResponse(
            original_query=request.query,
            strategy=request.strategy,
            results=results,
            graph_results=graph_results,
            vector_results=vector_results_raw,
            total_count=len(results),
            search_time_ms=metrics.total_time_ms,
            reranked=reranked,
            explanation=explanation,
        )

    async def _vector_only_search(
        self, request: SearchRequest, metrics: SearchMetrics
    ) -> tuple[List[VectorSearchResult], SearchMetrics]:
        """벡터 검색만 수행"""
        vector_start = time.time()

        vector_results = await self.vector_engine.search(
            query=request.query,
            top_k=request.top_k,
            index_name=request.index_name,
            min_score=request.min_score,
        )

        metrics.vector_search_time_ms = (time.time() - vector_start) * 1000
        metrics.vector_results_count = len(vector_results.results)

        return vector_results.results, metrics

    async def _graph_only_search(
        self, analysis: QueryAnalysisResult, metrics: SearchMetrics
    ) -> tuple[List[VectorSearchResult], List[Dict[str, Any]], SearchMetrics]:
        """그래프 검색만 수행"""
        graph_start = time.time()

        graph_response = await self.graph_executor.execute(analysis)

        metrics.graph_search_time_ms = (time.time() - graph_start) * 1000
        metrics.graph_results_count = graph_response.result.total_count

        # 그래프 결과를 VectorSearchResult로 변환
        vector_results = self._convert_graph_to_vector_results(graph_response)

        return vector_results, graph_response.result.table, metrics

    async def _hybrid_search(
        self, request: SearchRequest, analysis: QueryAnalysisResult, metrics: SearchMetrics
    ) -> tuple[
        List[VectorSearchResult],
        List[Dict[str, Any]],
        List[VectorSearchResult],
        SearchMetrics,
    ]:
        """하이브리드 검색 (그래프 + 벡터)"""
        # 1. 그래프 검색
        graph_start = time.time()
        graph_response = await self.graph_executor.execute(analysis)
        metrics.graph_search_time_ms = (time.time() - graph_start) * 1000
        metrics.graph_results_count = graph_response.result.total_count

        # 2. 벡터 검색
        vector_start = time.time()
        vector_results = await self.vector_engine.search(
            query=request.query,
            top_k=request.top_k,
            index_name=request.index_name,
            min_score=request.min_score,
        )
        metrics.vector_search_time_ms = (time.time() - vector_start) * 1000
        metrics.vector_results_count = len(vector_results.results)

        # 3. 결과 융합
        fusion_start = time.time()

        graph_vector_results = self._convert_graph_to_vector_results(graph_response)

        fused_results = self._fuse_results(
            graph_results=graph_vector_results,
            vector_results=vector_results.results,
            graph_weight=request.graph_weight,
            vector_weight=request.vector_weight,
            fusion_method=FusionMethod.RECIPROCAL_RANK,
        )

        metrics.fusion_time_ms = (time.time() - fusion_start) * 1000

        return (
            fused_results,
            graph_response.result.table,
            vector_results.results,
            metrics,
        )

    def _convert_graph_to_vector_results(
        self, graph_response
    ) -> List[VectorSearchResult]:
        """
        그래프 쿼리 결과를 VectorSearchResult로 변환

        Args:
            graph_response: 그래프 쿼리 응답

        Returns:
            VectorSearchResult 리스트
        """
        vector_results = []

        for row in graph_response.result.table:
            # 점수 계산 (그래프 쿼리는 기본 점수 0.8)
            score = row.get("score", 0.8)

            # 텍스트 내용 추출
            text_fields = ["clause_text", "coverage_name", "disease_name", "text"]
            text_content = ""
            for field in text_fields:
                if field in row and row[field]:
                    text_content = str(row[field])
                    break

            result = VectorSearchResult(
                node_id=str(row.get("node_id", hash(str(row)))),
                score=float(score),
                properties=row,
                labels=["GraphResult"],
            )

            # 조항 정보가 있으면 설정
            if "clause_id" in row:
                result.clause_id = row["clause_id"]
            if "article_num" in row:
                result.article_num = row["article_num"]
            if "clause_text" in row:
                result.clause_text = row["clause_text"]

            vector_results.append(result)

        return vector_results

    def _fuse_results(
        self,
        graph_results: List[VectorSearchResult],
        vector_results: List[VectorSearchResult],
        graph_weight: float,
        vector_weight: float,
        fusion_method: FusionMethod,
    ) -> List[VectorSearchResult]:
        """
        결과 융합

        Args:
            graph_results: 그래프 검색 결과
            vector_results: 벡터 검색 결과
            graph_weight: 그래프 가중치
            vector_weight: 벡터 가중치
            fusion_method: 융합 방법

        Returns:
            융합된 결과
        """
        if fusion_method == FusionMethod.RECIPROCAL_RANK:
            return self._reciprocal_rank_fusion(
                graph_results, vector_results, graph_weight, vector_weight
            )
        elif fusion_method == FusionMethod.WEIGHTED_SUM:
            return self._weighted_sum_fusion(
                graph_results, vector_results, graph_weight, vector_weight
            )
        else:
            # 기본: Reciprocal Rank Fusion
            return self._reciprocal_rank_fusion(
                graph_results, vector_results, graph_weight, vector_weight
            )

    def _reciprocal_rank_fusion(
        self,
        graph_results: List[VectorSearchResult],
        vector_results: List[VectorSearchResult],
        graph_weight: float,
        vector_weight: float,
    ) -> List[VectorSearchResult]:
        """
        Reciprocal Rank Fusion (RRF)

        Args:
            graph_results: 그래프 결과
            vector_results: 벡터 결과
            graph_weight: 그래프 가중치
            vector_weight: 벡터 가중치

        Returns:
            융합된 결과
        """
        rrf = ReciprocalRankFusion(k=60)

        # 점수 계산
        scores: Dict[str, float] = {}
        result_map: Dict[str, VectorSearchResult] = {}

        # 그래프 결과 점수
        for rank, result in enumerate(graph_results):
            key = result.node_id or result.get_text_content()
            rrf_score = rrf.calculate_score(rank) * graph_weight
            scores[key] = scores.get(key, 0) + rrf_score
            result_map[key] = result

        # 벡터 결과 점수
        for rank, result in enumerate(vector_results):
            key = result.node_id or result.get_text_content()
            rrf_score = rrf.calculate_score(rank) * vector_weight
            scores[key] = scores.get(key, 0) + rrf_score
            if key not in result_map:
                result_map[key] = result

        # 점수로 정렬
        sorted_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)

        # 결과 생성
        fused_results = []
        for rank, key in enumerate(sorted_keys):
            result = result_map[key]
            # 융합 점수로 업데이트
            fused_result = result.model_copy()
            fused_result.score = scores[key]
            fused_result.rank = rank + 1
            fused_results.append(fused_result)

        logger.info(
            f"RRF fusion: {len(graph_results)} graph + {len(vector_results)} vector "
            f"→ {len(fused_results)} combined"
        )

        return fused_results

    def _weighted_sum_fusion(
        self,
        graph_results: List[VectorSearchResult],
        vector_results: List[VectorSearchResult],
        graph_weight: float,
        vector_weight: float,
    ) -> List[VectorSearchResult]:
        """
        가중 합 융합

        Args:
            graph_results: 그래프 결과
            vector_results: 벡터 결과
            graph_weight: 그래프 가중치
            vector_weight: 벡터 가중치

        Returns:
            융합된 결과
        """
        scores: Dict[str, float] = {}
        result_map: Dict[str, VectorSearchResult] = {}

        # 그래프 결과 점수
        for result in graph_results:
            key = result.node_id or result.get_text_content()
            scores[key] = result.score * graph_weight
            result_map[key] = result

        # 벡터 결과 점수
        for result in vector_results:
            key = result.node_id or result.get_text_content()
            vector_score = result.score * vector_weight
            scores[key] = scores.get(key, 0) + vector_score
            if key not in result_map:
                result_map[key] = result

        # 점수로 정렬
        sorted_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)

        # 결과 생성
        fused_results = []
        for rank, key in enumerate(sorted_keys):
            result = result_map[key]
            fused_result = result.model_copy()
            fused_result.score = scores[key]
            fused_result.rank = rank + 1
            fused_results.append(fused_result)

        return fused_results

    def _rerank_results(
        self, results: List[VectorSearchResult], query: str, config
    ) -> List[VectorSearchResult]:
        """
        결과 재랭킹

        Args:
            results: 검색 결과
            query: 질문
            config: 재랭킹 설정

        Returns:
            재랭킹된 결과
        """
        # 간단한 재랭킹: 엔티티 매칭 부스트
        query_lower = query.lower()

        reranked = []
        for result in results:
            text_content = result.get_text_content().lower()
            score = result.score

            # 정확 매칭 부스트
            if query_lower in text_content:
                score *= config.boost_exact_match

            # 길이 페널티
            if config.penalize_length and len(text_content) > 500:
                score *= 0.9

            reranked_result = result.model_copy()
            reranked_result.score = min(score, 1.0)
            reranked.append(reranked_result)

        # 점수로 재정렬
        reranked.sort(key=lambda r: r.score, reverse=True)

        logger.info(f"Reranked {len(reranked)} results")
        return reranked

    def _generate_explanation(
        self, strategy: SearchStrategy, result_count: int, metrics: SearchMetrics
    ) -> str:
        """검색 설명 생성"""
        explanations = []

        if strategy == SearchStrategy.VECTOR_ONLY:
            explanations.append(
                f"벡터 유사도 검색으로 {result_count}개의 관련 조항을 찾았습니다."
            )
        elif strategy == SearchStrategy.GRAPH_ONLY:
            explanations.append(
                f"그래프 쿼리로 {result_count}개의 보장 정보를 찾았습니다."
            )
        elif strategy == SearchStrategy.HYBRID:
            explanations.append(
                f"하이브리드 검색 (그래프 {metrics.graph_results_count}개 + "
                f"벡터 {metrics.vector_results_count}개)으로 "
                f"{result_count}개의 결과를 찾았습니다."
            )

        explanations.append(f"검색 시간: {metrics.total_time_ms:.2f}ms")

        return " ".join(explanations)
