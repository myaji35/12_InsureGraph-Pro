"""
Samsung Fire & Marine Insurance Crawler

삼성화재 보험 약관 크롤러
동적 JavaScript를 사용하는 4단계 선택 시스템 크롤러
"""
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import httpx
from loguru import logger

from app.services.crawlers.base_crawler import (
    BaseInsurerCrawler,
    InsurerConfig,
    PolicyMetadata,
    CrawlMethod,
)
from app.services.playwright_crawler import PlaywrightCrawler


class SamsungFireCrawler(BaseInsurerCrawler):
    """
    삼성화재 크롤러

    페이지 구조:
    - Step1: 상품종류 (자동차, 장기, 일반, 퇴직연금, 퇴직보험)
    - Step2: 상품명 (대면, TM/홈쇼핑, 인터넷, 방카슈랑스 등)
    - Step3: 구체적 상품명 (동적 로딩)
    - Step4: 판매기간 (동적 로딩)
    - 다운로드: PDF 버튼 (사업방법서, 상품요약서, 보험약관, 상품설명서)
    """

    def __init__(self):
        """삼성화재 크롤러 초기화"""
        config = InsurerConfig(
            insurer_code="samsung_fire",
            insurer_name="삼성화재",
            base_url="https://www.samsungfire.com",
            product_list_url="https://www.samsungfire.com/vh/page/VH.HPIF0103.do",
            crawl_method=CrawlMethod.DYNAMIC_JS,
            request_delay=1.5,
            wait_timeout=30000,
        )
        super().__init__(config)
        self.playwright_crawler: Optional[PlaywrightCrawler] = None

    async def initialize_browser(self):
        """브라우저 초기화"""
        if not self.playwright_crawler:
            self.playwright_crawler = PlaywrightCrawler(
                headless=True,
                timeout=self.config.wait_timeout
            )
            await self.playwright_crawler.initialize()
            self.logger.info("Playwright browser initialized for Samsung Fire")

    async def close_browser(self):
        """브라우저 종료"""
        if self.playwright_crawler:
            await self.playwright_crawler.close()
            self.playwright_crawler = None
            self.logger.info("Playwright browser closed")

    async def get_product_list(self, category: Optional[str] = None, progress_callback=None) -> List[Dict[str, Any]]:
        """
        삼성화재 상품 목록 가져오기

        Args:
            category: "active" (판매상품) 또는 "discontinued" (판매중지상품)
                     None이면 모두 가져옴
            progress_callback: 진행 상황 업데이트 콜백 함수

        Returns:
            상품 목록
        """
        await self.initialize_browser()

        if not self.playwright_crawler or not self.playwright_crawler.page:
            raise RuntimeError("Browser not initialized")

        page = self.playwright_crawler.page

        try:
            # 페이지 로드
            self.logger.info(f"Navigating to: {self.config.product_list_url}")
            await page.goto(self.config.product_list_url, wait_until="networkidle")
            await asyncio.sleep(3)

            products = []

            # 판매상품 크롤링
            if category is None or category == "active":
                self.logger.info("Crawling active products...")
                active_products = await self._crawl_tab("active", page, progress_callback)
                products.extend(active_products)

            # 판매중지 상품 크롤링
            if category is None or category == "discontinued":
                self.logger.info("Crawling discontinued products...")
                discontinued_products = await self._crawl_tab("discontinued", page, progress_callback)
                products.extend(discontinued_products)

            self.logger.info(f"Total products found: {len(products)}")
            return products

        except Exception as e:
            self.logger.error(f"Failed to get product list: {e}")
            raise

    async def _crawl_tab(self, tab_type: str, page, progress_callback=None) -> List[Dict[str, Any]]:
        """
        특정 탭의 상품 목록 크롤링

        Args:
            tab_type: "active" 또는 "discontinued"
            page: Playwright Page 객체
            progress_callback: 진행 상황 업데이트 콜백 함수

        Returns:
            상품 목록
        """
        # products 리스트를 try 블록 외부에 선언하여 에러 발생 시에도 유지
        products = []

        try:
            # 탭 클릭
            if tab_type == "discontinued":
                # 판매중지 상품 탭 클릭
                tab_button = await page.query_selector("a.ui-tab-btn:has-text('판매중지 상품')")
                if tab_button:
                    await tab_button.click()
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(2)

            # Step1: 상품종류 목록 (자동차, 장기, 일반, 퇴직연금, 퇴직보험)
            product_types = await page.query_selector_all("#depth1 li a")
            self.logger.info(f"Found {len(product_types)} product types")

            # 진행 상황 업데이트
            if progress_callback:
                await progress_callback(
                    current_step="crawling",
                    total_product_types=len(product_types),
                    current_product_type=0
                )

            for type_idx, type_elem in enumerate(product_types):
                type_name = await type_elem.inner_text()
                type_name = type_name.strip()
                self.logger.info(f"[삼성화재 크롤링] 상품종류 {type_idx + 1}/{len(product_types)}: {type_name}")

                # 진행 상황 업데이트
                if progress_callback:
                    await progress_callback(
                        current_product_type=type_idx + 1,
                        current_product_type_name=type_name
                    )

                # Step1 클릭
                await type_elem.click()
                await asyncio.sleep(self.config.request_delay)

                # Step2: 상품명 목록 (대면, TM/홈쇼핑, 인터넷 등)
                product_categories = await page.query_selector_all("#product_gubun > li > a")
                self.logger.info(f"  Found {len(product_categories)} categories")

                # 진행 상황 업데이트
                if progress_callback:
                    await progress_callback(
                        total_categories=len(product_categories),
                        current_category=0
                    )

                for cat_idx, cat_elem in enumerate(product_categories):
                    cat_name = await cat_elem.inner_text()
                    cat_name = cat_name.strip()
                    self.logger.info(f"[삼성화재 크롤링] {type_name} > 카테고리 {cat_idx + 1}/{len(product_categories)}: {cat_name}")

                    # 진행 상황 업데이트
                    if progress_callback:
                        await progress_callback(
                            current_category=cat_idx + 1,
                            current_category_name=cat_name,
                            total_documents_found=len(products)
                        )

                    # Step2 클릭
                    await cat_elem.click()
                    await asyncio.sleep(self.config.request_delay)

                    # Step3: 하위 상품명이 있는 경우 (예: 대면 > 운전자, 자녀 등)
                    sub_categories = await page.query_selector_all("#depth3 li a")

                    if len(sub_categories) > 0:
                        # 하위 카테고리가 있는 경우
                        self.logger.info(f"    Found {len(sub_categories)} sub-categories")
                        for sub_idx, sub_elem in enumerate(sub_categories):
                            sub_name = await sub_elem.inner_text()
                            sub_name = sub_name.strip()
                            self.logger.info(f"    Processing sub-category {sub_idx + 1}/{len(sub_categories)}: {sub_name}")

                            await sub_elem.click()
                            await asyncio.sleep(self.config.request_delay)

                            # 상품 목록 추출
                            await self._extract_products(page, products, type_name, cat_name, sub_name, tab_type, progress_callback)
                    else:
                        # 하위 카테고리가 없는 경우 바로 상품 목록 추출
                        await self._extract_products(page, products, type_name, cat_name, None, tab_type, progress_callback)

            self.logger.info(f"Total products found in {tab_type} tab: {len(products)}")
            return products

        except Exception as e:
            self.logger.error(f"Failed to crawl tab '{tab_type}': {e}")
            import traceback
            traceback.print_exc()
            # 에러가 발생해도 이미 수집한 문서는 반환
            self.logger.warning(f"Returning {len(products)} products collected before error")
            return products

    async def _extract_products(
        self,
        page,
        products: List[Dict[str, Any]],
        type_name: str,
        cat_name: str,
        sub_name: Optional[str],
        tab_type: str,
        progress_callback=None
    ):
        """
        현재 선택된 카테고리의 상품 목록 추출

        Args:
            page: Playwright Page 객체
            products: 상품 목록 (추가될 리스트)
            type_name: 상품종류 (예: 장기보험)
            cat_name: 카테고리 (예: 대면)
            sub_name: 하위 카테고리 (예: 운전자) - 없으면 None
            tab_type: "active" 또는 "discontinued"
        """
        try:
            # Step3: 상품명 목록
            product_list = await page.query_selector_all("#product_list li a")

            if len(product_list) == 0:
                self.logger.warning(f"      No products found for {type_name} > {cat_name} > {sub_name}")
                return

            self.logger.info(f"      Found {len(product_list)} products")

            for prod_idx, prod_elem in enumerate(product_list):
                prod_name = await prod_elem.inner_text()
                prod_name = prod_name.strip()

                # 상품 클릭
                await prod_elem.click()
                await asyncio.sleep(self.config.request_delay)

                # Step4: 판매기간 목록
                date_list = await page.query_selector_all("#date_list li a")

                if len(date_list) == 0:
                    self.logger.warning(f"        No sale periods found for {prod_name}")
                    continue

                for date_idx, date_elem in enumerate(date_list):
                    date_text = await date_elem.inner_text()
                    date_text = date_text.strip()

                    # 판매기간 클릭
                    await date_elem.click()
                    await asyncio.sleep(1)

                    # PDF 다운로드 버튼 확인
                    pdf_buttons = await page.query_selector_all("#pdfDiv2 button:not([disabled])")

                    pdf_links_list = []

                    # 보험약관 버튼만 찾기
                    yakgwan_button = None
                    for button in pdf_buttons:
                        button_text = await button.inner_text()
                        button_text = button_text.strip()
                        if "보험약관" in button_text:
                            yakgwan_button = button
                            break

                    if not yakgwan_button:
                        # 보험약관이 없으면 스킵
                        continue

                    # 네트워크 응답을 감지하여 PDF URL 캡처
                    captured_pdf_url = None

                    async def handle_response(response):
                        nonlocal captured_pdf_url
                        url = response.url
                        content_type = response.headers.get("content-type", "")

                        # PDF 파일 응답 감지
                        if ("application/pdf" in content_type) or url.endswith('.pdf') or '/pdf/' in url.lower():
                            # 쿼리 파라미터는 유지 (다운로드에 필요할 수 있음)
                            captured_pdf_url = url
                            self.logger.info(f"          Captured PDF URL: {url}")

                    # 네트워크 리스너 등록
                    page.on("response", handle_response)

                    try:
                        # 보험약관 버튼 클릭
                        await yakgwan_button.click()
                        await asyncio.sleep(1.0)  # PDF URL이 캡처될 시간을 충분히 줌

                        if captured_pdf_url:
                            pdf_links_list.append({
                                "type": "보험약관",
                                "url": captured_pdf_url
                            })
                            self.logger.info(f"          ✓ PDF URL added: {captured_pdf_url}")
                        else:
                            self.logger.warning(f"          No PDF URL captured for {prod_name}")

                    except Exception as e:
                        self.logger.error(f"          Failed to click button: {e}")
                    finally:
                        # 리스너 제거
                        try:
                            page.remove_listener("response", handle_response)
                        except:
                            pass

                    # 보험약관이 없으면 스킵
                    if not pdf_links_list:
                        continue

                    # 상품 정보 저장
                    full_name = prod_name
                    if sub_name:
                        full_name = f"{type_name} > {cat_name} > {sub_name} > {prod_name}"
                    else:
                        full_name = f"{type_name} > {cat_name} > {prod_name}"

                    product_info = {
                        "id": f"samsung_fire_{tab_type}_{len(products)}",
                        "name": prod_name,
                        "full_name": full_name,
                        "type": type_name,
                        "category": cat_name,
                        "sub_category": sub_name,
                        "sale_period": date_text,
                        "tab": tab_type,
                        "insurer": "삼성화재",
                        "source_url": "https://www.samsungfire.com/vh/page/VH.HPIF0103.do",
                        "pdf_links": pdf_links_list,
                        "pdf_count": len(pdf_links_list)
                    }

                    products.append(product_info)
                    self.logger.info(f"[삼성화재 크롤링] ✓ 수집완료 [{len(products)}건] {full_name} ({date_text}) - {len(pdf_links_list)}개 PDF")

                    # 진행 상황 업데이트
                    if progress_callback:
                        await progress_callback(total_documents_found=len(products))

        except Exception as e:
            self.logger.error(f"Failed to extract products: {e}")
            import traceback
            traceback.print_exc()

    async def get_policy_metadata(self, product_id: str) -> PolicyMetadata:
        """
        특정 상품의 약관 메타데이터 가져오기

        Args:
            product_id: 상품 ID

        Returns:
            약관 메타데이터
        """
        # TODO: 실제 구현
        # 1. 상품 페이지로 이동
        # 2. 약관 링크 찾기
        # 3. 메타데이터 추출

        metadata = PolicyMetadata(
            insurer_code=self.config.insurer_code,
            insurer_name=self.config.insurer_name,
            product_name=f"Product_{product_id}",
            product_code=product_id,
            category="insurance",
            file_type="pdf"
        )

        return metadata

    async def download_policy(self, metadata: PolicyMetadata, save_path: str) -> str:
        """
        약관 PDF 다운로드

        Args:
            metadata: 약관 메타데이터
            save_path: 저장 디렉토리

        Returns:
            다운로드된 파일 경로
        """
        if not metadata.download_url:
            raise ValueError("Download URL not provided in metadata")

        try:
            # 저장 디렉토리 생성
            save_dir = Path(save_path)
            save_dir.mkdir(parents=True, exist_ok=True)

            # 파일명 생성
            filename = f"{metadata.insurer_code}_{metadata.product_code}.{metadata.file_type}"
            file_path = save_dir / filename

            # 다운로드
            async with httpx.AsyncClient() as client:
                response = await client.get(metadata.download_url, timeout=60)
                response.raise_for_status()

                with open(file_path, "wb") as f:
                    f.write(response.content)

            self.logger.info(f"Downloaded policy: {file_path}")
            return str(file_path)

        except Exception as e:
            self.logger.error(f"Failed to download policy: {e}")
            raise

    async def crawl_all_policies_with_browser(
        self,
        categories: Optional[List[str]] = None,
        save_dir: Optional[str] = None
    ) -> List[PolicyMetadata]:
        """
        모든 약관 크롤링 (브라우저 자동 열고 닫음)

        Args:
            categories: 크롤링할 카테고리 ("active", "discontinued")
            save_dir: 파일 저장 디렉토리

        Returns:
            크롤링된 약관 메타데이터 목록
        """
        try:
            await self.initialize_browser()
            return await self.crawl_all_policies(categories, save_dir)
        finally:
            await self.close_browser()


