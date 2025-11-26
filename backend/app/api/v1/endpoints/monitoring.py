"""
Monitoring and Metrics Endpoints

Story 3.4: Rate Limiting & Monitoring - 모니터링 엔드포인트
"""
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Response, status
from loguru import logger

from app.core.logging import get_metrics_store, get_error_tracker
from app.core.config import settings


# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="Prometheus 메트릭",
    description="""
    Prometheus 형식의 메트릭을 반환합니다.

    이 엔드포인트는 Prometheus scraper에서 사용됩니다.
    """,
    response_class=Response,
)
async def get_metrics():
    """
    Prometheus 메트릭 조회

    Returns:
        Prometheus text format metrics
    """
    metrics_store = get_metrics_store()
    prometheus_metrics = metrics_store.get_prometheus_metrics()

    return Response(
        content=prometheus_metrics,
        media_type="text/plain; version=0.0.4"
    )


@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    summary="시스템 통계",
    description="""
    시스템 통계를 JSON 형식으로 반환합니다.

    - 총 요청 수
    - 응답 시간 (p50, p95, p99)
    - 에러율
    - 상위 엔드포인트
    """,
)
async def get_stats() -> Dict:
    """
    시스템 통계 조회

    Returns:
        System statistics
    """
    metrics_store = get_metrics_store()
    stats = metrics_store.get_stats()

    return {
        "timestamp": datetime.now().isoformat(),
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "stats": stats,
    }


@router.get(
    "/errors",
    status_code=status.HTTP_200_OK,
    summary="에러 로그",
    description="""
    최근 에러 로그를 조회합니다.

    **Warning**: Production에서는 인증된 사용자만 접근해야 합니다.
    """,
)
async def get_errors() -> Dict:
    """
    에러 로그 조회

    Returns:
        Recent errors
    """
    # In production: Add authentication check
    # if current_user.role != "admin":
    #     raise HTTPException(403, detail="Admin access required")

    error_tracker = get_error_tracker()
    error_summary = error_tracker.get_error_summary()

    return {
        "timestamp": datetime.now().isoformat(),
        "errors": error_summary,
    }


@router.get(
    "/health/detailed",
    status_code=status.HTTP_200_OK,
    summary="상세 헬스 체크",
    description="""
    시스템의 상세한 건강 상태를 확인합니다.

    - Application status
    - Database connections
    - Metrics summary
    - Error rate
    """,
)
async def detailed_health_check() -> Dict:
    """
    상세 헬스 체크

    Returns:
        Detailed health information
    """
    metrics_store = get_metrics_store()
    stats = metrics_store.get_stats()
    error_tracker = get_error_tracker()
    error_summary = error_tracker.get_error_summary()

    # Check database connections (simplified)
    db_status = "ok"  # In production: actual DB health checks
    cache_status = "ok"  # In production: actual Redis health checks

    # Determine overall health
    error_rate = stats.get("error_rate", 0)
    if error_rate > 0.1:  # > 10% error rate
        overall_status = "degraded"
    elif error_rate > 0.5:  # > 50% error rate
        overall_status = "unhealthy"
    else:
        overall_status = "healthy"

    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        },
        "components": {
            "database": db_status,
            "cache": cache_status,
            "api": "ok",
        },
        "metrics": {
            "uptime_seconds": stats.get("uptime_seconds", 0),
            "total_requests": stats.get("total_requests", 0),
            "requests_per_second": stats.get("requests_per_second", 0),
            "error_rate": error_rate,
            "response_time_p95_ms": stats.get("response_time", {}).get("p95_ms", 0),
        },
        "errors": {
            "total": error_summary.get("total_errors", 0),
            "types": error_summary.get("error_types", {}),
        },
    }


@router.post(
    "/test-error",
    status_code=status.HTTP_200_OK,
    summary="에러 테스트",
    description="""
    에러 추적을 테스트하기 위한 엔드포인트입니다.

    **Warning**: Development/Testing only
    """,
)
async def test_error():
    """
    에러 테스트

    Raises:
        Exception: Test error
    """
    if not settings.DEBUG:
        return {"message": "This endpoint is only available in DEBUG mode"}

    logger.error("Test error triggered")
    raise Exception("This is a test error")
