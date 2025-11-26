"""
Query API Endpoints

사용자 질의 처리 API 엔드포인트.
"""
import asyncio
from typing import Dict
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from loguru import logger
import json
from datetime import datetime

from app.api.v1.models.query import (
    QueryRequest,
    QueryResponse,
    QueryStatusResponse,
    QueryMetrics,
    StreamChunk,
    ErrorResponse,
)
from app.models.orchestration import (
    OrchestrationRequest,
    OrchestrationStrategy,
)
from app.services.orchestration.query_orchestrator import QueryOrchestrator


# Router
router = APIRouter(prefix="/query", tags=["Query"])

# Orchestrator 인스턴스 (싱글톤)
_orchestrator: QueryOrchestrator = None

# 비동기 작업 저장소 (간단한 in-memory store)
_query_tasks: Dict[str, Dict] = {}


def get_orchestrator() -> QueryOrchestrator:
    """QueryOrchestrator 싱글톤 반환"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = QueryOrchestrator()
    return _orchestrator


# ============================================================================
# POST /query - 일반 질의
# ============================================================================


@router.post(
    "",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="질의 실행",
    description="사용자 질문을 처리하고 답변을 생성합니다.",
    responses={
        200: {"description": "성공적으로 답변 생성"},
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        500: {"model": ErrorResponse, "description": "서버 에러"},
    },
)
async def execute_query(request: QueryRequest) -> QueryResponse:
    """
    질의 실행

    GraphRAG 파이프라인을 통해 사용자 질문을 처리하고 답변을 생성합니다.

    **Flow**:
    1. Query Analysis (의도 분석)
    2. Hybrid Search (그래프 + 벡터 검색)
    3. Response Generation (답변 생성)

    **Parameters**:
    - **query**: 사용자 질문 (필수)
    - **strategy**: 실행 전략 (standard/fast/comprehensive)
    - **max_results**: 최대 검색 결과 수 (1-50)
    - **include_citations**: 출처 포함 여부
    - **include_follow_ups**: 후속 질문 포함 여부

    **Returns**:
    - QueryResponse: 생성된 답변 및 메타데이터
    """
    try:
        logger.info(f"Received query request: '{request.query[:50]}...'")

        # Orchestration 요청 생성
        orch_request = OrchestrationRequest(
            query=request.query,
            session_id=request.session_id,
            strategy=OrchestrationStrategy(request.strategy.value),
            use_cache=True,
            include_citations=request.include_citations,
            include_follow_ups=request.include_follow_ups,
            max_search_results=request.max_results,
            conversation_history=request.conversation_history,
        )

        # Orchestrator 실행
        orchestrator = get_orchestrator()
        orch_response = await orchestrator.process(orch_request)

        # API 응답 생성
        api_response = QueryResponse(
            query_id=orch_response.request_id,
            query=orch_response.query,
            answer=orch_response.response.answer,
            format=orch_response.response.format,
            confidence=orch_response.response.confidence_score,
            citations=orch_response.response.citations if request.include_citations else [],
            follow_up_suggestions=orch_response.response.follow_up_suggestions if request.include_follow_ups else [],
            intent=orch_response.query_analysis.intent if orch_response.query_analysis else None,
            strategy=orch_response.strategy.value,
            metrics=QueryMetrics(
                total_duration_ms=orch_response.metrics.total_duration_ms,
                query_analysis_ms=orch_response.metrics.query_analysis_ms,
                search_ms=orch_response.metrics.search_ms,
                response_generation_ms=orch_response.metrics.response_generation_ms,
                cache_hit=orch_response.cache_hit,
                search_result_count=orch_response.metrics.search_result_count,
            ),
            timestamp=orch_response.timestamp,
            success=orch_response.success,
            errors=orch_response.errors,
        )

        logger.info(
            f"Query processed successfully: {api_response.query_id} "
            f"({api_response.metrics.total_duration_ms:.2f}ms)"
        )

        return api_response

    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "QUERY_EXECUTION_FAILED",
                "error_message": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )


# ============================================================================
# GET /query/{query_id}/status - 질의 상태 조회
# ============================================================================


@router.get(
    "/{query_id}/status",
    response_model=QueryStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="질의 상태 조회",
    description="비동기 질의의 현재 상태를 조회합니다.",
    responses={
        200: {"description": "상태 조회 성공"},
        404: {"model": ErrorResponse, "description": "질의를 찾을 수 없음"},
    },
)
async def get_query_status(query_id: str) -> QueryStatusResponse:
    """
    질의 상태 조회

    비동기로 실행 중인 질의의 현재 상태를 조회합니다.

    **Parameters**:
    - **query_id**: 질의 ID

    **Returns**:
    - QueryStatusResponse: 질의 상태 및 결과 (완료된 경우)
    """
    try:
        # 작업 저장소에서 조회
        if query_id not in _query_tasks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "QUERY_NOT_FOUND",
                    "error_message": f"Query ID '{query_id}' not found",
                    "timestamp": datetime.now().isoformat(),
                },
            )

        task_info = _query_tasks[query_id]

        return QueryStatusResponse(
            query_id=query_id,
            status=task_info["status"],
            progress=task_info.get("progress"),
            current_stage=task_info.get("current_stage"),
            result=task_info.get("result"),
            error_message=task_info.get("error_message"),
            created_at=task_info["created_at"],
            updated_at=task_info["updated_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "STATUS_CHECK_FAILED",
                "error_message": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )


# ============================================================================
# POST /query/async - 비동기 질의 (백그라운드 실행)
# ============================================================================


@router.post(
    "/async",
    response_model=QueryStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="비동기 질의 실행",
    description="질의를 백그라운드에서 비동기로 실행합니다.",
)
async def execute_query_async(request: QueryRequest) -> QueryStatusResponse:
    """
    비동기 질의 실행

    질의를 백그라운드에서 실행하고 즉시 질의 ID를 반환합니다.
    상태는 GET /query/{query_id}/status로 조회할 수 있습니다.

    **Parameters**:
    - **request**: QueryRequest

    **Returns**:
    - QueryStatusResponse: 초기 상태 (pending)
    """
    try:
        # Orchestration 요청 생성
        orch_request = OrchestrationRequest(
            query=request.query,
            session_id=request.session_id,
            strategy=OrchestrationStrategy(request.strategy.value),
            use_cache=True,
            include_citations=request.include_citations,
            include_follow_ups=request.include_follow_ups,
            max_search_results=request.max_results,
        )

        # 요청 ID 생성
        import hashlib
        query_id = hashlib.md5(
            f"{request.query}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        # 작업 정보 저장
        _query_tasks[query_id] = {
            "status": "pending",
            "progress": 0,
            "current_stage": "initializing",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        # 백그라운드 작업 시작
        asyncio.create_task(_execute_query_background(query_id, orch_request, request))

        logger.info(f"Async query started: {query_id}")

        return QueryStatusResponse(
            query_id=query_id,
            status="pending",
            progress=0,
            current_stage="initializing",
            created_at=_query_tasks[query_id]["created_at"],
            updated_at=_query_tasks[query_id]["updated_at"],
        )

    except Exception as e:
        logger.error(f"Async query creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "ASYNC_QUERY_FAILED",
                "error_message": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )


async def _execute_query_background(
    query_id: str, orch_request: OrchestrationRequest, api_request: QueryRequest
):
    """백그라운드 질의 실행"""
    try:
        # 상태 업데이트: processing
        _query_tasks[query_id].update({
            "status": "processing",
            "progress": 10,
            "current_stage": "query_analysis",
            "updated_at": datetime.now(),
        })

        # Orchestrator 실행
        orchestrator = get_orchestrator()
        orch_response = await orchestrator.process(orch_request)

        # API 응답 생성
        api_response = QueryResponse(
            query_id=orch_response.request_id,
            query=orch_response.query,
            answer=orch_response.response.answer,
            format=orch_response.response.format,
            confidence=orch_response.response.confidence_score,
            citations=orch_response.response.citations if api_request.include_citations else [],
            follow_up_suggestions=orch_response.response.follow_up_suggestions if api_request.include_follow_ups else [],
            intent=orch_response.query_analysis.intent if orch_response.query_analysis else None,
            strategy=orch_response.strategy.value,
            metrics=QueryMetrics(
                total_duration_ms=orch_response.metrics.total_duration_ms,
                query_analysis_ms=orch_response.metrics.query_analysis_ms,
                search_ms=orch_response.metrics.search_ms,
                response_generation_ms=orch_response.metrics.response_generation_ms,
                cache_hit=orch_response.cache_hit,
                search_result_count=orch_response.metrics.search_result_count,
            ),
            timestamp=orch_response.timestamp,
            success=orch_response.success,
            errors=orch_response.errors,
        )

        # 상태 업데이트: completed
        _query_tasks[query_id].update({
            "status": "completed",
            "progress": 100,
            "current_stage": "completed",
            "result": api_response,
            "updated_at": datetime.now(),
        })

        logger.info(f"Async query completed: {query_id}")

    except Exception as e:
        logger.error(f"Background query execution failed: {e}")
        _query_tasks[query_id].update({
            "status": "failed",
            "progress": 100,
            "error_message": str(e),
            "updated_at": datetime.now(),
        })


# ============================================================================
# WebSocket /ws/query - 스트리밍 질의
# ============================================================================


@router.websocket("/ws")
async def query_websocket(websocket: WebSocket):
    """
    WebSocket 질의 스트리밍

    실시간으로 질의 진행 상황과 결과를 스트리밍합니다.

    **Protocol**:
    1. Client sends: {"query": "...", "strategy": "standard"}
    2. Server sends: {"chunk_type": "status", "content": "processing"}
    3. Server sends: {"chunk_type": "data", "content": "partial answer"}
    4. Server sends: {"chunk_type": "complete", "content": "final answer"}
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            message = json.loads(data)

            query = message.get("query")
            strategy = message.get("strategy", "standard")

            if not query:
                await websocket.send_json({
                    "chunk_type": "error",
                    "content": "Query is required",
                    "timestamp": datetime.now().isoformat(),
                })
                continue

            logger.info(f"WebSocket query received: '{query[:50]}...'")

            # 시작 알림
            await websocket.send_json({
                "chunk_type": "status",
                "content": "started",
                "metadata": {"stage": "initializing"},
                "timestamp": datetime.now().isoformat(),
            })

            try:
                # Orchestration 요청 생성
                orch_request = OrchestrationRequest(
                    query=query,
                    strategy=OrchestrationStrategy(strategy),
                    use_cache=True,
                    include_citations=True,
                    include_follow_ups=True,
                )

                # Stage 1: Query Analysis
                await websocket.send_json({
                    "chunk_type": "status",
                    "content": "analyzing",
                    "metadata": {"stage": "query_analysis", "progress": 10},
                    "timestamp": datetime.now().isoformat(),
                })

                # Orchestrator 실행
                orchestrator = get_orchestrator()
                orch_response = await orchestrator.process(orch_request)

                # Stage 2: Searching
                await websocket.send_json({
                    "chunk_type": "status",
                    "content": "searching",
                    "metadata": {"stage": "search", "progress": 50},
                    "timestamp": datetime.now().isoformat(),
                })

                # Stage 3: Generating
                await websocket.send_json({
                    "chunk_type": "status",
                    "content": "generating",
                    "metadata": {"stage": "response_generation", "progress": 80},
                    "timestamp": datetime.now().isoformat(),
                })

                # 최종 결과 전송
                api_response = QueryResponse(
                    query_id=orch_response.request_id,
                    query=orch_response.query,
                    answer=orch_response.response.answer,
                    format=orch_response.response.format,
                    confidence=orch_response.response.confidence_score,
                    citations=orch_response.response.citations,
                    follow_up_suggestions=orch_response.response.follow_up_suggestions,
                    intent=orch_response.query_analysis.intent if orch_response.query_analysis else None,
                    strategy=orch_response.strategy.value,
                    metrics=QueryMetrics(
                        total_duration_ms=orch_response.metrics.total_duration_ms,
                        cache_hit=orch_response.cache_hit,
                        search_result_count=orch_response.metrics.search_result_count,
                    ),
                    success=orch_response.success,
                    errors=orch_response.errors,
                )

                await websocket.send_json({
                    "chunk_type": "complete",
                    "content": api_response.model_dump(),
                    "metadata": {"progress": 100},
                    "timestamp": datetime.now().isoformat(),
                })

                logger.info(f"WebSocket query completed: {api_response.query_id}")

            except Exception as e:
                logger.error(f"WebSocket query processing failed: {e}")
                await websocket.send_json({
                    "chunk_type": "error",
                    "content": str(e),
                    "timestamp": datetime.now().isoformat(),
                })

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass
