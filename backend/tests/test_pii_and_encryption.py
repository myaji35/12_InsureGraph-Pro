"""
Tests for PII Detection, Masking, and Encryption

개인정보 보호 기능 테스트
"""

import pytest

from app.core.pii import (
    PIIDetector,
    PIIMasker,
    PIIHandler,
    PIIType,
    mask_email,
    mask_phone,
    mask_ssn,
    detect_pii,
    contains_pii,
    sanitize_for_logging,
)
from app.core.encryption import (
    EncryptionManager,
    HashManager,
    encrypt,
    decrypt,
    hash_sha256,
    generate_token,
)
from app.core.data_protection import (
    mask_response_pii,
    redact_sensitive_fields,
    encrypt_sensitive_fields,
    decrypt_sensitive_fields,
    sanitize_for_storage,
    sanitize_for_response,
    DataAccessLogger,
    PIIValidator,
)


class TestPIIDetector:
    """PIIDetector 테스트"""

    def test_detect_email(self):
        """이메일 감지"""
        text = "Contact us at support@example.com or admin@insuregraph.com"
        detected = PIIDetector.detect(text)

        assert PIIType.EMAIL in detected
        assert len(detected[PIIType.EMAIL]) == 2
        assert "support@example.com" in detected[PIIType.EMAIL]

    def test_detect_phone(self):
        """전화번호 감지"""
        text = "Call me at 010-1234-5678 or 01098765432"
        detected = PIIDetector.detect(text)

        assert PIIType.PHONE in detected
        assert len(detected[PIIType.PHONE]) == 2

    def test_detect_ssn(self):
        """주민등록번호 감지"""
        text = "My SSN is 900101-1234567"
        detected = PIIDetector.detect(text)

        assert PIIType.SSN in detected
        assert "900101-1234567" in detected[PIIType.SSN]

    def test_detect_credit_card(self):
        """신용카드 번호 감지"""
        text = "Card: 1234-5678-9012-3456"
        detected = PIIDetector.detect(text)

        assert PIIType.CREDIT_CARD in detected

    def test_detect_ip_address(self):
        """IP 주소 감지"""
        text = "Server IP: 192.168.1.100"
        detected = PIIDetector.detect(text)

        assert PIIType.IP_ADDRESS in detected
        assert "192.168.1.100" in detected[PIIType.IP_ADDRESS]

    def test_contains_pii_true(self):
        """PII 포함 여부 - True"""
        text = "Email: user@example.com"
        assert PIIDetector.contains_pii(text) is True

    def test_contains_pii_false(self):
        """PII 포함 여부 - False"""
        text = "This is a safe text without any PII"
        assert PIIDetector.contains_pii(text) is False

    def test_detect_empty_text(self):
        """빈 텍스트 처리"""
        detected = PIIDetector.detect("")
        assert detected == {}


class TestPIIMasker:
    """PIIMasker 테스트"""

    def test_mask_email(self):
        """이메일 마스킹"""
        assert PIIMasker.mask_email("user@example.com") == "u***@example.com"
        assert PIIMasker.mask_email("a@example.com") == "a@example.com"
        assert PIIMasker.mask_email("ab@example.com") == "a*@example.com"
        assert PIIMasker.mask_email("abcd@example.com") == "a**d@example.com"

    def test_mask_phone(self):
        """전화번호 마스킹"""
        assert PIIMasker.mask_phone("010-1234-5678") == "010-****-5678"
        assert PIIMasker.mask_phone("01012345678") == "010-****-5678"
        assert PIIMasker.mask_phone("010 1234 5678") == "010-****-5678"

    def test_mask_ssn(self):
        """주민등록번호 마스킹"""
        assert PIIMasker.mask_ssn("900101-1234567") == "900101-1******"
        assert PIIMasker.mask_ssn("9001011234567") == "900101-1******"

    def test_mask_credit_card(self):
        """신용카드 마스킹"""
        assert PIIMasker.mask_credit_card("1234-5678-9012-3456") == "****-****-****-3456"
        assert PIIMasker.mask_credit_card("1234567890123456") == "****-****-****-3456"

    def test_mask_bank_account(self):
        """계좌번호 마스킹"""
        masked = PIIMasker.mask_bank_account("123-456-789012")
        assert masked.startswith("123-")
        assert masked.endswith("-012")
        assert "***" in masked

    def test_mask_name(self):
        """이름 마스킹"""
        assert PIIMasker.mask_name("김철수") == "김**"
        assert PIIMasker.mask_name("John Doe") == "J*** D**"
        assert PIIMasker.mask_name("이") == "이"

    def test_mask_ip_address(self):
        """IP 주소 마스킹"""
        assert PIIMasker.mask_ip_address("192.168.1.100") == "192.168.***. ***"

    def test_mask_text(self):
        """텍스트 전체 마스킹"""
        text = "Contact user@example.com or call 010-1234-5678. SSN: 900101-1234567"
        masked = PIIMasker.mask_text(text)

        assert "u***@example.com" in masked
        assert "010-****-5678" in masked
        assert "900101-1******" in masked


