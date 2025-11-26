# Story 3.4: Rate Limiting & Monitoring - 구현 완료

**Story ID**: 3.4
**Story Name**: Rate Limiting & Monitoring
**Story Points**: 3
**Status**: ✅ Completed
**Epic**: Epic 3 - API & Service Layer

---

## 📋 Story 개요

### 목표
API 보호 및 시스템 모니터링을 위한 Rate Limiting과 Metrics 수집 시스템을 구축합니다.

### 주요 기능
1. **Rate Limiting**: IP/사용자 기반 요청 제한
2. **Request Logging**: 모든 요청/응답 로깅
3. **Performance Metrics**: 응답 시간, 요청 수 등 수집
4. **Error Tracking**: 에러 추적 및 분석
5. **Monitoring Endpoints**: Prometheus metrics, 통계, 헬스 체크

### 보호 기능
- DDoS 공격 방어
- API 남용 방지
- 시스템 성능 모니터링
- 실시간 에러 추적

---

## 🏗️ 아키텍처

### Middleware Stack

```
Request
  ↓
CORS Middleware
  ↓
GZip Middleware
  ↓
Request Logging Middleware
  ├─ Generate Request ID
  ├─ Log request (method, path, IP, user)
  ├─ Measure response time
  └─ Record metrics
  ↓
Rate Limiting Middleware
  ├─ Check IP/User rate limit
  ├─ Increment counter
  ├─ Add headers (X-RateLimit-*)
  └─ Reject if exceeded (429)
  ↓
Application Logic
  ↓
Response
  ├─ Add X-Request-ID
  ├─ Add X-Response-Time
  └─ Add X-RateLimit-* headers
```

### Metrics Flow

```
Request → Logging Middleware
            ↓
          Record:
          - Request count
          - Response time
          - Status code
          - User info
            ↓
        Metrics Store
          - In-Memory (Development)
          - Redis/Prometheus (Production)
            ↓
    Monitoring Endpoints
      /api/v1/monitoring/metrics    (Prometheus format)
      /api/v1/monitoring/stats       (JSON stats)
      /api/v1/monitoring/errors      (Error logs)
      /api/v1/monitoring/health/detailed
```

---

## 📁 구현 파일

### 1. Rate Limiting (`app/core/rate_limit.py` - 310 lines)

**주요 클래스**:

```python
class RateLimitStore:
    """
    Rate limit 정보를 저장하는 In-Memory 스토어

    Production: Redis로 교체 필요
    """
    def get(self, key: str) -> Optional[Dict]
    def set(self, key: str, value: Dict)
    def cleanup_expired(self, window_seconds: int)

class RateLimiter:
    """
    Rate Limiter 클래스

    Sliding window 알고리즘 사용
    """
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        identifier_func: Optional[Callable] = None
    )

    async def check_rate_limit(self, request: Request) -> tuple[bool, Dict]:
        """
        Rate limit 확인

        Returns:
            (allowed, info)
            - allowed: bool - 요청 허용 여부
            - info: Dict - rate limit 정보
        """

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate Limiting Middleware"""
    async def dispatch(self, request: Request, call_next):
        # Check rate limit
        allowed, info = await self.rate_limiter.check_rate_limit(request)

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many requests",
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(window_seconds),
                }
            )

        # Add headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])

        return response
```

**엔드포인트별 Rate Limiter**:
```python
# Login endpoint: 5 requests per 5 minutes
login_rate_limiter = RateLimiter(max_requests=5, window_seconds=300)

# Query endpoint: 20 requests per minute
query_rate_limiter = create_user_rate_limiter(max_requests=20, window_seconds=60)

# Document upload: 10 requests per hour
upload_rate_limiter = create_user_rate_limiter(max_requests=10, window_seconds=3600)
```

### 2. Logging & Metrics (`app/core/logging.py` - 450 lines)

**Request Logging Middleware**:
```python
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """모든 HTTP 요청을 로깅하는 미들웨어"""
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid4())[:8]

        # Record start time
        start_time = time.time()

        # Log request
        logger.info(f"[{request_id}] {method} {path} | IP: {ip}")

        # Process
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log response
        logger.info(
            f"[{request_id}] {method} {path} | "
            f"Status: {response.status_code} | "
            f"Duration: {duration_ms:.2f}ms"
        )

        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        # Record metrics
        _record_request_metrics(method, path, status_code, duration_ms)

        return response
```

