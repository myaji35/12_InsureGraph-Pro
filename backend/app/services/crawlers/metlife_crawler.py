"""
MetLife Insurance Crawler

메트라이프 보험 약관 크롤러
- 판매상품목록: https://brand.metlife.co.kr/pn/mcvrgProd/retrieveMcvrgProdMain.do
- 판매중지상품: https://brand.metlife.co.kr/pn/saleStop/retrieveSaleStopProdMain.do
"""
import asyncio
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import aiohttp
from loguru import logger

from app.services.crawlers.base_crawler import (
    BaseInsurerCrawler,
    InsurerConfig,
    CrawlMethod,
    AuthMethod,
    PolicyMetadata
)


class MetLifeCrawler(BaseInsurerCrawler):
    """메트라이프 보험 약관 크롤러"""

    def __init__(self):
        config = InsurerConfig(
            insurer_code="metlife",
            insurer_name="메트라이프생명",
            base_url="https://brand.metlife.co.kr",
            crawl_method=CrawlMethod.STATIC_HTML,
            auth_method=AuthMethod.NONE,
            request_delay=0.5,
            max_retries=3,
            custom_headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://brand.metlife.co.kr/pn/paReal/insuProductDisclMain.do'
            }
        )
        super().__init__(config)

        # 메트라이프 엔드포인트
        self.active_products_url = f"{config.base_url}/pn/mcvrgProd/retrieveMcvrgProdMain.do"
        self.discontinued_products_url = f"{config.base_url}/pn/saleStop/retrieveSaleStopProdMain.do"
        self.download_url_template = f"{config.base_url}/pn/mcvrgProd/mcvrgProdDownloadFile.do"

    async def get_product_list(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        상품 목록 가져오기

        Args:
            category: 'active' (판매상품), 'discontinued' (판매중지), None (전체)

        Returns:
            상품 목록
        """
        all_products = []

        if category is None or category == 'active':
            self.logger.info("Fetching active products...")
            active_products = await self._fetch_products_from_page(
                self.active_products_url,
                is_active=True
            )
            all_products.extend(active_products)
            self.logger.info(f"Found {len(active_products)} active products")

        if category is None or category == 'discontinued':
            self.logger.info("Fetching discontinued products...")
            discontinued_products = await self._fetch_products_from_page(
                self.discontinued_products_url,
                is_active=False
            )
            all_products.extend(discontinued_products)
            self.logger.info(f"Found {len(discontinued_products)} discontinued products")

        self.logger.info(f"Total products found: {len(all_products)}")
        return all_products

    async def _fetch_products_from_page(self, url: str, is_active: bool) -> List[Dict[str, Any]]:
        """
        특정 페이지에서 상품 목록 가져오기

        Args:
            url: 페이지 URL
            is_active: 판매중 여부

        Returns:
            상품 목록
        """
        products = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.config.custom_headers) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to fetch {url}: HTTP {response.status}")
                        return products

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # 상품 테이블 찾기
                    tables = soup.find_all('table', class_='tbl_list')

                    for table in tables:
                        # 테이블의 tbody에서 상품 행 추출
                        rows = table.find('tbody').find_all('tr', recursive=False)

                        for row in rows:
                            try:
                                product = await self._parse_product_row(row, is_active)
                                if product:
                                    products.append(product)
                            except Exception as e:
                                self.logger.warning(f"Failed to parse row: {e}")
                                continue

        except Exception as e:
            self.logger.error(f"Error fetching products from {url}: {e}")

        return products

    async def _parse_product_row(self, row, is_active: bool) -> Optional[Dict[str, Any]]:
        """
        테이블 행에서 상품 정보 파싱

        Args:
            row: BeautifulSoup 테이블 행
            is_active: 판매중 여부

        Returns:
            상품 정보 딕셔너리 또는 None
        """
        try:
            cells = row.find_all('td')
            if len(cells) < 7:
                return None

            # 컬럼 구조: 구분, 상품명, 판매기간, 사업방법서, 상품요약서, 약관, 상품설명서, 특약
            product_name_cell = cells[1]
            sales_period_cell = cells[2]
            terms_cell = cells[5] if len(cells) > 5 else None

            # 상품명
            product_name = product_name_cell.get_text(strip=True)
            if not product_name or product_name == '-':
                return None

            # 판매기간
            sales_period = sales_period_cell.get_text(strip=True)

            # 약관 다운로드 링크 (fnum=03)
            download_url = None
            if terms_cell:
                download_link = terms_cell.find('a', class_='btn_file')
                if download_link and 'onclick' in download_link.attrs:
                    onclick = download_link['onclick']
                    # onclick="mcvrgProdFileDown('12345', '678', '03')"
                    match = re.search(r"mcvrgProdFileDown\('(\d+)',\s*'(\d+)',\s*'(\d+)'\)", onclick)
                    if match:
                        ins_prod_seq = match.group(1)
                        seq = match.group(2)
                        fnum = match.group(3)
                        download_url = f"{self.download_url_template}?insProdSeq={ins_prod_seq}&seq={seq}&fnum={fnum}"

            # 약관이 없으면 스킵
            if not download_url:
                return None

            # 상품 유형 추출 (상품명에서 "종신", "정기", "연금" 등 키워드 추출)
            product_type = self._extract_product_type(product_name)

            return {
                "product_name": product_name,
                "product_type": product_type,
                "sales_period": sales_period,
                "download_url": download_url,
                "is_active": is_active,
                "category": "판매상품" if is_active else "판매중지상품"
            }

        except Exception as e:
            self.logger.warning(f"Error parsing product row: {e}")
            return None

    def _extract_product_type(self, product_name: str) -> str:
        """
        상품명에서 상품 유형 추출

        Args:
            product_name: 상품명

        Returns:
            상품 유형
        """
        type_keywords = {
            "종신": "종신보험",
            "정기": "정기보험",
            "연금": "연금보험",
            "저축": "저축보험",
            "CI": "CI보험",
            "간병": "간병보험",
            "암": "암보험",
            "건강": "건강보험",
            "변액": "변액보험",
            "어린이": "어린이보험",
            "실손": "실손보험"
        }

        for keyword, insurance_type in type_keywords.items():
            if keyword in product_name:
                return insurance_type

        return "기타"

    async def get_policy_metadata(self, product_id: str) -> PolicyMetadata:
        """
        약관 메타데이터 가져오기

        Args:
            product_id: 상품 정보 JSON 문자열 또는 download_url

        Returns:
            약관 메타데이터
        """
        # product_id가 JSON 문자열이면 파싱
        import json
        try:
            product_data = json.loads(product_id)
        except:
            # JSON이 아니면 URL로 간주
            product_data = {"download_url": product_id}

        return PolicyMetadata(
            insurer_code="metlife",
            insurer_name="메트라이프생명",
            product_name=product_data.get("product_name", "Unknown"),
            product_code=None,
            category=product_data.get("product_type"),
            download_url=product_data.get("download_url"),
            file_type="pdf",
            additional_info={
                "sales_period": product_data.get("sales_period"),
                "is_active": product_data.get("is_active")
            }
        )

    async def download_policy(self, metadata: PolicyMetadata, save_path: str) -> str:
        """
        약관 PDF 다운로드

        Args:
            metadata: 약관 메타데이터
            save_path: 저장 경로

        Returns:
            다운로드된 파일 경로 (성공 시) 또는 빈 문자열 (실패 시)
        """
        download_url = metadata.download_url
        if not download_url:
            self.logger.error("No download URL in metadata")
            return ""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url, headers=self.config.custom_headers) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to download {download_url}: HTTP {response.status}")
                        return ""

                    content = await response.read()

                    # PDF 파일인지 확인
                    if not content.startswith(b'%PDF'):
                        self.logger.error(f"Downloaded file is not a valid PDF: {download_url}")
                        return ""

                    with open(save_path, 'wb') as f:
                        f.write(content)

                    self.logger.info(f"Downloaded policy to {save_path}")
                    return save_path

        except Exception as e:
            self.logger.error(f"Error downloading policy from {download_url}: {e}")
            return ""

    async def validate_url(self, url: str) -> bool:
        """
        URL 유효성 검증

        Args:
            url: 검증할 URL

        Returns:
            유효 여부
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, headers=self.config.custom_headers) as response:
                    return response.status == 200
        except Exception:
            return False

    async def save_results_to_json(
        self,
        products: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> str:
        """
        크롤링 결과를 JSON 파일로 저장

        Args:
            products: 상품 목록
            output_path: 저장 경로 (선택사항)

        Returns:
            저장된 파일 경로
        """
        if output_path is None:
            # 기본 저장 경로: data/crawl_results/metlife_{timestamp}.json
            data_dir = Path("data/crawl_results")
            data_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = data_dir / f"metlife_{timestamp}.json"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # 메타데이터 포함한 결과 생성
        result_data = {
            "metadata": {
                "insurer_code": "metlife",
                "insurer_name": "메트라이프생명",
                "crawl_timestamp": datetime.now().isoformat(),
                "total_products": len(products),
                "active_products": sum(1 for p in products if p.get('is_active')),
                "discontinued_products": sum(1 for p in products if not p.get('is_active')),
                "crawler_version": "1.0.0",
                "comment": "판매상품목록, 판매중지상품 약관을 읽어야 함"
            },
            "products": products
        }

        # JSON 저장 (한글 유지, 들여쓰기)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Saved crawl results to: {output_path}")
        return str(output_path)

    async def load_results_from_json(self, json_path: str) -> Dict[str, Any]:
        """
        JSON 파일에서 크롤링 결과 로드

        Args:
            json_path: JSON 파일 경로

        Returns:
            크롤링 결과 데이터
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.logger.info(
                f"Loaded {data['metadata']['total_products']} products from {json_path}"
            )
            return data

        except Exception as e:
            self.logger.error(f"Failed to load JSON: {e}")
            raise


# Factory 함수
def create_metlife_crawler() -> MetLifeCrawler:
    """메트라이프 크롤러 생성"""
    return MetLifeCrawler()
