# Session Summary: Database Connection Fix (2025-12-02)

## Problem Solved

Fixed the server startup error that was preventing the document crawler feature from working.

### Original Error
```
File "/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro/backend/app/services/document_crawler_service.py", line 11, in <module>
from app.core.database import get_pg_connection
```

Server would not start due to incorrect database connection usage pattern.

## Root Cause

The code was trying to use `get_pg_connection()` as if it returned a direct database connection, but it's actually a **generator function** designed for FastAPI dependency injection with synchronous psycopg2.

Additionally, the code was using `await conn.fetch()` which is an **asyncpg pattern**, but `get_pg_connection()` returns a **psycopg2 connection** (synchronous).

## Solution

Refactored the code to use **SQLAlchemy's AsyncSession** with proper FastAPI dependency injection pattern.

## Files Modified

### 1. `backend/app/services/document_crawler_service.py`

**Changes:**
- Added SQLAlchemy imports: `AsyncSession`, `text`
- Removed import of `get_pg_connection`
- Modified `__init__` to accept `db: AsyncSession` parameter
- Updated `_get_crawler_urls()` to use SQLAlchemy `text()` queries
- Updated `save_crawled_documents()` to use SQLAlchemy with commit

**Before:**
```python
from app.core.database import get_pg_connection

class DocumentCrawlerService:
    def __init__(self):
        self.pdf_extractor = AIPdfExtractor()

    async def _get_crawler_urls(self, insurer: str) -> List[str]:
        conn = get_pg_connection()
        rows = await conn.fetch(...)
```

**After:**
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

class DocumentCrawlerService:
    def __init__(self, db: AsyncSession):
        self.pdf_extractor = AIPdfExtractor()
        self.db = db

    async def _get_crawler_urls(self, insurer: str) -> List[str]:
        query = text("""
            SELECT url
            FROM crawler_urls
            WHERE insurer = :insurer AND enabled = true
            ORDER BY created_at DESC
        """)
        result = await self.db.execute(query, {"insurer": insurer})
        rows = result.fetchall()
        urls = [row.url for row in rows]
```

### 2. `backend/app/api/v1/endpoints/crawler_documents.py`

**Changes:**
- Added imports: `Depends`, `AsyncSession`, `text`
- Added import of `get_db` from database module
- Updated POST `/crawl-documents` endpoint to inject `db: AsyncSession = Depends(get_db)`
- Pass db session to `DocumentCrawlerService(db=db)`
- Updated GET `/documents` endpoint to use SQLAlchemy queries

**Before:**
```python
@router.post("/crawl-documents", response_model=CrawlResultResponse)
async def crawl_documents(
    background_tasks: BackgroundTasks,
    insurer: str = Query(..., description="보험사명")
):
    crawler_service = DocumentCrawlerService()
    ...

@router.get("/documents", response_model=DocumentListResponse)
async def list_crawler_documents(...):
    from app.core.database import get_pg_connection
    conn = get_pg_connection()
    rows = await conn.fetch(query, ...)
```

**After:**
```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

@router.post("/crawl-documents", response_model=CrawlResultResponse)
async def crawl_documents(
    background_tasks: BackgroundTasks,
    insurer: str = Query(..., description="보험사명"),
    db: AsyncSession = Depends(get_db)
):
    crawler_service = DocumentCrawlerService(db=db)
    ...

@router.get("/documents", response_model=DocumentListResponse)
async def list_crawler_documents(
    ...,
    db: AsyncSession = Depends(get_db)
):
    query = text(f"""
        SELECT ...
        FROM crawler_documents
        WHERE {where_clause}
        LIMIT :limit OFFSET :offset
    """)
    result = await db.execute(query, params)
    rows = result.fetchall()
