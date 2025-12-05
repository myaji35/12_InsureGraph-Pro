"""
Crawler Documents API

문서 크롤링 및 관리 API 엔드포인트
"""
from fastapi import APIRouter, Query, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.services.document_crawler_service import DocumentCrawlerService
from app.services.crawler_progress_tracker import CrawlerProgressTracker
from app.core.database import get_db


router = APIRouter(prefix="/crawler", tags=["Crawler Documents"])


# Pydantic Models
class CreateCrawlerUrlRequest(BaseModel):
    """크롤러 URL 생성 요청 모델"""
    insurer: str
    url: str
    description: str = ""
    enabled: bool = True


class UpdateCrawlerUrlRequest(BaseModel):
    """크롤러 URL 수정 요청 모델"""
    url: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


class CrawlerDocumentResponse(BaseModel):
    """크롤러 문서 응답 모델"""
    id: str
    insurer: str
    title: str
    pdf_url: str
    category: str  # '약관' or '특약'
    product_type: Optional[str] = None
    source_url: Optional[str] = None
    status: str  # 'pending', 'downloaded', 'processing', 'processed', 'failed'
    processing_step: Optional[str] = None  # Current processing step
    processing_progress: Optional[int] = None  # Progress percentage (0-100)
    processing_detail: Optional[dict] = None  # Detailed processing information
    created_at: datetime
    updated_at: datetime


class CrawlResultResponse(BaseModel):
    """크롤링 결과 응답 모델"""
    message: str = Field(..., description="결과 메시지")
    total_urls: int = Field(..., description="크롤링한 URL 수")
    total_documents: int = Field(..., description="발견한 문서 수")
    saved_documents: int = Field(..., description="저장된 문서 수")
    documents: List[dict] = Field(default_factory=list, description="문서 목록")


class DocumentListResponse(BaseModel):
    """문서 목록 응답 모델"""
    total: int
    items: List[CrawlerDocumentResponse]


async def _background_crawl_task(insurer: str):
    """백그라운드 크롤링 태스크"""
    from app.core.database import async_engine
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    # 새로운 DB 세션 생성
    async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            crawler_service = DocumentCrawlerService(db=session)

            # 문서 크롤링
            result = await crawler_service.crawl_insurer_documents(insurer=insurer)

            # 문서 저장
            saved_count = await crawler_service.save_crawled_documents(
                documents=result['documents']
            )

            logger.info(
                f"Background crawling completed for {insurer}: "
                f"{result['total_documents']} documents, {saved_count} saved"
            )

        except Exception as e:
            logger.error(f"Background crawling failed for {insurer}: {e}")
            import traceback
            traceback.print_exc()


@router.post("/crawl-documents")
async def crawl_documents(
    background_tasks: BackgroundTasks,
    insurer: str = Query(..., description="보험사명")
):
    """
    특정 보험사의 문서를 크롤링합니다.

    - **insurer**: 보험사명

    크롤링은 백그라운드에서 실행되며, 즉시 결과를 반환합니다.
    """
    logger.info(f"Starting background crawl task for {insurer}")

    # 백그라운드 태스크로 크롤링 실행
    background_tasks.add_task(_background_crawl_task, insurer)

    return {
        "message": f"{insurer}의 문서 크롤링을 시작했습니다. 백그라운드에서 처리됩니다.",
        "status": "started",
        "insurer": insurer
    }


@router.get("/urls")
async def list_crawler_urls(
    insurer: Optional[str] = Query(None, description="보험사명 (선택)"),
    db: AsyncSession = Depends(get_db)
):
    """
    크롤러 URL 목록을 조회합니다.

    - **insurer**: 보험사명 (선택)
    """
    where_clauses = ["enabled = true"]
    params = {}

    if insurer:
        where_clauses.append("insurer = :insurer")
        params["insurer"] = insurer

    where_clause = " AND ".join(where_clauses)

    query = text(f"""
        SELECT id, insurer, url, description, enabled, created_at
        FROM crawler_urls
        WHERE {where_clause}
        ORDER BY created_at DESC
    """)

    result = await db.execute(query, params)
    rows = result.fetchall()

    items = [
        {
            "id": str(row.id),
            "insurer": row.insurer,
            "url": row.url,
            "description": row.description,
            "enabled": row.enabled,
            "created_at": row.created_at.isoformat() if row.created_at else None
        }
        for row in rows
    ]

    return {"items": items}


