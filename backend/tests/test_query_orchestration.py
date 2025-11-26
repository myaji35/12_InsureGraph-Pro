"""
Tests for Query Orchestration

Story 2.5: Query Orchestration 관련 테스트
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.models.orchestration import (
    OrchestrationRequest,
    OrchestrationResponse,
    OrchestrationStrategy,
    OrchestrationConfig,
    ExecutionStage,
    StageMetrics,
    OrchestrationMetrics,
    CacheEntry,
)
from app.models.query import QueryAnalysisResult
from app.models.vector_search import SearchResponse, SearchStrategy, VectorSearchResult
from app.models.response import GeneratedResponse, AnswerFormat
from app.services.orchestration.query_orchestrator import QueryOrchestrator


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_query_analyzer():
    """Mock QueryAnalyzer"""
    analyzer = Mock()
    analyzer.analyze = AsyncMock(
        return_value=QueryAnalysisResult(
            query="암 보장 금액은?",
            intent="coverage_amount",
            confidence=0.95,
            entities=["암"],
            query_type="coverage_query",
            keywords=["암", "보장", "금액"],
        )
    )
    return analyzer


@pytest.fixture
def mock_hybrid_search():
    """Mock HybridSearchEngine"""
    search = Mock()
    search.search = AsyncMock(
        return_value=SearchResponse(
            original_query="암 보장 금액은?",
            strategy=SearchStrategy.HYBRID,
            results=[
                VectorSearchResult(
                    text="암 진단 시 5천만원 지급",
                    score=0.95,
                    metadata={"disease_name": "암", "amount": 50000000},
                )
            ],
            total_count=1,
            search_time_ms=10.5,
            reranked=False,
        )
    )
    return search


@pytest.fixture
def mock_response_generator():
    """Mock ResponseGenerator"""
    generator = Mock()
    generator.generate = AsyncMock(
        return_value=GeneratedResponse(
            answer="암의 경우 진단비 5,000만원이 보장됩니다.",
            format=AnswerFormat.TEXT,
            confidence_score=0.9,
            generation_time_ms=5.2,
        )
    )
    return generator


@pytest.fixture
def orchestrator(mock_query_analyzer, mock_hybrid_search, mock_response_generator):
    """QueryOrchestrator 인스턴스"""
    return QueryOrchestrator(
        query_analyzer=mock_query_analyzer,
        hybrid_search=mock_hybrid_search,
        response_generator=mock_response_generator,
    )


@pytest.fixture
def sample_request():
    """샘플 오케스트레이션 요청"""
    return OrchestrationRequest(
        query="암 보장 금액은?",
        user_id="user123",
        session_id="session456",
        strategy=OrchestrationStrategy.STANDARD,
        use_cache=True,
        include_citations=True,
        include_follow_ups=True,
        max_search_results=10,
    )


# ============================================================================
# Test Orchestration Models
# ============================================================================


class TestOrchestrationModels:
    """Orchestration 모델 테스트"""

    def test_orchestration_request_creation(self):
        """OrchestrationRequest 생성"""
        request = OrchestrationRequest(
            query="테스트 질문",
            strategy=OrchestrationStrategy.STANDARD,
        )

        assert request.query == "테스트 질문"
        assert request.strategy == OrchestrationStrategy.STANDARD
        assert request.use_cache is True
        assert request.max_search_results == 10

    def test_stage_metrics(self):
        """StageMetrics 테스트"""
        metrics = StageMetrics(
            stage=ExecutionStage.QUERY_ANALYSIS,
            start_time=datetime.now(),
        )

        metrics.mark_completed(success=True)

        assert metrics.success is True
        assert metrics.end_time is not None
        assert metrics.duration_ms is not None
        assert metrics.duration_ms > 0

    def test_orchestration_metrics(self):
        """OrchestrationMetrics 테스트"""
        metrics = OrchestrationMetrics(total_duration_ms=0.0)

        stage1 = StageMetrics(
            stage=ExecutionStage.QUERY_ANALYSIS,
            start_time=datetime.now(),
        )
        stage1.mark_completed()
        stage1.duration_ms = 5.0

        metrics.add_stage(stage1)

        assert len(metrics.stages) == 1
        assert metrics.query_analysis_ms == 5.0

    def test_cache_entry(self):
        """CacheEntry 테스트"""
        response = Mock(spec=OrchestrationResponse)
        entry = CacheEntry(
            key="test_key",
            query="테스트 질문",
            response=response,
        )

        assert entry.hits == 0

        entry.access()
        assert entry.hits == 1

        entry.access()
        assert entry.hits == 2

    def test_cache_entry_expiration(self):
        """CacheEntry 만료 테스트"""
        response = Mock(spec=OrchestrationResponse)
        entry = CacheEntry(
            key="test_key",
            query="테스트 질문",
            response=response,
        )

        # 1시간 TTL, 아직 만료 안됨
        assert entry.is_expired(ttl_seconds=3600) is False

        # 0초 TTL, 즉시 만료
        assert entry.is_expired(ttl_seconds=0) is True

    def test_orchestration_response_summary(self):
        """OrchestrationResponse 요약 테스트"""
        response = OrchestrationResponse(
            request_id="req123",
            query="테스트 질문",
            response=GeneratedResponse(
                answer="테스트 답변입니다. " * 10,  # 긴 답변
                format=AnswerFormat.TEXT,
                confidence_score=0.9,
            ),
            strategy=OrchestrationStrategy.STANDARD,
            success=True,
            errors=[],
            metrics=OrchestrationMetrics(total_duration_ms=15.5),
        )

        summary = response.get_summary()

        assert "query" in summary
        assert "answer" in summary
        assert len(summary["answer"]) <= 103  # 100 + "..."
        assert summary["confidence"] == 0.9
        assert summary["total_time_ms"] == 15.5


# ============================================================================
# Test Query Orchestrator
# ============================================================================


class TestQueryOrchestrator:
    """QueryOrchestrator 테스트"""

    @pytest.mark.asyncio
    async def test_orchestrator_standard_strategy(
        self, orchestrator, sample_request
    ):
        """표준 전략 실행"""
        response = await orchestrator.process(sample_request)

        assert response.success is True
        assert response.query == "암 보장 금액은?"
        assert response.strategy == OrchestrationStrategy.STANDARD
        assert response.response is not None
        assert response.query_analysis is not None
        assert response.search_response is not None
        assert len(response.errors) == 0
        assert response.metrics.total_duration_ms > 0

    @pytest.mark.asyncio
    async def test_orchestrator_all_stages_executed(
        self, orchestrator, sample_request
    ):
        """모든 단계 실행 확인"""
        response = await orchestrator.process(sample_request)

        # 3개 단계 모두 실행
        assert len(response.metrics.stages) == 3

        # 각 단계 확인
        stages = {s.stage: s for s in response.metrics.stages}
        assert ExecutionStage.QUERY_ANALYSIS in stages
        assert ExecutionStage.SEARCH in stages
        assert ExecutionStage.RESPONSE_GENERATION in stages

        # 모든 단계 성공
        assert all(s.success for s in response.metrics.stages)

    @pytest.mark.asyncio
    async def test_orchestrator_fast_strategy(
        self, orchestrator
    ):
        """빠른 전략 실행"""
        request = OrchestrationRequest(
            query="테스트 질문",
            strategy=OrchestrationStrategy.FAST,
        )

        response = await orchestrator.process(request)

        assert response.success is True
        assert response.strategy == OrchestrationStrategy.FAST

    @pytest.mark.asyncio
    async def test_orchestrator_comprehensive_strategy(
        self, orchestrator
    ):
        """포괄적 전략 실행"""
        request = OrchestrationRequest(
            query="테스트 질문",
            strategy=OrchestrationStrategy.COMPREHENSIVE,
            max_search_results=5,
        )

        response = await orchestrator.process(request)

        assert response.success is True
        assert response.strategy == OrchestrationStrategy.COMPREHENSIVE

    @pytest.mark.asyncio
    async def test_orchestrator_fallback_strategy(
        self, orchestrator
    ):
        """폴백 전략 실행"""
        request = OrchestrationRequest(
            query="테스트 질문",
            strategy=OrchestrationStrategy.FALLBACK,
        )

        response = await orchestrator.process(request)

        assert response.success is False
        assert response.strategy == OrchestrationStrategy.FALLBACK
        assert len(response.errors) > 0

    @pytest.mark.asyncio
    async def test_orchestrator_query_analysis_failure(
        self, mock_hybrid_search, mock_response_generator
    ):
        """질의 분석 실패 시 폴백"""
        # QueryAnalyzer가 에러 발생
        mock_analyzer = Mock()
        mock_analyzer.analyze = AsyncMock(side_effect=Exception("Analysis error"))

        orchestrator = QueryOrchestrator(
            query_analyzer=mock_analyzer,
            hybrid_search=mock_hybrid_search,
            response_generator=mock_response_generator,
        )

        request = OrchestrationRequest(query="테스트")
        response = await orchestrator.process(request)

        # 폴백으로 계속 진행
        assert response.success is True
        assert response.query_analysis is not None
        assert response.query_analysis.intent == "general_info"

    @pytest.mark.asyncio
    async def test_orchestrator_search_failure(
        self, mock_query_analyzer, mock_response_generator
    ):
        """검색 실패 시 폴백"""
        # HybridSearch가 에러 발생
        mock_search = Mock()
        mock_search.search = AsyncMock(side_effect=Exception("Search error"))

        orchestrator = QueryOrchestrator(
            query_analyzer=mock_query_analyzer,
            hybrid_search=mock_search,
            response_generator=mock_response_generator,
        )

        request = OrchestrationRequest(query="테스트")
        response = await orchestrator.process(request)

        # 폴백으로 계속 진행
        assert response.success is True
        assert response.search_response is not None
        assert response.search_response.total_count == 0

    @pytest.mark.asyncio
    async def test_orchestrator_response_generation_failure(
        self, mock_query_analyzer, mock_hybrid_search
    ):
        """응답 생성 실패 시 폴백"""
        # ResponseGenerator가 에러 발생
        mock_generator = Mock()
        mock_generator.generate = AsyncMock(
            side_effect=Exception("Generation error")
        )

        orchestrator = QueryOrchestrator(
            query_analyzer=mock_query_analyzer,
            hybrid_search=mock_hybrid_search,
            response_generator=mock_generator,
        )

        request = OrchestrationRequest(query="테스트")
        response = await orchestrator.process(request)

        # 폴백으로 계속 진행
        assert response.success is True
        assert response.response is not None
        assert response.response.confidence_score == 0.0


# ============================================================================
# Test Caching
# ============================================================================


class TestOrchestrationCaching:
    """캐싱 테스트"""

    @pytest.mark.asyncio
    async def test_cache_miss_then_hit(
        self, orchestrator, sample_request
    ):
        """캐시 미스 후 히트"""
        # 첫 번째 요청 - 캐시 미스
        response1 = await orchestrator.process(sample_request)
        assert response1.cache_hit is False

        # 두 번째 동일 요청 - 캐시 히트
        response2 = await orchestrator.process(sample_request)
        assert response2.cache_hit is True

        # 동일한 응답
        assert response1.query == response2.query
        assert response1.response.answer == response2.response.answer

    @pytest.mark.asyncio
    async def test_cache_disabled(
        self, mock_query_analyzer, mock_hybrid_search, mock_response_generator
    ):
        """캐시 비활성화"""
        config = OrchestrationConfig(cache_enabled=False)
        orchestrator = QueryOrchestrator(
            query_analyzer=mock_query_analyzer,
            hybrid_search=mock_hybrid_search,
            response_generator=mock_response_generator,
            config=config,
        )

        request = OrchestrationRequest(query="테스트")

        # 두 번 요청해도 캐시 안됨
        response1 = await orchestrator.process(request)
        response2 = await orchestrator.process(request)

        assert response1.cache_hit is False
        assert response2.cache_hit is False

    @pytest.mark.asyncio
    async def test_cache_use_false_in_request(
        self, orchestrator
    ):
        """요청에서 캐시 사용 안함"""
        request = OrchestrationRequest(
            query="테스트",
            use_cache=False,
        )

        # 첫 요청
        response1 = await orchestrator.process(request)
        assert response1.cache_hit is False

        # 두 번째 요청 (캐시 사용 안함)
        response2 = await orchestrator.process(request)
        assert response2.cache_hit is False

    @pytest.mark.asyncio
    async def test_cache_different_strategies(
        self, orchestrator
    ):
        """다른 전략은 별도 캐시"""
        # STANDARD 전략
        request1 = OrchestrationRequest(
            query="테스트",
            strategy=OrchestrationStrategy.STANDARD,
        )
        response1 = await orchestrator.process(request1)

        # FAST 전략 (동일 질문)
        request2 = OrchestrationRequest(
            query="테스트",
            strategy=OrchestrationStrategy.FAST,
        )
        response2 = await orchestrator.process(request2)

        # 둘 다 캐시 미스 (다른 전략이므로)
        assert response1.cache_hit is False
        assert response2.cache_hit is False

    def test_cache_stats(self, orchestrator):
        """캐시 통계"""
        stats = orchestrator.get_cache_stats()

        assert "cache_size" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats

    def test_clear_cache(self, orchestrator):
        """캐시 초기화"""
        # 캐시에 뭔가 저장되어 있다고 가정
        orchestrator._cache["key1"] = Mock()
        orchestrator._cache["key2"] = Mock()

        assert len(orchestrator._cache) == 2

        orchestrator.clear_cache()

        assert len(orchestrator._cache) == 0


# ============================================================================
# Test Performance and Metrics
# ============================================================================


class TestOrchestrationMetrics:
    """메트릭 테스트"""

    @pytest.mark.asyncio
    async def test_metrics_collection(
        self, orchestrator, sample_request
    ):
        """메트릭 수집"""
        response = await orchestrator.process(sample_request)

        # 전체 시간 기록
        assert response.metrics.total_duration_ms > 0

        # 단계별 시간 기록
        assert response.metrics.query_analysis_ms is not None
        assert response.metrics.search_ms is not None
        assert response.metrics.response_generation_ms is not None

        # 단계별 메트릭
        assert len(response.metrics.stages) == 3
        for stage in response.metrics.stages:
            assert stage.duration_ms is not None
            assert stage.duration_ms > 0

    @pytest.mark.asyncio
    async def test_stage_metadata(
        self, orchestrator, sample_request
    ):
        """단계별 메타데이터"""
        response = await orchestrator.process(sample_request)

        # Query Analysis 메타데이터
        analysis_stage = response.metrics.get_stage_metrics(
            ExecutionStage.QUERY_ANALYSIS
        )
        assert analysis_stage is not None
        assert "intent" in analysis_stage.metadata
        assert "confidence" in analysis_stage.metadata

        # Search 메타데이터
        search_stage = response.metrics.get_stage_metrics(ExecutionStage.SEARCH)
        assert search_stage is not None
        assert "result_count" in search_stage.metadata
        assert "strategy" in search_stage.metadata

        # Response Generation 메타데이터
        gen_stage = response.metrics.get_stage_metrics(
            ExecutionStage.RESPONSE_GENERATION
        )
        assert gen_stage is not None
        assert "format" in gen_stage.metadata
        assert "confidence" in gen_stage.metadata


# ============================================================================
# Test Health Check
# ============================================================================


class TestHealthCheck:
    """헬스 체크 테스트"""

    @pytest.mark.asyncio
    async def test_health_check(self, orchestrator):
        """헬스 체크"""
        health = await orchestrator.health_check()

        assert health["status"] == "healthy"
        assert "components" in health
        assert "cache" in health
        assert "config" in health

        # 컴포넌트 상태
        assert health["components"]["query_analyzer"] == "ok"
        assert health["components"]["hybrid_search"] == "ok"
        assert health["components"]["response_generator"] == "ok"


# ============================================================================
# Integration Tests
# ============================================================================


class TestOrchestrationIntegration:
    """통합 테스트"""

    @pytest.mark.asyncio
    async def test_end_to_end_standard_flow(
        self, orchestrator, sample_request
    ):
        """E2E 표준 플로우"""
        response = await orchestrator.process(sample_request)

        # 성공 확인
        assert response.success is True
        assert len(response.errors) == 0

        # 모든 중간 결과 존재
        assert response.query_analysis is not None
        assert response.search_response is not None
        assert response.response is not None

        # 질의 분석 결과
        assert response.query_analysis.intent == "coverage_amount"
        assert response.query_analysis.confidence > 0.9

        # 검색 결과
        assert response.search_response.total_count > 0

        # 최종 응답
        assert len(response.response.answer) > 0
        assert response.response.confidence_score > 0.5

        # 메트릭
        assert response.metrics.total_duration_ms > 0
        assert len(response.metrics.stages) == 3

    @pytest.mark.asyncio
    async def test_end_to_end_with_caching(
        self, orchestrator
    ):
        """E2E 캐싱 포함"""
        request = OrchestrationRequest(
            query="암 보장 금액은?",
            strategy=OrchestrationStrategy.STANDARD,
            use_cache=True,
        )

        # 첫 번째 요청 - 전체 파이프라인 실행
        response1 = await orchestrator.process(request)
        time1 = response1.metrics.total_duration_ms

        assert response1.cache_hit is False
        assert response1.success is True

        # 두 번째 요청 - 캐시에서 조회
        response2 = await orchestrator.process(request)

        assert response2.cache_hit is True
        assert response2.success is True
        assert response2.response.answer == response1.response.answer

    @pytest.mark.asyncio
    async def test_end_to_end_error_recovery(
        self, mock_hybrid_search, mock_response_generator
    ):
        """E2E 에러 복구"""
        # QueryAnalyzer가 실패
        mock_analyzer = Mock()
        mock_analyzer.analyze = AsyncMock(
            side_effect=Exception("Analysis error")
        )

        config = OrchestrationConfig(enable_fallback=True)
        orchestrator = QueryOrchestrator(
            query_analyzer=mock_analyzer,
            hybrid_search=mock_hybrid_search,
            response_generator=mock_response_generator,
            config=config,
        )

        request = OrchestrationRequest(query="테스트")
        response = await orchestrator.process(request)

        # 폴백으로 성공
        assert response.success is True
        assert response.response is not None
        assert len(response.errors) > 0  # 에러는 기록됨

    @pytest.mark.asyncio
    async def test_end_to_end_multiple_queries(
        self, orchestrator
    ):
        """E2E 여러 질의 처리"""
        queries = [
            "암 보장 금액은?",
            "당뇨병은 보장되나요?",
            "대기기간은 얼마나 되나요?",
        ]

        responses = []
        for query in queries:
            request = OrchestrationRequest(query=query)
            response = await orchestrator.process(request)
            responses.append(response)

        # 모두 성공
        assert all(r.success for r in responses)

        # 각각 다른 응답
        answers = [r.response.answer for r in responses]
        assert len(set(answers)) == 3  # 3개 모두 다름

    @pytest.mark.asyncio
    async def test_performance_benchmark(
        self, orchestrator
    ):
        """성능 벤치마크"""
        request = OrchestrationRequest(
            query="테스트 질문",
            strategy=OrchestrationStrategy.FAST,
        )

        # 10번 실행
        times = []
        for _ in range(10):
            response = await orchestrator.process(request)
            times.append(response.metrics.total_duration_ms)

        # 평균 시간
        avg_time = sum(times) / len(times)

        # 첫 번째는 캐시 미스, 나머지는 캐시 히트
        assert times[0] > avg_time  # 첫 번째가 더 오래 걸림
        assert avg_time < 50  # 평균 50ms 이내 (캐싱 덕분)