```

## Verification

### Server Status
✅ Server starts successfully on port 3030
✅ No import errors
✅ All modules load correctly

### API Endpoints Registered
```bash
$ curl -s http://localhost:3030/openapi.json | python3 -m json.tool | grep "/api/v1/crawler"
```

Confirmed endpoints:
- ✅ `POST /api/v1/crawler/crawl-documents` - Trigger document crawling
- ✅ `GET /api/v1/crawler/documents` - List crawled documents
- ✅ `POST /api/v1/crawler/urls` - Manage crawler URLs
- ✅ `GET /api/v1/crawler/urls` - List crawler URLs
- ✅ `PUT /api/v1/crawler/urls/{url_id}` - Update crawler URL
- ✅ `DELETE /api/v1/crawler/urls/{url_id}` - Delete crawler URL

### Test Data
Added MetLife crawler URL for testing:
```sql
INSERT INTO crawler_urls (insurer, url, description, enabled) VALUES
('메트라이프생명', 'https://brand.metlife.co.kr/pn/mcvrgProd/retrieveMcvrgProdMain.do', '약관정보', true);
```

## Key Learnings

### FastAPI Database Patterns

**❌ Incorrect Pattern:**
```python
# Module-level connection call
from app.core.database import get_pg_connection
conn = get_pg_connection()  # This is a generator!

# Then trying to use await
rows = await conn.fetch(...)  # Won't work!
```

**✅ Correct Pattern:**
```python
# Use dependency injection
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

@router.post("/endpoint")
async def my_endpoint(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT ..."), params)
    rows = result.fetchall()
```

### SQLAlchemy vs AsyncPG Patterns

**AsyncPG style** (not used in this project):
```python
rows = await conn.fetch("SELECT * FROM table WHERE id = $1", id)
value = rows[0]['column_name']
```

**SQLAlchemy style** (used in this project):
```python
from sqlalchemy import text

query = text("SELECT * FROM table WHERE id = :id")
result = await db.execute(query, {"id": id})
rows = result.fetchall()
value = rows[0].column_name  # Access via attribute, not dict
```

## Next Steps

1. ✅ Server startup error - **FIXED**
2. ⏳ Test crawler functionality with frontend "문서 업데이트" button
3. ⏳ Verify PDF links are extracted and classified correctly
4. ⏳ Connect frontend document list to real crawler_documents data
5. ⏳ Implement learned/unlearned document sorting

## Architecture Overview

```
Frontend (Next.js)
    ↓
[문서 업데이트 버튼] clicks
    ↓
POST /api/v1/crawler/crawl-documents?insurer=메트라이프생명
    ↓
DocumentCrawlerService (with SQLAlchemy AsyncSession)
    ↓
├─→ Fetch crawler_urls from DB
├─→ PlaywrightCrawler (crawl each URL)
│   └─→ Wait 3 seconds, extract HTML
├─→ AIPdfExtractor (AI classification)
│   ├─→ Parse HTML with BeautifulSoup
│   ├─→ Filter PDF links
│   └─→ OpenAI GPT-4o-mini classification
│       └─→ Returns: {title, category, product_type, is_relevant}
└─→ Save to crawler_documents table
    └─→ ON CONFLICT (pdf_url) DO UPDATE

Frontend displays: "N개 문서 발견"
```

## Database Schema

### `crawler_documents` table
- `id` (UUID PK)
- `insurer` (보험사명)
- `title` (문서 제목)
- `pdf_url` (UNIQUE - PDF URL)
- `category` (약관/특약)
- `product_type` (종신보험, 정기보험, etc.)
- `source_url` (원본 페이지 URL)
- `status` (pending/downloaded/processed/failed)
- `file_path` (다운로드된 파일 경로)
- `error_message` (에러 메시지)
- `metadata` (JSONB)
- `created_at`, `updated_at`

**Indexes:**
- `insurer`, `status`, `category`, `product_type`, `created_at DESC`

## Status

✅ **Server startup issue resolved**
✅ **Database connection pattern fixed**
✅ **All endpoints registered and accessible**
🎯 **Ready for functional testing**

---

**Session End Time:** 2025-12-02 10:46 KST
**Next Session:** Test crawler functionality and frontend integration
