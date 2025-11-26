"""
Tests for Audit Logging

감사 로깅 테스트
"""

import pytest
from datetime import datetime, timedelta

from app.core.audit import (
    AuditLogger,
    AuditEventType,
    AuditSeverity,
    log_auth,
    log_access,
    log_security,
)


class TestAuditLogger:
    """AuditLogger 테스트"""

    def setup_method(self):
        """테스트 셋업"""
        AuditLogger.clear_logs()

    def test_log_event_basic(self):
        """기본 이벤트 로깅"""
        AuditLogger.log_event(
            event_type=AuditEventType.LOGIN,
            user_id="user_123",
            resource_type="auth",
            action="login",
            success=True,
        )

        logs = AuditLogger.get_audit_logs()

        assert logs["total"] == 1
        assert logs["logs"][0]["event_type"] == "login"
        assert logs["logs"][0]["user_id"] == "user_123"
        assert logs["logs"][0]["success"] is True

    def test_log_event_with_details(self):
        """상세 정보 포함 이벤트 로깅"""
        details = {
            "ip": "192.168.1.1",
            "browser": "Chrome",
        }

        AuditLogger.log_event(
            event_type=AuditEventType.LOGIN,
            user_id="user_123",
            details=details,
        )

        logs = AuditLogger.get_audit_logs()

        assert logs["logs"][0]["details"] == details

    def test_log_event_severity(self):
        """심각도별 이벤트 로깅"""
        severities = [
            AuditSeverity.INFO,
            AuditSeverity.WARNING,
            AuditSeverity.ERROR,
            AuditSeverity.CRITICAL,
        ]

        for severity in severities:
            AuditLogger.log_event(
                event_type=AuditEventType.LOGIN,
                severity=severity,
            )

        logs = AuditLogger.get_audit_logs()

        assert logs["total"] == len(severities)

        severities_in_logs = [log["severity"] for log in logs["logs"]]
        for severity in severities:
            assert severity.value in severities_in_logs

    def test_log_auth_event_success(self):
        """인증 이벤트 로깅 - 성공"""
        AuditLogger.log_auth_event(
            event_type=AuditEventType.LOGIN,
            user_id="user_123",
            email="user@example.com",
            success=True,
            ip_address="192.168.1.1",
        )

        logs = AuditLogger.get_audit_logs()

        assert logs["total"] == 1
        assert logs["logs"][0]["event_type"] == "login"
        assert logs["logs"][0]["success"] is True
        assert "email_masked" in logs["logs"][0]["details"]

    def test_log_auth_event_failure(self):
        """인증 이벤트 로깅 - 실패"""
        AuditLogger.log_auth_event(
            event_type=AuditEventType.FAILED_LOGIN,
            email="user@example.com",
            success=False,
            failure_reason="Invalid password",
        )

        logs = AuditLogger.get_audit_logs()

        assert logs["total"] == 1
        assert logs["logs"][0]["success"] is False
        assert logs["logs"][0]["severity"] == "warning"
        assert logs["logs"][0]["details"]["failure_reason"] == "Invalid password"

    def test_log_data_access(self):
        """데이터 접근 로깅"""
        AuditLogger.log_data_access(
            user_id="user_123",
            resource_type="document",
            resource_id="doc_456",
            action="read",
        )

        logs = AuditLogger.get_audit_logs()

        assert logs["total"] == 1
        assert logs["logs"][0]["resource_type"] == "document"
        assert logs["logs"][0]["resource_id"] == "doc_456"
        assert logs["logs"][0]["action"] == "read"

    def test_log_data_access_with_pii(self):
        """PII 접근 로깅"""
        AuditLogger.log_data_access(
            user_id="user_123",
            resource_type="user",
            resource_id="user_456",
            action="read",
            pii_fields=["email", "phone", "ssn"],
        )

        logs = AuditLogger.get_audit_logs()

        assert logs["total"] == 1
        assert logs["logs"][0]["severity"] == "warning"  # PII 접근은 경고
        assert "pii_fields_accessed" in logs["logs"][0]["details"]
        assert logs["logs"][0]["details"]["pii_fields_accessed"] == ["email", "phone", "ssn"]

    def test_log_security_event(self):
        """보안 이벤트 로깅"""
        AuditLogger.log_security_event(
            event_type=AuditEventType.SQL_INJECTION_ATTEMPT,
            user_id="user_123",
            details={"pattern": "SELECT * FROM users"},
            ip_address="192.168.1.1",
        )

        logs = AuditLogger.get_audit_logs()

        assert logs["total"] == 1
        assert logs["logs"][0]["event_type"] == "sql_injection_attempt"
        assert logs["logs"][0]["severity"] == "warning"
        assert logs["logs"][0]["success"] is False

    def test_get_audit_logs_filter_by_user(self):
        """사용자별 감사 로그 필터링"""
        AuditLogger.log_event(AuditEventType.LOGIN, user_id="user_1")
        AuditLogger.log_event(AuditEventType.LOGIN, user_id="user_2")
        AuditLogger.log_event(AuditEventType.LOGOUT, user_id="user_1")

        logs = AuditLogger.get_audit_logs(user_id="user_1")

        assert logs["total"] == 2
        assert all(log["user_id"] == "user_1" for log in logs["logs"])

    def test_get_audit_logs_filter_by_event_type(self):
        """이벤트 타입별 필터링"""
        AuditLogger.log_event(AuditEventType.LOGIN, user_id="user_1")
        AuditLogger.log_event(AuditEventType.LOGOUT, user_id="user_1")
        AuditLogger.log_event(AuditEventType.LOGIN, user_id="user_2")

        logs = AuditLogger.get_audit_logs(event_type=AuditEventType.LOGIN)

        assert logs["total"] == 2
        assert all(log["event_type"] == "login" for log in logs["logs"])

    def test_get_audit_logs_filter_by_severity(self):
        """심각도별 필터링"""
        AuditLogger.log_event(AuditEventType.LOGIN, severity=AuditSeverity.INFO)
        AuditLogger.log_event(AuditEventType.FAILED_LOGIN, severity=AuditSeverity.WARNING)
        AuditLogger.log_event(AuditEventType.SQL_INJECTION_ATTEMPT, severity=AuditSeverity.ERROR)

        logs = AuditLogger.get_audit_logs(severity=AuditSeverity.ERROR)

        assert logs["total"] == 1
        assert logs["logs"][0]["severity"] == "error"

    def test_get_audit_logs_filter_by_date_range(self):
        """날짜 범위 필터링"""
        # 과거 로그
        old_log_time = datetime.utcnow() - timedelta(days=10)
        AuditLogger._audit_logs.append({
            "timestamp": old_log_time.isoformat(),
            "event_type": "login",
            "user_id": "user_old",
            "resource_type": None,
            "resource_id": None,
            "action": None,
            "severity": "info",
            "success": True,
            "ip_address": None,
            "user_agent": None,
            "details": {},
        })

        # 최근 로그
        AuditLogger.log_event(AuditEventType.LOGIN, user_id="user_recent")

        # 최근 7일간 로그만 조회
        start_date = datetime.utcnow() - timedelta(days=7)
        logs = AuditLogger.get_audit_logs(start_date=start_date)

        assert logs["total"] == 1
        assert logs["logs"][0]["user_id"] == "user_recent"

    def test_get_audit_logs_pagination(self):
        """페이징"""
        # 10개 로그 생성
        for i in range(10):
            AuditLogger.log_event(AuditEventType.LOGIN, user_id=f"user_{i}")

        # 첫 페이지 (5개)
        logs_page1 = AuditLogger.get_audit_logs(limit=5, offset=0)
        assert len(logs_page1["logs"]) == 5
        assert logs_page1["total"] == 10
        assert logs_page1["page"] == 1

        # 두 번째 페이지 (5개)
        logs_page2 = AuditLogger.get_audit_logs(limit=5, offset=5)
        assert len(logs_page2["logs"]) == 5
        assert logs_page2["page"] == 2

    def test_generate_compliance_report(self):
        """규제 준수 리포트 생성"""
        # 다양한 이벤트 생성
        AuditLogger.log_auth_event(AuditEventType.LOGIN, user_id="user_1", success=True)
        AuditLogger.log_auth_event(AuditEventType.FAILED_LOGIN, email="bad@user.com", success=False)

        AuditLogger.log_data_access(
            user_id="user_1",
            resource_type="user",
            resource_id="user_2",
            pii_fields=["email"],
        )

        AuditLogger.log_security_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            user_id="user_3",
        )

        report = AuditLogger.generate_compliance_report()

        assert "report_period" in report
        assert "summary" in report
        assert report["summary"]["total_events"] >= 4
        assert report["summary"]["auth_events"] >= 2
        assert report["summary"]["pii_access_events"] >= 1
        assert report["summary"]["security_events"] >= 1
        assert report["summary"]["failed_logins"] >= 1

        assert "top_users" in report
        assert "security_alerts" in report
        assert "pii_access_summary" in report

    def test_generate_compliance_report_date_range(self):
        """규제 준수 리포트 - 날짜 범위 지정"""
        # 과거 로그
        old_time = datetime.utcnow() - timedelta(days=40)
        AuditLogger._audit_logs.append({
            "timestamp": old_time.isoformat(),
            "event_type": "login",
            "user_id": "user_old",
            "resource_type": "auth",
            "resource_id": None,
            "action": "login",
            "severity": "info",
            "success": True,
            "ip_address": None,
            "user_agent": None,
            "details": {},
        })

        # 최근 로그
        AuditLogger.log_event(AuditEventType.LOGIN, user_id="user_recent")

        # 최근 30일 리포트
        start_date = datetime.utcnow() - timedelta(days=30)
        report = AuditLogger.generate_compliance_report(start_date=start_date)

        # 최근 로그만 포함
        assert report["summary"]["total_events"] == 1


