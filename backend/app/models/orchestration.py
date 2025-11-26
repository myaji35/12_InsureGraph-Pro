"""
Orchestration Models

Query Orchestration을 위한 데이터 모델들.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

from app.models.query import QueryAnalysisResult
from app.models.graph_query import GraphQueryResponse
from app.models.vector_search import SearchResponse
from app.models.response import GeneratedResponse


class OrchestrationStrategy(str, Enum):
    """오케스트레이션 전략"""

    STANDARD = "standard"  # 표준: Analysis → Search → Generation
    FAST = "fast"  # 빠른: 캐시 우선, 간단한 응답
    COMPREHENSIVE = "comprehensive"  # 포괄적: 모든 검색 전략 시도
    FALLBACK = "fallback"  # 폴백: 에러 발생 시 기본 응답


class ExecutionStage(str, Enum):
    """실행 단계"""

    STARTED = "started"
    QUERY_ANALYSIS = "query_analysis"
    SEARCH = "search"
    RESPONSE_GENERATION = "response_generation"
    COMPLETED = "completed"
    FAILED = "failed"


class OrchestrationRequest(BaseModel):
    """
    오케스트레이션 요청
    """

    # 질문 정보
    query: str = Field(..., description="사용자 질문")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    session_id: Optional[str] = Field(None, description="세션 ID")

    # 전략 및 옵션
    strategy: OrchestrationStrategy = Field(
        default=OrchestrationStrategy.STANDARD, description="오케스트레이션 전략"
    )
    use_cache: bool = Field(default=True, description="캐시 사용 여부")
    include_citations: bool = Field(default=True, description="출처 포함 여부")
    include_follow_ups: bool = Field(default=True, description="후속 질문 포함 여부")

    # 제한
    max_search_results: int = Field(default=10, description="최대 검색 결과 수")
    timeout_seconds: Optional[int] = Field(None, description="타임아웃 (초)")

    # 컨텍스트
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="대화 이력"
    )
    user_context: Dict[str, Any] = Field(
        default_factory=dict, description="사용자 컨텍스트"
    )


class StageMetrics(BaseModel):
    """단계별 메트릭"""

    stage: ExecutionStage = Field(..., description="실행 단계")
    start_time: datetime = Field(..., description="시작 시간")
    end_time: Optional[datetime] = Field(None, description="종료 시간")
    duration_ms: Optional[float] = Field(None, description="실행 시간 (ms)")
    success: bool = Field(default=True, description="성공 여부")
    error: Optional[str] = Field(None, description="에러 메시지")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")

    def mark_completed(self, success: bool = True, error: Optional[str] = None):
        """단계 완료 표시"""
        self.end_time = datetime.now()
        self.duration_ms = (
            (self.end_time - self.start_time).total_seconds() * 1000
        )
        self.success = success
        self.error = error


class OrchestrationMetrics(BaseModel):
    """
    오케스트레이션 메트릭
    """

    # 전체 메트릭
    total_duration_ms: float = Field(..., description="전체 실행 시간 (ms)")
    stages: List[StageMetrics] = Field(default_factory=list, description="단계별 메트릭")

    # 세부 시간
    query_analysis_ms: Optional[float] = Field(None, description="질의 분석 시간")
    search_ms: Optional[float] = Field(None, description="검색 시간")
    response_generation_ms: Optional[float] = Field(None, description="응답 생성 시간")

    # 성능 지표
    cache_hit: bool = Field(default=False, description="캐시 히트 여부")
    search_result_count: int = Field(default=0, description="검색 결과 수")
    tokens_used: Optional[int] = Field(None, description="사용된 토큰 수")

    def add_stage(self, stage: StageMetrics):
        """단계 메트릭 추가"""
        self.stages.append(stage)

        # 단계별 시간 업데이트
        if stage.stage == ExecutionStage.QUERY_ANALYSIS and stage.duration_ms:
            self.query_analysis_ms = stage.duration_ms
        elif stage.stage == ExecutionStage.SEARCH and stage.duration_ms:
            self.search_ms = stage.duration_ms
        elif stage.stage == ExecutionStage.RESPONSE_GENERATION and stage.duration_ms:
            self.response_generation_ms = stage.duration_ms

    def get_stage_metrics(self, stage: ExecutionStage) -> Optional[StageMetrics]:
        """특정 단계 메트릭 조회"""
        for s in self.stages:
            if s.stage == stage:
                return s
        return None


class OrchestrationContext(BaseModel):
    """
    오케스트레이션 컨텍스트

    실행 중 공유되는 컨텍스트 정보
    """

    request_id: str = Field(..., description="요청 ID")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")

    # 실행 상태
    current_stage: ExecutionStage = Field(
        default=ExecutionStage.STARTED, description="현재 단계"
    )
    strategy: OrchestrationStrategy = Field(..., description="실행 전략")

    # 중간 결과
    query_analysis: Optional[QueryAnalysisResult] = Field(
        None, description="질의 분석 결과"
    )
    search_response: Optional[SearchResponse] = Field(None, description="검색 결과")
    graph_response: Optional[GraphQueryResponse] = Field(None, description="그래프 쿼리 결과")

    # 메타데이터
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")
    errors: List[str] = Field(default_factory=list, description="발생한 에러 목록")

    def add_error(self, error: str):
        """에러 추가"""
        self.errors.append(error)

    def has_errors(self) -> bool:
        """에러 존재 여부"""
        return len(self.errors) > 0


class OrchestrationResponse(BaseModel):
    """
    오케스트레이션 응답

    전체 파이프라인 실행 결과
    """

    # 요청 정보
    request_id: str = Field(..., description="요청 ID")
    query: str = Field(..., description="원본 질문")

    # 최종 응답
    response: GeneratedResponse = Field(..., description="생성된 응답")

    # 중간 결과 (디버깅/분석용)
    query_analysis: Optional[QueryAnalysisResult] = Field(
        None, description="질의 분석 결과"
    )
    search_response: Optional[SearchResponse] = Field(None, description="검색 결과")

    # 실행 정보
    strategy: OrchestrationStrategy = Field(..., description="실행 전략")
    success: bool = Field(default=True, description="성공 여부")
    errors: List[str] = Field(default_factory=list, description="에러 목록")

    # 메트릭
    metrics: OrchestrationMetrics = Field(..., description="실행 메트릭")

    # 메타데이터
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")
    cache_hit: bool = Field(default=False, description="캐시 히트 여부")

    def get_summary(self) -> Dict[str, Any]:
        """응답 요약"""
        return {
            "query": self.query,
            "answer": self.response.answer[:100] + "..."
            if len(self.response.answer) > 100
            else self.response.answer,
            "format": self.response.format,
            "confidence": self.response.confidence_score,
            "total_time_ms": self.metrics.total_duration_ms,
            "cache_hit": self.cache_hit,
            "success": self.success,
        }


class CacheEntry(BaseModel):
    """캐시 엔트리"""

    key: str = Field(..., description="캐시 키")
    query: str = Field(..., description="질문")
    response: OrchestrationResponse = Field(..., description="응답")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    hits: int = Field(default=0, description="히트 횟수")
    last_accessed: datetime = Field(default_factory=datetime.now, description="마지막 접근")

    def access(self):
        """캐시 접근 기록"""
        self.hits += 1
        self.last_accessed = datetime.now()

    def is_expired(self, ttl_seconds: int = 3600) -> bool:
        """만료 여부 (기본 1시간)"""
        age_seconds = (datetime.now() - self.created_at).total_seconds()
        return age_seconds > ttl_seconds


class OrchestrationError(BaseModel):
    """오케스트레이션 에러"""

    error_type: str = Field(..., description="에러 타입")
    stage: ExecutionStage = Field(..., description="발생 단계")
    message: str = Field(..., description="에러 메시지")
    details: Optional[Dict[str, Any]] = Field(None, description="에러 상세")
    timestamp: datetime = Field(default_factory=datetime.now, description="발생 시간")
    recoverable: bool = Field(default=True, description="복구 가능 여부")

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "error_type": self.error_type,
            "stage": self.stage,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "recoverable": self.recoverable,
        }


class OrchestrationConfig(BaseModel):
    """
    오케스트레이션 설정
    """

    # 타임아웃
    default_timeout_seconds: int = Field(default=30, description="기본 타임아웃")
    query_analysis_timeout: int = Field(default=5, description="질의 분석 타임아웃")
    search_timeout: int = Field(default=15, description="검색 타임아웃")
    response_generation_timeout: int = Field(default=10, description="응답 생성 타임아웃")

    # 캐시
    cache_enabled: bool = Field(default=True, description="캐시 활성화")
    cache_ttl_seconds: int = Field(default=3600, description="캐시 TTL (1시간)")
    cache_max_size: int = Field(default=1000, description="최대 캐시 크기")

    # 재시도
    max_retries: int = Field(default=3, description="최대 재시도 횟수")
    retry_delay_seconds: float = Field(default=1.0, description="재시도 대기 시간")

    # 검색
    default_search_limit: int = Field(default=10, description="기본 검색 결과 수")
    min_confidence_threshold: float = Field(default=0.3, description="최소 신뢰도")

    # 폴백
    enable_fallback: bool = Field(default=True, description="폴백 활성화")
    fallback_response: str = Field(
        default="죄송합니다. 요청을 처리하는 중 문제가 발생했습니다.",
        description="폴백 응답",
    )

    # 로깅
    log_intermediate_results: bool = Field(
        default=False, description="중간 결과 로깅"
    )
    log_performance_metrics: bool = Field(default=True, description="성능 메트릭 로깅")


class PipelineStage(BaseModel):
    """파이프라인 단계 정의"""

    name: str = Field(..., description="단계 이름")
    stage: ExecutionStage = Field(..., description="실행 단계")
    required: bool = Field(default=True, description="필수 여부")
    timeout_seconds: Optional[int] = Field(None, description="타임아웃")
    retry_on_failure: bool = Field(default=False, description="실패 시 재시도")
    fallback_available: bool = Field(default=False, description="폴백 가능 여부")


class OrchestrationPipeline(BaseModel):
    """오케스트레이션 파이프라인 정의"""

    name: str = Field(..., description="파이프라인 이름")
    strategy: OrchestrationStrategy = Field(..., description="전략")
    stages: List[PipelineStage] = Field(..., description="단계 목록")
    config: OrchestrationConfig = Field(..., description="설정")

    def get_stage(self, stage: ExecutionStage) -> Optional[PipelineStage]:
        """특정 단계 조회"""
        for s in self.stages:
            if s.stage == stage:
                return s
        return None

    def get_required_stages(self) -> List[PipelineStage]:
        """필수 단계 목록"""
        return [s for s in self.stages if s.required]
