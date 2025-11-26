"""
OCR service using Upstage Document AI for policy document processing
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
import httpx
import asyncio
from datetime import datetime

from app.core.config import settings
from app.services.ingestion.storage import gcs_service
from app.services.ingestion.job_manager import JobManager
from app.schemas.ingestion import JobStatus, JobStageType


class UpstageOCRService:
    """Service for OCR processing using Upstage Document AI"""

    def __init__(self):
        """Initialize Upstage OCR service"""
        self.api_key = settings.UPSTAGE_API_KEY
        self.api_base_url = "https://api.upstage.ai/v1/document-ai"
        self.timeout = 300  # 5 minutes timeout for OCR

    async def process_document(
        self,
        job_id: UUID,
        gcs_uri: str,
        db_connection
    ) -> Dict[str, Any]:
        """
        Process a document using Upstage Document AI

        Args:
            job_id: Job ID for tracking
            gcs_uri: GCS URI of the PDF document
            db_connection: PostgreSQL connection

        Returns:
            Dictionary with OCR results:
            {
                "pages": [
                    {
                        "page_num": 1,
                        "text": "...",
                        "tables": [...],
                        "layout": {...}
                    }
                ],
                "total_pages": 120,
                "processing_time_seconds": 45.2
            }

        Raises:
            Exception: If OCR processing fails
        """
        job_manager = JobManager(db_connection)

        try:
            # Update stage status to processing
            job_manager.create_stage(job_id, JobStageType.OCR, JobStatus.PENDING)
            job_manager.update_stage_status(
                job_id,
                JobStageType.OCR,
                JobStatus.PROCESSING,
                metadata={"started_at": datetime.utcnow().isoformat()}
            )

            # Get signed URL for temporary access
            # Extract blob name from GCS URI
            blob_name = gcs_uri.replace(f"gs://{settings.GCS_BUCKET_POLICIES}/", "")
            signed_url = gcs_service.generate_signed_url(blob_name, expiration_minutes=60)

            # Call Upstage Document AI API
            start_time = datetime.utcnow()
            ocr_result = await self._call_upstage_api(signed_url)
            end_time = datetime.utcnow()

            processing_time = (end_time - start_time).total_seconds()

            # Parse and structure the response
            structured_result = self._parse_upstage_response(ocr_result)
            structured_result["processing_time_seconds"] = processing_time

            # Update stage status to completed
            job_manager.update_stage_status(
                job_id,
                JobStageType.OCR,
                JobStatus.COMPLETED,
                metadata={
                    "total_pages": structured_result["total_pages"],
                    "processing_time_seconds": processing_time,
                    "completed_at": end_time.isoformat()
                }
            )

            # Update overall job status
            job_manager.update_job_status(job_id, JobStatus.PROCESSING)

            return structured_result

        except Exception as e:
            # Mark stage as failed
            job_manager.update_stage_status(
                job_id,
                JobStageType.OCR,
                JobStatus.FAILED,
                error_message=str(e)
            )
            job_manager.update_job_status(job_id, JobStatus.FAILED, error_message=f"OCR failed: {str(e)}")
            raise

    async def _call_upstage_api(self, file_url: str) -> Dict[str, Any]:
        """
        Call Upstage Document AI API

        Args:
            file_url: Signed URL to the PDF file

        Returns:
            Raw API response

        Raises:
            httpx.HTTPError: If API call fails
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Upstage Document AI endpoint
            response = await client.post(
                f"{self.api_base_url}/ocr",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "document": {
                        "url": file_url
                    },
                    "options": {
                        "extract_text": True,
                        "extract_tables": True,
                        "extract_layout": True,
                        "language": "ko"  # Korean language
                    }
                }
            )

            response.raise_for_status()
            return response.json()

    def _parse_upstage_response(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Upstage API response into structured format

        Args:
            raw_response: Raw API response from Upstage

        Returns:
            Structured OCR result
        """
        pages = []

        # Parse pages from Upstage response
        # Note: Actual response format may vary - adjust based on Upstage API docs
        for page_data in raw_response.get("pages", []):
            page = {
                "page_num": page_data.get("page_number", 0),
                "text": page_data.get("text", ""),
                "tables": page_data.get("tables", []),
                "layout": page_data.get("layout", {}),
                "coordinates": page_data.get("coordinates", {}),
                "confidence": page_data.get("confidence", 0.0)
            }
            pages.append(page)

        return {
            "pages": pages,
            "total_pages": len(pages),
            "metadata": raw_response.get("metadata", {})
        }

    async def batch_process_documents(
        self,
        job_ids: List[UUID],
        db_connection,
        max_concurrent: int = 3
    ) -> Dict[UUID, Dict[str, Any]]:
        """
        Process multiple documents concurrently

        Args:
            job_ids: List of job IDs to process
            db_connection: PostgreSQL connection
            max_concurrent: Maximum concurrent OCR requests

        Returns:
            Dictionary mapping job_id to OCR results
        """
        results = {}
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(job_id: UUID):
            async with semaphore:
                # Get GCS URI from database
                with db_connection.cursor() as cur:
                    cur.execute("SELECT gcs_uri FROM ingestion_jobs WHERE id = %s", (job_id,))
                    result = cur.fetchone()
                    gcs_uri = result[0] if result else None

                if not gcs_uri:
                    return None

                return await self.process_document(job_id, gcs_uri, db_connection)

        # Process all jobs concurrently
        tasks = [process_with_semaphore(job_id) for job_id in job_ids]
        ocr_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Map results to job IDs
        for job_id, result in zip(job_ids, ocr_results):
            if isinstance(result, Exception):
                results[job_id] = {"error": str(result)}
            else:
                results[job_id] = result

        return results


# Global instance
ocr_service = UpstageOCRService()
