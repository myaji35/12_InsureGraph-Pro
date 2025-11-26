"""
Unit tests for ingestion API endpoints
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from io import BytesIO
from datetime import datetime

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestIngestionAPI:
    """Test cases for ingestion API endpoints"""

    @patch("app.api.v1.ingestion.get_current_user")
    @patch("app.api.v1.ingestion.gcs_service")
    @patch("app.api.v1.ingestion.JobManager")
    def test_upload_policy_success(
        self,
        mock_job_manager_class,
        mock_gcs_service,
        mock_get_current_user
    ):
        """Test successful policy upload"""
        # Arrange
        mock_get_current_user.return_value = {"sub": str(uuid4()), "role": "fp"}

        job_id = uuid4()
        mock_job_manager = Mock()
        mock_job_manager.create_job.return_value = job_id
        mock_job_manager.get_job_status.return_value = Mock(created_at=datetime.utcnow())
        mock_job_manager_class.return_value = mock_job_manager

        mock_gcs_service.upload_policy_pdf.return_value = (
            "policies/test.pdf",
            "gs://bucket/policies/test.pdf"
        )

        # Create a small PDF-like file
        pdf_content = b"%PDF-1.4\n%Test PDF content"
        files = {"file": ("test.pdf", BytesIO(pdf_content), "application/pdf")}
        data = {
            "insurer": "삼성생명",
            "product_name": "테스트 상품",
        }

        # Act
        response = client.post("/api/v1/policies/ingest", files=files, data=data)

        # Assert
        assert response.status_code == 201
        assert "job_id" in response.json()

    @patch("app.api.v1.ingestion.get_current_user")
    def test_upload_policy_invalid_file_type(self, mock_get_current_user):
        """Test upload with invalid file type"""
        # Arrange
        mock_get_current_user.return_value = {"sub": str(uuid4()), "role": "fp"}

        files = {"file": ("test.txt", BytesIO(b"text content"), "text/plain")}
        data = {
            "insurer": "삼성생명",
            "product_name": "테스트 상품",
        }

        # Act
        response = client.post("/api/v1/policies/ingest", files=files, data=data)

        # Assert
        assert response.status_code == 400
        assert "Only PDF files are supported" in response.json()["detail"]

    @patch("app.api.v1.ingestion.get_current_user")
    @patch("app.api.v1.ingestion.JobManager")
    def test_get_job_status_success(self, mock_job_manager_class, mock_get_current_user):
        """Test getting job status"""
        # Arrange
        mock_get_current_user.return_value = {"sub": str(uuid4()), "role": "fp"}

        job_id = uuid4()
        mock_job_manager = Mock()
        mock_status = Mock()
        mock_status.dict = Mock(return_value={
            "job_id": str(job_id),
            "status": "processing",
            "product_name": "Test",
            "insurer": "Test",
            "stages": []
        })
        mock_job_manager.get_job_status.return_value = mock_status
        mock_job_manager_class.return_value = mock_job_manager

        # Act
        response = client.get(f"/api/v1/policies/ingest/{job_id}/status")

        # Assert
        assert response.status_code == 200

    @patch("app.api.v1.ingestion.get_current_user")
    @patch("app.api.v1.ingestion.JobManager")
    def test_get_job_status_not_found(self, mock_job_manager_class, mock_get_current_user):
        """Test getting status of non-existent job"""
        # Arrange
        mock_get_current_user.return_value = {"sub": str(uuid4()), "role": "fp"}

        job_id = uuid4()
        mock_job_manager = Mock()
        mock_job_manager.get_job_status.return_value = None
        mock_job_manager_class.return_value = mock_job_manager

        # Act
        response = client.get(f"/api/v1/policies/ingest/{job_id}/status")

        # Assert
        assert response.status_code == 404

    @patch("app.api.v1.ingestion.get_current_user")
    @patch("app.api.v1.ingestion.JobManager")
    def test_list_jobs(self, mock_job_manager_class, mock_get_current_user):
        """Test listing jobs"""
        # Arrange
        mock_get_current_user.return_value = {"sub": str(uuid4()), "role": "fp"}

        mock_job_manager = Mock()
        mock_job_manager.list_jobs.return_value = []
        mock_job_manager_class.return_value = mock_job_manager

        # Act
        response = client.get("/api/v1/policies/ingest")

        # Assert
        assert response.status_code == 200
        assert "jobs" in response.json()
        assert "total" in response.json()
