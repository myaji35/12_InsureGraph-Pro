"""
API v1 Router

API v1의 모든 엔드포인트를 통합하는 라우터.
"""
from fastapi import APIRouter, status
from loguru import logger

from app.api.v1.endpoints import query, auth, monitoring, graph, metadata, test_crawler, ingest, query_simple, search, customers, analytics, query_history, ga_analytics, notifications
from app.api.v1.endpoints import documents, crawler_documents, crawler_urls, fp_customers
from app.api.v1.endpoints import insurer_crawlers, learning_stats, knowledge, knowledge_graph, relearning
# Temporarily disabled documents due to missing pdfplumber
# from app.api.v1.endpoints import documents
# Temporarily disabled crawler due to missing app.core.deps
# from app.api.v1.endpoints import crawler
from app.api.v1.models.query import HealthCheckResponse
from app.services.orchestration.query_orchestrator import QueryOrchestrator


# API v1 Router
api_router = APIRouter()

# Auth endpoints
api_router.include_router(auth.router)

# Metadata endpoints (Human-in-the-Loop)
api_router.include_router(metadata.router)

# Ingest endpoints (Policy Upload & Job Management)
api_router.include_router(ingest.router)

# Query endpoints
api_router.include_router(query.router)

# Simple Query endpoints (Stories 2.1-2.5)
api_router.include_router(query_simple.router, prefix="/query-simple", tags=["Query Simple"])

# Customer endpoints (Story 3.4)
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])

# Analytics endpoints (Story 3.5)
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

# Query History endpoints (Enhancement #2)
api_router.include_router(query_history.router, prefix="/query-history", tags=["Query History"])

# GA Analytics endpoints (Enhancement #4)
api_router.include_router(ga_analytics.router, prefix="/ga-analytics", tags=["GA Analytics"])

# Notifications endpoints (Task D)
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])

# Search endpoints (MVP)
api_router.include_router(search.router)

# Document endpoints
api_router.include_router(documents.router)

# Monitoring endpoints
api_router.include_router(monitoring.router)

# Graph endpoints
api_router.include_router(graph.router)

# Test Crawler endpoints (new)
api_router.include_router(test_crawler.router)

# Crawler Documents endpoints (includes URL management)
api_router.include_router(crawler_documents.router)

# FP Customer Management endpoints
api_router.include_router(fp_customers.router, prefix="/fp", tags=["FP Customers"])

# Insurer Crawlers endpoints (Samsung Fire, KB Insurance, etc.)
api_router.include_router(insurer_crawlers.router, prefix="/crawlers", tags=["Insurer Crawlers"])

# Learning Statistics endpoints (Smart Insurance Learner monitoring)
api_router.include_router(learning_stats.router, prefix="/learning", tags=["Learning Stats"])

# Knowledge Extraction endpoints (Entity extraction from documents)
api_router.include_router(knowledge.router)

# Knowledge Graph endpoints (Neo4j graph visualization)
api_router.include_router(knowledge_graph.router, prefix="/knowledge-graph", tags=["Knowledge Graph"])

# Relearning endpoints (Incremental Learning with Upstage)
api_router.include_router(relearning.router, prefix="/relearning", tags=["Relearning"])

# Crawler endpoints (temporarily disabled)
# api_router.include_router(crawler.router, prefix="/crawler", tags=["Crawler"])


# Health Check
@api_router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="헬스 체크",
    description="API 및 시스템 상태를 확인합니다.",
    tags=["Health"],
)
async def health_check() -> HealthCheckResponse:
    """
    헬스 체크

    API 서버와 주요 컴포넌트의 상태를 확인합니다.

    **Returns**:
    - HealthCheckResponse: 시스템 상태
    """
    try:
        # Orchestrator health check
        orchestrator = query.get_orchestrator()
        health = await orchestrator.health_check()

        return HealthCheckResponse(
            status=health["status"],
            version="1.0.0",
            components=health["components"],
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            version="1.0.0",
            components={
                "error": str(e)
            },
        )


# Root endpoint
@api_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="API 루트",
    description="API v1 루트 엔드포인트",
    tags=["Root"],
)
async def root():
    """
    API 루트

    API v1의 기본 정보를 반환합니다.
    """
    return {
        "name": "InsureGraph Pro API",
        "version": "1.0.0",
        "description": "GraphRAG 기반 보험 질의응답 API",
        "docs_url": "/docs",
        "health_url": "/api/v1/health",
        "endpoints": {
            "auth_register": "/api/v1/auth/register",
            "auth_login": "/api/v1/auth/login",
            "auth_refresh": "/api/v1/auth/refresh",
            "auth_logout": "/api/v1/auth/logout",
            "auth_me": "/api/v1/auth/me",
            "query": "/api/v1/query",
            "query_async": "/api/v1/query/async",
            "query_status": "/api/v1/query/{query_id}/status",
            "query_ws": "/api/v1/query/ws",
            "documents": "/api/v1/documents",
            "document_upload": "/api/v1/documents/upload",
            "document_detail": "/api/v1/documents/{document_id}",
            "document_content": "/api/v1/documents/{document_id}/content",
            "document_stats": "/api/v1/documents/stats/summary",
            "metadata_policies": "/api/v1/metadata/policies",
            "metadata_queue": "/api/v1/metadata/queue",
            "metadata_stats": "/api/v1/metadata/stats",
        },
    }
