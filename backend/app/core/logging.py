"""
Request Logging and Monitoring

Story 3.4: Rate Limiting & Monitoring - 로깅 및 모니터링
"""
import time
import json
from typing import Dict, Optional
from datetime import datetime
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from app.core.config import settings


# ============================================================================
# Request Logging Middleware
# ============================================================================


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    모든 HTTP 요청을 로깅하는 미들웨어

    - Request/Response 정보
    - 처리 시간
    - Status code
    - User agent, IP 등
    """
    async def dispatch(self, request: Request, call_next):
        """요청 처리"""
        # Generate request ID
        request_id = str(uuid4())[:8]

        # Record start time
        start_time = time.time()

        # Extract request info
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""

        # Get client info
        client_host = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        real_ip = forwarded_for.split(",")[0].strip() if forwarded_for else client_host

        # Get user agent
        user_agent = request.headers.get("User-Agent", "unknown")

        # Get user info (if authenticated)
        auth_header = request.headers.get("Authorization")
        user_id = "anonymous"
        if auth_header and auth_header.startswith("Bearer "):
            # Try to extract user from token (simplified)
            user_id = "authenticated"

        # Add request ID to request state
        request.state.request_id = request_id

        # Log request start
        logger.info(
            f"[{request_id}] {method} {path} | "
            f"IP: {real_ip} | User: {user_id}"
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                f"[{request_id}] {method} {path} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration_ms:.2f}ms"
            )

            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            # Record metrics
            _record_request_metrics(
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=user_id,
            )

            return response

        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            logger.error(
                f"[{request_id}] {method} {path} | "
                f"Error: {str(e)} | "
                f"Duration: {duration_ms:.2f}ms"
            )

            # Record error metrics
            _record_error_metrics(
                method=method,
                path=path,
                error_type=type(e).__name__,
                user_id=user_id,
            )

            # Re-raise
            raise


# ============================================================================
# Metrics Storage
# ============================================================================


class MetricsStore:
    """
    메트릭 저장소

    Production: Prometheus, Datadog 등으로 교체
    """
    def __init__(self):
        # Request metrics
        self.request_count: Dict[str, int] = {}  # endpoint -> count
        self.request_duration: Dict[str, list] = {}  # endpoint -> [durations]
        self.status_codes: Dict[int, int] = {}  # status_code -> count

        # Error metrics
        self.error_count: Dict[str, int] = {}  # error_type -> count
        self.error_by_endpoint: Dict[str, int] = {}  # endpoint -> count

        # User metrics
        self.requests_by_user: Dict[str, int] = {}  # user_id -> count

        # Timestamp
        self.start_time = datetime.now()

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: str = "anonymous"
    ):
        """요청 기록"""
        # Endpoint key
        endpoint = f"{method} {path}"

        # Request count
        self.request_count[endpoint] = self.request_count.get(endpoint, 0) + 1

        # Duration
        if endpoint not in self.request_duration:
            self.request_duration[endpoint] = []
        self.request_duration[endpoint].append(duration_ms)

        # Keep only last 1000 durations per endpoint
        if len(self.request_duration[endpoint]) > 1000:
            self.request_duration[endpoint] = self.request_duration[endpoint][-1000:]

        # Status codes
        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1

        # User requests
        self.requests_by_user[user_id] = self.requests_by_user.get(user_id, 0) + 1

    def record_error(
        self,
        method: str,
        path: str,
        error_type: str,
        user_id: str = "anonymous"
    ):
        """에러 기록"""
        # Error count by type
        self.error_count[error_type] = self.error_count.get(error_type, 0) + 1

        # Error count by endpoint
        endpoint = f"{method} {path}"
        self.error_by_endpoint[endpoint] = self.error_by_endpoint.get(endpoint, 0) + 1

    def get_stats(self) -> Dict:
        """통계 조회"""
        # Calculate percentiles
        all_durations = []
        for durations in self.request_duration.values():
            all_durations.extend(durations)

        all_durations.sort()

        p50 = all_durations[len(all_durations) // 2] if all_durations else 0
        p95 = all_durations[int(len(all_durations) * 0.95)] if all_durations else 0
        p99 = all_durations[int(len(all_durations) * 0.99)] if all_durations else 0

        # Total requests
        total_requests = sum(self.request_count.values())
        total_errors = sum(self.error_count.values())

        # Uptime
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()

        return {
            "uptime_seconds": uptime_seconds,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "requests_per_second": total_requests / uptime_seconds if uptime_seconds > 0 else 0,
            "response_time": {
                "p50_ms": p50,
                "p95_ms": p95,
                "p99_ms": p99,
            },
            "top_endpoints": self._get_top_endpoints(5),
            "status_codes": self.status_codes,
            "error_types": self.error_count,
        }

    def _get_top_endpoints(self, limit: int = 5) -> Dict[str, int]:
        """가장 많이 호출된 엔드포인트"""
        sorted_endpoints = sorted(
            self.request_count.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return dict(sorted_endpoints[:limit])

    def get_prometheus_metrics(self) -> str:
        """
        Prometheus 형식 메트릭 반환

        Format:
        # HELP metric_name Description
        # TYPE metric_name type
        metric_name{label="value"} value
        """
        lines = []

        # Total requests
        lines.append("# HELP http_requests_total Total HTTP requests")
        lines.append("# TYPE http_requests_total counter")
        for endpoint, count in self.request_count.items():
            method, path = endpoint.split(" ", 1)
            lines.append(f'http_requests_total{{method="{method}",path="{path}"}} {count}')

        # Response time
        lines.append("\n# HELP http_request_duration_milliseconds HTTP request duration in milliseconds")
        lines.append("# TYPE http_request_duration_milliseconds histogram")
        for endpoint, durations in self.request_duration.items():
            if durations:
                method, path = endpoint.split(" ", 1)
                avg_duration = sum(durations) / len(durations)
                lines.append(f'http_request_duration_milliseconds{{method="{method}",path="{path}"}} {avg_duration}')

        # Status codes
        lines.append("\n# HELP http_responses_total Total HTTP responses by status code")
        lines.append("# TYPE http_responses_total counter")
        for status_code, count in self.status_codes.items():
            lines.append(f'http_responses_total{{status_code="{status_code}"}} {count}')

        # Errors
        lines.append("\n# HELP http_errors_total Total HTTP errors by type")
        lines.append("# TYPE http_errors_total counter")
        for error_type, count in self.error_count.items():
            lines.append(f'http_errors_total{{error_type="{error_type}"}} {count}')

        return "\n".join(lines)


# Global metrics store
_metrics_store = MetricsStore()


def _record_request_metrics(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: str = "anonymous"
):
    """메트릭 기록 헬퍼"""
    _metrics_store.record_request(method, path, status_code, duration_ms, user_id)


def _record_error_metrics(
    method: str,
    path: str,
    error_type: str,
    user_id: str = "anonymous"
):
    """에러 메트릭 기록 헬퍼"""
    _metrics_store.record_error(method, path, error_type, user_id)


def get_metrics_store() -> MetricsStore:
    """메트릭 스토어 조회"""
    return _metrics_store


# ============================================================================
# Error Tracking
# ============================================================================


class ErrorTracker:
    """
    에러 추적 및 분석

    Production: Sentry, Rollbar 등으로 교체
    """
    def __init__(self):
        self.errors: list = []
        self.max_errors = 100  # Keep last 100 errors

    def track_error(
        self,
        error: Exception,
        request: Optional[Request] = None,
        context: Optional[Dict] = None
    ):
        """에러 추적"""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": self._get_stack_trace(error) if settings.DEBUG else None,
        }

        if request:
            error_info["request"] = {
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
            }

        if context:
            error_info["context"] = context

        self.errors.append(error_info)

        # Keep only last N errors
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]

        # Log error
        logger.error(
            f"Error tracked: {error_info['error_type']} - {error_info['error_message']}"
        )

    def _get_stack_trace(self, error: Exception) -> str:
        """스택 트레이스 추출"""
        import traceback
        return "".join(traceback.format_exception(type(error), error, error.__traceback__))

    def get_recent_errors(self, limit: int = 10) -> list:
        """최근 에러 조회"""
        return self.errors[-limit:]

    def get_error_summary(self) -> Dict:
        """에러 요약"""
        if not self.errors:
            return {"total_errors": 0, "error_types": {}}

        error_types = {}
        for error in self.errors:
            error_type = error["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            "total_errors": len(self.errors),
            "error_types": error_types,
            "recent_errors": self.get_recent_errors(5),
        }


# Global error tracker
_error_tracker = ErrorTracker()


def get_error_tracker() -> ErrorTracker:
    """에러 트래커 조회"""
    return _error_tracker
