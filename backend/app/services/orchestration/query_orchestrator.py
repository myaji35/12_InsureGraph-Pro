"""
Query Orchestrator

GraphRAG 쿼리 파이프라인 전체를 조율하는 오케스트레이터.
Story 2.1, 2.2, 2.3, 2.4를 통합합니다.
"""
import time
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger
import asyncio

from app.models.orchestration import (
    OrchestrationRequest,
    OrchestrationResponse,
    OrchestrationContext,
    OrchestrationMetrics,
    OrchestrationStrategy,
    OrchestrationConfig,
    OrchestrationError,
    ExecutionStage,
    StageMetrics,
    CacheEntry,
)
from app.models.response import GeneratedResponse, AnswerFormat, ResponseGenerationRequest
from app.services.query.query_analyzer import QueryAnalyzer
from app.services.vector_search.hybrid_search_engine import HybridSearchEngine
from app.services.response.response_generator import ResponseGenerator


class QueryOrchestrator:
    """
    쿼리 오케스트레이터

    전체 GraphRAG 파이프라인을 조율합니다:
    1. Query Analysis (Story 2.1)
    2. Hybrid Search (Story 2.3 + 2.2)
    3. Response Generation (Story 2.4)
    """

    def __init__(
        self,
        query_analyzer: Optional[QueryAnalyzer] = None,
        hybrid_search: Optional[HybridSearchEngine] = None,
        response_generator: Optional[ResponseGenerator] = None,
        config: Optional[OrchestrationConfig] = None,
    ):
        """
        Args:
            query_analyzer: 질의 분석기
            hybrid_search: 하이브리드 검색 엔진
            response_generator: 응답 생성기
            config: 오케스트레이션 설정
        """
        self.query_analyzer = query_analyzer or QueryAnalyzer()
        self.hybrid_search = hybrid_search or HybridSearchEngine()
        self.response_generator = response_generator or ResponseGenerator()
        self.config = config or OrchestrationConfig()

        # 캐시
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_stats = {"hits": 0, "misses": 0, "evictions": 0}

    async def process(
        self, request: OrchestrationRequest
    ) -> OrchestrationResponse:
        """
        쿼리 처리 (메인 메서드)

        Args:
            request: 오케스트레이션 요청

        Returns:
            오케스트레이션 응답
        """
        start_time = time.time()
        request_id = self._generate_request_id(request)

        logger.info(
            f"[{request_id}] Starting orchestration: '{request.query}' "
            f"(strategy: {request.strategy})"
        )

        # 컨텍스트 초기화
        context = OrchestrationContext(
            request_id=request_id,
            strategy=request.strategy,
        )

        # 메트릭 초기화
        metrics = OrchestrationMetrics(total_duration_ms=0.0, stages=[])

        try:
            # 캐시 확인
            if request.use_cache and self.config.cache_enabled:
                cached_response = self._get_from_cache(request)
                if cached_response:
                    logger.info(f"[{request_id}] Cache hit!")
                    cached_response.cache_hit = True
                    cached_response.metrics.cache_hit = True
                    self._cache_stats["hits"] += 1
                    return cached_response
                self._cache_stats["misses"] += 1

            # 전략별 실행
            if request.strategy == OrchestrationStrategy.FAST:
                response = await self._execute_fast_strategy(
                    request, context, metrics
                )
            elif request.strategy == OrchestrationStrategy.COMPREHENSIVE:
                response = await self._execute_comprehensive_strategy(
                    request, context, metrics
                )
            elif request.strategy == OrchestrationStrategy.FALLBACK:
                response = await self._execute_fallback_strategy(
                    request, context, metrics
                )
            else:  # STANDARD
                response = await self._execute_standard_strategy(
                    request, context, metrics
                )

            # 전체 실행 시간
            total_time = (time.time() - start_time) * 1000
            response.metrics.total_duration_ms = total_time

            # 캐시 저장
            if request.use_cache and self.config.cache_enabled and response.success:
                self._save_to_cache(request, response)

            logger.info(
                f"[{request_id}] Orchestration completed in {total_time:.2f}ms "
                f"(success: {response.success})"
            )

            return response

        except Exception as e:
            logger.error(f"[{request_id}] Orchestration failed: {e}")
            context.add_error(str(e))

            # 폴백 응답 생성
            if self.config.enable_fallback:
                return await self._create_fallback_response(
                    request, context, metrics, str(e)
                )
            else:
                raise

    async def _execute_standard_strategy(
        self,
        request: OrchestrationRequest,
        context: OrchestrationContext,
        metrics: OrchestrationMetrics,
    ) -> OrchestrationResponse:
        """
        표준 전략 실행

        Analysis → Search → Generation
        """
        # Stage 1: Query Analysis
        stage_metrics = StageMetrics(
            stage=ExecutionStage.QUERY_ANALYSIS,
            start_time=datetime.now(),
        )
        context.current_stage = ExecutionStage.QUERY_ANALYSIS

        try:
            query_analysis = await self._run_with_timeout(
                self.query_analyzer.analyze(request.query),
                timeout=self.config.query_analysis_timeout,
            )
            context.query_analysis = query_analysis
            stage_metrics.mark_completed(success=True)
            stage_metrics.metadata = {
                "intent": query_analysis.intent,
                "confidence": query_analysis.confidence,
            }
            logger.debug(
                f"[{context.request_id}] Query analysis: intent={query_analysis.intent}, "
                f"confidence={query_analysis.confidence:.2f}"
            )

        except Exception as e:
            logger.error(f"[{context.request_id}] Query analysis failed: {e}")
            stage_metrics.mark_completed(success=False, error=str(e))
            context.add_error(f"Query analysis error: {e}")

            # 폴백: 기본 분석 결과 사용
            query_analysis = await self._create_fallback_analysis(request.query)
            context.query_analysis = query_analysis

        metrics.add_stage(stage_metrics)

        # Stage 2: Search
        stage_metrics = StageMetrics(
            stage=ExecutionStage.SEARCH,
            start_time=datetime.now(),
        )
        context.current_stage = ExecutionStage.SEARCH

        try:
            search_response = await self._run_with_timeout(
                self.hybrid_search.search(
                    query=request.query,
                    analysis=query_analysis,
                    top_k=request.max_search_results,
                ),
                timeout=self.config.search_timeout,
            )
            context.search_response = search_response
            stage_metrics.mark_completed(success=True)
            stage_metrics.metadata = {
                "result_count": search_response.total_count,
                "strategy": search_response.strategy,
            }
            logger.debug(
                f"[{context.request_id}] Search: found {search_response.total_count} results "
                f"(strategy: {search_response.strategy})"
            )

        except Exception as e:
            logger.error(f"[{context.request_id}] Search failed: {e}")
            stage_metrics.mark_completed(success=False, error=str(e))
            context.add_error(f"Search error: {e}")

            # 폴백: 빈 검색 결과
            search_response = await self._create_fallback_search_response(request.query)
            context.search_response = search_response

        metrics.add_stage(stage_metrics)

        # Stage 3: Response Generation
        stage_metrics = StageMetrics(
            stage=ExecutionStage.RESPONSE_GENERATION,
            start_time=datetime.now(),
        )
        context.current_stage = ExecutionStage.RESPONSE_GENERATION

        try:
            # 검색 결과를 딕셔너리 형태로 변환
            search_results = self._convert_search_results(search_response)

            generation_request = ResponseGenerationRequest(
                query=request.query,
                intent=query_analysis.intent,
                search_results=search_results,
                include_citations=request.include_citations,
                include_follow_ups=request.include_follow_ups,
            )

            generated_response = await self._run_with_timeout(
                self.response_generator.generate(generation_request),
                timeout=self.config.response_generation_timeout,
            )

            stage_metrics.mark_completed(success=True)
            stage_metrics.metadata = {
                "format": generated_response.format,
                "confidence": generated_response.confidence_score,
                "citation_count": len(generated_response.citations),
            }
            logger.debug(
                f"[{context.request_id}] Response generated: "
                f"format={generated_response.format}, "
                f"confidence={generated_response.confidence_score:.2f}"
            )

        except Exception as e:
            logger.error(f"[{context.request_id}] Response generation failed: {e}")
            stage_metrics.mark_completed(success=False, error=str(e))
            context.add_error(f"Response generation error: {e}")

            # 폴백: 기본 응답
            generated_response = await self._create_fallback_generated_response(
                request.query
            )

        metrics.add_stage(stage_metrics)

        # 최종 응답 생성
        return OrchestrationResponse(
            request_id=context.request_id,
            query=request.query,
            response=generated_response,
            query_analysis=context.query_analysis,
            search_response=context.search_response,
            strategy=request.strategy,
            success=not context.has_errors(),
            errors=context.errors,
            metrics=metrics,
            cache_hit=False,
        )

    async def _execute_fast_strategy(
        self,
        request: OrchestrationRequest,
        context: OrchestrationContext,
        metrics: OrchestrationMetrics,
    ) -> OrchestrationResponse:
        """
        빠른 전략 실행

        캐시 우선, 간단한 분석, 제한된 검색
        """
        # 표준 전략과 동일하지만 타임아웃을 더 짧게 설정
        original_timeouts = (
            self.config.query_analysis_timeout,
            self.config.search_timeout,
            self.config.response_generation_timeout,
        )

        # 타임아웃 단축
        self.config.query_analysis_timeout = 2
        self.config.search_timeout = 5
        self.config.response_generation_timeout = 3

        try:
            # 검색 결과 수도 제한
            request.max_search_results = min(request.max_search_results, 5)
            return await self._execute_standard_strategy(request, context, metrics)
        finally:
            # 타임아웃 복원
            (
                self.config.query_analysis_timeout,
                self.config.search_timeout,
                self.config.response_generation_timeout,
            ) = original_timeouts

    async def _execute_comprehensive_strategy(
        self,
        request: OrchestrationRequest,
        context: OrchestrationContext,
        metrics: OrchestrationMetrics,
    ) -> OrchestrationResponse:
        """
        포괄적 전략 실행

        모든 검색 전략 시도, 더 많은 결과, 더 긴 타임아웃
        """
        # 검색 결과 수 증가
        request.max_search_results = max(request.max_search_results, 20)

        # 타임아웃 증가
        self.config.query_analysis_timeout = 10
        self.config.search_timeout = 30
        self.config.response_generation_timeout = 15

        return await self._execute_standard_strategy(request, context, metrics)

    async def _execute_fallback_strategy(
        self,
        request: OrchestrationRequest,
        context: OrchestrationContext,
        metrics: OrchestrationMetrics,
    ) -> OrchestrationResponse:
        """폴백 전략 실행"""
        return await self._create_fallback_response(
            request, context, metrics, "Fallback strategy requested"
        )

    async def _run_with_timeout(self, coroutine, timeout: int):
        """타임아웃과 함께 코루틴 실행"""
        try:
            return await asyncio.wait_for(coroutine, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Operation timed out after {timeout}s")

    def _generate_request_id(self, request: OrchestrationRequest) -> str:
        """요청 ID 생성"""
        timestamp = datetime.now().isoformat()
        data = f"{request.query}:{timestamp}:{request.user_id}"
        return hashlib.md5(data.encode()).hexdigest()[:12]

    def _generate_cache_key(self, request: OrchestrationRequest) -> str:
        """캐시 키 생성"""
        # query + strategy로 캐시 키 생성
        data = f"{request.query}:{request.strategy}:{request.max_search_results}"
        return hashlib.md5(data.encode()).hexdigest()

    def _get_from_cache(
        self, request: OrchestrationRequest
    ) -> Optional[OrchestrationResponse]:
        """캐시에서 조회"""
        cache_key = self._generate_cache_key(request)

        if cache_key in self._cache:
            entry = self._cache[cache_key]

            # 만료 확인
            if entry.is_expired(self.config.cache_ttl_seconds):
                del self._cache[cache_key]
                self._cache_stats["evictions"] += 1
                return None

            # 히트 기록
            entry.access()
            logger.debug(f"Cache hit for query: '{request.query}' (hits: {entry.hits})")
            return entry.response

        return None

    def _save_to_cache(
        self, request: OrchestrationRequest, response: OrchestrationResponse
    ):
        """캐시에 저장"""
        cache_key = self._generate_cache_key(request)

        # 캐시 크기 제한
        if len(self._cache) >= self.config.cache_max_size:
            # LRU: 가장 오래된 항목 제거
            oldest_key = min(
                self._cache.keys(),
                key=lambda k: self._cache[k].last_accessed,
            )
            del self._cache[oldest_key]
            self._cache_stats["evictions"] += 1

        # 캐시 저장
        self._cache[cache_key] = CacheEntry(
            key=cache_key,
            query=request.query,
            response=response,
        )

        logger.debug(
            f"Cached response for query: '{request.query}' "
            f"(cache size: {len(self._cache)})"
        )

    def _convert_search_results(self, search_response) -> list:
        """검색 결과를 딕셔너리 리스트로 변환"""
        results = []
        for result in search_response.results:
            results.append({
                "text": result.text,
                "score": result.score,
                "metadata": result.metadata,
                **result.metadata,  # metadata 내용을 풀어서 추가
            })
        return results

    async def _create_fallback_analysis(self, query: str):
        """폴백 질의 분석"""
        from app.models.query import QueryAnalysisResult

        return QueryAnalysisResult(
            query=query,
            intent="general_info",
            confidence=0.3,
            entities=[],
            query_type="general",
            keywords=[],
        )

    async def _create_fallback_search_response(self, query: str):
        """폴백 검색 응답"""
        from app.models.vector_search import SearchResponse, SearchStrategy

        return SearchResponse(
            original_query=query,
            strategy=SearchStrategy.VECTOR_ONLY,
            results=[],
            total_count=0,
            search_time_ms=0.0,
            reranked=False,
        )

    async def _create_fallback_generated_response(
        self, query: str
    ) -> GeneratedResponse:
        """폴백 생성 응답"""
        return GeneratedResponse(
            answer=self.config.fallback_response,
            format=AnswerFormat.TEXT,
            confidence_score=0.0,
            generation_time_ms=0.0,
        )

    async def _create_fallback_response(
        self,
        request: OrchestrationRequest,
        context: OrchestrationContext,
        metrics: OrchestrationMetrics,
        error_message: str,
    ) -> OrchestrationResponse:
        """폴백 응답 생성"""
        fallback_response = GeneratedResponse(
            answer=self.config.fallback_response,
            format=AnswerFormat.TEXT,
            confidence_score=0.0,
            generation_time_ms=0.0,
        )

        return OrchestrationResponse(
            request_id=context.request_id,
            query=request.query,
            response=fallback_response,
            strategy=OrchestrationStrategy.FALLBACK,
            success=False,
            errors=[error_message],
            metrics=metrics,
            cache_hit=False,
        )

    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (
            self._cache_stats["hits"] / total_requests if total_requests > 0 else 0.0
        )

        return {
            "cache_size": len(self._cache),
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "evictions": self._cache_stats["evictions"],
            "hit_rate": hit_rate,
            "total_requests": total_requests,
        }

    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        logger.info("Cache cleared")

    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        return {
            "status": "healthy",
            "components": {
                "query_analyzer": "ok",
                "hybrid_search": "ok",
                "response_generator": "ok",
            },
            "cache": self.get_cache_stats(),
            "config": {
                "cache_enabled": self.config.cache_enabled,
                "default_timeout": self.config.default_timeout_seconds,
                "max_retries": self.config.max_retries,
            },
        }
