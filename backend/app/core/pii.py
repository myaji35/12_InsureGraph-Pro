"""
PII (Personally Identifiable Information) Detection and Masking

금융권 개인정보 보호 및 GDPR 준수를 위한 PII 감지, 마스킹, 비식별화 유틸리티
"""

import re
from typing import Any, Dict, Optional, Union
from enum import Enum


class PIIType(str, Enum):
    """PII 타입 분류"""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"  # Social Security Number (주민등록번호)
    CREDIT_CARD = "credit_card"
    BANK_ACCOUNT = "bank_account"
    ADDRESS = "address"
    NAME = "name"
    IP_ADDRESS = "ip_address"


class PIIDetector:
    """
    PII 자동 감지 클래스

    정규표현식을 사용하여 텍스트 내 PII를 감지합니다.
    """

    # 정규표현식 패턴
    PATTERNS = {
        PIIType.EMAIL: r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        PIIType.PHONE: r"(?:010|011|016|017|018|019)[-\s]?\d{3,4}[-\s]?\d{4}",
        PIIType.SSN: r"\d{6}[-\s]?[1-4]\d{6}",  # 주민등록번호 (YYMMDD-NNNNNNN)
        PIIType.CREDIT_CARD: r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        PIIType.BANK_ACCOUNT: r"\b\d{3,6}[-\s]?\d{2,6}[-\s]?\d{4,8}\b",
        PIIType.IP_ADDRESS: r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    }

    @classmethod
    def detect(cls, text: str) -> Dict[PIIType, list[str]]:
        """
        텍스트에서 PII를 감지합니다.

        Args:
            text: 검사할 텍스트

        Returns:
            Dict[PIIType, list[str]]: 감지된 PII 타입별 값 리스트
        """
        if not text:
            return {}

        detected = {}

        for pii_type, pattern in cls.PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                detected[pii_type] = matches

        return detected

    @classmethod
    def contains_pii(cls, text: str) -> bool:
        """
        텍스트에 PII가 포함되어 있는지 확인합니다.

        Args:
            text: 검사할 텍스트

        Returns:
            bool: PII 포함 여부
        """
        detected = cls.detect(text)
        return len(detected) > 0


class PIIMasker:
    """
    PII 마스킹 클래스

    개인정보를 부분적으로 가려 보호합니다.
    """

    @staticmethod
    def mask_email(email: str) -> str:
        """
        이메일 마스킹: user@example.com → u***@example.com

        Args:
            email: 이메일 주소

        Returns:
            str: 마스킹된 이메일
        """
        if not email or "@" not in email:
            return email

        local, domain = email.split("@", 1)

        if len(local) <= 1:
            masked_local = local
        elif len(local) <= 3:
            masked_local = local[0] + "*" * (len(local) - 1)
        else:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]

        return f"{masked_local}@{domain}"

    @staticmethod
    def mask_phone(phone: str) -> str:
        """
        전화번호 마스킹: 010-1234-5678 → 010-****-5678

        Args:
            phone: 전화번호

        Returns:
            str: 마스킹된 전화번호
        """
        if not phone:
            return phone

        # 숫자만 추출
        digits = re.sub(r"\D", "", phone)

        if len(digits) < 8:
            return phone

        # 010-XXXX-1234 형태로 마스킹
        if len(digits) == 10:
            return f"{digits[:3]}-****-{digits[-4:]}"
        elif len(digits) == 11:
            return f"{digits[:3]}-****-{digits[-4:]}"
        else:
            # 일반 전화번호
            return f"{digits[:-4]}****"

    @staticmethod
    def mask_ssn(ssn: str) -> str:
        """
        주민등록번호 마스킹: 900101-1234567 → 900101-1******

        Args:
            ssn: 주민등록번호

        Returns:
            str: 마스킹된 주민등록번호
        """
        if not ssn:
            return ssn

        # 숫자만 추출
        digits = re.sub(r"\D", "", ssn)

        if len(digits) != 13:
            return ssn

        # 앞 6자리 + 뒷자리 첫 숫자 표시, 나머지 마스킹
        return f"{digits[:6]}-{digits[6]}******"

    @staticmethod
    def mask_credit_card(card: str) -> str:
        """
        신용카드 마스킹: 1234-5678-9012-3456 → ****-****-****-3456

        Args:
            card: 신용카드 번호

        Returns:
            str: 마스킹된 신용카드 번호
        """
        if not card:
            return card

        # 숫자만 추출
        digits = re.sub(r"\D", "", card)

        if len(digits) < 12:
            return card

        # 마지막 4자리만 표시
        return f"****-****-****-{digits[-4:]}"

    @staticmethod
    def mask_bank_account(account: str) -> str:
        """
        계좌번호 마스킹: 123-456-789012 → 123-456-***012

        Args:
            account: 계좌번호

        Returns:
            str: 마스킹된 계좌번호
        """
        if not account:
            return account

        # 숫자만 추출
        digits = re.sub(r"\D", "", account)

        if len(digits) < 6:
            return account

        # 앞 3자리, 뒤 3자리 표시, 중간 마스킹
        masked_middle = "*" * max(0, len(digits) - 6)
        return f"{digits[:3]}-***-{masked_middle}{digits[-3:]}"

    @staticmethod
    def mask_name(name: str) -> str:
        """
        이름 마스킹: 김철수 → 김**, John Doe → J*** D**

        Args:
            name: 이름

        Returns:
            str: 마스킹된 이름
        """
        if not name:
            return name

        # 공백으로 구분 (영문 이름 대응)
        parts = name.split()

        masked_parts = []
        for part in parts:
            if len(part) <= 1:
                masked_parts.append(part)
            elif len(part) == 2:
                masked_parts.append(part[0] + "*")
            else:
                masked_parts.append(part[0] + "*" * (len(part) - 1))

        return " ".join(masked_parts)

    @staticmethod
    def mask_ip_address(ip: str) -> str:
        """
        IP 주소 마스킹: 192.168.1.100 → 192.168.***.***

        Args:
            ip: IP 주소

        Returns:
            str: 마스킹된 IP 주소
        """
        if not ip:
            return ip

        parts = ip.split(".")

        if len(parts) != 4:
            return ip

        # 앞 2개 옥텟만 표시
        return f"{parts[0]}.{parts[1]}.***.***"

    @classmethod
    def mask_text(cls, text: str) -> str:
        """
        텍스트 내 모든 PII를 자동으로 마스킹합니다.

        Args:
            text: 원본 텍스트

        Returns:
            str: 마스킹된 텍스트
        """
        if not text:
            return text

        masked_text = text

        # 이메일 마스킹
        emails = re.findall(PIIDetector.PATTERNS[PIIType.EMAIL], text)
        for email in emails:
            masked_text = masked_text.replace(email, cls.mask_email(email))

        # 전화번호 마스킹
        phones = re.findall(PIIDetector.PATTERNS[PIIType.PHONE], text)
        for phone in phones:
            masked_text = masked_text.replace(phone, cls.mask_phone(phone))

        # 주민등록번호 마스킹
        ssns = re.findall(PIIDetector.PATTERNS[PIIType.SSN], text)
        for ssn in ssns:
            masked_text = masked_text.replace(ssn, cls.mask_ssn(ssn))

        # 신용카드 마스킹
        cards = re.findall(PIIDetector.PATTERNS[PIIType.CREDIT_CARD], text)
        for card in cards:
            masked_text = masked_text.replace(card, cls.mask_credit_card(card))

        # IP 주소 마스킹
        ips = re.findall(PIIDetector.PATTERNS[PIIType.IP_ADDRESS], text)
        for ip in ips:
            masked_text = masked_text.replace(ip, cls.mask_ip_address(ip))

        return masked_text


