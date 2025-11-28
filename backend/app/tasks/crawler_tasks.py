"""
Crawler Celery Tasks

Scheduled and on-demand tasks for policy metadata crawling.

Epic: Epic 1, Story 1.0
Created: 2025-11-28
"""

from typing import List, Dict, Any
from loguru import logger

from app.celery_app import celery_app
from app.services.crawler.insurer_configs import INSURER_CONFIGS, get_insurer_config
from app.services.crawler.metadata_crawler import CrawlerManager


@celery_app.task(
    name="crawler.crawl_all_insurers",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def crawl_all_insurers_task(self) -> Dict[str, Any]:
    """
    Scheduled task to crawl all configured insurers

    This task runs periodically (e.g., daily) to discover new policies.

    Returns:
        Summary of crawl results
    """
    logger.info("Starting scheduled crawl for all insurers")

    try:
        import asyncio

        # Get all insurer configs
        configs = list(INSURER_CONFIGS.values())

        # Filter out test insurer in production
        configs = [c for c in configs if c.code != "test_insurer"]

        # Run crawler manager
        manager = CrawlerManager()
        results = asyncio.run(manager.crawl_all(configs, save_to_db=True))

        # Generate summary
        summary = {
            "status": "success",
            "insurers_crawled": len(results),
            "total_policies_found": sum(len(policies) for policies in results.values()),
            "results_by_insurer": {
                code: len(policies)
                for code, policies in results.items()
            },
        }

        logger.info(f"Crawl complete: {summary}")
        return summary

    except Exception as e:
        logger.error(f"Crawl task failed: {e}")

        # Retry on failure
        raise self.retry(exc=e)


@celery_app.task(
    name="crawler.crawl_single_insurer",
    bind=True,
    max_retries=3,
)
def crawl_single_insurer_task(self, insurer_code: str) -> Dict[str, Any]:
    """
    Task to crawl a single insurer on-demand

    Args:
        insurer_code: Insurer code to crawl

    Returns:
        Crawl results
    """
    logger.info(f"Starting on-demand crawl for {insurer_code}")

    try:
        import asyncio

        # Get insurer config
        config = get_insurer_config(insurer_code)
        if not config:
            raise ValueError(f"Unknown insurer code: {insurer_code}")

        # Run crawler
        manager = CrawlerManager()
        policies = asyncio.run(manager.crawl_insurer(config, save_to_db=True))

        summary = {
            "status": "success",
            "insurer": config.name,
            "insurer_code": insurer_code,
            "policies_found": len(policies),
        }

        logger.info(f"Crawl complete for {insurer_code}: {summary}")
        return summary

    except Exception as e:
        logger.error(f"Crawl task failed for {insurer_code}: {e}")
        raise self.retry(exc=e)
