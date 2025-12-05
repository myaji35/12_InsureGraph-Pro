# 세션 요약: 문서 크롤링 기능 구현 (2025-12-02)

## 📋 세션 목표

사용자 요청: "크롤링 설정 우측 옆에 [문서 업데이트] 버튼을 두고 크롤링 정보에 따라 문서 목록을 업데이트. Playwright + AI를 이용한 HTML 파일 분석으로 약관/특약에 대한 PDF 파일 링크 목록 수집"

## ✅ 완료된 작업

### 1. 프론트엔드 UI 수정

**파일**: `frontend/src/components/dashboard/InsurerDetailView.tsx`

- "문서 업데이트" 버튼 추가 (크롤링 설정 버튼 옆)
- 크롤링 중 상태 표시 (`isCrawling` state)
- API 호출: `POST /api/v1/crawler/crawl-documents?insurer={보험사명}`
- 성공/실패 토스트 메시지 표시

**변경 사항**:
```typescript
// Import 추가
import { RefreshCw } from "lucide-react";
import { showSuccess, showError, showInfo } from "@/lib/toast-config";

// 버튼 추가
<Button
  variant="default"
  size="sm"
  onClick={handleUpdateDocuments}
  disabled={isCrawling}
  className="bg-blue-600 hover:bg-blue-700"
>
  <RefreshCw className={`h-4 w-4 mr-1 ${isCrawling ? "animate-spin" : ""}`} />
  {isCrawling ? "크롤링 중..." : "문서 업데이트"}
</Button>
```

### 2. 데이터베이스 스키마

**파일**: `backend/alembic/versions/005_add_crawler_documents_table.sql`

**테이블**: `crawler_documents`

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | UUID | 문서 고유 ID (Primary Key) |
| insurer | VARCHAR(255) | 보험사명 |
| title | TEXT | 문서 제목 |
| pdf_url | TEXT | PDF 파일 URL (UNIQUE) |
| category | VARCHAR(50) | 문서 카테고리 (약관/특약) |
| product_type | VARCHAR(100) | 상품 유형 (종신보험, 정기보험 등) |
| source_url | TEXT | 크롤링한 원본 페이지 URL |
| status | VARCHAR(50) | 처리 상태 (pending, downloaded, processed, failed) |
| file_path | TEXT | 다운로드한 파일 경로 |
| error_message | TEXT | 에러 메시지 (있는 경우) |
| metadata | JSONB | 추가 메타데이터 |
| created_at | TIMESTAMP | 생성 시간 |
| updated_at | TIMESTAMP | 수정 시간 |

**인덱스**:
- `idx_crawler_documents_insurer` (insurer)
- `idx_crawler_documents_status` (status)
- `idx_crawler_documents_category` (category)
- `idx_crawler_documents_product_type` (product_type)
- `idx_crawler_documents_created_at` (created_at DESC)

**마이그레이션 실행**:
```bash
psql -h localhost -U gangseungsig -d insuregraph -f backend/alembic/versions/005_add_crawler_documents_table.sql
```
상태: ✅ 완료

### 3. AI 기반 PDF 링크 추출 서비스

**파일**: `backend/app/services/ai_pdf_extractor.py`

**클래스**: `AIPdfExtractor`

**주요 기능**:
1. **HTML 파싱**: BeautifulSoup4로 HTML에서 모든 링크 추출
2. **PDF 링크 필터링**: `.pdf` 포함 또는 `download` 키워드가 있는 링크 선별
3. **AI 분류**: OpenAI GPT-4o-mini를 사용하여 링크를 다음과 같이 분류
   - 문서 제목 (한국어, 간결)
   - 카테고리 (약관/특약)
   - 상품 유형 (종신보험, 정기보험, 연금보험, CI보험, 건강보험, 저축보험 등)
   - 관련성 판단 (보험약관/특약 문서인지 여부)
4. **Fallback**: AI 실패 시 키워드 기반 분류

**의존성**:
- `beautifulsoup4` ✅ 설치됨
- `openai` ✅ 설치됨

**AI 프롬프트 예시**:
```
당신은 {보험사} 보험사의 약관 문서를 분류하는 전문가입니다.

각 링크를 분석하여 다음 정보를 JSON 배열 형식으로 출력해주세요:

{
  "documents": [
    {
      "index": 링크 번호,
      "title": "문서 제목",
      "category": "약관" 또는 "특약",
      "product_type": "상품 유형",
      "is_relevant": true/false
    }
  ]
}
```

### 4. Playwright + AI 통합 크롤러 서비스

**파일**: `backend/app/services/document_crawler_service.py`

**클래스**: `DocumentCrawlerService`

**주요 메서드**:

