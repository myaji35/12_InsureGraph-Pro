"""
Ingestion Job Repository

Data access layer for ingestion_jobs table.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from loguru import logger

from app.core.database import PostgreSQLManager
from app.models.ingestion_job import (
    IngestionJob,
    IngestionJobCreate,
    IngestionJobUpdate,
    IngestionJobStatus,
    IngestionJobResults,
)


class IngestionJobRepository:
    """Repository for ingestion jobs data access"""

    def __init__(self, db_manager: PostgreSQLManager):
        self.db_manager = db_manager

    def create(self, job_data: IngestionJobCreate) -> IngestionJob:
        """
        Create a new ingestion job.

        Args:
            job_data: Job creation data

        Returns:
            Created IngestionJob

        Raises:
            Exception: If database operation fails
        """
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                INSERT INTO ingestion_jobs (
                    policy_name, insurer, launch_date, s3_key, status, progress
                )
                VALUES (%(policy_name)s, %(insurer)s, %(launch_date)s, %(s3_key)s, %(status)s, %(progress)s)
                RETURNING *
            """

            cursor.execute(query, {
                "policy_name": job_data.policy_name,
                "insurer": job_data.insurer,
                "launch_date": job_data.launch_date,
                "s3_key": job_data.s3_key,
                "status": IngestionJobStatus.PENDING.value,
                "progress": 0,
            })

            row = cursor.fetchone()
            conn.commit()

            logger.info(f"Created ingestion job: {row['job_id']}")

            return self._row_to_model(row)

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to create ingestion job: {e}")
            raise

        finally:
            if conn:
                self.db_manager.return_connection(conn)

    def get_by_job_id(self, job_id: UUID) -> Optional[IngestionJob]:
        """
        Get job by job_id.

        Args:
            job_id: Public job identifier

        Returns:
            IngestionJob if found, None otherwise
        """
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = "SELECT * FROM ingestion_jobs WHERE job_id = %s"
            cursor.execute(query, (str(job_id),))

            row = cursor.fetchone()

            if row:
                return self._row_to_model(row)
            return None

        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            raise

        finally:
            if conn:
                self.db_manager.return_connection(conn)

    def update(self, job_id: UUID, update_data: IngestionJobUpdate) -> Optional[IngestionJob]:
        """
        Update job status and progress.

        Args:
            job_id: Job identifier
            update_data: Fields to update

        Returns:
            Updated IngestionJob if found, None otherwise
        """
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Build dynamic UPDATE query
            update_fields = []
            params = {}

            if update_data.status is not None:
                update_fields.append("status = %(status)s")
                params["status"] = update_data.status.value

                # Auto-set completed_at for terminal states
                if update_data.status in [IngestionJobStatus.COMPLETED, IngestionJobStatus.FAILED]:
                    update_fields.append("completed_at = NOW()")

            if update_data.progress is not None:
                update_fields.append("progress = %(progress)s")
                params["progress"] = update_data.progress

            if update_data.results is not None:
                update_fields.append("results = %(results)s")
                params["results"] = Json(update_data.results.model_dump())

            if update_data.error_message is not None:
                update_fields.append("error_message = %(error_message)s")
                params["error_message"] = update_data.error_message

            if not update_fields:
                # No updates requested
                return self.get_by_job_id(job_id)

            params["job_id"] = str(job_id)

            query = f"""
                UPDATE ingestion_jobs
                SET {", ".join(update_fields)}
                WHERE job_id = %(job_id)s
                RETURNING *
            """

            cursor.execute(query, params)
            row = cursor.fetchone()
            conn.commit()

            if row:
                logger.info(f"Updated ingestion job {job_id}: {update_fields}")
                return self._row_to_model(row)

            return None

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to update job {job_id}: {e}")
            raise

        finally:
            if conn:
                self.db_manager.return_connection(conn)

    def list_jobs(
        self,
        status: Optional[IngestionJobStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[IngestionJob]:
        """
        List all ingestion jobs with optional filtering.

        Args:
            status: Optional status filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of IngestionJob
        """
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            if status is not None:
                query = """
                    SELECT * FROM ingestion_jobs
                    WHERE status = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(query, (status.value, limit, offset))
            else:
                query = """
                    SELECT * FROM ingestion_jobs
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(query, (limit, offset))

            rows = cursor.fetchall()
            return [self._row_to_model(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            raise

        finally:
            if conn:
                self.db_manager.return_connection(conn)

    def list_by_status(self, status: IngestionJobStatus, limit: int = 100) -> List[IngestionJob]:
        """
        List jobs by status.

        Args:
            status: Job status to filter
            limit: Maximum number of results

        Returns:
            List of IngestionJob
        """
        return self.list_jobs(status=status, limit=limit, offset=0)

    def _row_to_model(self, row: dict) -> IngestionJob:
        """Convert database row to IngestionJob model"""
        # Parse results JSON if present
        results = None
        if row.get("results"):
            results = IngestionJobResults(**row["results"])

        return IngestionJob(
            id=row["id"],
            job_id=row["job_id"],
            policy_name=row["policy_name"],
            insurer=row["insurer"],
            launch_date=row.get("launch_date"),
            s3_key=row["s3_key"],
            status=IngestionJobStatus(row["status"]),
            progress=row["progress"],
            results=results,
            error_message=row.get("error_message"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row.get("completed_at"),
        )
