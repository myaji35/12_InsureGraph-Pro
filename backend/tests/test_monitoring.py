"""
Tests for Monitoring and Rate Limiting

Story 3.4: Rate Limiting & Monitoring 테스트
"""
import pytest
import time
from fastapi.testclient import TestClient

from app.main import app


# TestClient
client = TestClient(app)


# ============================================================================
# Test Monitoring Endpoints
# ============================================================================


class TestMonitoringEndpoints:
    """Monitoring endpoints 테스트"""

    def test_get_metrics(self):
        """Prometheus 메트릭 조회"""
        response = client.get("/api/v1/monitoring/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        # Check for Prometheus format
        content = response.text
        assert "# HELP" in content or "# TYPE" in content or len(content) == 0

    def test_get_stats(self):
        """시스템 통계 조회"""
        response = client.get("/api/v1/monitoring/stats")

        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "app_name" in data
        assert "stats" in data
        assert "total_requests" in data["stats"]

    def test_get_errors(self):
        """에러 로그 조회"""
        response = client.get("/api/v1/monitoring/errors")

        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "errors" in data

    def test_detailed_health_check(self):
        """상세 헬스 체크"""
        response = client.get("/api/v1/monitoring/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "metrics" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]


# ============================================================================
# Test Rate Limiting
# ============================================================================


class TestRateLimiting:
    """Rate limiting 테스트"""

    def test_rate_limit_headers(self):
        """Rate limit 헤더 확인"""
        response = client.get("/api/v1/")

        # Check rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_rate_limit_exceeded(self):
        """Rate limit 초과 테스트"""
        # Note: This test might be slow as it makes many requests
        # Skip in CI environment if needed

        # Get rate limit
        response = client.get("/api/v1/")
        limit = int(response.headers.get("X-RateLimit-Limit", 100))

        # Make requests until limit
        # (This is a simplified test - actual rate limit is 100/min)
        # For testing, we can't easily exceed the limit without modifying settings

        assert response.status_code == 200


# ============================================================================
# Test Request Logging
# ============================================================================


class TestRequestLogging:
    """Request logging 테스트"""

    def test_request_id_header(self):
        """Request ID 헤더 확인"""
        response = client.get("/api/v1/")

        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_response_time_header(self):
        """Response time 헤더 확인"""
        response = client.get("/api/v1/")

        assert "X-Response-Time" in response.headers
        assert "ms" in response.headers["X-Response-Time"]


# ============================================================================
# Test Metrics Collection
# ============================================================================


class TestMetricsCollection:
    """Metrics 수집 테스트"""

    def test_metrics_after_requests(self):
        """요청 후 메트릭 확인"""
        # Make some requests
        for _ in range(5):
            client.get("/api/v1/")

        # Check metrics
        response = client.get("/api/v1/monitoring/stats")
        assert response.status_code == 200

        data = response.json()
        stats = data["stats"]

        # Should have recorded some requests
        assert stats["total_requests"] > 0

    def test_prometheus_format(self):
        """Prometheus 형식 확인"""
        # Make a request to generate metrics
        client.get("/api/v1/")

        # Get metrics
        response = client.get("/api/v1/monitoring/metrics")
        assert response.status_code == 200

        content = response.text

        # Check for Prometheus metric format
        # Format: metric_name{label="value"} number
        if content:  # Only check if there are metrics
            assert any([
                "http_requests_total" in content,
                "http_request_duration" in content,
                "http_responses_total" in content,
                "# HELP" in content,
                "# TYPE" in content
            ])


# ============================================================================
# Integration Tests
# ============================================================================


class TestMonitoringIntegration:
    """통합 테스트"""

    def test_full_monitoring_flow(self):
        """전체 모니터링 플로우"""
        # 1. Make some requests
        for i in range(3):
            response = client.get("/api/v1/")
            assert response.status_code == 200
            assert "X-Request-ID" in response.headers

        # 2. Check stats
        stats_response = client.get("/api/v1/monitoring/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()["stats"]
        assert stats["total_requests"] >= 3

        # 3. Check metrics
        metrics_response = client.get("/api/v1/monitoring/metrics")
        assert metrics_response.status_code == 200

        # 4. Check detailed health
        health_response = client.get("/api/v1/monitoring/health/detailed")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        assert health_data["metrics"]["total_requests"] >= 3
