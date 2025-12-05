"""
Insurance Company Crawlers

보험사별 약관 크롤링 전략을 제공하는 모듈
각 보험사마다 다른 웹사이트 구조와 수집 방법을 유연하게 대응
"""
from app.services.crawlers.base_crawler import BaseInsurerCrawler
from app.services.crawlers.crawler_factory import CrawlerFactory, get_crawler
from app.services.crawlers.crawler_registry import register_crawler, get_registered_insurers

__all__ = [
    "BaseInsurerCrawler",
    "CrawlerFactory",
    "get_crawler",
    "register_crawler",
    "get_registered_insurers",
]
