# InsureGraph Pro - Coolify 배포 가이드

## 🎯 Coolify 접속 정보
- **Coolify URL**: http://58.225.113.125
- **서버 IP**: 58.225.113.125

## ⚠️ 포트 충돌 방지
서버에 nginx와 다른 시스템이 이미 설치되어 있으므로, Coolify는 자동으로 사용 가능한 포트를 할당합니다.
- Coolify는 기본적으로 리버스 프록시를 사용하여 포트 충돌을 방지합니다
- 각 서비스는 내부 Docker 네트워크에서 격리되어 실행됩니다
- 외부 접근은 Coolify가 자동으로 할당한 포트나 도메인을 통해 이루어집니다

**권장 포트 설정** (Coolify UI에서 수동 지정 시):
- Frontend: 18000 (기본 3000 대신)
- Backend API: 18001 (기본 8000 대신)
- Neo4j Browser: 17474 (기본 7474 대신)

---

## 📋 배포 단계

### Step 1: Coolify 대시보드 접속

```bash
# 브라우저에서 접속
open http://58.225.113.125
```

Coolify 로그인 페이지가 나타납니다.

---

### Step 2: 새 프로젝트 생성

1. **Dashboard** → **New Project** 클릭
2. 프로젝트 이름: `InsureGraph Pro`
3. 프로젝트 설명: `AI-powered Insurance Graph RAG Platform`
4. **Create** 클릭

---

### Step 3: Git Repository 연결

#### Option 1: GitHub Repository 연결 (권장)

1. **Add New Resource** → **Git Repository**
2. Repository URL: GitHub 주소 입력
   - 예: `https://github.com/YOUR_USERNAME/InsureGraph-Pro`
3. Branch: `main`
4. **Connect** 클릭

#### Option 2: 로컬 파일 직접 업로드

Coolify는 Git 연동을 권장하므로, 먼저 GitHub에 푸시하는 것이 좋습니다:

```bash
cd "/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro"

# GitHub에 푸시 (이미 설정되어 있다면 스킵)
git add .
git commit -m "Add Coolify deployment configuration"
git push origin main
```

---

### Step 4: 서비스 생성

#### 4.1 Backend API 서비스

1. **Add Service** → **Docker Compose**
2. 설정:
   - **Name**: `insuregraph-backend`
   - **Docker Compose File**: `docker-compose.coolify.yml`
   - **Service**: `backend`
   - **Internal Port**: `8080` (컨테이너 내부 포트)
   - **Public Port**: `18001` (nginx 충돌 방지를 위해 18001 사용)
3. **Domain 설정** (선택사항):
   - Custom Domain: `api.yourdomain.com`
   - 또는 Coolify 자동 도메인 사용
4. **Environment Variables** 추가:
   - `.coolify.env` 파일의 내용을 복사해서 붙여넣기
5. **Create** 클릭

#### 4.2 Frontend 서비스

1. **Add Service** → **Docker Compose**
2. 설정:
   - **Name**: `insuregraph-frontend`
   - **Docker Compose File**: `docker-compose.coolify.yml`
   - **Service**: `frontend`
   - **Internal Port**: `3000` (컨테이너 내부 포트)
   - **Public Port**: `18000` (nginx 충돌 방지를 위해 18000 사용)
3. **Domain 설정**:
   - Custom Domain: `yourdomain.com`
   - 또는 Coolify 자동 도메인 사용
4. **Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL=http://58.225.113.125:18001
   # 또는 도메인 사용 시
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com
   ```
5. **Create** 클릭

#### 4.3 Database 서비스들

**PostgreSQL**:
1. **Add Service** → **Database** → **PostgreSQL**
2. 설정:
   - **Name**: `insuregraph-postgres`
   - **Version**: `15`
   - **Database Name**: `insuregraph`
   - **Username**: `insuregraph_user`
   - **Password**: `.coolify.env`에서 복사
3. **Create** 클릭

**Redis**:
1. **Add Service** → **Database** → **Redis**
2. 설정:
   - **Name**: `insuregraph-redis`
   - **Version**: `7`
3. **Create** 클릭

**Neo4j**:
1. **Add Service** → **Custom Docker**
2. 설정:
   - **Name**: `insuregraph-neo4j`
   - **Image**: `neo4j:5.14`
   - **Internal Ports**: `7474,7687`
   - **Public Port (Browser)**: `17474` (nginx 충돌 방지를 위해 17474 사용)
   - **Public Port (Bolt)**: `17687` (nginx 충돌 방지를 위해 17687 사용)
   - **Environment Variables**:
     ```
     NEO4J_AUTH=neo4j/Neo4j2024!Graph!Secure
     NEO4J_PLUGINS=["apoc"]
     NEO4J_dbms_security_procedures_unrestricted=apoc.*
     ```
3. **Create** 클릭

**⚠️ 포트 매핑 확인**:
- Neo4j Browser를 사용할 때는 `http://58.225.113.125:17474` 로 접속
- Backend에서 Neo4j Bolt 연결 시 환경변수에 `NEO4J_URI=bolt://insuregraph-neo4j:7687` 사용 (내부 네트워크)

---

### Step 5: 환경변수 설정

각 서비스의 **Environment** 탭에서 환경변수를 설정하세요.

#### Backend 환경변수

