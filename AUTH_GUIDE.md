# InsureGraph Pro - 인증 가이드 (Authentication Guide)

## 🔐 개요

InsureGraph Pro는 JWT 기반 인증 시스템을 사용합니다. 대부분의 API 엔드포인트는 유효한 인증 토큰이 필요합니다.

---

## 🚀 빠른 시작: 로그인 방법

### 1. 프론트엔드 로그인 페이지 (권장)

**URL**: http://localhost:3001/simple-login

**기본 계정**:
- 이메일: `admin@insuregraph.com`
- 비밀번호: `Admin123!`

**로그인 절차**:
1. 브라우저에서 http://localhost:3001/simple-login 접속
2. 이메일과 비밀번호 입력
3. "로그인" 버튼 클릭
4. 성공 시 자동으로 대시보드로 이동
5. 토큰이 localStorage에 자동 저장됨

### 2. API 직접 호출 (테스트/개발용)

```bash
curl -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "admin@insuregraph.com",
    "password": "Admin123!"
  }'
```

**응답 예시**:
```json
{
  "user": {
    "user_id": "ded8cdcb-ff0c-4a3c-b95b-be435d9b711b",
    "email": "admin@insuregraph.com",
    "username": "admin",
    "full_name": "System Admin",
    "role": "admin",
    "status": "active"
  },
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

## 🔍 인증 토큰 확인

### 브라우저에서 확인

```javascript
// 개발자 도구 Console에서 실행
localStorage.getItem('access_token')
// 토큰이 있으면 로그인 상태
// null이면 로그인 필요
```

### 토큰 정보

- **access_token**: API 요청에 사용하는 주 토큰 (유효기간: 15분)
- **refresh_token**: access_token 갱신용 토큰 (유효기간: 1일)
- **token_type**: "bearer" (Authorization 헤더에 "Bearer {token}" 형식으로 사용)

---

## 📡 인증이 필요한 API 사용

### 프론트엔드에서 자동 인증

프론트엔드의 API 클라이언트는 자동으로 localStorage에서 토큰을 읽어 요청에 포함합니다:

```typescript
// frontend/src/lib/simple-query-api.ts
const token = localStorage.getItem('access_token')
const headers = {
  'Content-Type': 'application/json',
  ...(token ? { Authorization: `Bearer ${token}` } : {})
}
```

### curl로 인증 API 호출

```bash
# 1. 로그인하여 토큰 받기
TOKEN=$(curl -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@insuregraph.com","password":"Admin123!"}' \
  2>/dev/null | jq -r '.access_token')

# 2. 토큰을 사용하여 API 호출
curl -X POST 'http://localhost:8000/api/v1/query-simple/execute' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"question":"보험료는 얼마인가요?"}'
```

---

## 🚨 자주 발생하는 인증 에러

### 1. 401 Unauthorized - "Not authenticated"

**증상**:
```
POST http://localhost:8000/api/v1/query-simple/execute 401 (Unauthorized)
Failed to submit question: Error: Not authenticated
```

**원인**:
- localStorage에 인증 토큰이 없음 (로그인하지 않음)
- 토큰이 만료됨 (15분 경과)
- 잘못된 토큰

**해결**:
1. http://localhost:3001/simple-login 페이지로 이동
2. `admin@insuregraph.com` / `Admin123!` 로 로그인
3. 로그인 성공 후 API 재시도

### 2. 403 Forbidden - "Account pending/inactive"

**증상**:
```
403 Forbidden
Your account is pending admin approval
```

**원인**:
- 신규 가입 계정이 관리자 승인 대기 중 (status: pending)
- 계정이 비활성화됨 (status: suspended)

**해결**:
- 기본 관리자 계정(`admin@insuregraph.com`)은 즉시 사용 가능
- 신규 계정은 관리자 승인 필요

### 3. 토큰 만료 (Token expired)

**증상**:
```
401 Unauthorized
Token has expired
```

**원인**: access_token 유효기간 만료 (15분)

**해결**:
1. **자동 갱신** (프론트엔드에서 구현 필요):
   ```bash
   curl -X POST 'http://localhost:8000/api/v1/auth/refresh' \
     -H 'Content-Type: application/json' \
     -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'
   ```

2. **재로그인**:
   - 간단한 방법: 다시 로그인

---

## 🔄 토큰 갱신 (Token Refresh)

### access_token 갱신

```bash
curl -X POST 'http://localhost:8000/api/v1/auth/refresh' \
  -H 'Content-Type: application/json' \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

**응답**:
```json
{
  "access_token": "NEW_ACCESS_TOKEN",
  "refresh_token": "NEW_REFRESH_TOKEN",
  "token_type": "bearer",
  "expires_in": 900
}
```

**중요**:
- refresh_token도 새로 발급됨 (이전 refresh_token은 무효화)
- 새 토큰들을 localStorage에 업데이트 필요

---

## 🔑 사용자 계정 관리

### 기본 관리자 계정

백엔드 시작 시 자동으로 생성됨:

```python
# backend/app/api/v1/endpoints/auth.py
Email: admin@insuregraph.com
Password: Admin123!
Role: admin
Status: active
```

### 신규 사용자 등록

```bash
curl -X POST 'http://localhost:8000/api/v1/auth/register' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "SecurePass123!",
    "organization_name": "My Company",
    "phone": "010-1234-5678"
  }'
```

**중요**: 신규 가입 계정은 `status: pending` 상태로 생성되며, 관리자 승인 후 사용 가능합니다.

### 사용자 승인 (관리자만)

