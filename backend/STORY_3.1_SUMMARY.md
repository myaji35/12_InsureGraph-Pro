# Story 3.1: Query API Endpoints - 구현 완료

**Story ID**: 3.1
**Story Name**: Query API Endpoints
**Story Points**: 5
**Status**: ✅ Completed
**Epic**: Epic 3 - API & Service Layer

---

## 📋 Story 개요

### 목표
FastAPI 기반 REST API 엔드포인트를 구현하여 GraphRAG 쿼리 기능을 외부에 노출합니다. 동기/비동기 질의, 상태 조회, WebSocket 스트리밍을 지원합니다.

### 주요 기능
1. **POST /api/v1/query**: 동기 질의 실행
2. **POST /api/v1/query/async**: 비동기 질의 실행
3. **GET /api/v1/query/{query_id}/status**: 질의 상태 조회
4. **WebSocket /api/v1/query/ws**: 실시간 스트리밍
5. **GET /api/v1/health**: 헬스 체크
6. **GET /api/v1/**: API 정보

### 통합 컴포넌트
- **Story 2.5**: QueryOrchestrator (전체 파이프라인)
- **FastAPI**: REST API 프레임워크
- **Pydantic**: Request/Response 검증
- **WebSocket**: 실시간 통신

---

## 🏗️ API 설계

### 엔드포인트 구조

```
/api/v1
├── /                       [GET]  API 정보
├── /health                 [GET]  헬스 체크
└── /query
    ├── /                   [POST] 동기 질의
    ├── /async              [POST] 비동기 질의
    ├── /{query_id}/status  [GET]  상태 조회
    └── /ws                 [WS]   스트리밍
```

### Request/Response 플로우

```
Client
  ↓ POST /api/v1/query
  │ {
  │   "query": "급성심근경색증 보장 금액은?",
  │   "strategy": "standard",
  │   "max_results": 10
  │ }
  ↓
API Layer (FastAPI)
  ↓ Validation (Pydantic)
  ↓ OrchestrationRequest 생성
  ↓
QueryOrchestrator (Story 2.5)
  ↓ Story 2.1: Query Analysis
  ↓ Story 2.3: Hybrid Search
  ↓ Story 2.4: Response Generation
  ↓
API Layer
  ↓ OrchestrationResponse → QueryResponse 변환
  ↓
Client
  ← HTTP 200 OK
  │ {
  │   "query_id": "a1b2c3d4",
  │   "answer": "급성심근경색증의 경우...",
  │   "confidence": 0.92,
  │   "metrics": {...}
  │ }
```

---

## 📁 구현 파일

### 1. API Models (`app/api/v1/models/query.py` - 229 lines)

**주요 모델**:

```python
# 요청 모델
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    strategy: QueryStrategyAPI = QueryStrategyAPI.STANDARD
    max_results: int = Field(default=10, ge=1, le=50)
    include_citations: bool = True
    include_follow_ups: bool = True
    session_id: Optional[str] = None
    conversation_history: List[Dict[str, str]] = []

# 응답 모델
class QueryResponse(BaseModel):
    query_id: str
    query: str
    answer: str
    format: AnswerFormat
    confidence: float
    citations: List[Citation]
    follow_up_suggestions: List[str]
    intent: Optional[str]
    strategy: str
    metrics: QueryMetrics
    timestamp: datetime
    success: bool
    errors: List[str]

# 메트릭
class QueryMetrics(BaseModel):
    total_duration_ms: float
    query_analysis_ms: Optional[float]
    search_ms: Optional[float]
    response_generation_ms: Optional[float]
    cache_hit: bool
    search_result_count: int

# 상태 응답
class QueryStatusResponse(BaseModel):
    query_id: str
    status: str  # pending/processing/completed/failed
    progress: Optional[int]  # 0-100%
    current_stage: Optional[str]
    result: Optional[QueryResponse]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

# 스트리밍 청크
class StreamChunk(BaseModel):
    chunk_type: str  # status/data/error/complete
    content: Optional[str]
    metadata: Dict[str, Any]
    timestamp: datetime

# 에러 응답
class ErrorResponse(BaseModel):
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]]
    timestamp: datetime
    request_id: Optional[str]

# 헬스 체크
class HealthCheckResponse(BaseModel):
    status: str  # healthy/degraded/unhealthy
    version: str
    components: Dict[str, str]
    timestamp: datetime
```

### 2. Query Endpoints (`app/api/v1/endpoints/query.py` - 485 lines)

**POST /api/v1/query** (동기 질의):

```python
@router.post("", response_model=QueryResponse)
async def execute_query(request: QueryRequest) -> QueryResponse:
    """
    질의 실행

    GraphRAG 파이프라인을 통해 사용자 질문을 처리하고 답변을 생성합니다.
    """
    # 1. Orchestration 요청 생성
    orch_request = OrchestrationRequest(
        query=request.query,
        session_id=request.session_id,
        strategy=OrchestrationStrategy(request.strategy.value),
        use_cache=True,
        include_citations=request.include_citations,
        include_follow_ups=request.include_follow_ups,
        max_search_results=request.max_results,
        conversation_history=request.conversation_history,
    )

    # 2. Orchestrator 실행
    orchestrator = get_orchestrator()
    orch_response = await orchestrator.process(orch_request)

    # 3. API 응답 생성
    api_response = QueryResponse(
        query_id=orch_response.request_id,
        query=orch_response.query,
        answer=orch_response.response.answer,
        format=orch_response.response.format,
        confidence=orch_response.response.confidence_score,
        citations=orch_response.response.citations,
        follow_up_suggestions=orch_response.response.follow_up_suggestions,
        intent=orch_response.query_analysis.intent,
        strategy=orch_response.strategy.value,
        metrics=QueryMetrics(...),
        success=orch_response.success,
        errors=orch_response.errors,
    )

    return api_response
```

**GET /api/v1/query/{query_id}/status** (상태 조회):

```python
@router.get("/{query_id}/status", response_model=QueryStatusResponse)
async def get_query_status(query_id: str) -> QueryStatusResponse:
    """질의 상태 조회"""
    if query_id not in _query_tasks:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "QUERY_NOT_FOUND",
                "error_message": f"Query ID '{query_id}' not found"
            }
        )

    task_info = _query_tasks[query_id]

    return QueryStatusResponse(
        query_id=query_id,
        status=task_info["status"],
        progress=task_info.get("progress"),
        current_stage=task_info.get("current_stage"),
        result=task_info.get("result"),
        error_message=task_info.get("error_message"),
        created_at=task_info["created_at"],
        updated_at=task_info["updated_at"],
    )
```

**POST /api/v1/query/async** (비동기 질의):

```python
@router.post("/async", response_model=QueryStatusResponse, status_code=202)
async def execute_query_async(request: QueryRequest) -> QueryStatusResponse:
    """비동기 질의 실행"""
    # 1. 요청 ID 생성
    query_id = hashlib.md5(...).hexdigest()[:12]

    # 2. 작업 정보 저장
    _query_tasks[query_id] = {
        "status": "pending",
        "progress": 0,
        "current_stage": "initializing",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    # 3. 백그라운드 작업 시작
    asyncio.create_task(_execute_query_background(query_id, orch_request, request))

    # 4. 즉시 응답 반환
    return QueryStatusResponse(
        query_id=query_id,
        status="pending",
        progress=0,
        current_stage="initializing",
        created_at=_query_tasks[query_id]["created_at"],
        updated_at=_query_tasks[query_id]["updated_at"],
    )
```

**WebSocket /api/v1/query/ws** (스트리밍):

```python
@router.websocket("/ws")
async def query_websocket(websocket: WebSocket):
    """WebSocket 질의 스트리밍"""
    await websocket.accept()

    try:
        while True:
            # 1. 클라이언트로부터 질의 수신
            data = await websocket.receive_text()
            message = json.loads(data)
            query = message.get("query")

            # 2. 시작 알림
            await websocket.send_json({
                "chunk_type": "status",
                "content": "started",
                "metadata": {"stage": "initializing"},
            })

            # 3. Query Analysis 단계
            await websocket.send_json({
                "chunk_type": "status",
                "content": "analyzing",
                "metadata": {"stage": "query_analysis", "progress": 10},
            })

            # 4. Orchestrator 실행
            orchestrator = get_orchestrator()
            orch_response = await orchestrator.process(orch_request)

            # 5. 최종 결과 전송
            await websocket.send_json({
                "chunk_type": "complete",
                "content": api_response.model_dump(),
                "metadata": {"progress": 100},
            })

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
```

### 3. API Router (`app/api/v1/router.py` - 64 lines)

```python
# API v1 Router
api_router = APIRouter()

# Query endpoints
api_router.include_router(query.router)

# Health Check
@api_router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """헬스 체크"""
    orchestrator = query.get_orchestrator()
    health = await orchestrator.health_check()

    return HealthCheckResponse(
        status=health["status"],
        version="1.0.0",
        components=health["components"],
    )

# Root endpoint
@api_router.get("/")
async def root():
    """API 루트"""
    return {
        "name": "InsureGraph Pro API",
        "version": "1.0.0",
        "description": "GraphRAG 기반 보험 질의응답 API",
        "docs_url": "/docs",
        "health_url": "/api/v1/health",
        "endpoints": {
            "query": "/api/v1/query",
            "query_async": "/api/v1/query/async",
            "query_status": "/api/v1/query/{query_id}/status",
            "query_ws": "/api/v1/query/ws",
        },
    }
```

### 4. Main App Integration (`app/main.py` - updated)

```python
# API v1 routers
from app.api.v1.router import api_router as v1_router

app.include_router(v1_router, prefix=settings.API_V1_PREFIX)
```

### 5. Tests (`tests/test_api_query.py` - 299 lines)

**테스트 구조**:

```python
# 1. POST /api/v1/query (6 tests)
class TestQueryEndpoint:
    test_query_success                # 정상 실행
    test_query_missing_query          # 필수 필드 누락
    test_query_empty_query            # 빈 질문
    test_query_too_long               # 너무 긴 질문
    test_query_with_strategy          # 전략 지정
    test_query_with_options           # 옵션 지정

# 2. GET /api/v1/query/{query_id}/status (1 test)
class TestQueryStatusEndpoint:
    test_status_not_found             # 존재하지 않는 질의

# 3. POST /api/v1/query/async (1 test)
class TestQueryAsyncEndpoint:
    test_async_query_created          # 비동기 질의 생성

# 4. GET /api/v1/health (1 test)
class TestHealthEndpoint:
    test_health_check                 # 헬스 체크

# 5. GET /api/v1/ (1 test)
class TestRootEndpoint:
    test_root                         # 루트 엔드포인트

# 6. Integration (2 tests)
class TestQueryAPIIntegration:
    test_end_to_end_query             # E2E 질의 실행
    test_error_handling               # 에러 처리
```

---

## 🔑 핵심 구현 내용

### 1. API 설계 원칙

**RESTful 설계**:
```
POST   /api/v1/query              - 리소스 생성 (질의 실행)
GET    /api/v1/query/{id}/status  - 리소스 조회 (상태)
WS     /api/v1/query/ws           - 실시간 통신
```

**HTTP 상태 코드**:
```
200 OK             - 성공
202 Accepted       - 비동기 작업 시작
400 Bad Request    - 잘못된 요청
404 Not Found      - 리소스 없음
422 Unprocessable  - 유효성 검사 실패
500 Internal Error - 서버 에러
```

### 2. Request Validation

**Pydantic 검증**:
```python
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    max_results: int = Field(default=10, ge=1, le=50)

# 자동 검증:
# - query가 1-1000자인지 확인
# - max_results가 1-50 범위인지 확인
# - 타입이 맞는지 확인
```

**검증 에러 예시**:
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "query"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {"min_length": 1}
    }
  ]
}
```

### 3. 에러 처리

**표준화된 에러 응답**:
```python
class ErrorResponse(BaseModel):
    error_code: str      # "QUERY_EXECUTION_FAILED"
    error_message: str   # "Orchestrator timeout"
    details: Optional[Dict[str, Any]]
    timestamp: datetime
    request_id: Optional[str]
```

**에러 코드**:
```
INVALID_QUERY          - 잘못된 질문
QUERY_EXECUTION_FAILED - 실행 실패
QUERY_NOT_FOUND        - 질의 없음
ASYNC_QUERY_FAILED     - 비동기 실패
STATUS_CHECK_FAILED    - 상태 조회 실패
```

### 4. 비동기 처리

**백그라운드 작업**:
```python
# 1. 즉시 응답 반환 (202 Accepted)
query_id = generate_id()
_query_tasks[query_id] = {"status": "pending", ...}
asyncio.create_task(_execute_query_background(...))
return QueryStatusResponse(query_id=query_id, status="pending")

# 2. 백그라운드 실행
async def _execute_query_background(query_id, ...):
    _query_tasks[query_id]["status"] = "processing"
    result = await orchestrator.process(...)
    _query_tasks[query_id]["status"] = "completed"
    _query_tasks[query_id]["result"] = result

# 3. 상태 조회
GET /api/v1/query/{query_id}/status
→ QueryStatusResponse(status="completed", result=...)
```

### 5. WebSocket 프로토콜

**클라이언트 → 서버**:
```json
{
  "query": "급성심근경색증 보장 금액은?",
  "strategy": "standard"
}
```

**서버 → 클라이언트** (순차적):
```json
// 1. 시작
{"chunk_type": "status", "content": "started", "metadata": {"stage": "initializing"}}

// 2. 분석 중
{"chunk_type": "status", "content": "analyzing", "metadata": {"stage": "query_analysis", "progress": 10}}

// 3. 검색 중
{"chunk_type": "status", "content": "searching", "metadata": {"stage": "search", "progress": 50}}

// 4. 생성 중
{"chunk_type": "status", "content": "generating", "metadata": {"stage": "response_generation", "progress": 80}}

// 5. 완료
{"chunk_type": "complete", "content": {...}, "metadata": {"progress": 100}}

// 에러 발생 시
{"chunk_type": "error", "content": "Error message"}
```

---

## 📊 API 사용 예시

### 1. 동기 질의 (cURL)

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "급성심근경색증에 걸리면 얼마를 받을 수 있나요?",
    "strategy": "standard",
    "max_results": 10,
    "include_citations": true,
    "include_follow_ups": true
  }'
```

**응답**:
```json
{
  "query_id": "a1b2c3d4e5f6",
  "query": "급성심근경색증에 걸리면 얼마를 받을 수 있나요?",
  "answer": "급성심근경색증의 경우 진단비 5,000만원과 입원비 100만원을 받을 수 있습니다.",
  "format": "table",
  "confidence": 0.92,
  "citations": [
    {
      "citation_type": "clause",
      "source_id": "clause_001",
      "article_num": "제10조",
      "relevance_score": 0.95
    }
  ],
  "follow_up_suggestions": [
    "대기기간은 얼마나 되나요?",
    "보장 조건이 있나요?"
  ],
  "intent": "coverage_amount",
  "strategy": "standard",
  "metrics": {
    "total_duration_ms": 287.5,
    "query_analysis_ms": 123.0,
    "search_ms": 145.2,
    "response_generation_ms": 19.3,
    "cache_hit": false,
    "search_result_count": 8
  },
  "timestamp": "2025-11-25T20:30:00",
  "success": true,
  "errors": []
}
```

### 2. 비동기 질의 (Python)

```python
import httpx
import asyncio

async def async_query():
    async with httpx.AsyncClient() as client:
        # 1. 비동기 질의 시작
        response = await client.post(
            "http://localhost:8000/api/v1/query/async",
            json={"query": "당뇨병은 보장되나요?"}
        )
        data = response.json()
        query_id = data["query_id"]
        print(f"Query started: {query_id}")

        # 2. 상태 폴링
        while True:
            status_response = await client.get(
                f"http://localhost:8000/api/v1/query/{query_id}/status"
            )
            status_data = status_response.json()

            print(f"Status: {status_data['status']} - {status_data['progress']}%")

            if status_data["status"] == "completed":
                result = status_data["result"]
                print(f"Answer: {result['answer']}")
                break
            elif status_data["status"] == "failed":
                print(f"Error: {status_data['error_message']}")
                break

            await asyncio.sleep(1)

asyncio.run(async_query())
```

### 3. WebSocket 스트리밍 (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/query/ws');

ws.onopen = () => {
  // 질의 전송
  ws.send(JSON.stringify({
    query: "암과 뇌졸중 보장 비교해주세요",
    strategy: "standard"
  }));
};

ws.onmessage = (event) => {
  const chunk = JSON.parse(event.data);

  if (chunk.chunk_type === 'status') {
    console.log(`Status: ${chunk.content} (${chunk.metadata.progress}%)`);
  } else if (chunk.chunk_type === 'complete') {
    console.log('Complete!');
    console.log('Answer:', chunk.content.answer);
    ws.close();
  } else if (chunk.chunk_type === 'error') {
    console.error('Error:', chunk.content);
    ws.close();
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket connection closed');
};
```

### 4. 헬스 체크

```bash
curl http://localhost:8000/api/v1/health
```

**응답**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "query_analyzer": "ok",
    "hybrid_search": "ok",
    "response_generator": "ok",
    "cache": "ok"
  },
  "timestamp": "2025-11-25T20:30:00"
}
```

---

## 🎯 검증 및 품질 보증

### 1. API 테스트
✅ **12개 테스트 구현**
- POST /api/v1/query: 6 tests
- GET /api/v1/query/{id}/status: 1 test
- POST /api/v1/query/async: 1 test
- GET /api/v1/health: 1 test
- GET /api/v1/: 1 test
- Integration: 2 tests

### 2. Request Validation
✅ **Pydantic 자동 검증**
- 필수 필드 검사
- 타입 검증
- 길이 제한 (1-1000자)
- 범위 검증 (1-50 results)

### 3. Error Handling
✅ **표준화된 에러 응답**
- HTTP 상태 코드
- 에러 코드
- 상세 메시지
- 타임스탬프

### 4. API Documentation
✅ **OpenAPI/Swagger 자동 생성**
- `/docs` - Swagger UI
- `/redoc` - ReDoc
- JSON Schema 포함

---

## 🚀 다음 단계

### Story 3.2: Document Upload API (5 points)
```
POST /api/v1/documents/upload
GET  /api/v1/documents/{doc_id}
DELETE /api/v1/documents/{doc_id}
```

### Story 3.3: Authentication & Authorization (5 points)
```
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
```

---

## 📝 결론

### 구현 완료 사항
✅ **API Request/Response 모델** (229 lines)
✅ **Query 엔드포인트** (485 lines)
  - POST /query (동기)
  - POST /query/async (비동기)
  - GET /query/{id}/status (상태)
  - WebSocket /query/ws (스트리밍)
✅ **API 라우터** (64 lines)
✅ **헬스 체크** & **Root 엔드포인트**
✅ **Main App 통합**
✅ **포괄적 테스트** (299 lines, 12 tests)

### Story Points 달성
- **추정**: 5 points
- **실제**: 5 points
- **상태**: ✅ **COMPLETED**

### Epic 3 진행 상황
```
Epic 3: API & Service Layer
├─ Story 3.1: Query API Endpoints (5 pts) ✅
├─ Story 3.2: Document Upload API (5 pts) ⏳ Next
├─ Story 3.3: Authentication & Authorization (5 pts) ⏳
├─ Story 3.4: Rate Limiting & Monitoring (3 pts) ⏳
└─ Story 3.5: API Documentation (3 pts) ⏳

Progress: 5/21 points (24% complete)
```

### 주요 성과
1. **완전한 REST API**: 동기/비동기/스트리밍 지원
2. **Story 2.5 통합**: QueryOrchestrator 완벽 연동
3. **표준화된 인터페이스**: Pydantic 검증, 에러 처리
4. **실시간 통신**: WebSocket 스트리밍
5. **Production-ready**: 헬스 체크, 모니터링 준비

---

## 📚 참고 자료

### 생성된 파일
1. `app/api/v1/models/query.py` (229 lines)
2. `app/api/v1/endpoints/query.py` (485 lines)
3. `app/api/v1/router.py` (64 lines)
4. `app/main.py` (updated)
5. `tests/test_api_query.py` (299 lines)

### API 문서
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

### 테스트 실행
```bash
pytest tests/test_api_query.py -v
```

---

**작성일**: 2025-11-25
**작성자**: Claude (AI Assistant)
**Epic**: Epic 3 - API & Service Layer
**Status**: ✅ Completed - Story 3.1 Done! 🎉
