"""
Document Management API Endpoints

Story 3.2: Document Upload API - 문서 관리 엔드포인트
"""
import hashlib
import threading
import time
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from loguru import logger
import psycopg2
from psycopg2.extras import RealDictCursor

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
    ProcessingJobStatus,
)
from app.core.database import get_pg_connection, get_pg_pool, neo4j_manager
from app.services.pdf_processor import pdf_processor
from app.services.knowledge_graph import create_knowledge_graph
# Temporarily disabled Celery to fix server restart loop
# from app.tasks.document_processing import process_document


# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/documents", tags=["Documents"])


# ============================================================================
# Database Helper Functions
# ============================================================================


def _row_to_document_metadata(row: dict) -> DocumentMetadata:
    """Convert database row to DocumentMetadata model"""
    return DocumentMetadata(
        document_id=row['document_id'],
        insurer=row['insurer'],
        product_name=row['product_name'],
        product_code=row['product_code'],
        launch_date=row['launch_date'],
        description=row['description'],
        document_type=DocumentType(row['document_type']),
        tags=row['tags'] or [],
        filename=row['filename'],
        file_size_bytes=row['file_size_bytes'],
        content_type=row['content_type'],
        file_hash=row['file_hash'],
        status=DocumentStatus(row['status']),
        total_pages=row['total_pages'],
        total_articles=row['total_articles'],
        parsing_confidence=row['parsing_confidence'],
        gcs_uri=row['gcs_uri'],
        created_at=row['created_at'],
        updated_at=row['updated_at'],
        processed_at=row['processed_at'],
        uploaded_by_user_id=row['uploaded_by_user_id'],
    )


def _insert_document(conn, doc: DocumentMetadata) -> None:
    """Insert document into database"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO documents (
                document_id, insurer, product_name, product_code, launch_date,
                description, document_type, tags, filename, file_size_bytes,
                content_type, file_hash, status, total_pages, total_articles,
                parsing_confidence, gcs_uri, created_at, updated_at, processed_at,
                uploaded_by_user_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            str(doc.document_id), doc.insurer, doc.product_name, doc.product_code, doc.launch_date,
            doc.description, doc.document_type.value, doc.tags, doc.filename, doc.file_size_bytes,
            doc.content_type, doc.file_hash, doc.status.value, doc.total_pages, doc.total_articles,
            doc.parsing_confidence, doc.gcs_uri, doc.created_at, doc.updated_at, doc.processed_at,
            str(doc.uploaded_by_user_id)
        ))
        conn.commit()


def _get_document_by_id(conn, document_id: UUID) -> Optional[DocumentMetadata]:
    """Get document by ID"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM documents WHERE document_id = %s", (str(document_id),))
        row = cur.fetchone()
        if row:
            return _row_to_document_metadata(dict(row))
        return None


def _get_document_by_hash(conn, file_hash: str) -> Optional[DocumentMetadata]:
    """Get document by file hash"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM documents WHERE file_hash = %s", (file_hash,))
        row = cur.fetchone()
        if row:
            return _row_to_document_metadata(dict(row))
        return None


def _get_document_by_product(conn, insurer: str, product_name: str, product_code: Optional[str]) -> Optional[DocumentMetadata]:
    """Get document by product details"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT * FROM documents
            WHERE insurer = %s AND product_name = %s AND product_code = %s
        """, (insurer, product_name, product_code))
        row = cur.fetchone()
        if row:
            return _row_to_document_metadata(dict(row))
        return None


def _list_documents_filtered(
    conn,
    insurer: Optional[str] = None,
    status_filter: Optional[DocumentStatus] = None,
    document_type: Optional[DocumentType] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[DocumentMetadata], int]:
    """List documents with filters and pagination"""

    # Build WHERE clause
    where_conditions = []
    params = []

    if insurer:
        where_conditions.append("insurer = %s")
        params.append(insurer)

    if status_filter:
        where_conditions.append("status = %s")
        params.append(status_filter.value)

    if document_type:
        where_conditions.append("document_type = %s")
        params.append(document_type.value)

    if search:
        where_conditions.append("(LOWER(product_name) LIKE %s OR LOWER(description) LIKE %s)")
        search_pattern = f"%{search.lower()}%"
        params.extend([search_pattern, search_pattern])

    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get total count
        cur.execute(f"SELECT COUNT(*) as count FROM documents WHERE {where_clause}", params)
        total = cur.fetchone()['count']

        # Get paginated results
        offset = (page - 1) * page_size
        cur.execute(f"""
            SELECT * FROM documents
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, params + [page_size, offset])

        rows = cur.fetchall()
        documents = [_row_to_document_metadata(dict(row)) for row in rows]

        return documents, total


