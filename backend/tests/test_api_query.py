"""
Tests for Query API Endpoints

Story 3.1: Query API Endpoints 테스트
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from app.main import app
from app.models.orchestration import OrchestrationResponse, OrchestrationMetrics, OrchestrationStrategy
from app.models.response import GeneratedResponse, AnswerFormat
from app.models.query import QueryAnalysisResult


# TestClient
client = TestClient(app)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_orchestration_response():
    """Mock OrchestrationResponse"""
    return OrchestrationResponse(
        request_id="test_query_123",
        query="급성심근경색증 보장 금액은?",
        response=GeneratedResponse(
            answer="급성심근경색증의 경우 진단비 5,000만원이 보장됩니다.",
            format=AnswerFormat.TEXT,
            confidence_score=0.92,
            generation_time_ms=19.5,
            citations=[],
            follow_up_suggestions=["대기기간은 얼마나 되나요?"],
        ),
        query_analysis=QueryAnalysisResult(
            original_query="급성심근경색증 보장 금액은?",
            intent="coverage_amount",
            intent_confidence=0.95,
            query_type="coverage_query",
            entities=[],
            keywords=["급성심근경색증", "보장", "금액"],
        ),
        search_response=None,
        strategy=OrchestrationStrategy.STANDARD,
        success=True,
        errors=[],
        metrics=OrchestrationMetrics(
            total_duration_ms=287.5,
            query_analysis_ms=123.0,
            search_ms=145.0,
            response_generation_ms=19.5,
            cache_hit=False,
            search_result_count=8,
            stages=[],
        ),
        cache_hit=False,
    )


# ============================================================================
# Test POST /api/v1/query
# ============================================================================


class TestQueryEndpoint:
    """POST /api/v1/query 테스트"""

    @patch('app.api.v1.endpoints.query.get_orchestrator')
    def test_query_success(self, mock_get_orch, mock_orchestration_response):
        """정상 질의 실행"""
        # Mock setup
        mock_orchestrator = Mock()
        mock_orchestrator.process = AsyncMock(return_value=mock_orchestration_response)
        mock_get_orch.return_value = mock_orchestrator

        # Request
        response = client.post(
            "/api/v1/query",
            json={
                "query": "급성심근경색증 보장 금액은?",
                "strategy": "standard",
                "max_results": 10,
            }
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["query_id"] == "test_query_123"
        assert data["query"] == "급성심근경색증 보장 금액은?"
        assert "급성심근경색증" in data["answer"]
        assert data["confidence"] >= 0.9
        assert data["success"] is True

    def test_query_missing_query(self):
        """필수 필드 누락"""
        response = client.post(
            "/api/v1/query",
            json={}
        )

        assert response.status_code == 422  # Validation error

    def test_query_empty_query(self):
        """빈 질문"""
        response = client.post(
            "/api/v1/query",
            json={"query": ""}
        )

        assert response.status_code == 422  # Validation error

    def test_query_too_long(self):
        """너무 긴 질문"""
        response = client.post(
            "/api/v1/query",
            json={"query": "A" * 1001}  # max_length=1000
        )

        assert response.status_code == 422  # Validation error

    @patch('app.api.v1.endpoints.query.get_orchestrator')
    def test_query_with_strategy(self, mock_get_orch, mock_orchestration_response):
        """전략 지정"""
        mock_orchestrator = Mock()
        mock_orchestrator.process = AsyncMock(return_value=mock_orchestration_response)
        mock_get_orch.return_value = mock_orchestrator

        response = client.post(
            "/api/v1/query",
            json={
                "query": "테스트 질문",
                "strategy": "fast",
            }
        )

        assert response.status_code == 200
        assert response.json()["strategy"] == "standard"  # from mock

    @patch('app.api.v1.endpoints.query.get_orchestrator')
    def test_query_with_options(self, mock_get_orch, mock_orchestration_response):
        """옵션 지정"""
        mock_orchestrator = Mock()
        mock_orchestrator.process = AsyncMock(return_value=mock_orchestration_response)
        mock_get_orch.return_value = mock_orchestrator

        response = client.post(
            "/api/v1/query",
            json={
                "query": "테스트 질문",
                "max_results": 5,
                "include_citations": False,
                "include_follow_ups": False,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["citations"]) == 0
        assert len(data["follow_up_suggestions"]) > 0  # mock에서 제공


# ============================================================================
# Test GET /api/v1/query/{query_id}/status
# ============================================================================


class TestQueryStatusEndpoint:
    """GET /api/v1/query/{query_id}/status 테스트"""

    def test_status_not_found(self):
        """존재하지 않는 질의"""
        response = client.get("/api/v1/query/nonexistent_id/status")

        assert response.status_code == 404
        data = response.json()
        assert "error_code" in data["detail"]
        assert data["detail"]["error_code"] == "QUERY_NOT_FOUND"


# ============================================================================
# Test POST /api/v1/query/async
# ============================================================================


class TestQueryAsyncEndpoint:
    """POST /api/v1/query/async 테스트"""

    @patch('app.api.v1.endpoints.query.get_orchestrator')
    def test_async_query_created(self, mock_get_orch, mock_orchestration_response):
        """비동기 질의 생성"""
        mock_orchestrator = Mock()
        mock_orchestrator.process = AsyncMock(return_value=mock_orchestration_response)
        mock_get_orch.return_value = mock_orchestrator

        response = client.post(
            "/api/v1/query/async",
            json={"query": "테스트 질문"}
        )

        assert response.status_code == 202  # Accepted
        data = response.json()
        assert "query_id" in data
        assert data["status"] == "pending"
        assert data["progress"] == 0


# ============================================================================
# Test GET /api/v1/health
# ============================================================================


class TestHealthEndpoint:
    """GET /api/v1/health 테스트"""

    @patch('app.api.v1.endpoints.query.get_orchestrator')
    def test_health_check(self, mock_get_orch):
        """헬스 체크"""
        mock_orchestrator = Mock()
        mock_orchestrator.health_check = AsyncMock(return_value={
            "status": "healthy",
            "components": {
                "query_analyzer": "ok",
                "hybrid_search": "ok",
                "response_generator": "ok",
            },
            "cache": {},
            "config": {},
        })
        mock_get_orch.return_value = mock_orchestrator

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "components" in data


# ============================================================================
# Test GET /api/v1/
# ============================================================================


class TestRootEndpoint:
    """GET /api/v1/ 테스트"""

    def test_root(self):
        """루트 엔드포인트"""
        response = client.get("/api/v1/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "InsureGraph Pro API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert "/api/v1/query" in data["endpoints"]["query"]


# ============================================================================
# Integration Tests
# ============================================================================


class TestQueryAPIIntegration:
    """통합 테스트"""

    @patch('app.api.v1.endpoints.query.get_orchestrator')
    def test_end_to_end_query(self, mock_get_orch, mock_orchestration_response):
        """E2E 질의 실행"""
        mock_orchestrator = Mock()
        mock_orchestrator.process = AsyncMock(return_value=mock_orchestration_response)
        mock_get_orch.return_value = mock_orchestrator

        # 1. Query 실행
        response = client.post(
            "/api/v1/query",
            json={
                "query": "급성심근경색증에 걸리면 얼마를 받을 수 있나요?",
                "strategy": "standard",
                "include_citations": True,
                "include_follow_ups": True,
            }
        )

        assert response.status_code == 200
        data = response.json()

        # 2. 응답 검증
        assert "query_id" in data
        assert "answer" in data
        assert "format" in data
        assert "confidence" in data
        assert "metrics" in data

        # 3. 메트릭 검증
        metrics = data["metrics"]
        assert metrics["total_duration_ms"] > 0
        assert "cache_hit" in metrics

    @patch('app.api.v1.endpoints.query.get_orchestrator')
    def test_error_handling(self, mock_get_orch):
        """에러 처리"""
        mock_orchestrator = Mock()
        mock_orchestrator.process = AsyncMock(side_effect=Exception("Test error"))
        mock_get_orch.return_value = mock_orchestrator

        response = client.post(
            "/api/v1/query",
            json={"query": "테스트"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "error_code" in data["detail"]
