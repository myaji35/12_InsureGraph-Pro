"""
Document Processing Celery Tasks

문서 처리 백그라운드 작업
"""
import time
from uuid import UUID
from datetime import datetime
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from app.celery_app import celery_app
from app.core.config import settings
from app.core.database import get_pg_pool
from loguru import logger


def _get_db_connection():
    """Get database connection from pool"""
    pool = get_pg_pool()
    return pool.getconn()


def _return_db_connection(conn):
    """Return database connection to pool"""
    pool = get_pg_pool()
    pool.putconn(conn)


def _update_job_progress(
    conn,
    job_id: UUID,
    current_step: str,
    progress_percentage: int,
    steps_completed: list[str],
    status: str = "processing"
):
    """진행 상황 업데이트"""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE processing_jobs
                SET
                    current_step = %s,
                    progress_percentage = %s,
                    steps_completed = %s,
                    status = %s,
                    updated_at = NOW()
                WHERE job_id = %s
                """,
                (current_step, progress_percentage, steps_completed, status, str(job_id))
            )
            conn.commit()
            logger.info(f"Job {job_id} progress updated: {progress_percentage}% - {current_step}")
    except Exception as e:
        logger.error(f"Failed to update job progress: {e}")
        conn.rollback()


def _update_job_error(conn, job_id: UUID, error_message: str):
    """작업 실패 처리"""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE processing_jobs
                SET
                    status = 'failed',
                    error_message = %s,
                    updated_at = NOW(),
                    completed_at = NOW()
                WHERE job_id = %s
                """,
                (error_message, str(job_id))
            )
            conn.commit()
            logger.error(f"Job {job_id} failed: {error_message}")
    except Exception as e:
        logger.error(f"Failed to update job error: {e}")
        conn.rollback()


def _update_job_completed(conn, job_id: UUID):
    """작업 완료 처리"""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE processing_jobs
                SET
                    status = 'completed',
                    progress_percentage = 100,
                    updated_at = NOW(),
                    completed_at = NOW()
                WHERE job_id = %s
                """,
                (str(job_id),)
            )
            conn.commit()
            logger.info(f"Job {job_id} completed successfully")
    except Exception as e:
        logger.error(f"Failed to update job completion: {e}")
        conn.rollback()


def _update_document_status(conn, document_id: UUID, status: str):
    """문서 상태 업데이트"""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE documents
                SET
                    status = %s,
                    updated_at = NOW(),
                    processed_at = CASE WHEN %s = 'completed' THEN NOW() ELSE processed_at END
                WHERE document_id = %s
                """,
                (status, status, str(document_id))
            )
            conn.commit()
            logger.info(f"Document {document_id} status updated to: {status}")
    except Exception as e:
        logger.error(f"Failed to update document status: {e}")
        conn.rollback()


@celery_app.task(bind=True, name="app.tasks.process_document")
def process_document(self, job_id: str, document_id: str, gcs_uri: str):
    """
    문서 처리 백그라운드 작업

    Args:
        job_id: 작업 ID
        document_id: 문서 ID
        gcs_uri: GCS 파일 경로
    """
    conn = None
    try:
        conn = _get_db_connection()
        job_uuid = UUID(job_id)
        doc_uuid = UUID(document_id)

        logger.info(f"Starting document processing job: {job_id} for document: {document_id}")

        # 1단계: OCR (25%)
        _update_job_progress(
            conn, job_uuid, "OCR 진행 중", 5, [], "processing"
        )
        time.sleep(2)  # Simulate OCR processing
        logger.info(f"OCR started for document: {document_id}")

        # OCR 완료
        _update_job_progress(
            conn, job_uuid, "OCR 완료", 25, ["OCR 완료"], "processing"
        )
        time.sleep(1)

        # 2단계: 파싱 (50%)
        _update_job_progress(
            conn, job_uuid, "문서 파싱 중", 30, ["OCR 완료"], "processing"
        )
        time.sleep(2)  # Simulate parsing
        logger.info(f"Parsing started for document: {document_id}")

        # 파싱 완료
        _update_job_progress(
            conn, job_uuid, "파싱 완료", 50, ["OCR 완료", "파싱 완료"], "processing"
        )
        time.sleep(1)

        # 3단계: 임베딩 생성 (75%)
        _update_job_progress(
            conn, job_uuid, "임베딩 생성 중", 55, ["OCR 완료", "파싱 완료"], "processing"
        )
        time.sleep(3)  # Simulate embedding generation
        logger.info(f"Embedding generation started for document: {document_id}")

        # 임베딩 완료
        _update_job_progress(
            conn, job_uuid, "임베딩 완료", 75, ["OCR 완료", "파싱 완료", "임베딩 완료"], "processing"
        )
        time.sleep(1)

        # 4단계: 그래프 생성 (95%)
        _update_job_progress(
            conn, job_uuid, "그래프 생성 중", 80, ["OCR 완료", "파싱 완료", "임베딩 완료"], "processing"
        )
        time.sleep(2)  # Simulate graph creation
        logger.info(f"Graph creation started for document: {document_id}")

        # 그래프 완료
        _update_job_progress(
            conn, job_uuid, "그래프 완료", 95, ["OCR 완료", "파싱 완료", "임베딩 완료", "그래프 완료"], "processing"
        )
        time.sleep(1)

        # 5단계: 최종 처리 (100%)
        _update_job_progress(
            conn, job_uuid, "최종 처리 중", 98, ["OCR 완료", "파싱 완료", "임베딩 완료", "그래프 완료"], "processing"
        )
        time.sleep(1)

        # 작업 완료
        _update_job_completed(conn, job_uuid)
        _update_document_status(conn, doc_uuid, "completed")

        logger.info(f"Document processing completed successfully: {document_id}")

        return {
            "job_id": job_id,
            "document_id": document_id,
            "status": "completed",
            "message": "Document processing completed successfully"
        }

    except Exception as e:
        logger.exception(f"Document processing failed for job {job_id}: {e}")

        if conn:
            _update_job_error(conn, UUID(job_id), str(e))
            _update_document_status(conn, UUID(document_id), "failed")

        raise

    finally:
        if conn:
            _return_db_connection(conn)