def _update_document_metadata(conn, document_id: UUID, product_name: Optional[str], description: Optional[str], tags: Optional[List[str]]) -> None:
    """Update document metadata"""
    updates = []
    params = []

    if product_name is not None:
        updates.append("product_name = %s")
        params.append(product_name)

    if description is not None:
        updates.append("description = %s")
        params.append(description)

    if tags is not None:
        updates.append("tags = %s")
        params.append(tags)

    if updates:
        updates.append("updated_at = %s")
        params.append(datetime.now())
        params.append(str(document_id))

        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE documents
                SET {", ".join(updates)}
                WHERE document_id = %s
            """, params)
            conn.commit()


def _delete_document_by_id(conn, document_id: UUID) -> bool:
    """Delete document by ID"""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM documents WHERE document_id = %s", (str(document_id),))
        conn.commit()
        return cur.rowcount > 0


def _get_document_stats(conn) -> dict:
    """Get document statistics"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Total count
        cur.execute("SELECT COUNT(*) as total FROM documents")
        total = cur.fetchone()['total']

        # By status
        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM documents
            GROUP BY status
        """)
        by_status = {row['status']: row['count'] for row in cur.fetchall()}

        # By insurer
        cur.execute("""
            SELECT insurer, COUNT(*) as count
            FROM documents
            GROUP BY insurer
        """)
        by_insurer = {row['insurer']: row['count'] for row in cur.fetchall()}

        # By type
        cur.execute("""
            SELECT document_type, COUNT(*) as count
            FROM documents
            GROUP BY document_type
        """)
        by_type = {row['document_type']: row['count'] for row in cur.fetchall()}

        # Total pages and articles
        cur.execute("""
            SELECT
                COALESCE(SUM(total_pages), 0) as total_pages,
                COALESCE(SUM(total_articles), 0) as total_articles
            FROM documents
        """)
        sums = cur.fetchone()

        return {
            'total_documents': total,
            'by_status': by_status,
            'by_insurer': by_insurer,
            'by_type': by_type,
            'total_pages': sums['total_pages'],
            'total_articles': sums['total_articles']
        }


def _update_document_processing_status(conn, document_id: UUID, status: DocumentStatus,
                                       total_pages: Optional[int] = None,
                                       total_articles: Optional[int] = None,
                                       parsing_confidence: Optional[float] = None) -> None:
    """Update document processing status"""
    now = datetime.now()
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE documents
            SET status = %s,
                total_pages = COALESCE(%s, total_pages),
                total_articles = COALESCE(%s, total_articles),
                parsing_confidence = COALESCE(%s, parsing_confidence),
                processed_at = %s,
                updated_at = %s
            WHERE document_id = %s
        """, (status.value, total_pages, total_articles, parsing_confidence, now, now, str(document_id)))
        conn.commit()


