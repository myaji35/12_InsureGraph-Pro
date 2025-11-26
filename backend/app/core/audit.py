"""
Audit Logging System

감사 로깅 시스템 - 모든 중요한 작업을 기록
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import json

from loguru import logger


class AuditEventType(str, Enum):
    """감사 이벤트 타입"""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    PASSWORD_CHANGE = "password_change"
    TOKEN_REFRESH = "token_refresh"

    # Data Access
    READ_USER = "read_user"
    READ_DOCUMENT = "read_document"
    READ_QUERY = "read_query"

    # Data Modification
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    CREATE_DOCUMENT = "create_document"
    UPDATE_DOCUMENT = "update_document"
    DELETE_DOCUMENT = "delete_document"

    # Business Operations
    EXECUTE_QUERY = "execute_query"
    UPLOAD_FILE = "upload_file"
    DOWNLOAD_FILE = "download_file"

    # Admin Operations
    APPROVE_USER = "approve_user"
    SUSPEND_USER = "suspend_user"
    CHANGE_ROLE = "change_role"
    VIEW_AUDIT_LOG = "view_audit_log"

    # Security Events
    FAILED_LOGIN = "failed_login"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_TOKEN = "invalid_token"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"

    # Compliance Events
    PII_ACCESS = "pii_access"
    COMPLIANCE_CHECK = "compliance_check"
    CITATION_VALIDATION = "citation_validation"


class AuditSeverity(str, Enum):
    """감사 이벤트 심각도"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogger:
    """
    감사 로깅 클래스

    모든 중요한 작업을 WHO, WHAT, WHEN, WHERE로 기록합니다.
    """

    # In-memory storage (production에서는 DB 사용)
    _audit_logs: List[Dict[str, Any]] = []

    @classmethod
    def log_event(
        cls,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        success: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        감사 이벤트를 기록합니다.

        Args:
            event_type: 이벤트 타입
            user_id: 사용자 ID (WHO)
            resource_type: 리소스 타입 (WHAT)
            resource_id: 리소스 ID (WHAT)
            action: 액션 (WHAT)
            severity: 심각도
            success: 성공 여부
            ip_address: IP 주소 (WHERE)
            user_agent: User agent
            details: 추가 상세 정보
        """
        timestamp = datetime.utcnow()

        audit_entry = {
            "timestamp": timestamp.isoformat(),
            "event_type": event_type.value,
            "user_id": user_id or "anonymous",
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "severity": severity.value,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details or {},
        }

        cls._audit_logs.append(audit_entry)

        # 로그 출력
        log_message = (
            f"[AUDIT] {event_type.value} | "
            f"User: {user_id or 'anonymous'} | "
            f"Resource: {resource_type}:{resource_id} | "
            f"Success: {success}"
        )

        if severity == AuditSeverity.CRITICAL:
            logger.critical(log_message)
        elif severity == AuditSeverity.ERROR:
            logger.error(log_message)
        elif severity == AuditSeverity.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)

    @classmethod
    def log_auth_event(
        cls,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        success: bool = True,
        failure_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
    ):
        """
        인증 관련 이벤트를 기록합니다.

        Args:
            event_type: 이벤트 타입 (LOGIN, LOGOUT, etc.)
            user_id: 사용자 ID
            email: 이메일 (마스킹 처리)
            success: 성공 여부
            failure_reason: 실패 이유
            ip_address: IP 주소
        """
        from app.core.pii import mask_email, mask_ip_address

        details = {}

        if email:
            details["email_masked"] = mask_email(email)

        if not success and failure_reason:
            details["failure_reason"] = failure_reason

        severity = AuditSeverity.INFO if success else AuditSeverity.WARNING

        cls.log_event(
            event_type=event_type,
            user_id=user_id,
            resource_type="auth",
            action=event_type.value,
            severity=severity,
            success=success,
            ip_address=mask_ip_address(ip_address) if ip_address else None,
            details=details,
        )

    @classmethod
    def log_data_access(
        cls,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str = "read",
        pii_fields: Optional[List[str]] = None,
        ip_address: Optional[str] = None,
    ):
        """
        데이터 접근을 기록합니다.

        Args:
            user_id: 사용자 ID
            resource_type: 리소스 타입 (user, document, query)
            resource_id: 리소스 ID
            action: 액션 (read, create, update, delete)
            pii_fields: 접근한 PII 필드
            ip_address: IP 주소
        """
        from app.core.pii import mask_ip_address

        details = {}
        if pii_fields:
            details["pii_fields_accessed"] = pii_fields

        event_type_map = {
            ("user", "read"): AuditEventType.READ_USER,
            ("document", "read"): AuditEventType.READ_DOCUMENT,
            ("query", "read"): AuditEventType.READ_QUERY,
            ("user", "create"): AuditEventType.CREATE_USER,
            ("user", "update"): AuditEventType.UPDATE_USER,
            ("user", "delete"): AuditEventType.DELETE_USER,
            ("document", "create"): AuditEventType.CREATE_DOCUMENT,
            ("document", "update"): AuditEventType.UPDATE_DOCUMENT,
            ("document", "delete"): AuditEventType.DELETE_DOCUMENT,
        }

        event_type = event_type_map.get(
            (resource_type, action),
            AuditEventType.READ_USER  # Default
        )

        severity = AuditSeverity.INFO
        if pii_fields:
            severity = AuditSeverity.WARNING  # PII 접근은 경고

        cls.log_event(
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            severity=severity,
            success=True,
            ip_address=mask_ip_address(ip_address) if ip_address else None,
            details=details,
        )

    @classmethod
    def log_security_event(
        cls,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ):
        """
        보안 이벤트를 기록합니다.

        Args:
            event_type: 이벤트 타입
            user_id: 사용자 ID
            details: 상세 정보
            ip_address: IP 주소
        """
        from app.core.pii import mask_ip_address

        cls.log_event(
            event_type=event_type,
            user_id=user_id,
            resource_type="security",
            action=event_type.value,
            severity=AuditSeverity.ERROR if not user_id else AuditSeverity.WARNING,
            success=False,
            ip_address=mask_ip_address(ip_address) if ip_address else None,
            details=details or {},
        )

    @classmethod
    def get_audit_logs(
        cls,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        resource_type: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        감사 로그를 조회합니다.

        Args:
            user_id: 사용자 ID 필터
            event_type: 이벤트 타입 필터
            resource_type: 리소스 타입 필터
            severity: 심각도 필터
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 반환 개수
            offset: 오프셋

        Returns:
            Dict[str, Any]: {
                "total": int,
                "logs": List[Dict[str, Any]],
                "page": int,
                "page_size": int,
            }
        """
        logs = cls._audit_logs.copy()

        # 필터링
        if user_id:
            logs = [log for log in logs if log["user_id"] == user_id]

        if event_type:
            logs = [log for log in logs if log["event_type"] == event_type.value]

        if resource_type:
            logs = [log for log in logs if log["resource_type"] == resource_type]

        if severity:
            logs = [log for log in logs if log["severity"] == severity.value]

        if start_date:
            logs = [
                log for log in logs
                if datetime.fromisoformat(log["timestamp"]) >= start_date
            ]

        if end_date:
            logs = [
                log for log in logs
                if datetime.fromisoformat(log["timestamp"]) <= end_date
            ]

        # 정렬 (최신 순)
        logs = sorted(logs, key=lambda x: x["timestamp"], reverse=True)

        total = len(logs)

        # 페이징
        logs = logs[offset:offset + limit]

        return {
            "total": total,
            "logs": logs,
            "page": (offset // limit) + 1,
            "page_size": limit,
        }

    @classmethod
    def generate_compliance_report(
        cls,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        규제 준수 리포트를 생성합니다.

        Args:
            start_date: 시작 날짜 (기본: 30일 전)
            end_date: 종료 날짜 (기본: 현재)

        Returns:
            Dict[str, Any]: 규제 준수 리포트
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        logs_result = cls.get_audit_logs(
            start_date=start_date,
            end_date=end_date,
            limit=10000  # Get all logs
        )

        logs = logs_result["logs"]
        total_events = logs_result["total"]

        # 통계 계산
        auth_events = [log for log in logs if "login" in log["event_type"] or "logout" in log["event_type"]]
        data_access_events = [log for log in logs if log["event_type"] in [
            "read_user", "read_document", "read_query"
        ]]
        pii_access_events = [
            log for log in logs
            if log["details"].get("pii_fields_accessed")
        ]
        security_events = [
            log for log in logs
            if log["severity"] in ["error", "critical"]
        ]
        failed_logins = [
            log for log in logs
            if log["event_type"] == "failed_login"
        ]

        # 사용자별 활동
        user_activity = {}
        for log in logs:
            user_id = log["user_id"]
            if user_id not in user_activity:
                user_activity[user_id] = 0
            user_activity[user_id] += 1

        top_users = sorted(
            user_activity.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        report = {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": {
                "total_events": total_events,
                "auth_events": len(auth_events),
                "data_access_events": len(data_access_events),
                "pii_access_events": len(pii_access_events),
                "security_events": len(security_events),
                "failed_logins": len(failed_logins),
            },
            "top_users": [
                {"user_id": user_id, "event_count": count}
                for user_id, count in top_users
            ],
            "security_alerts": [
                {
                    "timestamp": log["timestamp"],
                    "event_type": log["event_type"],
                    "user_id": log["user_id"],
                    "severity": log["severity"],
                }
                for log in security_events[:20]  # Top 20
            ],
            "pii_access_summary": {
                "total_pii_accesses": len(pii_access_events),
                "users_accessed_pii": len(set(log["user_id"] for log in pii_access_events)),
            },
        }

        return report

    @classmethod
    def clear_logs(cls):
        """모든 감사 로그를 삭제합니다 (테스트용)."""
        cls._audit_logs.clear()


# Convenience functions
def log_auth(event_type: AuditEventType, user_id: Optional[str] = None, **kwargs):
    """인증 이벤트 로깅 (편의 함수)"""
    AuditLogger.log_auth_event(event_type, user_id=user_id, **kwargs)


def log_access(user_id: str, resource_type: str, resource_id: str, **kwargs):
    """데이터 접근 로깅 (편의 함수)"""
    AuditLogger.log_data_access(user_id, resource_type, resource_id, **kwargs)


def log_security(event_type: AuditEventType, **kwargs):
    """보안 이벤트 로깅 (편의 함수)"""
    AuditLogger.log_security_event(event_type, **kwargs)


# Export
__all__ = [
    "AuditEventType",
    "AuditSeverity",
    "AuditLogger",
    "log_auth",
    "log_access",
    "log_security",
]