**Metrics Store**:
```python
class MetricsStore:
    """메트릭 저장소"""
    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: str = "anonymous"
    ):
        # Request count
        self.request_count[endpoint] += 1

        # Duration (keep last 1000)
        self.request_duration[endpoint].append(duration_ms)

        # Status codes
        self.status_codes[status_code] += 1

        # User requests
        self.requests_by_user[user_id] += 1

    def get_stats(self) -> Dict:
        """통계 조회"""
        # Calculate percentiles
        p50 = percentile(all_durations, 0.50)
        p95 = percentile(all_durations, 0.95)
        p99 = percentile(all_durations, 0.99)

        return {
            "uptime_seconds": uptime,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": error_rate,
            "requests_per_second": rps,
            "response_time": {
                "p50_ms": p50,
                "p95_ms": p95,
                "p99_ms": p99,
            },
            "top_endpoints": top_5_endpoints,
            "status_codes": status_distribution,
        }

    def get_prometheus_metrics(self) -> str:
        """Prometheus 형식 메트릭 반환"""
        return """
        # HELP http_requests_total Total HTTP requests
        # TYPE http_requests_total counter
        http_requests_total{method="GET",path="/api/v1/"} 150

        # HELP http_request_duration_milliseconds HTTP request duration
        # TYPE http_request_duration_milliseconds histogram
        http_request_duration_milliseconds{method="GET",path="/api/v1/"} 45.2
        """
```

**Error Tracker**:
```python
class ErrorTracker:
    """에러 추적 및 분석"""
    def track_error(
        self,
        error: Exception,
        request: Optional[Request] = None,
        context: Optional[Dict] = None
    ):
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": traceback if DEBUG else None,
            "request": {
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host,
            },
            "context": context,
        }

        self.errors.append(error_info)
        logger.error(f"Error tracked: {error_type}")

    def get_error_summary(self) -> Dict:
        """에러 요약"""
        return {
            "total_errors": len(self.errors),
            "error_types": error_type_counts,
            "recent_errors": last_5_errors,
        }
```

### 3. Monitoring Endpoints (`app/api/v1/endpoints/monitoring.py` - 195 lines)

**GET /api/v1/monitoring/metrics** (Prometheus):
```python
@router.get("/metrics", response_class=Response)
async def get_metrics():
    """Prometheus 메트릭 조회"""
    metrics_store = get_metrics_store()
    prometheus_metrics = metrics_store.get_prometheus_metrics()

    return Response(
        content=prometheus_metrics,
        media_type="text/plain; version=0.0.4"
    )
```

**GET /api/v1/monitoring/stats** (JSON):
```python
@router.get("/stats")
async def get_stats() -> Dict:
    """시스템 통계 조회"""
    stats = metrics_store.get_stats()

    return {
        "timestamp": datetime.now().isoformat(),
        "app_name": "InsureGraph Pro",
        "version": "1.0.0",
        "stats": stats,
    }
```

**GET /api/v1/monitoring/errors**:
```python
@router.get("/errors")
async def get_errors() -> Dict:
    """에러 로그 조회"""
    # In production: Admin only
    error_summary = error_tracker.get_error_summary()

    return {
        "timestamp": datetime.now().isoformat(),
        "errors": error_summary,
    }
```

**GET /api/v1/monitoring/health/detailed**:
```python
@router.get("/health/detailed")
async def detailed_health_check() -> Dict:
    """상세 헬스 체크"""
    # Determine health based on error rate
    if error_rate > 0.5:
        overall_status = "unhealthy"
    elif error_rate > 0.1:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return {
        "status": overall_status,
        "components": {
            "database": "ok",
            "cache": "ok",
            "api": "ok",
        },
        "metrics": {
            "uptime_seconds": uptime,
            "total_requests": total,
            "error_rate": error_rate,
            "response_time_p95_ms": p95,
        },
        "errors": error_summary,
    }
```

### 4. Main App Integration (`app/main.py` - updated)

```python
from app.core.rate_limit import RateLimitMiddleware
from app.core.logging import RequestLoggingMiddleware

# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting middleware (100 requests per minute)
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
```

### 5. Tests (`tests/test_monitoring.py` - 185 lines)