# 크롤러 등록용 함수
def register_samsung_fire_crawler():
    """삼성화재 크롤러를 등록용 함수"""
    try:
        from app.services.crawlers.crawler_registry import register_crawler
        register_crawler("samsung_fire", SamsungFireCrawler)
        logger.info("Samsung Fire crawler registered")
    except ImportError:
        logger.warning("Crawler registry not available")


# 테스트 함수
async def test_samsung_fire_crawler():
    """삼성화재 크롤러 테스트"""
    crawler = SamsungFireCrawler()

    try:
        # 연결 테스트
        is_connected = await crawler.test_connection()
        print(f"Connection test: {'✓ PASS' if is_connected else '✗ FAIL'}")

        # 상품 목록 가져오기 테스트 (판매상품만)
        print("\nFetching active products...")
        products = await crawler.get_product_list(category="active")
        print(f"Found {len(products)} active products")

        for i, product in enumerate(products[:5], 1):  # 처음 5개만 출력
            print(f"{i}. {product.get('full_name', 'N/A')}")
            print(f"   판매기간: {product.get('sale_period', 'N/A')}")
            print(f"   PDF 개수: {product.get('pdf_count', 0)}")

    finally:
        await crawler.close_browser()


if __name__ == "__main__":
    # 테스트 실행
    asyncio.run(test_samsung_fire_crawler())