class TestPIIHandler:
    """PIIHandler 테스트"""

    def test_sanitize_dict(self):
        """Dictionary PII 마스킹"""
        data = {
            "email": "user@example.com",
            "phone": "010-1234-5678",
            "name": "김철수",
            "age": 30,
        }

        sanitized = PIIHandler.sanitize_dict(data)

        assert sanitized["email"] == "u***@example.com"
        assert sanitized["phone"] == "010-****-5678"
        assert sanitized["name"] == "김**"
        assert sanitized["age"] == 30  # Non-PII field unchanged

    def test_sanitize_dict_with_custom_fields(self):
        """커스텀 필드 마스킹"""
        data = {
            "description": "Contact at user@example.com",
            "other": "No PII here",
        }

        sanitized = PIIHandler.sanitize_dict(data, fields_to_mask=["description"])

        assert "u***@example.com" in sanitized["description"]
        assert sanitized["other"] == "No PII here"

    def test_validate_no_pii_success(self):
        """PII 검증 - 성공"""
        text = "This is a safe text"
        assert PIIHandler.validate_no_pii(text) is True

    def test_validate_no_pii_failure(self):
        """PII 검증 - 실패"""
        text = "Email: user@example.com"
        assert PIIHandler.validate_no_pii(text) is False

    def test_validate_no_pii_raise_error(self):
        """PII 검증 - 예외 발생"""
        text = "Email: user@example.com"

        with pytest.raises(ValueError) as exc_info:
            PIIHandler.validate_no_pii(text, raise_error=True)

        assert "PII detected" in str(exc_info.value)


class TestEncryptionManager:
    """EncryptionManager 테스트"""

    def setup_method(self):
        """테스트 셋업"""
        self.manager = EncryptionManager(secret_key="test-secret-key-12345")

    def test_encrypt_decrypt(self):
        """암호화/복호화"""
        plaintext = "sensitive data"
        encrypted = self.manager.encrypt(plaintext)

        assert encrypted != plaintext
        assert len(encrypted) > 0

        decrypted = self.manager.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_empty_string(self):
        """빈 문자열 암호화"""
        encrypted = self.manager.encrypt("")
        assert encrypted == ""

    def test_decrypt_invalid_token(self):
        """잘못된 토큰 복호화"""
        with pytest.raises(ValueError) as exc_info:
            self.manager.decrypt("invalid_token_here")

        assert "Failed to decrypt" in str(exc_info.value)

    def test_encrypt_dict(self):
        """Dictionary 암호화"""
        data = {
            "ssn": "900101-1234567",
            "email": "user@example.com",
            "age": 30,
        }

        encrypted = self.manager.encrypt_dict(data, fields=["ssn"])

        assert encrypted["ssn"] != data["ssn"]
        assert encrypted["email"] == data["email"]  # Not encrypted
        assert encrypted["age"] == 30

    def test_decrypt_dict(self):
        """Dictionary 복호화"""
        data = {
            "ssn": "900101-1234567",
            "email": "user@example.com",
        }

        encrypted = self.manager.encrypt_dict(data, fields=["ssn"])
        decrypted = self.manager.decrypt_dict(encrypted, fields=["ssn"])

        assert decrypted["ssn"] == "900101-1234567"
        assert decrypted["email"] == "user@example.com"


