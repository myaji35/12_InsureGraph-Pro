"""
Unit tests for JobManager service
"""
import pytest
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.ingestion.job_manager import JobManager
from app.schemas.ingestion import (
    PolicyUploadRequest,
    JobStatus,
    JobStageType
)


class TestJobManager:
    """Test cases for JobManager"""

    def test_create_job_success(self, mock_db_connection, sample_user_id, sample_policy_upload_request):
        """Test successful job creation"""
        # Arrange
        job_manager = JobManager(mock_db_connection)
        request = PolicyUploadRequest(**sample_policy_upload_request)
        gcs_uri = "gs://test-bucket/policies/test.pdf"
        blob_name = "policies/test.pdf"
        file_size = 1024000  # 1MB

        # Act
        job_id = job_manager.create_job(
            user_id=sample_user_id,
            request=request,
            gcs_uri=gcs_uri,
            blob_name=blob_name,
            file_size_bytes=file_size,
            filename="test.pdf"
        )

        # Assert
        assert job_id is not None
        assert mock_db_connection.cursor.called
        assert mock_db_connection.commit.called

    def test_update_job_status(self, mock_db_connection, sample_job_id):
        """Test updating job status"""
        # Arrange
        job_manager = JobManager(mock_db_connection)

        # Act
        job_manager.update_job_status(
            sample_job_id,
            JobStatus.PROCESSING
        )

        # Assert
        assert mock_db_connection.cursor.called
        assert mock_db_connection.commit.called

    def test_create_stage(self, mock_db_connection, sample_job_id):
        """Test creating a job stage"""
        # Arrange
        job_manager = JobManager(mock_db_connection)

        # Act
        job_manager.create_stage(
            sample_job_id,
            JobStageType.OCR,
            JobStatus.PENDING,
            metadata={"test": "data"}
        )

        # Assert
        assert mock_db_connection.cursor.called
        assert mock_db_connection.commit.called

    def test_update_stage_status(self, mock_db_connection, sample_job_id):
        """Test updating stage status"""
        # Arrange
        job_manager = JobManager(mock_db_connection)

        # Act
        job_manager.update_stage_status(
            sample_job_id,
            JobStageType.OCR,
            JobStatus.COMPLETED,
            metadata={"pages_processed": 120}
        )

        # Assert
        assert mock_db_connection.cursor.called
        assert mock_db_connection.commit.called

    def test_get_job_status_not_found(self, mock_db_connection, sample_job_id):
        """Test getting status of non-existent job"""
        # Arrange
        job_manager = JobManager(mock_db_connection)
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = None

        # Act
        result = job_manager.get_job_status(sample_job_id)

        # Assert
        assert result is None

    def test_get_job_status_success(self, mock_db_connection, sample_job_id):
        """Test getting job status successfully"""
        # Arrange
        job_manager = JobManager(mock_db_connection)
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value

        # Mock job data
        cursor.fetchone.return_value = {
            "id": sample_job_id,
            "status": "processing",
            "product_name": "Test Product",
            "insurer": "Test Insurer",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "completed_at": None,
            "error_message": None
        }

        # Mock stages data
        cursor.fetchall.return_value = [
            {
                "stage": "upload",
                "status": "completed",
                "started_at": datetime.utcnow(),
                "completed_at": datetime.utcnow(),
                "error_message": None,
                "metadata": '{"file_size_mb": 1.5}'
            }
        ]

        # Act
        result = job_manager.get_job_status(sample_job_id)

        # Assert
        assert result is not None
        assert result.job_id == sample_job_id
        assert len(result.stages) == 1

    def test_list_jobs(self, mock_db_connection, sample_user_id):
        """Test listing jobs"""
        # Arrange
        job_manager = JobManager(mock_db_connection)
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = []

        # Act
        jobs = job_manager.list_jobs(user_id=sample_user_id, limit=10)

        # Assert
        assert isinstance(jobs, list)
        assert mock_db_connection.cursor.called
