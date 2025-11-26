"""
Background worker for OCR processing queue

This module would typically be run as a separate process/container
that polls for new upload jobs and processes them asynchronously.
"""
import asyncio
import time
from typing import List
from uuid import UUID

from app.core.database import pg_manager, redis_manager
from app.services.ingestion.ocr_service import ocr_service
from app.services.ingestion.job_manager import JobManager
from app.schemas.ingestion import JobStatus


class OCRWorker:
    """Background worker for processing OCR jobs"""

    def __init__(self, poll_interval_seconds: int = 10):
        """
        Initialize OCR worker

        Args:
            poll_interval_seconds: How often to poll for new jobs
        """
        self.poll_interval = poll_interval_seconds
        self.running = False

    async def start(self):
        """Start the worker loop"""
        print("🤖 OCR Worker starting...")
        self.running = True

        # Connect to databases
        pg_manager.connect()
        redis_manager.connect()

        print("✅ OCR Worker connected to databases")

        try:
            while self.running:
                await self._process_pending_jobs()
                await asyncio.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print("\n⚠️ Received interrupt signal, shutting down...")
        finally:
            self.stop()

    def stop(self):
        """Stop the worker"""
        self.running = False
        pg_manager.disconnect()
        redis_manager.disconnect()
        print("✅ OCR Worker stopped")

    async def _process_pending_jobs(self):
        """Poll for pending jobs and process them"""
        conn = pg_manager.get_connection()

        try:
            job_manager = JobManager(conn)

            # Find jobs with status UPLOADED (ready for OCR)
            pending_job_ids = self._get_pending_job_ids(conn)

            if not pending_job_ids:
                return

            print(f"📋 Found {len(pending_job_ids)} pending job(s)")

            # Process jobs concurrently (max 3 at a time)
            results = await ocr_service.batch_process_documents(
                pending_job_ids,
                conn,
                max_concurrent=3
            )

            # Log results
            for job_id, result in results.items():
                if "error" in result:
                    print(f"❌ Job {job_id} failed: {result['error']}")
                else:
                    pages = result.get("total_pages", 0)
                    time_taken = result.get("processing_time_seconds", 0)
                    print(f"✅ Job {job_id} completed: {pages} pages in {time_taken:.2f}s")

        finally:
            pg_manager.return_connection(conn)

    def _get_pending_job_ids(self, conn) -> List[UUID]:
        """
        Get list of job IDs that are ready for OCR processing

        Args:
            conn: PostgreSQL connection

        Returns:
            List of job UUIDs
        """
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM ingestion_jobs
                WHERE status = %s
                ORDER BY created_at
                LIMIT 10
                """,
                (JobStatus.UPLOADED.value,)
            )
            rows = cur.fetchall()
            return [row[0] for row in rows]


async def main():
    """Main entry point for OCR worker"""
    worker = OCRWorker(poll_interval_seconds=10)
    await worker.start()


if __name__ == "__main__":
    """
    Run the OCR worker as a standalone process:

    python -m app.services.ingestion.ocr_worker
    """
    asyncio.run(main())
