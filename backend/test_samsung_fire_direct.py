"""
삼성화재 크롤러 직접 테스트 (수정된 버전)
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.services.crawlers.samsung_fire_crawler import SamsungFireCrawler
from loguru import logger


async def test_crawler():
    """크롤러 테스트"""
    logger.info("Starting Samsung Fire crawler test")

    crawler = SamsungFireCrawler()

    try:
        # 브라우저 초기화
        await crawler.initialize_browser()

        # 판매상품만 크롤링
        logger.info("Fetching active products...")
        products = await crawler.get_product_list(category="active")

        logger.info(f"✅ Total products collected: {len(products)}")

        # 처음 5개만 출력
        for i, product in enumerate(products[:5], 1):
            logger.info(f"{i}. {product.get('full_name', 'N/A')}")
            logger.info(f"   판매기간: {product.get('sale_period', 'N/A')}")
            logger.info(f"   PDF 개수: {product.get('pdf_count', 0)}")

            # PDF URL 출력
            for pdf_link in product.get('pdf_links', []):
                logger.info(f"   - {pdf_link.get('type')}: {pdf_link.get('url')}")

        return products

    finally:
        await crawler.close_browser()


if __name__ == "__main__":
    products = asyncio.run(test_crawler())
    print(f"\n\n{'='*80}")
    print(f"Total products collected: {len(products)}")
    print(f"{'='*80}")
