"""
Base Crawler

Abstract base class for insurance policy metadata crawlers.
Provides common functionality for HTTP requests, rate limiting, and error handling.

Epic: Epic 1, Story 1.0
Created: 2025-11-28
"""

import asyncio
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from app.services.crawler.insurer_configs import InsurerConfig


class CrawlerError(Exception):
    """Base exception for crawler errors"""
    pass


class RobotsTxtError(CrawlerError):
    """Raised when robots.txt disallows crawling"""
    pass


class BaseCrawler(ABC):
    """
    Base class for insurance policy metadata crawlers

    This crawler:
    - Respects robots.txt
    - Implements rate limiting
    - NEVER downloads PDF files
    - Only extracts metadata from HTML pages
    """

    def __init__(self, config: InsurerConfig):
        self.config = config
        self.session: Optional[httpx.AsyncClient] = None
        self.robot_parser: Optional[RobotFileParser] = None
        self.last_request_time: float = 0

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def initialize(self):
        """Initialize HTTP client and check robots.txt"""
        # Create HTTP client
        self.session = httpx.AsyncClient(
            headers={
                "User-Agent": self.config.user_agent,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            },
            timeout=30.0,
            follow_redirects=True,
        )

        # Check robots.txt
        if self.config.respect_robots_txt:
            await self._check_robots_txt()

        logger.info(
            f"Initialized crawler for {self.config.name} ({self.config.code})"
        )

    async def close(self):
        """Close HTTP client"""
        if self.session:
            await self.session.aclose()
            logger.info(f"Closed crawler for {self.config.name}")

    async def _check_robots_txt(self):
        """Check if crawling is allowed by robots.txt"""
        robots_url = urljoin(self.config.base_url, "/robots.txt")

        try:
            response = await self.session.get(robots_url)
            if response.status_code == 200:
                self.robot_parser = RobotFileParser()
                self.robot_parser.parse(response.text.splitlines())

                # Check if our user agent can access the policies page
                if not self.robot_parser.can_fetch(
                    self.config.user_agent, self.config.policies_url
                ):
                    raise RobotsTxtError(
                        f"robots.txt disallows crawling {self.config.policies_url}"
                    )

                logger.info(f"robots.txt check passed for {self.config.name}")
            else:
                # No robots.txt found - proceed with caution
                logger.warning(
                    f"robots.txt not found for {self.config.name} - proceeding anyway"
                )

        except httpx.HTTPError as e:
            logger.warning(f"Failed to fetch robots.txt: {e} - proceeding anyway")

    async def _rate_limit(self):
        """Implement rate limiting between requests"""
        if self.last_request_time > 0:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.config.request_delay:
                sleep_time = self.config.request_delay - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()

    async def fetch_page(self, url: str) -> str:
        """
        Fetch a single page with rate limiting

        Args:
            url: Page URL to fetch

        Returns:
            HTML content

        Raises:
            CrawlerError: If request fails
        """
        await self._rate_limit()

        try:
            logger.debug(f"Fetching {url}")
            response = await self.session.get(url)
            response.raise_for_status()

            logger.info(
                f"Fetched {url} - status: {response.status_code}, "
                f"size: {len(response.content)} bytes"
            )

            return response.text

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise CrawlerError(f"Failed to fetch {url}: {e}")

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML with BeautifulSoup"""
        return BeautifulSoup(html, "html.parser")

    @abstractmethod
    async def crawl(self) -> List[Dict[str, Any]]:
        """
        Main crawl method - to be implemented by subclasses

        Returns:
            List of policy metadata dictionaries
        """
        pass

    def _extract_text(self, element, selector: str) -> Optional[str]:
        """Extract text from element using CSS selector"""
        if not element:
            return None

        try:
            found = element.select_one(selector)
            if found:
                return found.get_text(strip=True)
            return None
        except Exception as e:
            logger.warning(f"Error extracting text with selector '{selector}': {e}")
            return None

    def _extract_link(self, element, selector: str) -> Optional[str]:
        """Extract href from element using CSS selector"""
        if not element:
            return None

        try:
            found = element.select_one(selector)
            if found:
                href = found.get("href")
                if href:
                    # Convert relative URL to absolute
                    return urljoin(self.config.base_url, href)
            return None
        except Exception as e:
            logger.warning(f"Error extracting link with selector '{selector}': {e}")
            return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None

        # Try common Korean date formats
        formats = [
            "%Y.%m.%d",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y년 %m월 %d일",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        logger.warning(f"Failed to parse date: {date_str}")
        return None
