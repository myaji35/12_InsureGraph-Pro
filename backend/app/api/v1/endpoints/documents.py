"""
Document Management API Endpoints

Story 3.2: Document Upload API - 문서 관리 엔드포인트
"""
import hashlib
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.v1.models.document import (
    DocumentUploadRequest,
    DocumentUploadResponse,
    DocumentMetadata,
    DocumentListResponse,
    DocumentListItem,
    DocumentContentResponse,
    DocumentUpdateRequest,
    DocumentStatsResponse,
    DocumentErrorResponse,
    DocumentStatus,
    DocumentType,
)


# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/documents", tags=["Documents"])


# ============================================================================
# In-Memory Storage (Temporary - replace with database in production)
# ============================================================================

# Simulated document storage
_documents: dict[UUID, DocumentMetadata] = {}


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="문서 업로드",
    description="""
    보험 약관 문서를 업로드하고 처리를 시작합니다.

    업로드된 문서는 다음 단계를 거칩니다:
    1. 파일 검증 (PDF, 최대 50MB)
    2. 저장소 업로드 (GCS)
    3. OCR 처리
    4. 구조 파싱
    5. 지식 그래프 생성

    **Returns**: 문서 ID와 처리 작업 ID를 포함한 응답
    """,
    responses={
        201: {"description": "문서 업로드 성공"},
        400: {"model": DocumentErrorResponse, "description": "잘못된 파일 또는 파라미터"},
        413: {"description": "파일 크기 초과 (최대 50MB)"},
        500: {"model": DocumentErrorResponse, "description": "서버 에러"},
    },
)
async def upload_document(
    file: UploadFile = File(..., description="업로드할 PDF 파일 (최대 50MB)"),
    insurer: str = Form(..., description="보험사명"),
    product_name: str = Form(..., description="상품명"),
    product_code: Optional[str] = Form(None, description="상품코드"),
    launch_date: Optional[str] = Form(None, description="출시일 (YYYY-MM-DD)"),
    description: Optional[str] = Form(None, description="설명"),
    document_type: str = Form("insurance_policy", description="문서 타입"),
    tags: Optional[str] = Form(None, description="태그 (쉼표로 구분)"),
) -> DocumentUploadResponse:
    """
    문서 업로드

    PDF 파일을 업로드하고 처리 작업을 시작합니다.
    """
    # 1. Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_FILE_TYPE",
                "error_message": "Only PDF files are supported",
                "details": {"content_type": file.content_type}
            }
        )

    # 2. Validate file size (max 50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    file_content = await file.read()
    file_size_bytes = len(file_content)

    if file_size_bytes > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error_code": "FILE_TOO_LARGE",
                "error_message": f"File too large. Maximum size is 50MB, got {file_size_bytes / (1024*1024):.2f}MB",
                "details": {"file_size_mb": file_size_bytes / (1024*1024), "max_size_mb": 50}
            }
        )

    # Reset file pointer
    await file.seek(0)

    try:
        # 3. Generate IDs
        document_id = uuid4()
        job_id = uuid4()

        # 4. Parse tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        # 5. Simulate GCS upload (in production, use actual GCS service)
        gcs_uri = f"gs://insuregraph-policies/documents/{document_id}.pdf"

        # 6. Create document metadata
        now = datetime.now()
        # Simulate user ID (in production, get from auth)
        user_id = uuid4()

        document_metadata = DocumentMetadata(
            document_id=document_id,
            insurer=insurer,
            product_name=product_name,
            product_code=product_code,
            launch_date=launch_date,
            description=description,
            document_type=DocumentType(document_type),
            tags=tag_list,
            filename=file.filename or "unknown.pdf",
            file_size_bytes=file_size_bytes,
            content_type=file.content_type or "application/pdf",
            status=DocumentStatus.PROCESSING,
            total_pages=None,  # Will be set after OCR
            total_articles=None,  # Will be set after parsing
            parsing_confidence=None,  # Will be set after parsing
            gcs_uri=gcs_uri,
            created_at=now,
            updated_at=now,
            processed_at=None,
            uploaded_by_user_id=user_id,
        )

        # 7. Store document metadata
        _documents[document_id] = document_metadata

        logger.info(f"Document uploaded: {document_id} - {product_name}")

        # 8. In production: Trigger async processing
        # await trigger_ingestion_pipeline(document_id, job_id, gcs_uri)

        # 9. Return response
        return DocumentUploadResponse(
            document_id=document_id,
            job_id=job_id,
            status=DocumentStatus.PROCESSING,
            message="Document uploaded successfully. Processing in progress.",
            gcs_uri=gcs_uri,
            created_at=now,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "error_message": str(e),
                "details": {}
            }
        )
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "UPLOAD_FAILED",
                "error_message": f"Failed to upload document: {str(e)}",
                "details": {}
            }
        )


