"""
Crawler API Endpoints

보험사 웹사이트 크롤러 관리 및 실행 엔드포인트
"""
import asyncio
import os
import tempfile
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from loguru import logger

from app.core.deps import get_pg_connection
from app.services.crawler import (
    CrawlerManager,
    InsuranceCompanyCrawler,
    download_pdf
)
from app.services.background_tasks import process_pdf_background


router = APIRouter()


# Pydantic models
class CrawlerConfig(BaseModel):
    """크롤러 설정"""
    config_id: Optional[str] = None
    company_name: str
    base_url: str
    policy_page_urls: List[str]
    selectors: dict
    respect_robots_txt: bool = True
    enabled: bool = False
    crawl_schedule: Optional[str] = None
    notes: Optional[str] = None


class CrawlerConfigUpdate(BaseModel):
    """크롤러 설정 업데이트"""
    base_url: Optional[str] = None
    policy_page_urls: Optional[List[str]] = None
    selectors: Optional[dict] = None
    respect_robots_txt: Optional[bool] = None
    enabled: Optional[bool] = None
    crawl_schedule: Optional[str] = None
    notes: Optional[str] = None


class CrawlerJob(BaseModel):
    """크롤러 작업"""
    job_id: str
    company_name: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_documents_found: int = 0
    documents_downloaded: int = 0
    documents_processed: int = 0
    result_summary: Optional[dict] = None


class CrawlerJobDocument(BaseModel):
    """크롤러가 발견한 문서"""
    id: str
    job_id: str
    url: str
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    description: Optional[str] = None
    insurer: str
    download_status: str
    document_id: Optional[str] = None


# Endpoints

@router.get(
    "/configs",
    status_code=status.HTTP_200_OK,
    summary="크롤러 설정 목록 조회",
    description="등록된 모든 크롤러 설정을 조회합니다."
)
async def get_crawler_configs(
    enabled_only: bool = False,
    conn = Depends(get_pg_connection)
):
    """크롤러 설정 목록 조회"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        query = "SELECT * FROM crawler_configs"
        if enabled_only:
            query += " WHERE enabled = TRUE"
        query += " ORDER BY company_name"

        cur.execute(query)
        configs = cur.fetchall()

        return {"configs": configs, "total": len(configs)}


@router.get(
    "/configs/{company_name}",
    status_code=status.HTTP_200_OK,
    summary="크롤러 설정 조회",
    description="특정 보험사의 크롤러 설정을 조회합니다."
)
async def get_crawler_config(
    company_name: str,
    conn = Depends(get_pg_connection)
):
    """특정 보험사 크롤러 설정 조회"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT * FROM crawler_configs WHERE company_name = %s",
            (company_name,)
        )
        config = cur.fetchone()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crawler config not found for {company_name}"
            )

        return config


