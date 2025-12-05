# SmartInsuranceLearner 권장작업 3-4-5 구현 완료

**날짜**: 2025-12-03
**세션**: SmartInsuranceLearner 최적화 및 모니터링 도구 구현

---

## 요약

SmartInsuranceLearner의 권장작업 3, 4, 5번을 구현하여 프로덕션 운영에 필요한 인프라를 완성했습니다.

### 완료된 작업

1. ✅ 보험사별 템플릿 사전 추출 스크립트
2. ✅ 학습 통계 API 엔드포인트 추가
3. ✅ Redis 캐시 모니터링 유틸리티
4. ✅ 병렬 문서 처리 최적화 스크립트

---

## 1. 보험사별 템플릿 사전 추출 스크립트

**파일**: `backend/scripts/extract_insurance_templates.py`

### 기능

- DB에서 보험사별 문서 조회
- 상품 유형별 템플릿 자동 추출
- 템플릿 캐시에 저장
- 추출 통계 및 성공률 리포트

### 사용법

```bash
cd backend

# 모든 보험사 템플릿 추출 (최소 3개 문서 필요)
python scripts/extract_insurance_templates.py

# 실행 결과
# - 보험사별 상품 템플릿 추출
# - 성공률 통계 출력
# - 템플릿 캐시에 자동 저장
```

### 주요 함수

- `extract_all_templates()`: 모든 보험사 템플릿 추출
- `extract_templates_for_insurer(insurer)`: 특정 보험사 템플릿 추출
- `extract_template_for_product(insurer, product_type)`: 특정 상품 템플릿 추출

### 출력 예시

```
================================================================================
Insurance Template Extraction Script
================================================================================
Min documents required per product: 3

Found 3 insurers in DB: ['삼성화재', '삼성생명', 'KB손해보험']

================================================================================
Extracting templates for 삼성화재
================================================================================
Found 5 product types for 삼성화재: ['종신보험', '정기보험', '연금보험', 'CI보험', '건강보험']

✅ Template extracted for 삼성화재 - 종신보험: 15 variables, 87.3% coverage
✅ Template extracted for 삼성화재 - 정기보험: 12 variables, 85.1% coverage

✅ 삼성화재 optimization complete:
   - Products optimized: 3/5
   - Success rate: 60.0%

================================================================================
Overall Statistics
================================================================================
Insurers processed: 3
Total products optimized: 8/15
Success rate: 53.3%
```

### 크론잡 설정 (권장)

주간 또는 월간 자동 실행:

```bash
# crontab -e
# 매주 일요일 오전 2시 실행
0 2 * * 0 cd /path/to/backend && python scripts/extract_insurance_templates.py >> logs/template_extraction.log 2>&1
```

---

## 2. 학습 통계 API 엔드포인트

**파일**: `backend/app/api/v1/endpoints/learning_stats.py`

### 엔드포인트

#### GET `/api/v1/learning/stats`
전체 학습 통계 조회

**응답 예시**:
```json
{
  "status": "success",
  "total_documents": 58,
  "strategy_distribution": {
    "template_learning": 20,
    "incremental_learning": 25,
    "cached_learning": 10,
    "full_learning": 3
  },
  "total_cost_saved": 45.2,
  "average_cost_saving_per_document": 0.78,
  "average_cost_saving_percent": "78.0%"
}
```

#### GET `/api/v1/learning/cache/stats`
Redis 캐시 통계 조회

**응답 예시**:
```json
{
  "status": "success",
  "cached_chunks": 1250,
  "memory_used_mb": 12.5,
  "memory_peak_mb": 15.2,
  "keys_total": 1350,
  "uptime_seconds": 86400,
  "hit_rate": 0.73
}
```

#### POST `/api/v1/learning/cache/clear`
Redis 캐시 삭제

**Parameters**:
- `pattern` (optional): 삭제할 키 패턴 (기본값: `chunk:learned:*`)

**응답 예시**:
```json
{
  "status": "success",
  "pattern": "chunk:learned:*",
  "deleted_count": 1250
}
```

#### GET `/api/v1/learning/strategies`
학습 전략 정보 조회

**응답 예시**:
```json
{
  "status": "success",
  "strategies": [
    {
      "name": "template",
      "priority": 1,
      "cost_saving_percent": "95%",
      "description": "템플릿 매칭 기반 학습 (변수만 처리)",
      "conditions": "템플릿 캐시 존재 + 유사도 80% 이상"
    },
    {
      "name": "incremental",
      "priority": 2,
      "cost_saving_percent": "80-90%",
      "description": "증분 학습 (이전 버전과의 차이만 학습)",
      "conditions": "이전 버전 존재 + 유사도 85% 이상"
    },
    {
      "name": "chunking",
      "priority": 3,
      "cost_saving_percent": "70-80%",
      "description": "의미 기반 청킹 + Redis 캐싱",
      "conditions": "항상 사용 가능 (fallback)"
    }
  ]
}
```

