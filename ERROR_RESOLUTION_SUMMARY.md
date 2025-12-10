# InsureGraph Pro - 에러 해결 완전 요약

## 📌 발생한 문제들 (시간순)

사용자가 프론트엔드 서버를 실행하면서 3가지 주요 에러가 순차적으로 발생했습니다:

1. **CORS 400 Bad Request** - "Disallowed CORS origin"
2. **500 Internal Server Error** - 실제로는 **429 Rate Limit Exceeded**
3. **401 Unauthorized** - "Not authenticated"

---

## 🔍 문제 1: CORS 400 Bad Request

### 증상
```
OPTIONS /api/v1/crawler/stats/learning HTTP/1.1 400 Bad Request
Disallowed CORS origin
```

### 근본 원인
프론트엔드는 **포트 3001**에서 실행 중이지만, `backend/.env` 파일의 `CORS_ORIGINS`에 **포트 3001이 없었음**

```bash
# backend/.env - 문제
CORS_ORIGINS=http://localhost:3000,http://localhost:3030,http://localhost:8000
# ❌ 포트 3001이 없음!
```

### 해결 방법
`backend/.env` 파일에 포트 3001 추가:

```bash
# backend/.env - 수정 후
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3030,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:3001
```

**중요**: `.env` 파일 변경 후 반드시 백엔드 서버를 **수동으로 재시작**해야 합니다!
- `uvicorn --reload`는 Python 코드만 감지하고, `.env` 파일 변경은 감지하지 않습니다

### 검증
```bash
curl -X OPTIONS http://localhost:8000/api/v1/crawler/stats/learning \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: GET" \
  -v

# ✅ 결과: HTTP/1.1 200 OK
# ✅ access-control-allow-origin: http://localhost:3001
```

---

## 🔍 문제 2: 500 Internal Server Error (실제로는 Rate Limit!)

### 증상
```
GET http://localhost:8000/api/v1/crawler/documents?status=processing&limit=1
net::ERR_FAILED 500 (Internal Server Error)

Access to fetch has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present
```

### 첫인상
CORS 에러처럼 보이지만, **실제로는 CORS 문제가 아님!**

### 근본 원인 (백엔드 로그 분석 결과)
```
ERROR: 429 Rate Limit Exceeded
- limit: 100 requests per minute
- actual requests: ~150-200 requests per minute

fastapi.exceptions.HTTPException: 429: {
  'error_code': 'RATE_LIMIT_EXCEEDED',
  'error_message': 'Too many requests. Please try again later.',
  'limit': 100
}
```

**왜 발생했나?**
- 프론트엔드 대시보드가 **2초마다 여러 API를 동시에 polling**
- Rate Limit이 **100 requests/minute**로 설정됨
- 실제 요청: **~150-200 requests/minute** → 제한 초과

**왜 CORS 에러로 보였나?**
1. Rate Limit 초과 → 429 에러 발생
2. Exception handler에서 500 응답 생성
3. **500 에러 응답에는 CORS 헤더가 붙지 않음**
4. 브라우저가 "No CORS header"로 표시

### 해결 방법
개발 환경에서는 Rate Limit을 대폭 완화:

```python
# backend/app/main.py
# Rate limiting middleware
# ⚠️ In development: very high limit (10000/min) to avoid blocking dashboard polling
# ⚠️ In production: strict limit (100/min) for security
if settings.ENVIRONMENT == "production":
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
else:
    # Development: 10000 requests per minute (effectively unlimited for local dev)
    app.add_middleware(RateLimitMiddleware, max_requests=10000, window_seconds=60)
```

**결과**: 개발 환경에서 분당 10,000개 요청까지 허용 → 대시보드 polling이 Rate Limit에 걸리지 않음

### 검증
백엔드 로그에서 429 에러가 사라짐. 대시보드가 정상적으로 polling 수행.

---

## 🔍 문제 3: 401 Unauthorized - "Not authenticated"

### 증상
```
POST http://localhost:8000/api/v1/query-simple/execute 401 (Unauthorized)
Failed to submit question: Error: Not authenticated
```

### 근본 원인
**사용자가 로그인하지 않음** → localStorage에 인증 토큰이 없음

**API 엔드포인트 분석**:
```python
# backend/app/api/v1/endpoints/query_simple.py
@router.post("/execute", response_model=SimpleQueryResponse)
async def execute_simple_query(
    request: SimpleQueryRequest,
    user: User = Depends(get_current_active_user),  # ← 인증 필수!
    db = Depends(get_pg_connection),
):
```

**프론트엔드 API 클라이언트**:
```typescript
// frontend/src/lib/simple-query-api.ts
const token = typeof window !== 'undefined'
  ? (localStorage.getItem('access_token') || localStorage.getItem('token'))
  : null

const headers = {
  'Content-Type': 'application/json',
  ...(token ? { Authorization: `Bearer ${token}` } : {}),  // 토큰 없으면 헤더도 없음
}
```

### 해결 방법

#### 1. 로그인 페이지로 이동
```
http://localhost:3001/simple-login
```

#### 2. 기본 계정으로 로그인
- 이메일: `admin@insuregraph.com`
- 비밀번호: `Admin123!`

#### 3. 로그인 성공 시
- 자동으로 대시보드로 이동
- `access_token`과 `refresh_token`이 localStorage에 저장됨
- 이후 모든 API 요청에 자동으로 토큰 포함됨

### 검증

