"""
Crawler API Models

크롤러 API의 요청/응답 모델
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime


class TestCrawlRequest(BaseModel):
    """테스트 크롤링 요청"""
    company_name: str = Field(..., description="보험사명")
    url: str = Field(..., description="크롤링할 URL")
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="사용자 정의 HTTP 헤더"
    )
    save_headers: bool = Field(
        default=False,
        description="헤더 설정 저장 여부"
    )


class DiscoveredFile(BaseModel):
    """발견된 파일 정보"""
    filename: str = Field(..., description="파일명")
    url: Optional[str] = Field(None, description="파일 URL (있는 경우)")
    confidence: float = Field(..., description="신뢰도 (0.0 ~ 1.0)")
    context: Optional[str] = Field(None, description="파일명 주변 컨텍스트")


class CrawlStep(BaseModel):
    """크롤링 진행 단계"""
    step: int = Field(..., description="단계 번호")
    name: str = Field(..., description="단계명")
    status: str = Field(..., description="상태: pending, running, completed, failed")
    message: Optional[str] = Field(None, description="진행 메시지")
    timestamp: datetime = Field(default_factory=datetime.now)


class TestCrawlResponse(BaseModel):
    """테스트 크롤링 응답"""
    success: bool = Field(..., description="크롤링 성공 여부")
    company_name: str = Field(..., description="보험사명")
    url: str = Field(..., description="크롤링한 URL")
    html_saved: bool = Field(..., description="HTML 저장 여부")
    html_path: Optional[str] = Field(None, description="저장된 HTML 파일 경로")
    html_size: Optional[int] = Field(None, description="HTML 파일 크기 (bytes)")
    discovered_files: List[DiscoveredFile] = Field(
        default_factory=list,
        description="발견된 파일 목록"
    )
    total_files: int = Field(0, description="발견된 파일 총 개수")
    steps: List[CrawlStep] = Field(
        default_factory=list,
        description="크롤링 진행 단계"
    )
    logs: List[str] = Field(
        default_factory=list,
        description="크롤링 로그"
    )
    error: Optional[str] = Field(None, description="에러 메시지")
    duration: Optional[float] = Field(None, description="소요 시간 (초)")


class HeaderConfig(BaseModel):
    """헤더 설정"""
    company_name: str = Field(..., description="보험사명")
    headers: Dict[str, str] = Field(..., description="HTTP 헤더")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class HeaderConfigResponse(BaseModel):
    """헤더 설정 응답"""
    company_name: str
    headers: Dict[str, str]
    created_at: datetime
    updated_at: datetime


class SaveHeaderRequest(BaseModel):
    """헤더 저장 요청"""
    company_name: str = Field(..., description="보험사명")
    headers: Dict[str, str] = Field(..., description="HTTP 헤더")
