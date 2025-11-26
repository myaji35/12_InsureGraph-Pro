"""
Unit tests for Workflow State Models

파이프라인 상태 모델의 기능을 테스트합니다.
"""
import pytest
from datetime import datetime, timedelta

from app.workflows.state import (
    PipelineState,
    PipelineStatus,
    PipelineResult,
    StepResult,
    StepStatus,
    WorkflowConfig,
    BatchPipelineState,
)


class TestPipelineState:
    """Test suite for PipelineState"""

    @pytest.fixture
    def pipeline_state(self):
        """기본 파이프라인 상태"""
        return PipelineState(
            pipeline_id="test_pipeline_001",
            status=PipelineStatus.PENDING,
        )

    def test_pipeline_state_initialization(self, pipeline_state):
        """파이프라인 상태 초기화 테스트"""
        assert pipeline_state.pipeline_id == "test_pipeline_001"
        assert pipeline_state.status == PipelineStatus.PENDING
        assert len(pipeline_state.step_results) == 0
        assert len(pipeline_state.errors) == 0

    def test_mark_step_started(self, pipeline_state):
        """단계 시작 표시 테스트"""
        pipeline_state.mark_step_started("extract_ocr")

        assert len(pipeline_state.step_results) == 1
        step = pipeline_state.step_results[0]
        assert step.step_name == "extract_ocr"
        assert step.status == StepStatus.RUNNING
        assert step.start_time is not None

    def test_mark_step_completed(self, pipeline_state):
        """단계 완료 표시 테스트"""
        pipeline_state.mark_step_started("extract_ocr")
        pipeline_state.mark_step_completed(
            "extract_ocr",
            output={"text_length": 1000}
        )

        step = pipeline_state.step_results[0]
        assert step.status == StepStatus.COMPLETED
        assert step.end_time is not None
        assert step.duration_seconds is not None
        assert step.output["text_length"] == 1000

    def test_mark_step_failed(self, pipeline_state):
        """단계 실패 표시 테스트"""
        pipeline_state.mark_step_started("extract_ocr")
        pipeline_state.mark_step_failed("extract_ocr", "File not found")

        step = pipeline_state.step_results[0]
        assert step.status == StepStatus.FAILED
        assert step.error_message == "File not found"
        assert pipeline_state.status == PipelineStatus.FAILED
        assert "File not found" in pipeline_state.errors[0]

    def test_get_current_step(self, pipeline_state):
        """현재 실행 중인 단계 가져오기 테스트"""
        # 초기에는 None
        assert pipeline_state.get_current_step() is None

        # 단계 시작
        pipeline_state.mark_step_started("parse_structure")
        assert pipeline_state.get_current_step() == "parse_structure"

        # 단계 완료
        pipeline_state.mark_step_completed("parse_structure")
        assert pipeline_state.get_current_step() is None

    def test_get_completed_steps(self, pipeline_state):
        """완료된 단계 목록 테스트"""
        pipeline_state.mark_step_started("step1")
        pipeline_state.mark_step_completed("step1")
        pipeline_state.mark_step_started("step2")
        pipeline_state.mark_step_completed("step2")
        pipeline_state.mark_step_started("step3")

        completed = pipeline_state.get_completed_steps()
        assert len(completed) == 2
        assert "step1" in completed
        assert "step2" in completed
        assert "step3" not in completed

    def test_get_failed_steps(self, pipeline_state):
        """실패한 단계 목록 테스트"""
        pipeline_state.mark_step_started("step1")
        pipeline_state.mark_step_completed("step1")
        pipeline_state.mark_step_started("step2")
        pipeline_state.mark_step_failed("step2", "Error")
        pipeline_state.mark_step_started("step3")
        pipeline_state.mark_step_failed("step3", "Error")

        failed = pipeline_state.get_failed_steps()
        assert len(failed) == 2
        assert "step2" in failed
        assert "step3" in failed

    def test_get_progress_percentage(self, pipeline_state):
        """진행률 계산 테스트"""
        # 단계가 없을 때
        assert pipeline_state.get_progress_percentage() == 0.0

        # 5개 단계 중 3개 완료
        for i in range(5):
            pipeline_state.mark_step_started(f"step{i}")

        for i in range(3):
            pipeline_state.mark_step_completed(f"step{i}")

        progress = pipeline_state.get_progress_percentage()
        assert progress == 60.0  # 3/5 * 100

    def test_get_total_duration(self, pipeline_state):
        """전체 실행 시간 계산 테스트"""
        # 시간이 설정되지 않으면 None
        assert pipeline_state.get_total_duration() is None

        # 시간 설정
        start = datetime.utcnow()
        end = start + timedelta(seconds=10)
        pipeline_state.start_time = start
        pipeline_state.end_time = end

        duration = pipeline_state.get_total_duration()
        assert duration == pytest.approx(10.0, rel=0.1)

    def test_add_step_result(self, pipeline_state):
        """단계 결과 추가 테스트"""
        step1 = StepResult(
            step_name="test_step",
            status=StepStatus.RUNNING,
        )
        pipeline_state.add_step_result(step1)

        assert len(pipeline_state.step_results) == 1

        # 같은 이름의 단계는 업데이트됨
        step2 = StepResult(
            step_name="test_step",
            status=StepStatus.COMPLETED,
        )
        pipeline_state.add_step_result(step2)

        assert len(pipeline_state.step_results) == 1
        assert pipeline_state.step_results[0].status == StepStatus.COMPLETED