```bash
curl -X PATCH 'http://localhost:8000/api/v1/auth/users/{user_id}/approve' \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## 📊 인증 흐름 (Authentication Flow)

```
┌─────────┐                                     ┌─────────┐
│         │  1. POST /auth/login                │         │
│ Client  │ ──────────────────────────────────> │ Backend │
│         │     email + password                │         │
│         │                                     │         │
│         │  2. access_token + refresh_token    │         │
│         │ <────────────────────────────────── │         │
│         │                                     │         │
│         │  3. Store tokens in localStorage    │         │
│         │                                     │         │
│         │  4. API Request                     │         │
│         │     + Authorization: Bearer token   │         │
│         │ ──────────────────────────────────> │         │
│         │                                     │         │
│         │  5. Validate token                  │         │
│         │                                     │  ✓ JWT  │
│         │                                     │  verify │
│         │  6. API Response                    │         │
│         │ <────────────────────────────────── │         │
└─────────┘                                     └─────────┘

# Token 만료 시:
┌─────────┐                                     ┌─────────┐
│         │  1. API Request (expired token)     │         │
│ Client  │ ──────────────────────────────────> │ Backend │
│         │                                     │         │
│         │  2. 401 Token expired               │         │
│         │ <────────────────────────────────── │         │
│         │                                     │         │
│         │  3. POST /auth/refresh              │         │
│         │     refresh_token                   │         │
│         │ ──────────────────────────────────> │         │
│         │                                     │         │
│         │  4. New tokens                      │         │
│         │ <────────────────────────────────── │         │
│         │                                     │         │
│         │  5. Retry API Request               │         │
│         │     + new access_token              │         │
│         │ ──────────────────────────────────> │         │
└─────────┘                                     └─────────┘
```

---

## 🛡️ 보안 고려사항

### 개발 환경

- 기본 비밀번호(`Admin123!`)는 개발용입니다
- 실제 프로덕션 환경에서는 강력한 비밀번호로 변경 필요
- localStorage는 XSS 공격에 취약하므로 프로덕션에서는 httpOnly 쿠키 사용 권장

### 프로덕션 환경

1. **비밀번호 정책 강화**:
   - 최소 8자 이상
   - 대소문자, 숫자, 특수문자 포함

2. **토큰 저장소**:
   - httpOnly 쿠키 사용 (XSS 방지)
   - Secure flag 활성화 (HTTPS only)
   - SameSite=Strict 설정 (CSRF 방지)

3. **환경 변수**:
   ```bash
   # backend/.env
   SECRET_KEY=<strong-random-secret-key>
   JWT_SECRET_KEY=<another-strong-random-key>
   ```

---

## 📚 API 엔드포인트 목록

### 인증 관련 엔드포인트

| Method | Endpoint | 인증 필요 | 설명 |
|--------|----------|---------|------|
| POST | `/api/v1/auth/register` | ❌ | 회원가입 |
| POST | `/api/v1/auth/login` | ❌ | 로그인 |
| POST | `/api/v1/auth/refresh` | ❌ | 토큰 갱신 |
| POST | `/api/v1/auth/logout` | ✅ | 로그아웃 |
| GET | `/api/v1/auth/me` | ✅ | 현재 사용자 정보 조회 |
| PATCH | `/api/v1/auth/me` | ✅ | 프로필 수정 |
| POST | `/api/v1/auth/change-password` | ✅ | 비밀번호 변경 |
| GET | `/api/v1/auth/users` | ✅ | 사용자 목록 (Admin) |
| PATCH | `/api/v1/auth/users/{id}/approve` | ✅ | 사용자 승인 (Admin) |

### 인증이 필요한 주요 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/query-simple/execute` | 간단한 자연어 쿼리 실행 |
| GET | `/api/v1/customers` | 고객 목록 조회 |
| POST | `/api/v1/documents/upload` | 문서 업로드 |
| GET | `/api/v1/analytics/*` | 분석 데이터 조회 |

---

## 🧪 테스트

### 로그인 테스트

```bash
# 1. 로그인 성공 테스트
curl -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@insuregraph.com","password":"Admin123!"}' \
  | jq .

# 2. 잘못된 비밀번호 테스트
curl -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@insuregraph.com","password":"wrong"}' \
  | jq .

# 3. 존재하지 않는 사용자 테스트
curl -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"nonexistent@example.com","password":"test"}' \
  | jq .
```

### 인증 API 호출 테스트

```bash
# 1. 토큰 없이 API 호출 (401 예상)
curl -X GET 'http://localhost:8000/api/v1/auth/me' | jq .

# 2. 토큰과 함께 API 호출 (200 예상)
TOKEN=$(curl -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@insuregraph.com","password":"Admin123!"}' \
  2>/dev/null | jq -r '.access_token')

curl -X GET 'http://localhost:8000/api/v1/auth/me' \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

## 📖 참고 자료

### JWT 공식 문서
- https://jwt.io/
- https://datatracker.ietf.org/doc/html/rfc7519

### FastAPI Security
- https://fastapi.tiangolo.com/tutorial/security/

### 관련 파일

**Backend**:
- `backend/app/api/v1/endpoints/auth.py` - 인증 엔드포인트
- `backend/app/core/security.py` - JWT 토큰 생성/검증
- `backend/app/models/user.py` - 사용자 모델

**Frontend**:
- `frontend/src/app/simple-login/page.tsx` - 로그인 페이지
- `frontend/src/store/auth-store.ts` - 인증 상태 관리
- `frontend/src/lib/simple-query-api.ts` - 인증 API 클라이언트

---

**작성일**: 2025-12-10
**작성자**: Claude AI Assistant
**버전**: 1.0

**상태**: ✅ 완료
**테스트**: ✅ 로그인 성공 확인 (admin@insuregraph.com)
