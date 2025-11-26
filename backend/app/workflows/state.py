"""
Pipeline State Models

워크플로우 실행 중 상태를 관리하는 모델들.
각 단계의 입력/출력 데이터를 추적합니다.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class PipelineStatus(str, Enum):
    """파이프라인 실행 상태"""
    PENDING = "pending"           # 대기 중
    RUNNING = "running"           # 실행 중
    COMPLETED = "completed"       # 완료
    FAILED = "failed"             # 실패
    RETRYING = "retrying"         # 재시도 중
    CANCELLED = "cancelled"       # 취소됨


class StepStatus(str, Enum):
    """개별 단계 실행 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepResult(BaseModel):
    """개별 단계 실행 결과"""
    step_name: str = Field(..., description="단계 이름")
    status: StepStatus = Field(..., description="실행 상태")
    start_time: Optional[datetime] = Field(None, description="시작 시간")
    end_time: Optional[datetime] = Field(None, description="종료 시간")
    duration_seconds: Optional[float] = Field(None, description="실행 시간(초)")
    error_message: Optional[str] = Field(None, description="에러 메시지")
    retry_count: int = Field(default=0, description="재시도 횟수")

    # 단계별 출력 데이터
    output: Optional[Dict[str, Any]] = Field(None, description="단계 출력 데이터")