@router.post(
    "/configs",
    status_code=status.HTTP_201_CREATED,
    summary="크롤러 설정 생성",
    description="새로운 보험사 크롤러 설정을 생성합니다."
)
async def create_crawler_config(
    config: CrawlerConfig,
    conn = Depends(get_pg_connection)
):
    """크롤러 설정 생성"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            INSERT INTO crawler_configs (
                company_name, base_url, policy_page_urls, selectors,
                respect_robots_txt, enabled, crawl_schedule, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            config.company_name,
            config.base_url,
            config.policy_page_urls,
            config.selectors,
            config.respect_robots_txt,
            config.enabled,
            config.crawl_schedule,
            config.notes
        ))

        new_config = cur.fetchone()
        conn.commit()

        logger.info(f"Created crawler config for {config.company_name}")
        return new_config


@router.patch(
    "/configs/{company_name}",
    status_code=status.HTTP_200_OK,
    summary="크롤러 설정 업데이트",
    description="기존 크롤러 설정을 업데이트합니다."
)
async def update_crawler_config(
    company_name: str,
    config_update: CrawlerConfigUpdate,
    conn = Depends(get_pg_connection)
):
    """크롤러 설정 업데이트"""
    # Build update query dynamically
    update_fields = []
    params = []

    if config_update.base_url is not None:
        update_fields.append("base_url = %s")
        params.append(config_update.base_url)

    if config_update.policy_page_urls is not None:
        update_fields.append("policy_page_urls = %s")
        params.append(config_update.policy_page_urls)

    if config_update.selectors is not None:
        update_fields.append("selectors = %s")
        params.append(config_update.selectors)

    if config_update.respect_robots_txt is not None:
        update_fields.append("respect_robots_txt = %s")
        params.append(config_update.respect_robots_txt)

    if config_update.enabled is not None:
        update_fields.append("enabled = %s")
        params.append(config_update.enabled)

    if config_update.crawl_schedule is not None:
        update_fields.append("crawl_schedule = %s")
        params.append(config_update.crawl_schedule)

    if config_update.notes is not None:
        update_fields.append("notes = %s")
        params.append(config_update.notes)

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    params.append(company_name)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        query = f"""
            UPDATE crawler_configs
            SET {', '.join(update_fields)}
            WHERE company_name = %s
            RETURNING *
        """

        cur.execute(query, params)
        updated_config = cur.fetchone()

        if not updated_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crawler config not found for {company_name}"
            )

        conn.commit()
        logger.info(f"Updated crawler config for {company_name}")

        return updated_config


@router.delete(
    "/configs/{company_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="크롤러 설정 삭제",
    description="보험사 크롤러 설정을 삭제합니다."
)
async def delete_crawler_config(
    company_name: str,
    conn = Depends(get_pg_connection)
):
    """크롤러 설정 삭제"""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM crawler_configs WHERE company_name = %s",
            (company_name,)
        )

        if cur.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crawler config not found for {company_name}"
            )

        conn.commit()
        logger.info(f"Deleted crawler config for {company_name}")


@router.post(
    "/jobs/start/{company_name}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="크롤링 작업 시작",
    description="특정 보험사에 대한 크롤링 작업을 시작합니다."
)
async def start_crawl_job(
    company_name: str,
    background_tasks: BackgroundTasks,
    conn = Depends(get_pg_connection)
):
    """크롤링 작업 시작"""
    # Check if config exists and is enabled
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT * FROM crawler_configs WHERE company_name = %s",
            (company_name,)
        )
        config = cur.fetchone()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crawler config not found for {company_name}"
            )

        if not config['enabled']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Crawler is disabled for {company_name}. Enable it first."
            )

        # Create crawler job
        cur.execute("""
            INSERT INTO crawler_jobs (
                config_id, company_name, status, started_at
            ) VALUES (%s, %s, %s, %s)
            RETURNING job_id
        """, (
            config['config_id'],
            company_name,
            'running',
            datetime.now()
        ))

        job = cur.fetchone()
        job_id = job['job_id']
        conn.commit()

    # Start crawling in background
    background_tasks.add_task(
        run_crawler_job,
        job_id,
        company_name,
        dict(config)
    )

    logger.info(f"Started crawler job {job_id} for {company_name}")

    return {
        "job_id": str(job_id),
        "company_name": company_name,
        "status": "running",
        "message": "Crawler job started successfully"
    }


@router.get(
    "/jobs",
    status_code=status.HTTP_200_OK,
    summary="크롤러 작업 목록 조회",
    description="크롤러 작업 목록을 조회합니다."
)
async def get_crawler_jobs(
    company_name: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 20,
    conn = Depends(get_pg_connection)
):
    """크롤러 작업 목록 조회"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        query = "SELECT * FROM crawler_jobs WHERE 1=1"
        params = []

        if company_name:
            query += " AND company_name = %s"
            params.append(company_name)

        if status_filter:
            query += " AND status = %s"
            params.append(status_filter)

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cur.execute(query, params)
        jobs = cur.fetchall()

        return {"jobs": jobs, "total": len(jobs)}


