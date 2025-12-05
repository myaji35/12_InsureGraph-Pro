"""
Samsung Life Insurance Crawler

삼성생명 보험 약관 크롤러
"""
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from loguru import logger

from app.services.crawlers.base_crawler import (
    BaseInsurerCrawler,
    InsurerConfig,
    PolicyMetadata,
    CrawlMethod,
    AuthMethod,
)


class SamsungLifeCrawler(BaseInsurerCrawler):
    """삼성생명 크롤러"""

    def __init__(self):
        config = InsurerConfig(
            insurer_code="samsung_life",
            insurer_name="삼성생명",
            base_url="https://www.samsunglife.com",
            product_list_url="https://www.samsunglife.com/product/list",
            crawl_method=CrawlMethod.DYNAMIC_JS,  # JavaScript 필요할 가능성 높음
            auth_method=AuthMethod.NONE,

            # Selectors (실제 웹사이트 구조에 맞게 수정 필요)
            product_list_selector=".product-list .product-item",
            product_name_selector=".product-name",
            product_category_selector=".product-category",
            download_link_selector="a.download-pdf",

            # Pagination
            has_pagination=True,
            pagination_selector=".pagination .next",
            max_pages=50,

            # Rate limiting
            request_delay=1.5,  # 삼성생명은 조금 더 천천히
            max_retries=3,

            # Custom headers
            custom_headers={
                "Referer": "https://www.samsunglife.com",
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            },

            wait_for_selector=".product-list",
            wait_timeout=30000,
        )
        super().__init__(config)

    async def get_product_list(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        삼성생명 상품 목록 조회

        Note: 실제 구현 시 삼성생명 웹사이트 구조에 맞게 수정 필요
        """
        self.logger.info(f"Fetching Samsung Life product list (category: {category})")

        products = []

        try:
            # 실제 구현 예시 (정적 크롤링)
            url = self.config.product_list_url
            if category:
                url = f"{url}?category={category}"

            async with httpx.AsyncClient(headers=self.config.custom_headers) as client:
                response = await client.get(url, timeout=30)

                if response.status_code != 200:
                    self.logger.error(f"Failed to fetch product list: {response.status_code}")
                    return products

                # BeautifulSoup로 파싱
                soup = BeautifulSoup(response.text, "html.parser")
                product_items = soup.select(self.config.product_list_selector)

                for item in product_items:
                    try:
                        # 실제 구조에 맞게 수정
                        product = {
                            "id": item.get("data-product-id", ""),
                            "code": item.get("data-product-code", ""),
                            "name": item.select_one(self.config.product_name_selector).text.strip()
                            if item.select_one(self.config.product_name_selector) else "",
                            "category": item.select_one(self.config.product_category_selector).text.strip()
                            if item.select_one(self.config.product_category_selector) else "",
                            "link": item.select_one("a")["href"]
                            if item.select_one("a") else "",
                        }

                        if product["name"]:
                            products.append(product)

                    except Exception as e:
                        self.logger.warning(f"Failed to parse product item: {e}")
                        continue

            self.logger.info(f"Found {len(products)} Samsung Life products")

        except Exception as e:
            self.logger.error(f"Error fetching Samsung Life products: {e}")

        return products

    async def get_policy_metadata(self, product_id: str) -> PolicyMetadata:
        """
        삼성생명 특정 상품의 약관 메타데이터 조회

        Note: 실제 구현 시 삼성생명 웹사이트 구조에 맞게 수정 필요
        """
        self.logger.info(f"Fetching Samsung Life policy metadata for: {product_id}")

        try:
            # 상품 상세 페이지 URL
            detail_url = f"{self.config.base_url}/product/detail/{product_id}"

            async with httpx.AsyncClient(headers=self.config.custom_headers) as client:
                response = await client.get(detail_url, timeout=30)

                if response.status_code != 200:
                    raise Exception(f"Failed to fetch product detail: {response.status_code}")

                soup = BeautifulSoup(response.text, "html.parser")

                # 약관 다운로드 링크 찾기
                download_link = soup.select_one(self.config.download_link_selector)
                download_url = download_link["href"] if download_link else None

                # 절대 URL로 변환
                if download_url and not download_url.startswith("http"):
                    download_url = f"{self.config.base_url}{download_url}"

                # 메타데이터 구성
                metadata = PolicyMetadata(
                    insurer_code=self.config.insurer_code,
                    insurer_name=self.config.insurer_name,
                    product_name=soup.select_one("h1.product-title").text.strip()
                    if soup.select_one("h1.product-title") else f"Product_{product_id}",
                    product_code=product_id,
                    category=soup.select_one(".product-category").text.strip()
                    if soup.select_one(".product-category") else None,
                    download_url=download_url,
                    effective_date=soup.select_one(".effective-date").text.strip()
                    if soup.select_one(".effective-date") else None,
                    version=soup.select_one(".version").text.strip()
                    if soup.select_one(".version") else "1.0",
                    file_type="pdf",
                )

                return metadata

        except Exception as e:
            self.logger.error(f"Error fetching Samsung Life metadata: {e}")
            # 최소한의 메타데이터 반환
            return PolicyMetadata(
                insurer_code=self.config.insurer_code,
                insurer_name=self.config.insurer_name,
                product_name=f"Unknown_{product_id}",
                product_code=product_id,
            )

    async def download_policy(self, metadata: PolicyMetadata, save_path: str) -> str:
        """
        삼성생명 약관 파일 다운로드
        """
        if not metadata.download_url:
            raise ValueError("No download URL provided")

        self.logger.info(f"Downloading Samsung Life policy: {metadata.product_name}")

        try:
            async with httpx.AsyncClient(headers=self.config.custom_headers) as client:
                response = await client.get(metadata.download_url, timeout=60)

                if response.status_code != 200:
                    raise Exception(f"Download failed: {response.status_code}")

                # 파일 저장
                import os
                os.makedirs(save_path, exist_ok=True)

                filename = f"{self.config.insurer_code}_{metadata.product_code}.pdf"
                filepath = os.path.join(save_path, filename)

                with open(filepath, "wb") as f:
                    f.write(response.content)

                self.logger.info(f"Downloaded to: {filepath}")
                return filepath

        except Exception as e:
            self.logger.error(f"Error downloading Samsung Life policy: {e}")
            raise