class TestHashManager:
    """HashManager 테스트"""

    def test_hash_sha256(self):
        """SHA-256 해시"""
        text = "password123"
        hash1 = HashManager.hash_sha256(text)

        assert len(hash1) == 64  # SHA-256 produces 64 hex characters
        assert hash1 == HashManager.hash_sha256(text)  # Deterministic

    def test_hash_sha256_with_salt(self):
        """Salt를 사용한 SHA-256 해시"""
        text = "password123"
        hash_no_salt = HashManager.hash_sha256(text)
        hash_with_salt = HashManager.hash_sha256(text, salt="random_salt")

        assert hash_no_salt != hash_with_salt

    def test_hash_md5(self):
        """MD5 해시"""
        text = "test"
        hash1 = HashManager.hash_md5(text)

        assert len(hash1) == 32  # MD5 produces 32 hex characters

    def test_generate_token(self):
        """토큰 생성"""
        token1 = HashManager.generate_token(16)
        token2 = HashManager.generate_token(16)

        assert len(token1) == 32  # 16 bytes = 32 hex characters
        assert token1 != token2  # Random


class TestDataProtection:
    """Data Protection 유틸리티 테스트"""

    def test_mask_response_pii(self):
        """응답 데이터 PII 마스킹"""
        data = {
            "user": {
                "email": "user@example.com",
                "phone": "010-1234-5678",
                "age": 30,
            }
        }

        masked = mask_response_pii(data)

        assert masked["user"]["email"] == "u***@example.com"
        assert masked["user"]["phone"] == "010-****-5678"
        assert masked["user"]["age"] == 30

    def test_mask_response_pii_list(self):
        """리스트 응답 데이터 마스킹"""
        data = [
            {"email": "user1@example.com"},
            {"email": "user2@example.com"},
        ]

        masked = mask_response_pii(data)

        assert masked[0]["email"] == "u****@example.com"
        assert masked[1]["email"] == "u****@example.com"

    def test_redact_sensitive_fields(self):
        """민감 필드 Redaction"""
        data = {
            "email": "user@example.com",
            "password": "secret123",
            "access_token": "token_abc",
            "age": 30,
        }

        redacted = redact_sensitive_fields(data)

        assert redacted["email"] == "user@example.com"  # Not redacted
        assert redacted["password"] == "[REDACTED]"
        assert redacted["access_token"] == "[REDACTED]"
        assert redacted["age"] == 30

    def test_sanitize_for_storage(self):
        """저장용 데이터 정제"""
        data = {
            "ssn": "900101-1234567",
            "email": "user@example.com",
            "password": "secret123",
        }

        sanitized = sanitize_for_storage(data)

        # SSN should be encrypted
        assert sanitized["ssn"] != "900101-1234567"

        # Password should be redacted
        assert sanitized["password"] == "[REDACTED]"

    def test_sanitize_for_response(self):
        """응답용 데이터 정제"""
        data = {
            "email": "user@example.com",
            "phone": "010-1234-5678",
            "password": "secret123",
        }

        sanitized = sanitize_for_response(data)

        # Email and phone should be masked
        assert sanitized["email"] == "u***@example.com"
        assert sanitized["phone"] == "010-****-5678"

        # Password should be redacted
        assert sanitized["password"] == "[REDACTED]"


class TestDataAccessLogger:
    """DataAccessLogger 테스트"""

    def setup_method(self):
        """테스트 셋업"""
        DataAccessLogger.clear_logs()

    def test_log_access(self):
        """데이터 접근 로깅"""
        DataAccessLogger.log_access(
            user_id="user_123",
            action="read",
            resource_type="user",
            resource_id="user_456",
            pii_fields=["email", "phone"],
        )

        logs = DataAccessLogger.get_access_logs()

        assert len(logs) == 1
        assert logs[0]["user_id"] == "user_123"
        assert logs[0]["action"] == "read"
        assert logs[0]["resource_type"] == "user"
        assert logs[0]["pii_fields"] == ["email", "phone"]

    def test_get_access_logs_filter_by_user(self):
        """사용자별 접근 로그 필터링"""
        DataAccessLogger.log_access("user_1", "read", "document", "doc_1")
        DataAccessLogger.log_access("user_2", "read", "document", "doc_2")
        DataAccessLogger.log_access("user_1", "update", "document", "doc_1")

        logs = DataAccessLogger.get_access_logs(user_id="user_1")

        assert len(logs) == 2
        assert all(log["user_id"] == "user_1" for log in logs)

    def test_get_access_logs_filter_by_resource_type(self):
        """리소스 타입별 접근 로그 필터링"""
        DataAccessLogger.log_access("user_1", "read", "document", "doc_1")
        DataAccessLogger.log_access("user_1", "read", "user", "user_1")

        logs = DataAccessLogger.get_access_logs(resource_type="document")

        assert len(logs) == 1
        assert logs[0]["resource_type"] == "document"

    def test_get_access_logs_limit(self):
        """접근 로그 개수 제한"""
        for i in range(10):
            DataAccessLogger.log_access(f"user_{i}", "read", "document", f"doc_{i}")

        logs = DataAccessLogger.get_access_logs(limit=5)

        assert len(logs) == 5


