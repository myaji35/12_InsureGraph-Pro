"""
Downloader Celery Tasks

On-demand tasks for downloading and ingesting queued policy files.

Epic: Epic 1, Story 1.0
Created: 2025-11-28
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import UUID

import httpx
from loguru import logger

from app.celery_app import celery_app
from app.models.policy_metadata import PolicyMetadataStatus


@celery_app.task(
    name="downloader.download_and_ingest_policy",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    time_limit=600,  # 10 minutes max
)
def download_and_ingest_policy_task(self, job_id: str) -> Dict[str, Any]:
    """
    Download policy PDF and trigger ingestion pipeline

    This task:
    1. Fetches job from database
    2. Downloads PDF from download_url
    3. Uploads to S3/local storage
    4. Updates policy_metadata status
    5. Triggers existing ingestion pipeline (Story 1.2+)

    Args:
        job_id: Ingestion job ID (UUID string)

    Returns:
        Result dictionary
    """
    logger.info(f"Starting download task for job {job_id}")

    try:
        # Get job from database
        job = _get_ingestion_job(job_id)
        if not job:
            raise ValueError(f"Ingestion job not found: {job_id}")

        policy_metadata_id = job.get("policy_metadata_id")
        download_url = job.get("download_url")

        if not download_url:
            raise ValueError(f"No download URL for job {job_id}")

        # Update policy status: QUEUED -> DOWNLOADING
        _update_policy_status(policy_metadata_id, PolicyMetadataStatus.DOWNLOADING)
        _update_job_status(job_id, "DOWNLOADING")

        # Download file
        logger.info(f"Downloading from {download_url}")
        file_path = _download_file(download_url, job)

        # Update status: DOWNLOADING -> PROCESSING
        _update_policy_status(policy_metadata_id, PolicyMetadataStatus.PROCESSING)
        _update_job_status(job_id, "PROCESSING", progress=50)

        # Trigger ingestion pipeline
        logger.info(f"Triggering ingestion pipeline for {file_path}")
        ingestion_result = _trigger_ingestion_pipeline(file_path, job)

        # Update status: PROCESSING -> COMPLETED
        _update_policy_status(policy_metadata_id, PolicyMetadataStatus.COMPLETED)
        _update_job_status(job_id, "COMPLETED", progress=100, results=ingestion_result)

        result = {
            "status": "success",
            "job_id": job_id,
            "policy_metadata_id": str(policy_metadata_id),
            "file_path": str(file_path),
            "ingestion_result": ingestion_result,
        }

        logger.info(f"Download and ingestion complete for job {job_id}")
        return result

    except Exception as e:
        logger.error(f"Download task failed for job {job_id}: {e}")

        # Update status to FAILED
        try:
            _update_policy_status(
                job.get("policy_metadata_id"),
                PolicyMetadataStatus.FAILED
            )
            _update_job_status(
                job_id,
                "FAILED",
                error_message=str(e)
            )
        except:
            pass

        # Retry on failure
        raise self.retry(exc=e)


# ============================================
# Helper Functions
# ============================================

def _get_ingestion_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get ingestion job from database"""
    # TODO: Replace with actual database query
    from app.api.v1.endpoints.metadata import _ingestion_jobs_store

    try:
        job_uuid = UUID(job_id)
        return _ingestion_jobs_store.get(job_uuid)
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        return None


def _update_policy_status(policy_id: UUID, new_status: PolicyMetadataStatus):
    """Update policy metadata status"""
    # TODO: Replace with actual database update
    from app.api.v1.endpoints.metadata import _policy_metadata_store

    policy = _policy_metadata_store.get(policy_id)
    if policy:
        policy.update_status(new_status)
        logger.info(f"Updated policy {policy_id} status to {new_status.value}")


def _update_job_status(
    job_id: str,
    status: str,
    progress: int = 0,
    error_message: Optional[str] = None,
    results: Optional[Dict[str, Any]] = None,
):
    """Update ingestion job status"""
    # TODO: Replace with actual database update
    from app.api.v1.endpoints.metadata import _ingestion_jobs_store

    try:
        job_uuid = UUID(job_id)
        job = _ingestion_jobs_store.get(job_uuid)

        if job:
            job["status"] = status
            job["progress"] = progress

            if error_message:
                job["error_message"] = error_message

            if results:
                job["results"] = results

            if status == "PROCESSING":
                job["started_at"] = datetime.utcnow()
            elif status in ["COMPLETED", "FAILED"]:
                job["completed_at"] = datetime.utcnow()

            logger.info(f"Updated job {job_id} status to {status}")

    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")


def _download_file(download_url: str, job: Dict[str, Any]) -> Path:
    """
    Download file from URL to local storage

    Args:
        download_url: Source URL
        job: Job metadata

    Returns:
        Path to downloaded file
    """
    # Create download directory
    download_dir = Path("/tmp/insuregraph/downloads")
    download_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    file_name = job.get("file_name") or f"policy_{job['id']}.pdf"
    file_path = download_dir / file_name

    # Download file
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        response = client.get(download_url)
        response.raise_for_status()

        # Save to file
        with open(file_path, "wb") as f:
            f.write(response.content)

        logger.info(
            f"Downloaded {len(response.content)} bytes to {file_path}"
        )

    # TODO: Upload to S3 for permanent storage
    # s3_url = upload_to_s3(file_path, bucket="insuregraph-policies")

    return file_path


def _trigger_ingestion_pipeline(
    file_path: Path,
    job: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Trigger existing ingestion pipeline (Story 1.2+)

    Args:
        file_path: Path to downloaded PDF
        job: Job metadata

    Returns:
        Ingestion results
    """
    # TODO: Integrate with existing LangGraph ingestion workflow
    # from app.workflows.ingestion_workflow import run_ingestion_workflow
    #
    # result = await run_ingestion_workflow(
    #     file_path=str(file_path),
    #     metadata={
    #         "insurer": job["metadata"]["insurer"],
    #         "product_name": job["metadata"]["policy_name"],
    #         "launch_date": job["metadata"]["publication_date"],
    #     }
    # )

    # For now, return a mock result
    logger.warning("Ingestion pipeline integration not yet implemented")

    return {
        "status": "mocked",
        "nodes_created": 0,
        "edges_created": 0,
        "message": "Ingestion pipeline not yet connected"
    }


@celery_app.task(name="downloader.cleanup_old_downloads")
def cleanup_old_downloads_task() -> Dict[str, Any]:
    """
    Cleanup old downloaded files from local storage

    This task runs periodically to free up disk space.
    """
    logger.info("Starting cleanup of old downloads")

    download_dir = Path("/tmp/insuregraph/downloads")

    if not download_dir.exists():
        return {"status": "skipped", "reason": "Download directory does not exist"}

    # Delete files older than 7 days
    import time
    from datetime import timedelta

    cutoff_time = time.time() - timedelta(days=7).total_seconds()
    deleted_count = 0
    freed_bytes = 0

    for file_path in download_dir.glob("*.pdf"):
        if file_path.stat().st_mtime < cutoff_time:
            freed_bytes += file_path.stat().st_size
            file_path.unlink()
            deleted_count += 1

    logger.info(
        f"Cleanup complete: deleted {deleted_count} files, "
        f"freed {freed_bytes / 1024 / 1024:.2f} MB"
    )

    return {
        "status": "success",
        "deleted_count": deleted_count,
        "freed_mb": freed_bytes / 1024 / 1024,
    }
