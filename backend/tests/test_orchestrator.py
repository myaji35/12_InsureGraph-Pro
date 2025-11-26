"""
Unit tests for Pipeline Orchestrator

오케스트레이터의 문서 처리 및 배치 처리 기능을 테스트합니다.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from app.workflows.orchestrator import (
    IngestionOrchestrator,
    process_single_document,
    process_directory,
)
from app.workflows.state import (
    PipelineState,
    PipelineResult,
    PipelineStatus,
    WorkflowConfig,
)


class TestIngestionOrchestrator:
    """Test suite for IngestionOrchestrator"""

    @pytest.fixture
    def config(self):
        """테스트용 워크플로우 설정"""
        return WorkflowConfig(
            max_retries=1,
            retry_delay_seconds=0,
            generate_embeddings=False,
            embedding_provider="mock",
            verbose=False,
        )

    @pytest.fixture
    def orchestrator(self, config):
        """오케스트레이터 인스턴스"""
        return IngestionOrchestrator(config)

    @pytest.fixture
    def sample_product_info(self):
        """샘플 제품 정보"""
        return {
            "product_name": "테스트암보험",
            "company": "테스트생명",
            "product_type": "암보험",
        }

    @pytest.fixture
    def temp_pdf_file(self):
        """임시 PDF 파일 생성"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False, encoding='utf-8') as f:
            f.write("제1조 [보험금의 지급사유]\n")
            f.write("① 회사는 피보험자가 암으로 진단확정된 경우 보험금을 지급합니다.\n")
            temp_path = f.name

        yield temp_path

        # 정리
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_orchestrator_initialization(self, orchestrator, config):
        """오케스트레이터 초기화 테스트"""
        assert orchestrator.config == config
        assert len(orchestrator.progress_callbacks) == 0

    def test_add_progress_callback(self, orchestrator):
        """진행 상황 콜백 추가 테스트"""
        callback = Mock()
        orchestrator.add_progress_callback(callback)

        assert len(orchestrator.progress_callbacks) == 1
        assert orchestrator.progress_callbacks[0] == callback

    @pytest.mark.asyncio
    async def test_notify_progress(self, orchestrator):
        """진행 상황 알림 테스트"""
        callback = Mock()
        orchestrator.add_progress_callback(callback)

        state = PipelineState(
            pipeline_id="test_001",
            status=PipelineStatus.RUNNING,
        )

        await orchestrator._notify_progress(state)

        callback.assert_called_once_with(state)

    @pytest.mark.asyncio
    async def test_process_document(
        self, orchestrator, temp_pdf_file, sample_product_info
    ):
        """단일 문서 처리 테스트"""
        # IngestionWorkflow.run을 mock으로 대체
        with patch('app.workflows.orchestrator.IngestionWorkflow') as mock_workflow_class:
            # Mock 워크플로우 인스턴스
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow

            # Mock 실행 결과
            mock_final_state = PipelineState(
                pipeline_id="test_001",
                status=PipelineStatus.COMPLETED,
                pdf_path=temp_pdf_file,
                product_info=sample_product_info,
            )
            mock_final_state.start_time = mock_final_state.end_time = None
            mock_workflow.run = AsyncMock(return_value=mock_final_state)
            mock_workflow.cleanup = Mock()

            # 실행
            result = await orchestrator.process_document(
                pdf_path=temp_pdf_file,
                product_info=sample_product_info,
            )

            # 검증
            assert isinstance(result, PipelineResult)
            assert result.status == PipelineStatus.COMPLETED
            mock_workflow.run.assert_called_once()
            mock_workflow.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_document_with_retry(
        self, orchestrator, temp_pdf_file, sample_product_info
    ):
        """재시도 로직 테스트"""
        with patch('app.workflows.orchestrator.IngestionWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow

            # 첫 번째 시도는 실패, 두 번째 시도는 성공
            failed_state = PipelineState(
                pipeline_id="test_001",
                status=PipelineStatus.FAILED,
                pdf_path=temp_pdf_file,
                product_info=sample_product_info,
            )
            success_state = PipelineState(
                pipeline_id="test_001",
                status=PipelineStatus.COMPLETED,
                pdf_path=temp_pdf_file,
                product_info=sample_product_info,
            )

            mock_workflow.run = AsyncMock(side_effect=[failed_state, success_state])
            mock_workflow.cleanup = Mock()

            # 실행
            result = await orchestrator.process_document(
                pdf_path=temp_pdf_file,
                product_info=sample_product_info,
            )

            # 검증 - 두 번 실행되었는지 확인
            assert mock_workflow.run.call_count == 2
            assert result.status == PipelineStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_validate_document_success(self, orchestrator, temp_pdf_file):
        """문서 검증 성공 테스트"""
        validation = await orchestrator.validate_document(temp_pdf_file)

        assert validation["is_valid"] is True
        assert len(validation["errors"]) == 0
        assert validation["file_size_mb"] > 0

    @pytest.mark.asyncio
    async def test_validate_document_not_exists(self, orchestrator):
        """존재하지 않는 파일 검증 테스트"""
        validation = await orchestrator.validate_document("nonexistent.pdf")

        assert validation["is_valid"] is False
        assert len(validation["errors"]) > 0
        assert "존재하지 않습니다" in validation["errors"][0]

    def test_get_default_product_info(self, orchestrator):
        """기본 제품 정보 추출 테스트"""
        # 파일명 파싱 테스트
        product_info = orchestrator.get_default_product_info(
            "ABC생명_암보험_v2023.pdf"
        )

        assert product_info["company"] == "ABC생명"
        assert product_info["product_name"] == "암보험"
        assert product_info["version"] == "v2023"

    def test_get_default_product_info_simple(self, orchestrator):
        """단순 파일명 테스트"""
        product_info = orchestrator.get_default_product_info("보험상품.pdf")

        assert product_info["product_name"] == "보험상품"
        assert "document_id" in product_info

    @pytest.mark.asyncio
    async def test_process_batch(
        self, orchestrator, temp_pdf_file, sample_product_info
    ):
        """배치 처리 테스트"""
        with patch('app.workflows.orchestrator.IngestionWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow

            # Mock 성공 상태
            success_state = PipelineState(
                pipeline_id="test_001",
                status=PipelineStatus.COMPLETED,
                pdf_path=temp_pdf_file,
                product_info=sample_product_info,
            )
            mock_workflow.run = AsyncMock(return_value=success_state)
            mock_workflow.cleanup = Mock()

            # 배치 문서 목록
            documents = [
                {
                    "pdf_path": temp_pdf_file,
                    "product_info": sample_product_info,
                },
                {
                    "pdf_path": temp_pdf_file,
                    "product_info": sample_product_info,
                },
            ]

            # 실행
            results = await orchestrator.process_batch(
                documents=documents,
                max_concurrent=2,
            )

            # 검증
            assert len(results) == 2
            assert all(isinstance(r, PipelineResult) for r in results.values())

    def test_get_statistics(self, orchestrator):
        """통계 정보 테스트"""
        stats = orchestrator.get_statistics()

        assert "config" in stats
        assert "progress_callbacks" in stats
        assert stats["progress_callbacks"] == 0

    def test_create_result(self, orchestrator):
        """결과 생성 테스트"""
        from datetime import datetime

        state = PipelineState(
            pipeline_id="test_001",
            status=PipelineStatus.COMPLETED,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
        )

        result = orchestrator._create_result(state)

        assert isinstance(result, PipelineResult)
        assert result.pipeline_id == "test_001"
        assert result.status == PipelineStatus.COMPLETED


class TestConvenienceFunctions:
    """편의 함수 테스트"""

    @pytest.fixture
    def temp_pdf_file(self):
        """임시 PDF 파일"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False, encoding='utf-8') as f:
            f.write("테스트 내용")
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_process_single_document_convenience(self, temp_pdf_file):
        """process_single_document 편의 함수 테스트"""
        with patch('app.workflows.orchestrator.IngestionWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow

            success_state = PipelineState(
                pipeline_id="test_001",
                status=PipelineStatus.COMPLETED,
                pdf_path=temp_pdf_file,
                product_info={},
            )
            mock_workflow.run = AsyncMock(return_value=success_state)
            mock_workflow.cleanup = Mock()

            result = await process_single_document(
                pdf_path=temp_pdf_file,
                product_info={"product_name": "테스트"},
            )

            assert isinstance(result, PipelineResult)

    @pytest.mark.asyncio
    async def test_process_directory_convenience(self, temp_pdf_file):
        """process_directory 편의 함수 테스트"""
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 임시 PDF 파일을 디렉토리에 복사
            import shutil
            dest_path = os.path.join(temp_dir, "test.pdf")
            shutil.copy(temp_pdf_file, dest_path)

            with patch('app.workflows.orchestrator.IngestionWorkflow') as mock_workflow_class:
                mock_workflow = Mock()
                mock_workflow_class.return_value = mock_workflow

                success_state = PipelineState(
                    pipeline_id="test_001",
                    status=PipelineStatus.COMPLETED,
                    pdf_path=dest_path,
                    product_info={},
                )
                mock_workflow.run = AsyncMock(return_value=success_state)
                mock_workflow.cleanup = Mock()

                results = await process_directory(
                    directory_path=temp_dir,
                    max_concurrent=1,
                )

                assert len(results) >= 1


class TestPipelineResult:
    """PipelineResult 모델 테스트"""

    def test_is_successful(self):
        """성공 여부 판단 테스트"""
        from datetime import datetime

        # 성공 케이스
        success_result = PipelineResult(
            pipeline_id="test_001",
            status=PipelineStatus.COMPLETED,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            duration_seconds=10.0,
            total_steps=5,
            completed_steps=5,
            failed_steps=0,
            step_results=[],
        )
        assert success_result.is_successful() is True

        # 실패 케이스
        failed_result = PipelineResult(
            pipeline_id="test_002",
            status=PipelineStatus.FAILED,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            duration_seconds=5.0,
            total_steps=5,
            completed_steps=3,
            failed_steps=2,
            step_results=[],
            errors=["Step 4 failed"],
        )
        assert failed_result.is_successful() is False

    def test_get_summary(self):
        """요약 문자열 생성 테스트"""
        from datetime import datetime

        result = PipelineResult(
            pipeline_id="test_001",
            status=PipelineStatus.COMPLETED,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            duration_seconds=15.5,
            total_steps=5,
            completed_steps=5,
            failed_steps=0,
            step_results=[],
        )

        summary = result.get_summary()
        assert "✅ 성공" in summary
        assert "5/5" in summary
        assert "15.5" in summary