#### 브라우저 Console에서 토큰 확인:
```javascript
localStorage.getItem('access_token')
// 토큰이 있으면 로그인 상태
// null이면 로그인 필요
```

#### curl로 로그인 테스트:
```bash
curl -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@insuregraph.com","password":"Admin123!"}' \
  | jq .
```

**응답**:
```json
{
  "user": {
    "user_id": "ded8cdcb-ff0c-4a3c-b95b-be435d9b711b",
    "email": "admin@insuregraph.com",
    "username": "admin",
    "role": "admin",
    "status": "active"
  },
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 900
}
```

✅ 로그인 엔드포인트가 정상 작동하고, 기본 관리자 계정이 사용 가능함을 확인

---

## 📊 종합 정리

### 3가지 에러의 실제 원인

| 에러 메시지 | 겉보기 원인 | 실제 원인 | 해결 방법 |
|-----------|-----------|---------|---------|
| CORS 400 Bad Request | CORS 설정 문제 | ✅ 포트 3001 누락 | CORS_ORIGINS에 포트 3001 추가 + 서버 재시작 |
| 500 Internal Server Error + CORS | CORS 문제 | ✅ Rate Limit 초과 | 개발 환경에서 Rate Limit을 10000/min으로 완화 |
| 401 Unauthorized | 인증 실패 | ✅ 로그인 안 함 | /simple-login 페이지에서 로그인 |

### 교훈

1. **CORS처럼 보이는 에러가 실제로는 다른 원인일 수 있음**
   - 500 에러 → CORS 헤더 없음 → 브라우저가 CORS 에러로 표시
   - 항상 백엔드 로그를 확인해야 함

2. **.env 파일 변경 후 서버 재시작 필수**
   - `uvicorn --reload`는 Python 코드만 감지
   - 환경 변수 변경은 수동 재시작 필요

3. **개발 환경 vs 프로덕션 환경**
   - Rate Limit: 개발(10000/min) vs 프로덕션(100/min)
   - 개발 중 polling이 많은 경우 Rate Limit 완화 필요

4. **인증이 필요한 API**
   - 대부분의 API 엔드포인트는 인증 필요
   - 개발 중에도 로그인 상태 유지해야 함

---

## 📋 수정된 파일 목록

### 1. backend/.env
```diff
- CORS_ORIGINS=http://localhost:3000,http://localhost:3030,http://localhost:8000
+ CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3030,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:3001
```

### 2. backend/app/main.py
```python
# Rate limiting middleware (이미 수정됨)
if settings.ENVIRONMENT == "production":
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
else:
    app.add_middleware(RateLimitMiddleware, max_requests=10000, window_seconds=60)
```

### 3. 문서 파일

**신규 생성**:
- `AUTH_GUIDE.md` - 완전한 인증 가이드
- `ERROR_RESOLUTION_SUMMARY.md` - 이 파일

**업데이트**:
- `DEV_SETUP_GUIDE.md` v2.0 - 인증 섹션 추가, 401 에러 가이드 추가
- `CORS_FIX_SUMMARY.md` v2.0 - Rate Limit 원인 추가 (이미 수정됨)

---

## 🚀 향후 개발 환경 시작 체크리스트

### 1. 환경 확인
- [ ] Docker Desktop 실행 중
- [ ] PostgreSQL 컨테이너 실행 중 (port 5432)
- [ ] Redis 컨테이너 실행 중 (port 6379)

### 2. 설정 확인
- [ ] `backend/.env` 파일에 CORS_ORIGINS 설정 (포트 3001 포함)
- [ ] `backend/app/main.py`에서 개발 환경 Rate Limit 10000/min 확인
- [ ] CORSMiddleware가 마지막에 추가되었는지 확인

### 3. 서버 시작
```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (별도 터미널)
cd frontend
npm run dev
```

### 4. 로그인
1. http://localhost:3001/simple-login 접속
2. `admin@insuregraph.com` / `Admin123!` 로 로그인
3. localStorage에 토큰 저장 확인

### 5. 접속
- Frontend: http://localhost:3001
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🔗 관련 문서

- **DEV_SETUP_GUIDE.md** - 개발 환경 설정 전체 가이드
- **AUTH_GUIDE.md** - 인증 시스템 완전 가이드
- **CORS_FIX_SUMMARY.md** - CORS 및 Rate Limit 에러 해결
- **ERROR_RESOLUTION_SUMMARY.md** - 이 문서 (전체 에러 해결 요약)

---

## 💡 빠른 참조

### 로그인 정보
```
URL: http://localhost:3001/simple-login
Email: admin@insuregraph.com
Password: Admin123!
```

### 토큰 확인
```javascript
// 브라우저 Console
localStorage.getItem('access_token')
```

### CORS 테스트
```bash
curl -X OPTIONS http://localhost:8000/api/v1/crawler/stats/learning \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

### Rate Limit 확인
```bash
# 백엔드 로그에서 429 에러 확인
tail -f backend/backend.log | grep "429\|Rate"
```

---

**작성일**: 2025-12-10
**작성자**: Claude AI Assistant
**버전**: 1.0

**상태**: ✅ 모든 에러 해결 완료
**테스트**: ✅ CORS, Rate Limit, Authentication 모두 정상 작동 확인

**요약**:
- CORS 에러 → 포트 3001 추가
- 500 에러 (실제 Rate Limit) → 개발 환경 10000/min으로 완화
- 401 에러 → 로그인 가이드 작성 및 테스트 완료