1. **`crawl_insurer_documents(insurer, urls=None)`**
   - 보험사의 문서를 크롤링
   - `crawler_urls` 테이블에서 활성화된 URL 목록 가져오기
   - 각 URL에 대해 Playwright로 페이지 크롤링
   - AI PDF 추출기로 PDF 링크 수집
   - 결과 반환: `{total_urls, total_documents, documents}`

2. **`_get_crawler_urls(insurer)`**
   - DB에서 해당 보험사의 활성화된 크롤링 URL 목록 조회

3. **`save_crawled_documents(documents)`**
   - 크롤링한 문서를 `crawler_documents` 테이블에 저장
   - `ON CONFLICT (pdf_url) DO UPDATE` - 중복 시 업데이트

**워크플로우**:
```
1. 사용자가 "문서 업데이트" 버튼 클릭
2. Frontend → POST /api/v1/crawler/crawl-documents?insurer=메트라이프생명
3. Backend:
   a. DocumentCrawlerService 초기화
   b. crawler_urls 테이블에서 URL 목록 조회
   c. 각 URL에 대해:
      - PlaywrightCrawler로 HTML 다운로드 (3초 대기)
      - AIPdfExtractor로 PDF 링크 추출 및 AI 분류
   d. crawler_documents 테이블에 저장
4. Frontend: 성공 메시지 표시 (N개 문서 발견)
```

### 5. API 엔드포인트

**파일**: `backend/app/api/v1/endpoints/crawler_documents.py`

**Router Prefix**: `/crawler`

**엔드포인트**:

#### 1. POST `/crawler/crawl-documents`
- **설명**: 특정 보험사의 문서를 크롤링
- **Query Params**: `insurer` (필수) - 보험사명
- **응답 모델**: `CrawlResultResponse`
  ```json
  {
    "message": "메트라이프생명의 문서 크롤링이 완료되었습니다.",
    "total_urls": 1,
    "total_documents": 45,
    "saved_documents": 45,
    "documents": [...]
  }
  ```

#### 2. GET `/crawler/documents`
- **설명**: 크롤링한 문서 목록 조회
- **Query Params**:
  - `insurer` (선택) - 보험사명
  - `category` (선택) - 카테고리 (약관/특약)
  - `status` (선택) - 상태 (pending/downloaded/processed/failed)
  - `limit` (기본 100) - 최대 결과 수
  - `offset` (기본 0) - 오프셋
- **응답 모델**: `DocumentListResponse`
  ```json
  {
    "total": 100,
    "items": [
      {
        "id": "uuid",
        "insurer": "메트라이프생명",
        "title": "무배당 하이라이프종신보험 약관",
        "pdf_url": "https://...",
        "category": "약관",
        "product_type": "종신보험",
        "source_url": "https://...",
        "status": "pending",
        "created_at": "2025-12-02T...",
        "updated_at": "2025-12-02T..."
      }
    ]
  }
  ```

**Router 등록**:
```python
# backend/app/api/v1/router.py
from app.api.v1.endpoints import crawler_documents
api_router.include_router(crawler_documents.router)
```

## ⚠️ 현재 이슈

### 서버 시작 에러

**문제**: 서버 시작 시 import 에러 발생

**에러 메시지**:
```
File "/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro/backend/app/services/document_crawler_service.py", line 11, in <module>
```

**원인 추정**:
1. `get_pg_connection()` 함수 호출 방식이 잘못되었을 가능성
2. AsyncPG connection을 동기적으로 사용하려는 시도

**해결 방법 (다음 세션)**:

1. **Option 1: Dependency Injection 사용**
   ```python
   # crawler_documents.py
   from app.core.database import get_db
   from fastapi import Depends
   from sqlalchemy.ext.asyncio import AsyncSession

   @router.post("/crawl-documents")
   async def crawl_documents(
       insurer: str,
       db: AsyncSession = Depends(get_db)
   ):
       # db 사용
   ```

2. **Option 2: AsyncPG Pool 직접 사용**
   ```python
   # document_crawler_service.py
   from app.core.database import pg_pool

   async def _get_crawler_urls(self, insurer: str):
       async with pg_pool.acquire() as conn:
           rows = await conn.fetch(...)
   ```

3. **Option 3: 전역 connection 대신 매개변수로 전달**
   ```python
   async def crawl_insurer_documents(
       self,
       insurer: str,
       conn  # connection을 매개변수로 받기
   ):
       # ...
   ```

## 📂 생성된 파일 목록

