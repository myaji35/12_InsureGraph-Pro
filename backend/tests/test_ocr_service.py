"""
Unit tests for OCR service
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from app.services.ingestion.ocr_service import UpstageOCRService
from app.schemas.ingestion import JobStatus, JobStageType


class TestUpstageOCRService:
    """Test cases for UpstageOCRService"""

    @pytest.mark.asyncio
    async def test_parse_upstage_response(self, mock_ocr_response):
        """Test parsing Upstage API response"""
        # Arrange
        service = UpstageOCRService()

        # Act
        result = service._parse_upstage_response(mock_ocr_response)

        # Assert
        assert result["total_pages"] == 2
        assert len(result["pages"]) == 2
        assert result["pages"][0]["page_num"] == 1
        assert result["pages"][0]["text"] == "보험약관 테스트 텍스트"
        assert result["pages"][1]["page_num"] == 2

    @pytest.mark.asyncio
    @patch("app.services.ingestion.ocr_service.gcs_service")
    @patch("app.services.ingestion.ocr_service.JobManager")
    async def test_process_document_success(
        self,
        mock_job_manager_class,
        mock_gcs_service,
        mock_db_connection,
        sample_job_id,
        mock_ocr_response
    ):
        """Test successful document processing"""
        # Arrange
        service = UpstageOCRService()
        gcs_uri = "gs://test-bucket/policies/test.pdf"

        # Mock GCS service
        mock_gcs_service.generate_signed_url.return_value = "https://signed-url.com"

        # Mock job manager
        mock_job_manager = Mock()
        mock_job_manager_class.return_value = mock_job_manager

        # Mock API call
        with patch.object(service, "_call_upstage_api", new=AsyncMock(return_value=mock_ocr_response)):
            # Act
            result = await service.process_document(
                sample_job_id,
                gcs_uri,
                mock_db_connection
            )

            # Assert
            assert result["total_pages"] == 2
            assert "processing_time_seconds" in result
            assert mock_job_manager.create_stage.called
            assert mock_job_manager.update_stage_status.called

    @pytest.mark.asyncio
    async def test_call_upstage_api_success(self, mock_ocr_response):
        """Test Upstage API call"""
        # Arrange
        service = UpstageOCRService()
        file_url = "https://signed-url.com/test.pdf"

        # Mock httpx client
        mock_response = Mock()
        mock_response.json.return_value = mock_ocr_response
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            # Act
            result = await service._call_upstage_api(file_url)

            # Assert
            assert result == mock_ocr_response
            assert "pages" in result

    @pytest.mark.asyncio
    @patch("app.services.ingestion.ocr_service.gcs_service")
    @patch("app.services.ingestion.ocr_service.JobManager")
    async def test_process_document_failure(
        self,
        mock_job_manager_class,
        mock_gcs_service,
        mock_db_connection,
        sample_job_id
    ):
        """Test document processing failure"""
        # Arrange
        service = UpstageOCRService()
        gcs_uri = "gs://test-bucket/policies/test.pdf"

        # Mock GCS service
        mock_gcs_service.generate_signed_url.return_value = "https://signed-url.com"

        # Mock job manager
        mock_job_manager = Mock()
        mock_job_manager_class.return_value = mock_job_manager

        # Mock API call to raise exception
        with patch.object(service, "_call_upstage_api", new=AsyncMock(side_effect=Exception("API Error"))):
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await service.process_document(
                    sample_job_id,
                    gcs_uri,
                    mock_db_connection
                )

            assert "API Error" in str(exc_info.value)
            assert mock_job_manager.update_stage_status.called
            assert mock_job_manager.update_job_status.called

    @pytest.mark.asyncio
    async def test_batch_process_documents(self, mock_db_connection, mock_ocr_response):
        """Test batch processing of multiple documents"""
        # Arrange
        service = UpstageOCRService()
        job_ids = [uuid4(), uuid4()]

        # Mock database queries
        cursor = mock_db_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [
            ("gs://bucket/file1.pdf",),
            ("gs://bucket/file2.pdf",)
        ]

        # Mock process_document
        with patch.object(service, "process_document", new=AsyncMock(return_value={"total_pages": 10})):
            # Act
            results = await service.batch_process_documents(
                job_ids,
                mock_db_connection,
                max_concurrent=2
            )

            # Assert
            assert len(results) == 2
            assert all(job_id in results for job_id in job_ids)
