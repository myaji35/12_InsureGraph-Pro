"""
API Models for Document Management

Story 3.2: Document Upload API - 문서 관리 API 모델
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================


class DocumentStatus(str, Enum):
    """문서 처리 상태"""
    UPLOADING = "uploading"           # 업로드 중
    PROCESSING = "processing"          # 처리 중 (OCR, 파싱, 그래프 생성)
    COMPLETED = "completed"            # 처리 완료
    FAILED = "failed"                  # 처리 실패


class DocumentType(str, Enum):
    """문서 타입"""
    INSURANCE_POLICY = "insurance_policy"   # 보험 약관
    TERMS_CONDITIONS = "terms_conditions"   # 약관
    CERTIFICATE = "certificate"              # 증권
    CLAIM_FORM = "claim_form"                # 청구서
    OTHER = "other"                          # 기타


# ============================================================================
# Request Models
# ============================================================================


class DocumentUploadRequest(BaseModel):
    """문서 업로드 요청"""
    insurer: str = Field(..., min_length=1, max_length=100, description="보험사명")
    product_name: str = Field(..., min_length=1, max_length=200, description="상품명")
    product_code: Optional[str] = Field(None, max_length=50, description="상품코드")
    launch_date: Optional[str] = Field(None, description="출시일 (YYYY-MM-DD)")
    description: Optional[str] = Field(None, max_length=1000, description="설명")
    document_type: DocumentType = Field(
        default=DocumentType.INSURANCE_POLICY,
        description="문서 타입"
    )
    tags: List[str] = Field(default_factory=list, description="태그 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "insurer": "삼성화재",
                "product_name": "무배당 삼성화재 슈퍼마일리지보험",
                "product_code": "P12345",
                "launch_date": "2023-01-15",
                "description": "종신보험 상품",
                "document_type": "insurance_policy",
                "tags": ["종신보험", "CI", "암"]
            }
        }


class DocumentUpdateRequest(BaseModel):
    """문서 메타데이터 수정 요청"""
    product_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, description="태그 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "무배당 삼성화재 슈퍼마일리지보험 Ver2",
                "description": "갱신된 약관",
                "tags": ["종신보험", "CI", "암", "갱신"]
            }
        }


# ============================================================================
# Response Models
# ============================================================================


class DocumentMetadata(BaseModel):
    """문서 메타데이터"""
    document_id: UUID = Field(..., description="문서 ID")
    insurer: str = Field(..., description="보험사명")
    product_name: str = Field(..., description="상품명")
    product_code: Optional[str] = Field(None, description="상품코드")
    launch_date: Optional[str] = Field(None, description="출시일")
    description: Optional[str] = Field(None, description="설명")
    document_type: DocumentType = Field(..., description="문서 타입")
    tags: List[str] = Field(default_factory=list, description="태그")

    # File info
    filename: str = Field(..., description="원본 파일명")
    file_size_bytes: int = Field(..., description="파일 크기 (bytes)")
    content_type: str = Field(..., description="MIME 타입")
    file_hash: str = Field(..., description="파일 SHA-256 해시 (중복 체크용)")

    # Processing info
    status: DocumentStatus = Field(..., description="처리 상태")
    total_pages: Optional[int] = Field(None, description="총 페이지 수")
    total_articles: Optional[int] = Field(None, description="총 조항 수")
    parsing_confidence: Optional[float] = Field(None, description="파싱 신뢰도")

    # Storage info
    gcs_uri: str = Field(..., description="GCS 저장 경로")

    # Timestamps
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    processed_at: Optional[datetime] = Field(None, description="처리 완료일시")

    # User info
    uploaded_by_user_id: UUID = Field(..., description="업로드한 사용자 ID")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "insurer": "삼성화재",
                "product_name": "무배당 삼성화재 슈퍼마일리지보험",
                "product_code": "P12345",
                "launch_date": "2023-01-15",
                "description": "종신보험 상품",
                "document_type": "insurance_policy",
                "tags": ["종신보험", "CI", "암"],
                "filename": "samsung_supermileage.pdf",
                "file_size_bytes": 2458624,
                "content_type": "application/pdf",
                "status": "completed",
                "total_pages": 45,
                "total_articles": 123,
                "parsing_confidence": 0.96,
                "gcs_uri": "gs://insuregraph-policies/documents/123e4567-e89b.pdf",
                "created_at": "2025-11-25T10:30:00",
                "updated_at": "2025-11-25T10:35:00",
                "processed_at": "2025-11-25T10:35:00",
                "uploaded_by_user_id": "987e6543-e21b-12d3-a456-426614174000"
            }
        }


class DocumentUploadResponse(BaseModel):
    """문서 업로드 응답"""
    document_id: UUID = Field(..., description="문서 ID")
    job_id: UUID = Field(..., description="처리 작업 ID")
    status: DocumentStatus = Field(..., description="처리 상태")
    message: str = Field(..., description="상태 메시지")
    gcs_uri: str = Field(..., description="GCS 저장 경로")
    created_at: datetime = Field(..., description="생성일시")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "job_id": "abc12345-e89b-12d3-a456-426614174000",
                "status": "processing",
                "message": "Document uploaded successfully. Processing in progress.",
                "gcs_uri": "gs://insuregraph-policies/documents/123e4567-e89b.pdf",
                "created_at": "2025-11-25T10:30:00"
            }
        }


class DocumentListItem(BaseModel):
    """문서 목록 항목"""
    document_id: UUID
    insurer: str
    product_name: str
    product_code: Optional[str]
    document_type: DocumentType
    status: DocumentStatus
    total_pages: Optional[int]
    filename: str
    file_size_bytes: int
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "insurer": "삼성화재",
                "product_name": "무배당 삼성화재 슈퍼마일리지보험",
                "product_code": "P12345",
                "document_type": "insurance_policy",
                "status": "completed",
                "total_pages": 45,
                "filename": "samsung_supermileage.pdf",
                "file_size_bytes": 2458624,
                "created_at": "2025-11-25T10:30:00",
                "updated_at": "2025-11-25T10:35:00"
            }
        }


class DocumentListResponse(BaseModel):
    """문서 목록 응답"""
    documents: List[DocumentListItem] = Field(..., description="문서 목록")
    total: int = Field(..., description="전체 문서 수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지 크기")
    total_pages: int = Field(..., description="전체 페이지 수")

    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    {
                        "document_id": "123e4567-e89b-12d3-a456-426614174000",
                        "insurer": "삼성화재",
                        "product_name": "무배당 삼성화재 슈퍼마일리지보험",
                        "product_code": "P12345",
                        "document_type": "insurance_policy",
                        "status": "completed",
                        "total_pages": 45,
                        "filename": "samsung_supermileage.pdf",
                        "file_size_bytes": 2458624,
                        "created_at": "2025-11-25T10:30:00",
                        "updated_at": "2025-11-25T10:35:00"
                    }
                ],
                "total": 150,
                "page": 1,
                "page_size": 20,
                "total_pages": 8
            }
        }


class DocumentContentResponse(BaseModel):
    """문서 컨텐츠 응답"""
    document_id: UUID = Field(..., description="문서 ID")
    insurer: str = Field(..., description="보험사명")
    product_name: str = Field(..., description="상품명")

    # Parsed content
    total_pages: int = Field(..., description="총 페이지 수")
    total_articles: int = Field(..., description="총 조항 수")
    total_paragraphs: int = Field(..., description="총 단락 수")
    parsing_confidence: float = Field(..., description="파싱 신뢰도")

    # Articles (simplified for API - full structure available via separate endpoint)
    articles: List[Dict[str, Any]] = Field(..., description="조항 목록")

    # Metadata
    created_at: datetime = Field(..., description="생성일시")
    processed_at: datetime = Field(..., description="처리 완료일시")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "insurer": "삼성화재",
                "product_name": "무배당 삼성화재 슈퍼마일리지보험",
                "total_pages": 45,
                "total_articles": 123,
                "total_paragraphs": 456,
                "parsing_confidence": 0.96,
                "articles": [
                    {
                        "article_num": "제1조",
                        "title": "용어의 정의",
                        "page": 5,
                        "paragraph_count": 3
                    }
                ],
                "created_at": "2025-11-25T10:30:00",
                "processed_at": "2025-11-25T10:35:00"
            }
        }


class DocumentStatsResponse(BaseModel):
    """문서 통계 응답"""
    total_documents: int = Field(..., description="전체 문서 수")
    by_status: Dict[str, int] = Field(..., description="상태별 문서 수")
    by_insurer: Dict[str, int] = Field(..., description="보험사별 문서 수")
    by_type: Dict[str, int] = Field(..., description="타입별 문서 수")
    total_pages: int = Field(..., description="전체 페이지 수")
    total_articles: int = Field(..., description="전체 조항 수")

    class Config:
        json_schema_extra = {
            "example": {
                "total_documents": 150,
                "by_status": {
                    "completed": 145,
                    "processing": 3,
                    "failed": 2
                },
                "by_insurer": {
                    "삼성화재": 45,
                    "현대해상": 38,
                    "KB손해보험": 32
                },
                "by_type": {
                    "insurance_policy": 120,
                    "terms_conditions": 25,
                    "other": 5
                },
                "total_pages": 6750,
                "total_articles": 18450
            }
        }


class ProcessingJobStatus(BaseModel):
    """문서 처리 작업 진행 상태"""
    job_id: UUID = Field(..., description="작업 ID")
    document_id: UUID = Field(..., description="문서 ID")
    status: str = Field(..., description="작업 상태 (processing, completed, failed)")
    current_step: Optional[str] = Field(None, description="현재 처리 중인 단계")
    progress_percentage: int = Field(..., description="진행률 (0-100)")
    steps_completed: List[str] = Field(default_factory=list, description="완료된 단계 목록")
    error_message: Optional[str] = Field(None, description="에러 메시지 (실패 시)")
    started_at: datetime = Field(..., description="작업 시작 시각")
    updated_at: datetime = Field(..., description="마지막 업데이트 시각")
    completed_at: Optional[datetime] = Field(None, description="작업 완료 시각")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "abc12345-e89b-12d3-a456-426614174000",
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "processing",
                "current_step": "임베딩 생성 중",
                "progress_percentage": 65,
                "steps_completed": ["OCR 완료", "파싱 완료"],
                "error_message": None,
                "started_at": "2025-11-26T20:00:00",
                "updated_at": "2025-11-26T20:02:30",
                "completed_at": None
            }
        }


# ============================================================================
# Error Models
# ============================================================================


class DocumentErrorResponse(BaseModel):
    """문서 API 에러 응답"""
    error_code: str = Field(..., description="에러 코드")
    error_message: str = Field(..., description="에러 메시지")
    details: Optional[Dict[str, Any]] = Field(None, description="상세 정보")
    timestamp: datetime = Field(default_factory=datetime.now, description="에러 발생 시각")
    document_id: Optional[UUID] = Field(None, description="문서 ID (있는 경우)")

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "DOCUMENT_NOT_FOUND",
                "error_message": "Document with ID '123e4567-e89b-12d3-a456-426614174000' not found",
                "details": {"requested_id": "123e4567-e89b-12d3-a456-426614174000"},
                "timestamp": "2025-11-25T10:30:00",
                "document_id": None
            }
        }
