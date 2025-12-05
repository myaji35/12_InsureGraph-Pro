"""
Crawler Registry

보험사 크롤러 등록 및 관리
"""
from typing import Dict, Type, List
from loguru import logger

from app.services.crawlers.base_crawler import BaseInsurerCrawler


class CrawlerRegistry:
    """크롤러 레지스트리 (싱글톤)"""

    _instance = None
    _crawlers: Dict[str, Type[BaseInsurerCrawler]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, insurer_code: str, crawler_class: Type[BaseInsurerCrawler]):
        """
        크롤러 등록

        Args:
            insurer_code: 보험사 코드 (e.g., "samsung_life")
            crawler_class: 크롤러 클래스
        """
        if insurer_code in self._crawlers:
            logger.warning(f"Overwriting existing crawler for: {insurer_code}")

        self._crawlers[insurer_code] = crawler_class
        logger.info(f"Registered crawler: {insurer_code}")

    def get(self, insurer_code: str) -> Type[BaseInsurerCrawler]:
        """
        크롤러 클래스 조회

        Args:
            insurer_code: 보험사 코드

        Returns:
            크롤러 클래스

        Raises:
            KeyError: 등록되지 않은 보험사
        """
        if insurer_code not in self._crawlers:
            raise KeyError(f"No crawler registered for: {insurer_code}")

        return self._crawlers[insurer_code]

    def get_all(self) -> Dict[str, Type[BaseInsurerCrawler]]:
        """
        모든 등록된 크롤러 조회

        Returns:
            크롤러 딕셔너리 {insurer_code: crawler_class}
        """
        return self._crawlers.copy()

    def list_insurers(self) -> List[str]:
        """
        등록된 보험사 코드 목록

        Returns:
            보험사 코드 리스트
        """
        return list(self._crawlers.keys())

    def is_registered(self, insurer_code: str) -> bool:
        """
        보험사 크롤러 등록 여부 확인

        Args:
            insurer_code: 보험사 코드

        Returns:
            등록되어 있으면 True
        """
        return insurer_code in self._crawlers

    def unregister(self, insurer_code: str):
        """
        크롤러 등록 해제

        Args:
            insurer_code: 보험사 코드
        """
        if insurer_code in self._crawlers:
            del self._crawlers[insurer_code]
            logger.info(f"Unregistered crawler: {insurer_code}")
        else:
            logger.warning(f"Crawler not found for unregister: {insurer_code}")


# 싱글톤 인스턴스
_registry = CrawlerRegistry()


def register_crawler(insurer_code: str, crawler_class: Type[BaseInsurerCrawler]):
    """
    크롤러 등록 (편의 함수)

    Args:
        insurer_code: 보험사 코드
        crawler_class: 크롤러 클래스
    """
    _registry.register(insurer_code, crawler_class)


def get_registered_insurers() -> List[str]:
    """
    등록된 보험사 목록 조회 (편의 함수)

    Returns:
        보험사 코드 리스트
    """
    return _registry.list_insurers()


def is_crawler_registered(insurer_code: str) -> bool:
    """
    크롤러 등록 여부 확인 (편의 함수)

    Args:
        insurer_code: 보험사 코드

    Returns:
        등록되어 있으면 True
    """
    return _registry.is_registered(insurer_code)


# 기본 크롤러 자동 등록
def _auto_register_crawlers():
    """기본 제공 크롤러들을 자동으로 등록"""
    try:
        from app.services.crawlers.samsung_life_crawler import SamsungLifeCrawler
        from app.services.crawlers.kb_insurance_crawler import KBInsuranceCrawler
        from app.services.crawlers.samsung_fire_crawler import SamsungFireCrawler
        from app.services.crawlers.metlife_crawler import MetLifeCrawler

        register_crawler("samsung_life", SamsungLifeCrawler)
        register_crawler("kb_insurance", KBInsuranceCrawler)
        register_crawler("samsung_fire", SamsungFireCrawler)
        register_crawler("metlife", MetLifeCrawler)

        logger.info(f"Auto-registered {len(_registry.list_insurers())} crawlers")

    except Exception as e:
        logger.error(f"Failed to auto-register crawlers: {e}")


# 모듈 로드 시 자동 등록
_auto_register_crawlers()
