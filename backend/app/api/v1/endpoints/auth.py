"""
Authentication API Endpoints

Story 3.3: Authentication & Authorization - 인증 엔드포인트
"""
from datetime import datetime, timedelta
from typing import Dict
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status, Depends
from loguru import logger

from app.api.v1.models.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    RefreshTokenRequest,
    TokenResponse,
    LogoutResponse,
    MeResponse,
    ChangePasswordRequest,
    UpdateProfileRequest,
    AuthErrorResponse,
)
from app.models.user import User, UserPublic, UserRole, UserStatus, user_to_public
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)
from app.core.config import settings


# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# In-Memory User Storage (Temporary - replace with database in production)
# ============================================================================

# Simulated user database
_users: Dict[UUID, User] = {}
_users_by_email: Dict[str, UUID] = {}

# Simulated refresh token storage (in production, use Redis)
_refresh_tokens: Dict[str, UUID] = {}  # token -> user_id


# ============================================================================
# Helper Functions
# ============================================================================


def create_default_admin():
    """
    기본 관리자 계정 생성

    In production: This should be done via migration/seeding
    """
    admin_id = uuid4()
    admin_email = "admin@insuregraph.com"

    if admin_email not in _users_by_email:
        admin = User(
            user_id=admin_id,
            email=admin_email,
            username="admin",
            full_name="System Admin",
            hashed_password=hash_password("Admin123!"),  # Change in production!
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_email_verified=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        _users[admin_id] = admin
        _users_by_email[admin_email] = admin_id
        logger.info(f"Default admin created: {admin_email}")


# Create default admin on module load
create_default_admin()


def get_user_by_email(email: str) -> User | None:
    """이메일로 사용자 조회"""
    user_id = _users_by_email.get(email)
    if user_id:
        return _users.get(user_id)
    return None


def get_user_by_id(user_id: UUID) -> User | None:
    """ID로 사용자 조회"""
    return _users.get(user_id)


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
    description="""
    새로운 사용자를 등록합니다.

    등록 후 관리자 승인이 필요합니다 (status: pending).
    """,
    responses={
        201: {"description": "회원가입 성공"},
        400: {"model": AuthErrorResponse, "description": "이메일 중복 또는 검증 실패"},
    },
)
async def register(request: RegisterRequest) -> RegisterResponse:
    """
    회원가입

    새로운 사용자를 등록합니다.
    """
    # 1. Check if email already exists
    if request.email in _users_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "EMAIL_ALREADY_EXISTS",
                "error_message": f"Email '{request.email}' is already registered",
            }
        )

    # 2. Create new user
    user_id = uuid4()
    now = datetime.now()

    new_user = User(
        user_id=user_id,
        email=request.email,
        username=request.username,
        full_name=request.full_name,
        hashed_password=hash_password(request.password),
        role=UserRole.FP,  # Default role
        status=UserStatus.PENDING,  # Requires admin approval
        organization_name=request.organization_name,
        phone=request.phone,
        is_active=True,
        is_email_verified=False,
        created_at=now,
        updated_at=now,
    )

    # 3. Store user
    _users[user_id] = new_user
    _users_by_email[request.email] = user_id

    logger.info(f"New user registered: {request.email} (ID: {user_id})")

    return RegisterResponse(
        user=user_to_public(new_user),
        message="Registration successful. Please wait for admin approval."
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="로그인",
    description="""
    이메일과 비밀번호로 로그인합니다.

    성공 시 access_token과 refresh_token을 반환합니다.
    """,
    responses={
        200: {"description": "로그인 성공"},
        401: {"model": AuthErrorResponse, "description": "인증 실패"},
        403: {"model": AuthErrorResponse, "description": "계정 비활성화"},
    },
)
async def login(request: LoginRequest) -> LoginResponse:
    """
    로그인

    이메일과 비밀번호로 인증합니다.
    """
    # 1. Get user by email
    user = get_user_by_email(request.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_CREDENTIALS",
                "error_message": "Invalid email or password",
            }
        )

    # 2. Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_CREDENTIALS",
                "error_message": "Invalid email or password",
            }
        )

    # 3. Check if user is active
    if not user.is_active or user.status == UserStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "ACCOUNT_INACTIVE",
                "error_message": "Your account is inactive or suspended",
            }
        )

    # 4. Check if user is pending approval
    if user.status == UserStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "ACCOUNT_PENDING",
                "error_message": "Your account is pending admin approval",
            }
        )

    # 5. Create tokens
    token_data = {
        "sub": str(user.user_id),
        "email": user.email,
        "role": user.role.value,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.user_id)})

    # 6. Store refresh token
    _refresh_tokens[refresh_token] = user.user_id

    # 7. Update last login
    user.last_login_at = datetime.now()
    user.updated_at = datetime.now()

    logger.info(f"User logged in: {user.email} (ID: {user.user_id})")

    return LoginResponse(
        user=user_to_public(user),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="토큰 갱신",
    description="""
    Refresh token을 사용하여 새로운 access token을 발급합니다.
    """,
    responses={
        200: {"description": "토큰 갱신 성공"},
        401: {"model": AuthErrorResponse, "description": "유효하지 않은 토큰"},
    },
)
async def refresh(request: RefreshTokenRequest) -> TokenResponse:
    """
    토큰 갱신

    Refresh token으로 새로운 access token을 발급합니다.
    """
    # 1. Decode refresh token
    try:
        payload = decode_token(request.refresh_token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_REFRESH_TOKEN",
                "error_message": "Invalid or expired refresh token",
            }
        )

    # 2. Verify token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_TOKEN_TYPE",
                "error_message": "Token is not a refresh token",
            }
        )

    # 3. Check if refresh token exists in storage
    if request.refresh_token not in _refresh_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "REFRESH_TOKEN_REVOKED",
                "error_message": "Refresh token has been revoked",
            }
        )

    # 4. Get user
    user_id = UUID(payload.get("sub"))
    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "USER_NOT_FOUND",
                "error_message": "User not found",
            }
        )

    # 5. Create new tokens
    token_data = {
        "sub": str(user.user_id),
        "email": user.email,
        "role": user.role.value,
    }

    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token({"sub": str(user.user_id)})

    # 6. Revoke old refresh token and store new one
    del _refresh_tokens[request.refresh_token]
    _refresh_tokens[new_refresh_token] = user.user_id

    logger.info(f"Token refreshed for user: {user.email}")

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="로그아웃",
    description="""
    현재 사용자의 refresh token을 무효화합니다.
    """,
)
async def logout(
    refresh_token: RefreshTokenRequest,
    current_user: dict = Depends(get_current_user)
) -> LogoutResponse:
    """
    로그아웃

    Refresh token을 무효화합니다.
    """
    # Revoke refresh token
    if refresh_token.refresh_token in _refresh_tokens:
        del _refresh_tokens[refresh_token.refresh_token]

    logger.info(f"User logged out: {current_user.get('email')}")

    return LogoutResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
    summary="현재 사용자 정보 조회",
    description="""
    현재 로그인한 사용자의 정보를 조회합니다.

    **Authentication**: Bearer token required
    """,
    responses={
        200: {"description": "사용자 정보 조회 성공"},
        401: {"model": AuthErrorResponse, "description": "인증 실패"},
    },
)
async def get_me(current_user: dict = Depends(get_current_user)) -> MeResponse:
    """
    현재 사용자 정보 조회

    JWT 토큰에서 사용자 정보를 가져옵니다.
    """
    # Get user from database
    user_id = UUID(current_user.get("sub"))
    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "USER_NOT_FOUND",
                "error_message": "User not found",
            }
        )

    return MeResponse(user=user_to_public(user))