class PIIHandler:
    """
    PII 처리 통합 클래스

    감지, 마스킹, 필터링을 통합하여 제공합니다.
    """

    @staticmethod
    def sanitize_dict(data: Dict[str, Any], fields_to_mask: Optional[list[str]] = None) -> Dict[str, Any]:
        """
        Dictionary의 특정 필드를 마스킹합니다.

        Args:
            data: 원본 데이터
            fields_to_mask: 마스킹할 필드 리스트 (None이면 자동 감지)

        Returns:
            Dict[str, Any]: 마스킹된 데이터
        """
        if not data:
            return data

        # 기본 PII 필드
        default_pii_fields = {
            "email": PIIMasker.mask_email,
            "phone": PIIMasker.mask_phone,
            "ssn": PIIMasker.mask_ssn,
            "social_security_number": PIIMasker.mask_ssn,
            "credit_card": PIIMasker.mask_credit_card,
            "bank_account": PIIMasker.mask_bank_account,
            "full_name": PIIMasker.mask_name,
            "name": PIIMasker.mask_name,
            "ip_address": PIIMasker.mask_ip_address,
        }

        sanitized = data.copy()

        for field, value in sanitized.items():
            if not value:
                continue

            # 명시적으로 지정된 필드 마스킹
            if fields_to_mask and field in fields_to_mask:
                if isinstance(value, str):
                    sanitized[field] = PIIMasker.mask_text(value)
                continue

            # 자동 감지된 PII 필드 마스킹
            if field.lower() in default_pii_fields:
                masker_func = default_pii_fields[field.lower()]
                if isinstance(value, str):
                    sanitized[field] = masker_func(value)

        return sanitized

    @staticmethod
    def validate_no_pii(text: str, raise_error: bool = False) -> bool:
        """
        텍스트에 PII가 없는지 검증합니다.

        Args:
            text: 검사할 텍스트
            raise_error: True이면 PII 발견 시 예외 발생

        Returns:
            bool: PII가 없으면 True

        Raises:
            ValueError: raise_error=True이고 PII가 발견된 경우
        """
        has_pii = PIIDetector.contains_pii(text)

        if has_pii and raise_error:
            detected = PIIDetector.detect(text)
            pii_types = ", ".join([pii_type.value for pii_type in detected.keys()])
            raise ValueError(f"PII detected in text: {pii_types}")

        return not has_pii


# Convenience functions
def mask_email(email: str) -> str:
    """이메일 마스킹 (편의 함수)"""
    return PIIMasker.mask_email(email)


def mask_phone(phone: str) -> str:
    """전화번호 마스킹 (편의 함수)"""
    return PIIMasker.mask_phone(phone)


def mask_ssn(ssn: str) -> str:
    """주민등록번호 마스킹 (편의 함수)"""
    return PIIMasker.mask_ssn(ssn)


def detect_pii(text: str) -> Dict[PIIType, list[str]]:
    """PII 감지 (편의 함수)"""
    return PIIDetector.detect(text)


def contains_pii(text: str) -> bool:
    """PII 포함 여부 확인 (편의 함수)"""
    return PIIDetector.contains_pii(text)


def sanitize_for_logging(data: Union[str, Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
    """
    로깅용 데이터 정제 (PII 자동 마스킹)

    Args:
        data: 원본 데이터 (문자열 또는 딕셔너리)

    Returns:
        마스킹된 데이터
    """
    if isinstance(data, str):
        return PIIMasker.mask_text(data)
    elif isinstance(data, dict):
        return PIIHandler.sanitize_dict(data)
    else:
        return data