class PipelineState(BaseModel):
    """파이프라인 전체 상태"""

    # 파이프라인 메타데이터
    pipeline_id: str = Field(..., description="파이프라인 고유 ID")
    status: PipelineStatus = Field(default=PipelineStatus.PENDING, description="전체 상태")
    start_time: Optional[datetime] = Field(None, description="시작 시간")
    end_time: Optional[datetime] = Field(None, description="종료 시간")

    # 입력 데이터
    pdf_path: Optional[str] = Field(None, description="PDF 파일 경로")
    product_info: Optional[Dict[str, Any]] = Field(None, description="제품 정보")

    # 중간 결과 데이터 (각 단계의 출력)
    ocr_text: Optional[str] = Field(None, description="OCR 추출 텍스트")
    parsed_document: Optional[Dict[str, Any]] = Field(None, description="파싱된 문서 구조")
    critical_data: Optional[Dict[str, Any]] = Field(None, description="핵심 데이터")
    relations: Optional[List[Dict[str, Any]]] = Field(None, description="추출된 관계")
    entity_links: Optional[Dict[str, Any]] = Field(None, description="엔티티 연결 결과")
    graph_batch: Optional[Dict[str, Any]] = Field(None, description="그래프 배치")
    graph_stats: Optional[Dict[str, Any]] = Field(None, description="그래프 통계")

    # 단계별 결과
    step_results: List[StepResult] = Field(default_factory=list, description="각 단계 실행 결과")

    # 설정
    config: Dict[str, Any] = Field(default_factory=dict, description="파이프라인 설정")

    # 에러 정보
    errors: List[str] = Field(default_factory=list, description="에러 목록")

    def get_current_step(self) -> Optional[str]:
        """현재 실행 중인 단계 이름 반환"""
        for step in self.step_results:
            if step.status == StepStatus.RUNNING:
                return step.step_name
        return None

    def get_completed_steps(self) -> List[str]:
        """완료된 단계 목록 반환"""
        return [step.step_name for step in self.step_results if step.status == StepStatus.COMPLETED]

    def get_failed_steps(self) -> List[str]:
        """실패한 단계 목록 반환"""
        return [step.step_name for step in self.step_results if step.status == StepStatus.FAILED]

    def get_progress_percentage(self) -> float:
        """진행률 계산 (0-100)"""
        if not self.step_results:
            return 0.0

        completed = len([s for s in self.step_results if s.status == StepStatus.COMPLETED])
        total = len(self.step_results)

        return (completed / total) * 100 if total > 0 else 0.0

    def get_total_duration(self) -> Optional[float]:
        """전체 실행 시간 계산(초)"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def add_step_result(self, step_result: StepResult):
        """단계 결과 추가"""
        # 기존 결과가 있으면 업데이트, 없으면 추가
        for i, existing in enumerate(self.step_results):
            if existing.step_name == step_result.step_name:
                self.step_results[i] = step_result
                return
        self.step_results.append(step_result)

    def mark_step_started(self, step_name: str):
        """단계 시작 표시"""
        step_result = StepResult(
            step_name=step_name,
            status=StepStatus.RUNNING,
            start_time=datetime.utcnow(),
        )
        self.add_step_result(step_result)

    def mark_step_completed(self, step_name: str, output: Optional[Dict[str, Any]] = None):
        """단계 완료 표시"""
        for step in self.step_results:
            if step.step_name == step_name:
                step.status = StepStatus.COMPLETED
                step.end_time = datetime.utcnow()
                if step.start_time:
                    step.duration_seconds = (step.end_time - step.start_time).total_seconds()
                if output:
                    step.output = output
                break

    def mark_step_failed(self, step_name: str, error_message: str):
        """단계 실패 표시"""
        for step in self.step_results:
            if step.step_name == step_name:
                step.status = StepStatus.FAILED
                step.end_time = datetime.utcnow()
                if step.start_time:
                    step.duration_seconds = (step.end_time - step.start_time).total_seconds()
                step.error_message = error_message
                break

        # 전체 파이프라인도 실패로 표시
        self.status = PipelineStatus.FAILED
        self.errors.append(f"{step_name}: {error_message}")


class WorkflowConfig(BaseModel):
    """워크플로우 설정"""

    # 재시도 설정
    max_retries: int = Field(default=3, description="최대 재시도 횟수")
    retry_delay_seconds: int = Field(default=5, description="재시도 대기 시간(초)")

    # LLM 설정
    use_cascade: bool = Field(default=True, description="LLM cascade 사용 여부")
    llm_temperature: float = Field(default=0.3, description="LLM temperature")

    # 임베딩 설정
    generate_embeddings: bool = Field(default=True, description="임베딩 생성 여부")
    embedding_provider: str = Field(default="openai", description="임베딩 제공자 (openai/upstage/mock)")

    # 퍼지 매칭 설정
    use_fuzzy_matching: bool = Field(default=True, description="퍼지 매칭 사용 여부")
    fuzzy_threshold: float = Field(default=0.8, description="퍼지 매칭 임계값")

    # Neo4j 설정
    neo4j_uri: Optional[str] = Field(None, description="Neo4j URI")
    neo4j_user: Optional[str] = Field(None, description="Neo4j 사용자")
    neo4j_password: Optional[str] = Field(None, description="Neo4j 비밀번호")

    # 로깅 설정
    verbose: bool = Field(default=True, description="상세 로깅 여부")
    log_level: str = Field(default="INFO", description="로그 레벨")


class PipelineResult(BaseModel):
    """파이프라인 최종 결과"""

    pipeline_id: str = Field(..., description="파이프라인 ID")
    status: PipelineStatus = Field(..., description="최종 상태")

    # 시간 정보
    start_time: datetime = Field(..., description="시작 시간")
    end_time: datetime = Field(..., description="종료 시간")
    duration_seconds: float = Field(..., description="총 실행 시간(초)")

    # 결과 통계
    total_steps: int = Field(..., description="전체 단계 수")
    completed_steps: int = Field(..., description="완료된 단계 수")
    failed_steps: int = Field(..., description="실패한 단계 수")

    # 그래프 통계
    graph_stats: Optional[Dict[str, Any]] = Field(None, description="그래프 생성 통계")

    # 단계별 상세 결과
    step_results: List[StepResult] = Field(..., description="각 단계 실행 결과")

    # 에러 정보
    errors: List[str] = Field(default_factory=list, description="발생한 에러 목록")

    def is_successful(self) -> bool:
        """성공 여부 판단"""
        return self.status == PipelineStatus.COMPLETED and len(self.errors) == 0

    def get_summary(self) -> str:
        """결과 요약 문자열 생성"""
        if self.is_successful():
            return f"✅ 성공: {self.completed_steps}/{self.total_steps} 단계 완료 ({self.duration_seconds:.1f}초)"
        else:
            return f"❌ 실패: {self.failed_steps}개 단계 실패 - {', '.join(self.errors[:3])}"


class BatchPipelineState(BaseModel):
    """여러 문서를 처리하는 배치 파이프라인 상태"""

    batch_id: str = Field(..., description="배치 ID")
    status: PipelineStatus = Field(default=PipelineStatus.PENDING, description="배치 상태")

    # 문서 목록
    document_paths: List[str] = Field(..., description="처리할 문서 경로 목록")

    # 개별 파이프라인 상태
    pipeline_states: Dict[str, PipelineState] = Field(default_factory=dict, description="문서별 파이프라인 상태")

    # 배치 통계
    total_documents: int = Field(..., description="전체 문서 수")
    completed_documents: int = Field(default=0, description="완료된 문서 수")
    failed_documents: int = Field(default=0, description="실패한 문서 수")

    start_time: Optional[datetime] = Field(None, description="배치 시작 시간")
    end_time: Optional[datetime] = Field(None, description="배치 종료 시간")

    def get_progress_percentage(self) -> float:
        """배치 진행률 계산"""
        if self.total_documents == 0:
            return 0.0
        return (self.completed_documents / self.total_documents) * 100

    def add_pipeline_result(self, pipeline_id: str, result: PipelineResult):
        """파이프라인 결과 추가"""
        if result.is_successful():
            self.completed_documents += 1
        else:
            self.failed_documents += 1

    def is_complete(self) -> bool:
        """배치 완료 여부"""
        return (self.completed_documents + self.failed_documents) == self.total_documents
