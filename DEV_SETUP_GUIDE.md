# InsureGraph Pro - 개발 환경 설정 가이드

## ⚠️ 중요: CORS 에러 방지

### 문제 상황
프론트엔드(localhost:3001)에서 백엔드(localhost:8000) API 호출 시 CORS 에러 발생:
```
OPTIONS /api/v1/crawler/stats/learning 405 Method Not Allowed
```

### 근본 원인
**FastAPI 미들웨어 실행 순서 문제**

FastAPI에서 미들웨어는 **역순으로 실행**됩니다:
- 마지막에 추가된 미들웨어가 **가장 먼저** 실행
- 첫 번째로 추가된 미들웨어가 **가장 나중에** 실행

따라서:
```python
# ❌ 잘못된 순서
app.add_middleware(CORSMiddleware)  # 3번째 실행
app.add_middleware(SecurityHeadersMiddleware)  # 2번째 실행
app.add_middleware(RateLimitMiddleware)  # 1번째 실행 ⚠️ CORS 전에 실행!

# ✅ 올바른 순서
app.add_middleware(RateLimitMiddleware)  # 3번째 실행
app.add_middleware(SecurityHeadersMiddleware)  # 2번째 실행
app.add_middleware(CORSMiddleware)  # 1번째 실행 ✅ 가장 먼저!
```

### 해결 방법

#### 1. CORS 미들웨어는 **항상 마지막에 추가**

`backend/app/main.py`:
```python
# ⚠️  Middleware execution order: Last added = First executed
# CORS must be added LAST to execute FIRST

# 1. 일반 미들웨어들
app.add_middleware(GZipMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# 2. ✅ CORS는 항상 마지막에!
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],  # OPTIONS 포함
    allow_headers=["*"],
    expose_headers=["*"],
)
```

#### 2. CORS 설정 확인

`backend/.env`:
```bash
# 개발 환경 - 반드시 포트 3001 포함!
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3030,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:3001

# 프로덕션 환경
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

**⚠️ 중요**: `.env` 파일 변경 후에는 **반드시 백엔드 서버를 재시작**해야 합니다!
- `uvicorn --reload`는 Python 코드만 감지하고, `.env` 파일 변경은 감지하지 않습니다
- 변경 후: `Ctrl+C`로 서버 종료 → 다시 시작

`backend/app/core/config.py`:
```python
class Settings(BaseSettings):
    # CORS origins
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
```

---

## 🔐 인증 (Authentication)

### 필수: 로그인 필요

**중요**: 대부분의 API 엔드포인트는 **인증이 필요**합니다. 로그인하지 않으면 `401 Unauthorized` 에러가 발생합니다.

### 로그인 방법

1. **프론트엔드 로그인 페이지 사용** (권장):
   ```
   http://localhost:3001/simple-login
   ```
   - 기본 계정: `admin@insuregraph.com` / `Admin123!`
   - 로그인 성공 시 토큰이 자동으로 localStorage에 저장됨

2. **API 직접 호출** (테스트용):
   ```bash
   curl -X POST 'http://localhost:8000/api/v1/auth/login' \
     -H 'Content-Type: application/json' \
     -d '{"email":"admin@insuregraph.com","password":"Admin123!"}'
   ```

### 401 Unauthorized 에러 해결

**증상**:
```
POST http://localhost:8000/api/v1/query-simple/execute 401 (Unauthorized)
Failed to submit question: Error: Not authenticated
```

**원인**: localStorage에 인증 토큰이 없음 (로그인 필요)

**해결**:
1. http://localhost:3001/simple-login 페이지로 이동
2. 기본 계정으로 로그인: `admin@insuregraph.com` / `Admin123!`
3. 로그인 성공 후 원하는 페이지로 이동
4. 이제 API 요청이 정상 작동함

**토큰 확인 방법**:
```javascript
// 브라우저 개발자 도구 Console에서
localStorage.getItem('access_token')
// 토큰이 있으면 로그인 상태, null이면 로그인 필요
```

---

## 🚀 빠른 시작

### 1. Docker Desktop 시작
```bash
open -a Docker
sleep 15  # Docker 시작 대기
```

### 2. Backend 시작
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend 시작 (별도 터미널)
```bash
cd frontend
npm run dev
```

### 4. 접속
- Frontend: http://localhost:3001
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🔍 문제 진단

### CORS 에러 확인
```bash
# OPTIONS 요청 테스트
curl -X OPTIONS http://localhost:8000/api/v1/crawler/stats/learning -v

