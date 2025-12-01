# InsureGraph Pro - Deployment Guide

Story 1.1 (PDF Upload & Job Management) 배포 가이드입니다.

## 📋 사전 준비 사항

### 필수 환경

- **Python**: 3.11+
- **PostgreSQL**: 14+
- **Google Cloud Platform**: 활성화된 프로젝트
- **gcloud CLI**: 설치 및 인증 완료
- **psql**: PostgreSQL 클라이언트

### 필수 환경 변수

`backend/.env` 파일에 다음 변수들을 설정하세요:

```bash
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=insuregraph
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password

# Google Cloud Storage
GCP_PROJECT_ID=your-gcp-project-id
GCS_BUCKET_POLICIES=insuregraph-policies-prod
GCS_LOCATION=asia-northeast3  # Seoul region
GCS_STORAGE_CLASS=STANDARD

# Optional: Service Account
GCS_SERVICE_ACCOUNT=insuregraph-storage@your-project.iam.gserviceaccount.com

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## 🚀 배포 단계

### 1. 데이터베이스 마이그레이션 적용

```bash
# 프로젝트 루트에서 실행
./backend/scripts/apply_migration.sh backend/alembic/versions/002_add_ingestion_jobs_table.sql
```

**예상 출력:**
```
Applying migration: backend/alembic/versions/002_add_ingestion_jobs_table.sql
Database: insuregraph
Host: localhost:5432
User: postgres

CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE FUNCTION
CREATE TRIGGER

✓ Migration applied successfully!
```

**검증:**
```bash
PGPASSWORD=$POSTGRES_PASSWORD psql \
  -h $POSTGRES_HOST \
  -U $POSTGRES_USER \
  -d $POSTGRES_DB \
  -c "\dt ingestion_jobs"
```

### 2. GCS 버킷 생성 및 구성

```bash
# 프로젝트 루트에서 실행
./backend/scripts/setup_gcs_bucket.sh
```

**스크립트 실행 내용:**
- GCS 버킷 생성 (이미 존재하면 스킵)
- 버전 관리 활성화
- 라이프사이클 정책 설정 (90일 후 구버전 삭제)
- 균일한 버킷 수준 액세스 활성화
- CORS 정책 구성
- IAM 권한 부여

**필요한 IAM 권한:**
```bash
# 서비스 계정에 다음 역할 부여
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:$GCS_SERVICE_ACCOUNT" \
  --role="roles/storage.objectAdmin"
```

### 3. 서비스 계정 키 생성 (처음 배포 시만)

```bash
# 서비스 계정 생성
gcloud iam service-accounts create insuregraph-storage \
  --display-name="InsureGraph Storage Service" \
  --project=$GCP_PROJECT_ID

# 키 생성 (JSON 형식)
gcloud iam service-accounts keys create \
  backend/credentials/gcs-service-account.json \
  --iam-account=insuregraph-storage@$GCP_PROJECT_ID.iam.gserviceaccount.com

# 환경 변수 설정
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/backend/credentials/gcs-service-account.json
```

### 4. Python 의존성 설치

```bash
cd backend
pip install -r requirements.txt
```

### 5. 애플리케이션 시작

**개발 환경:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**프로덕션 환경 (Gunicorn + Uvicorn):**
```bash
cd backend
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --log-level info
```

### 6. 헬스 체크

```bash
# API 헬스 체크
curl http://localhost:8000/health

# 예상 응답:
# {"status": "healthy", "timestamp": "2025-11-30T..."}
```

## 🧪 테스트

### 단위 테스트 실행

```bash
cd backend
pytest tests/unit/api/test_ingest.py -v
```

**예상 결과:**
```
test_upload_policy_success PASSED
test_upload_policy_invalid_extension PASSED
test_upload_policy_file_too_large PASSED
test_upload_policy_empty_file PASSED
test_upload_policy_invalid_pdf_magic_bytes PASSED
test_upload_policy_unauthorized PASSED
test_upload_policy_forbidden_non_admin PASSED
test_get_job_status_success PASSED
test_get_job_status_not_found PASSED
test_get_job_status_unauthorized PASSED
test_upload_policy_db_failure_cleanup PASSED
test_upload_policy_insurer_required PASSED
test_upload_policy_product_name_required PASSED
```

### 통합 테스트 실행

```bash
cd backend
pytest tests/integration/test_s3_upload.py -v
```

### 전체 테스트 실행

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

## 📊 모니터링 체크리스트

배포 후 다음 사항들을 확인하세요:

### 데이터베이스
- [ ] `ingestion_jobs` 테이블 생성 확인
- [ ] 인덱스 3개 생성 확인 (job_id, status, created_at)
- [ ] Trigger 동작 확인 (updated_at 자동 업데이트)

### GCS 버킷
- [ ] 버킷 생성 확인: `gsutil ls -b gs://$GCS_BUCKET_POLICIES`
- [ ] 버전 관리 활성화 확인: `gsutil versioning get gs://$GCS_BUCKET_POLICIES`
- [ ] 라이프사이클 정책 확인: `gsutil lifecycle get gs://$GCS_BUCKET_POLICIES`
- [ ] IAM 권한 확인: `gsutil iam get gs://$GCS_BUCKET_POLICIES`

### API 엔드포인트
- [ ] POST `/api/v1/policies/ingest` - PDF 업로드
- [ ] GET `/api/v1/policies/ingest/status/{job_id}` - 작업 상태 조회

