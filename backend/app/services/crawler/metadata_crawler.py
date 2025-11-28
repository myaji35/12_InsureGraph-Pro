"""
Metadata Crawler

Main crawler implementation that discovers insurance policy metadata
from insurer disclosure pages. Stores results in the database.

Epic: Epic 1, Story 1.0
Created: 2025-11-28
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from loguru import logger

from app.services.crawler.base_crawler import BaseCrawler
from app.services.crawler.insurer_configs import InsurerConfig
from app.models.policy_metadata import (
    PolicyMetadata,
    PolicyMetadataCreate,
    PolicyCategory,
    PolicyMetadataStatus,
)


class MetadataCrawler(BaseCrawler):
    """
    Crawler for insurance policy metadata

    This crawler:
    1. Fetches HTML from insurer disclosure pages
    2. Parses tables/lists for policy information
    3. Extracts metadata (name, date, download link)
    4. NEVER downloads actual PDF files
    5. Returns metadata for storage in database
    """

    async def crawl(self) -> List[Dict[str, Any]]:
        """
        Crawl insurer's disclosure page and extract policy metadata

        Returns:
            List of policy metadata dictionaries
        """
        logger.info(f"Starting crawl for {self.config.name}")

        all_policies = []
        page_num = 1

        # Fetch first page
        current_url = self.config.policies_url

        while True:
            try:
                # Fetch page HTML
                html = await self.fetch_page(current_url)
                soup = self.parse_html(html)

                # Extract policies from current page
                policies = self._extract_policies_from_page(soup)
                all_policies.extend(policies)

                logger.info(
                    f"Extracted {len(policies)} policies from page {page_num}"
                )

                # Check for pagination
                if not self.config.has_pagination or page_num >= self.config.max_pages:
                    break

                # Find next page link
                next_url = self._find_next_page(soup)
                if not next_url:
                    break

                current_url = next_url
                page_num += 1

            except Exception as e:
                logger.error(f"Error crawling page {page_num}: {e}")
                break

        logger.info(
            f"Crawl complete for {self.config.name}: "
            f"found {len(all_policies)} policies"
        )

        return all_policies

    def _extract_policies_from_page(self, soup) -> List[Dict[str, Any]]:
        """Extract policy metadata from a single page"""
        policies = []

        # Find the table/container
        table = soup.select_one(self.config.table_selector)
        if not table:
            logger.warning(
                f"Table not found with selector: {self.config.table_selector}"
            )
            return policies

        # Find all rows
        rows = table.select(self.config.row_selector)
        logger.debug(f"Found {len(rows)} rows in table")

        for row in rows:
            try:
                policy = self._extract_policy_from_row(row)
                if policy:
                    policies.append(policy)
            except Exception as e:
                logger.warning(f"Error extracting policy from row: {e}")
                continue

        return policies

    def _extract_policy_from_row(self, row) -> Optional[Dict[str, Any]]:
        """Extract policy metadata from a single row"""

        # Extract policy name
        policy_name = self._extract_text(row, self.config.policy_name_selector)
        if not policy_name:
            # Skip rows without policy name (e.g., header rows)
            return None

        # Extract download link (REQUIRED)
        download_url = self._extract_link(row, self.config.download_link_selector)
        if not download_url:
            logger.warning(f"No download link found for: {policy_name}")
            return None

        # Validate that it's not a PDF direct link (we only want metadata links)
        if download_url.lower().endswith('.pdf'):
            # This is a direct PDF link - extract it but don't download
            logger.debug(f"Direct PDF link found: {download_url}")

        # Extract optional fields
        file_name = None
        if self.config.file_name_selector:
            file_name = self._extract_text(row, self.config.file_name_selector)

        # If no file_name, try to extract from download URL
        if not file_name and download_url:
            file_name = download_url.split('/')[-1]

        publication_date = None
        if self.config.publication_date_selector:
            date_str = self._extract_text(row, self.config.publication_date_selector)
            publication_date = self._parse_date(date_str)

        category = None
        if self.config.category_selector:
            category_str = self._extract_text(row, self.config.category_selector)
            category = self._infer_category(category_str or policy_name)

        # If category not extracted, try to infer from policy name
        if not category:
            category = self._infer_category(policy_name)

        return {
            "insurer": self.config.name,
            "policy_name": policy_name,
            "file_name": file_name,
            "download_url": download_url,
            "publication_date": publication_date,
            "category": category,
        }

    def _find_next_page(self, soup) -> Optional[str]:
        """Find URL of next page (pagination)"""
        if not self.config.next_page_selector:
            return None

        next_link = soup.select_one(self.config.next_page_selector)
        if not next_link:
            return None

        href = next_link.get("href")
        if not href:
            return None

        # Convert to absolute URL
        from urllib.parse import urljoin
        return urljoin(self.config.base_url, href)

    def _infer_category(self, text: str) -> Optional[str]:
        """
        Infer policy category from text (policy name or category field)

        This is a simple keyword-based approach. Can be improved with ML.
        """
        if not text:
            return None

        text_lower = text.lower()

        # Category keywords (Korean)
        category_keywords = {
            PolicyCategory.CANCER: ["암", "cancer", "종양"],
            PolicyCategory.CARDIOVASCULAR: ["심혈관", "뇌혈관", "심장", "뇌졸중"],
            PolicyCategory.LIFE: ["종신", "정기", "생명"],
            PolicyCategory.ANNUITY: ["연금", "펜션"],
            PolicyCategory.DISABILITY: ["장애", "간병"],
            PolicyCategory.HEALTH: ["건강", "의료", "실손"],
            PolicyCategory.ACCIDENT: ["상해", "사고"],
            PolicyCategory.DENTAL: ["치아", "치과"],
            PolicyCategory.LONG_TERM_CARE: ["간병", "요양"],
            PolicyCategory.SAVINGS: ["저축", "적금"],
        }

        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category.value

        return None


# ============================================
# Crawler Manager
# ============================================

class CrawlerManager:
    """
    Manager for running multiple crawlers

    Coordinates crawling across multiple insurers and
    stores results in the database.
    """

    def __init__(self):
        self.results: Dict[str, List[Dict[str, Any]]] = {}

    async def crawl_insurer(
        self,
        config: InsurerConfig,
        save_to_db: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Crawl a single insurer

        Args:
            config: Insurer configuration
            save_to_db: Whether to save results to database

        Returns:
            List of discovered policies
        """
        logger.info(f"Crawling {config.name}...")

        async with MetadataCrawler(config) as crawler:
            policies = await crawler.crawl()

        if save_to_db:
            saved_count = await self._save_to_database(config.code, policies)
            logger.info(f"Saved {saved_count}/{len(policies)} new policies")

        self.results[config.code] = policies
        return policies

    async def crawl_all(
        self,
        insurer_configs: List[InsurerConfig],
        save_to_db: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Crawl multiple insurers

        Args:
            insurer_configs: List of insurer configurations
            save_to_db: Whether to save results to database

        Returns:
            Dictionary mapping insurer code to list of policies
        """
        logger.info(f"Starting crawl for {len(insurer_configs)} insurers")

        for config in insurer_configs:
            try:
                await self.crawl_insurer(config, save_to_db=save_to_db)
            except Exception as e:
                logger.error(f"Failed to crawl {config.name}: {e}")
                continue

        total_policies = sum(len(policies) for policies in self.results.values())
        logger.info(
            f"Crawl complete: {len(self.results)} insurers, "
            f"{total_policies} total policies"
        )

        return self.results

    async def _save_to_database(
        self,
        insurer_code: str,
        policies: List[Dict[str, Any]]
    ) -> int:
        """
        Save discovered policies to database

        Args:
            insurer_code: Insurer code
            policies: List of policy metadata

        Returns:
            Number of new policies saved
        """
        # TODO: Replace with actual database implementation
        # For now, this is a placeholder that would:
        # 1. Check if policy already exists (by download_url or policy_name)
        # 2. If new, create PolicyMetadata record with status=DISCOVERED
        # 3. If exists, optionally update metadata

        from app.api.v1.endpoints.metadata import _policy_metadata_store

        saved_count = 0

        for policy_data in policies:
            # Check if already exists (simple check by download_url)
            exists = any(
                p.download_url == policy_data["download_url"]
                for p in _policy_metadata_store.values()
            )

            if not exists:
                # Create new policy metadata
                policy = PolicyMetadata(
                    insurer=policy_data["insurer"],
                    policy_name=policy_data["policy_name"],
                    file_name=policy_data.get("file_name"),
                    download_url=policy_data["download_url"],
                    publication_date=policy_data.get("publication_date"),
                    category=policy_data.get("category"),
                    status=PolicyMetadataStatus.DISCOVERED,
                )

                _policy_metadata_store[policy.id] = policy
                saved_count += 1

                logger.debug(f"Saved new policy: {policy.policy_name}")

        return saved_count
