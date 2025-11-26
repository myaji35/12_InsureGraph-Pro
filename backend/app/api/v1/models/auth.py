"""
Authentication API Models

Story 3.3: Authentication & Authorization - 인증 API 모델
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole, UserStatus, UserPublic


# ============================================================================
# Request Models
# ============================================================================


class LoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr = Field(..., description="이메일")
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "fp@example.com",
                "password": "SecurePassword123!"
            }
        }


class RegisterRequest(BaseModel):
    """회원가입 요청"""
    email: EmailStr = Field(..., description="이메일")
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호")
    username: str = Field(..., min_length=2, max_length=50, description="사용자명")
    full_name: str = Field(..., min_length=2, max_length=100, description="전체 이름")
    phone: Optional[str] = Field(None, description="전화번호")
    organization_name: Optional[str] = Field(None, description="소속 조직명")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "username": "fp_park",
                "full_name": "박설계",
                "phone": "010-9876-5432",
                "organization_name": "삼성GA 서초지점"
            }
        }


class RefreshTokenRequest(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str = Field(..., description="Refresh token")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class ChangePasswordRequest(BaseModel):
    """비밀번호 변경 요청"""
    current_password: str = Field(..., description="현재 비밀번호")
    new_password: str = Field(..., min_length=8, max_length=100, description="새 비밀번호")

    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword456!"
            }
        }


class UpdateProfileRequest(BaseModel):
    """프로필 수정 요청"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None)
    profile_image_url: Optional[str] = Field(None)

    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "김설계",
                "phone": "010-1111-2222",
                "profile_image_url": "https://example.com/profile.jpg"
            }
        }


# ============================================================================
# Response Models
# ============================================================================


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str = Field(..., description="Access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer", description="토큰 타입")
    expires_in: int = Field(..., description="만료 시간 (초)")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiaWF0IjoxNTE2MjM5MDIyfQ.cThIIoDvwdueQB468K5xDc5633seEFoqwxjF_xSJyQQ",
                "token_type": "bearer",
                "expires_in": 900
            }
        }


class LoginResponse(BaseModel):
    """로그인 응답"""
    user: UserPublic = Field(..., description="사용자 정보")
    access_token: str = Field(..., description="Access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer", description="토큰 타입")
    expires_in: int = Field(..., description="만료 시간 (초)")

    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "fp@example.com",
                    "username": "fp_kim",
                    "full_name": "김설계",
                    "role": "fp",
                    "status": "active",
                    "organization_id": "987e6543-e21b-12d3-a456-426614174000",
                    "organization_name": "삼성GA 강남지점",
                    "phone": "010-1234-5678",
                    "profile_image_url": None,
                    "created_at": "2025-11-25T10:00:00",
                    "last_login_at": "2025-11-25T14:30:00",
                    "is_email_verified": True,
                },
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900
            }
        }


class RegisterResponse(BaseModel):
    """회원가입 응답"""
    user: UserPublic = Field(..., description="생성된 사용자 정보")
    message: str = Field(..., description="상태 메시지")

    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "newuser@example.com",
                    "username": "fp_park",
                    "full_name": "박설계",
                    "role": "fp",
                    "status": "pending",
                    "organization_id": None,
                    "organization_name": "삼성GA 서초지점",
                    "phone": "010-9876-5432",
                    "profile_image_url": None,
                    "created_at": "2025-11-25T10:00:00",
                    "last_login_at": None,
                    "is_email_verified": False,
                },
                "message": "Registration successful. Please wait for admin approval."
            }
        }


class LogoutResponse(BaseModel):
    """로그아웃 응답"""
    message: str = Field(..., description="상태 메시지")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Logged out successfully"
            }
        }


class MeResponse(BaseModel):
    """현재 사용자 정보 응답"""
    user: UserPublic = Field(..., description="사용자 정보")

    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "fp@example.com",
                    "username": "fp_kim",
                    "full_name": "김설계",
                    "role": "fp",
                    "status": "active",
                    "organization_id": "987e6543-e21b-12d3-a456-426614174000",
                    "organization_name": "삼성GA 강남지점",
                    "phone": "010-1234-5678",
                    "profile_image_url": None,
                    "created_at": "2025-11-25T10:00:00",
                    "last_login_at": "2025-11-25T14:30:00",
                    "is_email_verified": True,
                }
            }
        }


# ============================================================================
# Error Models
# ============================================================================


class AuthErrorResponse(BaseModel):
    """인증 에러 응답"""
    error_code: str = Field(..., description="에러 코드")
    error_message: str = Field(..., description="에러 메시지")
    timestamp: datetime = Field(default_factory=datetime.now, description="에러 발생 시각")

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "INVALID_CREDENTIALS",
                "error_message": "Invalid email or password",
                "timestamp": "2025-11-25T10:30:00"
            }
        }
