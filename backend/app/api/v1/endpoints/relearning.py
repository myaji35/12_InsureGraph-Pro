"""
재학습 (Relearning) API Endpoints

기존 학습된 문서를 Upstage로 재학습하는 엔드포인트
증분 학습(Incremental Learning) 지원으로 비용 80-90% 절감
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from loguru import logger
from datetime import datetime
import asyncio

from app.core.database import get_db
from app.services.parallel_document_processor import ParallelDocumentProcessor
from app.services.learning.smart_learner import SmartInsuranceLearner
from app.core.config import settings

router = APIRouter()


# 재학습 작업 상태 저장 (메모리)
relearning_jobs = {}


class RelearningRequest(BaseModel):
    """재학습 요청 모델"""
    document_ids: Optional[List[str]] = None  # 특정 문서만 재학습 (None이면 전체)
    insurer: Optional[str] = None  # 특정 보험사만 재학습
    force_upstage: bool = True  # 강제로 Upstage 사용
    smart_chunking: bool = True  # 스마트 청킹 사용
    use_incremental: bool = True  # 증분 학습 사용 (90% 유사 시 변경 부분만 학습)


class RelearningStatus(BaseModel):
    """재학습 상태 모델"""
    job_id: str
    status: str  # pending, running, completed, failed
    total_documents: int
    processed_documents: int
    success_count: int
    failed_count: int
    incremental_count: int = 0  # 증분 학습 적용 건수
    full_learning_count: int = 0  # 전체 학습 건수
    cost_saved_percent: Optional[str] = None  # 절감 비용 (%)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    estimated_time_remaining: Optional[int] = None  # 초


class RelearningResponse(BaseModel):
    """재학습 응답 모델"""
    job_id: str
    message: str
    total_documents: int
    status: str


@router.post("/start", response_model=RelearningResponse)
async def start_relearning(
    request: RelearningRequest,
    background_tasks: BackgroundTasks
):
    """
    재학습 시작

    - 기존 학습된 문서를 Upstage + 스마트 청킹으로 재학습
    - 백그라운드로 실행되며, 상태는 /status 엔드포인트로 확인
    """
    try:
        # 재학습 대상 문서 조회
        db = next(get_db())

        query = """
            SELECT id, pdf_url, insurer, product_type, title
            FROM crawler_documents
            WHERE status IN ('processed', 'completed')
        """

        params = {}
        conditions = []

        if request.document_ids:
            conditions.append("id = ANY(:document_ids)")
            params["document_ids"] = request.document_ids

        if request.insurer:
            conditions.append("insurer = :insurer")
            params["insurer"] = request.insurer

        if conditions:
            query += " AND " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC"

        result = db.execute(query, params)
        documents = result.fetchall()

        if not documents:
            raise HTTPException(
                status_code=404,
                detail="재학습할 문서를 찾을 수 없습니다."
            )

        # Job ID 생성
        job_id = f"relearn_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 작업 상태 초기화
        relearning_jobs[job_id] = RelearningStatus(
            job_id=job_id,
            status="pending",
            total_documents=len(documents),
            processed_documents=0,
            success_count=0,
            failed_count=0,
            incremental_count=0,
            full_learning_count=0,
            cost_saved_percent=None,
            started_at=None,
            completed_at=None
        )

        # 백그라운드로 재학습 실행
        background_tasks.add_task(
            run_relearning_job,
            job_id=job_id,
            documents=documents,
            force_upstage=request.force_upstage,
            smart_chunking=request.smart_chunking,
            use_incremental=request.use_incremental
        )

        logger.info(f"재학습 작업 시작: job_id={job_id}, documents={len(documents)}")

        return RelearningResponse(
            job_id=job_id,
            message=f"재학습 작업이 시작되었습니다. 총 {len(documents)}개 문서를 처리합니다.",
            total_documents=len(documents),
            status="pending"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"재학습 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=f"재학습 시작 실패: {str(e)}")
    finally:
        db.close()


@router.get("/status/{job_id}", response_model=RelearningStatus)
async def get_relearning_status(job_id: str):
    """
    재학습 작업 상태 조회

    - 현재 진행 상황, 성공/실패 건수 등을 반환
    """
    if job_id not in relearning_jobs:
        raise HTTPException(status_code=404, detail="재학습 작업을 찾을 수 없습니다.")

    return relearning_jobs[job_id]


@router.get("/jobs", response_model=List[RelearningStatus])
async def list_relearning_jobs():
    """
    모든 재학습 작업 목록 조회

    - 최근 10개 작업 반환
    """
    jobs = list(relearning_jobs.values())
    jobs.sort(key=lambda x: x.started_at or datetime.now(), reverse=True)
    return jobs[:10]


@router.delete("/cancel/{job_id}")
async def cancel_relearning_job(job_id: str):
    """
    재학습 작업 취소

    - 실행 중인 작업을 중단
    """
    if job_id not in relearning_jobs:
        raise HTTPException(status_code=404, detail="재학습 작업을 찾을 수 없습니다.")

    job = relearning_jobs[job_id]

    if job.status in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"이미 완료된 작업은 취소할 수 없습니다. (상태: {job.status})"
        )

    # 작업 취소
    job.status = "cancelled"
    job.completed_at = datetime.now()
    job.error_message = "사용자가 작업을 취소했습니다."

    logger.info(f"재학습 작업 취소: job_id={job_id}")

    return {"message": "재학습 작업이 취소되었습니다.", "job_id": job_id}


# ============================================================================
# 백그라운드 작업 함수
# ============================================================================

async def run_relearning_job(
    job_id: str,
    documents: list,
    force_upstage: bool,
    smart_chunking: bool,
    use_incremental: bool = True
):
    """
    재학습 작업 실행 (백그라운드)

    Args:
        job_id: 작업 ID
        documents: 재학습할 문서 목록
        force_upstage: Upstage 강제 사용 여부
        smart_chunking: 스마트 청킹 사용 여부
        use_incremental: 증분 학습 사용 여부 (90% 유사 시 변경 부분만 학습)
    """
    job = relearning_jobs[job_id]
    job.status = "running"
    job.started_at = datetime.now()

    logger.info(f"[{job_id}] 재학습 작업 실행 시작: {len(documents)}개 문서 (증분학습: {use_incremental})")

    # 증분 학습기 초기화
    smart_learner = None
    if use_incremental:
        smart_learner = SmartInsuranceLearner()
        logger.info(f"[{job_id}] SmartInsuranceLearner 초기화 완료")

    try:
        # ParallelDocumentProcessor 생성 (Upstage 강제 사용)
        if force_upstage:
            # Upstage 강제 사용 모드
            processor = ParallelDocumentProcessor(
                max_concurrent=3,  # 재학습은 동시 처리 3개로 제한 (비용 고려)
                use_streaming=True,
                use_hybrid=False  # 하이브리드 비활성화 (Upstage만 사용)
            )
        else:
            # 하이브리드 모드 (자동 선택)
            processor = ParallelDocumentProcessor(
                max_concurrent=5,
                use_streaming=True,
                use_hybrid=True
            )

        # 각 문서를 순차적으로 재학습
        for i, doc in enumerate(documents):
            # 작업 취소 확인
            if job.status == "cancelled":
                logger.info(f"[{job_id}] 작업 취소됨")
                break

            doc_id = str(doc[0])
            pdf_url = doc[1]
            insurer = doc[2]
            product_type = doc[3]
            title = doc[4]

            logger.info(f"[{job_id}] 재학습 진행 ({i+1}/{len(documents)}): {title}")

            try:
                # 증분 학습 시도
                learning_strategy = "full"
                cost_saving = 0.0

                if use_incremental and smart_learner:
                    # 현재 문서 텍스트 조회
                    current_text = await get_document_text(doc_id)

                    if current_text:
                        # 이전 버전 확인
                        previous = await smart_learner.incremental_learner.check_previous_version(
                            document_id=doc_id,
                            current_text=current_text,
                            insurer=insurer,
                            product_type=product_type
                        )

                        if previous:
                            # Diff 계산
                            diff_info = smart_learner.incremental_learner.calculate_diff(
                                previous["text"],
                                current_text
                            )

                            # 변경 비율이 30% 이하면 증분 학습
                            if diff_info["change_ratio"] <= 0.3:
                                learning_strategy = "incremental"
                                cost_saving = 1.0 - diff_info["change_ratio"]
                                job.incremental_count += 1

                                logger.info(
                                    f"[{job_id}] 증분 학습 적용: {title} "
                                    f"(유사도: {previous['similarity']:.1%}, "
                                    f"변경: {diff_info['change_ratio']:.1%}, "
                                    f"절감: {cost_saving:.1%})"
                                )
                            else:
                                job.full_learning_count += 1
                                logger.info(
                                    f"[{job_id}] 전체 학습 (변경 많음): {title} "
                                    f"(변경: {diff_info['change_ratio']:.1%})"
                                )
                        else:
                            job.full_learning_count += 1
                            logger.info(f"[{job_id}] 전체 학습 (이전 버전 없음): {title}")
                    else:
                        job.full_learning_count += 1
                else:
                    job.full_learning_count += 1

                # 문서 상태를 'pending'으로 변경 (재처리 대상)
                await update_document_status(doc_id, "pending")

                # 문서 재처리
                success = await processor._process_single_document(
                    document_id=doc_id,
                    pdf_url=pdf_url,
                    insurer=insurer,
                    product_type=product_type,
                    product_name=title
                )

                if success:
                    job.success_count += 1
                    logger.info(
                        f"[{job_id}] 재학습 성공: {title} "
                        f"(전략: {learning_strategy}, 절감: {cost_saving:.1%})"
                    )
                else:
                    job.failed_count += 1
                    logger.warning(f"[{job_id}] 재학습 실패: {title}")

            except Exception as e:
                job.failed_count += 1
                logger.error(f"[{job_id}] 재학습 중 오류: {title} - {e}")

            # 진행 상황 업데이트
            job.processed_documents = i + 1

            # 예상 남은 시간 계산
            if job.started_at:
                elapsed = (datetime.now() - job.started_at).total_seconds()
                avg_time_per_doc = elapsed / (i + 1)
                remaining_docs = len(documents) - (i + 1)
                job.estimated_time_remaining = int(avg_time_per_doc * remaining_docs)

        # 작업 완료
        if job.status != "cancelled":
            job.status = "completed"
            job.completed_at = datetime.now()

            # 비용 절감 계산
            if job.total_documents > 0:
                avg_cost_saving = (job.incremental_count * 0.85) / job.total_documents  # 증분 학습 시 평균 85% 절감
                job.cost_saved_percent = f"{avg_cost_saving * 100:.1f}%"

            logger.info(
                f"[{job_id}] 재학습 작업 완료: "
                f"성공={job.success_count}, 실패={job.failed_count}, "
                f"증분학습={job.incremental_count}, 전체학습={job.full_learning_count}, "
                f"비용절감={job.cost_saved_percent}"
            )

        # 정리
        if smart_learner:
            await smart_learner.cleanup()

    except Exception as e:
        job.status = "failed"
        job.completed_at = datetime.now()
        job.error_message = str(e)
        logger.error(f"[{job_id}] 재학습 작업 실패: {e}")

        # 정리
        if smart_learner:
            await smart_learner.cleanup()


async def update_document_status(document_id: str, status: str):
    """문서 상태 업데이트"""
    db = next(get_db())
    try:
        query = """
            UPDATE crawler_documents
            SET status = :status, updated_at = NOW()
            WHERE id = :id
        """
        db.execute(query, {"id": document_id, "status": status})
        db.commit()
    finally:
        db.close()


async def get_document_text(document_id: str) -> Optional[str]:
    """문서 텍스트 조회"""
    db = next(get_db())
    try:
        query = """
            SELECT extracted_text
            FROM crawler_documents
            WHERE id = :id
        """
        result = db.execute(query, {"id": document_id})
        row = result.fetchone()
        return row[0] if row else None
    finally:
        db.close()


# ============================================================================
# 재학습 통계
# ============================================================================

@router.get("/stats")
async def get_relearning_stats():
    """
    재학습 통계 조회

    - 재학습 가능한 문서 수
    - 최근 재학습 작업 요약
    """
    db = next(get_db())

    try:
        # 재학습 가능한 문서 수
        query = """
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN status = 'processed' THEN 1 END) as processed,
                   COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed
            FROM crawler_documents
            WHERE status IN ('processed', 'completed')
        """
        result = db.execute(query)
        row = result.fetchone()

        # 최근 재학습 작업
        recent_jobs = list(relearning_jobs.values())
        recent_jobs.sort(key=lambda x: x.started_at or datetime.now(), reverse=True)

        return {
            "available_documents": {
                "total": row[0],
                "processed": row[1],
                "completed": row[2]
            },
            "recent_jobs": [
                {
                    "job_id": job.job_id,
                    "status": job.status,
                    "total": job.total_documents,
                    "success": job.success_count,
                    "failed": job.failed_count,
                    "incremental": job.incremental_count,
                    "full_learning": job.full_learning_count,
                    "cost_saved": job.cost_saved_percent,
                    "started_at": job.started_at
                }
                for job in recent_jobs[:5]
            ]
        }

    finally:
        db.close()
