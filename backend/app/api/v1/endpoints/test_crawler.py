"""
Test Crawler API Endpoints

샘플 크롤링 및 파일 추출 테스트 엔드포인트
"""
import time
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from loguru import logger

from app.api.v1.models.crawler import (
    TestCrawlRequest,
    TestCrawlResponse,
    DiscoveredFile,
    CrawlStep,
    SaveHeaderRequest,
    HeaderConfigResponse
)
from app.services.playwright_crawler import PlaywrightCrawler, PLAYWRIGHT_AVAILABLE
from app.services.file_extractor import FileExtractor
from app.services.header_storage import get_header_storage


router = APIRouter(prefix="/test-crawler", tags=["Test Crawler"])


@router.post(
    "/crawl",
    response_model=TestCrawlResponse,
    status_code=status.HTTP_200_OK,
    summary="테스트 크롤링 실행",
    description="URL을 크롤링하고 HTML을 저장한 후 Claude로 파일명을 추출합니다."
)
async def test_crawl(request: TestCrawlRequest) -> TestCrawlResponse:
    """
    테스트 크롤링 실행

    1. Playwright로 URL 크롤링
    2. HTML 파일 저장
    3. Claude API로 파일명 추출
    4. 헤더 설정 저장 (옵션)
    """
    start_time = time.time()
    steps = []
    logs = []

    def add_log(message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        logs.append(f"[{timestamp}] {message}")
        logger.info(message)

    def add_step(step_num: int, name: str, status: str, message: Optional[str] = None):
        steps.append(CrawlStep(
            step=step_num,
            name=name,
            status=status,
            message=message
        ))

    try:
        # Check if Playwright is available
        if not PLAYWRIGHT_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Playwright is not installed. Run: pip install playwright && playwright install chromium"
            )

        # Step 1: Playwright 페이지 분석
        add_step(1, "Playwright 페이지 분석", "running", "브라우저 시작 중...")
        add_log("🌐 Playwright 브라우저 실행")
        add_log(f"URL: {request.url}")

        # Get stored headers if available
        header_storage = get_header_storage()
        stored_headers = header_storage.get_headers_dict_only(request.company_name)

        # Merge with request headers
        final_headers = {**stored_headers, **(request.headers or {})}

        if final_headers:
            add_log(f"사용자 정의 헤더: {list(final_headers.keys())}")

        # Initialize crawler
        async with PlaywrightCrawler(headless=True) as crawler:
            # Crawl page
            html_content, metadata = await crawler.crawl_page(
                url=request.url,
                custom_headers=final_headers if final_headers else None,
                wait_time=2000
            )

            add_log(f"페이지 로딩 완료: {metadata['title']}")
            add_log(f"콘텐츠 크기: {metadata['content_length']:,} bytes")
            add_step(1, "Playwright 페이지 분석", "completed", f"완료 ({metadata['duration']:.2f}초)")

            # Step 2: HTML 파싱 및 분석
            add_step(2, "HTML 파싱 및 분석", "running", "HTML 구조 분석 중...")
            add_log("📄 HTML 파싱 중...")

            # Parse HTML structure
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Count links
            all_links = soup.find_all('a', href=True)
            pdf_links = [a for a in all_links if '.pdf' in a.get('href', '').lower()]

            add_log(f"총 링크 수: {len(all_links)}개")
            add_log(f"PDF 링크 수: {len(pdf_links)}개")
            add_step(2, "HTML 파싱 및 분석", "completed", f"{len(all_links)}개 링크 발견")

            # Step 3: HTML 저장
            add_step(3, "HTML 저장", "running", "파일 저장 중...")
            add_log("💾 HTML 파일 저장 중...")

            html_path = await crawler.save_html(
                html_content=html_content,
                company_name=request.company_name
            )

            import os
            html_size = os.path.getsize(html_path)

            add_log(f"저장 완료: {html_path}")
            add_log(f"파일 크기: {html_size:,} bytes")
            add_step(3, "HTML 저장", "completed", f"{html_size:,} bytes 저장")

        # Step 4: LLM 분석 (파일명 추출)
        add_step(4, "LLM 분석 (파일명 추출)", "running", "Claude API 호출 중...")
        add_log("🤖 Claude Sonnet 4.5 분석 시작")
        add_log("HTML에서 약관 파일명 추출 중...")

        # Extract filenames using Claude
        extractor = FileExtractor()
        files = await extractor.extract_filenames(
            html_content=html_content,
            company_name=request.company_name,
            max_files=10
        )

        add_log(f"✅ 분석 완료! 발견된 문서: {len(files)}개")

        # Convert to DiscoveredFile model
        discovered_files = [
            DiscoveredFile(
                filename=f.get('filename', ''),
                url=f.get('url'),
                confidence=f.get('confidence', 0.0),
                context=f.get('context')
            )
            for f in files
        ]

        for i, file in enumerate(discovered_files, 1):
            add_log(f"  {i}. {file.filename} (신뢰도: {file.confidence:.2f})")

        add_step(4, "LLM 분석 (파일명 추출)", "completed", f"{len(files)}개 파일 발견")

        # Save headers if requested
        if request.save_headers and final_headers:
            header_storage.save_headers(
                company_name=request.company_name,
                headers=final_headers
            )
            add_log(f"📝 헤더 설정 저장 완료")

        # Calculate duration
        duration = time.time() - start_time

        return TestCrawlResponse(
            success=True,
            company_name=request.company_name,
            url=request.url,
            html_saved=True,
            html_path=html_path,
            html_size=html_size,
            discovered_files=discovered_files,
            total_files=len(discovered_files),
            steps=steps,
            logs=logs,
            duration=duration
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test crawl failed: {e}", exc_info=True)

        # Add error step
        add_step(0, "오류 발생", "failed", str(e))
        add_log(f"❌ 오류 발생: {str(e)}")

        duration = time.time() - start_time

        return TestCrawlResponse(
            success=False,
            company_name=request.company_name,
            url=request.url,
            html_saved=False,
            discovered_files=[],
            total_files=0,
            steps=steps,
            logs=logs,
            error=str(e),
            duration=duration
        )


@router.post(
    "/headers",
    response_model=HeaderConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="헤더 설정 저장",
    description="보험사별 HTTP 헤더 설정을 저장합니다."
)
async def save_headers(request: SaveHeaderRequest) -> HeaderConfigResponse:
    """헤더 설정 저장"""
    header_storage = get_header_storage()

    config = header_storage.save_headers(
        company_name=request.company_name,
        headers=request.headers
    )

    return HeaderConfigResponse(**config)


@router.get(
    "/headers/{company_name}",
    response_model=HeaderConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="헤더 설정 조회",
    description="보험사의 저장된 HTTP 헤더 설정을 조회합니다."
)
async def get_headers(company_name: str) -> HeaderConfigResponse:
    """헤더 설정 조회"""
    header_storage = get_header_storage()

    config = header_storage.get_headers(company_name)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Headers not found for {company_name}"
        )

    return HeaderConfigResponse(**config)


@router.delete(
    "/headers/{company_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="헤더 설정 삭제",
    description="보험사의 HTTP 헤더 설정을 삭제합니다."
)
async def delete_headers(company_name: str):
    """헤더 설정 삭제"""
    header_storage = get_header_storage()

    success = header_storage.delete_headers(company_name)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Headers not found for {company_name}"
        )
