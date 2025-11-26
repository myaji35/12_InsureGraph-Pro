"""
Pipeline Orchestrator

파이프라인 실행을 관리하고 모니터링하는 오케스트레이터.
단일 문서 및 배치 처리를 지원합니다.
"""
import logging
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path

from app.workflows.state import (
    PipelineState,
    PipelineResult,
    PipelineStatus,
    WorkflowConfig,
    BatchPipelineState,
    StepResult,
)
from app.workflows.ingestion_workflow import IngestionWorkflow

logger = logging.getLogger(__name__)


class IngestionOrchestrator:
    """데이터 수집 파이프라인 오케스트레이터"""

    def __init__(self, config: Optional[WorkflowConfig] = None):
        """
        오케스트레이터 초기화

        Args:
            config: 워크플로우 설정
        """
        self.config = config or WorkflowConfig()

        # 진행 상황 콜백 함수들
        self.progress_callbacks: List[Callable[[PipelineState], None]] = []

    def add_progress_callback(self, callback: Callable[[PipelineState], None]):
        """
        진행 상황 콜백 추가

        Args:
            callback: 파이프라인 상태를 받는 콜백 함수
        """
        self.progress_callbacks.append(callback)

    async def _notify_progress(self, state: PipelineState):
        """진행 상황을 모든 콜백에 알림"""
        for callback in self.progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(state)
                else:
                    callback(state)
            except Exception as e:
                logger.warning(f"Progress callback 실패: {e}")

    async def process_document(
        self,
        pdf_path: str,
        product_info: Dict[str, Any],
        pipeline_id: Optional[str] = None,
    ) -> PipelineResult:
        """
        단일 문서 처리

        Args:
            pdf_path: PDF 파일 경로
            product_info: 제품 정보 (product_name, company, etc.)
            pipeline_id: 파이프라인 ID (선택사항, 자동 생성됨)

        Returns:
            PipelineResult: 파이프라인 실행 결과

        Example:
            ```python
            orchestrator = IngestionOrchestrator()

            result = await orchestrator.process_document(
                pdf_path="insurance_policy.pdf",
                product_info={
                    "product_name": "무배당 ABC암보험",
                    "company": "ABC생명",
                    "product_type": "암보험"
                }
            )

            if result.is_successful():
                print(f"✅ 성공: {result.graph_stats}")
            else:
                print(f"❌ 실패: {result.errors}")
            ```
        """
        # 파이프라인 ID 생성
        if not pipeline_id:
            pipeline_id = f"pipeline_{uuid.uuid4().hex[:8]}"

        logger.info(f"=== 문서 처리 시작: {pipeline_id} ===")
        logger.info(f"PDF: {pdf_path}")
        logger.info(f"제품: {product_info.get('product_name', 'Unknown')}")

        # 초기 상태 생성
        state = PipelineState(
            pipeline_id=pipeline_id,
            pdf_path=pdf_path,
            product_info=product_info,
            config=self.config.model_dump(),
        )

        # 재시도 로직을 포함한 실행
        final_state = await self._execute_with_retry(state)

        # 결과 변환
        result = self._create_result(final_state)

        logger.info(f"=== 문서 처리 완료: {pipeline_id} ===")
        logger.info(result.get_summary())

        return result

    async def _execute_with_retry(self, state: PipelineState) -> PipelineState:
        """
        재시도 로직을 포함한 워크플로우 실행

        Args:
            state: 초기 파이프라인 상태

        Returns:
            최종 파이프라인 상태
        """
        retry_count = 0
        max_retries = self.config.max_retries

        while retry_count <= max_retries:
            try:
                # 워크플로우 생성 및 실행
                workflow = IngestionWorkflow(self.config)

                # 진행 상황 알림
                await self._notify_progress(state)

                # 실행
                final_state = await workflow.run(state)

                # 리소스 정리
                workflow.cleanup()

                # 성공하면 반환
                if final_state.status == PipelineStatus.COMPLETED:
                    return final_state

                # 실패했지만 재시도 가능하면 계속
                if retry_count < max_retries:
                    retry_count += 1
                    logger.warning(
                        f"파이프라인 실패, 재시도 {retry_count}/{max_retries}"
                    )
                    state.status = PipelineStatus.RETRYING

                    # 재시도 대기
                    await asyncio.sleep(self.config.retry_delay_seconds)
                    continue
                else:
                    # 최대 재시도 횟수 초과
                    logger.error(f"최대 재시도 횟수 초과: {max_retries}")
                    return final_state

            except Exception as e:
                logger.error(f"워크플로우 실행 중 에러: {e}")
                state.status = PipelineStatus.FAILED
                state.errors.append(str(e))

                if retry_count < max_retries:
                    retry_count += 1
                    logger.warning(f"재시도 {retry_count}/{max_retries}")
                    await asyncio.sleep(self.config.retry_delay_seconds)
                    continue
                else:
                    return state

        return state

    def _create_result(self, state: PipelineState) -> PipelineResult:
        """
        파이프라인 상태를 결과로 변환

        Args:
            state: 최종 파이프라인 상태

        Returns:
            PipelineResult
        """
        return PipelineResult(
            pipeline_id=state.pipeline_id,
            status=state.status,
            start_time=state.start_time or datetime.utcnow(),
            end_time=state.end_time or datetime.utcnow(),
            duration_seconds=state.get_total_duration() or 0.0,
            total_steps=len(state.step_results),
            completed_steps=len(state.get_completed_steps()),
            failed_steps=len(state.get_failed_steps()),
            graph_stats=state.graph_stats,
            step_results=state.step_results,
            errors=state.errors,
        )

    async def process_batch(
        self,
        documents: List[Dict[str, Any]],
        max_concurrent: int = 3,
        batch_id: Optional[str] = None,
    ) -> Dict[str, PipelineResult]:
        """
        여러 문서를 배치로 처리

        Args:
            documents: 문서 목록 [{"pdf_path": "...", "product_info": {...}}, ...]
            max_concurrent: 최대 동시 실행 수
            batch_id: 배치 ID (선택사항)

        Returns:
            문서별 처리 결과 딕셔너리

        Example:
            ```python
            documents = [
                {
                    "pdf_path": "policy1.pdf",
                    "product_info": {"product_name": "암보험A"}
                },
                {
                    "pdf_path": "policy2.pdf",
                    "product_info": {"product_name": "암보험B"}
                }
            ]

            results = await orchestrator.process_batch(
                documents=documents,
                max_concurrent=2
            )

            for pdf_path, result in results.items():
                print(f"{pdf_path}: {result.get_summary()}")
            ```
        """
        if not batch_id:
            batch_id = f"batch_{uuid.uuid4().hex[:8]}"

        logger.info(f"=== 배치 처리 시작: {batch_id} ===")
        logger.info(f"총 문서 수: {len(documents)}")
        logger.info(f"동시 실행 수: {max_concurrent}")

        # 배치 상태 생성
        batch_state = BatchPipelineState(
            batch_id=batch_id,
            document_paths=[doc["pdf_path"] for doc in documents],
            total_documents=len(documents),
            start_time=datetime.utcnow(),
        )

        # 세마포어를 사용한 동시 실행 제어
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(doc: Dict[str, Any]) -> tuple:
            """세마포어를 사용하여 문서 처리"""
            async with semaphore:
                result = await self.process_document(
                    pdf_path=doc["pdf_path"],
                    product_info=doc["product_info"],
                )
                return doc["pdf_path"], result

        # 모든 문서를 병렬로 처리
        tasks = [process_with_semaphore(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 정리
        results_dict = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"배치 처리 중 에러: {result}")
                batch_state.failed_documents += 1
            else:
                pdf_path, pipeline_result = result
                results_dict[pdf_path] = pipeline_result

                if pipeline_result.is_successful():
                    batch_state.completed_documents += 1
                else:
                    batch_state.failed_documents += 1

        # 배치 완료
        batch_state.end_time = datetime.utcnow()
        batch_state.status = PipelineStatus.COMPLETED

        logger.info(f"=== 배치 처리 완료: {batch_id} ===")
        logger.info(
            f"성공: {batch_state.completed_documents}, "
            f"실패: {batch_state.failed_documents}, "
            f"전체: {batch_state.total_documents}"
        )

        return results_dict

    async def validate_document(self, pdf_path: str) -> Dict[str, Any]:
        """
        문서 처리 가능 여부 사전 검증

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            검증 결과 딕셔너리

        Example:
            ```python
            validation = await orchestrator.validate_document("policy.pdf")

            if validation["is_valid"]:
                result = await orchestrator.process_document(...)
            else:
                print(f"검증 실패: {validation['errors']}")
            ```
        """
        logger.info(f"문서 검증 시작: {pdf_path}")

        errors = []
        warnings = []

        # 파일 존재 확인
        path = Path(pdf_path)
        if not path.exists():
            errors.append(f"파일이 존재하지 않습니다: {pdf_path}")
        elif not path.is_file():
            errors.append(f"파일이 아닙니다: {pdf_path}")

        # 파일 크기 확인
        if path.exists() and path.stat().st_size == 0:
            errors.append("파일이 비어있습니다")
        elif path.exists() and path.stat().st_size > 100 * 1024 * 1024:  # 100MB
            warnings.append("파일 크기가 매우 큽니다 (>100MB)")

        # 확장자 확인
        if path.suffix.lower() not in ['.pdf', '.txt']:
            warnings.append(f"예상치 못한 파일 확장자: {path.suffix}")

        validation_result = {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "file_size_mb": path.stat().st_size / (1024 * 1024) if path.exists() else 0,
            "file_extension": path.suffix if path.exists() else None,
        }

        if validation_result["is_valid"]:
            logger.info(f"✅ 문서 검증 통과: {pdf_path}")
        else:
            logger.error(f"❌ 문서 검증 실패: {pdf_path}")
            for error in errors:
                logger.error(f"  - {error}")

        return validation_result

    def get_default_product_info(self, pdf_path: str) -> Dict[str, Any]:
        """
        파일명에서 기본 제품 정보 추출

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            기본 제품 정보 딕셔너리

        Example:
            ```python
            # "ABC생명_암보험_v2023.pdf" → {"product_name": "암보험", "company": "ABC생명"}
            product_info = orchestrator.get_default_product_info(pdf_path)
            ```
        """
        path = Path(pdf_path)
        filename = path.stem  # 확장자 제외한 파일명

        # 기본 정보
        product_info = {
            "product_name": filename,
            "company": "Unknown",
            "product_type": "보험",
            "document_id": f"doc_{uuid.uuid4().hex[:8]}",
        }

        # 파일명 파싱 시도 (예: "ABC생명_암보험_v2023.pdf")
        parts = filename.split("_")
        if len(parts) >= 2:
            product_info["company"] = parts[0]
            product_info["product_name"] = parts[1]

        if len(parts) >= 3 and parts[2].startswith("v"):
            product_info["version"] = parts[2]

        return product_info

    def get_statistics(self) -> Dict[str, Any]:
        """
        오케스트레이터 통계 정보

        Returns:
            통계 정보 딕셔너리
        """
        return {
            "config": self.config.model_dump(),
            "progress_callbacks": len(self.progress_callbacks),
        }


# 편의 함수들

async def process_single_document(
    pdf_path: str,
    product_info: Dict[str, Any],
    config: Optional[WorkflowConfig] = None,
) -> PipelineResult:
    """
    단일 문서 처리 편의 함수

    Args:
        pdf_path: PDF 파일 경로
        product_info: 제품 정보
        config: 워크플로우 설정 (선택사항)

    Returns:
        PipelineResult

    Example:
        ```python
        from app.workflows.orchestrator import process_single_document

        result = await process_single_document(
            pdf_path="policy.pdf",
            product_info={"product_name": "암보험", "company": "ABC생명"}
        )
        ```
    """
    orchestrator = IngestionOrchestrator(config)
    return await orchestrator.process_document(pdf_path, product_info)


async def process_directory(
    directory_path: str,
    max_concurrent: int = 3,
    config: Optional[WorkflowConfig] = None,
) -> Dict[str, PipelineResult]:
    """
    디렉토리 내 모든 PDF 파일 처리

    Args:
        directory_path: 디렉토리 경로
        max_concurrent: 최대 동시 실행 수
        config: 워크플로우 설정 (선택사항)

    Returns:
        파일별 처리 결과 딕셔너리

    Example:
        ```python
        from app.workflows.orchestrator import process_directory

        results = await process_directory(
            directory_path="./policies",
            max_concurrent=2
        )
        ```
    """
    orchestrator = IngestionOrchestrator(config)

    # 디렉토리에서 PDF 파일 찾기
    path = Path(directory_path)
    pdf_files = list(path.glob("*.pdf")) + list(path.glob("*.txt"))

    if not pdf_files:
        logger.warning(f"디렉토리에 PDF 파일이 없습니다: {directory_path}")
        return {}

    # 문서 목록 생성
    documents = []
    for pdf_file in pdf_files:
        product_info = orchestrator.get_default_product_info(str(pdf_file))
        documents.append({
            "pdf_path": str(pdf_file),
            "product_info": product_info,
        })

    # 배치 처리
    return await orchestrator.process_batch(
        documents=documents,
        max_concurrent=max_concurrent,
    )
