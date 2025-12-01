"""
Header Storage Service

보험사별 HTTP 헤더 설정을 저장/조회하는 서비스
"""
import json
import os
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

from loguru import logger


class HeaderStorage:
    """보험사별 헤더 설정 저장소"""

    def __init__(self, storage_file: str = "data/header_configs.json"):
        """
        Initialize header storage

        Args:
            storage_file: 저장 파일 경로
        """
        self.storage_file = Path(storage_file)
        self._ensure_storage_file()

    def _ensure_storage_file(self):
        """저장 파일 및 디렉토리 생성"""
        # Create directory if not exists
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)

        # Create file if not exists
        if not self.storage_file.exists():
            self._write_data({})
            logger.info(f"Created header storage file: {self.storage_file}")

    def _read_data(self) -> Dict:
        """데이터 읽기"""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error reading header storage: {e}")
            return {}

    def _write_data(self, data: Dict):
        """데이터 쓰기"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error writing header storage: {e}")
            raise

    def save_headers(
        self,
        company_name: str,
        headers: Dict[str, str]
    ) -> Dict:
        """
        헤더 설정 저장

        Args:
            company_name: 보험사명
            headers: HTTP 헤더

        Returns:
            Dict: 저장된 설정
        """
        data = self._read_data()

        # Create or update config
        config = {
            'company_name': company_name,
            'headers': headers,
            'created_at': data.get(company_name, {}).get('created_at', datetime.now().isoformat()),
            'updated_at': datetime.now().isoformat()
        }

        data[company_name] = config
        self._write_data(data)

        logger.info(f"Saved headers for {company_name}")
        return config

    def get_headers(self, company_name: str) -> Optional[Dict]:
        """
        헤더 설정 조회

        Args:
            company_name: 보험사명

        Returns:
            Optional[Dict]: 헤더 설정 또는 None
        """
        data = self._read_data()
        return data.get(company_name)

    def get_all_headers(self) -> Dict[str, Dict]:
        """
        모든 헤더 설정 조회

        Returns:
            Dict: 보험사별 헤더 설정
        """
        return self._read_data()

    def delete_headers(self, company_name: str) -> bool:
        """
        헤더 설정 삭제

        Args:
            company_name: 보험사명

        Returns:
            bool: 삭제 성공 여부
        """
        data = self._read_data()

        if company_name in data:
            del data[company_name]
            self._write_data(data)
            logger.info(f"Deleted headers for {company_name}")
            return True
        else:
            logger.warning(f"Headers not found for {company_name}")
            return False

    def get_headers_dict_only(self, company_name: str) -> Dict[str, str]:
        """
        헤더 딕셔너리만 조회 (메타데이터 제외)

        Args:
            company_name: 보험사명

        Returns:
            Dict[str, str]: 헤더 딕셔너리
        """
        config = self.get_headers(company_name)
        if config:
            return config.get('headers', {})
        return {}


# Singleton instance
_header_storage: Optional[HeaderStorage] = None


def get_header_storage() -> HeaderStorage:
    """Get singleton header storage instance"""
    global _header_storage
    if _header_storage is None:
        _header_storage = HeaderStorage()
    return _header_storage
