"""
Input Validation and Sanitization

입력 검증 및 정제
"""

import re
from typing import Optional
from html import escape
import unicodedata

from loguru import logger


class InputSanitizer:
    """
    입력 정제 클래스

    XSS, SQL Injection 등의 공격을 방어합니다.
    """

    # 위험한 패턴들
    SQL_INJECTION_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bselect\b.*\bfrom\b)",
        r"(\binsert\b.*\binto\b)",
        r"(\bupdate\b.*\bset\b)",
        r"(\bdelete\b.*\bfrom\b)",
        r"(\bdrop\b.*\btable\b)",
        r"(--|\#|\/\*|\*\/)",  # SQL comments
        r"(\bor\b\s+\d+\s*=\s*\d+)",  # or 1=1
        r"(\band\b\s+\d+\s*=\s*\d+)",  # and 1=1
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",  # onclick, onload, etc.
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",  # ../
        r"\.\.",  # ..
        r"%2e%2e",  # URL encoded ..
        r"\.\.%2f",  # ..%2f
    ]

    @classmethod
    def sanitize_text(cls, text: str, allow_html: bool = False) -> str:
        """
        텍스트를 정제합니다.

        Args:
            text: 원본 텍스트
            allow_html: HTML 허용 여부

        Returns:
            str: 정제된 텍스트
        """
        if not text:
            return text

        # 1. Unicode 정규화 (같은 문자의 다른 표현 통일)
        text = unicodedata.normalize('NFKC', text)

        # 2. HTML escape (XSS 방어)
        if not allow_html:
            text = escape(text)

        # 3. 제어 문자 제거 (NULL byte 등)
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\n\r\t')

        # 4. 앞뒤 공백 제거
        text = text.strip()

        return text

    @classmethod
    def check_sql_injection(cls, text: str) -> tuple[bool, Optional[str]]:
        """
        SQL Injection 시도를 감지합니다.

        Args:
            text: 검사할 텍스트

        Returns:
            tuple[bool, Optional[str]]: (의심 여부, 매칭된 패턴)
        """
        if not text:
            return False, None

        text_lower = text.lower()

        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {pattern}")
                return True, pattern

        return False, None

    @classmethod
    def check_xss(cls, text: str) -> tuple[bool, Optional[str]]:
        """
        XSS 공격을 감지합니다.

        Args:
            text: 검사할 텍스트

        Returns:
            tuple[bool, Optional[str]]: (의심 여부, 매칭된 패턴)
        """
        if not text:
            return False, None

        text_lower = text.lower()

        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning(f"Potential XSS detected: {pattern}")
                return True, pattern

        return False, None

    @classmethod
    def check_path_traversal(cls, path: str) -> tuple[bool, Optional[str]]:
        """
        Path Traversal 공격을 감지합니다.

        Args:
            path: 검사할 경로

        Returns:
            tuple[bool, Optional[str]]: (의심 여부, 매칭된 패턴)
        """
        if not path:
            return False, None

        path_lower = path.lower()

        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, path_lower, re.IGNORECASE):
                logger.warning(f"Potential path traversal detected: {pattern}")
                return True, pattern

        return False, None

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        파일명을 안전하게 정제합니다.

        Args:
            filename: 원본 파일명

        Returns:
            str: 정제된 파일명
        """
        if not filename:
            return ""

        # 1. 경로 구분자 제거
        filename = filename.replace('/', '_').replace('\\', '_')

        # 2. 위험한 문자 제거
        filename = re.sub(r'[<>:"|?*]', '', filename)

        # 3. Path traversal 패턴 제거
        filename = filename.replace('..', '')

        # 4. 제어 문자 제거
        filename = ''.join(char for char in filename if unicodedata.category(char)[0] != 'C')

        # 5. 앞뒤 공백 및 점 제거
        filename = filename.strip('. ')

        # 6. 길이 제한 (255자)
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            max_name_len = 255 - len(ext) - 1
            filename = f"{name[:max_name_len]}.{ext}" if ext else name[:255]

        return filename

    @classmethod
    def validate_email(cls, email: str) -> bool:
        """
        이메일 형식을 검증합니다.

        Args:
            email: 이메일 주소

        Returns:
            bool: 유효 여부
        """
        if not email:
            return False

        # RFC 5322 기반 간단한 이메일 검증
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """
        전화번호 형식을 검증합니다 (한국 전화번호).

        Args:
            phone: 전화번호

        Returns:
            bool: 유효 여부
        """
        if not phone:
            return False

        # 숫자만 추출
        digits = re.sub(r'\D', '', phone)

        # 한국 전화번호 패턴
        # 010-1234-5678 (11자리) or 02-1234-5678 (9-10자리)
        return len(digits) in [9, 10, 11]

    @classmethod
    def sanitize_url(cls, url: str) -> Optional[str]:
        """
        URL을 정제합니다.

        Args:
            url: 원본 URL

        Returns:
            Optional[str]: 정제된 URL (위험한 경우 None)
        """
        if not url:
            return None

        # 1. 허용되는 프로토콜만 허용
        allowed_protocols = ['http://', 'https://']
        if not any(url.lower().startswith(proto) for proto in allowed_protocols):
            logger.warning(f"Disallowed URL protocol: {url}")
            return None

        # 2. javascript: 프로토콜 차단
        if 'javascript:' in url.lower():
            logger.warning(f"JavaScript protocol detected in URL: {url}")
            return None

        # 3. 기본 정제
        url = url.strip()

        return url


class InputValidator:
    """
    입력 검증 클래스

    비즈니스 로직 레벨의 검증을 수행합니다.
    """

    @staticmethod
    def validate_query_length(query: str, max_length: int = 1000) -> tuple[bool, Optional[str]]:
        """
        질의문 길이를 검증합니다.

        Args:
            query: 질의문
            max_length: 최대 길이

        Returns:
            tuple[bool, Optional[str]]: (유효 여부, 에러 메시지)
        """
        if not query:
            return False, "Query cannot be empty"

        if len(query) > max_length:
            return False, f"Query too long (max {max_length} characters)"

        return True, None

    @staticmethod
    def validate_document_name(name: str, max_length: int = 200) -> tuple[bool, Optional[str]]:
        """
        문서명을 검증합니다.

        Args:
            name: 문서명
            max_length: 최대 길이

        Returns:
            tuple[bool, Optional[str]]: (유효 여부, 에러 메시지)
        """
        if not name:
            return False, "Document name cannot be empty"

        if len(name) > max_length:
            return False, f"Document name too long (max {max_length} characters)"

        # 위험한 문자 확인
        dangerous_chars = ['<', '>', '|', '\x00']
        if any(char in name for char in dangerous_chars):
            return False, "Document name contains invalid characters"

        return True, None

    @staticmethod
    def validate_user_input(
        text: str,
        min_length: int = 1,
        max_length: int = 10000,
        check_sql_injection: bool = True,
        check_xss: bool = True
    ) -> tuple[bool, Optional[str]]:
        """
        사용자 입력을 종합적으로 검증합니다.

        Args:
            text: 입력 텍스트
            min_length: 최소 길이
            max_length: 최대 길이
            check_sql_injection: SQL Injection 검사 여부
            check_xss: XSS 검사 여부

        Returns:
            tuple[bool, Optional[str]]: (유효 여부, 에러 메시지)
        """
        if not text:
            return False, "Input cannot be empty"

        if len(text) < min_length:
            return False, f"Input too short (min {min_length} characters)"

        if len(text) > max_length:
            return False, f"Input too long (max {max_length} characters)"

        # SQL Injection 검사
        if check_sql_injection:
            is_sql_injection, pattern = InputSanitizer.check_sql_injection(text)
            if is_sql_injection:
                return False, "Input contains potentially malicious SQL patterns"

        # XSS 검사
        if check_xss:
            is_xss, pattern = InputSanitizer.check_xss(text)
            if is_xss:
                return False, "Input contains potentially malicious scripts"

        return True, None


# Convenience functions
def sanitize_text(text: str, allow_html: bool = False) -> str:
    """텍스트 정제 (편의 함수)"""
    return InputSanitizer.sanitize_text(text, allow_html=allow_html)


def sanitize_filename(filename: str) -> str:
    """파일명 정제 (편의 함수)"""
    return InputSanitizer.sanitize_filename(filename)


def validate_user_input(text: str, max_length: int = 10000) -> tuple[bool, Optional[str]]:
    """사용자 입력 검증 (편의 함수)"""
    return InputValidator.validate_user_input(text, max_length=max_length)


# Export
__all__ = [
    "InputSanitizer",
    "InputValidator",
    "sanitize_text",
    "sanitize_filename",
    "validate_user_input",
]
