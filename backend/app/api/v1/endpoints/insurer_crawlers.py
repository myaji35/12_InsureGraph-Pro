"""
Insurer Crawlers API Endpoints
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from loguru import logger

from app.services.crawlers.crawler_factory import (
    get_crawler,
    get_available_insurers,
    is_insurer_supported
)

router = APIRouter()


class CrawlRequest(BaseModel):
    """Crawling request model"""
    insurer_code: str
    category: Optional[str] = None
    save_to_db: bool = True


class CrawlResponse(BaseModel):
    """Crawling response model"""
    success: bool
    insurer_code: str
    insurer_name: str
    total_documents: int
    message: str


@router.get("/available-insurers")
async def list_available_insurers():
    """List available insurers"""
    try:
        insurers = get_available_insurers()
        insurer_names = {
            "samsung_life": "Samsung Life",
            "kb_insurance": "KB Insurance",
            "samsung_fire": "Samsung Fire"
        }
        result = [
            {
                "code": code,
                "name": insurer_names.get(code, code),
                "supported": True
            }
            for code in insurers
        ]
        return {
            "success": True,
            "insurers": result,
            "total": len(result)
        }
    except Exception as e:
        logger.error(f"Failed to list available insurers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-connection/{insurer_code}")
async def test_crawler_connection(insurer_code: str):
    """Test crawler connection"""
    try:
        if not is_insurer_supported(insurer_code):
            available = get_available_insurers()
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported insurer: {insurer_code}. Available: {', '.join(available)}"
            )
        crawler = get_crawler(insurer_code)
        is_connected = await crawler.test_connection()
        return {
            "success": True,
            "insurer_code": insurer_code,
            "insurer_name": crawler.config.insurer_name,
            "base_url": crawler.config.base_url,
            "connected": is_connected,
            "message": "Connection successful" if is_connected else "Connection failed"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
