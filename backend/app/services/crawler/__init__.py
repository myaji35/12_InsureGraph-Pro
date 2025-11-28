"""
Metadata Crawler Service

Lightweight web crawler for discovering insurance policy metadata
from insurer public disclosure pages. This crawler NEVER downloads
PDF files directly - it only collects metadata (links, names, dates).

Epic: Epic 1, Story 1.0
Created: 2025-11-28
"""

from .base_crawler import BaseCrawler
from .insurer_configs import InsurerConfig, INSURER_CONFIGS
from .metadata_crawler import MetadataCrawler

__all__ = [
    "BaseCrawler",
    "InsurerConfig",
    "INSURER_CONFIGS",
    "MetadataCrawler",
]
