"""
Data Encryption Utilities

민감 데이터 암호화/복호화 유틸리티 (AES-256, Fernet)
"""

import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend

from app.core.config import settings


class EncryptionManager:
    """
    암호화 관리 클래스

    Fernet (symmetric encryption)을 사용하여 데이터를 암호화/복호화합니다.
    """

    def __init__(self, secret_key: Optional[str] = None):
        """
        Args:
            secret_key: 암호화 키 (None이면 settings에서 가져옴)
        """
        self.secret_key = secret_key or settings.SECRET_KEY
        self._fernet = None

    def _get_fernet(self) -> Fernet:
        """Fernet 인스턴스를 생성하거나 반환합니다."""
        if self._fernet is None:
            # Secret key를 Fernet 키로 변환
            key = self._derive_key(self.secret_key)
            self._fernet = Fernet(key)
        return self._fernet

    @staticmethod
    def _derive_key(password: str, salt: Optional[bytes] = None) -> bytes:
        """
        비밀번호에서 Fernet 호환 키를 생성합니다.

        Args:
            password: 비밀번호
            salt: Salt (None이면 고정 salt 사용)

        Returns:
            bytes: Fernet 키 (32 bytes, base64 encoded)
        """
        if salt is None:
            # 고정 salt (production에서는 환경변수로 관리)
            salt = b"insuregraph_pro_2025"

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, plaintext: str) -> str:
        """
        문자열을 암호화합니다.

        Args:
            plaintext: 평문

        Returns:
            str: 암호화된 문자열 (base64 encoded)
        """
        if not plaintext:
            return plaintext

        fernet = self._get_fernet()
        encrypted_bytes = fernet.encrypt(plaintext.encode())
        return encrypted_bytes.decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        암호화된 문자열을 복호화합니다.

        Args:
            ciphertext: 암호문

        Returns:
            str: 복호화된 평문

        Raises:
            InvalidToken: 복호화 실패 시
        """
        if not ciphertext:
            return ciphertext

        try:
            fernet = self._get_fernet()
            decrypted_bytes = fernet.decrypt(ciphertext.encode())
            return decrypted_bytes.decode()
        except InvalidToken:
            raise ValueError("Failed to decrypt: Invalid token or corrupted data")

    def encrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """
        Dictionary의 특정 필드를 암호화합니다.

        Args:
            data: 원본 데이터
            fields: 암호화할 필드 리스트

        Returns:
            dict: 암호화된 데이터
        """
        encrypted_data = data.copy()

        for field in fields:
            if field in encrypted_data and encrypted_data[field]:
                if isinstance(encrypted_data[field], str):
                    encrypted_data[field] = self.encrypt(encrypted_data[field])

        return encrypted_data

    def decrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """
        Dictionary의 특정 필드를 복호화합니다.

        Args:
            data: 암호화된 데이터
            fields: 복호화할 필드 리스트

        Returns:
            dict: 복호화된 데이터
        """
        decrypted_data = data.copy()

        for field in fields:
            if field in decrypted_data and decrypted_data[field]:
                if isinstance(decrypted_data[field], str):
                    try:
                        decrypted_data[field] = self.decrypt(decrypted_data[field])
                    except ValueError:
                        # 복호화 실패 시 원본 유지 (암호화되지 않은 데이터일 수 있음)
                        pass

        return decrypted_data


class HashManager:
    """
    해시 관리 클래스

    일방향 해시 생성 (비밀번호 제외, bcrypt 사용)
    """

    @staticmethod
    def hash_sha256(text: str, salt: Optional[str] = None) -> str:
        """
        SHA-256 해시 생성

        Args:
            text: 해시할 텍스트
            salt: Salt (선택)

        Returns:
            str: 해시값 (hex)
        """
        if salt:
            text = f"{text}{salt}"

        hash_obj = hashlib.sha256(text.encode())
        return hash_obj.hexdigest()

    @staticmethod
    def hash_md5(text: str) -> str:
        """
        MD5 해시 생성 (비보안 용도, ID 생성 등)

        Args:
            text: 해시할 텍스트

        Returns:
            str: 해시값 (hex)
        """
        hash_obj = hashlib.md5(text.encode())
        return hash_obj.hexdigest()

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        무작위 토큰 생성

        Args:
            length: 토큰 길이 (bytes)

        Returns:
            str: 토큰 (hex)
        """
        import secrets
        return secrets.token_hex(length)


# Global instance
_encryption_manager = EncryptionManager()


# Convenience functions
def encrypt(plaintext: str) -> str:
    """문자열 암호화 (편의 함수)"""
    return _encryption_manager.encrypt(plaintext)


def decrypt(ciphertext: str) -> str:
    """문자열 복호화 (편의 함수)"""
    return _encryption_manager.decrypt(ciphertext)


def encrypt_field(data: dict, field: str) -> dict:
    """Dictionary의 단일 필드 암호화 (편의 함수)"""
    return _encryption_manager.encrypt_dict(data, [field])


def decrypt_field(data: dict, field: str) -> dict:
    """Dictionary의 단일 필드 복호화 (편의 함수)"""
    return _encryption_manager.decrypt_dict(data, [field])


def hash_sha256(text: str, salt: Optional[str] = None) -> str:
    """SHA-256 해시 (편의 함수)"""
    return HashManager.hash_sha256(text, salt)


def generate_token(length: int = 32) -> str:
    """무작위 토큰 생성 (편의 함수)"""
    return HashManager.generate_token(length)
