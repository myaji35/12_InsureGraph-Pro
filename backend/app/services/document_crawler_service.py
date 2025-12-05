"""
Document Crawler Service

Playwright + AI를 사용한 보험약관 문서 크롤링 서비스
"""
from typing import List, Dict, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.services.playwright_crawler import PlaywrightCrawler
from app.services.ai_pdf_extractor import AIPdfExtractor


class DocumentCrawlerService:
    """문서 크롤링 서비스"""

    def __init__(self, db: AsyncSession):
        """
        Initialize Document Crawler Service

        Args:
            db: SQLAlchemy AsyncSession for database operations
        """
        self.pdf_extractor = AIPdfExtractor()
        self.db = db

    async def crawl_insurer_documents(
        self,
        insurer: str,
        urls: Optional[List[str]] = None
    ) -> Dict:
        """
        보험사의 문서를 크롤링

        Args:
            insurer: 보험사명
            urls: 크롤링할 URL 리스트 (None인 경우 DB에서 가져옴)

        Returns:
            Dict: 크롤링 결과
                - total_urls: 크롤링한 URL 수
                - total_documents: 발견한 문서 수
                - documents: 문서 리스트
        """
        logger.info(f"Starting document crawling for {insurer}")

        # 삼성화재는 전용 크롤러 사용
        if insurer == "삼성화재":
            urls_from_db = await self._get_crawler_urls(insurer)
            if not urls_from_db:
                logger.warning(f"No URLs found for {insurer}")
                return {
                    'total_urls': 0,
                    'total_documents': 0,
                    'documents': []
                }
            return await self._crawl_samsung_fire(urls_from_db)

        # 다른 보험사는 기본 범용 크롤러 사용
        # (Playwright + AI PDF 분석)

        # URLs를 DB에서 가져오기 (None인 경우)
        if urls is None:
            urls = await self._get_crawler_urls(insurer)

        if not urls:
            logger.warning(f"No URLs found for {insurer}")
            return {
                'total_urls': 0,
                'total_documents': 0,
                'documents': []
            }

        all_documents = []

        # Playwright 크롤러 초기화
        async with PlaywrightCrawler(headless=True) as crawler:
            for url in urls:
                try:
                    # 페이지 크롤링
                    html_content, metadata = await crawler.crawl_page(
                        url=url,
                        wait_time=3000  # 3초 대기
                    )

                    logger.info(
                        f"Crawled {url}: {metadata['content_length']} bytes"
                    )

                    # AI로 PDF 링크 추출
                    pdf_links = await self.pdf_extractor.extract_pdf_links_from_html(
                        html_content=html_content,
                        insurer=insurer,
                        url=url
                    )

                    # 결과에 메타데이터 추가
                    for doc in pdf_links:
                        doc['source_url'] = url
                        doc['insurer'] = insurer

                    all_documents.extend(pdf_links)

                    logger.info(f"Extracted {len(pdf_links)} documents from {url}")

                except Exception as e:
                    logger.error(f"Failed to crawl {url}: {e}")
                    continue

        logger.info(
            f"Crawling completed for {insurer}: "
            f"{len(urls)} URLs, {len(all_documents)} documents"
        )

        return {
            'total_urls': len(urls),
            'total_documents': len(all_documents),
            'documents': all_documents
        }

    async def _get_crawler_urls(self, insurer: str) -> List[str]:
        """
        DB에서 크롤러 URL 목록 가져오기

        Args:
            insurer: 보험사명

        Returns:
            List[str]: URL 리스트
        """
        query = text("""
            SELECT url
            FROM crawler_urls
            WHERE insurer = :insurer AND enabled = true
            ORDER BY created_at DESC
        """)

        result = await self.db.execute(query, {"insurer": insurer})
        rows = result.fetchall()

        urls = [row.url for row in rows]
        logger.info(f"Found {len(urls)} enabled URLs for {insurer}")

        return urls

    async def save_crawled_documents(
        self,
        documents: List[Dict]
    ) -> int:
        """
        크롤링한 문서를 DB에 저장

        Args:
            documents: 문서 리스트

        Returns:
            int: 저장된 문서 수
        """
        if not documents:
            return 0

        saved_count = 0

        for doc in documents:
            try:
                # crawler_documents 테이블에 저장
                query = text("""
                    INSERT INTO crawler_documents (
                        insurer,
                        title,
                        pdf_url,
                        category,
                        product_type,
                        source_url,
                        status
                    ) VALUES (:insurer, :title, :pdf_url, :category, :product_type, :source_url, :status)
                    ON CONFLICT (pdf_url) DO UPDATE
                    SET
                        title = EXCLUDED.title,
                        category = EXCLUDED.category,
                        product_type = EXCLUDED.product_type,
                        updated_at = CURRENT_TIMESTAMP
                """)

                await self.db.execute(query, {
                    "insurer": doc['insurer'],
                    "title": doc['title'],
                    "pdf_url": doc['url'],
                    "category": doc['category'],
                    "product_type": doc['product_type'],
                    "source_url": doc['source_url'],
                    "status": 'pending'  # 초기 상태는 pending
                })
                saved_count += 1

            except Exception as e:
                logger.error(f"Failed to save document {doc.get('title')}: {e}")
                continue

        # Commit the transaction
        await self.db.commit()

        logger.info(f"Saved {saved_count} documents to database")
        return saved_count

    async def _crawl_samsung_fire(self, urls: List[str]) -> Dict:
        """
        삼성화재 전용 크롤러 실행

        삼성화재는 고유한 4단계 선택 시스템을 사용합니다.
        등록된 URL을 기준으로 크롤링을 시작합니다.

        Args:
            urls: 크롤링할 URL 목록 (보통 상품 공시 페이지)

        Returns:
            Dict: 크롤링 결과
        """
        logger.info(f"Using Samsung Fire specialized crawler with {len(urls)} URLs")

        try:
            from app.services.crawlers.samsung_fire_crawler import SamsungFireCrawler
            from app.services.crawler_progress_tracker import CrawlerProgressTracker

            # 진행 상황 추적 시작
            await CrawlerProgressTracker.start_crawling("삼성화재")

            # 삼성화재 크롤러 초기화 및 실행
            crawler = SamsungFireCrawler()
            await crawler.initialize_browser()

            # 진행 상황 업데이트 콜백
            async def progress_callback(**update_data):
                await CrawlerProgressTracker.update_progress("삼성화재", **update_data)

            try:
                # 판매상품만 크롤링 (시간 절약)
                products = await crawler.get_product_list(category="active", progress_callback=progress_callback)

                logger.info(f"Samsung Fire crawler found {len(products)} products")

                # 결과를 문서 형식으로 변환
                documents = []
                for product in products:
                    # 각 상품의 PDF 링크 정보 추출
                    pdf_links = product.get('pdf_links', [])

                    for pdf_link in pdf_links:
                        documents.append({
                            'insurer': '삼성화재',
                            'title': f"{product['name']} - {pdf_link.get('type', 'PDF')} ({product['sale_period']})",
                            'url': pdf_link['url'],
                            'category': '약관' if '약관' in pdf_link.get('type', '') else '기타',
                            'product_type': product.get('type', '자동차보험'),
                            'source_url': product.get('source_url', 'https://www.samsungfire.com/vh/page/VH.HPIF0103.do')
                        })

                # 크롤링 완료
                await CrawlerProgressTracker.complete_crawling("삼성화재", len(documents))

                return {
                    'total_urls': len(urls),
                    'total_documents': len(documents),
                    'documents': documents
                }

            finally:
                await crawler.close_browser()

        except Exception as e:
            logger.error(f"Samsung Fire crawler failed: {e}")
            import traceback
            traceback.print_exc()

            # 크롤링 실패 기록
            await CrawlerProgressTracker.fail_crawling("삼성화재", str(e))

            return {
                'total_urls': 0,
                'total_documents': 0,
                'documents': []
            }
