"""
KB Insurance Crawler

KB손해보험 약관 크롤러
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


class KBInsuranceCrawler(BaseInsurerCrawler):
    """KB손해보험 크롤러"""

    def __init__(self):
        config = InsurerConfig(
            insurer_code="kb_insurance",
            insurer_name="KB손해보험",
            base_url="https://www.kbinsure.co.kr",
            product_list_url="https://www.kbinsure.co.kr/product/list",
            crawl_method=CrawlMethod.HYBRID,  # API + 스크래핑 혼합
            auth_method=AuthMethod.NONE,

            # Selectors (실제 웹사이트 구조에 맞게 수정 필요)
            product_list_selector=".insurance-list .insurance-item",
            product_name_selector=".insurance-name",
            product_category_selector=".insurance-type",
            download_link_selector="a.btn-download",

            # Pagination
            has_pagination=True,
            pagination_selector=".page-next",
            max_pages=30,

            # Rate limiting
            request_delay=1.0,
            max_retries=3,

            # Custom headers
            custom_headers={
                "Referer": "https://www.kbinsure.co.kr",
                "Accept": "application/json, text/html",
                "Accept-Language": "ko-KR,ko;q=0.9",
            },

            wait_for_selector=".insurance-list",
            wait_timeout=20000,

            # KB손해보험 특화 설정
            metadata={
                "api_endpoint": "https://api.kbinsure.co.kr/v1/products",
                "requires_session": False,
                "pdf_pattern": r".*약관.*\.pdf$",
            }
        )
        super().__init__(config)

    async def get_product_list(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        KB손해보험 상품 목록 조회

        KB는 API를 제공할 수도 있으므로 우선 API 시도 후 실패 시 스크래핑
        """
        self.logger.info(f"Fetching KB Insurance product list (category: {category})")

        products = []

        try:
            # 방법 1: API 시도 (만약 있다면)
            api_endpoint = self.config.metadata.get("api_endpoint")

            if api_endpoint:
                try:
                    products = await self._fetch_from_api(api_endpoint, category)
                    if products:
                        self.logger.info(f"Fetched {len(products)} products from API")
                        return products
                except Exception as e:
                    self.logger.warning(f"API fetch failed, falling back to scraping: {e}")

            # 방법 2: 웹 스크래핑
            products = await self._fetch_from_web(category)

        except Exception as e:
            self.logger.error(f"Error fetching KB Insurance products: {e}")

        return products

    async def _fetch_from_api(
        self,
        api_endpoint: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """API를 통한 상품 목록 조회"""
        self.logger.info("Trying to fetch from API...")

        params = {}
        if category:
            params["category"] = category

        async with httpx.AsyncClient(headers=self.config.custom_headers) as client:
            response = await client.get(api_endpoint, params=params, timeout=30)

            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code}")

            data = response.json()

            # API 응답 구조에 맞게 파싱
            products = []
            for item in data.get("products", []):
                products.append({
                    "id": item.get("productId"),
                    "code": item.get("productCode"),
                    "name": item.get("productName"),
                    "category": item.get("category"),
                    "link": item.get("detailUrl"),
                })

            return products

    async def _fetch_from_web(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """웹 스크래핑을 통한 상품 목록 조회"""
        self.logger.info("Fetching from web...")

        products = []
        url = self.config.product_list_url

        if category:
            url = f"{url}?type={category}"

        async with httpx.AsyncClient(headers=self.config.custom_headers) as client:
            response = await client.get(url, timeout=30)

            if response.status_code != 200:
                self.logger.error(f"Failed to fetch product list: {response.status_code}")
                return products

            soup = BeautifulSoup(response.text, "html.parser")
            product_items = soup.select(self.config.product_list_selector)

            for item in product_items:
                try:
                    product = {
                        "id": item.get("data-id", ""),
                        "code": item.get("data-code", ""),
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

        self.logger.info(f"Found {len(products)} KB Insurance products")
        return products

    async def get_policy_metadata(self, product_id: str) -> PolicyMetadata:
        """KB손해보험 특정 상품의 약관 메타데이터 조회"""
        self.logger.info(f"Fetching KB Insurance policy metadata for: {product_id}")

        try:
            detail_url = f"{self.config.base_url}/product/view/{product_id}"

            async with httpx.AsyncClient(headers=self.config.custom_headers) as client:
                response = await client.get(detail_url, timeout=30)

                if response.status_code != 200:
                    raise Exception(f"Failed to fetch product detail: {response.status_code}")

                soup = BeautifulSoup(response.text, "html.parser")

                # KB는 여러 약관 파일이 있을 수 있음 (주계약, 특약 등)
                download_links = soup.select(self.config.download_link_selector)

                # 메인 약관 선택 (첫 번째 또는 "주계약" 키워드 포함)
                main_download_url = None
                for link in download_links:
                    href = link.get("href", "")
                    text = link.text.strip()

                    if "주계약" in text or "약관" in text:
                        main_download_url = href
                        break

                if not main_download_url and download_links:
                    main_download_url = download_links[0].get("href")

                # 절대 URL로 변환
                if main_download_url and not main_download_url.startswith("http"):
                    main_download_url = f"{self.config.base_url}{main_download_url}"

                metadata = PolicyMetadata(
                    insurer_code=self.config.insurer_code,
                    insurer_name=self.config.insurer_name,
                    product_name=soup.select_one("h1.product-title").text.strip()
                    if soup.select_one("h1.product-title") else f"Product_{product_id}",
                    product_code=product_id,
                    category=soup.select_one(".insurance-type").text.strip()
                    if soup.select_one(".insurance-type") else None,
                    download_url=main_download_url,
                    effective_date=soup.select_one(".effective-date").text.strip()
                    if soup.select_one(".effective-date") else None,
                    version=soup.select_one(".version").text.strip()
                    if soup.select_one(".version") else "1.0",
                    file_type="pdf",
                    additional_info={
                        "total_documents": len(download_links),
                        "document_types": [link.text.strip() for link in download_links],
                    }
                )

                return metadata

        except Exception as e:
            self.logger.error(f"Error fetching KB Insurance metadata: {e}")
            return PolicyMetadata(
                insurer_code=self.config.insurer_code,
                insurer_name=self.config.insurer_name,
                product_name=f"Unknown_{product_id}",
                product_code=product_id,
            )

    async def download_policy(self, metadata: PolicyMetadata, save_path: str) -> str:
        """KB손해보험 약관 파일 다운로드"""
        if not metadata.download_url:
            raise ValueError("No download URL provided")

        self.logger.info(f"Downloading KB Insurance policy: {metadata.product_name}")

        try:
            async with httpx.AsyncClient(headers=self.config.custom_headers) as client:
                response = await client.get(metadata.download_url, timeout=60)

                if response.status_code != 200:
                    raise Exception(f"Download failed: {response.status_code}")

                import os
                os.makedirs(save_path, exist_ok=True)

                filename = f"{self.config.insurer_code}_{metadata.product_code}.pdf"
                filepath = os.path.join(save_path, filename)

                with open(filepath, "wb") as f:
                    f.write(response.content)

                self.logger.info(f"Downloaded to: {filepath}")
                return filepath

        except Exception as e:
            self.logger.error(f"Error downloading KB Insurance policy: {e}")
            raise
