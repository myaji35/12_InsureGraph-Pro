"""
Playwright Crawler Service

Playwright를 사용한 실제 웹 크롤링 서비스
"""
import os
import asyncio
from typing import Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path

from loguru import logger

try:
    from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright is not installed. Test crawling will be limited.")


class PlaywrightCrawler:
    """Playwright 기반 웹 크롤러"""

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
        user_agent: Optional[str] = None
    ):
        """
        Initialize Playwright crawler

        Args:
            headless: 헤드리스 모드 사용 여부
            timeout: 페이지 로드 타임아웃 (ms)
            user_agent: 사용자 정의 User-Agent
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is not installed. "
                "Install it with: pip install playwright && playwright install chromium"
            )

        self.headless = headless
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def __aenter__(self):
        """컨텍스트 매니저 진입"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        await self.close()

    async def initialize(self):
        """브라우저 초기화"""
        logger.info("Initializing Playwright browser...")

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless
        )

        # Create context with custom user agent
        self.context = await self.browser.new_context(
            user_agent=self.user_agent,
            viewport={'width': 1920, 'height': 1080}
        )

        # Create page
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout)

        logger.info("Playwright browser initialized")

    async def close(self):
        """브라우저 종료"""
        if self.page:
            await self.page.close()

        if self.context:
            await self.context.close()

        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

        logger.info("Playwright browser closed")

    async def crawl_page(
        self,
        url: str,
        custom_headers: Optional[Dict[str, str]] = None,
        wait_for_selector: Optional[str] = None,
        wait_time: int = 2000
    ) -> Tuple[str, Dict]:
        """
        페이지 크롤링

        Args:
            url: 크롤링할 URL
            custom_headers: 사용자 정의 HTTP 헤더
            wait_for_selector: 대기할 CSS 셀렉터
            wait_time: 추가 대기 시간 (ms)

        Returns:
            Tuple[str, Dict]: (HTML 콘텐츠, 메타데이터)
        """
        if not self.page:
            raise RuntimeError("Browser not initialized. Call initialize() first.")

        logger.info(f"Crawling: {url}")

        # Set custom headers if provided
        if custom_headers:
            await self.page.set_extra_http_headers(custom_headers)
            logger.debug(f"Custom headers set: {custom_headers}")

        try:
            # Navigate to URL
            start_time = datetime.now()
            response = await self.page.goto(
                url,
                wait_until='networkidle',
                timeout=self.timeout
            )

            # Wait for specific selector if provided
            if wait_for_selector:
                try:
                    await self.page.wait_for_selector(
                        wait_for_selector,
                        timeout=wait_time
                    )
                    logger.info(f"Selector found: {wait_for_selector}")
                except PlaywrightTimeout:
                    logger.warning(f"Selector not found within timeout: {wait_for_selector}")

            # Additional wait for dynamic content
            await asyncio.sleep(wait_time / 1000)

            # Get page content
            html_content = await self.page.content()

            # Get page metadata
            title = await self.page.title()
            url_final = self.page.url

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            metadata = {
                'url': url,
                'final_url': url_final,
                'title': title,
                'status_code': response.status if response else None,
                'content_length': len(html_content),
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            }

            logger.info(
                f"Page crawled successfully: {title} "
                f"({len(html_content)} bytes in {duration:.2f}s)"
            )

            return html_content, metadata

        except PlaywrightTimeout as e:
            logger.error(f"Timeout while crawling {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            raise

    async def save_html(
        self,
        html_content: str,
        company_name: str,
        output_dir: str = "data/crawl_results"
    ) -> str:
        """
        HTML 파일 저장

        Args:
            html_content: HTML 콘텐츠
            company_name: 보험사명
            output_dir: 출력 디렉토리

        Returns:
            str: 저장된 파일 경로
        """
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{company_name}_{timestamp}.html"
        file_path = output_path / filename

        # Save HTML
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        file_size = os.path.getsize(file_path)
        logger.info(f"HTML saved: {file_path} ({file_size} bytes)")

        return str(file_path)

    async def take_screenshot(
        self,
        output_path: str,
        full_page: bool = True
    ):
        """
        스크린샷 저장

        Args:
            output_path: 저장 경로
            full_page: 전체 페이지 스크린샷 여부
        """
        if not self.page:
            raise RuntimeError("Browser not initialized")

        await self.page.screenshot(
            path=output_path,
            full_page=full_page
        )

        logger.info(f"Screenshot saved: {output_path}")


async def test_crawler():
    """크롤러 테스트"""
    async with PlaywrightCrawler(headless=True) as crawler:
        # Test URL
        url = "https://www.samsungfire.com"

        # Crawl page
        html, metadata = await crawler.crawl_page(url)

        print(f"Title: {metadata['title']}")
        print(f"Content length: {metadata['content_length']} bytes")
        print(f"Duration: {metadata['duration']:.2f}s")

        # Save HTML
        file_path = await crawler.save_html(html, "삼성화재")
        print(f"Saved to: {file_path}")


if __name__ == "__main__":
    asyncio.run(test_crawler())
