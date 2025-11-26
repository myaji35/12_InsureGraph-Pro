"""
Security Headers Middleware

보안 헤더 추가 미들웨어
"""

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from loguru import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    보안 헤더 추가 미들웨어

    OWASP 권장 보안 헤더를 자동으로 추가합니다.
    """

    def __init__(
        self,
        app: ASGIApp,
        enable_csp: bool = True,
        enable_hsts: bool = True,
        enable_frame_options: bool = True,
    ):
        """
        Args:
            app: ASGI application
            enable_csp: Content Security Policy 활성화
            enable_hsts: HTTP Strict Transport Security 활성화
            enable_frame_options: X-Frame-Options 활성화
        """
        super().__init__(app)
        self.enable_csp = enable_csp
        self.enable_hsts = enable_hsts
        self.enable_frame_options = enable_frame_options

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        요청 처리 및 보안 헤더 추가
        """
        # 요청 처리
        response = await call_next(request)

        # 보안 헤더 추가
        self._add_security_headers(response)

        return response

    def _add_security_headers(self, response: Response):
        """
        응답에 보안 헤더를 추가합니다.
        """
        # 1. X-Content-Type-Options
        # MIME sniffing 공격 방지
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 2. X-Frame-Options
        # Clickjacking 공격 방지
        if self.enable_frame_options:
            response.headers["X-Frame-Options"] = "DENY"

        # 3. X-XSS-Protection
        # XSS 공격 방지 (구형 브라우저 대응)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 4. Referrer-Policy
        # Referrer 정보 노출 최소화
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 5. Permissions-Policy
        # 브라우저 기능 접근 제한
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        # 6. Content-Security-Policy (CSP)
        # XSS 공격 방지 (강력한 보호)
        if self.enable_csp:
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # FastAPI docs requires unsafe-inline
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: https:",
                "font-src 'self' data:",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
            response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # 7. Strict-Transport-Security (HSTS)
        # HTTPS 강제 (production 환경에서만 활성화 권장)
        if self.enable_hsts:
            # max-age=31536000 (1년), includeSubDomains
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # 8. X-Permitted-Cross-Domain-Policies
        # Adobe Flash/PDF 크로스 도메인 정책 제한
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # 9. Cache-Control (민감한 데이터)
        # API 응답은 캐시하지 않음
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"


class SecureResponseHeaders:
    """
    보안 헤더 유틸리티 클래스
    """

    @staticmethod
    def get_recommended_headers(environment: str = "production") -> dict:
        """
        환경에 맞는 권장 보안 헤더를 반환합니다.

        Args:
            environment: "development" or "production"

        Returns:
            dict: 보안 헤더 딕셔너리
        """
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "X-Permitted-Cross-Domain-Policies": "none",
        }

        # Production 환경에서만 HSTS 활성화
        if environment == "production":
            headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

            # Production CSP (더 엄격)
            headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            # Development CSP (덜 엄격, FastAPI docs 허용)
            headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:"
            )

        return headers

    @staticmethod
    def check_security_headers(response: Response) -> dict:
        """
        응답의 보안 헤더를 검사합니다.

        Args:
            response: Response 객체

        Returns:
            dict: 검사 결과
                {
                    "score": int (0-100),
                    "missing_headers": List[str],
                    "present_headers": List[str],
                }
        """
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Content-Security-Policy",
        ]

        present_headers = []
        missing_headers = []

        for header in required_headers:
            if header in response.headers:
                present_headers.append(header)
            else:
                missing_headers.append(header)

        # Score 계산 (각 헤더당 20점)
        score = (len(present_headers) / len(required_headers)) * 100

        return {
            "score": int(score),
            "missing_headers": missing_headers,
            "present_headers": present_headers,
        }


# Export
__all__ = [
    "SecurityHeadersMiddleware",
    "SecureResponseHeaders",
]