def _background_process_document(job_id: str, document_id: str, gcs_uri: str):
    """
    백그라운드 문서 처리 함수 (Threading 기반)

    pdfplumber + Claude API 파이프라인으로 실제 PDF 처리

    Args:
        job_id: 작업 ID
        document_id: 문서 ID
        gcs_uri: GCS 파일 경로 (실제 환경에서는 GCS에서 다운로드)
    """
    import asyncio
    from psycopg2.extras import RealDictCursor

    conn = None
    pool = None
    neo4j_session = None

    try:
        # Get connection from pool
        pool = get_pg_pool()
        conn = pool.getconn()

        job_uuid = UUID(job_id)
        doc_uuid = UUID(document_id)

        logger.info(f"Starting PDF processing with pdfplumber + Claude API: job={job_id}, document={document_id}")

        # 문서 정보 조회 (insurer, product_name 등)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT insurer, product_name, product_code, filename FROM documents WHERE document_id = %s",
                (str(doc_uuid),)
            )
            doc_info = cur.fetchone()

        if not doc_info:
            raise Exception(f"Document {document_id} not found in database")

        # 1단계: PDF 파일 준비 (5%)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE processing_jobs
                SET current_step = %s, progress_percentage = %s,
                    steps_completed = %s, updated_at = NOW()
                WHERE job_id = %s
                """,
                ("PDF 파일 로딩 중...", 5, [], str(job_uuid))
            )
            conn.commit()

        # TODO: 실제 환경에서는 GCS에서 파일 다운로드
        # 현재는 로컬 임시 파일 사용 (테스트용)
        # pdf_path = download_from_gcs(gcs_uri)
        pdf_path = f"/tmp/{doc_uuid}.pdf"  # Placeholder

        # 2단계: PDF 텍스트 추출 (10-30%)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE processing_jobs
                SET current_step = %s, progress_percentage = %s,
                    steps_completed = %s, updated_at = NOW()
                WHERE job_id = %s
                """,
                ("PDF 텍스트 추출 중 (pdfplumber)...", 10, ["파일 로딩 완료"], str(job_uuid))
            )
            conn.commit()

        # pdfplumber로 PDF 처리 (async 함수를 동기적으로 실행)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(pdf_processor.process_pdf(pdf_path))
        finally:
            loop.close()

        total_pages = result.total_pages
        total_articles = result.total_articles
        parsing_confidence = result.parsing_confidence

        logger.info(f"PDF processing completed: {total_pages} pages, {total_articles} articles, confidence={parsing_confidence}")

        # 3단계: 조항 파싱 완료 (35%)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE processing_jobs
                SET current_step = %s, progress_percentage = %s,
                    steps_completed = %s, updated_at = NOW()
                WHERE job_id = %s
                """,
                (f"조항 파싱 완료 ({total_articles}개 조항)", 35, ["파일 로딩 완료", "텍스트 추출 완료"], str(job_uuid))
            )
            conn.commit()

        # 4단계: Claude API 엔티티 추출 (40-70%)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE processing_jobs
                SET current_step = %s, progress_percentage = %s,
                    steps_completed = %s, updated_at = NOW()
                WHERE job_id = %s
                """,
                (f"Claude API 엔티티 추출 중 ({len(result.entities)}개 엔티티)...", 70,
                 ["파일 로딩 완료", "텍스트 추출 완료", "조항 파싱 완료"], str(job_uuid))
            )
            conn.commit()

        # 5단계: Neo4j 지식 그래프 생성 (75-90%)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE processing_jobs
                SET current_step = %s, progress_percentage = %s,
                    steps_completed = %s, updated_at = NOW()
                WHERE job_id = %s
                """,
                ("Neo4j 지식 그래프 생성 중...", 75,
                 ["파일 로딩 완료", "텍스트 추출 완료", "조항 파싱 완료", "엔티티 추출 완료"], str(job_uuid))
            )
            conn.commit()

        # Neo4j 세션 생성 및 그래프 생성
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Neo4j 세션 가져오기
            async def create_graph_async():
                async with neo4j_manager.get_session() as session:
                    return await create_knowledge_graph(
                        session,
                        doc_uuid,
                        doc_info['insurer'],
                        doc_info['product_name'],
                        doc_info.get('product_code'),
                        result.articles,
                        result.entities
                    )

            graph_stats = loop.run_until_complete(create_graph_async())
            logger.info(f"Knowledge graph created: {graph_stats}")

        finally:
            loop.close()

        # 6단계: 문서 메타데이터 업데이트 (95%)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE processing_jobs
                SET current_step = %s, progress_percentage = %s,
                    steps_completed = %s, updated_at = NOW()
                WHERE job_id = %s
                """,
                ("메타데이터 업데이트 중...", 95,
                 ["파일 로딩 완료", "텍스트 추출 완료", "조항 파싱 완료", "엔티티 추출 완료", "그래프 생성 완료"],
                 str(job_uuid))
            )
            conn.commit()

        # 문서 메타데이터 업데이트
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE documents
                SET total_pages = %s,
                    total_articles = %s,
                    parsing_confidence = %s,
                    updated_at = NOW()
                WHERE document_id = %s
                """,
                (total_pages, total_articles, parsing_confidence, str(doc_uuid))
            )
            conn.commit()

        # 7단계: 완료 (100%)
        with conn.cursor() as cur:
            # Update job status
            cur.execute(
                """
                UPDATE processing_jobs
                SET status = 'completed',
                    current_step = '처리 완료',
                    progress_percentage = 100,
                    updated_at = NOW(),
                    completed_at = NOW()
                WHERE job_id = %s
                """,
                (str(job_uuid),)
            )
            # Update document status
            cur.execute(
                """
                UPDATE documents
                SET status = 'completed',
                    processed_at = NOW(),
                    updated_at = NOW()
                WHERE document_id = %s
                """,
                (str(doc_uuid),)
            )
            conn.commit()

        logger.info(f"Document processing completed successfully: {document_id}")

    except Exception as e:
        logger.exception(f"Background document processing failed for job {job_id}: {e}")

        if conn:
            try:
                with conn.cursor() as cur:
                    # Update job error
                    cur.execute(
                        """
                        UPDATE processing_jobs
                        SET status = 'failed', error_message = %s,
                            updated_at = NOW(), completed_at = NOW()
                        WHERE job_id = %s
                        """,
                        (str(e), str(job_uuid))
                    )
                    # Update document status
                    cur.execute(
                        """
                        UPDATE documents
                        SET status = 'failed', updated_at = NOW()
                        WHERE document_id = %s
                        """,
                        (str(doc_uuid),)
                    )
                    conn.commit()
            except Exception as update_error:
                logger.error(f"Failed to update error status: {update_error}")

    finally:
        if conn and pool:
            try:
                pool.putconn(conn)
            except Exception as e:
                logger.error(f"Failed to return connection to pool: {e}")


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
    conn = Depends(get_pg_connection),
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

    # 3. Calculate file hash for duplicate detection
    file_hash = hashlib.sha256(file_content).hexdigest()

    # 4. Check for duplicate files by hash
    existing_doc = _get_document_by_hash(conn, file_hash)
    if existing_doc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "DUPLICATE_FILE",
                "error_message": f"동일한 파일이 이미 업로드되어 있습니다: {existing_doc.product_name}",
                "details": {
                    "existing_document_id": str(existing_doc.document_id),
                    "existing_product_name": existing_doc.product_name,
                    "existing_insurer": existing_doc.insurer
                }
            }
        )

    # 5. Check by insurer + product_name + product_code combination
    if product_code is not None:
        existing_product = _get_document_by_product(conn, insurer, product_name, product_code)
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error_code": "DUPLICATE_PRODUCT",
                    "error_message": f"동일한 상품이 이미 등록되어 있습니다: {insurer} - {product_name} ({product_code})",
                    "details": {
                        "existing_document_id": str(existing_product.document_id),
                        "existing_product_name": existing_product.product_name,
                        "existing_product_code": existing_product.product_code
                    }
                }
            )

    try:
        # 5. Generate IDs
        document_id = uuid4()
        job_id = uuid4()

        # 6. Parse tags
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
            file_hash=file_hash,
            status=DocumentStatus.PROCESSING,  # Start processing immediately
            total_pages=None,  # Will be set after OCR
            total_articles=None,  # Will be set after parsing
            parsing_confidence=None,  # Will be set after parsing
            gcs_uri=gcs_uri,
            created_at=now,
            updated_at=now,
            processed_at=None,
            uploaded_by_user_id=user_id,
        )

        # 7. Store document metadata in PostgreSQL
        _insert_document(conn, document_metadata)

        logger.info(f"Document uploaded to DB: {document_id} - {product_name}")

        # 8. Create processing job record
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO processing_jobs (
                    job_id, document_id, status, current_step,
                    progress_percentage, steps_completed, started_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                """,
                (
                    str(job_id),
                    str(document_id),
                    "processing",
                    "파일 업로드 완료",
                    0,
                    []
                )
            )
            conn.commit()

        logger.info(f"Processing job created: {job_id}")

        # 9. Trigger Celery background task (temporarily disabled)
        # process_document.delay(str(job_id), str(document_id), gcs_uri)
        # logger.info(f"Celery task triggered for document: {document_id}")
        logger.info(f"Celery task SKIPPED (disabled) for document: {document_id}")

        # 10. Return response immediately
        return DocumentUploadResponse(
            document_id=document_id,
            job_id=job_id,
            status=DocumentStatus.PROCESSING,
            message="문서 업로드가 완료되었습니다. 백그라운드에서 처리 중입니다.",
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
    conn = Depends(get_pg_connection),
) -> DocumentListResponse:
    """
    문서 목록 조회

    필터링과 페이지네이션을 지원합니다.
    """
    # Get documents from PostgreSQL with filters and pagination
    documents, total = _list_documents_filtered(
        conn, insurer, status_filter, document_type, search, page, page_size
    )

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    # Convert to list items
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
        for doc in documents
    ]

    return DocumentListResponse(
        documents=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{document_id}/processing-status",
    response_model=ProcessingJobStatus,
    status_code=status.HTTP_200_OK,
    summary="문서 처리 진행률 조회",
    description="""
    문서 처리 작업의 진행 상황을 조회합니다.

    **반환 정보**:
    - 현재 처리 단계
    - 진행률 (0-100%)
    - 완료된 단계 목록
    - 작업 상태 (processing, completed, failed)
    """,
)
async def get_processing_status(
    document_id: UUID,
    conn = Depends(get_pg_connection),
) -> ProcessingJobStatus:
    """
    문서 처리 진행률 조회

    백그라운드에서 진행 중인 문서 처리 작업의 진행 상황을 반환합니다.
    """
    # Get processing job from database
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM processing_jobs
                WHERE document_id = %s
                ORDER BY started_at DESC
                LIMIT 1
                """,
                (str(document_id),)
            )
            row = cur.fetchone()

            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error_code": "JOB_NOT_FOUND",
                        "error_message": f"Processing job not found for document: {document_id}",
                        "details": {"document_id": str(document_id)}
                    }
                )

            return ProcessingJobStatus(
                job_id=row['job_id'],
                document_id=row['document_id'],
                status=row['status'],
                current_step=row['current_step'],
                progress_percentage=row['progress_percentage'],
                steps_completed=row['steps_completed'] or [],
                error_message=row['error_message'],
                started_at=row['started_at'],
                updated_at=row['updated_at'],
                completed_at=row['completed_at'],
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processing status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "STATUS_QUERY_FAILED",
                "error_message": f"Failed to query processing status: {str(e)}",
                "details": {}
            }
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
async def get_document(document_id: UUID, conn = Depends(get_pg_connection)) -> DocumentMetadata:
    """
    문서 메타데이터 조회

    문서 ID로 메타데이터를 조회합니다.
    """
    doc = _get_document_by_id(conn, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "DOCUMENT_NOT_FOUND",
                "error_message": f"Document with ID '{document_id}' not found",
                "details": {"requested_id": str(document_id)},
                "document_id": None,
            }
        )

    return doc


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
async def get_document_content(document_id: UUID, conn = Depends(get_pg_connection)) -> DocumentContentResponse:
    """
    문서 컨텐츠 조회

    파싱된 조항과 구조화된 데이터를 조회합니다.
    """
    doc = _get_document_by_id(conn, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "DOCUMENT_NOT_FOUND",
                "error_message": f"Document with ID '{document_id}' not found",
                "details": {"requested_id": str(document_id)},
            }
        )

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
    conn = Depends(get_pg_connection),
) -> DocumentMetadata:
    """
    문서 메타데이터 수정

    상품명, 설명, 태그 등을 수정할 수 있습니다.
    """
    doc = _get_document_by_id(conn, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "DOCUMENT_NOT_FOUND",
                "error_message": f"Document with ID '{document_id}' not found",
                "details": {"requested_id": str(document_id)},
            }
        )

    # Update in database
    _update_document_metadata(
        conn, document_id,
        update_request.product_name,
        update_request.description,
        update_request.tags
    )

    logger.info(f"Document updated in DB: {document_id}")

    # Fetch and return updated document
    updated_doc = _get_document_by_id(conn, document_id)
    return updated_doc


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
async def delete_document(document_id: UUID, conn = Depends(get_pg_connection)):
    """
    문서 삭제

    메타데이터와 저장소의 파일을 모두 삭제합니다.
    """
    doc = _get_document_by_id(conn, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "DOCUMENT_NOT_FOUND",
                "error_message": f"Document with ID '{document_id}' not found",
                "details": {"requested_id": str(document_id)},
            }
        )

    try:
        # In production: Delete from GCS
        # await gcs_service.delete_file(doc.gcs_uri)

        # Delete from database
        deleted = _delete_document_by_id(conn, document_id)

        if deleted:
            logger.info(f"Document deleted from DB: {document_id} - {doc.product_name}")
            return JSONResponse(
                status_code=status.HTTP_204_NO_CONTENT,
                content=None
            )
        else:
            raise Exception("Failed to delete document from database")

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
async def get_document_stats(conn = Depends(get_pg_connection)) -> DocumentStatsResponse:
    """
    문서 통계 조회

    전체 문서 수, 상태별/보험사별/타입별 분포 등을 조회합니다.
    """
    stats = _get_document_stats(conn)

    return DocumentStatsResponse(
        total_documents=stats['total_documents'],
        by_status=stats['by_status'],
        by_insurer=stats['by_insurer'],
        by_type=stats['by_type'],
        total_pages=stats['total_pages'],
        total_articles=stats['total_articles'],
    )


@router.get(
    "/stats/timeseries",
    status_code=status.HTTP_200_OK,
    summary="시계열 통계 조회",
    description="월별 문서 등록 및 처리 통계를 조회합니다.",
)
async def get_timeseries_stats(conn = Depends(get_pg_connection)):
    """
    시계열 통계 조회

    최근 12개월 간 월별 문서 등록 및 처리 현황을 반환합니다.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # 최근 12개월 데이터 조회
        cur.execute("""
            WITH RECURSIVE months AS (
                SELECT DATE_TRUNC('month', CURRENT_DATE - INTERVAL '11 months') AS month
                UNION ALL
                SELECT DATE_TRUNC('month', month + INTERVAL '1 month')
                FROM months
                WHERE month < DATE_TRUNC('month', CURRENT_DATE)
            ),
            monthly_stats AS (
                SELECT
                    DATE_TRUNC('month', created_at) AS month,
                    COUNT(*) FILTER (WHERE status = 'completed') AS completed_count,
                    COUNT(*) FILTER (WHERE status = 'processing') AS processing_count,
                    COUNT(*) FILTER (WHERE status = 'pending') AS pending_count,
                    COUNT(*) AS total_count
                FROM documents
                WHERE created_at >= CURRENT_DATE - INTERVAL '11 months'
                GROUP BY DATE_TRUNC('month', created_at)
            )
            SELECT
                TO_CHAR(m.month, 'YYYY-MM') AS date,
                COALESCE(s.completed_count, 0) AS learned_docs,
                COALESCE(s.processing_count, 0) AS in_progress_docs,
                COALESCE(s.pending_count, 0) AS pending_docs,
                COALESCE(s.total_count, 0) AS total_docs
            FROM months m
            LEFT JOIN monthly_stats s ON m.month = s.month
            ORDER BY m.month
        """)

        results = cur.fetchall()

        # Convert to list of dicts
        timeseries = []
        for row in results:
            timeseries.append({
                'date': row['date'],
                'learnedDocs': row['learned_docs'],
                'inProgressDocs': row['in_progress_docs'],
                'pendingDocs': row['pending_docs'],
                'totalDocs': row['total_docs']
            })

        return timeseries


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


