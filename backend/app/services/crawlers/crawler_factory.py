"""
Crawler Factory

보험사 크롤러 인스턴스 생성 팩토리
"""
from typing import Optional
from loguru import logger

from app.services.crawlers.base_crawler import BaseInsurerCrawler
from app.services.crawlers.crawler_registry import CrawlerRegistry


class CrawlerFactory:
    """크롤러 팩토리"""

    def __init__(self):
        self.registry = CrawlerRegistry()

    def create_crawler(self, insurer_code: str) -> BaseInsurerCrawler:
        """
        보험사 크롤러 인스턴스 생성

        Args:
            insurer_code: 보험사 코드 (e.g., "samsung_life", "kb_insurance")

        Returns:
            크롤러 인스턴스

        Raises:
            KeyError: 등록되지 않은 보험사
        """
        logger.info(f"Creating crawler for: {insurer_code}")

        try:
            crawler_class = self.registry.get(insurer_code)
            crawler_instance = crawler_class()

            logger.info(f"Crawler created successfully: {insurer_code}")
            return crawler_instance

        except KeyError:
            available = self.registry.list_insurers()
            raise KeyError(
                f"No crawler registered for '{insurer_code}'. "
                f"Available insurers: {', '.join(available)}"
            )

    def create_all_crawlers(self) -> dict[str, BaseInsurerCrawler]:
        """
        모든 등록된 크롤러 인스턴스 생성

        Returns:
            {insurer_code: crawler_instance} 딕셔너리
        """
        logger.info("Creating all registered crawlers")

        crawlers = {}
        for insurer_code in self.registry.list_insurers():
            try:
                crawlers[insurer_code] = self.create_crawler(insurer_code)
            except Exception as e:
                logger.error(f"Failed to create crawler for {insurer_code}: {e}")

        logger.info(f"Created {len(crawlers)} crawlers")
        return crawlers

    def get_available_insurers(self) -> list[str]:
        """
        사용 가능한 보험사 목록

        Returns:
            보험사 코드 리스트
        """
        return self.registry.list_insurers()

    def is_supported(self, insurer_code: str) -> bool:
        """
        지원되는 보험사인지 확인

        Args:
            insurer_code: 보험사 코드

        Returns:
            지원되면 True
        """
        return self.registry.is_registered(insurer_code)


# 싱글톤 팩토리 인스턴스
_factory = CrawlerFactory()


def get_crawler(insurer_code: str) -> BaseInsurerCrawler:
    """
    크롤러 인스턴스 조회 (편의 함수)

    Args:
        insurer_code: 보험사 코드

    Returns:
        크롤러 인스턴스
    """
    return _factory.create_crawler(insurer_code)


def get_all_crawlers() -> dict[str, BaseInsurerCrawler]:
    """
    모든 크롤러 인스턴스 조회 (편의 함수)

    Returns:
        {insurer_code: crawler_instance} 딕셔너리
    """
    return _factory.create_all_crawlers()


def get_available_insurers() -> list[str]:
    """
    사용 가능한 보험사 목록 (편의 함수)

    Returns:
        보험사 코드 리스트
    """
    return _factory.get_available_insurers()


def is_insurer_supported(insurer_code: str) -> bool:
    """
    보험사 지원 여부 확인 (편의 함수)

    Args:
        insurer_code: 보험사 코드

    Returns:
        지원되면 True
    """
    return _factory.is_supported(insurer_code)
