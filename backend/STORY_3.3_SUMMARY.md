# Story 3.3: Authentication & Authorization - 구현 완료

**Story ID**: 3.3
**Story Name**: Authentication & Authorization
**Story Points**: 5
**Status**: ✅ Completed
**Epic**: Epic 3 - API & Service Layer

---

## 📋 Story 개요

### 목표
JWT 기반 인증/인가 시스템을 구축하여 API 보안을 강화합니다.

### 주요 기능
1. **POST /api/v1/auth/register**: 회원가입
2. **POST /api/v1/auth/login**: 로그인
3. **POST /api/v1/auth/refresh**: 토큰 갱신
4. **POST /api/v1/auth/logout**: 로그아웃
5. **GET /api/v1/auth/me**: 현재 사용자 정보 조회
6. **PATCH /api/v1/auth/me**: 프로필 수정
7. **POST /api/v1/auth/change-password**: 비밀번호 변경
8. **역할 기반 권한 관리 (RBAC)**: Admin, FP Manager, FP, User

### 보안 기능
- JWT Access Token (15분 만료)
- JWT Refresh Token (1일 만료)
- bcrypt 비밀번호 해싱
- Token rotation (갱신 시 새 refresh token 발급)
- 역할 기반 접근 제어

---

## 🏗️ 아키텍처

### 인증 플로우

```
Client
  ↓ POST /api/v1/auth/register
  │ {email, password, username, full_name}
  ↓
Auth API
  ↓ 1. Check email uniqueness
  ↓ 2. Hash password (bcrypt)
  ↓ 3. Create user (status: pending)
  ↓
Client
  ← HTTP 201 Created
  │ {user, message: "Pending approval"}

  ↓ (Admin approves)
  ↓ PATCH /api/v1/auth/users/{id}/approve
  ↓
  ↓ POST /api/v1/auth/login
  │ {email, password}
  ↓
Auth API
  ↓ 1. Verify email exists
  ↓ 2. Verify password (bcrypt)
  ↓ 3. Check user status (active/pending/suspended)
  ↓ 4. Create access token (JWT, 15min)
  ↓ 5. Create refresh token (JWT, 1day)
  ↓ 6. Update last_login_at
  ↓
Client
  ← HTTP 200 OK
  │ {user, access_token, refresh_token}

  ↓ (Use API with access token)
  ↓ GET /api/v1/query
  ↓ Headers: Authorization: Bearer {access_token}
  ↓
API
  ↓ Middleware: get_current_user
  ↓ - Decode JWT
  ↓ - Verify token type (access)
  ↓ - Extract user info
  ↓
  ↓ (Access token expired)
  ↓ POST /api/v1/auth/refresh
  │ {refresh_token}
  ↓
Auth API
  ↓ 1. Decode refresh token
  ↓ 2. Verify token type (refresh)
  ↓ 3. Check if revoked
  ↓ 4. Create new tokens
  ↓ 5. Revoke old refresh token
  ↓
Client
  ← HTTP 200 OK
  │ {access_token, refresh_token}
```

### 역할 기반 권한

```
UserRole
├─ ADMIN (관리자)
│  └─ 모든 권한
│     - 사용자 승인/관리
│     - 시스템 설정
│     - 모든 문서/질의 접근
│
├─ FP_MANAGER (GA 지점장)
│  └─ 지점 관리 권한
│     - 소속 FP 관리
│     - 지점 통계 조회
│     - 소속 FP 데이터 접근
│
├─ FP (보험설계사)
│  └─ 본인 데이터만 접근
│     - 본인 문서 업로드/조회
│     - 본인 질의 실행/조회
│     - 프로필 관리
│
└─ USER (일반 사용자)
   └─ 제한된 조회 권한
      - 공개 문서 조회
      - 제한된 질의 실행
```

---

## 📁 구현 파일

### 1. User Model (`app/models/user.py` - 165 lines)

**주요 모델**:

```python
class UserRole(str, Enum):
    ADMIN = "admin"
    FP_MANAGER = "fp_manager"
    FP = "fp"
    USER = "user"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class User(BaseModel):
    user_id: UUID
    email: EmailStr
    username: str
    full_name: str
    hashed_password: str
    role: UserRole
    status: UserStatus
    organization_id: Optional[UUID]
    organization_name: Optional[str]
    phone: Optional[str]
    profile_image_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    is_email_verified: bool
    is_active: bool

class UserPublic(BaseModel):
    # Same as User but without hashed_password
    ...

def user_to_public(user: User) -> UserPublic:
    # Convert User to UserPublic (remove sensitive data)
    ...
```

### 2. Auth API Models (`app/api/v1/models/auth.py` - 265 lines)

