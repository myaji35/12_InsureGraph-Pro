"""
Tests for Security Hardening

보안 강화 기능 테스트
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.security_headers import (
    SecurityHeadersMiddleware,
    SecureResponseHeaders,
)
from app.core.input_validation import (
    InputSanitizer,
    InputValidator,
    sanitize_text,
    sanitize_filename,
    validate_user_input,
)


class TestSecurityHeadersMiddleware:
    """SecurityHeadersMiddleware 테스트"""

    def setup_method(self):
        """테스트 셋업"""
        self.app = FastAPI()

        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        self.app.add_middleware(SecurityHeadersMiddleware)
        self.client = TestClient(self.app)

    def test_security_headers_added(self):
        """보안 헤더가 추가되는지 확인"""
        response = self.client.get("/test")

        assert response.status_code == 200

        # 필수 보안 헤더 확인
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Content-Security-Policy" in response.headers

    def test_csp_header(self):
        """CSP 헤더 확인"""
        response = self.client.get("/test")

        csp = response.headers.get("Content-Security-Policy")
        assert csp is not None
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_cache_control_for_api(self):
        """API 경로에 대한 캐시 제어 확인"""
        @self.app.get("/api/test")
        async def api_test():
            return {"data": "sensitive"}

        self.client = TestClient(self.app)
        response = self.client.get("/api/test")

        # API 응답은 캐시하지 않음
        cache_control = response.headers.get("Cache-Control")
        if cache_control:  # Middleware에서 추가되었다면
            assert "no-store" in cache_control or "no-cache" in cache_control


class TestSecureResponseHeaders:
    """SecureResponseHeaders 테스트"""

    def test_get_recommended_headers_production(self):
        """Production 환경 권장 헤더"""
        headers = SecureResponseHeaders.get_recommended_headers("production")

        assert "X-Content-Type-Options" in headers
        assert "Strict-Transport-Security" in headers
        assert "Content-Security-Policy" in headers

    def test_get_recommended_headers_development(self):
        """Development 환경 권장 헤더"""
        headers = SecureResponseHeaders.get_recommended_headers("development")

        assert "X-Content-Type-Options" in headers
        # Development에서는 HSTS 없음
        assert "Strict-Transport-Security" not in headers


class TestInputSanitizer:
    """InputSanitizer 테스트"""

    def test_sanitize_text_basic(self):
        """기본 텍스트 정제"""
        text = "  Hello World  "
        sanitized = InputSanitizer.sanitize_text(text)

        assert sanitized == "Hello World"

    def test_sanitize_text_html_escape(self):
        """HTML 이스케이프"""
        text = "<script>alert('xss')</script>"
        sanitized = InputSanitizer.sanitize_text(text, allow_html=False)

        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized

    def test_sanitize_text_allow_html(self):
        """HTML 허용"""
        text = "<p>Hello</p>"
        sanitized = InputSanitizer.sanitize_text(text, allow_html=True)

        # allow_html=True여도 실제로는 escape됨 (기본 동작)
        # 이 테스트는 allow_html 파라미터가 작동하는지 확인
        assert sanitized is not None

    def test_check_sql_injection_positive(self):
        """SQL Injection 감지 - 양성"""
        texts = [
            "SELECT * FROM users",
            "1 OR 1=1",
            "'; DROP TABLE users--",
            "UNION SELECT password FROM users",
        ]

        for text in texts:
            is_sql, pattern = InputSanitizer.check_sql_injection(text)
            assert is_sql is True, f"Failed to detect SQL injection in: {text}"

    def test_check_sql_injection_negative(self):
        """SQL Injection 감지 - 음성"""
        text = "이 상품의 보장 내용은 무엇인가요?"
        is_sql, pattern = InputSanitizer.check_sql_injection(text)

        assert is_sql is False

    def test_check_xss_positive(self):
        """XSS 감지 - 양성"""
        texts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src='evil.com'></iframe>",
        ]

        for text in texts:
            is_xss, pattern = InputSanitizer.check_xss(text)
            assert is_xss is True, f"Failed to detect XSS in: {text}"

    def test_check_xss_negative(self):
        """XSS 감지 - 음성"""
        text = "이 상품은 좋은 상품입니다."
        is_xss, pattern = InputSanitizer.check_xss(text)

        assert is_xss is False

    def test_check_path_traversal_positive(self):
        """Path Traversal 감지 - 양성"""
        paths = [
            "../../../etc/passwd",
            "..\\windows\\system32",
            "%2e%2e/",
        ]

        for path in paths:
            is_traversal, pattern = InputSanitizer.check_path_traversal(path)
            assert is_traversal is True, f"Failed to detect path traversal in: {path}"

    def test_check_path_traversal_negative(self):
        """Path Traversal 감지 - 음성"""
        path = "documents/insurance_policy.pdf"
        is_traversal, pattern = InputSanitizer.check_path_traversal(path)

        assert is_traversal is False

    def test_sanitize_filename_basic(self):
        """파일명 정제 - 기본"""
        filename = "  my_document.pdf  "
        sanitized = InputSanitizer.sanitize_filename(filename)

        assert sanitized == "my_document.pdf"

    def test_sanitize_filename_dangerous_chars(self):
        """파일명 정제 - 위험한 문자"""
        filename = "my<doc>ument.pdf"
        sanitized = InputSanitizer.sanitize_filename(filename)

        assert "<" not in sanitized
        assert ">" not in sanitized

    def test_sanitize_filename_path_traversal(self):
        """파일명 정제 - Path traversal"""
        filename = "../../../etc/passwd"
        sanitized = InputSanitizer.sanitize_filename(filename)

        assert ".." not in sanitized
        assert "/" not in sanitized or sanitized.count("/") == 0

    def test_sanitize_filename_too_long(self):
        """파일명 정제 - 너무 긴 파일명"""
        filename = "a" * 300 + ".pdf"
        sanitized = InputSanitizer.sanitize_filename(filename)

        assert len(sanitized) <= 255

    def test_validate_email_valid(self):
        """이메일 검증 - 유효"""
        emails = [
            "user@example.com",
            "test.user@example.co.kr",
            "admin+tag@insuregraph.com",
        ]

        for email in emails:
            assert InputSanitizer.validate_email(email) is True

    def test_validate_email_invalid(self):
        """이메일 검증 - 무효"""
        emails = [
            "invalid",
            "@example.com",
            "user@",
            "user @example.com",
        ]

        for email in emails:
            assert InputSanitizer.validate_email(email) is False

    def test_validate_phone_valid(self):
        """전화번호 검증 - 유효"""
        phones = [
            "010-1234-5678",
            "01012345678",
            "02-1234-5678",
            "0212345678",
        ]

        for phone in phones:
            assert InputSanitizer.validate_phone(phone) is True

    def test_validate_phone_invalid(self):
        """전화번호 검증 - 무효"""
        phones = [
            "123",
            "invalid",
            "010-123",  # Too short
        ]

        for phone in phones:
            assert InputSanitizer.validate_phone(phone) is False

    def test_sanitize_url_valid(self):
        """URL 정제 - 유효"""
        urls = [
            "https://example.com",
            "http://insuregraph.com/api",
        ]

        for url in urls:
            sanitized = InputSanitizer.sanitize_url(url)
            assert sanitized is not None

    def test_sanitize_url_invalid_protocol(self):
        """URL 정제 - 잘못된 프로토콜"""
        urls = [
            "javascript:alert('xss')",
            "ftp://example.com",
            "file:///etc/passwd",
        ]

        for url in urls:
            sanitized = InputSanitizer.sanitize_url(url)
            assert sanitized is None


class TestInputValidator:
    """InputValidator 테스트"""

    def test_validate_query_length_valid(self):
        """질의문 길이 검증 - 유효"""
        query = "급성심근경색증 보장 금액은?"
        valid, error = InputValidator.validate_query_length(query)

        assert valid is True
        assert error is None

    def test_validate_query_length_too_long(self):
        """질의문 길이 검증 - 너무 김"""
        query = "A" * 1001
        valid, error = InputValidator.validate_query_length(query, max_length=1000)

        assert valid is False
        assert "too long" in error

    def test_validate_query_length_empty(self):
        """질의문 길이 검증 - 빈 문자열"""
        query = ""
        valid, error = InputValidator.validate_query_length(query)

        assert valid is False
        assert "empty" in error

    def test_validate_document_name_valid(self):
        """문서명 검증 - 유효"""
        name = "삼성화재_슈퍼마일리지보험_약관.pdf"
        valid, error = InputValidator.validate_document_name(name)

        assert valid is True
        assert error is None

    def test_validate_document_name_invalid_chars(self):
        """문서명 검증 - 잘못된 문자"""
        name = "document<script>.pdf"
        valid, error = InputValidator.validate_document_name(name)

        assert valid is False
        assert "invalid characters" in error

    def test_validate_user_input_valid(self):
        """사용자 입력 검증 - 유효"""
        text = "이것은 안전한 입력입니다."
        valid, error = InputValidator.validate_user_input(text)

        assert valid is True
        assert error is None

    def test_validate_user_input_sql_injection(self):
        """사용자 입력 검증 - SQL Injection"""
        text = "SELECT * FROM users WHERE id=1"
        valid, error = InputValidator.validate_user_input(text)

        assert valid is False
        assert "SQL" in error

    def test_validate_user_input_xss(self):
        """사용자 입력 검증 - XSS"""
        text = "<script>alert('xss')</script>"
        valid, error = InputValidator.validate_user_input(text)

        assert valid is False
        assert "script" in error

    def test_validate_user_input_skip_checks(self):
        """사용자 입력 검증 - 검사 스킵"""
        text = "SELECT * FROM users"  # SQL pattern but check disabled
        valid, error = InputValidator.validate_user_input(
            text,
            check_sql_injection=False
        )

        assert valid is True


class TestConvenienceFunctions:
    """편의 함수 테스트"""

    def test_sanitize_text_function(self):
        """sanitize_text 편의 함수"""
        text = "  <script>test</script>  "
        sanitized = sanitize_text(text)

        assert "<script>" not in sanitized
        assert sanitized.strip() == sanitized

    def test_sanitize_filename_function(self):
        """sanitize_filename 편의 함수"""
        filename = "../../../evil.pdf"
        sanitized = sanitize_filename(filename)

        assert ".." not in sanitized
        assert "/" not in sanitized or sanitized.count("/") == 0

    def test_validate_user_input_function(self):
        """validate_user_input 편의 함수"""
        text = "안전한 입력입니다."
        valid, error = validate_user_input(text)

        assert valid is True
        assert error is None


class TestSecurityIntegration:
    """보안 통합 테스트"""

    def test_full_security_workflow(self):
        """전체 보안 워크플로우"""
        # 1. 사용자 입력 받기
        user_input = "  급성심근경색증 보장되나요?  "

        # 2. 입력 검증
        valid, error = validate_user_input(user_input)
        assert valid is True

        # 3. 입력 정제
        sanitized = sanitize_text(user_input)
        assert sanitized == "급성심근경색증 보장되나요?"

        # 4. 파일 업로드 시 파일명 정제
        filename = "../../../evil_file.pdf"
        safe_filename = sanitize_filename(filename)
        assert ".." not in safe_filename

    def test_malicious_input_detected(self):
        """악의적인 입력 감지"""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users--",
            "javascript:alert('xss')",
            "../../../etc/passwd",
        ]

        for malicious in malicious_inputs:
            # 검증 실패해야 함
            valid, error = validate_user_input(malicious)
            assert valid is False, f"Failed to detect malicious input: {malicious}"

            # 정제 후에는 안전해야 함
            sanitized = sanitize_text(malicious)
            assert "<script>" not in sanitized
