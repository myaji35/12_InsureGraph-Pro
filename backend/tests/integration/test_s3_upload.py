"""
Integration tests for S3/GCS storage operations
"""
import pytest
from io import BytesIO
from fastapi import UploadFile
from unittest.mock import Mock, patch, MagicMock

from app.services.storage import S3StorageService, get_storage_service


class TestS3StorageService:
    """Integration tests for S3StorageService (GCS)"""

    @pytest.fixture
    def mock_gcs_client(self):
        """Mock Google Cloud Storage client"""
        with patch('app.services.storage.storage.Client') as mock_client:
            # Mock bucket and blob
            mock_bucket = Mock()
            mock_blob = Mock()

            mock_client.return_value.bucket.return_value = mock_bucket
            mock_bucket.blob.return_value = mock_blob

            yield {
                "client": mock_client,
                "bucket": mock_bucket,
                "blob": mock_blob,
            }

    @pytest.mark.asyncio
    async def test_upload_pdf_creates_proper_s3_key(self, mock_gcs_client):
        """Test that PDF upload creates properly formatted S3 key"""
        # Arrange
        service = S3StorageService()
        pdf_content = b'%PDF-1.4\nTest PDF content\n%%EOF'
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.seek = Mock()
        mock_file.read = Mock(return_value=pdf_content)

        # Act
        s3_key = await service.upload_pdf(
            file=mock_file,
            policy_name="Cancer Insurance 2.0",
            insurer="Samsung Life",
        )

        # Assert
        assert s3_key.startswith("policies/Samsung_Life/Cancer_Insurance_2.0_")
        assert s3_key.endswith(".pdf")

        # Verify blob upload was called
        mock_gcs_client["blob"].upload_from_string.assert_called_once()
        upload_args = mock_gcs_client["blob"].upload_from_string.call_args
        assert upload_args[0][0] == pdf_content  # First positional arg
        assert upload_args[1]["content_type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_upload_pdf_with_special_characters_in_names(self, mock_gcs_client):
        """Test that special characters are sanitized in S3 key"""
        # Arrange
        service = S3StorageService()
        pdf_content = b'%PDF-1.4\nContent\n%%EOF'
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.seek = Mock()
        mock_file.read = Mock(return_value=pdf_content)

        # Act
        s3_key = await service.upload_pdf(
            file=mock_file,
            policy_name="Test/Policy Name",  # Has slash
            insurer="Test Insurer",  # Has space
        )

        # Assert
        # Spaces should be replaced with underscores, slashes with hyphens
        assert "Test_Insurer" in s3_key
        assert "Test-Policy_Name" in s3_key
        assert " " not in s3_key
        assert "/" not in s3_key.replace("policies/", "")  # Except prefix

    @pytest.mark.asyncio
    async def test_upload_pdf_sets_content_type(self, mock_gcs_client):
        """Test that PDF content type is set correctly"""
        # Arrange
        service = S3StorageService()
        pdf_content = b'%PDF-1.4\n'
        mock_file = Mock(spec=UploadFile)
        mock_file.seek = Mock()
        mock_file.read = Mock(return_value=pdf_content)

        # Act
        await service.upload_pdf(
            file=mock_file,
            policy_name="Test",
            insurer="Test",
        )

        # Assert
        mock_blob = mock_gcs_client["blob"]
        assert mock_blob.content_type == "application/pdf"

    @pytest.mark.asyncio
    async def test_get_signed_url_generates_valid_url(self, mock_gcs_client):
        """Test signed URL generation"""
        # Arrange
        service = S3StorageService()
        s3_key = "policies/test/test.pdf"
        expected_url = "https://storage.googleapis.com/signed-url"

        mock_blob = mock_gcs_client["blob"]
        mock_blob.generate_signed_url.return_value = expected_url

        # Act
        url = await service.get_signed_url(s3_key, expiration=3600)

        # Assert
        assert url == expected_url
        mock_blob.generate_signed_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_file_exists_returns_true_for_existing_file(self, mock_gcs_client):
        """Test file existence check for existing file"""
        # Arrange
        service = S3StorageService()
        s3_key = "policies/test/test.pdf"

        mock_blob = mock_gcs_client["blob"]
        mock_blob.exists.return_value = True

        # Act
        exists = await service.file_exists(s3_key)

        # Assert
        assert exists is True

    @pytest.mark.asyncio
    async def test_file_exists_returns_false_for_missing_file(self, mock_gcs_client):
        """Test file existence check for missing file"""
        # Arrange
        service = S3StorageService()
        s3_key = "policies/nonexistent/file.pdf"

        mock_blob = mock_gcs_client["blob"]
        mock_blob.exists.return_value = False

        # Act
        exists = await service.file_exists(s3_key)

        # Assert
        assert exists is False

    @pytest.mark.asyncio
    async def test_delete_file_success(self, mock_gcs_client):
        """Test successful file deletion"""
        # Arrange
        service = S3StorageService()
        s3_key = "policies/test/test.pdf"

        mock_blob = mock_gcs_client["blob"]
        mock_blob.delete.return_value = None  # Successful deletion

        # Act
        result = await service.delete_file(s3_key)

        # Assert
        assert result is True
        mock_blob.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_storage_service_returns_singleton(self):
        """Test that get_storage_service returns singleton instance"""
        # Act
        service1 = get_storage_service()
        service2 = get_storage_service()

        # Assert
        assert service1 is service2  # Same instance