@router.patch(
    "/me",
    response_model=UserPublic,
    status_code=status.HTTP_200_OK,
    summary="프로필 수정",
    description="""
    현재 사용자의 프로필 정보를 수정합니다.

    **Authentication**: Bearer token required
    """,
)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user)
) -> UserPublic:
    """
    프로필 수정
    """
    # Get user
    user_id = UUID(current_user.get("sub"))
    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "USER_NOT_FOUND",
                "error_message": "User not found",
            }
        )

    # Update fields
    if request.full_name is not None:
        user.full_name = request.full_name
    if request.phone is not None:
        user.phone = request.phone
    if request.profile_image_url is not None:
        user.profile_image_url = request.profile_image_url

    user.updated_at = datetime.now()

    logger.info(f"Profile updated for user: {user.email}")

    return user_to_public(user)


@router.post(
    "/change-password",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="비밀번호 변경",
    description="""
    현재 사용자의 비밀번호를 변경합니다.

    **Authentication**: Bearer token required
    """,
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
) -> LogoutResponse:
    """
    비밀번호 변경
    """
    # Get user
    user_id = UUID(current_user.get("sub"))
    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "USER_NOT_FOUND",
                "error_message": "User not found",
            }
        )

    # Verify current password
    if not verify_password(request.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_PASSWORD",
                "error_message": "Current password is incorrect",
            }
        )

    # Update password
    user.hashed_password = hash_password(request.new_password)
    user.updated_at = datetime.now()

    logger.info(f"Password changed for user: {user.email}")

    return LogoutResponse(message="Password changed successfully")


# ============================================================================
# Admin Endpoints (for testing/demo)
# ============================================================================


@router.get(
    "/users",
    response_model=list[UserPublic],
    status_code=status.HTTP_200_OK,
    summary="사용자 목록 조회 (Admin only)",
    description="""
    모든 사용자 목록을 조회합니다.

    **Authentication**: Bearer token required
    **Authorization**: Admin role required
    """,
)
async def list_users(
    current_user: dict = Depends(get_current_user)
) -> list[UserPublic]:
    """
    사용자 목록 조회 (Admin only)

    In production: Add role check (admin only)
    """
    # In production: Check if user is admin
    # if current_user.get("role") != "admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")

    users = list(_users.values())
    return [user_to_public(user) for user in users]


@router.patch(
    "/users/{user_id}/approve",
    response_model=UserPublic,
    status_code=status.HTTP_200_OK,
    summary="사용자 승인 (Admin only)",
    description="""
    Pending 상태의 사용자를 승인합니다.

    **Authentication**: Bearer token required
    **Authorization**: Admin role required
    """,
)
async def approve_user(
    user_id: UUID,
    current_user: dict = Depends(get_current_user)
) -> UserPublic:
    """
    사용자 승인 (Admin only)
    """
    # In production: Check if user is admin
    # if current_user.get("role") != "admin":
    #     raise HTTPException(status_code=403, detail="Admin access required")

    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "USER_NOT_FOUND",
                "error_message": "User not found",
            }
        )

    user.status = UserStatus.ACTIVE
    user.updated_at = datetime.now()

    logger.info(f"User approved: {user.email} (ID: {user_id})")

    return user_to_public(user)
