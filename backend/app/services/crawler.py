"""
Insurance Policy Document Crawler Service

보험사 웹사이트에서 약관 PDF 문서를 자동으로 수집하는 크롤러 서비스
"""
import asyncio
import re
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import hashlib

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

from app.core.config import settings


class CrawlerConfig:
    """크롤러 설정"""

    # Rate limiting
    REQUEST_DELAY = 2.0  # seconds between requests
    MAX_CONCURRENT_REQUESTS = 3

    # Timeouts
    REQUEST_TIMEOUT = 30  # seconds

    # User agent
    USER_AGENT = "InsureGraphBot/1.0 (Insurance Policy Document Collector; +https://insuregraph.pro/bot)"

    # File filtering
    ALLOWED_EXTENSIONS = ['.pdf']
    MIN_FILE_SIZE = 1024  # 1KB
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class InsuranceCompanyCrawler:
    """보험사 웹사이트 크롤러"""

    def __init__(self, company_config: Dict):
        """
        Initialize crawler for specific insurance company

        Args:
            company_config: 보험사별 크롤링 설정
                {
                    "company_name": "삼성화재",
                    "base_url": "https://www.samsungfire.com",
                    "policy_page_urls": ["https://..."],
                    "selectors": {
                        "product_links": "a.product-link",
                        "pdf_links": "a[href$='.pdf']",
                        "product_name": "h2.product-name"
                    },
                    "respect_robots_txt": True
                }
        """
        self.company_name = company_config["company_name"]
        self.base_url = company_config["base_url"]
        self.policy_page_urls = company_config.get("policy_page_urls", [])
        self.selectors = company_config.get("selectors", {})
        self.respect_robots_txt = company_config.get("respect_robots_txt", True)

        self.session: Optional[aiohttp.ClientSession] = None
        self.robots_parser: Optional[RobotFileParser] = None
        self.visited_urls: Set[str] = set()
        self.found_documents: List[Dict] = []

    async def initialize(self):
        """크롤러 초기화"""
        # Create HTTP session
        timeout = aiohttp.ClientTimeout(total=CrawlerConfig.REQUEST_TIMEOUT)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={'User-Agent': CrawlerConfig.USER_AGENT}
        )

        # Load robots.txt
        if self.respect_robots_txt:
            await self._load_robots_txt()

    async def close(self):
        """리소스 정리"""
        if self.session:
            await self.session.close()

    async def _load_robots_txt(self):
        """robots.txt 로드"""
        try:
            robots_url = urljoin(self.base_url, '/robots.txt')
            self.robots_parser = RobotFileParser()
            self.robots_parser.set_url(robots_url)

            # Fetch robots.txt content
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    content = await response.text()
                    # Parse robots.txt
                    self.robots_parser.parse(content.splitlines())
                    logger.info(f"Loaded robots.txt for {self.company_name}")
                else:
                    logger.warning(f"robots.txt not found for {self.company_name}")
        except Exception as e:
            logger.warning(f"Failed to load robots.txt: {e}")

    def _can_fetch(self, url: str) -> bool:
        """URL 크롤링 가능 여부 확인"""
        if not self.respect_robots_txt or not self.robots_parser:
            return True

        return self.robots_parser.can_fetch(CrawlerConfig.USER_AGENT, url)

    async def _fetch_page(self, url: str) -> Optional[str]:
        """
        페이지 HTML 가져오기

        Args:
            url: 페이지 URL

        Returns:
            Optional[str]: HTML 콘텐츠 또는 None
        """
        if url in self.visited_urls:
            logger.debug(f"Already visited: {url}")
            return None

        if not self._can_fetch(url):
            logger.warning(f"Blocked by robots.txt: {url}")
            return None

        try:
            # Rate limiting
            await asyncio.sleep(CrawlerConfig.REQUEST_DELAY)

            async with self.session.get(url) as response:
                if response.status == 200:
                    self.visited_urls.add(url)
                    return await response.text()
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def _extract_product_info(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        페이지에서 상품 정보 추출

        Args:
            soup: BeautifulSoup 객체
            url: 페이지 URL

        Returns:
            Dict: 상품 정보
        """
        product_info = {
            "product_name": "",
            "product_code": "",
            "description": ""
        }

        # Extract product name
        if "product_name" in self.selectors:
            name_elem = soup.select_one(self.selectors["product_name"])
            if name_elem:
                product_info["product_name"] = name_elem.get_text(strip=True)

        # Extract product code (if available)
        if "product_code" in self.selectors:
            code_elem = soup.select_one(self.selectors["product_code"])
            if code_elem:
                product_info["product_code"] = code_elem.get_text(strip=True)

        # Extract description
        if "description" in self.selectors:
            desc_elem = soup.select_one(self.selectors["description"])
            if desc_elem:
                product_info["description"] = desc_elem.get_text(strip=True)

        return product_info

    def _is_valid_pdf_url(self, url: str) -> bool:
        """PDF URL 유효성 검사"""
        # Check extension
        parsed = urlparse(url)
        path = parsed.path.lower()

        if not any(path.endswith(ext) for ext in CrawlerConfig.ALLOWED_EXTENSIONS):
            return False

        # Check if it's a policy document (한국어 키워드 체크)
        policy_keywords = ['약관', '보험약관', 'terms', 'policy', '계약']
        url_lower = url.lower()

        return any(keyword in url_lower for keyword in policy_keywords)

    async def _find_pdf_links(self, html: str, base_url: str) -> List[Dict]:
        """
        HTML에서 PDF 링크 찾기

        Args:
            html: HTML 콘텐츠
            base_url: 기준 URL

        Returns:
            List[Dict]: PDF 문서 정보 목록
        """
        soup = BeautifulSoup(html, 'html.parser')
        documents = []

        # Method 1: Use selector if provided
        if "pdf_links" in self.selectors:
            pdf_links = soup.select(self.selectors["pdf_links"])
        else:
            # Method 2: Find all <a> tags with PDF href
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))

        for link in pdf_links:
            href = link.get('href')
            if not href:
                continue

            # Convert to absolute URL
            absolute_url = urljoin(base_url, href)

            # Validate
            if not self._is_valid_pdf_url(absolute_url):
                continue

            # Extract product info from surrounding context
            product_info = self._extract_product_info(soup, base_url)

            # Try to extract product name from link text
            link_text = link.get_text(strip=True)
            if not product_info["product_name"] and link_text:
                product_info["product_name"] = link_text

            # Generate unique ID for this document
            doc_id = hashlib.md5(absolute_url.encode()).hexdigest()

            documents.append({
                "doc_id": doc_id,
                "url": absolute_url,
                "product_name": product_info.get("product_name", ""),
                "product_code": product_info.get("product_code", ""),
                "description": product_info.get("description", ""),
                "source_page": base_url,
                "insurer": self.company_name,
                "discovered_at": datetime.now().isoformat()
            })

        return documents

    async def crawl(self) -> List[Dict]:
        """
        보험사 웹사이트 크롤링 실행

        Returns:
            List[Dict]: 발견된 PDF 문서 목록
        """
        logger.info(f"Starting crawl for {self.company_name}")

        try:
            await self.initialize()

            # Crawl each policy page
            for page_url in self.policy_page_urls:
                logger.info(f"Crawling: {page_url}")

                # Fetch page
                html = await self._fetch_page(page_url)
                if not html:
                    continue

                # Find PDF links
                documents = await self._find_pdf_links(html, page_url)
                self.found_documents.extend(documents)

                logger.info(f"Found {len(documents)} documents on {page_url}")

            logger.info(f"Crawl completed for {self.company_name}. Total documents: {len(self.found_documents)}")
            return self.found_documents

        finally:
            await self.close()


class CrawlerManager:
    """크롤러 매니저 - 여러 보험사 크롤링 관리"""

    def __init__(self):
        self.company_configs = self._load_company_configs()

    def _load_company_configs(self) -> List[Dict]:
        """
        보험사별 크롤링 설정 로드

        Returns:
            List[Dict]: 보험사 설정 목록
        """
        # TODO: 실제로는 데이터베이스나 설정 파일에서 로드
        # 현재는 하드코딩된 예시 설정
        return [
            {
                "company_name": "삼성화재",
                "base_url": "https://www.samsungfire.com",
                "policy_page_urls": [
                    "https://www.samsungfire.com/personal/product/list.html"
                ],
                "selectors": {
                    "product_links": "a.product-link",
                    "pdf_links": "a[href*='약관']",
                    "product_name": "h3.product-title"
                },
                "respect_robots_txt": True,
                "enabled": False  # 실제 크롤링 전 테스트 필요
            },
            {
                "company_name": "한화생명",
                "base_url": "https://www.hanwhalife.com",
                "policy_page_urls": [
                    "https://www.hanwhalife.com/product/list.do"
                ],
                "selectors": {
                    "pdf_links": "a.btn-terms",
                    "product_name": "div.product-name"
                },
                "respect_robots_txt": True,
                "enabled": False
            },
            # 추가 보험사 설정...
        ]

    async def crawl_company(self, company_name: str) -> List[Dict]:
        """
        특정 보험사 크롤링

        Args:
            company_name: 보험사명

        Returns:
            List[Dict]: 발견된 문서 목록
        """
        # Find company config
        config = next(
            (c for c in self.company_configs if c["company_name"] == company_name),
            None
        )

        if not config:
            raise ValueError(f"Unknown company: {company_name}")

        if not config.get("enabled", False):
            logger.warning(f"Crawler disabled for {company_name}")
            return []

        # Create and run crawler
        crawler = InsuranceCompanyCrawler(config)
        return await crawler.crawl()

    async def crawl_all(self) -> Dict[str, List[Dict]]:
        """
        모든 활성화된 보험사 크롤링

        Returns:
            Dict[str, List[Dict]]: 보험사별 문서 목록
        """
        results = {}

        enabled_companies = [c for c in self.company_configs if c.get("enabled", False)]

        for config in enabled_companies:
            company_name = config["company_name"]
            try:
                documents = await self.crawl_company(company_name)
                results[company_name] = documents
            except Exception as e:
                logger.error(f"Failed to crawl {company_name}: {e}")
                results[company_name] = []

        return results


async def download_pdf(url: str, save_path: str) -> bool:
    """
    PDF 파일 다운로드

    Args:
        url: PDF URL
        save_path: 저장 경로

    Returns:
        bool: 성공 여부
    """
    try:
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()

                    # Check file size
                    if len(content) < CrawlerConfig.MIN_FILE_SIZE:
                        logger.warning(f"File too small: {len(content)} bytes")
                        return False

                    if len(content) > CrawlerConfig.MAX_FILE_SIZE:
                        logger.warning(f"File too large: {len(content)} bytes")
                        return False

                    # Save file
                    with open(save_path, 'wb') as f:
                        f.write(content)

                    logger.info(f"Downloaded: {save_path} ({len(content)} bytes)")
                    return True
                else:
                    logger.error(f"HTTP {response.status} for {url}")
                    return False
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False
