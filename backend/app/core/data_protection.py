"""
Data Protection Utilities

데이터 보호 데코레이터, 필터, 유틸리티
"""

import functools
from typing import Any, Callable, Dict, Optional, Union
from datetime import datetime

from fastapi import Request
from loguru import logger

from app.core.pii import PIIHandler, PIIMasker, sanitize_for_logging
from app.core.encryption import EncryptionManager


class DataProtectionConfig:
    """데이터 보호 설정"""

    # 자동 마스킹할 필드
    AUTO_MASK_FIELDS = [
        "email",
        "phone",
        "ssn",
        "social_security_number",
        "credit_card",
        "bank_account",
        "full_name",
        "password",
        "token",
        "secret",
    ]

    # 암호화할 필드 (DB 저장 시)
    ENCRYPTED_FIELDS = [
        "ssn",
        "social_security_number",
        "credit_card",
        "bank_account",
    ]

    # 로그에서 완전히 제거할 필드
    REDACTED_FIELDS = [
        "password",
        "hashed_password",
        "access_token",
        "refresh_token",
        "secret_key",
        "api_key",
    ]


# Global encryption manager
_encryption_manager = EncryptionManager()


def mask_response_pii(response_data: Any) -> Any:
    """
    API 응답 데이터에서 PII를 마스킹합니다.

    Args:
        response_data: 응답 데이터 (dict, list, or other)

    Returns:
        마스킹된 데이터
    """
    if isinstance(response_data, dict):
        return PIIHandler.sanitize_dict(
            response_data,
            fields_to_mask=DataProtectionConfig.AUTO_MASK_FIELDS
        )
    elif isinstance(response_data, list):
        return [mask_response_pii(item) for item in response_data]
    else:
        return response_data


def redact_sensitive_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    민감한 필드를 완전히 제거합니다 (로깅용).

    Args:
        data: 원본 데이터

    Returns:
        Dict[str, Any]: Redacted 데이터
    """
    redacted = data.copy()

    for field in DataProtectionConfig.REDACTED_FIELDS:
        if field in redacted:
            redacted[field] = "[REDACTED]"

    return redacted


def encrypt_sensitive_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    민감한 필드를 암호화합니다 (DB 저장용).

    Args:
        data: 원본 데이터

    Returns:
        Dict[str, Any]: 암호화된 데이터
    """
    return _encryption_manager.encrypt_dict(
        data,
        fields=DataProtectionConfig.ENCRYPTED_FIELDS
    )


