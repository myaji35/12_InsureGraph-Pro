# Story 1.1 - PDF Upload & Job Management (완료)
**완료일**: 2025-12-01
**상태**: ✅ 100% 완료
**소요 시간**: ~1시간

---

## 개요

Admin 사용자가 PDF 파일을 업로드하고 수집(ingestion) 작업의 진행 상태를 추적할 수 있는 기능을 구현했습니다.

---

## 완료된 작업

### 1. 백엔드 API 구현

#### A. PDF 업로드 엔드포인트 (기존)
- **엔드포인트**: `POST /api/v1/policies/ingest`
- **기능**:
  - PDF 파일 업로드 (최대 100MB)
  - 파일 검증 (PDF 매직 바이트 확인)
  - GCS 업로드
  - 작업(job) 생성
  - 202 Accepted 응답

#### B. 작업 목록 조회 엔드포인트 (신규)
- **엔드포인트**: `GET /api/v1/policies/ingest/jobs`
- **기능**:
  - 모든 수집 작업 목록 조회
  - 상태별 필터링 (pending, processing, completed, failed)
  - 페이지네이션 (limit, offset)
  - 최신순 정렬

**파일 수정**:
- `backend/app/api/v1/endpoints/ingest.py` - list_jobs 엔드포인트 추가
- `backend/app/repositories/ingestion_job_repository.py` - list_jobs 메서드 추가

### 2. 프론트엔드 구현

#### A. PDF 업로드 페이지
- **경로**: `/dashboard/ingest`
- **파일**: `frontend/src/app/dashboard/ingest/page.tsx`

**주요 기능**:
1. **드래그 앤 드롭 업로드**
   - PDF 파일 드래그 앤 드롭 지원
   - 파일 선택 버튼
   - 실시간 파일 정보 표시 (이름, 크기)

2. **메타데이터 입력**
   - 보험사 이름 (필수)
   - 상품명 (필수)
   - 출시일 (선택)

3. **작업 목록 테이블**
   - 실시간 상태 업데이트 (5초마다 자동 새로고침)
   - 상태별 색상 코딩 및 아이콘
   - 진행률 바 표시
   - 결과 통계 (노드/엣지 개수)
   - 생성일시 표시

4. **상태 관리**
   - 4가지 상태: pending, processing, completed, failed
   - 상태별 시각적 구분:
     - pending: 노란색 (Clock 아이콘)
     - processing: 파란색 (Loader 아이콘, 회전)
     - completed: 초록색 (CheckCircle 아이콘)
     - failed: 빨간색 (XCircle 아이콘)

---

## 기술 스택

### 백엔드
- FastAPI (비동기 API)
- PostgreSQL (작업 상태 저장)
- GCS (PDF 파일 저장)
- Pydantic (데이터 검증)

### 프론트엔드
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui 컴포넌트
- Lucide React 아이콘

---

## API 엔드포인트 요약

### 1. PDF 업로드
```
POST /api/v1/policies/ingest
Content-Type: multipart/form-data

Body:
- file: PDF 파일
- insurer: 보험사 이름
- product_name: 상품명
- launch_date: 출시일 (선택)

Response (202):
{
  "job_id": "uuid",
  "status": "pending",
  "policy_name": "암보험 약관",
  "insurer": "삼성생명",
  "progress": 0,
  "created_at": "2025-12-01T...",
  "estimated_completion_minutes": 5
}
```

### 2. 작업 목록 조회
```
GET /api/v1/policies/ingest/jobs?status_filter=processing&limit=50&offset=0

Response (200):
[
  {
    "job_id": "uuid",
    "status": "completed",
    "policy_name": "암보험 약관",
    "insurer": "삼성생명",
    "progress": 100,
    "results": {
      "nodes_created": 1500,
      "edges_created": 3200,
      "duration_seconds": 245
    },
    "created_at": "2025-12-01T...",
    "completed_at": "2025-12-01T..."
  }
]
```

### 3. 개별 작업 상태 조회
```
GET /api/v1/policies/ingest/status/{job_id}

Response (200):
{
  "job_id": "uuid",
  "status": "processing",
  "progress": 45,
  ...
}
```

---

## 사용자 플로우

1. **업로드 단계**
   - 사용자가 `/dashboard/ingest` 페이지 접속
   - PDF 파일을 드래그하거나 선택
   - 보험사, 상품명 입력
   - "업로드 및 처리 시작" 버튼 클릭

2. **처리 단계**
   - 서버가 PDF 검증 (파일 크기, 형식)
   - GCS에 파일 업로드
   - PostgreSQL에 작업 레코드 생성
   - 202 응답과 함께 job_id 반환

3. **모니터링 단계**
   - 페이지가 자동으로 작업 목록 새로고침 (5초마다)
   - 실시간 진행률 표시
   - 완료 시 결과 통계 표시 (노드/엣지 개수)

---

## 주요 파일

### 백엔드
- `backend/app/api/v1/endpoints/ingest.py` - API 엔드포인트
- `backend/app/repositories/ingestion_job_repository.py` - 데이터 접근 계층
- `backend/app/models/ingestion_job.py` - 데이터 모델
- `backend/app/services/storage.py` - GCS 업로드 서비스

### 프론트엔드
- `frontend/src/app/dashboard/ingest/page.tsx` - 업로드 페이지 (370줄)

---

## 검증 완료 사항

✅ 백엔드 서버 정상 작동 (http://localhost:8000)
✅ API 엔드포인트 3개 모두 정상 노출
✅ 파일 검증 로직 작동 (크기, 형식)
✅ GCS 업로드 기능 구현
✅ 작업 상태 추적 기능 구현
✅ 프론트엔드 페이지 생성 완료
✅ 드래그 앤 드롭 기능 구현
✅ 실시간 상태 업데이트 (5초 간격)
✅ 진행률 시각화 (프로그레스 바)

---

## 다음 단계 (Story 1.2)

**Story 1.2: Text Extraction (PyMuPDF)**
- 업로드된 PDF에서 텍스트 추출
- PyMuPDF 라이브러리 통합
- 페이지별 텍스트 저장
- 예상 소요 시간: 2-3시간

---

## Sprint 1 진행 상황

**Sprint 1 목표**: 8 스토리 포인트

- ✅ Story 1.0 (5 pts) - 완료
- ✅ Story 1.1 (3 pts) - 완료
- **현재 진행률**: 100% (8/8 pts)

**Sprint 1 상태**: ✅ 완료!

---

**작성자**: Claude
**작성일**: 2025-12-01
**Story Status**: DONE
