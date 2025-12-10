# CORS 에러 완전 해결 요약

## 🎯 문제 상황

프론트엔드(http://localhost:3001)에서 백엔드 API 호출 시 CORS 에러 발생:
```
OPTIONS /api/v1/crawler/stats/learning 400 Bad Request
Disallowed CORS origin
```

---

## 🔍 근본 원인

**세 가지 문제가 복합적으로 발생**:

### 1. ❌ Rate Limiting (주요 원인!)

**프론트엔드 대시보드가 2초마다 여러 API를 동시에 polling** → 분당 100개 제한 초과 → **429 Too Many Requests** → 500 에러로 표시 → CORS 헤더 없음 → **브라우저가 CORS 에러로 표시**

```
ERROR: 429 Rate Limit Exceeded
- limit: 100 requests per minute
- 실제 요청: ~150-200 requests per minute (dashboard polling)
```

**해결**: 개발 환경에서는 Rate Limit을 10000/min으로 대폭 증가

### 2. ❌ 잘못된 CORS_ORIGINS 설정
```bash
# backend/.env - 기존 (문제)
CORS_ORIGINS=http://localhost:3000,http://localhost:3030,http://localhost:8000
```

프론트엔드는 **포트 3001**에서 실행 중이지만, CORS_ORIGINS에 **3001이 없었음**!

### 2. ⚠️ FastAPI 미들웨어 실행 순서

FastAPI는 미들웨어를 **역순으로 실행**합니다:
- 마지막에 추가된 미들웨어 = 가장 먼저 실행
- 첫 번째로 추가된 미들웨어 = 가장 나중에 실행

따라서 **CORSMiddleware는 항상 마지막에 추가**해야 가장 먼저 실행됩니다.

---

## ✅ 해결 방법

### Step 0: Rate Limit 조정 (가장 중요!)

**파일**: `backend/app/main.py`
```python
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

### Step 1: CORS_ORIGINS 업데이트

**파일**: `backend/.env`
```bash
# 수정 전
CORS_ORIGINS=http://localhost:3000,http://localhost:3030,http://localhost:8000

# 수정 후 - 포트 3001 추가!
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3030,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:3001
```

### Step 2: 백엔드 서버 재시작

**⚠️ 매우 중요**: `.env` 파일 변경 후에는 **반드시 서버를 재시작**해야 합니다!

```bash
# uvicorn --reload는 Python 코드만 감지하고, .env 파일 변경은 감지 안 함!
# 1. 현재 실행 중인 백엔드 종료 (Ctrl+C)
# 2. 다시 시작
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: CORSMiddleware 순서 확인

**파일**: `backend/app/main.py` (이미 수정됨)

```python
# ⚠️ Middleware execution order: Last added = First executed
# CORS must be added LAST to execute FIRST

# 1. 일반 미들웨어들 먼저
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityHeadersMiddleware, ...)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, ...)

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

---

## ✅ 테스트 및 검증

### 1. CORS Preflight 요청 테스트
```bash
curl -X OPTIONS http://localhost:8000/api/v1/crawler/stats/learning \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

**정상 응답**:
```
HTTP/1.1 200 OK
access-control-allow-origin: http://localhost:3001
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
access-control-allow-credentials: true
```

**에러 응답** (수정 전):
```
HTTP/1.1 400 Bad Request
Disallowed CORS origin
```

### 2. 프론트엔드 확인
브라우저에서 http://localhost:3001 접속 후:
- 개발자 도구(F12) → Console 탭
- CORS 에러가 없어야 함
- API 요청이 정상적으로 완료되어야 함

---

## 📋 체크리스트 (향후 재발 방지)

개발 환경 시작 전 확인:
- [x] **Rate Limit 설정** 확인 (`backend/app/main.py`에서 개발 환경은 10000/min)
- [x] `backend/.env`에 `CORS_ORIGINS` 설정 확인
- [x] 프론트엔드가 실제로 실행되는 포트(3001) 포함 여부 확인
- [x] `.env` 파일 수정 후 **백엔드 서버 재시작** 여부 확인
- [x] `backend/app/main.py`에서 `CORSMiddleware`가 마지막에 추가되었는지 확인

**CORS처럼 보이는 500 에러 발생 시**:
1. 먼저 백엔드 로그 확인 (`tail -f backend/backend.log`)
2. 429 Rate Limit 에러 확인
3. 실제 에러 원인 파악 (Rate Limit, DB 연결, 기타)

---

## 🛠️ 자동화 스크립트

### 개발 환경 시작
```bash
./dev-start.sh
```

이 스크립트는 자동으로:
1. Docker Desktop 확인 및 시작
2. Backend 서버 시작 (포트 8000)
3. Frontend 서버 시작 (포트 3000 또는 3001)
4. 상태 확인 (health check)

### 개발 환경 중지
```bash
./dev-stop.sh
```

---

## 📚 참고 자료

### FastAPI 공식 문서
- CORS: https://fastapi.tiangolo.com/tutorial/cors/
- Middleware: https://fastapi.tiangolo.com/tutorial/middleware/

### CORS 동작 원리
1. **Preflight Request**: 브라우저가 실제 요청 전에 OPTIONS 요청으로 권한 확인
2. **Access-Control-Allow-Origin**: 허용된 origin 목록
3. **Access-Control-Allow-Methods**: 허용된 HTTP 메서드 (GET, POST, PUT, DELETE, OPTIONS 등)
4. **Access-Control-Allow-Headers**: 허용된 헤더

---

**작성일**: 2025-12-10
**작성자**: Claude AI Assistant
**버전**: 2.0 (완전 해결)

**상태**: ✅ 해결 완료
**테스트**: ✅ 통과 (OPTIONS 200 OK, access-control-allow-origin 정상)
