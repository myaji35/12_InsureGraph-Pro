"""
Ingestion job management service
"""
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import json

import psycopg2
from psycopg2.extras import RealDictCursor

from app.schemas.ingestion import (
    JobStatus,
    JobStageType,
    JobStageStatus,
    JobStatusResponse,
    PolicyUploadRequest
)


class JobManager:
    """Service for managing ingestion jobs and their stages"""

    def __init__(self, db_connection):
        """
        Initialize job manager

        Args:
            db_connection: PostgreSQL connection object
        """
        self.conn = db_connection

    def create_job(
        self,
        user_id: UUID,
        request: PolicyUploadRequest,
        gcs_uri: str,
        blob_name: str,
        file_size_bytes: int,
        filename: str
    ) -> UUID:
        """
        Create a new ingestion job

        Args:
            user_id: User who initiated the job
            request: Policy upload request data
            gcs_uri: GCS URI of uploaded file
            blob_name: Blob name in GCS
            file_size_bytes: File size in bytes
            filename: Original filename

        Returns:
            Job ID (UUID)
        """
        job_id = uuid4()

        with self.conn.cursor() as cur:
            # Insert into ingestion_jobs table
            cur.execute(
                """
                INSERT INTO ingestion_jobs (
                    id, user_id, insurer, product_name, product_code,
                    launch_date, description, gcs_uri, blob_name,
                    file_size_bytes, original_filename, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    job_id,
                    user_id,
                    request.insurer,
                    request.product_name,
                    request.product_code,
                    request.launch_date,
                    request.description,
                    gcs_uri,
                    blob_name,
                    file_size_bytes,
                    filename,
                    JobStatus.UPLOADED.value
                )
            )

            # Create initial upload stage
            self._create_stage(
                cur,
                job_id,
                JobStageType.UPLOAD,
                JobStatus.COMPLETED,
                metadata={"file_size_mb": round(file_size_bytes / (1024 * 1024), 2)}
            )

            self.conn.commit()

        return job_id

    def _create_stage(
        self,
        cursor,
        job_id: UUID,
        stage: JobStageType,
        status: JobStatus,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Create a job stage record

        Args:
            cursor: Database cursor
            job_id: Job ID
            stage: Stage type
            status: Stage status
            error_message: Optional error message
            metadata: Optional metadata dictionary
        """
        stage_id = uuid4()
        started_at = datetime.utcnow() if status != JobStatus.PENDING else None
        completed_at = datetime.utcnow() if status in [JobStatus.COMPLETED, JobStatus.FAILED] else None

        cursor.execute(
            """
            INSERT INTO ingestion_job_stages (
                id, job_id, stage, status, started_at, completed_at,
                error_message, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                stage_id,
                job_id,
                stage.value,
                status.value,
                started_at,
                completed_at,
                error_message,
                json.dumps(metadata) if metadata else None
            )
        )

    def update_job_status(self, job_id: UUID, status: JobStatus, error_message: Optional[str] = None):
        """
        Update overall job status

        Args:
            job_id: Job ID
            status: New status
            error_message: Optional error message
        """
        with self.conn.cursor() as cur:
            completed_at = datetime.utcnow() if status in [JobStatus.COMPLETED, JobStatus.FAILED] else None

            cur.execute(
                """
                UPDATE ingestion_jobs
                SET status = %s, error_message = %s, completed_at = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (status.value, error_message, completed_at, job_id)
            )
            self.conn.commit()

    def create_stage(
        self,
        job_id: UUID,
        stage: JobStageType,
        status: JobStatus = JobStatus.PENDING,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Create a new stage for a job (public method)

        Args:
            job_id: Job ID
            stage: Stage type
            status: Initial status (default: PENDING)
            metadata: Optional metadata
        """
        with self.conn.cursor() as cur:
            self._create_stage(cur, job_id, stage, status, metadata=metadata)
            self.conn.commit()

    def update_stage_status(
        self,
        job_id: UUID,
        stage: JobStageType,
        status: JobStatus,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Update a stage status

        Args:
            job_id: Job ID
            stage: Stage type
            status: New status
            error_message: Optional error message
            metadata: Optional metadata to merge
        """
        with self.conn.cursor() as cur:
            # Determine timestamps
            started_at = datetime.utcnow() if status == JobStatus.PROCESSING else None
            completed_at = datetime.utcnow() if status in [JobStatus.COMPLETED, JobStatus.FAILED] else None

            # Update stage
            cur.execute(
                """
                UPDATE ingestion_job_stages
                SET status = %s,
                    started_at = COALESCE(started_at, %s),
                    completed_at = %s,
                    error_message = %s,
                    metadata = COALESCE(metadata::jsonb || %s::jsonb, metadata, %s::jsonb)
                WHERE job_id = %s AND stage = %s
                """,
                (
                    status.value,
                    started_at,
                    completed_at,
                    error_message,
                    json.dumps(metadata) if metadata else None,
                    json.dumps(metadata) if metadata else None,
                    job_id,
                    stage.value
                )
            )
            self.conn.commit()

    def get_job_status(self, job_id: UUID) -> Optional[JobStatusResponse]:
        """
        Get detailed job status with all stages

        Args:
            job_id: Job ID

        Returns:
            JobStatusResponse or None if not found
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get job info
            cur.execute(
                """
                SELECT id, status, product_name, insurer, created_at, updated_at,
                       completed_at, error_message
                FROM ingestion_jobs
                WHERE id = %s
                """,
                (job_id,)
            )
            job = cur.fetchone()

            if not job:
                return None

            # Get stages
            cur.execute(
                """
                SELECT stage, status, started_at, completed_at, error_message, metadata
                FROM ingestion_job_stages
                WHERE job_id = %s
                ORDER BY created_at
                """,
                (job_id,)
            )
            stages_data = cur.fetchall()

            # Convert to JobStageStatus objects
            stages = [
                JobStageStatus(
                    stage=JobStageType(stage["stage"]),
                    status=JobStatus(stage["status"]),
                    started_at=stage["started_at"],
                    completed_at=stage["completed_at"],
                    error_message=stage["error_message"],
                    metadata=json.loads(stage["metadata"]) if stage["metadata"] else None
                )
                for stage in stages_data
            ]

            # Calculate progress
            total_stages = len(stages)
            completed_stages = sum(1 for s in stages if s.status == JobStatus.COMPLETED)
            progress_percentage = int((completed_stages / total_stages * 100)) if total_stages > 0 else 0

            return JobStatusResponse(
                job_id=job["id"],
                status=JobStatus(job["status"]),
                product_name=job["product_name"],
                insurer=job["insurer"],
                created_at=job["created_at"],
                updated_at=job["updated_at"],
                completed_at=job["completed_at"],
                stages=stages,
                error_message=job["error_message"],
                progress_percentage=progress_percentage
            )

    def list_jobs(
        self,
        user_id: Optional[UUID] = None,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[JobStatusResponse]:
        """
        List jobs with optional filters

        Args:
            user_id: Optional filter by user
            status: Optional filter by status
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of JobStatusResponse
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT id
                FROM ingestion_jobs
                WHERE 1=1
            """
            params = []

            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)

            if status:
                query += " AND status = %s"
                params.append(status.value)

            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cur.execute(query, params)
            job_ids = [row["id"] for row in cur.fetchall()]

        # Get full status for each job
        jobs = []
        for job_id in job_ids:
            job_status = self.get_job_status(job_id)
            if job_status:
                jobs.append(job_status)

        return jobs
