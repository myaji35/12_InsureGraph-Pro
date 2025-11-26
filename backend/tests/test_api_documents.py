"""
Tests for Document API Endpoints

Story 3.2: Document Upload API 테스트
"""
import pytest
import io
from uuid import UUID, uuid4
from unittest.mock import Mock, patch
from datetime import datetime

from fastapi.testclient import TestClient
from fastapi import UploadFile

from app.main import app
from app.api.v1.models.document import (
    DocumentStatus,
    DocumentType,
    DocumentMetadata,
)


# TestClient
client = TestClient(app)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_pdf_file():
    """샘플 PDF 파일 생성"""
    # Create a small PDF-like file (not a real PDF, just for testing)
    content = b"%PDF-1.4\n" + b"Sample PDF content" * 100  # ~2KB
    return io.BytesIO(content)


@pytest.fixture
def large_pdf_file():
    """큰 PDF 파일 생성 (51MB)"""
    content = b"%PDF-1.4\n" + b"X" * (51 * 1024 * 1024)  # 51MB
    return io.BytesIO(content)


@pytest.fixture
def mock_document_metadata():
    """Mock DocumentMetadata"""
    doc_id = uuid4()
    user_id = uuid4()

    return DocumentMetadata(
        document_id=doc_id,
        insurer="삼성화재",
        product_name="무배당 삼성화재 슈퍼마일리지보험",
        product_code="P12345",
        launch_date="2023-01-15",
        description="종신보험 상품",
        document_type=DocumentType.INSURANCE_POLICY,
        tags=["종신보험", "CI", "암"],
        filename="samsung_supermileage.pdf",
        file_size_bytes=2458624,
        content_type="application/pdf",
        status=DocumentStatus.COMPLETED,
        total_pages=45,
        total_articles=123,
        parsing_confidence=0.96,
        gcs_uri=f"gs://insuregraph-policies/documents/{doc_id}.pdf",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        processed_at=datetime.now(),
        uploaded_by_user_id=user_id,
    )


# ============================================================================
# Test POST /api/v1/documents/upload
# ============================================================================


class TestDocumentUpload:
    """POST /api/v1/documents/upload 테스트"""

    def test_upload_success(self, sample_pdf_file):
        """정상 업로드"""
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", sample_pdf_file, "application/pdf")},
            data={
                "insurer": "삼성화재",
                "product_name": "테스트 상품",
                "product_code": "TEST001",
                "launch_date": "2023-01-15",
                "description": "테스트 설명",
                "document_type": "insurance_policy",
                "tags": "종신보험,CI,암",
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "document_id" in data
        assert "job_id" in data
        assert data["status"] == "processing"
        assert "gcs_uri" in data
        assert UUID(data["document_id"])  # Valid UUID
        assert UUID(data["job_id"])  # Valid UUID

    def test_upload_minimal_fields(self, sample_pdf_file):
        """최소 필수 필드만으로 업로드"""
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", sample_pdf_file, "application/pdf")},
            data={
                "insurer": "현대해상",
                "product_name": "테스트 상품",
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "processing"

    def test_upload_invalid_file_type(self):
        """잘못된 파일 타입"""
        content = b"Not a PDF file"
        file = io.BytesIO(content)

        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", file, "text/plain")},
            data={
                "insurer": "삼성화재",
                "product_name": "테스트 상품",
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "INVALID_FILE_TYPE" in data["detail"]["error_code"]

    def test_upload_file_too_large(self, large_pdf_file):
        """파일 크기 초과 (50MB 초과)"""
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("large.pdf", large_pdf_file, "application/pdf")},
            data={
                "insurer": "삼성화재",
                "product_name": "테스트 상품",
            }
        )

        assert response.status_code == 413
        data = response.json()
        assert "FILE_TOO_LARGE" in data["detail"]["error_code"]

    def test_upload_missing_required_fields(self, sample_pdf_file):
        """필수 필드 누락"""
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", sample_pdf_file, "application/pdf")},
            data={
                "insurer": "삼성화재",
                # product_name 누락
            }
        )

        assert response.status_code == 422  # Validation error

    def test_upload_with_tags(self, sample_pdf_file):
        """태그 포함 업로드"""
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", sample_pdf_file, "application/pdf")},
            data={
                "insurer": "삼성화재",
                "product_name": "테스트 상품",
                "tags": "종신보험, CI, 암, 뇌혈관",  # 공백 포함
            }
        )

        assert response.status_code == 201


