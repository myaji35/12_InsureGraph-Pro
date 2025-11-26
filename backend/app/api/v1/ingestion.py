"""
API endpoints for policy document ingestion
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.security import get_current_user, require_role
from app.core.database import get_pg_connection
from app.schemas.ingestion import (
    PolicyUploadRequest,
    PolicyUploadResponse,
    JobStatusResponse,
    JobListResponse,
    JobStatus,
    ErrorResponse
)
from app.services.ingestion.storage import gcs_service
from app.services.ingestion.job_manager import JobManager


router = APIRouter()


@router.post(
    "/ingest",
    response_model=PolicyUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload policy PDF for ingestion",
    description="""
    Upload a policy PDF document to start the ingestion pipeline.

    The file will be:
    1. Uploaded to Google Cloud Storage
    2. Queued for OCR processing
    3. Parsed and extracted
    4. Converted to knowledge graph in Neo4j

    Returns a job_id for tracking progress.
    """,
    responses={
        201: {"description": "PDF uploaded successfully"},
        400: {"model": ErrorResponse, "description": "Invalid file or parameters"},
        401: {"description": "Unauthorized"},
        413: {"description": "File too large (max 50MB)"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def upload_policy(
    file: UploadFile = File(..., description="PDF file to upload (max 50MB)"),
    insurer: str = Form(..., description="Insurance company name"),
    product_name: str = Form(..., description="Product name"),
    product_code: Optional[str] = Form(None, description="Product code"),
    launch_date: Optional[str] = Form(None, description="Launch date (YYYY-MM-DD)"),
    description: Optional[str] = Form(None, description="Additional description"),
    current_user: dict = Depends(get_current_user),
    db_conn = Depends(get_pg_connection)
):
    """Upload a policy PDF and create an ingestion job"""

    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )

    # Validate file size (max 50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
    file_content = await file.read()
    file_size_bytes = len(file_content)

    if file_size_bytes > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is 50MB, got {file_size_bytes / (1024*1024):.2f}MB"
        )

    # Reset file pointer for upload
    await file.seek(0)

    try:
        # Create request object
        upload_request = PolicyUploadRequest(
            insurer=insurer,
            product_name=product_name,
            product_code=product_code,
            launch_date=launch_date,
            description=description
        )

        # Initialize job manager
        job_manager = JobManager(db_conn)

        # Generate job ID first (for GCS path)
        from uuid import uuid4
        job_id = uuid4()

        # Upload to GCS
        blob_name, gcs_uri = gcs_service.upload_policy_pdf(
            file=file.file,
            job_id=job_id,
            filename=file.filename,
            content_type=file.content_type
        )

        # Create job in database
        user_id = UUID(current_user["sub"])
        created_job_id = job_manager.create_job(
            user_id=user_id,
            request=upload_request,
            gcs_uri=gcs_uri,
            blob_name=blob_name,
            file_size_bytes=file_size_bytes,
            filename=file.filename
        )

        # Note: In production, trigger async OCR processing here
        # await ocr_queue.enqueue(job_id)

        return PolicyUploadResponse(
            job_id=created_job_id,
            status=JobStatus.UPLOADED,
            message="PDF uploaded successfully. Processing will begin shortly.",
            gcs_uri=gcs_uri,
            created_at=job_manager.get_job_status(created_job_id).created_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload policy: {str(e)}"
        )


@router.get(
    "/ingest/{job_id}/status",
    response_model=JobStatusResponse,
    summary="Get ingestion job status",
    description="""
    Retrieve the current status of an ingestion job including:
    - Overall job status
    - Individual pipeline stage statuses
    - Progress percentage
    - Error messages if any
    """,
    responses={
        200: {"description": "Job status retrieved successfully"},
        404: {"description": "Job not found"},
        401: {"description": "Unauthorized"}
    }
)
async def get_job_status(
    job_id: UUID,
    current_user: dict = Depends(get_current_user),
    db_conn = Depends(get_pg_connection)
):
    """Get the status of an ingestion job"""

    job_manager = JobManager(db_conn)
    job_status = job_manager.get_job_status(job_id)

    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    return job_status


@router.get(
    "/ingest",
    response_model=JobListResponse,
    summary="List ingestion jobs",
    description="""
    List all ingestion jobs with optional filters:
    - Filter by status (pending, processing, completed, failed)
    - Pagination support

    Admin users can see all jobs, FPs see only their own jobs.
    """,
    responses={
        200: {"description": "Jobs retrieved successfully"},
        401: {"description": "Unauthorized"}
    }
)
async def list_jobs(
    status_filter: Optional[JobStatus] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db_conn = Depends(get_pg_connection)
):
    """List ingestion jobs with pagination"""

    # Validate pagination
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be >= 1"
        )
    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 100"
        )

    job_manager = JobManager(db_conn)

    # If user is not admin, filter by their user_id
    user_id = None
    if current_user.get("role") not in ["admin", "fp_manager"]:
        user_id = UUID(current_user["sub"])

    offset = (page - 1) * page_size
    jobs = job_manager.list_jobs(
        user_id=user_id,
        status=status_filter,
        limit=page_size,
        offset=offset
    )

    # Get total count (simplified - in production, use a COUNT query)
    total = len(jobs)

    return JobListResponse(
        jobs=jobs,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete(
    "/ingest/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an ingestion job",
    description="""
    Delete an ingestion job and its associated GCS file.
    Only admins or the job owner can delete jobs.
    """,
    responses={
        204: {"description": "Job deleted successfully"},
        404: {"description": "Job not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - not job owner"}
    },
    dependencies=[Depends(require_role(["admin", "fp_manager"]))]
)
async def delete_job(
    job_id: UUID,
    current_user: dict = Depends(get_current_user),
    db_conn = Depends(get_pg_connection)
):
    """Delete an ingestion job and its GCS file"""

    job_manager = JobManager(db_conn)
    job_status = job_manager.get_job_status(job_id)

    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    # Get blob name from database
    with db_conn.cursor() as cur:
        cur.execute("SELECT blob_name FROM ingestion_jobs WHERE id = %s", (job_id,))
        result = cur.fetchone()
        blob_name = result[0] if result else None

    try:
        # Delete from GCS
        if blob_name:
            gcs_service.delete_policy_pdf(blob_name)

        # Delete from database
        with db_conn.cursor() as cur:
            # Delete stages first (foreign key constraint)
            cur.execute("DELETE FROM ingestion_job_stages WHERE job_id = %s", (job_id,))
            # Delete job
            cur.execute("DELETE FROM ingestion_jobs WHERE id = %s", (job_id,))
            db_conn.commit()

        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job: {str(e)}"
        )