@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="문서 목록 조회",
    description="""
    업로드된 문서 목록을 조회합니다.

    **Filters**:
    - insurer: 보험사명으로 필터링
    - status: 처리 상태로 필터링
    - document_type: 문서 타입으로 필터링
    - search: 상품명 검색

    **Pagination**:
    - page: 페이지 번호 (기본값: 1)
    - page_size: 페이지 크기 (기본값: 20, 최대: 100)
    """,
)
async def list_documents(
    insurer: Optional[str] = Query(None, description="보험사명 필터"),
    status_filter: Optional[DocumentStatus] = Query(None, description="상태 필터", alias="status"),
    document_type: Optional[DocumentType] = Query(None, description="문서 타입 필터"),
    search: Optional[str] = Query(None, description="상품명 검색"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
) -> DocumentListResponse:
    """
    문서 목록 조회

    필터링과 페이지네이션을 지원합니다.
    """
    # 1. Filter documents
    filtered_docs = list(_documents.values())

    if insurer:
        filtered_docs = [d for d in filtered_docs if d.insurer == insurer]

    if status_filter:
        filtered_docs = [d for d in filtered_docs if d.status == status_filter]

    if document_type:
        filtered_docs = [d for d in filtered_docs if d.document_type == document_type]

    if search:
        search_lower = search.lower()
        filtered_docs = [
            d for d in filtered_docs
            if search_lower in d.product_name.lower() or
               (d.description and search_lower in d.description.lower())
        ]

    # 2. Sort by created_at (descending)
    filtered_docs.sort(key=lambda d: d.created_at, reverse=True)

    # 3. Pagination
    total = len(filtered_docs)
    total_pages = (total + page_size - 1) // page_size  # Ceiling division

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_docs = filtered_docs[start_idx:end_idx]

    # 4. Convert to list items
    items = [
        DocumentListItem(
            document_id=doc.document_id,
            insurer=doc.insurer,
            product_name=doc.product_name,
            product_code=doc.product_code,
            document_type=doc.document_type,
            status=doc.status,
            total_pages=doc.total_pages,
            filename=doc.filename,
            file_size_bytes=doc.file_size_bytes,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
        for doc in page_docs
    ]

    return DocumentListResponse(
        documents=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentMetadata,
    status_code=status.HTTP_200_OK,
    summary="문서 메타데이터 조회",
    description="문서 ID로 메타데이터를 조회합니다.",
    responses={
        200: {"description": "문서 조회 성공"},
        404: {"model": DocumentErrorResponse, "description": "문서를 찾을 수 없음"},
    },
)
async def get_document(document_id: UUID) -> DocumentMetadata:
    """
    문서 메타데이터 조회

    문서 ID로 메타데이터를 조회합니다.
    """
    if document_id not in _documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "DOCUMENT_NOT_FOUND",
                "error_message": f"Document with ID '{document_id}' not found",
                "details": {"requested_id": str(document_id)},
                "document_id": None,
            }
        )

    return _documents[document_id]


@router.get(
    "/{document_id}/content",
    response_model=DocumentContentResponse,
    status_code=status.HTTP_200_OK,
    summary="문서 컨텐츠 조회",
    description="""
    문서의 파싱된 컨텐츠를 조회합니다.

    조항 목록과 구조화된 정보를 포함합니다.
    """,
    responses={
        200: {"description": "컨텐츠 조회 성공"},
        404: {"model": DocumentErrorResponse, "description": "문서를 찾을 수 없음"},
        400: {"model": DocumentErrorResponse, "description": "문서 처리 미완료"},
    },
)
async def get_document_content(document_id: UUID) -> DocumentContentResponse:
    """
    문서 컨텐츠 조회

    파싱된 조항과 구조화된 데이터를 조회합니다.
    """
    if document_id not in _documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "DOCUMENT_NOT_FOUND",
                "error_message": f"Document with ID '{document_id}' not found",
                "details": {"requested_id": str(document_id)},
            }
        )

    doc = _documents[document_id]

    # Check if document is processed
    if doc.status != DocumentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "DOCUMENT_NOT_READY",
                "error_message": f"Document is not ready. Current status: {doc.status.value}",
                "details": {"status": doc.status.value},
            }
        )

    # In production: Fetch parsed content from database/storage
    # For now, return simulated data
    articles = [
        {
            "article_num": "제1조",
            "title": "용어의 정의",
            "page": 5,
            "paragraph_count": 3,
        },
        {
            "article_num": "제2조",
            "title": "보장의 종류",
            "page": 7,
            "paragraph_count": 5,
        },
        {
            "article_num": "제3조",
            "title": "보장의 내용",
            "page": 9,
            "paragraph_count": 8,
        },
    ]

    return DocumentContentResponse(
        document_id=doc.document_id,
        insurer=doc.insurer,
        product_name=doc.product_name,
        total_pages=doc.total_pages or 0,
        total_articles=doc.total_articles or 0,
        total_paragraphs=doc.total_articles * 3 if doc.total_articles else 0,  # Estimate
        parsing_confidence=doc.parsing_confidence or 0.0,
        articles=articles,
        created_at=doc.created_at,
        processed_at=doc.processed_at or doc.updated_at,
    )


