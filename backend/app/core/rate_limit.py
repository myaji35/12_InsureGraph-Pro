"""
Rate Limiting Middleware

Story 3.4: Rate Limiting & Monitoring - Rate Limiting 구현
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
import hashlib

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from app.core.config import settings


# ============================================================================
# Rate Limit Storage (In-Memory)
# ============================================================================


class RateLimitStore:
    """
    Rate limit 정보를 저장하는 In-Memory 스토어

    Production: Redis로 교체 필요
    """
    def __init__(self):
        # key: identifier (IP or user_id)
        # value: {count: int, window_start: datetime}
        self._store: Dict[str, Dict] = {}

    def get(self, key: str) -> Optional[Dict]:
        """키로 rate limit 정보 조회"""
        return self._store.get(key)

    def set(self, key: str, value: Dict):
        """Rate limit 정보 저장"""
        self._store[key] = value

    def delete(self, key: str):
        """키 삭제"""
        if key in self._store:
            del self._store[key]

    def cleanup_expired(self, window_seconds: int):
        """만료된 항목 정리"""
        now = datetime.now()
        expired_keys = []

        for key, value in self._store.items():
            window_start = value.get("window_start")
            if window_start and (now - window_start).total_seconds() > window_seconds:
                expired_keys.append(key)

        for key in expired_keys:
            del self._store[key]


# Global rate limit store
_rate_limit_store = RateLimitStore()


# ============================================================================
# Rate Limiter
# ============================================================================


class RateLimiter:
    """
    Rate Limiter 클래스

    Sliding window 알고리즘 사용
    """
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        identifier_func: Optional[Callable] = None
    ):
        """
        Args:
            max_requests: 윈도우 내 최대 요청 수
            window_seconds: 윈도우 크기 (초)
            identifier_func: 식별자 생성 함수 (None이면 IP 사용)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.identifier_func = identifier_func or self._default_identifier

    def _default_identifier(self, request: Request) -> str:
        """기본 식별자: IP 주소"""
        # Try to get real IP from X-Forwarded-For header
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Fallback to client host
        return request.client.host if request.client else "unknown"

    async def check_rate_limit(self, request: Request) -> tuple[bool, Dict]:
        """
        Rate limit 확인

        Returns:
            (allowed, info)
            - allowed: bool - 요청 허용 여부
            - info: Dict - rate limit 정보
        """
        # Get identifier
        identifier = self.identifier_func(request)

        # Get current data
        now = datetime.now()
        data = _rate_limit_store.get(identifier)

        # Initialize if not exists
        if not data:
            data = {
                "count": 0,
                "window_start": now
            }

        # Check if window has expired
        window_start = data["window_start"]
        elapsed = (now - window_start).total_seconds()

        if elapsed > self.window_seconds:
            # Reset window
            data = {
                "count": 0,
                "window_start": now
            }

        # Increment count
        data["count"] += 1

        # Save
        _rate_limit_store.set(identifier, data)

        # Check if limit exceeded
        allowed = data["count"] <= self.max_requests

        # Calculate remaining and reset time
        remaining = max(0, self.max_requests - data["count"])
        reset_time = window_start + timedelta(seconds=self.window_seconds)

        info = {
            "limit": self.max_requests,
            "remaining": remaining,
            "reset": reset_time.isoformat(),
            "identifier": identifier,
        }

        return allowed, info


# ============================================================================
# Rate Limit Middleware
# ============================================================================


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate Limiting Middleware

    모든 요청에 대해 rate limit을 적용합니다.
    """
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.rate_limiter = RateLimiter(
            max_requests=max_requests,
            window_seconds=window_seconds
        )
        self.enabled = settings.RATE_LIMIT_ENABLED

    async def dispatch(self, request: Request, call_next):
        """요청 처리"""
        # Skip if disabled
        if not self.enabled:
            return await call_next(request)

        # Skip health check and metrics endpoints
        if request.url.path in ["/health", "/api/v1/health", "/api/v1/metrics"]:
            return await call_next(request)

        # Check rate limit
        allowed, info = await self.rate_limiter.check_rate_limit(request)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded: {info['identifier']} on {request.url.path}"
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "error_message": "Too many requests. Please try again later.",
                    "limit": info["limit"],
                    "reset": info["reset"],
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": info["reset"],
                    "Retry-After": str(self.rate_limiter.window_seconds),
                }
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = info["reset"]

        return response


# ============================================================================
# User-based Rate Limiter
# ============================================================================


def create_user_rate_limiter(max_requests: int = 1000, window_seconds: int = 3600):
    """
    사용자 기반 Rate Limiter 생성

    JWT 토큰에서 사용자 ID를 추출하여 사용합니다.

    Args:
        max_requests: 윈도우 내 최대 요청 수
        window_seconds: 윈도우 크기 (초)
    """
    def user_identifier(request: Request) -> str:
        # Try to get user from token
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            # Hash token to create identifier
            return hashlib.sha256(token.encode()).hexdigest()[:16]

        # Fallback to IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.client.host if request.client else "unknown"

    return RateLimiter(
        max_requests=max_requests,
        window_seconds=window_seconds,
        identifier_func=user_identifier
    )


# ============================================================================
# Endpoint-specific Rate Limiters
# ============================================================================


# Login endpoint: 5 requests per 5 minutes
login_rate_limiter = RateLimiter(max_requests=5, window_seconds=300)

# Query endpoint: 20 requests per minute
query_rate_limiter = create_user_rate_limiter(max_requests=20, window_seconds=60)

# Document upload: 10 requests per hour
upload_rate_limiter = create_user_rate_limiter(max_requests=10, window_seconds=3600)


# ============================================================================
# Helper Function
# ============================================================================


async def check_rate_limit(request: Request, limiter: RateLimiter):
    """
    Rate limit 확인 헬퍼 함수

    FastAPI dependency로 사용할 수 있습니다.
    """
    allowed, info = await limiter.check_rate_limit(request)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error_code": "RATE_LIMIT_EXCEEDED",
                "error_message": "Too many requests. Please try again later.",
                "limit": info["limit"],
                "reset": info["reset"],
            }
        )

    return info
