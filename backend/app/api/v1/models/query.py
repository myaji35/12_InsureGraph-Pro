"""
Query API Models

Query API의 Request/Response 모델들.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from app.models.orchestration import OrchestrationStrategy
from app.models.response import AnswerFormat, Citation


class QueryStrategyAPI(str, Enum):
    """API용 쿼리 전략"""
    STANDARD = "standard"
    FAST = "fast"
    COMPREHENSIVE = "comprehensive"


class QueryRequest(BaseModel):
    """
    질의 요청

    사용자가 보험 관련 질문을 하기 위한 요청
    """
    query: str = Field(..., description="사용자 질문", min_length=1, max_length=1000)

    # 옵션
    strategy: QueryStrategyAPI = Field(
        default=QueryStrategyAPI.STANDARD,
        description="쿼리 실행 전략"
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=50,
        description="최대 검색 결과 수"
    )
    include_citations: bool = Field(
        default=True,
        description="출처 포함 여부"
    )
    include_follow_ups: bool = Field(
        default=True,
        description="후속 질문 포함 여부"
    )

    # 컨텍스트 (optional)
    session_id: Optional[str] = Field(
        None,
        description="세션 ID (대화 이력 유지용)"
    )
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="대화 이력",
        max_length=10
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "급성심근경색증에 걸리면 얼마를 받을 수 있나요?",
                "strategy": "standard",
                "max_results": 10,
                "include_citations": True,
                "include_follow_ups": True
            }
        }


class QueryMetrics(BaseModel):
    """쿼리 실행 메트릭"""
    total_duration_ms: float = Field(..., description="전체 실행 시간 (ms)")
    query_analysis_ms: Optional[float] = Field(None, description="질의 분석 시간")
    search_ms: Optional[float] = Field(None, description="검색 시간")
    response_generation_ms: Optional[float] = Field(None, description="응답 생성 시간")
    cache_hit: bool = Field(default=False, description="캐시 히트 여부")
    search_result_count: int = Field(default=0, description="검색 결과 수")


class QueryResponse(BaseModel):
    """
    질의 응답

    사용자 질문에 대한 최종 응답
    """
    # 기본 정보
    query_id: str = Field(..., description="질의 ID")
    query: str = Field(..., description="원본 질문")

    # 답변
    answer: str = Field(..., description="생성된 답변")
    format: AnswerFormat = Field(..., description="답변 형식")
    confidence: float = Field(..., ge=0.0, le=1.0, description="답변 신뢰도")

    # 추가 정보
    citations: List[Citation] = Field(
        default_factory=list,
        description="출처 목록"
    )
    follow_up_suggestions: List[str] = Field(
        default_factory=list,
        description="후속 질문 제안"
    )

    # 메타데이터
    intent: Optional[str] = Field(None, description="감지된 의도")
    strategy: str = Field(..., description="사용된 전략")
    metrics: QueryMetrics = Field(..., description="실행 메트릭")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")

    # 상태
    success: bool = Field(default=True, description="성공 여부")
    errors: List[str] = Field(default_factory=list, description="에러 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "q_a1b2c3d4",
                "query": "급성심근경색증에 걸리면 얼마를 받을 수 있나요?",
                "answer": "급성심근경색증의 경우 진단비 5,000만원과 입원비 100만원을 받을 수 있습니다.",
                "format": "table",
                "confidence": 0.92,
                "citations": [],
                "follow_up_suggestions": [
                    "대기기간은 얼마나 되나요?",
                    "보장 조건이 있나요?"
                ],
                "intent": "coverage_amount",
                "strategy": "standard",
                "metrics": {
                    "total_duration_ms": 287.5,
                    "cache_hit": False,
                    "search_result_count": 8
                },
                "success": True,
                "errors": []
            }
        }


class QueryStatusResponse(BaseModel):
    """
    질의 상태 응답

    비동기 질의의 현재 상태
    """
    query_id: str = Field(..., description="질의 ID")
    status: str = Field(..., description="상태 (pending/processing/completed/failed)")
    progress: Optional[int] = Field(None, ge=0, le=100, description="진행률 (%)")
    current_stage: Optional[str] = Field(None, description="현재 단계")
    result: Optional[QueryResponse] = Field(None, description="완료된 경우 결과")
    error_message: Optional[str] = Field(None, description="실패한 경우 에러 메시지")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    updated_at: datetime = Field(default_factory=datetime.now, description="업데이트 시간")

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "q_a1b2c3d4",
                "status": "completed",
                "progress": 100,
                "current_stage": "response_generation",
                "result": {
                    "query_id": "q_a1b2c3d4",
                    "answer": "답변입니다."
                }
            }
        }


class StreamChunk(BaseModel):
    """
    스트리밍 청크

    WebSocket을 통한 실시간 응답 전송
    """
    chunk_type: str = Field(..., description="청크 타입 (status/data/error/complete)")
    content: Optional[str] = Field(None, description="내용")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")
    timestamp: datetime = Field(default_factory=datetime.now, description="시간")

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_type": "data",
                "content": "급성심근경색증의 경우",
                "metadata": {"progress": 30},
                "timestamp": "2025-11-25T20:00:00"
            }
        }


class ErrorResponse(BaseModel):
    """
    에러 응답

    API 에러 발생 시 반환
    """
    error_code: str = Field(..., description="에러 코드")
    error_message: str = Field(..., description="에러 메시지")
    details: Optional[Dict[str, Any]] = Field(None, description="에러 상세")
    timestamp: datetime = Field(default_factory=datetime.now, description="발생 시간")
    request_id: Optional[str] = Field(None, description="요청 ID")

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "INVALID_QUERY",
                "error_message": "질문이 너무 짧습니다.",
                "details": {"min_length": 1},
                "timestamp": "2025-11-25T20:00:00"
            }
        }


class HealthCheckResponse(BaseModel):
    """헬스 체크 응답"""
    status: str = Field(..., description="상태 (healthy/degraded/unhealthy)")
    version: str = Field(..., description="API 버전")
    components: Dict[str, str] = Field(..., description="컴포넌트 상태")
    timestamp: datetime = Field(default_factory=datetime.now, description="시간")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "components": {
                    "query_analyzer": "ok",
                    "hybrid_search": "ok",
                    "response_generator": "ok",
                    "cache": "ok"
                },
                "timestamp": "2025-11-25T20:00:00"
            }
        }
