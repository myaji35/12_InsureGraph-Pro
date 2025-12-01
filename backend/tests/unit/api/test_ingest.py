"""
Unit tests for Policy Ingestion API
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from app.models.ingestion_job import (
    IngestionJob,
    IngestionJobStatus,
    IngestionJobResults,
)
from app.models.user import User, UserRole


class TestUploadPolicyEndpoint:
    """Tests for POST /api/v1/policies/ingest"""

    @pytest.fixture
    def mock_storage_service(self):
        """Mock storage service"""
        with patch('app.api.v1.endpoints.ingest.get_storage_service') as mock:
            service = Mock()
            service.upload_pdf.return_value = "policies/Samsung_Life/cancer_insurance_uuid.pdf"
            mock.return_value = service
            yield service

    @pytest.fixture
    def mock_repo(self):
        """Mock ingestion job repository"""
        with patch('app.api.v1.endpoints.ingest.get_ingestion_repo') as mock:
            repo = Mock()
            mock.return_value = repo
            yield repo

    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user"""
        with patch('app.api.v1.endpoints.ingest.get_current_user') as mock:
            user = User(
                id=uuid4(),
                email="admin@test.com",
                full_name="Admin User",
                role=UserRole.ADMIN,
                hashed_password="hashed",
            )
            mock.return_value = user
            yield user

    @pytest.fixture
    def valid_pdf_file(self):
        """Create a valid PDF file for testing"""
        # PDF magic bytes + minimal PDF content
        pdf_content = b'%PDF-1.4\n%Test PDF content\n%%EOF'
        return BytesIO(pdf_content)

    def test_upload_valid_pdf_success(
        self,
        client: TestClient,
        mock_storage_service,
        mock_repo,
        mock_admin_user,
        valid_pdf_file,
    ):
        """Test successful PDF upload"""
        # Arrange
        job_id = uuid4()
        mock_job = IngestionJob(
            id=uuid4(),
            job_id=job_id,
            policy_name="Cancer Insurance",
            insurer="Samsung Life",
            launch_date="2025-01-01",
            s3_key="policies/Samsung_Life/cancer_insurance_uuid.pdf",
            status=IngestionJobStatus.PENDING,
            progress=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_repo.create.return_value = mock_job

        # Act
        response = client.post(
            "/api/v1/policies/ingest",
            files={"file": ("test.pdf", valid_pdf_file, "application/pdf")},
            data={
                "insurer": "Samsung Life",
                "product_name": "Cancer Insurance",
                "launch_date": "2025-01-01",
            },
        )

        # Assert
        assert response.status_code == 202
        data = response.json()
        assert data["job_id"] == str(job_id)
        assert data["status"] == "pending"
        assert data["policy_name"] == "Cancer Insurance"
        assert data["insurer"] == "Samsung Life"
        assert data["progress"] == 0
        assert data["estimated_completion_minutes"] == 5

        # Verify storage service was called
        mock_storage_service.upload_pdf.assert_called_once()

        # Verify repository was called
        mock_repo.create.assert_called_once()

    def test_upload_invalid_extension_rejected(
        self,
        client: TestClient,
        mock_admin_user,
    ):
        """Test that non-PDF files are rejected by extension"""
        # Arrange
        invalid_file = BytesIO(b'%PDF-1.4\nContent')

        # Act
        response = client.post(
            "/api/v1/policies/ingest",
            files={"file": ("test.txt", invalid_file, "text/plain")},
            data={
                "insurer": "Samsung Life",
                "product_name": "Test",
            },
        )

        # Assert
        assert response.status_code == 400
        assert "invalid extension" in response.json()["detail"].lower()

    def test_upload_file_too_large_rejected(
        self,
        client: TestClient,
        mock_admin_user,
    ):
        """Test that files over 100MB are rejected"""
        # Arrange
        # Create a file larger than 100MB (100MB + 1 byte)
        large_content = b'%PDF-1.4\n' + b'X' * (100 * 1024 * 1024 + 1)
        large_file = BytesIO(large_content)

        # Act
        response = client.post(
            "/api/v1/policies/ingest",
            files={"file": ("large.pdf", large_file, "application/pdf")},
            data={
                "insurer": "Samsung Life",
                "product_name": "Test",
            },
        )

        # Assert
        assert response.status_code == 400
        assert "exceeds maximum 100mb" in response.json()["detail"].lower()

    def test_upload_invalid_pdf_magic_bytes_rejected(
        self,
        client: TestClient,
        mock_admin_user,
    ):
        """Test that files without PDF magic bytes are rejected"""
        # Arrange
        invalid_pdf = BytesIO(b'Not a PDF file content')

        # Act
        response = client.post(
            "/api/v1/policies/ingest",
            files={"file": ("fake.pdf", invalid_pdf, "application/pdf")},
            data={
                "insurer": "Samsung Life",
                "product_name": "Test",
            },
        )

        # Assert
        assert response.status_code == 400
        assert "invalid magic bytes" in response.json()["detail"].lower()

    def test_upload_empty_file_rejected(
        self,
        client: TestClient,
        mock_admin_user,
    ):
        """Test that empty files are rejected"""
        # Arrange
        empty_file = BytesIO(b'')

        # Act
        response = client.post(
            "/api/v1/policies/ingest",
            files={"file": ("empty.pdf", empty_file, "application/pdf")},
            data={
                "insurer": "Samsung Life",
                "product_name": "Test",
            },
        )

        # Assert
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_upload_requires_authentication(self, client: TestClient):
        """Test that endpoint requires authentication"""
        # Act (without authentication mock)
        response = client.post(
            "/api/v1/policies/ingest",
            files={"file": ("test.pdf", BytesIO(b'%PDF-1.4'), "application/pdf")},
            data={"insurer": "Test", "product_name": "Test"},
        )

        # Assert
        assert response.status_code == 401


class TestGetJobStatusEndpoint:
    """Tests for GET /api/v1/policies/ingest/status/{job_id}"""

    @pytest.fixture
    def mock_repo(self):
        """Mock repository"""
        with patch('app.api.v1.endpoints.ingest.get_ingestion_repo') as mock:
            repo = Mock()
            mock.return_value = repo
            yield repo

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        with patch('app.api.v1.endpoints.ingest.get_current_user') as mock:
            user = User(
                id=uuid4(),
                email="user@test.com",
                full_name="Test User",
                role=UserRole.FP,
                hashed_password="hashed",
            )
            mock.return_value = user
            yield user

    def test_get_status_pending_job(
        self,
        client: TestClient,
        mock_repo,
        mock_user,
    ):
        """Test getting status of pending job"""
        # Arrange
        job_id = uuid4()
        mock_job = IngestionJob(
            id=uuid4(),
            job_id=job_id,
            policy_name="Test Policy",
            insurer="Test Insurer",
            s3_key="policies/test.pdf",
            status=IngestionJobStatus.PENDING,
            progress=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_repo.get_by_job_id.return_value = mock_job

        # Act
        response = client.get(f"/api/v1/policies/ingest/status/{job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == str(job_id)
        assert data["status"] == "pending"
        assert data["progress"] == 0
        assert data["estimated_completion_minutes"] == 5

    def test_get_status_completed_job_with_results(
        self,
        client: TestClient,
        mock_repo,
        mock_user,
    ):
        """Test getting status of completed job with results"""
        # Arrange
        job_id = uuid4()
        results = IngestionJobResults(
            nodes_created=150,
            edges_created=300,
            errors=[],
            processing_time_seconds=45.2,
        )
        mock_job = IngestionJob(
            id=uuid4(),
            job_id=job_id,
            policy_name="Test Policy",
            insurer="Test Insurer",
            s3_key="policies/test.pdf",
            status=IngestionJobStatus.COMPLETED,
            progress=100,
            results=results,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        mock_repo.get_by_job_id.return_value = mock_job

        # Act
        response = client.get(f"/api/v1/policies/ingest/status/{job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress"] == 100
        assert data["results"]["nodes_created"] == 150
        assert data["results"]["edges_created"] == 300
        assert data["estimated_completion_minutes"] is None

    def test_get_status_failed_job_with_error(
        self,
        client: TestClient,
        mock_repo,
        mock_user,
    ):
        """Test getting status of failed job with error message"""
        # Arrange
        job_id = uuid4()
        mock_job = IngestionJob(
            id=uuid4(),
            job_id=job_id,
            policy_name="Test Policy",
            insurer="Test Insurer",
            s3_key="policies/test.pdf",
            status=IngestionJobStatus.FAILED,
            progress=50,
            error_message="OCR processing failed: timeout",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        mock_repo.get_by_job_id.return_value = mock_job

        # Act
        response = client.get(f"/api/v1/policies/ingest/status/{job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "OCR processing failed: timeout"

    def test_get_status_job_not_found(
        self,
        client: TestClient,
        mock_repo,
        mock_user,
    ):
        """Test 404 when job doesn't exist"""
        # Arrange
        job_id = uuid4()
        mock_repo.get_by_job_id.return_value = None

        # Act
        response = client.get(f"/api/v1/policies/ingest/status/{job_id}")

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_status_requires_authentication(self, client: TestClient):
        """Test that endpoint requires authentication"""
        # Act
        job_id = uuid4()
        response = client.get(f"/api/v1/policies/ingest/status/{job_id}")

        # Assert
        assert response.status_code == 401