#### GET `/api/v1/learning/templates/{insurer}`
특정 보험사의 템플릿 정보 조회

**응답 예시**:
```json
{
  "status": "success",
  "insurer": "삼성화재",
  "template_count": 3,
  "templates": {
    "종신보험": {
      "coverage_ratio": 0.873,
      "variable_count": 15,
      "template_id": "template_001"
    },
    "정기보험": {
      "coverage_ratio": 0.851,
      "variable_count": 12,
      "template_id": "template_002"
    }
  }
}
```

#### POST `/api/v1/learning/templates/extract/{insurer}`
특정 보험사의 템플릿 추출 트리거

**Parameters**:
- `min_documents` (optional): 최소 문서 수 (기본값: 3)

**응답 예시**:
```json
{
  "status": "success",
  "insurer": "삼성화재",
  "products_optimized": 3,
  "products_total": 5,
  "results": [...]
}
```

#### GET `/api/v1/learning/health`
학습 시스템 헬스 체크

**응답 예시**:
```json
{
  "status": "healthy",
  "redis_status": "connected",
  "learning_system": "operational",
  "total_documents_processed": 58,
  "cache_enabled": true
}
```

### API 라우터 통합

`backend/app/api/v1/router.py`에 추가됨:

```python
from app.api.v1.endpoints import learning_stats

# Learning Statistics endpoints (Smart Insurance Learner monitoring)
api_router.include_router(learning_stats.router, prefix="/learning", tags=["Learning Stats"])
```

### 테스트

```bash
# 학습 통계 조회
curl http://localhost:3030/api/v1/learning/stats | jq

# 캐시 통계 조회
curl http://localhost:3030/api/v1/learning/cache/stats | jq

# 전략 정보 조회
curl http://localhost:3030/api/v1/learning/strategies | jq

# 헬스 체크
curl http://localhost:3030/api/v1/learning/health | jq
```

---

## 3. Redis 캐시 모니터링 유틸리티

**파일**: `backend/scripts/monitor_redis_cache.py`

### 기능

- Redis 연결 상태 확인
- 전체 캐시 통계 조회
- 캐시 효율성 분석
- 캐시 샘플 조회
- 만료된 키 정리
- 종합 모니터링 리포트 생성

### 사용법

```bash
cd backend

# Redis 캐시 모니터링 리포트 출력
python scripts/monitor_redis_cache.py
```

### 출력 예시

```
================================================================================
Redis Cache Monitoring Report
================================================================================
Timestamp: 2025-12-03 14:23:45

[Overall Statistics]
  Status: connected
  Cached chunks: 1250
  Total keys: 1350
  Memory used: 12.52 MB
  Memory peak: 15.23 MB
  Uptime: 24.0 hours
  Connected clients: 3
  Total commands: 45820
  Cache hits: 3240
  Cache misses: 1120
  Hit rate: 74.3%

[Cache Efficiency Analysis]
  Efficiency score: 85/100
  Efficiency grade: B (Good)
  Average key size: 9.48 KB

[Recommendations]
  1. 캐시가 잘 활용되고 있습니다 (1350개 키).
  2. 캐시 적중률이 양호합니다 (74.3%).

[Cache Sample (5 entries)]
  1. Hash: a3f5b8c2d1e6f9a0..., TTL: 28.5 days, Size: 2458 bytes
  2. Hash: b7e3c9a1f5d8e2b4..., TTL: 27.3 days, Size: 3142 bytes
  3. Hash: c2a8f5e9b3d7c1a6..., TTL: 29.1 days, Size: 1987 bytes
  4. Hash: d5c7a2e8f3b9c4d1..., TTL: 26.8 days, Size: 2765 bytes
  5. Hash: e9b4c6a1d8f2e5c3..., TTL: 28.9 days, Size: 2234 bytes

================================================================================
```

### 주요 클래스 및 메서드

```python
class RedisCacheMonitor:
    async def get_overall_stats() -> Dict
    async def get_chunk_samples(limit: int) -> List[Dict]
    async def analyze_cache_efficiency() -> Dict
    async def cleanup_expired_keys() -> int
    async def print_report()
```

### 크론잡 설정 (권장)

일일 모니터링 리포트:

```bash
# crontab -e
# 매일 오전 9시 실행
0 9 * * * cd /path/to/backend && python scripts/monitor_redis_cache.py >> logs/redis_monitor.log 2>&1
```

---

## 4. 병렬 문서 처리 최적화 스크립트