### 로그 확인
```bash
# 애플리케이션 로그 확인 (GCS 업로드 관련)
tail -f logs/app.log | grep -E "(Uploaded PDF|Failed to upload)"

# PostgreSQL 로그 확인
tail -f /var/log/postgresql/postgresql-14-main.log
```

## 🔒 보안 체크리스트

배포 전 보안 설정을 확인하세요:

- [ ] 서비스 계정 키 파일을 `.gitignore`에 추가
- [ ] 환경 변수 파일 (`.env`)를 `.gitignore`에 추가
- [ ] GCS 버킷에 균일한 버킷 수준 액세스 활성화
- [ ] PostgreSQL 연결에 SSL/TLS 사용 (프로덕션)
- [ ] API 엔드포인트에 JWT 인증 활성화
- [ ] RBAC 권한 확인 (ADMIN, FP_MANAGER만 업로드 가능)
- [ ] CORS 정책 검증 (허용된 도메인만)
- [ ] 파일 크기 제한 확인 (100MB)
- [ ] PDF 매직 바이트 검증 활성화

## 🐛 트러블슈팅

### 문제: 데이터베이스 연결 실패

```bash
# PostgreSQL 서버 상태 확인
sudo systemctl status postgresql

# 연결 테스트
PGPASSWORD=$POSTGRES_PASSWORD psql \
  -h $POSTGRES_HOST \
  -U $POSTGRES_USER \
  -d $POSTGRES_DB \
  -c "SELECT version();"
```

### 문제: GCS 업로드 실패

```bash
# gcloud 인증 확인
gcloud auth list

# 서비스 계정 권한 확인
gcloud projects get-iam-policy $GCP_PROJECT_ID \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:serviceAccount:$GCS_SERVICE_ACCOUNT"

# 버킷 접근 테스트
gsutil ls gs://$GCS_BUCKET_POLICIES
```

### 문제: asyncio.to_thread() 관련 에러

이 문제는 Python 3.9 미만 버전에서 발생합니다:

```bash
# Python 버전 확인
python --version  # 3.11 이상 필요

# 또는 pyenv로 업그레이드
pyenv install 3.11.0
pyenv local 3.11.0
```

### 문제: 테스트 실패

```bash
# 테스트 데이터베이스 초기화
PGPASSWORD=$POSTGRES_PASSWORD psql \
  -h $POSTGRES_HOST \
  -U $POSTGRES_USER \
  -d $POSTGRES_DB \
  -c "TRUNCATE ingestion_jobs RESTART IDENTITY CASCADE;"

# 캐시 삭제 후 재실행
pytest --cache-clear tests/
```

## 📈 성능 최적화

### 데이터베이스
- [ ] Connection pooling 활성화 (PostgreSQLManager에서 이미 구현됨)
- [ ] 인덱스 사용률 모니터링
- [ ] 쿼리 성능 분석 (EXPLAIN ANALYZE)

### GCS 업로드
- [ ] 멀티파트 업로드 활성화 (대용량 파일용)
- [ ] 리전 선택 최적화 (서울: asia-northeast3)
- [ ] CDN 캐싱 (정적 파일용)

### 애플리케이션
- [ ] Uvicorn worker 수 조정 (CPU 코어 수 * 2 + 1)
- [ ] 요청 타임아웃 설정 (120초)
- [ ] 로그 레벨 최적화 (프로덕션: INFO, 디버그: DEBUG)

## 🔄 롤백 절차

문제 발생 시 다음 단계로 롤백하세요:

### 1. 데이터베이스 롤백

```bash
# 테이블 삭제
PGPASSWORD=$POSTGRES_PASSWORD psql \
  -h $POSTGRES_HOST \
  -U $POSTGRES_USER \
  -d $POSTGRES_DB \
  -c "DROP TABLE IF EXISTS ingestion_jobs CASCADE;"
```

### 2. GCS 버킷 정리 (선택사항)

```bash
# 버킷의 모든 객체 삭제
gsutil -m rm -r gs://$GCS_BUCKET_POLICIES/**

# 버킷 삭제
gsutil rb gs://$GCS_BUCKET_POLICIES
```

### 3. 애플리케이션 재시작

```bash
# 프로세스 종료
pkill -f "uvicorn app.main:app"

# 이전 버전으로 체크아웃
git checkout <previous-commit-hash>

# 재시작
uvicorn app.main:app --reload
```

## 📚 참고 자료

- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## 📞 지원

문제가 발생하면 다음 정보를 포함하여 이슈를 생성하세요:

1. 에러 메시지 전체
2. 환경 정보 (OS, Python 버전, PostgreSQL 버전)
3. 재현 단계
4. 관련 로그 파일

---

**배포 완료 체크리스트:**

- [ ] 데이터베이스 마이그레이션 적용 완료
- [ ] GCS 버킷 생성 및 구성 완료
- [ ] 환경 변수 설정 완료
- [ ] 서비스 계정 권한 부여 완료
- [ ] 애플리케이션 시작 완료
- [ ] 헬스 체크 통과
- [ ] 단위 테스트 통과 (13/13)
- [ ] 통합 테스트 통과 (8/8)
- [ ] 보안 체크리스트 완료
- [ ] 모니터링 설정 완료

**Story 1.1 배포 준비 완료!** 🎉
