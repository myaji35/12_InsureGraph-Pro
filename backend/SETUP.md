# Backend Setup Guide

InsureGraph Pro 백엔드 개발 환경 설정 가이드입니다.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Neo4j 5.x Enterprise
- Redis 7+
- Google Cloud Platform 계정 (GCS 사용)

## 1. 환경 설정

### Python 가상환경 생성

```bash
cd backend
python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 의존성 설치

```bash
pip install -r requirements.txt
```

## 2. 환경 변수 설정

`.env.example` 파일을 복사하여 `.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 파일을 편집하여 실제 값 입력:

```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PASSWORD=your_password
NEO4J_PASSWORD=your_password

# GCP
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json

# API Keys
UPSTAGE_API_KEY=your_upstage_api_key
OPENAI_API_KEY=your_openai_api_key

# JWT
JWT_SECRET_KEY=your_random_secret_key_here
```

## 3. 데이터베이스 마이그레이션

### PostgreSQL

로컬에서 PostgreSQL이 실행 중인지 확인:

```bash
# PostgreSQL 상태 확인
pg_isready

# 데이터베이스 생성
createdb insuregraph

# 마이그레이션 실행
python scripts/run_pg_migrations.py
```

### Neo4j

Neo4j가 실행 중인지 확인:

```bash
# Neo4j 상태 확인 (macOS)
neo4j status

# 마이그레이션 실행
python scripts/run_neo4j_migrations.py
```

## 4. 개발 서버 실행

### FastAPI 서버

```bash
# 개발 모드로 실행 (hot reload 활성화)
uvicorn app.main:app --reload --port 8000

# 또는
python -m app.main
```

서버가 시작되면:
- API 문서: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

### OCR 워커 (백그라운드 프로세스)

별도의 터미널에서 OCR 워커 실행:

```bash
python -m app.services.ingestion.ocr_worker
```

## 5. 테스트 실행

### 전체 테스트

```bash
pytest
```

### 커버리지 포함

```bash
pytest --cov=app --cov-report=html tests/
```

HTML 리포트는 `htmlcov/index.html`에서 확인 가능

### 특정 테스트 파일만 실행

```bash
pytest tests/test_ingestion_job_manager.py
```

### 특정 테스트만 실행

```bash
pytest tests/test_ingestion_job_manager.py::TestJobManager::test_create_job_success
```

## 6. 코드 품질 검사

### Formatting (Black)

```bash
black app/ tests/
```

### Linting (Flake8)

```bash
flake8 app/ tests/
```

### Type Checking (mypy)

```bash
mypy app/
```

## 7. API 사용 예제

### 정책 업로드

```bash
curl -X POST "http://localhost:8000/api/v1/policies/ingest" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@policy.pdf" \
  -F "insurer=삼성생명" \
  -F "product_name=무배당 건강보험"
```

### Job 상태 확인

```bash
curl -X GET "http://localhost:8000/api/v1/policies/ingest/{job_id}/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 8. Docker로 실행 (선택사항)

### Docker 빌드

```bash
docker build -t insuregraph-backend .
```

### Docker 실행

```bash
docker run -p 8000:8000 \
  --env-file .env \
  insuregraph-backend
```

## 9. 개발 워크플로우

### Story 1.1-1.2 구현 완료 ✅

현재 구현된 기능:
- ✅ PDF 업로드 API (`POST /api/v1/policies/ingest`)
- ✅ Job 상태 조회 API (`GET /api/v1/policies/ingest/{job_id}/status`)
- ✅ Job 목록 조회 API (`GET /api/v1/policies/ingest`)
- ✅ GCS 파일 업로드
- ✅ PostgreSQL Job 관리
- ✅ Upstage Document AI 연동
- ✅ 백그라운드 OCR 워커
- ✅ 단위 테스트

### 다음 작업 (Story 1.3: 문서 파싱)

```bash
# Story 1.3 브랜치 생성
git checkout -b feature/story-1.3-document-parsing
```

## 10. 트러블슈팅

### PostgreSQL 연결 오류

```bash
# PostgreSQL 재시작
brew services restart postgresql@15  # macOS
sudo systemctl restart postgresql    # Linux
```

### Neo4j 연결 오류

```bash
# Neo4j 재시작
neo4j restart
```

### GCS 인증 오류

```bash
# GCP 인증 확인
gcloud auth application-default login

# 서비스 계정 키 확인
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

### 포트 충돌

```bash
# 8000 포트 사용 중인 프로세스 확인
lsof -i :8000

# 프로세스 종료
kill -9 <PID>
```

## 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Upstage Document AI](https://upstage.ai/products/document-ai)
- [Google Cloud Storage](https://cloud.google.com/storage/docs/reference/libraries#client-libraries-install-python)

---

**문제가 발생하면 팀 Slack #insuregraph-dev 채널에 문의하세요.**