**파일**: `backend/scripts/optimize_parallel_learning.py`

### 기능

- 대기 중인 문서 대량 조회
- SmartInsuranceLearner를 사용한 병렬 학습
- 전략별 통계 수집
- 비용 절감 분석
- 처리 시간 측정
- 실패 문서 추적

### 사용법

```bash
cd backend

# 기본 실행 (100개 문서, 동시 3개 처리)
python scripts/optimize_parallel_learning.py

# 옵션 지정
python scripts/optimize_parallel_learning.py --limit 200 --concurrent 5

# 옵션
#   --limit: 처리할 최대 문서 수 (기본값: 100)
#   --concurrent: 동시 처리 문서 수 (기본값: 3)
```

### 출력 예시

```
================================================================================
Starting parallel processing of 50 documents
Max concurrent: 3
================================================================================

[a3f5b8c2] Processing document: https://www.samsungfire.com/...
[b7e3c9a1] Processing document: https://www.samsunglife.com/...
[c2a8f5e9] Processing document: https://www.kbinsure.co.kr/...

[a3f5b8c2] ✅ Success - Strategy: template, Cost saving: 95%
[b7e3c9a1] ✅ Success - Strategy: incremental, Cost saving: 85%
[c2a8f5e9] ✅ Success - Strategy: chunking, Cost saving: 75%

================================================================================
Parallel Learning Summary
================================================================================

[Processing Time]
  Start: 2025-12-03 14:30:00
  End: 2025-12-03 14:45:30
  Duration: 930.0 seconds (15.5 minutes)
  Average per document: 18.6 seconds

[Processing Statistics]
  Total documents: 50
  Successful: 48
  Failed: 2
  Success rate: 96.0%

[Strategy Distribution]
  Template: 18 (37.5%)
  Incremental: 20 (41.7%)
  Chunking: 8 (16.7%)
  Full: 2 (4.2%)

[Cost Savings]
  Total cost saving: 39.20
  Average per document: 81.7%

[Failed Documents] (2)
  1. https://example.com/doc1.pdf - Extraction failed
  2. https://example.com/doc2.pdf - Timeout

[SmartInsuranceLearner Overall Statistics]
  {'total_documents': 50, 'average_cost_saving_percent': '81.7%', ...}

================================================================================

✅ Optimization completed
```

### 주요 클래스 및 메서드

```python
class ParallelLearningOptimizer:
    async def get_pending_documents(limit: int) -> List[CrawlerDocument]
    async def process_single_document(document: CrawlerDocument) -> Dict
    async def process_documents_in_parallel(documents: List) -> List[Dict]
    def print_summary(results: List[Dict])
    async def optimize(limit: int) -> Dict
```

### 크론잡 설정 (권장)

정기적인 대량 학습 처리:

```bash
# crontab -e
# 매일 오전 3시 실행 (100개 문서, 동시 5개)
0 3 * * * cd /path/to/backend && python scripts/optimize_parallel_learning.py --limit 100 --concurrent 5 >> logs/parallel_learning.log 2>&1
```

---

## 통합 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                   SmartInsuranceLearner 생태계                    │
└─────────────────────────────────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
   ┌────▼────┐          ┌──────▼──────┐      ┌───────▼───────┐
   │  Core   │          │  Monitoring │      │ Optimization  │
   │ System  │          │   & Stats   │      │    Tools      │
   └────┬────┘          └──────┬──────┘      └───────┬───────┘
        │                      │                      │
   ┌────▼────────────┐  ┌──────▼─────────────┐ ┌─────▼─────────┐
   │ SmartLearner    │  │ API Endpoints      │ │ Scripts       │
   │ - Template      │  │ /learning/stats    │ │ - Template    │
   │ - Incremental   │  │ /learning/cache    │ │   Extraction  │
   │ - Chunking      │  │ /learning/health   │ │ - Parallel    │
   │                 │  │ /learning/templates│ │   Learning    │
   └─────────────────┘  └────────────────────┘ └───────────────┘
                               │
                        ┌──────▼──────┐
                        │   Redis     │
                        │   Cache     │
                        └─────────────┘
```

---

## 사용 시나리오

### 시나리오 1: 신규 보험사 문서 대량 처리

```bash
# 1. 템플릿 사전 추출
python scripts/extract_insurance_templates.py

# 2. 병렬 학습 실행
python scripts/optimize_parallel_learning.py --limit 500 --concurrent 10

# 3. 통계 확인
curl http://localhost:3030/api/v1/learning/stats | jq

# 4. 캐시 상태 확인
python scripts/monitor_redis_cache.py
```

### 시나리오 2: 정기 모니터링 및 최적화

```bash
# 1. 학습 시스템 헬스 체크
curl http://localhost:3030/api/v1/learning/health | jq

