# InsureGraph Pro 배포 가이드

이 문서는 InsureGraph Pro 애플리케이션을 Vercel(Frontend)과 GCP Cloud Run(Backend)에 배포하는 방법을 설명합니다.

## 목차

1. [사전 요구사항](#사전-요구사항)
2. [Backend 배포 (GCP Cloud Run)](#backend-배포-gcp-cloud-run)
3. [Frontend 배포 (Vercel)](#frontend-배포-vercel)
4. [환경 변수 설정](#환경-변수-설정)
5. [데이터베이스 설정](#데이터베이스-설정)
6. [배포 후 확인](#배포-후-확인)

---

## 사전 요구사항

### 필수 계정
- Google Cloud Platform (GCP) 계정
- Vercel 계정
- GitHub/GitLab 계정 (소스 코드 호스팅)

### 필수 CLI 도구
```bash
# Google Cloud SDK 설치
https://cloud.google.com/sdk/docs/install

# Vercel CLI 설치 (선택사항)
npm install -g vercel
```

### 필수 서비스
- **PostgreSQL** (GCP Cloud SQL 추천)
- **Neo4j** (Neo4j Aura 추천)
- **Redis** (GCP Memorystore 추천)
- **Google Cloud Storage** (파일 저장용)

---

## Backend 배포 (GCP Cloud Run)

### 1. GCP 프로젝트 설정

```bash
# GCP 프로젝트 생성
gcloud projects create insuregraph-pro --name="InsureGraph Pro"

# 프로젝트 설정
gcloud config set project insuregraph-pro

# 필요한 API 활성화
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable redis.googleapis.com
gcloud services enable storage.googleapis.com
```

### 2. Secret Manager에 비밀 정보 저장

```bash
# PostgreSQL 비밀번호
echo -n "your-pg-password" | gcloud secrets create PG_PASSWORD --data-file=-

# JWT Secret Key
echo -n "your-jwt-secret-key" | gcloud secrets create JWT_SECRET_KEY --data-file=-

# Neo4j 비밀번호
echo -n "your-neo4j-password" | gcloud secrets create NEO4J_PASSWORD --data-file=-

# Redis 비밀번호 (선택사항)
echo -n "your-redis-password" | gcloud secrets create REDIS_PASSWORD --data-file=-

# OpenAI API Key
echo -n "your-openai-api-key" | gcloud secrets create OPENAI_API_KEY --data-file=-

# Anthropic API Key
echo -n "your-anthropic-api-key" | gcloud secrets create ANTHROPIC_API_KEY --data-file=-
```

### 3. Cloud SQL (PostgreSQL) 생성

```bash
# Cloud SQL 인스턴스 생성
gcloud sql instances create insuregraph-postgres \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-7680 \
  --region=asia-northeast3 \
  --root-password=your-root-password

# 데이터베이스 생성
gcloud sql databases create insuregraph \
  --instance=insuregraph-postgres

# 사용자 생성
gcloud sql users create insuregraph_user \
  --instance=insuregraph-postgres \
  --password=your-pg-password
```

### 4. Cloud Build를 사용한 배포

#### 4.1 Cloud Build 트리거 설정

```bash
# GitHub/GitLab 저장소 연결
gcloud beta builds triggers create github \
  --name="insuregraph-backend-deploy" \
  --repo-name="InsureGraph-Pro" \
  --repo-owner="your-github-username" \
  --branch-pattern="^main$" \
  --build-config="backend/cloudbuild.yaml"
```

#### 4.2 수동 배포

```bash
# backend 디렉토리로 이동
cd backend

# Cloud Build를 사용하여 배포
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=\
_PG_HOST="10.x.x.x",\
_PG_PORT="5432",\
_PG_DATABASE="insuregraph",\
_PG_USER="insuregraph_user",\
_NEO4J_URI="neo4j+s://your-neo4j-uri",\
_REDIS_HOST="10.x.x.x",\
_OPENAI_API_KEY="",\
_ANTHROPIC_API_KEY=""
```

### 5. Cloud Run 서비스 권한 설정

```bash
# Secret Manager 접근 권한 부여
gcloud projects add-iam-policy-binding insuregraph-pro \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Cloud SQL 클라이언트 권한 부여
gcloud projects add-iam-policy-binding insuregraph-pro \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# Cloud Storage 권한 부여
gcloud projects add-iam-policy-binding insuregraph-pro \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

---

## Frontend 배포 (Vercel)

### 1. Vercel 프로젝트 생성

#### 웹 UI를 통한 배포 (추천)

1. [Vercel](https://vercel.com) 로그인
2. "New Project" 클릭
3. GitHub/GitLab 저장소 선택
4. 프로젝트 설정:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

#### CLI를 통한 배포

```bash
# frontend 디렉토리로 이동
cd frontend

# Vercel 로그인
vercel login

# 프로젝트 배포
vercel --prod
```

### 2. Vercel 환경 변수 설정

Vercel 대시보드에서 Settings > Environment Variables로 이동하여 다음 변수를 추가:

```env
# Backend API URL (Cloud Run URL)
NEXT_PUBLIC_API_BASE_URL=https://insuregraph-backend-xxxxx.a.run.app

# API Version
NEXT_PUBLIC_API_VERSION=v1

# WebSocket URL (선택사항)
NEXT_PUBLIC_WS_URL=wss://insuregraph-backend-xxxxx.a.run.app

# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
CLERK_SECRET_KEY=sk_test_xxxxx
```

### 3. Vercel CLI로 환경 변수 설정

```bash
# 환경 변수 추가
vercel env add NEXT_PUBLIC_API_BASE_URL production
vercel env add NEXT_PUBLIC_API_VERSION production
vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY production
vercel env add CLERK_SECRET_KEY production

# 재배포
vercel --prod
```

---

## 환경 변수 설정

### Backend 환경 변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `PG_HOST` | PostgreSQL 호스트 | `10.x.x.x` or `/cloudsql/project:region:instance` |
| `PG_PORT` | PostgreSQL 포트 | `5432` |
| `PG_DATABASE` | 데이터베이스 이름 | `insuregraph` |
| `PG_USER` | PostgreSQL 사용자 | `insuregraph_user` |
| `PG_PASSWORD` | PostgreSQL 비밀번호 | Secret Manager에서 관리 |
| `NEO4J_URI` | Neo4j 연결 URI | `neo4j+s://xxx.databases.neo4j.io` |
| `NEO4J_USER` | Neo4j 사용자 | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j 비밀번호 | Secret Manager에서 관리 |
| `REDIS_HOST` | Redis 호스트 | `10.x.x.x` |
| `REDIS_PORT` | Redis 포트 | `6379` |
| `REDIS_PASSWORD` | Redis 비밀번호 | Secret Manager에서 관리 (선택사항) |
| `JWT_SECRET_KEY` | JWT 서명 키 | Secret Manager에서 관리 |
| `OPENAI_API_KEY` | OpenAI API 키 | Secret Manager에서 관리 |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | Secret Manager에서 관리 |

### Frontend 환경 변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `NEXT_PUBLIC_API_BASE_URL` | Backend API URL | `https://insuregraph-backend-xxxxx.a.run.app` |
| `NEXT_PUBLIC_API_VERSION` | API 버전 | `v1` |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk Public Key | `pk_test_xxxxx` |
| `CLERK_SECRET_KEY` | Clerk Secret Key | `sk_test_xxxxx` |

---

## 데이터베이스 설정

### 1. PostgreSQL 스키마 초기화

```bash
# Cloud SQL Proxy 설치 (로컬에서 연결용)
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy

# Cloud SQL에 연결
./cloud_sql_proxy -instances=insuregraph-pro:asia-northeast3:insuregraph-postgres=tcp:5432

# 다른 터미널에서 스키마 실행
psql -h localhost -U insuregraph_user -d insuregraph -f backend/migrations/schema.sql
```

### 2. Neo4j 설정

1. [Neo4j Aura](https://neo4j.com/cloud/aura/) 무료 계정 생성
2. 데이터베이스 인스턴스 생성
3. 연결 URI와 비밀번호 저장

### 3. Redis 설정 (GCP Memorystore)

```bash
# Redis 인스턴스 생성
gcloud redis instances create insuregraph-redis \
  --size=1 \
  --region=asia-northeast3 \
  --redis-version=redis_6_x
```

---

## 배포 후 확인

### Backend 헬스 체크

```bash
# Backend API 헬스 체크
curl https://your-backend-url.a.run.app/api/v1/health

# 예상 응답:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "components": {
#     "postgresql": "connected",
#     "neo4j": "connected",
#     "redis": "connected"
#   }
# }
```

### Frontend 접속 확인

```bash
# Frontend 접속
open https://your-frontend.vercel.app
```

### 로그 확인

#### Backend 로그 (GCP)
```bash
# Cloud Run 로그 확인
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=insuregraph-backend" \
  --limit 50 \
  --format json
```

#### Frontend 로그 (Vercel)
Vercel 대시보드 > Deployments > Logs

---

## 트러블슈팅

### Backend 배포 실패

**문제**: Docker 이미지 빌드 실패
```bash
# 로컬에서 Docker 이미지 테스트
cd backend
docker build -t insuregraph-backend .
docker run -p 8080:8080 insuregraph-backend
```

**문제**: Secret Manager 접근 권한 오류
```bash
# Service Account에 권한 부여 확인
gcloud projects get-iam-policy insuregraph-pro \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/secretmanager.secretAccessor"
```

### Frontend 배포 실패

**문제**: 빌드 오류
```bash
# 로컬에서 빌드 테스트
cd frontend
npm install
npm run build
```

**문제**: API 연결 오류
- Backend URL이 올바른지 확인
- CORS 설정 확인 (backend에서 프론트엔드 도메인 허용)

---

## CI/CD 자동화

### GitHub Actions 워크플로우 예시

```yaml
# .github/workflows/deploy-backend.yml
name: Deploy Backend to GCP Cloud Run

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: insuregraph-pro

      - name: Deploy to Cloud Run
        run: |
          cd backend
          gcloud builds submit --config=cloudbuild.yaml
```

---

## 비용 최적화

### Cloud Run
- **최소 인스턴스**: 개발 환경에서는 0으로 설정
- **최대 인스턴스**: 트래픽에 따라 조정 (기본: 10)
- **CPU 할당**: 요청 처리 중에만 CPU 할당

### Cloud SQL
- **자동 백업**: 매일 자동 백업 활성화
- **고가용성**: 프로덕션에만 활성화
- **머신 타입**: 트래픽에 맞게 조정

### Vercel
- **Pro 플랜**: 무료 플랜으로 시작, 필요시 업그레이드
- **이미지 최적화**: Next.js 자동 이미지 최적화 활용
- **Edge Functions**: 자주 사용하는 API는 Edge로 캐싱

---

## 보안 체크리스트

- [ ] Secret Manager에 모든 비밀 정보 저장
- [ ] Cloud Run 서비스에 최소 권한 부여
- [ ] Cloud SQL은 Private IP 사용
- [ ] CORS 설정으로 허용된 도메인만 접근
- [ ] Cloud Armor로 DDoS 보호 활성화
- [ ] SSL/TLS 인증서 자동 갱신 확인
- [ ] 정기적인 보안 패치 및 업데이트

---

## 지원 및 문의

배포 관련 문의사항이 있으시면 GitHub Issues를 통해 문의해주세요.

---

**마지막 업데이트**: 2025-11-27