```python
# Request Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: str
    full_name: str
    phone: Optional[str]
    organization_name: Optional[str]

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str]
    phone: Optional[str]
    profile_image_url: Optional[str]

# Response Models
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class LoginResponse(BaseModel):
    user: UserPublic
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class RegisterResponse(BaseModel):
    user: UserPublic
    message: str

class LogoutResponse(BaseModel):
    message: str

class MeResponse(BaseModel):
    user: UserPublic

class AuthErrorResponse(BaseModel):
    error_code: str
    error_message: str
    timestamp: datetime
```

### 3. Security Utilities (`app/core/security.py` - 157 lines)

**이미 구현되어 있음**:

```python
# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT tokens
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    # Creates JWT access token (15min expiry)
    ...

def create_refresh_token(data: Dict[str, Any]) -> str:
    # Creates JWT refresh token (1day expiry)
    ...

def decode_token(token: str) -> Dict[str, Any]:
    # Decodes and verifies JWT token
    ...

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    # Extract user from JWT token
    ...

# Authorization dependency factory
def require_role(required_roles: list[str]):
    # Role-based access control
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if current_user.get("role") not in required_roles:
            raise HTTPException(status_code=403, detail="Access denied")
        return current_user
    return role_checker
```

### 4. Auth Endpoints (`app/api/v1/endpoints/auth.py` - 610 lines)

**POST /api/v1/auth/register**:
```python
@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(request: RegisterRequest) -> RegisterResponse:
    # 1. Check email uniqueness
    if request.email in _users_by_email:
        raise HTTPException(400, detail="EMAIL_ALREADY_EXISTS")

    # 2. Create user
    user = User(
        email=request.email,
        username=request.username,
        full_name=request.full_name,
        hashed_password=hash_password(request.password),
        role=UserRole.FP,
        status=UserStatus.PENDING,  # Requires approval
        ...
    )

    # 3. Store user
    _users[user.user_id] = user

    return RegisterResponse(user=user_to_public(user), message="Pending approval")
```

**POST /api/v1/auth/login**:
```python
@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    # 1. Get user by email
    user = get_user_by_email(request.email)
    if not user:
        raise HTTPException(401, detail="INVALID_CREDENTIALS")

    # 2. Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(401, detail="INVALID_CREDENTIALS")

    # 3. Check status
    if user.status == UserStatus.PENDING:
        raise HTTPException(403, detail="ACCOUNT_PENDING")
    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(403, detail="ACCOUNT_INACTIVE")

    # 4. Create tokens
    token_data = {"sub": str(user.user_id), "email": user.email, "role": user.role.value}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.user_id)})

    # 5. Store refresh token
    _refresh_tokens[refresh_token] = user.user_id

    # 6. Update last login
    user.last_login_at = datetime.now()

    return LoginResponse(
        user=user_to_public(user),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
```

**POST /api/v1/auth/refresh**:
```python
@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshTokenRequest) -> TokenResponse:
    # 1. Decode refresh token
    payload = decode_token(request.refresh_token)

    # 2. Verify token type
    if payload.get("type") != "refresh":
        raise HTTPException(401, detail="INVALID_TOKEN_TYPE")

    # 3. Check if revoked
    if request.refresh_token not in _refresh_tokens:
        raise HTTPException(401, detail="REFRESH_TOKEN_REVOKED")

    # 4. Create new tokens
    user_id = UUID(payload.get("sub"))
    user = get_user_by_id(user_id)

    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token({"sub": str(user.user_id)})

    # 5. Token rotation: Revoke old, store new
    del _refresh_tokens[request.refresh_token]
    _refresh_tokens[new_refresh_token] = user.user_id

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
```

**GET /api/v1/auth/me**:
```python
@router.get("/me", response_model=MeResponse)
async def get_me(current_user: dict = Depends(get_current_user)) -> MeResponse:
    # Get user from token
    user_id = UUID(current_user.get("sub"))
    user = get_user_by_id(user_id)

    if not user:
        raise HTTPException(401, detail="USER_NOT_FOUND")

    return MeResponse(user=user_to_public(user))
```

**기타 엔드포인트**:
- `POST /logout`: Refresh token 무효화
- `PATCH /me`: 프로필 수정
- `POST /change-password`: 비밀번호 변경
- `GET /users`: 사용자 목록 (Admin)
- `PATCH /users/{id}/approve`: 사용자 승인 (Admin)

### 5. Tests (`tests/test_api_auth.py` - 550 lines)