class TestConvenienceFunctions:
    """편의 함수 테스트"""

    def setup_method(self):
        """테스트 셋업"""
        AuditLogger.clear_logs()

    def test_log_auth_function(self):
        """log_auth 편의 함수"""
        log_auth(
            AuditEventType.LOGIN,
            user_id="user_123",
            email="user@example.com",
            success=True,
        )

        logs = AuditLogger.get_audit_logs()

        assert logs["total"] == 1
        assert logs["logs"][0]["event_type"] == "login"

    def test_log_access_function(self):
        """log_access 편의 함수"""
        log_access(
            user_id="user_123",
            resource_type="document",
            resource_id="doc_456",
            action="read",
        )

        logs = AuditLogger.get_audit_logs()

        assert logs["total"] == 1
        assert logs["logs"][0]["resource_type"] == "document"

    def test_log_security_function(self):
        """log_security 편의 함수"""
        log_security(
            AuditEventType.XSS_ATTEMPT,
            user_id="user_123",
            details={"pattern": "<script>"},
        )

        logs = AuditLogger.get_audit_logs()

        assert logs["total"] == 1
        assert logs["logs"][0]["event_type"] == "xss_attempt"


class TestAuditIntegration:
    """Audit 통합 테스트"""

    def setup_method(self):
        """테스트 셋업"""
        AuditLogger.clear_logs()

    def test_full_audit_workflow(self):
        """전체 감사 워크플로우"""
        # 1. 사용자 로그인
        log_auth(
            AuditEventType.LOGIN,
            user_id="user_123",
            email="fp@example.com",
            success=True,
            ip_address="192.168.1.100",
        )

        # 2. 문서 업로드
        log_access(
            user_id="user_123",
            resource_type="document",
            resource_id="doc_456",
            action="create",
        )

        # 3. 문서 조회 (PII 포함)
        log_access(
            user_id="user_123",
            resource_type="document",
            resource_id="doc_456",
            action="read",
            pii_fields=["customer_name", "ssn"],
        )

        # 4. 질의 실행
        AuditLogger.log_event(
            event_type=AuditEventType.EXECUTE_QUERY,
            user_id="user_123",
            resource_type="query",
            resource_id="query_789",
            action="execute",
        )

        # 5. 로그아웃
        log_auth(
            AuditEventType.LOGOUT,
            user_id="user_123",
            success=True,
        )

        # 감사 로그 확인
        logs = AuditLogger.get_audit_logs(user_id="user_123")

        assert logs["total"] == 5

        # 규제 준수 리포트 생성
        report = AuditLogger.generate_compliance_report()

        assert report["summary"]["total_events"] == 5
        assert report["summary"]["auth_events"] == 2  # login + logout
        assert report["summary"]["pii_access_events"] == 1

    def test_security_incident_tracking(self):
        """보안 사고 추적"""
        # 여러 번의 로그인 실패
        for i in range(5):
            log_auth(
                AuditEventType.FAILED_LOGIN,
                email="attacker@evil.com",
                success=False,
                failure_reason="Invalid password",
                ip_address="1.2.3.4",
            )

        # SQL Injection 시도
        log_security(
            AuditEventType.SQL_INJECTION_ATTEMPT,
            details={"pattern": "SELECT * FROM users WHERE id=1 OR 1=1"},
            ip_address="1.2.3.4",
        )

        # XSS 시도
        log_security(
            AuditEventType.XSS_ATTEMPT,
            details={"pattern": "<script>alert('xss')</script>"},
            ip_address="1.2.3.4",
        )

        # 보안 이벤트만 조회
        logs = AuditLogger.get_audit_logs(severity=AuditSeverity.WARNING)

        assert logs["total"] >= 5

        # 규제 준수 리포트
        report = AuditLogger.generate_compliance_report()

        assert report["summary"]["failed_logins"] == 5
        assert report["summary"]["security_events"] >= 2