# 2. 전략별 성능 확인
curl http://localhost:3030/api/v1/learning/stats | jq

# 3. Redis 캐시 효율성 분석
python scripts/monitor_redis_cache.py

# 4. 특정 보험사 템플릿 재추출
curl -X POST http://localhost:3030/api/v1/learning/templates/extract/삼성화재 | jq
```

### 시나리오 3: 캐시 관리

```bash
# 1. 캐시 통계 확인
curl http://localhost:3030/api/v1/learning/cache/stats | jq

# 2. 메모리 사용량 확인
python scripts/monitor_redis_cache.py

# 3. 필요시 캐시 정리
curl -X POST "http://localhost:3030/api/v1/learning/cache/clear?pattern=chunk:learned:*" | jq
```

---

## 예상 효과

### 비용 절감

- **템플릿 매칭**: 95% 절감 (변수만 처리)
- **증분 학습**: 80-90% 절감 (차이만 학습)
- **의미 기반 청킹**: 70-80% 절감 (캐시 활용)
- **전체 평균**: 57-78% 절감

### 시간 단축

- **병렬 처리**: 동시 3-10개 문서 처리
- **캐시 적중**: 즉시 결과 반환
- **전략 자동 선택**: 최적 경로 자동 결정

### 운영 효율화

- **자동 모니터링**: API 엔드포인트로 실시간 확인
- **정기 최적화**: 크론잡으로 자동 실행
- **효율성 분석**: 상세 통계 및 권장사항 제공

---

## 다음 단계 (선택사항)

### 1. 프론트엔드 대시보드 추가

```typescript
// frontend/src/app/admin/learning-stats/page.tsx
- 학습 전략별 분포 차트
- 비용 절감 추이 그래프
- Redis 캐시 상태 모니터링
- 실시간 학습 진행 상황
```

### 2. 알림 시스템 통합

```python
# 캐시 메모리 임계값 초과 시 알림
# 템플릿 추출 실패 시 알림
# 학습 실패율 급증 시 알림
```

### 3. 성능 벤치마크

```bash
# 전략별 실제 비용/시간 측정
# A/B 테스트: SmartLearner vs 기존 방식
# 보험사별 최적 전략 분석
```

---

## 파일 구조

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── router.py                      # [수정] learning_stats 라우터 추가
│   │       └── endpoints/
│   │           └── learning_stats.py          # [신규] 학습 통계 API
│   └── services/
│       ├── parallel_document_processor.py     # [수정] SmartLearner 통합됨
│       └── learning/
│           ├── smart_learner.py               # [기존] 오케스트레이터
│           ├── chunk_learner.py               # [수정] settings import 제거
│           ├── incremental_learner.py         # [기존]
│           └── template_matcher.py            # [기존]
└── scripts/
    ├── extract_insurance_templates.py         # [신규] 템플릿 추출
    ├── monitor_redis_cache.py                 # [신규] 캐시 모니터링
    └── optimize_parallel_learning.py          # [신규] 병렬 학습 최적화
```

---

## 테스트 방법

### 1. API 엔드포인트 테스트

```bash
# 서버 시작
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 3030 --reload

# 별도 터미널에서 테스트
curl http://localhost:3030/api/v1/learning/health | jq
curl http://localhost:3030/api/v1/learning/stats | jq
curl http://localhost:3030/api/v1/learning/strategies | jq
```

### 2. 스크립트 테스트

```bash
# Redis 모니터링
python scripts/monitor_redis_cache.py

# 템플릿 추출 (실제 DB 필요)
python scripts/extract_insurance_templates.py

# 병렬 학습 (실제 DB 필요)
python scripts/optimize_parallel_learning.py --limit 10 --concurrent 2
```

---

## 결론

✅ **필수 작업 완료**:
1. Redis 설치 및 설정 ✅
2. parallel_document_processor.py에 SmartLearner 통합 ✅

✅ **권장 작업 완료**:
3. 보험사별 템플릿 사전 추출 스크립트 ✅
4. 학습 통계 API 엔드포인트 추가 ✅
5. Redis 캐시 모니터링 유틸리티 ✅
6. 병렬 문서 처리 최적화 스크립트 ✅

**SmartInsuranceLearner 시스템이 프로덕션 운영 준비 완료되었습니다!**

---

## 참고 문서

- `SmartInsuranceLearner_구현완료.md`: 전체 시스템 설계 및 구현 문서
- `SESSION_2025-12-02_*.md`: 이전 세션 기록
- `backend/app/services/learning/`: 핵심 학습 모듈
- `backend/scripts/`: 운영 스크립트

---

**작성자**: Claude Code
**날짜**: 2025-12-03
**버전**: 1.0.0