# ============================================================================
# Test GET /api/v1/documents
# ============================================================================


class TestDocumentList:
    """GET /api/v1/documents 테스트"""

    def setup_method(self):
        """각 테스트 전에 문서 초기화"""
        # Clear documents
        from app.api.v1.endpoints.documents import _documents
        _documents.clear()

    def test_list_empty(self):
        """빈 문서 목록"""
        response = client.get("/api/v1/documents")

        assert response.status_code == 200
        data = response.json()
        assert data["documents"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    def test_list_with_documents(self, sample_pdf_file):
        """문서 목록 조회"""
        # Upload 3 documents
        for i in range(3):
            client.post(
                "/api/v1/documents/upload",
                files={"file": ("test.pdf", io.BytesIO(sample_pdf_file.read()), "application/pdf")},
                data={
                    "insurer": "삼성화재",
                    "product_name": f"테스트 상품 {i}",
                }
            )
            sample_pdf_file.seek(0)

        response = client.get("/api/v1/documents")

        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 3
        assert data["total"] == 3

    def test_list_pagination(self, sample_pdf_file):
        """페이지네이션"""
        # Upload 25 documents
        for i in range(25):
            client.post(
                "/api/v1/documents/upload",
                files={"file": ("test.pdf", io.BytesIO(sample_pdf_file.read()), "application/pdf")},
                data={
                    "insurer": "삼성화재",
                    "product_name": f"테스트 상품 {i}",
                }
            )
            sample_pdf_file.seek(0)

        # Page 1
        response = client.get("/api/v1/documents?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 10
        assert data["total"] == 25
        assert data["page"] == 1
        assert data["total_pages"] == 3

        # Page 2
        response = client.get("/api/v1/documents?page=2&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 10
        assert data["page"] == 2

        # Page 3
        response = client.get("/api/v1/documents?page=3&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 5
        assert data["page"] == 3

    def test_list_filter_by_insurer(self, sample_pdf_file):
        """보험사로 필터링"""
        # Upload documents from different insurers
        for insurer in ["삼성화재", "현대해상", "삼성화재"]:
            client.post(
                "/api/v1/documents/upload",
                files={"file": ("test.pdf", io.BytesIO(sample_pdf_file.read()), "application/pdf")},
                data={
                    "insurer": insurer,
                    "product_name": "테스트 상품",
                }
            )
            sample_pdf_file.seek(0)

        response = client.get("/api/v1/documents?insurer=삼성화재")

        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 2
        assert all(d["insurer"] == "삼성화재" for d in data["documents"])

    def test_list_search(self, sample_pdf_file):
        """상품명 검색"""
        # Upload documents
        products = ["슈퍼마일리지보험", "건강보험", "슈퍼실손보험"]
        for product in products:
            client.post(
                "/api/v1/documents/upload",
                files={"file": ("test.pdf", io.BytesIO(sample_pdf_file.read()), "application/pdf")},
                data={
                    "insurer": "삼성화재",
                    "product_name": product,
                }
            )
            sample_pdf_file.seek(0)

        response = client.get("/api/v1/documents?search=슈퍼")

        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 2
        assert all("슈퍼" in d["product_name"] for d in data["documents"])


# ============================================================================
# Test GET /api/v1/documents/{document_id}
# ============================================================================


class TestDocumentDetail:
    """GET /api/v1/documents/{document_id} 테스트"""

    def setup_method(self):
        """각 테스트 전에 문서 초기화"""
        from app.api.v1.endpoints.documents import _documents
        _documents.clear()

    def test_get_document_success(self, sample_pdf_file):
        """문서 조회 성공"""
        # Upload document
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", sample_pdf_file, "application/pdf")},
            data={
                "insurer": "삼성화재",
                "product_name": "테스트 상품",
            }
        )
        document_id = upload_response.json()["document_id"]

        # Get document
        response = client.get(f"/api/v1/documents/{document_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == document_id
        assert data["insurer"] == "삼성화재"
        assert data["product_name"] == "테스트 상품"

    def test_get_document_not_found(self):
        """존재하지 않는 문서"""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/documents/{fake_id}")

        assert response.status_code == 404
        data = response.json()
        assert "DOCUMENT_NOT_FOUND" in data["detail"]["error_code"]


# ============================================================================
# Test GET /api/v1/documents/{document_id}/content
# ============================================================================


class TestDocumentContent:
    """GET /api/v1/documents/{document_id}/content 테스트"""

    def setup_method(self):
        """각 테스트 전에 문서 초기화"""
        from app.api.v1.endpoints.documents import _documents
        _documents.clear()

    def test_get_content_success(self, sample_pdf_file):
        """컨텐츠 조회 성공"""
        # Upload and simulate processing
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", sample_pdf_file, "application/pdf")},
            data={
                "insurer": "삼성화재",
                "product_name": "테스트 상품",
            }
        )
        document_id = upload_response.json()["document_id"]

        # Simulate processing completion
        from app.api.v1.endpoints.documents import simulate_document_processing
        simulate_document_processing(UUID(document_id))

        # Get content
        response = client.get(f"/api/v1/documents/{document_id}/content")

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == document_id
        assert "articles" in data
        assert "total_pages" in data
        assert "total_articles" in data

    def test_get_content_not_ready(self, sample_pdf_file):
        """처리되지 않은 문서"""
        # Upload document (status: processing)
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", sample_pdf_file, "application/pdf")},
            data={
                "insurer": "삼성화재",
                "product_name": "테스트 상품",
            }
        )
        document_id = upload_response.json()["document_id"]

        # Try to get content before processing
        response = client.get(f"/api/v1/documents/{document_id}/content")

        assert response.status_code == 400
        data = response.json()
        assert "DOCUMENT_NOT_READY" in data["detail"]["error_code"]


# ============================================================================
# Test PATCH /api/v1/documents/{document_id}
# ============================================================================


class TestDocumentUpdate:
    """PATCH /api/v1/documents/{document_id} 테스트"""

    def setup_method(self):
        """각 테스트 전에 문서 초기화"""
        from app.api.v1.endpoints.documents import _documents
        _documents.clear()

    def test_update_success(self, sample_pdf_file):
        """메타데이터 수정 성공"""
        # Upload document
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", sample_pdf_file, "application/pdf")},
            data={
                "insurer": "삼성화재",
                "product_name": "테스트 상품",
            }
        )
        document_id = upload_response.json()["document_id"]

        # Update
        response = client.patch(
            f"/api/v1/documents/{document_id}",
            json={
                "product_name": "수정된 상품명",
                "description": "새로운 설명",
                "tags": ["태그1", "태그2"],
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["product_name"] == "수정된 상품명"
        assert data["description"] == "새로운 설명"
        assert "태그1" in data["tags"]

    def test_update_partial(self, sample_pdf_file):
        """부분 수정"""
        # Upload document
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", sample_pdf_file, "application/pdf")},
            data={
                "insurer": "삼성화재",
                "product_name": "테스트 상품",
            }
        )
        document_id = upload_response.json()["document_id"]

        # Update only product_name
        response = client.patch(
            f"/api/v1/documents/{document_id}",
            json={"product_name": "수정된 상품명"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["product_name"] == "수정된 상품명"
        assert data["insurer"] == "삼성화재"  # Unchanged


# ============================================================================
# Test DELETE /api/v1/documents/{document_id}
# ============================================================================


class TestDocumentDelete:
    """DELETE /api/v1/documents/{document_id} 테스트"""

    def setup_method(self):
        """각 테스트 전에 문서 초기화"""
        from app.api.v1.endpoints.documents import _documents
        _documents.clear()

    def test_delete_success(self, sample_pdf_file):
        """문서 삭제 성공"""
        # Upload document
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", sample_pdf_file, "application/pdf")},
            data={
                "insurer": "삼성화재",
                "product_name": "테스트 상품",
            }
        )
        document_id = upload_response.json()["document_id"]

        # Delete
        response = client.delete(f"/api/v1/documents/{document_id}")

        assert response.status_code == 204

        # Verify deleted
        get_response = client.get(f"/api/v1/documents/{document_id}")
        assert get_response.status_code == 404

    def test_delete_not_found(self):
        """존재하지 않는 문서 삭제"""
        fake_id = str(uuid4())
        response = client.delete(f"/api/v1/documents/{fake_id}")

        assert response.status_code == 404


# ============================================================================
# Test GET /api/v1/documents/stats/summary
# ============================================================================


class TestDocumentStats:
    """GET /api/v1/documents/stats/summary 테스트"""

    def setup_method(self):
        """각 테스트 전에 문서 초기화"""
        from app.api.v1.endpoints.documents import _documents
        _documents.clear()

    def test_stats_empty(self):
        """빈 통계"""
        response = client.get("/api/v1/documents/stats/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total_documents"] == 0

    def test_stats_with_documents(self, sample_pdf_file):
        """문서 통계 조회"""
        # Upload documents
        insurers = ["삼성화재", "현대해상", "삼성화재", "KB손해보험"]
        for insurer in insurers:
            client.post(
                "/api/v1/documents/upload",
                files={"file": ("test.pdf", io.BytesIO(sample_pdf_file.read()), "application/pdf")},
                data={
                    "insurer": insurer,
                    "product_name": "테스트 상품",
                }
            )
            sample_pdf_file.seek(0)

        response = client.get("/api/v1/documents/stats/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total_documents"] == 4
        assert "by_status" in data
        assert "by_insurer" in data
        assert "by_type" in data
        assert data["by_insurer"]["삼성화재"] == 2
        assert data["by_insurer"]["현대해상"] == 1


# ============================================================================
# Integration Tests
# ============================================================================


class TestDocumentAPIIntegration:
    """통합 테스트"""

    def setup_method(self):
        """각 테스트 전에 문서 초기화"""
        from app.api.v1.endpoints.documents import _documents
        _documents.clear()

    def test_full_document_lifecycle(self, sample_pdf_file):
        """문서 전체 라이프사이클 테스트"""
        # 1. Upload
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", sample_pdf_file, "application/pdf")},
            data={
                "insurer": "삼성화재",
                "product_name": "테스트 상품",
                "tags": "종신보험,CI",
            }
        )
        assert upload_response.status_code == 201
        document_id = upload_response.json()["document_id"]

        # 2. Get metadata
        get_response = client.get(f"/api/v1/documents/{document_id}")
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "processing"

        # 3. Simulate processing
        from app.api.v1.endpoints.documents import simulate_document_processing
        simulate_document_processing(UUID(document_id))

        # 4. Get content
        content_response = client.get(f"/api/v1/documents/{document_id}/content")
        assert content_response.status_code == 200
        assert len(content_response.json()["articles"]) > 0

        # 5. Update metadata
        update_response = client.patch(
            f"/api/v1/documents/{document_id}",
            json={"description": "Updated description"}
        )
        assert update_response.status_code == 200

        # 6. Check stats
        stats_response = client.get("/api/v1/documents/stats/summary")
        assert stats_response.status_code == 200
        assert stats_response.json()["total_documents"] == 1

        # 7. Delete
        delete_response = client.delete(f"/api/v1/documents/{document_id}")
        assert delete_response.status_code == 204

        # 8. Verify deleted
        final_get = client.get(f"/api/v1/documents/{document_id}")
        assert final_get.status_code == 404
