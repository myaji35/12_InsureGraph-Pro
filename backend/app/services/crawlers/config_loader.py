"""
Crawler Configuration Loader

YAML 파일로부터 보험사 크롤러 설정을 로드
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from app.services.crawlers.base_crawler import InsurerConfig, CrawlMethod, AuthMethod


class CrawlerConfigLoader:
    """크롤러 설정 로더"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Args:
            config_dir: 설정 파일 디렉토리 경로
        """
        if config_dir is None:
            # 기본 경로: backend/app/services/crawlers/configs
            config_dir = Path(__file__).parent / "configs"

        self.config_dir = Path(config_dir)

        if not self.config_dir.exists():
            logger.warning(f"Config directory does not exist: {self.config_dir}")
            self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self, insurer_code: str) -> Optional[InsurerConfig]:
        """
        특정 보험사의 설정 로드

        Args:
            insurer_code: 보험사 코드

        Returns:
            InsurerConfig 또는 None (파일이 없으면)
        """
        config_file = self.config_dir / f"{insurer_code}.yaml"

        if not config_file.exists():
            logger.warning(f"Config file not found: {config_file}")
            return None

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # YAML 데이터를 InsurerConfig로 변환
            config = self._dict_to_config(data)
            logger.info(f"Loaded config for: {insurer_code}")

            return config

        except Exception as e:
            logger.error(f"Failed to load config for {insurer_code}: {e}")
            return None

    def load_all_configs(self) -> Dict[str, InsurerConfig]:
        """
        모든 보험사 설정 로드

        Returns:
            {insurer_code: InsurerConfig} 딕셔너리
        """
        configs = {}

        for config_file in self.config_dir.glob("*.yaml"):
            insurer_code = config_file.stem

            try:
                config = self.load_config(insurer_code)
                if config:
                    configs[insurer_code] = config

            except Exception as e:
                logger.error(f"Failed to load {config_file}: {e}")
                continue

        logger.info(f"Loaded {len(configs)} configs")
        return configs

    def save_config(self, config: InsurerConfig):
        """
        설정을 YAML 파일로 저장

        Args:
            config: InsurerConfig
        """
        config_file = self.config_dir / f"{config.insurer_code}.yaml"

        try:
            data = self._config_to_dict(config)

            with open(config_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

            logger.info(f"Saved config to: {config_file}")

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    def _dict_to_config(self, data: Dict[str, Any]) -> InsurerConfig:
        """YAML 딕셔너리를 InsurerConfig로 변환"""

        # Enum 변환
        if "crawl_method" in data:
            data["crawl_method"] = CrawlMethod(data["crawl_method"])

        if "auth_method" in data:
            data["auth_method"] = AuthMethod(data["auth_method"])

        return InsurerConfig(**data)

    def _config_to_dict(self, config: InsurerConfig) -> Dict[str, Any]:
        """InsurerConfig를 YAML 딕셔너리로 변환"""

        data = {
            "insurer_code": config.insurer_code,
            "insurer_name": config.insurer_name,
            "base_url": config.base_url,
            "product_list_url": config.product_list_url,
            "crawl_method": config.crawl_method.value,
            "auth_method": config.auth_method.value,

            "product_list_selector": config.product_list_selector,
            "product_name_selector": config.product_name_selector,
            "product_category_selector": config.product_category_selector,
            "download_link_selector": config.download_link_selector,

            "has_pagination": config.has_pagination,
            "pagination_selector": config.pagination_selector,
            "max_pages": config.max_pages,

            "request_delay": config.request_delay,
            "max_retries": config.max_retries,

            "custom_headers": config.custom_headers,

            "wait_for_selector": config.wait_for_selector,
            "wait_timeout": config.wait_timeout,

            "metadata": config.metadata,
        }

        # None 값 제거
        return {k: v for k, v in data.items() if v is not None}


# 싱글톤 로더
_loader = CrawlerConfigLoader()


def load_insurer_config(insurer_code: str) -> Optional[InsurerConfig]:
    """
    보험사 설정 로드 (편의 함수)

    Args:
        insurer_code: 보험사 코드

    Returns:
        InsurerConfig 또는 None
    """
    return _loader.load_config(insurer_code)


def load_all_insurer_configs() -> Dict[str, InsurerConfig]:
    """
    모든 보험사 설정 로드 (편의 함수)

    Returns:
        {insurer_code: InsurerConfig} 딕셔너리
    """
    return _loader.load_all_configs()


def save_insurer_config(config: InsurerConfig):
    """
    보험사 설정 저장 (편의 함수)

    Args:
        config: InsurerConfig
    """
    _loader.save_config(config)