@router.patch(
    "/{document_id}",
    response_model=DocumentMetadata,
    status_code=status.HTTP_200_OK,
    summary="문서 메타데이터 수정",
    description="문서의 메타데이터를 수정합니다.",
    responses={
        200: {"description": "수정 성공"},
        404: {"model": DocumentErrorResponse, "description": "문서를 찾을 수 없음"},
    },
)
async def update_document(
    document_id: UUID,
    update_request: DocumentUpdateRequest,
) -> DocumentMetadata:
    """
    문서 메타데이터 수정

    상품명, 설명, 태그 등을 수정할 수 있습니다.
    """
    if document_id not in _documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "DOCUMENT_NOT_FOUND",
                "error_message": f"Document with ID '{document_id}' not found",
                "details": {"requested_id": str(document_id)},
            }
        )

    doc = _documents[document_id]

    # Update fields
    if update_request.product_name is not None:
        doc.product_name = update_request.product_name
    if update_request.description is not None:
        doc.description = update_request.description
    if update_request.tags is not None:
        doc.tags = update_request.tags

    doc.updated_at = datetime.now()

    logger.info(f"Document updated: {document_id}")

    return doc


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="문서 삭제",
    description="""
    문서를 삭제합니다.

    메타데이터와 저장된 파일을 모두 삭제합니다.
    """,
    responses={
        204: {"description": "삭제 성공"},
        404: {"model": DocumentErrorResponse, "description": "문서를 찾을 수 없음"},
        500: {"model": DocumentErrorResponse, "description": "서버 에러"},
    },
)
async def delete_document(document_id: UUID):
    """
    문서 삭제

    메타데이터와 저장소의 파일을 모두 삭제합니다.
    """
    if document_id not in _documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "DOCUMENT_NOT_FOUND",
                "error_message": f"Document with ID '{document_id}' not found",
                "details": {"requested_id": str(document_id)},
            }
        )

    try:
        doc = _documents[document_id]

        # In production: Delete from GCS
        # await gcs_service.delete_file(doc.gcs_uri)

        # In production: Delete from database (cascade delete related data)
        # await db.delete_document(document_id)

        # Delete from in-memory storage
        del _documents[document_id]

        logger.info(f"Document deleted: {document_id} - {doc.product_name}")

        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None
        )

    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DELETE_FAILED",
                "error_message": f"Failed to delete document: {str(e)}",
                "details": {},
            }
        )


@router.get(
    "/stats/summary",
    response_model=DocumentStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="문서 통계 조회",
    description="전체 문서 통계를 조회합니다.",
)
async def get_document_stats() -> DocumentStatsResponse:
    """
    문서 통계 조회

    전체 문서 수, 상태별/보험사별/타입별 분포 등을 조회합니다.
    """
    docs = list(_documents.values())

    # Total count
    total_documents = len(docs)

    # Count by status
    by_status = {}
    for status_value in DocumentStatus:
        count = sum(1 for d in docs if d.status == status_value)
        if count > 0:
            by_status[status_value.value] = count

    # Count by insurer
    by_insurer = {}
    for doc in docs:
        by_insurer[doc.insurer] = by_insurer.get(doc.insurer, 0) + 1

    # Count by type
    by_type = {}
    for type_value in DocumentType:
        count = sum(1 for d in docs if d.document_type == type_value)
        if count > 0:
            by_type[type_value.value] = count

    # Total pages and articles
    total_pages = sum(d.total_pages or 0 for d in docs)
    total_articles = sum(d.total_articles or 0 for d in docs)

    return DocumentStatsResponse(
        total_documents=total_documents,
        by_status=by_status,
        by_insurer=by_insurer,
        by_type=by_type,
        total_pages=total_pages,
        total_articles=total_articles,
    )


# ============================================================================
# Helper Functions
# ============================================================================


async def trigger_ingestion_pipeline(document_id: UUID, job_id: UUID, gcs_uri: str):
    """
    트리거 인제스트 파이프라인 (비동기)

    In production: This would enqueue a job to process the document through:
    1. OCR
    2. Parsing
    3. Entity extraction
    4. Graph construction
    """
    # Placeholder for async pipeline triggering
    logger.info(f"Triggering ingestion pipeline for document {document_id}, job {job_id}")
    pass


def simulate_document_processing(document_id: UUID):
    """
    문서 처리 시뮬레이션

    For testing: simulate document processing completion
    """
    if document_id in _documents:
        doc = _documents[document_id]
        doc.status = DocumentStatus.COMPLETED
        doc.total_pages = 45
        doc.total_articles = 123
        doc.parsing_confidence = 0.96
        doc.processed_at = datetime.now()
        doc.updated_at = datetime.now()
        logger.info(f"Document processing completed (simulated): {document_id}")
