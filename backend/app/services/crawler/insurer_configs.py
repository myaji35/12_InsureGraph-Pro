"""
Insurer Configuration

Configuration for each insurance company's public disclosure page.
Defines how to parse their specific HTML structure.

Epic: Epic 1, Story 1.0
Created: 2025-11-28
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class InsurerConfig:
    """Configuration for a specific insurer's crawler"""

    # Basic Info
    name: str
    code: str  # Short code (e.g., "samsung_life")

    # URL Configuration
    base_url: str
    policies_url: str

    # HTML Selectors (CSS or XPath)
    table_selector: str
    row_selector: str
    policy_name_selector: str
    file_name_selector: Optional[str] = None
    download_link_selector: str = "a[href]"
    publication_date_selector: Optional[str] = None
    category_selector: Optional[str] = None

    # Pagination
    has_pagination: bool = False
    next_page_selector: Optional[str] = None
    max_pages: int = 10

    # Rate Limiting
    request_delay: float = 2.0  # seconds between requests
    respect_robots_txt: bool = True

    # Headers
    user_agent: str = "InsureGraphBot/1.0 (Policy Research; +https://insuregraph.com/bot)"


# ============================================
# Insurer Configurations
# ============================================

INSURER_CONFIGS: Dict[str, InsurerConfig] = {
    # Samsung Life Insurance (Example - needs real selectors)
    "samsung_life": InsurerConfig(
        name="삼성생명",
        code="samsung_life",
        base_url="https://www.samsunglife.com",
        policies_url="https://www.samsunglife.com/customer/disclosure/policies",
        table_selector="table.policy-list",
        row_selector="tr",
        policy_name_selector="td.policy-name",
        file_name_selector="td.file-name",
        download_link_selector="a.download",
        publication_date_selector="td.date",
        category_selector="td.category",
        has_pagination=True,
        next_page_selector="a.page-next",
        max_pages=20,
    ),

    # Hanwha Life Insurance (Example - needs real selectors)
    "hanwha_life": InsurerConfig(
        name="한화생명",
        code="hanwha_life",
        base_url="https://www.hanwhalife.com",
        policies_url="https://www.hanwhalife.com/customer/policies",
        table_selector="div.policy-container",
        row_selector="div.policy-item",
        policy_name_selector="span.title",
        download_link_selector="a.btn-download",
        publication_date_selector="span.date",
        has_pagination=False,
    ),

    # KB Insurance (Example - needs real selectors)
    "kb_insurance": InsurerConfig(
        name="KB손해보험",
        code="kb_insurance",
        base_url="https://www.kbinsurance.co.kr",
        policies_url="https://www.kbinsurance.co.kr/disclosure/policies.do",
        table_selector="table#policyList",
        row_selector="tbody tr",
        policy_name_selector="td:nth-child(2)",
        file_name_selector="td:nth-child(3)",
        download_link_selector="td:nth-child(4) a",
        publication_date_selector="td:nth-child(1)",
        has_pagination=True,
        next_page_selector="a.next",
    ),

    # Test/Mock Insurer for development
    "test_insurer": InsurerConfig(
        name="테스트보험사",
        code="test_insurer",
        base_url="http://localhost:8080",
        policies_url="http://localhost:8080/policies",
        table_selector="table",
        row_selector="tr",
        policy_name_selector="td:nth-child(1)",
        download_link_selector="td:nth-child(2) a",
        publication_date_selector="td:nth-child(3)",
        request_delay=0.1,
    ),
}


def get_insurer_config(code: str) -> Optional[InsurerConfig]:
    """Get configuration for an insurer by code"""
    return INSURER_CONFIGS.get(code)


def list_insurers() -> List[str]:
    """List all configured insurer codes"""
    return list(INSURER_CONFIGS.keys())