@router.get(
    "/jobs/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="크롤러 작업 상세 조회",
    description="특정 크롤러 작업의 상세 정보를 조회합니다."
)
async def get_crawler_job(
    job_id: str,
    conn = Depends(get_pg_connection)
):
    """크롤러 작업 상세 조회"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT * FROM crawler_jobs WHERE job_id = %s",
            (job_id,)
        )
        job = cur.fetchone()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crawler job not found: {job_id}"
            )

        # Get discovered documents
        cur.execute(
            "SELECT * FROM crawler_job_documents WHERE job_id = %s ORDER BY created_at",
            (job_id,)
        )
        documents = cur.fetchall()

        return {
            "job": job,
            "documents": documents,
            "total_documents": len(documents)
        }


# Background task function
async def run_crawler_job(job_id: str, company_name: str, config: dict):
    """
    백그라운드에서 크롤링 작업 실행

    Args:
        job_id: 작업 ID
        company_name: 보험사명
        config: 크롤러 설정
    """
    import psycopg2
    from app.core.config import settings

    # Create new DB connection for background task
    conn = psycopg2.connect(
        host=settings.PG_HOST,
        port=settings.PG_PORT,
        dbname=settings.PG_DATABASE,
        user=settings.PG_USER,
        password=settings.PG_PASSWORD
    )

    try:
        # Run crawler
        crawler = InsuranceCompanyCrawler(config)
        documents = await crawler.crawl()

        # Save discovered documents
        with conn.cursor() as cur:
            for doc in documents:
                cur.execute("""
                    INSERT INTO crawler_job_documents (
                        job_id, doc_hash, url, product_name, product_code,
                        description, source_page, insurer, download_status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    job_id,
                    doc['doc_id'],
                    doc['url'],
                    doc.get('product_name'),
                    doc.get('product_code'),
                    doc.get('description'),
                    doc.get('source_page'),
                    doc['insurer'],
                    'pending'
                ))

            # Update job status
            cur.execute("""
                UPDATE crawler_jobs
                SET status = 'completed',
                    completed_at = %s,
                    total_documents_found = %s,
                    result_summary = %s
                WHERE job_id = %s
            """, (
                datetime.now(),
                len(documents),
                {'documents_found': len(documents)},
                job_id
            ))

            # Update config last_crawled_at
            cur.execute("""
                UPDATE crawler_configs
                SET last_crawled_at = %s
                WHERE company_name = %s
            """, (datetime.now(), company_name))

            conn.commit()

        logger.info(f"Crawler job {job_id} completed. Found {len(documents)} documents.")

    except Exception as e:
        logger.error(f"Crawler job {job_id} failed: {e}")

        # Update job status to failed
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE crawler_jobs
                SET status = 'failed',
                    completed_at = %s,
                    errors = %s
                WHERE job_id = %s
            """, (
                datetime.now(),
                [str(e)],
                job_id
            ))
            conn.commit()

    finally:
        conn.close()


@router.post(
    "/jobs/{job_id}/download",
    status_code=status.HTTP_202_ACCEPTED,
    summary="크롤링 결과 문서 다운로드",
    description="크롤링으로 발견한 문서를 다운로드하고 처리합니다."
)
async def download_crawler_documents(
    job_id: str,
    background_tasks: BackgroundTasks,
    conn = Depends(get_pg_connection)
):
    """크롤링 결과 문서 다운로드 및 처리"""
    # Get pending documents
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT * FROM crawler_job_documents
            WHERE job_id = %s AND download_status = 'pending'
        """, (job_id,))

        pending_docs = cur.fetchall()

        if not pending_docs:
            return {
                "message": "No pending documents to download",
                "total_pending": 0
            }

    # Download documents in background
    background_tasks.add_task(
        download_and_process_documents,
        job_id,
        pending_docs
    )

    return {
        "message": f"Started downloading {len(pending_docs)} documents",
        "total_pending": len(pending_docs)
    }