```env
# Database
POSTGRES_HOST=insuregraph-postgres
POSTGRES_PORT=5432
POSTGRES_DB=insuregraph
POSTGRES_USER=insuregraph_user
POSTGRES_PASSWORD=InsureGraph2024!Prod!Secure

# Redis
REDIS_HOST=insuregraph-redis
REDIS_PORT=6379

# Neo4j
NEO4J_URI=bolt://insuregraph-neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=Neo4j2024!Graph!Secure

# Security
SECRET_KEY=7K8mNpQ3rT9vX2bC5dF6gH8jK0lM4nP7qR9sT2uV5wX8yZ
JWT_SECRET_KEY=3aB5cD7eF9gH2iJ4kL6mN8oP0qR2sT4uV6wX8yZ1aB3cD5

# API Keys - Replace with your actual keys
UPSTAGE_API_KEY=your-upstage-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=http://58.225.113.125:18000
```

#### Frontend 환경변수

```env
NEXT_PUBLIC_API_URL=http://58.225.113.125:18001
NODE_ENV=production
```

---

### Step 6: 배포 시작

1. **Backend 서비스**로 이동
2. **Deploy** 버튼 클릭
3. 빌드 로그 확인 (5-10분 소요)
4. **Frontend 서비스**로 이동
5. **Deploy** 버튼 클릭
6. 빌드 로그 확인 (3-5분 소요)

---

### Step 7: 데이터베이스 마이그레이션

배포가 완료되면 마이그레이션 실행:

1. **Backend 서비스** → **Terminal** 탭
2. 터미널에서 실행:
```bash
alembic upgrade head
```

---

## 🌐 접속 URL (포트 충돌 방지 버전)

배포가 완료되면:

- **Frontend**:
  - Coolify 도메인: `https://insuregraph-frontend.coolify.yourdomain.com`
  - IP 접속: `http://58.225.113.125:18000` ⚠️ (기본 3000 대신 18000 사용)

- **Backend API**:
  - Coolify 도메인: `https://insuregraph-backend.coolify.yourdomain.com`
  - IP 접속: `http://58.225.113.125:18001` ⚠️ (기본 8000 대신 18001 사용)

- **API Docs**:
  - `http://58.225.113.125:18001/docs`

- **Neo4j Browser**:
  - `http://58.225.113.125:17474` ⚠️ (기본 7474 대신 17474 사용)
  - Username: `neo4j`
  - Password: `Neo4j2024!Graph!Secure`

**포트 변경 이유**: nginx와 다른 시스템이 이미 설치되어 있어 기본 포트(3000, 8000, 7474)와 충돌하지 않도록 18xxx 대역 포트를 사용합니다.

---

## 🔧 Coolify 유용한 기능

### 자동 배포 (CI/CD)

1. **Settings** → **Deployments**
2. **Auto Deploy on Git Push** 활성화
3. GitHub Webhook이 자동으로 설정됩니다

이제 `git push`만 하면 자동으로 배포됩니다!

### 로그 확인

1. 서비스 선택
2. **Logs** 탭
3. 실시간 로그 확인

### 리소스 모니터링

1. **Dashboard**
2. CPU, 메모리, 디스크 사용량 확인

### 백업 설정

1. **Database 서비스** 선택
2. **Backups** 탭
3. **Enable Automatic Backups**
4. 백업 주기 설정 (예: 매일, 매주)

---

## 🚀 빠른 시작 (요약)

Coolify가 이미 설치되어 있다면:

### 1. GitHub 레포지토리 준비

```bash
cd "/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro"

# 변경사항 커밋
git add .
git commit -m "Add Coolify deployment files"
git push origin main
```

### 2. Coolify에서 프로젝트 생성

1. http://58.225.113.125 접속
2. **New Project** → `InsureGraph Pro`
3. **Add Resource** → **Git Repository**
4. GitHub 레포지토리 연결

### 3. 서비스 배포

각 서비스별로:
- **Add Service** → **Docker Compose**
- `docker-compose.coolify.yml` 선택
- 환경변수 설정
- **Deploy** 클릭

---

## 📊 Coolify vs Manual Docker 비교

| 기능 | Coolify | Manual Docker |
|------|---------|---------------|
| **배포 시간** | 5분 | 15분 |
| **CI/CD** | 자동 | 수동 |
| **모니터링** | 내장 | 별도 설정 필요 |
| **백업** | 자동 | 수동 |
| **도메인** | 자동 SSL | 수동 설정 |
| **롤백** | 원클릭 | 수동 |
| **업데이트** | Git push만 | 파일 전송 + 재배포 |

---

## 🆘 트러블슈팅

### 문제 1: Coolify가 설치되어 있지 않음

Coolify 설치:
```bash
ssh root@58.225.113.125

# Coolify 설치 (공식 방법)
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

설치 후 `http://58.225.113.125:8000`으로 접속

### 문제 2: 빌드 실패

1. **Logs** 탭에서 에러 확인
2. 환경변수가 모두 설정되었는지 확인
3. Dockerfile 경로 확인

### 문제 3: 서비스 간 연결 실패

1. 모든 서비스가 같은 네트워크에 있는지 확인
2. 호스트명을 서비스 이름으로 사용 (예: `postgres`, `redis`)

---

## 🎯 추천 배포 방식

**Coolify 사용을 강력히 추천합니다!**

이유:
- ✅ Git push만으로 자동 배포
- ✅ 웹 UI로 간편한 관리
- ✅ 자동 SSL 인증서
- ✅ 내장 모니터링
- ✅ 원클릭 롤백
- ✅ 자동 백업

---

**작성일**: 2025-12-05
**Coolify 버전**: v4.x
**대상 서버**: 58.225.113.125