**테스트 구조**:
```python
# 1. Monitoring endpoints (4 tests)
class TestMonitoringEndpoints:
    test_get_metrics
    test_get_stats
    test_get_errors
    test_detailed_health_check

# 2. Rate limiting (2 tests)
class TestRateLimiting:
    test_rate_limit_headers
    test_rate_limit_exceeded

# 3. Request logging (2 tests)
class TestRequestLogging:
    test_request_id_header
    test_response_time_header

# 4. Metrics collection (2 tests)
class TestMetricsCollection:
    test_metrics_after_requests
    test_prometheus_format

# 5. Integration (1 test)
class TestMonitoringIntegration:
    test_full_monitoring_flow
```

---

## 🔑 핵심 구현 내용

### 1. Rate Limiting 알고리즘

**Sliding Window**:
```
Window: 60 seconds
Limit: 100 requests

Time:  0s        30s        60s        90s
       |----------|----------|----------|
Req:   50         30         20         40

At 30s: count=80  (allowed)
At 60s: count=50  (reset window, allowed)
At 90s: count=60  (allowed)
```

**Rate Limit Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 2025-11-25T21:00:00Z
Retry-After: 60
```

### 2. Request Logging Format

```
[a1b2c3d4] GET /api/v1/query | IP: 192.168.1.1 | User: authenticated
[a1b2c3d4] GET /api/v1/query | Status: 200 | Duration: 125.45ms
```

### 3. Metrics Collection

**Collected Metrics**:
- Request count per endpoint
- Response time (p50, p95, p99)
- Status code distribution
- Error count by type
- Requests per user

**Prometheus Format**:
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/api/v1/query"} 1234

# HELP http_request_duration_milliseconds HTTP request duration
# TYPE http_request_duration_milliseconds histogram
http_request_duration_milliseconds{method="GET",path="/api/v1/query"} 125.45
```

### 4. Error Tracking

**Tracked Information**:
```json
{
  "timestamp": "2025-11-25T20:30:00",
  "error_type": "ValueError",
  "error_message": "Invalid input",
  "stack_trace": "...",  // DEBUG only
  "request": {
    "method": "POST",
    "path": "/api/v1/query",
    "client_host": "192.168.1.1"
  },
  "context": {...}
}
```

---

## 📊 사용 예시

### 1. Rate Limit 확인

```bash
curl -v http://localhost:8000/api/v1/
```

**응답 헤더**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 2025-11-25T21:00:00Z
X-Request-ID: a1b2c3d4
X-Response-Time: 12.34ms
```

### 2. Prometheus Metrics 조회

```bash
curl http://localhost:8000/api/v1/monitoring/metrics
```

**응답**:
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/api/v1/"} 150

# HELP http_request_duration_milliseconds HTTP request duration
# TYPE http_request_duration_milliseconds histogram
http_request_duration_milliseconds{method="GET",path="/api/v1/"} 45.2
```

### 3. 시스템 통계 조회

```bash
curl http://localhost:8000/api/v1/monitoring/stats
```

**응답**:
```json
{
  "timestamp": "2025-11-25T20:30:00",
  "app_name": "InsureGraph Pro",
  "version": "1.0.0",
  "stats": {
    "uptime_seconds": 3600,
    "total_requests": 1234,
    "total_errors": 12,
    "error_rate": 0.0097,
    "requests_per_second": 0.34,
    "response_time": {
      "p50_ms": 45.2,
      "p95_ms": 125.8,
      "p99_ms": 250.3
    },
    "top_endpoints": {
      "GET /api/v1/query": 500,
      "POST /api/v1/auth/login": 300,
      "GET /api/v1/documents": 200
    },
    "status_codes": {
      "200": 1100,
      "201": 50,
      "400": 30,
      "401": 20,
      "500": 34
    }
  }
}
```

### 4. 상세 헬스 체크

```bash
curl http://localhost:8000/api/v1/monitoring/health/detailed
```