@router.get(
    "/companies/{company_name}/documents",
    status_code=status.HTTP_200_OK,
    summary="보험사별 크롤링 문서 조회",
    description="특정 보험사의 모든 크롤링된 문서 목록을 조회합니다."
)
async def get_company_crawler_documents(
    company_name: str,
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    conn = Depends(get_pg_connection)
):
    """보험사별 크롤링 문서 목록"""
    offset = (page - 1) * page_size

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Count total
        count_query = """
            SELECT COUNT(*) as total
            FROM crawler_job_documents cjd
            JOIN crawler_jobs cj ON cjd.job_id = cj.job_id
            WHERE cj.company_name = %s
        """
        params = [company_name]

        if status_filter:
            count_query += " AND cjd.download_status = %s"
            params.append(status_filter)

        cur.execute(count_query, params)
        total = cur.fetchone()['total']

        # Get documents
        query = """
            SELECT
                cjd.*,
                cj.started_at as job_started_at,
                cj.status as job_status,
                d.title as document_title,
                d.status as document_status
            FROM crawler_job_documents cjd
            JOIN crawler_jobs cj ON cjd.job_id = cj.job_id
            LEFT JOIN documents d ON cjd.document_id = d.document_id
            WHERE cj.company_name = %s
        """

        if status_filter:
            query += " AND cjd.download_status = %s"

        query += " ORDER BY cjd.created_at DESC LIMIT %s OFFSET %s"
        params.extend([page_size, offset])

        cur.execute(query, params)
        documents = cur.fetchall()

        return {
            "company_name": company_name,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "documents": documents
        }


@router.post(
    "/test-url",
    status_code=status.HTTP_200_OK,
    summary="URL 크롤링 테스트",
    description="Selenium을 사용하여 URL 접근성과 약관 링크를 테스트합니다."
)
async def test_url_crawling(
    url: str,
    crawler_type: str = "selenium",  # "selenium" only for now (playwright had install issues)
    headless: bool = True
):
    """
    URL 크롤링 테스트

    Args:
        url: 테스트할 URL
        crawler_type: 크롤러 타입 ("selenium")
        headless: 헤드리스 모드 사용 여부

    Returns:
        테스트 결과
    """
    if crawler_type != "selenium":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currently only 'selenium' crawler is supported"
        )

    try:
        from app.services.crawlers.browser_crawler import BrowserCrawler

        with BrowserCrawler(headless=headless) as crawler:
            # URL 접근 테스트
            access_result = crawler.test_url_access(url)

            if access_result["success"]:
                # PDF 링크 찾기
                pdf_links = crawler.find_pdf_links(url, wait_time=5)
                access_result["pdf_links_found"] = len(pdf_links)
                access_result["pdf_links"] = pdf_links[:10]  # 처음 10개만 반환

            return access_result

    except Exception as e:
        logger.error(f"URL 테스트 실패: {url} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"크롤링 테스트 실패: {str(e)}"
        )


async def download_and_process_documents(job_id: str, documents: List[dict]):
    """문서 다운로드 및 처리"""
    import psycopg2
    from app.core.config import settings

    conn = psycopg2.connect(
        host=settings.PG_HOST,
        port=settings.PG_PORT,
        dbname=settings.PG_DATABASE,
        user=settings.PG_USER,
        password=settings.PG_PASSWORD
    )

    downloaded = 0
    processed = 0

    try:
        for doc in documents:
            doc_row_id = doc['id']
            url = doc['url']

            # Create temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                temp_path = tmp_file.name

            # Download PDF
            success = await download_pdf(url, temp_path)

            if success:
                downloaded += 1

                # Update download status
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE crawler_job_documents
                        SET download_status = 'downloaded',
                            downloaded_at = %s
                        WHERE id = %s
                    """, (datetime.now(), doc_row_id))
                    conn.commit()

                # TODO: Trigger PDF processing
                # This would integrate with the existing PDF processing pipeline
                logger.info(f"Downloaded document from {url}")

                # Clean up temp file
                os.remove(temp_path)
            else:
                # Mark as failed
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE crawler_job_documents
                        SET download_status = 'failed',
                            error_message = 'Download failed'
                        WHERE id = %s
                    """, (doc_row_id,))
                    conn.commit()

        # Update job statistics
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE crawler_jobs
                SET documents_downloaded = %s
                WHERE job_id = %s
            """, (downloaded, job_id))
            conn.commit()

        logger.info(f"Downloaded {downloaded} documents for job {job_id}")

    except Exception as e:
        logger.error(f"Failed to download documents for job {job_id}: {e}")

    finally:
        conn.close()
