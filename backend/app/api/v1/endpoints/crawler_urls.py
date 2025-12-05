"""
Crawler URL Management API Endpoints

CRUD operations for managing crawler URLs
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
import psycopg2
from psycopg2.extras import RealDictCursor

from app.api.v1.models.crawler_url import (
    CrawlerUrlCreate,
    CrawlerUrlUpdate,
    CrawlerUrlResponse,
    CrawlerUrlListResponse,
)
from app.core.database import get_pg_connection


router = APIRouter(prefix="/crawler/urls", tags=["Crawler URLs"])


@router.get(
    "",
    response_model=CrawlerUrlListResponse,
    status_code=status.HTTP_200_OK,
    summary="크롤러 URL 목록 조회",
    description="특정 보험사의 크롤러 URL 목록을 조회합니다.",
)
async def list_crawler_urls(
    insurer: str = Query(..., description="보험사 이름"),
    enabled_only: bool = Query(False, description="활성화된 URL만 조회"),
    conn=Depends(get_pg_connection),
) -> CrawlerUrlListResponse:
    """
    크롤러 URL 목록 조회

    Args:
        insurer: 보험사 이름
        enabled_only: 활성화된 URL만 조회
        conn: DB connection

    Returns:
        CrawlerUrlListResponse: URL 목록
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if enabled_only:
                cur.execute(
                    """
                    SELECT * FROM crawler_urls
                    WHERE insurer = %s AND enabled = true
                    ORDER BY created_at DESC
                    """,
                    (insurer,)
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM crawler_urls
                    WHERE insurer = %s
                    ORDER BY created_at DESC
                    """,
                    (insurer,)
                )

            rows = cur.fetchall()

            return CrawlerUrlListResponse(
                items=[CrawlerUrlResponse(**row) for row in rows],
                total=len(rows),
            )

    except Exception as e:
        logger.error(f"Failed to list crawler URLs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="크롤러 URL 목록 조회에 실패했습니다",
        )


@router.post(
    "",
    response_model=CrawlerUrlResponse,
    status_code=status.HTTP_201_CREATED,
    summary="크롤러 URL 추가",
    description="새로운 크롤러 URL을 추가합니다.",
)
async def create_crawler_url(
    data: CrawlerUrlCreate,
    conn=Depends(get_pg_connection),
) -> CrawlerUrlResponse:
    """
    크롤러 URL 추가

    Args:
        data: URL 생성 데이터
        conn: DB connection

    Returns:
        CrawlerUrlResponse: 생성된 URL 정보
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO crawler_urls (insurer, url, description, enabled)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (data.insurer, data.url, data.description, data.enabled)
            )

            row = cur.fetchone()
            conn.commit()

            logger.info(f"Created crawler URL: {row['id']}")
            return CrawlerUrlResponse(**row)

    except Exception as e:
        logger.error(f"Failed to create crawler URL: {e}")
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="크롤러 URL 추가에 실패했습니다",
        )


@router.put(
    "/{url_id}",
    response_model=CrawlerUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="크롤러 URL 수정",
    description="크롤러 URL 정보를 수정합니다.",
)
async def update_crawler_url(
    url_id: UUID,
    data: CrawlerUrlUpdate,
    conn=Depends(get_pg_connection),
) -> CrawlerUrlResponse:
    """
    크롤러 URL 수정

    Args:
        url_id: URL ID
        data: 수정 데이터
        conn: DB connection

    Returns:
        CrawlerUrlResponse: 수정된 URL 정보
    """
    try:
        # Build update query dynamically based on provided fields
        update_fields = []
        update_values = []

        if data.url is not None:
            update_fields.append("url = %s")
            update_values.append(data.url)

        if data.description is not None:
            update_fields.append("description = %s")
            update_values.append(data.description)

        if data.enabled is not None:
            update_fields.append("enabled = %s")
            update_values.append(data.enabled)

        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="수정할 필드가 없습니다",
            )

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        update_values.append(str(url_id))

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = f"""
                UPDATE crawler_urls
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING *
            """
            cur.execute(query, update_values)

            row = cur.fetchone()
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="URL을 찾을 수 없습니다",
                )

            conn.commit()

            logger.info(f"Updated crawler URL: {url_id}")
            return CrawlerUrlResponse(**row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update crawler URL: {e}")
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="크롤러 URL 수정에 실패했습니다",
        )


@router.delete(
    "/{url_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="크롤러 URL 삭제",
    description="크롤러 URL을 삭제합니다.",
)
async def delete_crawler_url(
    url_id: UUID,
    conn=Depends(get_pg_connection),
):
    """
    크롤러 URL 삭제

    Args:
        url_id: URL ID
        conn: DB connection
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM crawler_urls WHERE id = %s",
                (str(url_id),)
            )

            if cur.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="URL을 찾을 수 없습니다",
                )

            conn.commit()

            logger.info(f"Deleted crawler URL: {url_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete crawler URL: {e}")
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="크롤러 URL 삭제에 실패했습니다",
        )


@router.get(
    "/{url_id}",
    response_model=CrawlerUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="크롤러 URL 상세 조회",
    description="특정 크롤러 URL의 상세 정보를 조회합니다.",
)
async def get_crawler_url(
    url_id: UUID,
    conn=Depends(get_pg_connection),
) -> CrawlerUrlResponse:
    """
    크롤러 URL 상세 조회

    Args:
        url_id: URL ID
        conn: DB connection

    Returns:
        CrawlerUrlResponse: URL 정보
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM crawler_urls WHERE id = %s",
                (str(url_id),)
            )

            row = cur.fetchone()
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="URL을 찾을 수 없습니다",
                )

            return CrawlerUrlResponse(**row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get crawler URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="크롤러 URL 조회에 실패했습니다",
        )
