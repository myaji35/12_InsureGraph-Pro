"""
Crawler Progress Tracker

크롤링 진행 상황을 추적하고 관리하는 서비스
"""
from typing import Dict, Optional
from datetime import datetime
import asyncio


class CrawlerProgressTracker:
    """크롤링 진행 상황 추적기"""

    _progress_store: Dict[str, Dict] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def start_crawling(cls, insurer: str) -> None:
        """크롤링 시작"""
        async with cls._lock:
            cls._progress_store[insurer] = {
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "current_step": "initializing",
                "progress_percentage": 0,
                "total_product_types": 0,
                "current_product_type": 0,
                "current_product_type_name": "",
                "total_categories": 0,
                "current_category": 0,
                "current_category_name": "",
                "total_documents_found": 0,
                "last_updated": datetime.now().isoformat(),
                "details": []
            }

    @classmethod
    async def update_progress(
        cls,
        insurer: str,
        **kwargs
    ) -> None:
        """진행 상황 업데이트"""
        async with cls._lock:
            if insurer not in cls._progress_store:
                await cls.start_crawling(insurer)

            progress = cls._progress_store[insurer]
            progress.update(kwargs)
            progress["last_updated"] = datetime.now().isoformat()

            # 진행률 자동 계산
            if "total_product_types" in kwargs and "current_product_type" in kwargs:
                total = kwargs["total_product_types"]
                current = kwargs["current_product_type"]
                if total > 0:
                    progress["progress_percentage"] = int((current / total) * 100)

    @classmethod
    async def add_detail(cls, insurer: str, detail: str) -> None:
        """상세 정보 추가"""
        async with cls._lock:
            if insurer not in cls._progress_store:
                await cls.start_crawling(insurer)

            progress = cls._progress_store[insurer]
            progress["details"].append({
                "timestamp": datetime.now().isoformat(),
                "message": detail
            })

            # 최근 50개만 유지
            if len(progress["details"]) > 50:
                progress["details"] = progress["details"][-50:]

    @classmethod
    async def complete_crawling(
        cls,
        insurer: str,
        total_documents: int
    ) -> None:
        """크롤링 완료"""
        async with cls._lock:
            if insurer in cls._progress_store:
                progress = cls._progress_store[insurer]
                progress["status"] = "completed"
                progress["current_step"] = "completed"
                progress["progress_percentage"] = 100
                progress["total_documents_found"] = total_documents
                progress["completed_at"] = datetime.now().isoformat()
                progress["last_updated"] = datetime.now().isoformat()

    @classmethod
    async def fail_crawling(cls, insurer: str, error: str) -> None:
        """크롤링 실패"""
        async with cls._lock:
            if insurer in cls._progress_store:
                progress = cls._progress_store[insurer]
                progress["status"] = "failed"
                progress["current_step"] = "failed"
                progress["error"] = error
                progress["failed_at"] = datetime.now().isoformat()
                progress["last_updated"] = datetime.now().isoformat()

    @classmethod
    async def get_progress(cls, insurer: str) -> Optional[Dict]:
        """진행 상황 조회"""
        async with cls._lock:
            return cls._progress_store.get(insurer)

    @classmethod
    async def clear_progress(cls, insurer: str) -> None:
        """진행 상황 삭제"""
        async with cls._lock:
            if insurer in cls._progress_store:
                del cls._progress_store[insurer]
