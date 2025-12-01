"""
Policy Ingestion API Endpoints

Handles PDF uploads and job status tracking.
"""
from typing import Annotated
from uuid import UUID
import tempfile
import os
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from app.models.user import User, UserRole
from app.models.ingestion_job import (
    IngestionJobCreate,
    IngestionJobResponse,
    IngestionJobUpdate,
    IngestionJobStatus,
)
from app.services.storage import get_storage_service, S3StorageService
from app.repositories.ingestion_job_repository import IngestionJobRepository
from app.core.database import PostgreSQLManager
from app.api.v1.endpoints.auth import get_current_user
from app.workflows.mvp_ingestion_workflow import get_mvp_workflow, MVPPipelineStatus
from app.repositories.document_repository import get_document_repository


router = APIRouter(prefix="/policies", tags=["Policy Ingestion"])

# Dependency injection
def get_db_manager() -> PostgreSQLManager:
    """Get PostgreSQL manager (singleton)"""
    from app.core.database import pg_manager
    return pg_manager


def get_ingestion_repo(db_manager: PostgreSQLManager = Depends(get_db_manager)) -> IngestionJobRepository:
    """Get ingestion job repository"""
    return IngestionJobRepository(db_manager)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require ADMIN or FP_MANAGER role"""
    if current_user.role not in [UserRole.ADMIN, UserRole.FP_MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can upload policies"
        )
    return current_user


# Constants
MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
PDF_MAGIC_BYTES = b'%PDF-'


@router.post(
    "/ingest",
    response_model=IngestionJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload policy PDF and create ingestion job",
    description="Upload an insurance policy PDF file with metadata. Creates an ingestion job and stores the file in S3.",
)
async def upload_policy(
    file: Annotated[UploadFile, File(description="PDF file (max 100MB)")],
    insurer: Annotated[str, Form(description="Insurance company name")],
    product_name: Annotated[str, Form(description="Product/policy name")],
    launch_date: Annotated[str | None, Form(description="Product launch date (ISO 8601)")] = None,
    current_user: User = Depends(require_admin),
    storage_service: S3StorageService = Depends(get_storage_service),
    repo: IngestionJobRepository = Depends(get_ingestion_repo),
) -> IngestionJobResponse:
    """
    Upload policy PDF and create ingestion job.

    **Authorization**: Requires ADMIN or FP_MANAGER role.

    **Request**:
    - multipart/form-data with PDF file and metadata

    **Response**:
    - 202 Accepted with job_id and status

    **Errors**:
    - 400: Invalid file (not PDF, too large, etc.)
    - 401: Unauthorized
    - 403: Forbidden (not admin)
    - 500: Internal server error
    """
    try:
        # Validation 1: Check file type from filename
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a PDF (invalid extension)"
            )

        # Validation 2: Check file size
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum {MAX_FILE_SIZE_MB}MB (got {file_size / 1024 / 1024:.2f}MB)"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

        # Validation 3: Check PDF magic bytes
        if not file_content.startswith(PDF_MAGIC_BYTES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is not a valid PDF (invalid magic bytes)"
            )

        # Reset file pointer and reattach content
        await file.seek(0)

        # Upload to S3/GCS
        logger.info(f"Uploading PDF: {file.filename} ({file_size} bytes) for {insurer}/{product_name}")

        s3_key = await storage_service.upload_pdf(
            file=file,
            policy_name=product_name,
            insurer=insurer,
        )

        # Create ingestion job in database
        # If this fails, cleanup the uploaded file to prevent orphaned files
        try:
            job_data = IngestionJobCreate(
                policy_name=product_name,
                insurer=insurer,
                launch_date=launch_date,
                s3_key=s3_key,
            )

            job = repo.create(job_data)

            logger.info(f"Created ingestion job {job.job_id} for policy {product_name}")

        except Exception as db_error:
            # Database operation failed - cleanup uploaded file
            logger.error(f"Database operation failed, cleaning up uploaded file {s3_key}: {db_error}")
            try:
                await storage_service.delete_file(s3_key)
                logger.info(f"Successfully cleaned up orphaned file: {s3_key}")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup orphaned file {s3_key}: {cleanup_error}")

            # Re-raise the original database error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create job record: {str(db_error)}"
            )

        # Return 202 Accepted with job info
        return IngestionJobResponse(
            job_id=job.job_id,
            status=job.status,
            policy_name=job.policy_name,
            insurer=job.insurer,
            progress=job.progress,
            results=job.results,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
            estimated_completion_minutes=5,  # Estimated time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload policy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get(
    "/ingest/status/{job_id}",
    response_model=IngestionJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ingestion job status",
    description="Query the status and progress of an ingestion job.",
)
async def get_job_status(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    repo: IngestionJobRepository = Depends(get_ingestion_repo),
) -> IngestionJobResponse:
    """
    Get ingestion job status and progress.

    **Authorization**: Requires authentication.

    **Response**:
    - Current job status (pending, processing, completed, failed)
    - Progress percentage (0-100)
    - Detailed results if completed
    - Error message if failed

    **Errors**:
    - 404: Job not found
    - 401: Unauthorized
    """
    job = repo.get_by_job_id(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    return IngestionJobResponse(
        job_id=job.job_id,
        status=job.status,
        policy_name=job.policy_name,
        insurer=job.insurer,
        progress=job.progress,
        results=job.results,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        estimated_completion_minutes=None if job.status != IngestionJobStatus.PENDING else 5,
    )


@router.get(
    "/ingest/jobs",
    response_model=list[IngestionJobResponse],
    status_code=status.HTTP_200_OK,
    summary="List all ingestion jobs",
    description="Get a list of all ingestion jobs with optional filtering.",
)
async def list_jobs(
    status_filter: IngestionJobStatus | None = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    repo: IngestionJobRepository = Depends(get_ingestion_repo),
) -> list[IngestionJobResponse]:
    """
    List all ingestion jobs with pagination and optional status filtering.

    **Authorization**: Requires authentication.

    **Query Parameters**:
    - status_filter: Filter by job status (pending, processing, completed, failed)
    - limit: Maximum number of jobs to return (default: 50, max: 100)
    - offset: Number of jobs to skip (default: 0)

    **Response**:
    - List of ingestion jobs ordered by created_at (newest first)

    **Errors**:
    - 401: Unauthorized
    """
    # Validate limit
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 1

    jobs = repo.list_jobs(
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    return [
        IngestionJobResponse(
            job_id=job.job_id,
            status=job.status,
            policy_name=job.policy_name,
            insurer=job.insurer,
            progress=job.progress,
            results=job.results,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
            estimated_completion_minutes=None if job.status != IngestionJobStatus.PENDING else 5,
        )
        for job in jobs
    ]

# ============================================================================
# MVP Ingestion Endpoint
# ============================================================================

from pydantic import BaseModel

class MVPIngestResponse(BaseModel):
    """Response for MVP ingestion"""
    success: bool
    message: str
    document_id: str | None = None
    policy_name: str
    insurer: str
    duration_seconds: float
    metrics: dict


@router.post(
    "/ingest-mvp",
    response_model=MVPIngestResponse,
    status_code=status.HTTP_200_OK,
    summary="[MVP] Upload and immediately process PDF",
    description="MVP endpoint that uploads PDF and immediately processes it through the pipeline. No S3, no Celery, immediate results.",
)
async def upload_policy_mvp(
    file: Annotated[UploadFile, File(description="PDF file (max 100MB)")],
    insurer: Annotated[str, Form(description="Insurance company name")],
    product_name: Annotated[str, Form(description="Product/policy name")],
) -> MVPIngestResponse:
    """
    MVP ingestion endpoint - immediate processing without S3 or Celery.

    **Flow**:
    1. Upload PDF to temporary file
    2. Run MVP workflow (extract → parse → save to PostgreSQL)
    3. Return result immediately

    **No authentication required for MVP**
    """
    temp_path = None
    
    try:
        # Validation 1: Check file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a PDF"
            )

        # Validation 2: Check file size
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds {MAX_FILE_SIZE_MB}MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

        # Validation 3: Check PDF magic bytes
        if not file_content.startswith(PDF_MAGIC_BYTES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is not a valid PDF"
            )

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as tmp:
            tmp.write(file_content)
            temp_path = tmp.name

        logger.info(f"Processing PDF (MVP): {file.filename} ({file_size} bytes) for {insurer}/{product_name}")

        # Run MVP workflow
        workflow = get_mvp_workflow()
        result = await workflow.run(
            pdf_path=temp_path,
            policy_name=product_name,
            insurer=insurer,
        )

        # Check result
        if result.status == MVPPipelineStatus.FAILED:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Pipeline failed: {result.error}"
            )

        logger.info(f"MVP pipeline completed: {result.document_id} in {result.duration_seconds:.2f}s")

        return MVPIngestResponse(
            success=True,
            message="Document processed successfully",
            document_id=str(result.document_id) if result.document_id else None,
            policy_name=product_name,
            insurer=insurer,
            duration_seconds=result.duration_seconds,
            metrics={
                "total_pages": result.total_pages,
                "total_chars": result.total_chars,
                "total_articles": result.total_articles,
                "total_paragraphs": result.total_paragraphs,
                "total_subclauses": result.total_subclauses,
                "total_amounts": result.total_amounts,
                "total_periods": result.total_periods,
                "total_kcd_codes": result.total_kcd_codes,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MVP ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )
    finally:
        # Cleanup temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.debug(f"Cleaned up temp file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_path}: {e}")