class TestStepResult:
    """Test suite for StepResult"""

    def test_step_result_initialization(self):
        """단계 결과 초기화 테스트"""
        step = StepResult(
            step_name="extract_ocr",
            status=StepStatus.RUNNING,
        )

        assert step.step_name == "extract_ocr"
        assert step.status == StepStatus.RUNNING
        assert step.retry_count == 0

    def test_step_result_with_output(self):
        """출력 데이터를 포함한 단계 결과 테스트"""
        step = StepResult(
            step_name="parse_structure",
            status=StepStatus.COMPLETED,
            output={
                "total_articles": 50,
                "total_paragraphs": 200,
            }
        )

        assert step.output["total_articles"] == 50
        assert step.output["total_paragraphs"] == 200

    def test_step_result_with_error(self):
        """에러 정보를 포함한 단계 결과 테스트"""
        step = StepResult(
            step_name="build_graph",
            status=StepStatus.FAILED,
            error_message="Connection refused",
        )

        assert step.status == StepStatus.FAILED
        assert step.error_message == "Connection refused"


class TestWorkflowConfig:
    """Test suite for WorkflowConfig"""

    def test_default_config(self):
        """기본 설정 테스트"""
        config = WorkflowConfig()

        assert config.max_retries == 3
        assert config.retry_delay_seconds == 5
        assert config.use_cascade is True
        assert config.generate_embeddings is True
        assert config.embedding_provider == "openai"
        assert config.use_fuzzy_matching is True
        assert config.fuzzy_threshold == 0.8

    def test_custom_config(self):
        """커스텀 설정 테스트"""
        config = WorkflowConfig(
            max_retries=5,
            retry_delay_seconds=10,
            embedding_provider="upstage",
            generate_embeddings=False,
        )

        assert config.max_retries == 5
        assert config.retry_delay_seconds == 10
        assert config.embedding_provider == "upstage"
        assert config.generate_embeddings is False


class TestBatchPipelineState:
    """Test suite for BatchPipelineState"""

    @pytest.fixture
    def batch_state(self):
        """배치 파이프라인 상태"""
        return BatchPipelineState(
            batch_id="batch_001",
            document_paths=["doc1.pdf", "doc2.pdf", "doc3.pdf"],
            total_documents=3,
        )

    def test_batch_initialization(self, batch_state):
        """배치 상태 초기화 테스트"""
        assert batch_state.batch_id == "batch_001"
        assert batch_state.total_documents == 3
        assert batch_state.completed_documents == 0
        assert batch_state.failed_documents == 0

    def test_get_progress_percentage(self, batch_state):
        """배치 진행률 계산 테스트"""
        # 초기 0%
        assert batch_state.get_progress_percentage() == 0.0

        # 1개 완료
        batch_state.completed_documents = 1
        assert batch_state.get_progress_percentage() == pytest.approx(33.33, rel=0.1)

        # 2개 완료
        batch_state.completed_documents = 2
        assert batch_state.get_progress_percentage() == pytest.approx(66.67, rel=0.1)

        # 모두 완료
        batch_state.completed_documents = 3
        assert batch_state.get_progress_percentage() == 100.0

    def test_add_pipeline_result(self, batch_state):
        """파이프라인 결과 추가 테스트"""
        # 성공 결과
        success_result = PipelineResult(
            pipeline_id="pipe_001",
            status=PipelineStatus.COMPLETED,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            duration_seconds=10.0,
            total_steps=5,
            completed_steps=5,
            failed_steps=0,
            step_results=[],
        )

        batch_state.add_pipeline_result("pipe_001", success_result)
        assert batch_state.completed_documents == 1
        assert batch_state.failed_documents == 0

        # 실패 결과
        failed_result = PipelineResult(
            pipeline_id="pipe_002",
            status=PipelineStatus.FAILED,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            duration_seconds=5.0,
            total_steps=5,
            completed_steps=2,
            failed_steps=3,
            step_results=[],
            errors=["Step failed"],
        )

        batch_state.add_pipeline_result("pipe_002", failed_result)
        assert batch_state.completed_documents == 1
        assert batch_state.failed_documents == 1

    def test_is_complete(self, batch_state):
        """배치 완료 여부 테스트"""
        assert batch_state.is_complete() is False

        batch_state.completed_documents = 2
        batch_state.failed_documents = 1
        assert batch_state.is_complete() is True


class TestPipelineStatus:
    """Test suite for PipelineStatus enum"""

    def test_status_values(self):
        """상태 값 테스트"""
        assert PipelineStatus.PENDING.value == "pending"
        assert PipelineStatus.RUNNING.value == "running"
        assert PipelineStatus.COMPLETED.value == "completed"
        assert PipelineStatus.FAILED.value == "failed"
        assert PipelineStatus.RETRYING.value == "retrying"
        assert PipelineStatus.CANCELLED.value == "cancelled"


class TestStepStatus:
    """Test suite for StepStatus enum"""

    def test_status_values(self):
        """상태 값 테스트"""
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.RUNNING.value == "running"
        assert StepStatus.COMPLETED.value == "completed"
        assert StepStatus.FAILED.value == "failed"
        assert StepStatus.SKIPPED.value == "skipped"