# 응답 확인
# ✅ 200 OK 또는 204 No Content = 정상
# ❌ 405 Method Not Allowed = CORS 문제
# ❌ 404 Not Found = 엔드포인트 없음
```

### 미들웨어 순서 확인
`backend/app/main.py`에서 확인:
```python
# ✅ CORSMiddleware가 가장 마지막에 추가되어 있어야 함
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CORSMiddleware)  # ← 마지막!
```

---

## 📋 체크리스트

개발 환경 시작 전 체크:
- [ ] Docker Desktop이 실행 중
- [ ] PostgreSQL 컨테이너 실행 중 (port 5432)
- [ ] Redis 컨테이너 실행 중 (port 6379)
- [ ] `backend/.env` 파일 존재
- [ ] `frontend/.env.local` 파일 존재
- [ ] CORS_ORIGINS 설정 확인 (포트 3001 포함)
- [ ] CORSMiddleware가 마지막에 추가됨
- [ ] Rate Limit이 개발 환경에서 10000/min으로 설정됨

API 사용 전 체크:
- [ ] http://localhost:3001/simple-login 에서 로그인 완료
- [ ] 기본 계정: admin@insuregraph.com / Admin123!
- [ ] localStorage에 access_token 존재 확인

---

## 🛠️ 자동화 스크립트

### 전체 개발 환경 시작
`dev-start.sh` 참조

### 전체 개발 환경 중지
`dev-stop.sh` 참조

---

## 📚 참고 자료

### FastAPI 미들웨어 공식 문서
https://fastapi.tiangolo.com/tutorial/middleware/

### CORS 설명
- Preflight Request: 브라우저가 실제 요청 전에 OPTIONS 요청으로 권한 확인
- Access-Control-Allow-Origin: 허용된 origin 목록
- Access-Control-Allow-Methods: 허용된 HTTP 메서드
- Access-Control-Allow-Headers: 허용된 헤더

---

## 🚨 자주 발생하는 에러

### 1. 500 Internal Server Error + CORS 에러 (실제로는 Rate Limit!)
**증상**: 프론트엔드에서 "No 'Access-Control-Allow-Origin' header" 에러 + 백엔드 500 에러
**실제 원인**: **429 Rate Limit Exceeded** (분당 100개 제한 초과)
**해결**:
```python
# backend/app/main.py 확인
# 개발 환경에서는 10000/min으로 설정되어 있어야 함
if settings.ENVIRONMENT == "production":
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
else:
    app.add_middleware(RateLimitMiddleware, max_requests=10000, window_seconds=60)
```

**진단 방법**:
```bash
# 백엔드 로그에서 429 에러 확인
tail -f backend/backend.log | grep "429\|Rate"

# 또는
grep -r "RATE_LIMIT_EXCEEDED" backend/backend.log
```

**왜 CORS 에러로 보이나?**
- Rate Limit 초과 → 429 에러 → Exception handler → 500 응답
- 500 에러 응답에는 CORS 헤더가 붙지 않음
- 브라우저가 "No CORS header"로 표시

### 2. OPTIONS 400 Bad Request + "Disallowed CORS origin"
**원인**: 프론트엔드가 사용하는 포트(3001)가 CORS_ORIGINS에 없음
**해결**:
```bash
# backend/.env 파일 수정
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3030,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:3001

# 서버 재시작 (중요!)
# Ctrl+C로 백엔드 종료 후 다시 시작
```

**진단 방법**:
```bash
# CORS preflight 요청 테스트
curl -X OPTIONS http://localhost:8000/api/v1/crawler/stats/learning \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: GET" \
  -v

# ✅ 정상: HTTP/1.1 200 OK
# ❌ 에러: HTTP/1.1 400 Bad Request + "Disallowed CORS origin"
```

### 3. OPTIONS 405 Method Not Allowed
**원인**: CORS 미들웨어 순서 문제 (현재는 해결됨)
**해결**: CORSMiddleware를 마지막에 추가 (이미 적용됨)

### 4. CORS policy: No 'Access-Control-Allow-Origin' header
**원인**: CORS_ORIGINS 설정 누락
**해결**: `.env`에 CORS_ORIGINS 추가 후 **서버 재시작**

### 5. Port already in use
**원인**: 이전 프로세스가 포트 사용 중
**해결**:
```bash
# 포트 8000 사용 프로세스 종료
lsof -ti :8000 | xargs kill -9

# 포트 3001 사용 프로세스 종료
lsof -ti :3001 | xargs kill -9
```

### 6. 401 Unauthorized - "Not authenticated"
**증상**:
```
POST http://localhost:8000/api/v1/query-simple/execute 401 (Unauthorized)
Failed to submit question: Error: Not authenticated
```

**원인**: 로그인하지 않아서 localStorage에 인증 토큰이 없음

**해결**:
1. 로그인 페이지로 이동: http://localhost:3001/simple-login
2. 기본 계정으로 로그인: `admin@insuregraph.com` / `Admin123!`
3. 로그인 성공 후 원하는 페이지에서 API 사용

**진단 방법**:
```javascript
// 브라우저 개발자 도구 Console에서
localStorage.getItem('access_token')
// null이면 로그인 필요, 토큰이 있으면 로그인 상태
```

**중요**: 대부분의 API 엔드포인트는 인증이 필요합니다. 개발 중에도 로그인 상태를 유지해야 합니다.

---

**작성일**: 2025-12-10
**작성자**: Claude AI Assistant
**버전**: 2.0 (인증 가이드 추가)