@router.post("/urls", status_code=201)
async def create_crawler_url(
    request: CreateCrawlerUrlRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    새로운 크롤러 URL을 추가합니다.

    - **insurer**: 보험사명
    - **url**: 크롤링할 URL
    - **description**: 설명 (선택)
    - **enabled**: 활성화 여부 (기본 True)
    """
    from uuid import uuid4

    url_id = uuid4()

    query = text("""
        INSERT INTO crawler_urls (id, insurer, url, description, enabled, created_at)
        VALUES (:id, :insurer, :url, :description, :enabled, NOW())
        RETURNING id, insurer, url, description, enabled, created_at
    """)

    try:
        result = await db.execute(query, {
            "id": url_id,
            "insurer": request.insurer,
            "url": request.url,
            "description": request.description,
            "enabled": request.enabled
        })
        await db.commit()

        row = result.fetchone()

        return {
            "id": str(row.id),
            "insurer": row.insurer,
            "url": row.url,
            "description": row.description,
            "enabled": row.enabled,
            "created_at": row.created_at.isoformat() if row.created_at else None
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create crawler URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create URL: {str(e)}")


@router.put("/urls/{url_id}")
async def update_crawler_url(
    url_id: str,
    request: UpdateCrawlerUrlRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    크롤러 URL을 수정합니다.

    - **url_id**: URL ID
    - **url**: 새로운 URL (선택)
    - **description**: 새로운 설명 (선택)
    - **enabled**: 활성화 여부 (선택)
    """
    # Build update query dynamically
    update_parts = []
    params = {"id": url_id}

    if request.url is not None:
        update_parts.append("url = :url")
        params["url"] = request.url

    if request.description is not None:
        update_parts.append("description = :description")
        params["description"] = request.description

    if request.enabled is not None:
        update_parts.append("enabled = :enabled")
        params["enabled"] = request.enabled

    if not update_parts:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_parts.append("updated_at = NOW()")
    update_clause = ", ".join(update_parts)

    query = text(f"""
        UPDATE crawler_urls
        SET {update_clause}
        WHERE id = :id
        RETURNING id, insurer, url, description, enabled, created_at
    """)

    try:
        result = await db.execute(query, params)
        await db.commit()

        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="URL not found")

        return {
            "id": str(row.id),
            "insurer": row.insurer,
            "url": row.url,
            "description": row.description,
            "enabled": row.enabled,
            "created_at": row.created_at.isoformat() if row.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update crawler URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update URL: {str(e)}")


@router.delete("/urls/{url_id}", status_code=204)
async def delete_crawler_url(
    url_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    크롤러 URL을 삭제합니다.

    - **url_id**: URL ID
    """
    query = text("DELETE FROM crawler_urls WHERE id = :id")

    try:
        result = await db.execute(query, {"id": url_id})
        await db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="URL not found")

        return None
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete crawler URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete URL: {str(e)}")


@router.post("/documents/{document_id}/process")
async def process_crawler_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    크롤러 문서를 학습(처리)합니다.

    이 엔드포인트는 PDF를 다운로드하고 텍스트를 추출한 후
    지식 그래프를 생성하여 문서를 학습합니다.
    """
    logger.info(f"Starting document processing for ID: {document_id}")

    try:
        # 문서 정보 조회
        query = text("""
            SELECT id, title, pdf_url, insurer, status
            FROM crawler_documents
            WHERE id = :id
        """)

        result = await db.execute(query, {"id": document_id})
        document = result.fetchone()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if document.status == "processed":
            return {"message": "Document already processed", "status": "completed"}

        # 상태를 'processing'으로 업데이트하고 초기 진행 상태 설정
        update_query = text("""
            UPDATE crawler_documents
            SET status = 'processing',
                processing_step = 'initializing',
                processing_progress = 10,
                updated_at = NOW()
            WHERE id = :id
        """)
        await db.execute(update_query, {"id": document_id})
        await db.commit()

        # 백그라운드에서 처리 작업 시작
        background_tasks.add_task(
            process_document_in_background,
            document_id=document_id,
            pdf_url=document.pdf_url,
            title=document.title,
            insurer=document.insurer,
            db_url=str(db.bind.url) if db.bind else None
        )

        return {
            "message": "Document processing started",
            "document_id": document_id,
            "status": "processing"
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to start document processing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start document processing: {str(e)}"
        )


async def process_document_in_background(
    document_id: str,
    pdf_url: str,
    title: str,
    insurer: str,
    db_url: str
):
    """백그라운드에서 문서를 처리하는 함수"""
    import asyncio
    from app.services.pdf_text_extractor import PDFTextExtractor
    from app.core.database import AsyncSessionLocal
    import httpx
    import tempfile
    import os

    logger.info(f"Background processing started for document {document_id}")

    async with AsyncSessionLocal() as db:
        try:
            async def update_progress(step: str, progress: int, detail: dict = None):
                """진행 상태를 업데이트하는 헬퍼 함수"""
                import json
                update_query = text("""
                    UPDATE crawler_documents
                    SET processing_step = :step,
                        processing_progress = :progress,
                        processing_detail = :detail,
                        updated_at = NOW()
                    WHERE id = :id
                """)
                await db.execute(update_query, {
                    "id": document_id,
                    "step": step,
                    "progress": progress,
                    "detail": json.dumps(detail) if detail else None
                })
                await db.commit()
                detail_msg = f" - {detail.get('message', '')}" if detail and 'message' in detail else ""
                logger.info(f"Document {document_id}: {step} ({progress}%){detail_msg}")

            # Step 1: PDF 다운로드 (20%)
            await update_progress("downloading_pdf", 20)
            logger.info(f"Downloading PDF from {pdf_url}")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(pdf_url)
                response.raise_for_status()
                pdf_content = response.content

            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(pdf_content)
                tmp_path = tmp_file.name

            try:
                # Step 2: PDF 텍스트 추출 - 세부 단계로 분할 (21% ~ 40%)
                extractor = PDFTextExtractor()

                # 2.1: PDF 분석 및 메타데이터 읽기 (21%)
                await update_progress("extracting_text", 21, {
                    "sub_step": "pdf_analysis",
                    "message": "PDF 메타데이터 분석 중"
                })
                logger.info(f"Analyzing PDF metadata")
                await asyncio.sleep(0.3)  # 실제 분석 시뮬레이션

                # 2.2: 여러 알고리즘으로 텍스트 추출 및 품질 평가 (23% ~ 40%)
                import time
                from app.services.pdf_text_quality_evaluator import PDFTextQualityEvaluator

                start_time = time.time()
                await update_progress("extracting_text", 23, {
                    "sub_step": "analyzing_algorithms",
                    "message": "최적의 텍스트 추출 알고리즘 분석 중..."
                })
                logger.info(f"Starting intelligent PDF text extraction with quality evaluation")

                # 여러 알고리즘 시도 및 최고 품질 결과 선택
                extraction_result = PDFTextQualityEvaluator.extract_best_quality(tmp_path)

                if "error" in extraction_result:
                    await update_progress("extracting_text", 35, {
                        "sub_step": "extraction_failed",
                        "message": "모든 텍스트 추출 방법 실패",
                        "attempts": extraction_result.get("all_attempts", [])
                    })
                    raise Exception(f"Text extraction failed: {extraction_result['error']}")

                extracted_text = extraction_result["text"]
                total_pages = extraction_result["total_pages"]
                algorithm = extraction_result["algorithm"]
                quality = extraction_result["quality"]

                # 진행 상황 업데이트 with 품질 정보
                await update_progress("extracting_text", 35, {
                    "sub_step": "algorithm_selected",
                    "message": f"{algorithm} 알고리즘 사용 (품질: {quality['quality_level']})",
                    "algorithm": algorithm,
                    "quality_score": quality["score"],
                    "quality_level": quality["quality_level"],
                    "total_pages": total_pages,
                    "all_attempts": extraction_result.get("all_attempts", [])
                })
                logger.info(f"Selected algorithm: {algorithm} with quality score {quality['score']}")

                # 품질이 너무 낮으면 경고
                if quality["score"] < 20:
                    await update_progress("extracting_text", 37, {
                        "sub_step": "low_quality_warning",
                        "message": f"텍스트 품질 낮음 (점수: {quality['score']}/100) - OCR 필요할 수 있음",
                        "quality": quality
                    })
                    logger.warning(f"Low quality extraction: {quality}")

                # 2.4: 품질 검증 완료 (40%)
                total_time = int(time.time() - start_time)
                await update_progress("extracting_text", 40, {
                    "sub_step": "extraction_complete",
                    "message": f"텍스트 추출 완료 ({algorithm}, {total_time}초)",
                    "algorithm": algorithm,
                    "quality_score": quality["score"],
                    "quality_level": quality["quality_level"],
                    "text_length": len(extracted_text),
                    "total_pages": total_pages,
                    "processing_time_seconds": total_time,
                    "avg_chars_per_page": quality["avg_chars_per_page"],
                    "korean_ratio": quality["korean_ratio"],
                    "english_ratio": quality["english_ratio"]
                })
                logger.info(f"Text extraction completed: {algorithm}, {len(extracted_text)} chars, {total_pages} pages, quality={quality['score']}, time={total_time}s")

                # Step 3: 엔티티 추출 (60%)
                await update_progress("extracting_entities", 60)
                await asyncio.sleep(2)  # 시뮬레이션 (실제 구현 시 제거)
                # TODO: 실제 엔티티 추출 로직
                # entities = await extract_entities(extracted_text)

                # Step 4: 관계 추출 (80%)
                await update_progress("extracting_relationships", 80)
                await asyncio.sleep(2)  # 시뮬레이션 (실제 구현 시 제거)
                # TODO: 실제 관계 추출 로직
                # relationships = await extract_relationships(extracted_text, entities)

                # Step 5: 임베딩 생성 및 저장 (85%)
                await update_progress("generating_embeddings", 85, {
                    "sub_step": "preparing_embeddings",
                    "message": "임베딩 생성 준비 중..."
                })
                logger.info(f"Starting embedding generation for document {document_id}")

                try:
                    from app.services.auto_embedding_service import AutoEmbeddingService

                    embedding_service = AutoEmbeddingService()

                    # 텍스트 청킹
                    await update_progress("generating_embeddings", 87, {
                        "sub_step": "chunking_text",
                        "message": "텍스트를 청크로 분할 중..."
                    })
                    chunks = embedding_service.chunk_text(extracted_text)
                    logger.info(f"Created {len(chunks)} text chunks")

                    # 임베딩 생성
                    await update_progress("generating_embeddings", 90, {
                        "sub_step": "creating_embeddings",
                        "message": f"{len(chunks)}개 청크의 임베딩 생성 중..."
                    })
                    embeddings = await embedding_service.create_embeddings(chunks)
                    logger.info(f"Generated {len(embeddings)} embeddings")

                    # 임베딩 저장
                    await update_progress("generating_embeddings", 93, {
                        "sub_step": "storing_embeddings",
                        "message": "임베딩을 데이터베이스에 저장 중..."
                    })
                    await embedding_service.store_embeddings(document_id, chunks, embeddings)
                    logger.info(f"Stored embeddings for document {document_id}")

                except Exception as e:
                    logger.warning(f"Embedding generation failed but continuing: {e}")
                    # 임베딩 실패해도 계속 진행

                # Step 6: Neo4j 그래프 구축 (95%)
                await update_progress("building_graph", 95, {
                    "sub_step": "preparing_graph",
                    "message": "그래프 구축 준비 중..."
                })
                logger.info(f"Starting Neo4j graph construction for document {document_id}")

                try:
                    from app.services.graph.graph_builder import GraphBuilder
                    from app.services.graph.neo4j_service import Neo4jService

                    # Neo4j 서비스 초기화
                    neo4j_service = Neo4jService()
                    neo4j_service.connect()

                    # GraphBuilder 초기화
                    graph_builder = GraphBuilder(
                        neo4j_service=neo4j_service,
                        embedding_service=None
                    )

                    # 상품 정보 준비
                    product_info = {
                        "product_name": title,
                        "company": insurer,
                        "product_type": "보험",
                        "document_id": document_id,
                        "version": "1.0",
                        "effective_date": None,
                    }

                    # 지식 그래프 구축
                    stats = await graph_builder.build_graph_from_document(
                        ocr_text=extracted_text,
                        product_info=product_info,
                        generate_embeddings=False
                    )

                    neo4j_service.close()

                    logger.info(
                        f"Graph built for {document_id}: "
                        f"{stats.total_nodes} nodes, {stats.total_relationships} relationships"
                    )

                    await update_progress("building_graph", 98, {
                        "sub_step": "graph_created",
                        "message": f"그래프 구축 완료 ({stats.total_nodes}개 노드, {stats.total_relationships}개 관계)",
                        "nodes": stats.total_nodes,
                        "relationships": stats.total_relationships,
                        "nodes_by_type": stats.nodes_by_type,
                        "relationships_by_type": stats.relationships_by_type
                    })

                except Exception as e:
                    logger.warning(f"Graph construction failed but continuing: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # 그래프 구축 실패해도 계속 진행
                    await update_progress("building_graph", 98, {
                        "sub_step": "graph_error",
                        "message": f"그래프 구축 실패 (계속 진행): {str(e)}"
                    })

                # Step 7: 완료 (100%)
                await update_progress("completed", 100, {
                    "sub_step": "finalized",
                    "message": "문서 학습 완료",
                    "total_pages": total_pages if 'total_pages' in locals() else 0,
                    "text_length": len(extracted_text) if 'extracted_text' in locals() else 0,
                    "algorithm": algorithm if 'algorithm' in locals() else "unknown",
                    "quality_score": quality["score"] if 'quality' in locals() else 0
                })

                # status를 'completed'로 변경
                final_update_query = text("""
                    UPDATE crawler_documents
                    SET status = 'completed'
                    WHERE id = :id
                """)
                await db.execute(final_update_query, {"id": document_id})
                await db.commit()

                logger.info(f"Document {document_id} processed successfully")

            finally:
                # 임시 파일 삭제
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}")
            # 상태를 'failed'로 업데이트
            try:
                update_query = text("""
                    UPDATE crawler_documents
                    SET status = 'failed',
                        updated_at = NOW(),
                        error_message = :error
                    WHERE id = :id
                """)
                await db.execute(update_query, {
                    "id": document_id,
                    "error": str(e)
                })
                await db.commit()
            except:
                pass


@router.get("/crawl-progress/{insurer}")
async def get_crawl_progress(insurer: str):
    """
    특정 보험사의 크롤링 진행 상황을 조회합니다.

    - **insurer**: 보험사명
    """
    progress = await CrawlerProgressTracker.get_progress(insurer)

    if not progress:
        raise HTTPException(
            status_code=404,
            detail=f"{insurer}의 크롤링 진행 정보가 없습니다."
        )

    return progress


@router.get("/documents", response_model=DocumentListResponse)
async def list_crawler_documents(
    insurer: Optional[str] = Query(None, description="보험사명 (선택)"),
    category: Optional[str] = Query(None, description="카테고리 (약관/특약)"),
    status: Optional[str] = Query(None, description="상태 (pending/downloaded/processed/failed)"),
    limit: int = Query(100, ge=1, le=1000, description="최대 결과 수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    db: AsyncSession = Depends(get_db)
):
    """
    크롤링한 문서 목록을 조회합니다.

    - **insurer**: 보험사명 (선택)
    - **category**: 카테고리 필터 (약관/특약)
    - **status**: 상태 필터
    - **limit**: 최대 결과 수 (기본 100)
    - **offset**: 오프셋 (기본 0)
    """
    # 쿼리 빌드
    where_clauses = []
    params = {}

    if insurer:
        where_clauses.append("insurer = :insurer")
        params["insurer"] = insurer

    if category:
        where_clauses.append("category = :category")
        params["category"] = category

    if status:
        where_clauses.append("status = :status")
        params["status"] = status

    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

    # 전체 개수 조회
    count_query = text(f"SELECT COUNT(*) FROM crawler_documents WHERE {where_clause}")
    count_result = await db.execute(count_query, params)
    total = count_result.scalar()

    # 문서 목록 조회
    query = text(f"""
        SELECT
            id, insurer, title, pdf_url, category, product_type,
            source_url, status, processing_step, processing_progress,
            processing_detail, created_at, updated_at
        FROM crawler_documents
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """)

    params["limit"] = limit
    params["offset"] = offset

    result = await db.execute(query, params)
    rows = result.fetchall()

    items = [
        CrawlerDocumentResponse(
            id=str(row.id),
            insurer=row.insurer,
            title=row.title,
            pdf_url=row.pdf_url,
            category=row.category,
            product_type=row.product_type,
            source_url=row.source_url,
            status=row.status,
            processing_step=row.processing_step if hasattr(row, 'processing_step') else None,
            processing_progress=row.processing_progress if hasattr(row, 'processing_progress') else None,
            processing_detail=row.processing_detail if hasattr(row, 'processing_detail') else None,
            created_at=row.created_at,
            updated_at=row.updated_at
        )
        for row in rows
    ]

    return DocumentListResponse(total=total, items=items)


@router.post("/process-parallel")
async def process_documents_in_parallel(
    background_tasks: BackgroundTasks,
    max_concurrent: int = Query(5, ge=1, le=10, description="동시 처리 문서 수 (1-10)"),
    limit: Optional[int] = Query(None, description="처리할 최대 문서 수"),
    insurer: Optional[str] = Query(None, description="특정 보험사만 처리"),
):
    """
    대기 중인 문서들을 병렬로 처리합니다.

    - **max_concurrent**: 동시에 처리할 최대 문서 수 (1-10, 기본값: 5)
      - CPU 코어 수와 메모리를 고려하여 설정
      - 권장: 4-6 (시스템 리소스에 따라 조정)
    - **limit**: 처리할 최대 문서 수 (None이면 모든 대기 문서 처리)
    - **insurer**: 특정 보험사의 문서만 처리 (None이면 모든 보험사)

    **처리 시간 예상:**
    - 문서당 평균 처리 시간: ~35초
    - max_concurrent=5일 경우: 100개 문서 → 약 12분
    - max_concurrent=1일 경우: 100개 문서 → 약 58분

    **주의사항:**
    - max_concurrent를 너무 높게 설정하면 메모리 부족이나 API 제한에 걸릴 수 있습니다
    - 디스크 공간이 충분한지 확인하세요 (현재 97% 사용 중)
    """
    from app.services.parallel_document_processor import ParallelDocumentProcessor

    processor = ParallelDocumentProcessor(
        max_concurrent=max_concurrent,
        use_smart_learning=True,  # SmartInsuranceLearner 사용
        use_streaming=True  # 스트리밍 PDF 처리 사용
    )

    # 백그라운드 작업으로 실행
    background_tasks.add_task(
        processor.process_pending_documents,
        limit=limit,
        insurer=insurer
    )

    return {
        "message": "병렬 문서 처리가 시작되었습니다",
        "max_concurrent": max_concurrent,
        "limit": limit or "모든 대기 문서",
        "insurer": insurer or "모든 보험사",
        "estimated_time_per_doc": "~35초",
        "note": "처리 진행 상황은 GET /api/v1/crawler/documents?status=processing 에서 확인하세요"
    }


@router.get("/stats")
async def get_document_stats(db: AsyncSession = Depends(get_db)):
    """
    문서 통계 조회 (초고속 응답)

    실시간 대시보드용 통계 엔드포인트
    - 전체 문서 수와 상태별 카운트만 반환
    - 모든 문서 데이터를 가져오지 않아 매우 빠름

    Returns:
        {
            "total": 956,
            "pending": 927,
            "processing": 1,
            "completed": 28,
            "failed": 0,
            "timestamp": "2025-12-02T20:15:00Z"
        }
    """
    try:
        # 상태별 카운트 쿼리 (GROUP BY 사용 - 매우 빠름)
        query = text("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) FILTER (WHERE status = 'processing') as processing,
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'failed') as failed
            FROM crawler_documents
        """)

        result = await db.execute(query)
        row = result.fetchone()

        return {
            "total": row[0] if row else 0,
            "pending": row[1] if row else 0,
            "processing": row[2] if row else 0,
            "completed": row[3] if row else 0,
            "failed": row[4] if row else 0,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except Exception as e:
        logger.error(f"Failed to get document stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/learning")
async def get_learning_stats(db: AsyncSession = Depends(get_db)):
    """
    GraphRAG 학습 진행 상황 조회

    실시간 대시보드용 학습 통계 엔드포인트
    - 문서 처리 상태별 카운트
    - Neo4j 지식 그래프 통계 (노드, 관계)
    - 마지막 처리 시간

    Returns:
        {
            "total_documents": 956,
            "completed_documents": 58,
            "processing_documents": 1,
            "pending_documents": 896,
            "neo4j_nodes": 1234,
            "neo4j_relationships": 567,
            "last_processed_at": "2025-12-02T20:15:00Z"
        }
    """
    try:
        # 1. PostgreSQL - 문서 상태별 카운트
        doc_query = text("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'processing') as processing,
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                MAX(updated_at) FILTER (WHERE status = 'completed') as last_processed
            FROM crawler_documents
        """)

        doc_result = await db.execute(doc_query)
        doc_row = doc_result.fetchone()

        # 2. Neo4j - 노드와 관계 카운트
        neo4j_nodes = 0
        neo4j_relationships = 0

        try:
            from app.core.config import settings
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )

            with driver.session() as session:
                # 노드 카운트
                node_result = session.run("MATCH (n) RETURN count(n) as count")
                neo4j_nodes = node_result.single()["count"]

                # 관계 카운트
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                neo4j_relationships = rel_result.single()["count"]

            driver.close()

        except Exception as neo_error:
            logger.warning(f"Failed to get Neo4j stats: {neo_error}")
            # Neo4j 연결 실패해도 문서 통계는 반환

        return {
            "total_documents": doc_row[0] if doc_row else 0,
            "completed_documents": doc_row[1] if doc_row else 0,
            "processing_documents": doc_row[2] if doc_row else 0,
            "pending_documents": doc_row[3] if doc_row else 0,
            "neo4j_nodes": neo4j_nodes,
            "neo4j_relationships": neo4j_relationships,
            "last_processed_at": doc_row[4].isoformat() + "Z" if doc_row and doc_row[4] else None
        }

    except Exception as e:
        logger.error(f"Failed to get learning stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{document_id}/reset")
async def reset_document_to_pending(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    문서를 미학습 상태로 초기화

    학습된 데이터를 삭제하고 status를 'pending'으로 변경합니다.

    Args:
        document_id: 초기화할 문서 ID

    Returns:
        초기화 결과
    """
    try:
        # 1. 문서 존재 확인
        check_query = text("""
            SELECT id, status, title
            FROM crawler_documents
            WHERE id = :document_id
        """)
        result = await db.execute(check_query, {"document_id": document_id})
        document = result.fetchone()

        if not document:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

        doc_status = document[1]
        doc_title = document[2]

        # 2. 이미 pending 상태인 경우
        if doc_status == 'pending':
            return {
                "message": "이미 미학습 상태입니다.",
                "document_id": document_id,
                "status": "pending"
            }

        # 3. 문서 상태를 pending으로 변경하고 학습 데이터 초기화
        reset_query = text("""
            UPDATE crawler_documents
            SET
                status = 'pending',
                processing_step = NULL,
                processing_progress = NULL,
                processing_detail = NULL,
                updated_at = NOW()
            WHERE id = :document_id
        """)
        await db.execute(reset_query, {"document_id": document_id})
        await db.commit()

        logger.info(f"Document reset to pending: {document_id} ({doc_title})")

        return {
            "message": "문서가 미학습 상태로 초기화되었습니다.",
            "document_id": document_id,
            "title": doc_title,
            "previous_status": doc_status,
            "new_status": "pending"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset document {document_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"문서 초기화 실패: {str(e)}")


@router.post("/reset-by-insurer/{insurer_code}")
async def reset_insurer_documents(
    insurer_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 보험사의 모든 학습 문서를 미학습 상태로 초기화

    Args:
        insurer_code: 보험사 코드 (예: 'metlife', 'samsung_life')

    Returns:
        초기화 결과 및 초기화된 문서 수
    """
    try:
        # 1. 해당 보험사의 학습 완료된 문서 수 확인
        count_query = text("""
            SELECT COUNT(*)
            FROM crawler_documents
            WHERE insurer = :insurer_code
            AND status IN ('ready', 'processed')
        """)
        result = await db.execute(count_query, {"insurer_code": insurer_code})
        total_learned = result.scalar()

        if total_learned == 0:
            return {
                "message": f"{insurer_code}에 초기화할 학습 완료 문서가 없습니다.",
                "insurer_code": insurer_code,
                "reset_count": 0
            }

        # 2. 모든 학습 완료 문서를 pending으로 초기화
        reset_query = text("""
            UPDATE crawler_documents
            SET
                status = 'pending',
                processing_step = NULL,
                processing_progress = NULL,
                processing_detail = NULL,
                updated_at = NOW()
            WHERE insurer = :insurer_code
            AND status IN ('ready', 'processed')
        """)
        await db.execute(reset_query, {"insurer_code": insurer_code})
        await db.commit()

        logger.info(f"Reset {total_learned} documents for insurer: {insurer_code}")

        return {
            "message": f"{insurer_code}의 모든 학습 문서가 초기화되었습니다.",
            "insurer_code": insurer_code,
            "reset_count": total_learned
        }

    except Exception as e:
        logger.error(f"Failed to reset documents for insurer {insurer_code}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"보험사 문서 초기화 실패: {str(e)}"
        )