**테스트 구조**:
```python
# 1. POST /api/v1/auth/register (5 tests)
class TestRegister:
    test_register_success
    test_register_minimal_fields
    test_register_duplicate_email
    test_register_invalid_email
    test_register_short_password

# 2. POST /api/v1/auth/login (4 tests)
class TestLogin:
    test_login_admin_success
    test_login_invalid_email
    test_login_invalid_password
    test_login_pending_user

# 3. POST /api/v1/auth/refresh (3 tests)
class TestRefreshToken:
    test_refresh_success
    test_refresh_invalid_token
    test_refresh_with_access_token

# 4. POST /api/v1/auth/logout (1 test)
class TestLogout:
    test_logout_success

# 5. GET /api/v1/auth/me (3 tests)
class TestGetMe:
    test_get_me_success
    test_get_me_no_token
    test_get_me_invalid_token

# 6. PATCH /api/v1/auth/me (2 tests)
class TestUpdateProfile:
    test_update_profile_success
    test_update_profile_partial

# 7. POST /api/v1/auth/change-password (2 tests)
class TestChangePassword:
    test_change_password_success
    test_change_password_wrong_current

# 8. Integration (1 test)
class TestAuthIntegration:
    test_full_auth_flow  # Full lifecycle test
```

---

## 🔑 핵심 구현 내용

### 1. JWT 토큰 관리

**Access Token** (짧은 수명):
```
{
  "sub": "user_id",
  "email": "user@example.com",
  "role": "fp",
  "exp": 1640000000,
  "type": "access"
}
```
- 수명: 15분
- 용도: API 인증
- 헤더: `Authorization: Bearer {token}`

**Refresh Token** (긴 수명):
```
{
  "sub": "user_id",
  "exp": 1640086400,
  "type": "refresh"
}
```
- 수명: 1일
- 용도: Access token 갱신
- Token rotation: 갱신 시 새 refresh token 발급

### 2. 비밀번호 보안

**bcrypt 해싱**:
```python
# 해싱
hashed = hash_password("MyPassword123!")
# Result: $2b$12$xxxxxxxxxxxxxxxxxxxxx

# 검증
is_valid = verify_password("MyPassword123!", hashed)
# Result: True
```

**비밀번호 요구사항**:
- 최소 8자
- API 검증에서 강제
- 프로덕션에서는 더 강한 요구사항 추천 (대소문자, 숫자, 특수문자)

### 3. 역할 기반 접근 제어 (RBAC)

**역할 체크 데코레이터**:
```python
from app.core.security import require_role

@router.get("/admin-only", dependencies=[Depends(require_role(["admin"]))])
async def admin_endpoint():
    # Only accessible by admin
    ...

@router.get("/fp-or-admin", dependencies=[Depends(require_role(["fp", "admin"]))])
async def fp_endpoint():
    # Accessible by FP or Admin
    ...
```

**사용자 상태 관리**:
- `PENDING`: 관리자 승인 대기
- `ACTIVE`: 활성 (로그인 가능)
- `INACTIVE`: 비활성
- `SUSPENDED`: 정지 (로그인 불가)

### 4. 보안 모범 사례

✅ **구현된 사항**:
- JWT 토큰 (stateless authentication)
- bcrypt 비밀번호 해싱
- Token rotation (refresh token)
- Token type 검증 (access vs refresh)
- 역할 기반 접근 제어

🔜 **프로덕션 준비사항**:
- Rate limiting (로그인 시도 제한)
- HTTPS only
- CSRF protection
- Token blacklist (Redis)
- 이메일 인증
- 2FA (Two-Factor Authentication)
- 비밀번호 복잡도 요구사항 강화

---

## 📊 API 사용 예시

### 1. 회원가입

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "fp@example.com",
    "password": "SecurePassword123!",
    "username": "fp_kim",
    "full_name": "김설계",
    "phone": "010-1234-5678",
    "organization_name": "삼성GA 강남지점"
  }'
```

**응답**:
```json
{
  "user": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "fp@example.com",
    "username": "fp_kim",
    "full_name": "김설계",
    "role": "fp",
    "status": "pending",
    ...
  },
  "message": "Registration successful. Please wait for admin approval."
}
```

### 2. 로그인

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@insuregraph.com",
    "password": "Admin123!"
  }'
```

**응답**:
```json
{
  "user": {
    "user_id": "...",
    "email": "admin@insuregraph.com",
    "role": "admin",
    "status": "active",
    ...
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 3. API 사용 (인증 필요)

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 4. 토큰 갱신

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**응답**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",  // 새 토큰
  "token_type": "bearer",
  "expires_in": 900
}
```

---

## 🎯 검증 및 품질 보증