class TestPIIValidator:
    """PIIValidator 테스트"""

    def test_validate_no_pii_in_query_success(self):
        """질의문 PII 검증 - 성공"""
        query = "급성심근경색증 보장 금액은?"
        valid, error = PIIValidator.validate_no_pii_in_query(query)

        assert valid is True
        assert error is None

    def test_validate_no_pii_in_query_failure(self):
        """질의문 PII 검증 - 실패"""
        query = "My email is user@example.com, can I get insurance?"
        valid, error = PIIValidator.validate_no_pii_in_query(query)

        assert valid is False
        assert "personal information" in error

    def test_validate_no_pii_in_document_name_success(self):
        """문서명 PII 검증 - 성공"""
        name = "Samsung Life Insurance Policy 2023"
        valid, error = PIIValidator.validate_no_pii_in_document_name(name)

        assert valid is True
        assert error is None

    def test_validate_no_pii_in_document_name_failure(self):
        """문서명 PII 검증 - 실패"""
        name = "Policy for user@example.com"
        valid, error = PIIValidator.validate_no_pii_in_document_name(name)

        assert valid is False
        assert "should not contain personal information" in error


class TestConvenienceFunctions:
    """편의 함수 테스트"""

    def test_mask_email_function(self):
        """mask_email 편의 함수"""
        assert mask_email("user@example.com") == "u***@example.com"

    def test_mask_phone_function(self):
        """mask_phone 편의 함수"""
        assert mask_phone("010-1234-5678") == "010-****-5678"

    def test_mask_ssn_function(self):
        """mask_ssn 편의 함수"""
        assert mask_ssn("900101-1234567") == "900101-1******"

    def test_detect_pii_function(self):
        """detect_pii 편의 함수"""
        text = "Email: user@example.com"
        detected = detect_pii(text)

        assert PIIType.EMAIL in detected

    def test_contains_pii_function(self):
        """contains_pii 편의 함수"""
        assert contains_pii("user@example.com") is True
        assert contains_pii("safe text") is False

    def test_sanitize_for_logging_string(self):
        """sanitize_for_logging 편의 함수 - 문자열"""
        text = "Contact: user@example.com, 010-1234-5678"
        sanitized = sanitize_for_logging(text)

        assert "u***@example.com" in sanitized
        assert "010-****-5678" in sanitized

    def test_sanitize_for_logging_dict(self):
        """sanitize_for_logging 편의 함수 - Dictionary"""
        data = {"email": "user@example.com", "age": 30}
        sanitized = sanitize_for_logging(data)

        assert sanitized["email"] == "u***@example.com"
        assert sanitized["age"] == 30

    def test_encrypt_decrypt_functions(self):
        """encrypt/decrypt 편의 함수"""
        plaintext = "sensitive data"
        encrypted = encrypt(plaintext)
        decrypted = decrypt(encrypted)

        assert encrypted != plaintext
        assert decrypted == plaintext

    def test_hash_sha256_function(self):
        """hash_sha256 편의 함수"""
        hash1 = hash_sha256("password")
        hash2 = hash_sha256("password")

        assert hash1 == hash2
        assert len(hash1) == 64

    def test_generate_token_function(self):
        """generate_token 편의 함수"""
        token1 = generate_token(16)
        token2 = generate_token(16)

        assert len(token1) == 32
        assert token1 != token2
