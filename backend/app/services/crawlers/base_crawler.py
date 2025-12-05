"""
Base Insurer Crawler

보험사별 크롤러의 추상 베이스 클래스
각 보험사 크롤러는 이 클래스를 상속받아 구현
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger


class CrawlMethod(str, Enum):
    """크롤링 방법"""
    STATIC_HTML = "static_html"  # requests + BeautifulSoup
    DYNAMIC_JS = "dynamic_js"  # Playwright/Selenium
    API = "api"  # REST API 직접 호출
    HYBRID = "hybrid"  # 복합 방식


class AuthMethod(str, Enum):
    """인증 방법"""
    NONE = "none"
    BASIC = "basic"
    OAUTH = "oauth"
    SESSION = "session"
    API_KEY = "api_key"


@dataclass
class InsurerConfig:
    """보험사 설정"""
    insurer_code: str  # e.g., "samsung_life", "kb_insurance"
    insurer_name: str  # e.g., "삼성생명", "KB손해보험"
    base_url: str
    product_list_url: Optional[str] = None
    crawl_method: CrawlMethod = CrawlMethod.STATIC_HTML
    auth_method: AuthMethod = AuthMethod.NONE

    # Selectors (CSS or XPath)
    product_list_selector: Optional[str] = None
    product_name_selector: Optional[str] = None
    product_category_selector: Optional[str] = None
    download_link_selector: Optional[str] = None

    # Pagination
    has_pagination: bool = False
    pagination_selector: Optional[str] = None
    max_pages: int = 100

    # Rate limiting
    request_delay: float = 1.0  # seconds between requests
    max_retries: int = 3

    # Custom headers
    custom_headers: Optional[Dict[str, str]] = None

    # JavaScript required
    wait_for_selector: Optional[str] = None
    wait_timeout: int = 30000  # ms

    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PolicyMetadata:
    """크롤링한 보험 약관 메타데이터"""
    insurer_code: str
    insurer_name: str
    product_name: str
    product_code: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    download_url: Optional[str] = None
    effective_date: Optional[str] = None
    version: Optional[str] = None
    file_type: str = "pdf"
    file_size: Optional[int] = None
    additional_info: Optional[Dict[str, Any]] = None


class BaseInsurerCrawler(ABC):
    """
    보험사별 크롤러 추상 베이스 클래스

    각 보험사는 이 클래스를 상속받아 구체적인 크롤링 로직을 구현합니다.
    """

    def __init__(self, config: InsurerConfig):
        """
        Args:
            config: 보험사별 설정
        """
        self.config = config
        self.logger = logger.bind(insurer=config.insurer_code)

    @abstractmethod
    async def get_product_list(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        보험 상품 목록 조회

        Args:
            category: 상품 카테고리 (예: "암보험", "실손보험")

        Returns:
            상품 목록 (각 상품은 dict)
        """
        pass

    @abstractmethod
    async def get_policy_metadata(self, product_id: str) -> PolicyMetadata:
        """
        특정 상품의 약관 메타데이터 조회

        Args:
            product_id: 상품 ID 또는 코드

        Returns:
            약관 메타데이터
        """
        pass

    @abstractmethod
    async def download_policy(self, metadata: PolicyMetadata, save_path: str) -> str:
        """
        약관 파일 다운로드

        Args:
            metadata: 약관 메타데이터
            save_path: 저장 경로

        Returns:
            다운로드된 파일 경로
        """
        pass

    async def crawl_all_policies(
        self,
        categories: Optional[List[str]] = None,
        save_dir: Optional[str] = None
    ) -> List[PolicyMetadata]:
        """
        모든 약관 크롤링 (기본 구현)

        Args:
            categories: 크롤링할 카테고리 목록 (None이면 전체)
            save_dir: 파일 저장 디렉토리

        Returns:
            크롤링된 약관 메타데이터 목록
        """
        self.logger.info(f"Starting crawl for {self.config.insurer_name}")

        all_metadata = []
        categories = categories or [None]  # None means all categories

        for category in categories:
            try:
                self.logger.info(f"Crawling category: {category or 'ALL'}")

                # Get product list
                products = await self.get_product_list(category)
                self.logger.info(f"Found {len(products)} products")

                # Get metadata for each product
                for product in products:
                    try:
                        product_id = product.get("id") or product.get("code")
                        metadata = await self.get_policy_metadata(product_id)
                        all_metadata.append(metadata)

                        # Optionally download
                        if save_dir:
                            await self.download_policy(metadata, save_dir)

                    except Exception as e:
                        self.logger.error(f"Failed to process product {product_id}: {e}")
                        continue

            except Exception as e:
                self.logger.error(f"Failed to crawl category {category}: {e}")
                continue

        self.logger.info(f"Crawl complete. Total policies: {len(all_metadata)}")
        return all_metadata

    def validate_metadata(self, metadata: PolicyMetadata) -> bool:
        """
        메타데이터 유효성 검증

        Args:
            metadata: 검증할 메타데이터

        Returns:
            유효하면 True
        """
        required_fields = ["insurer_code", "insurer_name", "product_name"]

        for field in required_fields:
            if not getattr(metadata, field):
                self.logger.warning(f"Missing required field: {field}")
                return False

        return True

    async def test_connection(self) -> bool:
        """
        보험사 웹사이트 연결 테스트

        Returns:
            연결 성공 시 True
        """
        try:
            self.logger.info(f"Testing connection to {self.config.base_url}")
            # 기본 구현: 단순히 base_url에 요청
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(self.config.base_url, timeout=10)
                success = response.status_code == 200

            if success:
                self.logger.info("Connection test passed")
            else:
                self.logger.warning(f"Connection test failed: {response.status_code}")

            return success

        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