### 1. 인증 테스트
✅ **21개 테스트 구현**
- Register: 5 tests
- Login: 4 tests
- Refresh: 3 tests
- Logout: 1 test
- Get Me: 3 tests
- Update Profile: 2 tests
- Change Password: 2 tests
- Integration: 1 test

### 2. 보안 검증
✅ **구현된 검증**
- 비밀번호 해싱 (bcrypt)
- JWT 서명 검증
- Token type 검증
- Token expiration 체크
- 역할 기반 접근 제어

### 3. 에러 처리
✅ **표준화된 에러 응답**
```
INVALID_CREDENTIALS        - 잘못된 이메일/비밀번호
EMAIL_ALREADY_EXISTS       - 이메일 중복
ACCOUNT_PENDING            - 승인 대기
ACCOUNT_INACTIVE           - 계정 비활성화
INVALID_REFRESH_TOKEN      - 유효하지 않은 refresh token
REFRESH_TOKEN_REVOKED      - 무효화된 refresh token
USER_NOT_FOUND             - 사용자 없음
INVALID_PASSWORD           - 잘못된 현재 비밀번호
```

---

## 🚀 다음 단계

### Story 3.4: Rate Limiting & Monitoring (3 points)
```
- Rate limiting (IP/User based)
- Request logging
- Performance metrics
- Error tracking
- Health monitoring
```

### Story 3.5: API Documentation (3 points)
```
- OpenAPI/Swagger enhancement
- API usage guide
- Authentication guide
- Best practices documentation
```

### 기존 API에 인증 적용 (선택적)
```python
# Query API
@router.post("/query", dependencies=[Depends(get_current_user)])
async def execute_query(...):
    # Authenticated users only
    ...

# Document API
@router.post("/documents/upload", dependencies=[Depends(require_role(["fp", "admin"]))])
async def upload_document(...):
    # FP or Admin only
    ...
```

---

## 📝 결론

### 구현 완료 사항
✅ **User Model** (165 lines)
  - User, UserPublic 모델
  - UserRole, UserStatus Enum
  - Helper functions

✅ **Auth API Models** (265 lines)
  - 5개 Request 모델
  - 6개 Response 모델
  - Error 모델

✅ **Security Utilities** (157 lines - 기존)
  - Password hashing
  - JWT token creation/verification
  - Authentication/Authorization dependencies

✅ **Auth Endpoints** (610 lines)
  - POST /auth/register
  - POST /auth/login
  - POST /auth/refresh
  - POST /auth/logout
  - GET /auth/me
  - PATCH /auth/me
  - POST /auth/change-password
  - Admin endpoints

✅ **Comprehensive Tests** (550 lines, 21 tests)

### Story Points 달성
- **추정**: 5 points
- **실제**: 5 points
- **상태**: ✅ **COMPLETED**

### Epic 3 진행 상황
```
Epic 3: API & Service Layer
├─ Story 3.1: Query API Endpoints (5 pts) ✅
├─ Story 3.2: Document Upload API (5 pts) ✅
├─ Story 3.3: Authentication & Authorization (5 pts) ✅
├─ Story 3.4: Rate Limiting & Monitoring (3 pts) ⏳ Next
└─ Story 3.5: API Documentation (3 pts) ⏳

Progress: 15/21 points (71% complete)
```

### 주요 성과
1. **완전한 JWT 인증 시스템**: Access/Refresh token
2. **역할 기반 권한 관리**: Admin, FP Manager, FP, User
3. **보안 모범 사례**: bcrypt, token rotation
4. **사용자 라이프사이클 관리**: Register → Approval → Active
5. **프로덕션 준비 구조**: 확장 가능한 인증 시스템

---

## 📚 참고 자료

### 생성된 파일
1. `app/models/user.py` (165 lines)
2. `app/api/v1/models/auth.py` (265 lines)
3. `app/api/v1/endpoints/auth.py` (610 lines)
4. `app/core/security.py` (157 lines - 기존)
5. `app/api/v1/models/__init__.py` (updated)
6. `app/api/v1/router.py` (updated)
7. `tests/test_api_auth.py` (550 lines)

### 기본 계정
- **Email**: admin@insuregraph.com
- **Password**: Admin123!
- **Role**: Admin

### 테스트 실행
```bash
# 모든 Auth 테스트
pytest tests/test_api_auth.py -v

# 특정 테스트
pytest tests/test_api_auth.py::TestLogin::test_login_admin_success -v

# Coverage
pytest tests/test_api_auth.py --cov=app.api.v1.endpoints.auth
```

---

**작성일**: 2025-11-25
**작성자**: Claude (AI Assistant)
**Epic**: Epic 3 - API & Service Layer
**Status**: ✅ Completed - Story 3.3 Done! 🎉
