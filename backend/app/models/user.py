"""
User Model

Story 3.3: Authentication & Authorization - 사용자 모델
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# Enums
# ============================================================================


class UserRole(str, Enum):
    """사용자 역할"""
    ADMIN = "admin"                    # 관리자 (모든 권한)
    FP_MANAGER = "fp_manager"          # GA 지점장 (지점 관리)
    FP = "fp"                          # 보험설계사 (본인 데이터만)
    USER = "user"                      # 일반 사용자 (제한된 조회)


class UserStatus(str, Enum):
    """사용자 상태"""
    ACTIVE = "active"                  # 활성
    INACTIVE = "inactive"              # 비활성
    SUSPENDED = "suspended"            # 정지
    PENDING = "pending"                # 승인 대기


# ============================================================================
# User Model
# ============================================================================


class User(BaseModel):
    """
    사용자 모델

    시스템 사용자 정보를 나타냅니다.
    """
    user_id: UUID = Field(..., description="사용자 ID")
    email: EmailStr = Field(..., description="이메일 (로그인 ID)")
    username: str = Field(..., min_length=2, max_length=50, description="사용자명")
    full_name: str = Field(..., min_length=2, max_length=100, description="전체 이름")

    # Authentication
    hashed_password: str = Field(..., description="해시된 비밀번호")

    # Role & Status
    role: UserRole = Field(default=UserRole.FP, description="사용자 역할")
    status: UserStatus = Field(default=UserStatus.PENDING, description="사용자 상태")

    # Organization (for FP/FP_MANAGER)
    organization_id: Optional[UUID] = Field(None, description="소속 조직 ID (GA)")
    organization_name: Optional[str] = Field(None, description="소속 조직명")

    # Profile
    phone: Optional[str] = Field(None, description="전화번호")
    profile_image_url: Optional[str] = Field(None, description="프로필 이미지 URL")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="생성일시")
    updated_at: datetime = Field(default_factory=datetime.now, description="수정일시")
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인")

    # Flags
    is_email_verified: bool = Field(default=False, description="이메일 인증 여부")
    is_active: bool = Field(default=True, description="활성 여부")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "fp@example.com",
                "username": "fp_kim",
                "full_name": "김설계",
                "hashed_password": "$2b$12$...",
                "role": "fp",
                "status": "active",
                "organization_id": "987e6543-e21b-12d3-a456-426614174000",
                "organization_name": "삼성GA 강남지점",
                "phone": "010-1234-5678",
                "profile_image_url": None,
                "created_at": "2025-11-25T10:00:00",
                "updated_at": "2025-11-25T10:00:00",
                "last_login_at": "2025-11-25T14:30:00",
                "is_email_verified": True,
                "is_active": True,
            }
        }


class UserInDB(User):
    """
    데이터베이스의 사용자 모델

    추가 필드를 포함할 수 있습니다.
    """
    pass


class UserPublic(BaseModel):
    """
    공개 사용자 정보 (비밀번호 제외)

    API 응답에 사용됩니다.
    """
    user_id: UUID
    email: EmailStr
    username: str
    full_name: str
    role: UserRole
    status: UserStatus
    organization_id: Optional[UUID]
    organization_name: Optional[str]
    phone: Optional[str]
    profile_image_url: Optional[str]
    created_at: datetime
    last_login_at: Optional[datetime]
    is_email_verified: bool

    class Config:
        json_schema_extra = {
            "example": {
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


# ============================================================================
# Helper Functions
# ============================================================================


def user_to_public(user: User) -> UserPublic:
    """
    User 모델을 UserPublic으로 변환

    비밀번호 등 민감한 정보를 제외합니다.
    """
    return UserPublic(
        user_id=user.user_id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        status=user.status,
        organization_id=user.organization_id,
        organization_name=user.organization_name,
        phone=user.phone,
        profile_image_url=user.profile_image_url,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        is_email_verified=user.is_email_verified,
    )
