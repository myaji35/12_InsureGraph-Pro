"""
Crawler URL Management Models

Request/Response models for crawler URL CRUD operations
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class CrawlerUrlBase(BaseModel):
    """Base model for crawler URL"""
    insurer: str = Field(..., description="보험사 이름")
    url: str = Field(..., description="크롤링 대상 URL")
    description: Optional[str] = Field(None, description="URL 설명")
    enabled: bool = Field(True, description="활성화 여부")


class CrawlerUrlCreate(CrawlerUrlBase):
    """Request model for creating crawler URL"""
    pass


class CrawlerUrlUpdate(BaseModel):
    """Request model for updating crawler URL"""
    url: Optional[str] = Field(None, description="크롤링 대상 URL")
    description: Optional[str] = Field(None, description="URL 설명")
    enabled: Optional[bool] = Field(None, description="활성화 여부")


class CrawlerUrlResponse(CrawlerUrlBase):
    """Response model for crawler URL"""
    id: UUID = Field(..., description="URL ID")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")

    class Config:
        from_attributes = True


class CrawlerUrlListResponse(BaseModel):
    """Response model for crawler URL list"""
    items: list[CrawlerUrlResponse] = Field(..., description="URL 목록")
    total: int = Field(..., description="전체 개수")