@router.post(
    "/{document_id}/start-processing",
    status_code=status.HTTP_200_OK,
    summary="문서 처리 시작",
    description="""
    문서 처리를 수동으로 시작합니다.

    processing job을 생성하고 문서 상태를 'processing'으로 변경합니다.
    """,
    responses={
        200: {"description": "처리 시작 성공"},
        404: {"model": DocumentErrorResponse, "description": "문서를 찾을 수 없음"},
        400: {"model": DocumentErrorResponse, "description": "이미 처리 중이거나 완료됨"},
    },
)
async def start_document_processing(
    document_id: UUID,
    conn = Depends(get_pg_connection),
):
    """
    문서 처리 수동 시작

    Celery 없이도 문서 처리를 시작할 수 있도록 합니다.
    """
    # 1. Check if document exists
    doc = _get_document_by_id(conn, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "DOCUMENT_NOT_FOUND",
                "error_message": f"Document with ID '{document_id}' not found",
                "details": {"requested_id": str(document_id)},
            }
        )

    # 2. Check if already processing or completed
    if doc.status in [DocumentStatus.PROCESSING, DocumentStatus.COMPLETED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_STATUS",
                "error_message": f"Document is already {doc.status.value}",
                "details": {"current_status": doc.status.value},
            }
        )

    # 3. Create or update processing job
    job_id = uuid4()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if job already exists
            cur.execute(
                """
                SELECT job_id FROM processing_jobs
                WHERE document_id = %s
                ORDER BY started_at DESC
                LIMIT 1
                """,
                (str(document_id),)
            )
            existing_job = cur.fetchone()

            if existing_job:
                job_id = UUID(existing_job['job_id'])
                # Update existing job
                cur.execute(
                    """
                    UPDATE processing_jobs
                    SET status = %s,
                        current_step = %s,
                        progress_percentage = %s,
                        updated_at = NOW()
                    WHERE job_id = %s
                    """,
                    ("processing", "문서 처리 시작", 0, str(job_id))
                )
            else:
                # Create new job
                cur.execute(
                    """
                    INSERT INTO processing_jobs (
                        job_id, document_id, status, current_step,
                        progress_percentage, steps_completed, started_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """,
                    (
                        str(job_id),
                        str(document_id),
                        "processing",
                        "문서 처리 시작",
                        0,
                        []
                    )
                )
            conn.commit()

        # 4. Update document status
        _update_document_processing_status(
            conn, document_id,
            DocumentStatus.PROCESSING
        )

        logger.info(f"Document processing started manually: {document_id}, job: {job_id}")

        # 5. Start background processing thread
        gcs_uri = doc.gcs_uri or f"gs://insuregraph/documents/{document_id}.pdf"
        thread = threading.Thread(
            target=_background_process_document,
            args=(str(job_id), str(document_id), gcs_uri),
            daemon=True
        )
        thread.start()
        logger.info(f"Background processing thread started: job={job_id}")

        return {
            "document_id": str(document_id),
            "job_id": str(job_id),
            "status": "processing",
            "message": "문서 처리가 시작되었습니다."
        }

    except Exception as e:
        logger.error(f"Failed to start document processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "PROCESSING_START_FAILED",
                "error_message": f"Failed to start processing: {str(e)}",
                "details": {}
            }
        )


def simulate_document_processing(document_id: UUID, conn):
    """
    문서 처리 시뮬레이션

    For testing: simulate document processing completion
    """
    doc = _get_document_by_id(conn, document_id)
    if doc:
        _update_document_processing_status(
            conn, document_id,
            DocumentStatus.COMPLETED,
            total_pages=45,
            total_articles=123,
            parsing_confidence=0.96
        )
        logger.info(f"Document processing completed (simulated) in DB: {document_id}")
