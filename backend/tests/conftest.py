"""
Pytest configuration and fixtures
"""
import pytest
from uuid import uuid4
from unittest.mock import Mock, MagicMock
import psycopg2

from app.core.config import settings


@pytest.fixture
def mock_db_connection():
    """Mock PostgreSQL connection"""
    conn = Mock()
    cursor = Mock()
    cursor.__enter__ = Mock(return_value=cursor)
    cursor.__exit__ = Mock(return_value=False)
    conn.cursor = Mock(return_value=cursor)
    conn.commit = Mock()
    return conn


@pytest.fixture
def mock_gcs_client():
    """Mock Google Cloud Storage client"""
    client = Mock()
    bucket = Mock()
    blob = Mock()

    client.bucket = Mock(return_value=bucket)
    bucket.blob = Mock(return_value=blob)
    blob.upload_from_file = Mock()
    blob.generate_signed_url = Mock(return_value="https://storage.googleapis.com/signed-url")
    blob.exists = Mock(return_value=True)
    blob.delete = Mock()

    return client


@pytest.fixture
def sample_job_id():
    """Sample job UUID"""
    return uuid4()


@pytest.fixture
def sample_user_id():
    """Sample user UUID"""
    return uuid4()


@pytest.fixture
def sample_policy_upload_request():
    """Sample policy upload request data"""
    return {
        "insurer": "삼성생명",
        "product_name": "삼성생명 무배당 건강보험",
        "product_code": "SL-HEALTH-001",
        "launch_date": "2024-01-01",
        "description": "Test policy"
    }


@pytest.fixture
def mock_ocr_response():
    """Mock OCR API response"""
    return {
        "pages": [
            {
                "page_number": 1,
                "text": "보험약관 테스트 텍스트",
                "tables": [],
                "layout": {},
                "coordinates": {},
                "confidence": 0.95
            },
            {
                "page_number": 2,
                "text": "제2조 보장내용",
                "tables": [{"rows": 3, "cols": 2}],
                "layout": {},
                "coordinates": {},
                "confidence": 0.92
            }
        ],
        "metadata": {
            "document_type": "insurance_policy",
            "language": "ko"
        }
    }