**응답**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-25T20:30:00",
  "app": {
    "name": "InsureGraph Pro",
    "version": "1.0.0",
    "environment": "production"
  },
  "components": {
    "database": "ok",
    "cache": "ok",
    "api": "ok"
  },
  "metrics": {
    "uptime_seconds": 3600,
    "total_requests": 1234,
    "requests_per_second": 0.34,
    "error_rate": 0.0097,
    "response_time_p95_ms": 125.8
  },
  "errors": {
    "total": 12,
    "types": {
      "ValueError": 8,
      "KeyError": 3,
      "HTTPException": 1
    }
  }
}
```

---

## 🎯 검증 및 품질 보증

### 1. Rate Limiting 테스트
✅ **2개 테스트 구현**
- Rate limit 헤더 확인
- Rate limit 초과 시나리오

### 2. Logging 테스트
✅ **2개 테스트 구현**
- Request ID 헤더
- Response time 헤더

### 3. Metrics 테스트
✅ **2개 테스트 구현**
- 요청 후 메트릭 확인
- Prometheus 형식 검증

### 4. Integration 테스트
✅ **1개 테스트 구현**
- 전체 모니터링 플로우

---

## 🚀 Production 준비사항

### 현재 구현 (Development)
- In-Memory storage
- 단일 서버 환경
- 기본 rate limiting

### Production 권장사항

**1. Redis 사용**:
```python
# Rate limit storage
from redis import Redis
redis_client = Redis(host='localhost', port=6379)

class RedisRateLimitStore:
    def get(self, key: str):
        return redis_client.get(key)

    def set(self, key: str, value: Dict, ttl: int):
        redis_client.setex(key, ttl, json.dumps(value))
```

**2. Prometheus Integration**:
```python
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'path']
)
```

**3. Grafana Dashboard**:
- Request rate
- Response time (p50, p95, p99)
- Error rate
- Active users
- Top endpoints

**4. Alerting**:
```yaml
# Alert rules
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_errors_total[5m]) > 0.1
        annotations:
          summary: "High error rate detected"

      - alert: SlowResponses
        expr: http_request_duration_p95 > 1000
        annotations:
          summary: "Slow response times (p95 > 1s)"
```

---

## 📝 결론

### 구현 완료 사항
✅ **Rate Limiting** (310 lines)
  - Sliding window algorithm
  - IP/User based limiting
  - Endpoint-specific limits
  - Rate limit headers

✅ **Request Logging** (450 lines)
  - Request/Response logging
  - Request ID tracking
  - Response time measurement
  - Error tracking

✅ **Metrics Collection**
  - Request count
  - Response time percentiles
  - Status code distribution
  - Error tracking

✅ **Monitoring Endpoints** (195 lines)
  - Prometheus metrics
  - JSON stats
  - Error logs
  - Detailed health check

✅ **Tests** (185 lines, 11 tests)

### Story Points 달성
- **추정**: 3 points
- **실제**: 3 points
- **상태**: ✅ **COMPLETED**

### Epic 3 진행 상황
```
Epic 3: API & Service Layer
├─ Story 3.1: Query API Endpoints (5 pts) ✅
├─ Story 3.2: Document Upload API (5 pts) ✅
├─ Story 3.3: Authentication & Authorization (5 pts) ✅
├─ Story 3.4: Rate Limiting & Monitoring (3 pts) ✅
└─ Story 3.5: API Documentation (3 pts) ⏳ Next

Progress: 18/21 points (86% complete)
```

### 주요 성과
1. **API 보호**: Rate limiting으로 DDoS/남용 방지
2. **완전한 모니터링**: Request, metrics, errors 추적
3. **Prometheus 호환**: Production 모니터링 준비
4. **실시간 관찰성**: Request ID, response time 추적
5. **Production 준비**: Redis/Prometheus 확장 가능

---

## 📚 참고 자료

### 생성된 파일
1. `app/core/rate_limit.py` (310 lines)
2. `app/core/logging.py` (450 lines)
3. `app/api/v1/endpoints/monitoring.py` (195 lines)
4. `app/api/v1/router.py` (updated)
5. `app/main.py` (updated - middleware)
6. `tests/test_monitoring.py` (185 lines)

### Monitoring 엔드포인트
- Metrics: `GET /api/v1/monitoring/metrics`
- Stats: `GET /api/v1/monitoring/stats`
- Errors: `GET /api/v1/monitoring/errors`
- Health: `GET /api/v1/monitoring/health/detailed`

### 테스트 실행
```bash
# 모든 모니터링 테스트
pytest tests/test_monitoring.py -v

# Coverage
pytest tests/test_monitoring.py --cov=app.core --cov=app.api.v1.endpoints.monitoring
```

---

**작성일**: 2025-11-25
**작성자**: Claude (AI Assistant)
**Epic**: Epic 3 - API & Service Layer
**Status**: ✅ Completed - Story 3.4 Done! 🎉