### Backend
1. `backend/alembic/versions/005_add_crawler_documents_table.sql` - 데이터베이스 마이그레이션
2. `backend/app/services/ai_pdf_extractor.py` - AI 기반 PDF 링크 추출 서비스
3. `backend/app/services/document_crawler_service.py` - Playwright + AI 통합 크롤러
4. `backend/app/api/v1/endpoints/crawler_documents.py` - API 엔드포인트

### Frontend
- `frontend/src/components/dashboard/InsurerDetailView.tsx` - 수정됨 (문서 업데이트 버튼 추가)

## 🔧 수정된 파일 목록

### Backend
1. `backend/app/api/v1/router.py` - crawler_documents router 추가
2. `backend/app/services/document_crawler_service.py` - `get_pg_pool` → `get_pg_connection` 변경 시도

### Frontend
1. `frontend/src/components/dashboard/InsurerDetailView.tsx` - 완전 수정

## 🎯 다음 세션 작업

### 우선순위 1: 서버 에러 수정
1. database.py의 connection 관리 방식 확인
2. DocumentCrawlerService의 DB 접근 방식 수정
3. 서버 시작 테스트

### 우선순위 2: 크롤링 테스트
1. 메트라이프생명 크롤링 URL 등록
   ```sql
   INSERT INTO crawler_urls (insurer, url, description, enabled) VALUES
   ('메트라이프생명', 'https://brand.metlife.co.kr/pn/mcvrgProd/retrieveMcvrgProdMain.do', '약관정보', true);
   ```
2. "문서 업데이트" 버튼 클릭 테스트
3. 크롤링 결과 확인
4. `crawler_documents` 테이블 데이터 확인

### 우선순위 3: 프론트엔드 문서 목록 연동
1. InsurerDetailView에서 실제 DB 데이터 로드
2. 학습 완료 / 미학습 문서 소팅
3. 카테고리별 필터링 (약관/특약)

### 우선순위 4: PDF 다운로드 및 학습 파이프라인
1. 크롤링된 PDF URL에서 파일 다운로드
2. 기존 ingestion workflow와 연동
3. 문서 상태 업데이트 (pending → downloaded → processed)

## 📦 필요한 패키지

이미 설치됨:
- ✅ `beautifulsoup4` - HTML 파싱
- ✅ `openai` - AI PDF 분류
- ✅ `playwright` - 웹 크롤링 (chromium 브라우저 포함)

## 💡 참고사항

### 크롤링 URL 예시
```sql
-- 메트라이프생명
INSERT INTO crawler_urls (insurer, url, description, enabled) VALUES
('메트라이프생명', 'https://brand.metlife.co.kr/pn/mcvrgProd/retrieveMcvrgProdMain.do', '약관정보', true);

-- 삼성생명
INSERT INTO crawler_urls (insurer, url, description, enabled) VALUES
('삼성생명', 'https://www.samsunglife.com/customer/info/custerms/retrieveTermsList.do', '약관 목록', true);
```

### 환경 변수 필요
```env
# .env
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1  # 선택사항
```

### Playwright 브라우저 설치 확인
```bash
playwright install chromium
```

## 🔍 디버깅 팁

### 서버 에러 상세 확인
```bash
cd backend
python -c "from app.services.document_crawler_service import DocumentCrawlerService"
```

### 데이터베이스 확인
```bash
psql -h localhost -U gangseungsig -d insuregraph
\d crawler_documents
SELECT * FROM crawler_documents;
```

### API 테스트
```bash
# 크롤링 시작
curl -X POST "http://localhost:3030/api/v1/crawler/crawl-documents?insurer=메트라이프생명"

# 문서 목록 조회
curl "http://localhost:3030/api/v1/crawler/documents?insurer=메트라이프생명&limit=10"
```

## 📊 진행 상황 요약

| 작업 | 상태 | 비고 |
|------|------|------|
| 프론트엔드 UI | ✅ 완료 | 문서 업데이트 버튼 추가 |
| 데이터베이스 스키마 | ✅ 완료 | crawler_documents 테이블 생성 |
| AI PDF 추출 서비스 | ✅ 완료 | ai_pdf_extractor.py |
| Playwright 크롤러 서비스 | ✅ 완료 | document_crawler_service.py |
| API 엔드포인트 | ✅ 완료 | crawler_documents.py |
| Router 등록 | ✅ 완료 | router.py 수정 |
| 서버 시작 테스트 | ❌ 실패 | Import 에러 |
| 크롤링 기능 테스트 | ⏳ 대기 | 서버 에러 해결 후 |
| 프론트엔드 데이터 연동 | ⏳ 대기 | |
| 문서 소팅 기능 | ⏳ 대기 | |

---

**세션 종료 시간**: 2025-12-02 10:38 (KST)
**다음 세션 시작점**: 서버 import 에러 수정 (database connection 방식 변경)