def decrypt_sensitive_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    암호화된 필드를 복호화합니다 (DB 조회 후).

    Args:
        data: 암호화된 데이터

    Returns:
        Dict[str, Any]: 복호화된 데이터
    """
    return _encryption_manager.decrypt_dict(
        data,
        fields=DataProtectionConfig.ENCRYPTED_FIELDS
    )


class DataAccessLogger:
    """
    데이터 접근 로거

    PII 접근을 기록하여 감사 추적(Audit Trail)을 생성합니다.
    """

    # In-memory storage (production에서는 DB 사용)
    _access_logs: list[Dict[str, Any]] = []

    @classmethod
    def log_access(
        cls,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        pii_fields: Optional[list[str]] = None,
        request: Optional[Request] = None
    ):
        """
        데이터 접근을 기록합니다.

        Args:
            user_id: 사용자 ID
            action: 액션 (read, create, update, delete)
            resource_type: 리소스 타입 (user, document, etc.)
            resource_id: 리소스 ID
            pii_fields: 접근한 PII 필드 리스트
            request: FastAPI Request 객체
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "pii_fields": pii_fields or [],
            "ip_address": PIIMasker.mask_ip_address(request.client.host) if request else None,
            "user_agent": request.headers.get("user-agent", "Unknown") if request else None,
        }

        cls._access_logs.append(log_entry)

        # 로그 출력 (민감 정보 마스킹)
        logger.info(
            f"[DATA_ACCESS] User {user_id} performed {action} on {resource_type}:{resource_id}"
        )

    @classmethod
    def get_access_logs(
        cls,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """
        접근 로그를 조회합니다.

        Args:
            user_id: 사용자 ID 필터 (선택)
            resource_type: 리소스 타입 필터 (선택)
            limit: 최대 반환 개수

        Returns:
            list[Dict[str, Any]]: 접근 로그 리스트
        """
        logs = cls._access_logs

        if user_id:
            logs = [log for log in logs if log["user_id"] == user_id]

        if resource_type:
            logs = [log for log in logs if log["resource_type"] == resource_type]

        # 최신 순으로 정렬
        logs = sorted(logs, key=lambda x: x["timestamp"], reverse=True)

        return logs[:limit]

    @classmethod
    def clear_logs(cls):
        """로그를 모두 삭제합니다 (테스트용)."""
        cls._access_logs.clear()


def log_pii_access(
    action: str,
    resource_type: str,
    pii_fields: Optional[list[str]] = None
):
    """
    PII 접근 로깅 데코레이터

    Args:
        action: 액션 (read, create, update, delete)
        resource_type: 리소스 타입
        pii_fields: PII 필드 리스트

    Usage:
        @log_pii_access(action="read", resource_type="user", pii_fields=["email", "phone"])
        async def get_user(user_id: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 함수 실행
            result = await func(*args, **kwargs)

            # 로깅 (user_id 추출 시도)
            try:
                # kwargs에서 user_id 또는 current_user 찾기
                user_id = kwargs.get("user_id") or kwargs.get("current_user", {}).get("sub", "unknown")
                resource_id = kwargs.get("document_id") or kwargs.get("query_id") or "unknown"
                request = kwargs.get("request")

                DataAccessLogger.log_access(
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    pii_fields=pii_fields,
                    request=request
                )
            except Exception as e:
                logger.warning(f"Failed to log data access: {e}")

            return result

        return wrapper

    return decorator


def sanitize_for_storage(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    저장용 데이터 정제 (암호화 + 마스킹)

    Args:
        data: 원본 데이터

    Returns:
        Dict[str, Any]: 정제된 데이터
    """
    # 1. 민감 필드 암호화
    sanitized = encrypt_sensitive_fields(data)

    # 2. 불필요한 민감 정보 제거
    sanitized = redact_sensitive_fields(sanitized)

    return sanitized


def sanitize_for_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    응답용 데이터 정제 (PII 마스킹)

    Args:
        data: 원본 데이터

    Returns:
        Dict[str, Any]: 정제된 데이터
    """
    # 1. 암호화된 필드 복호화
    sanitized = decrypt_sensitive_fields(data)

    # 2. PII 마스킹
    sanitized = PIIHandler.sanitize_dict(sanitized)

    # 3. 민감 필드 제거
    sanitized = redact_sensitive_fields(sanitized)

    return sanitized


class PIIValidator:
    """
    PII 검증 클래스

    사용자 입력에 PII가 포함되지 않아야 하는 필드를 검증합니다.
    """

    @staticmethod
    def validate_no_pii_in_query(query: str) -> tuple[bool, Optional[str]]:
        """
        질의문에 PII가 포함되지 않았는지 검증합니다.

        Args:
            query: 사용자 질의문

        Returns:
            tuple[bool, Optional[str]]: (유효 여부, 에러 메시지)
        """
        from app.core.pii import PIIDetector

        detected = PIIDetector.detect(query)

        if detected:
            pii_types = ", ".join([pii_type.value for pii_type in detected.keys()])
            return False, f"Query contains personal information ({pii_types}). Please remove it for privacy protection."

        return True, None

    @staticmethod
    def validate_no_pii_in_document_name(name: str) -> tuple[bool, Optional[str]]:
        """
        문서명에 PII가 포함되지 않았는지 검증합니다.

        Args:
            name: 문서명

        Returns:
            tuple[bool, Optional[str]]: (유효 여부, 에러 메시지)
        """
        from app.core.pii import PIIDetector

        detected = PIIDetector.detect(name)

        if detected:
            return False, "Document name should not contain personal information."

        return True, None


# Export commonly used functions
__all__ = [
    "mask_response_pii",
    "redact_sensitive_fields",
    "encrypt_sensitive_fields",
    "decrypt_sensitive_fields",
    "sanitize_for_storage",
    "sanitize_for_response",
    "sanitize_for_logging",
    "log_pii_access",
    "DataAccessLogger",
    "PIIValidator",
    "DataProtectionConfig",
]
