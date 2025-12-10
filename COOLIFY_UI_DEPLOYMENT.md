# InsureGraph Pro - Coolify UI 배포 가이드

## 🎯 개요

이 가이드는 Coolify UI를 사용하여 InsureGraph Pro를 배포하는 방법을 설명합니다.

## 📋 사전 요구사항

- Coolify 서버: http://34.64.191.91
- GitHub 저장소: https://github.com/myaji35/12_InsureGraph-Pro.git
- 실제 API 키 (Anthropic, Google, OpenAI, Upstage)

---

## 🚀 1단계: Coolify 대시보드 접속

1. 브라우저에서 Coolify 대시보드 접속
   ```
   http://34.64.191.91
   ```

2. Coolify 계정으로 로그인

---

## 🔗 2단계: GitHub 저장소 연결

### 2.1 새 프로젝트 생성

1. 대시보드에서 **"New Project"** 클릭
2. 프로젝트 이름: `InsureGraphPro`
3. **"Create Project"** 클릭

### 2.2 GitHub 저장소 연결

1. 프로젝트 내에서 **"New Resource"** 클릭
2. **"Git Repository"** 선택
3. GitHub 저장소 URL 입력:
   ```
   https://github.com/myaji35/12_InsureGraph-Pro.git
   ```
4. **Branch**: `main` 선택
5. **"Connect"** 클릭

### 2.3 Docker Compose 파일 선택

1. **Configuration Type**: `Docker Compose` 선택
2. **Compose File**: `docker-compose.coolify.yml` 선택
3. **"Save"** 클릭

---

## ⚙️ 3단계: 환경변수 설정

### 3.1 환경변수 추가

**Settings** → **Environment Variables** 메뉴로 이동하여 다음 환경변수를 추가합니다:

#### Application Settings
```bash
APP_NAME=InsureGraph Pro
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

#### Database - PostgreSQL
```bash
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=insuregraph
POSTGRES_USER=insuregraph_user
POSTGRES_PASSWORD=<your-secure-postgres-password>
```

#### Database - Neo4j
```bash
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your-secure-neo4j-password>
```

#### Cache - Redis
```bash
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

#### Security Keys
```bash
SECRET_KEY=<your-secret-key>
JWT_SECRET_KEY=<your-jwt-secret-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=1
```

#### LLM API Keys (실제 키 입력 필요!)
```bash
ANTHROPIC_API_KEY=<your-real-anthropic-api-key>
GOOGLE_API_KEY=<your-real-google-api-key>
OPENAI_API_KEY=<your-real-openai-api-key>
UPSTAGE_API_KEY=<your-real-upstage-api-key>
```

#### CORS Settings (통합 도메인)
```bash
CORS_ORIGINS=https://InsureGraphPro.34.64.191.91,http://InsureGraphPro.34.64.191.91,http://localhost:3000
```

#### Frontend API URL (통합 도메인)
```bash
NEXT_PUBLIC_API_URL=https://InsureGraphPro.34.64.191.91/api
```

#### Rate Limiting
```bash
RATE_LIMIT_ENABLED=true
```

### 3.2 환경변수 저장

모든 환경변수 입력 후 **"Save"** 클릭

---

## 🌐 4단계: 도메인 설정 (통합 도메인)

### 4.1 도메인 추가

1. **Settings** → **Domains** 메뉴로 이동
2. **"Add Domain"** 클릭
3. 도메인 입력:
   ```
   InsureGraphPro.34.64.191.91
   ```
4. **HTTPS**: 필요시 체크 (Let's Encrypt 자동 설정)
5. **"Save"** 클릭

### 4.2 서비스별 라우팅 확인

Docker Compose 파일에 Traefik 라벨이 설정되어 있어 자동으로 라우팅됩니다:

- **Frontend**: `Host(InsureGraphPro.34.64.191.91) && Path(/)`
- **Backend API**: `Host(InsureGraphPro.34.64.191.91) && PathPrefix(/api)`
- **Neo4j**: `Host(InsureGraphPro.34.64.191.91) && PathPrefix(/neo4j)`

---

## 🏗️ 5단계: 빌드 설정

### 5.1 플랫폼 설정

1. **Settings** → **Build** 메뉴로 이동
2. **Build Platform**: `linux/amd64` 선택
3. **Docker Compose Version**: `2.x` 선택
4. **"Save"** 클릭

### 5.2 빌드 순서 설정 (자동)

Docker Compose의 `depends_on`이 설정되어 있어 자동으로 올바른 순서로 빌드됩니다:
1. PostgreSQL, Redis, Neo4j (데이터베이스)
2. Backend (백엔드 API)
3. Frontend (프론트엔드)
4. Celery Worker (백그라운드 작업)

---

## 🚀 6단계: 배포 실행

### 6.1 배포 시작

1. 프로젝트 대시보드로 돌아가기
2. **"Deploy"** 버튼 클릭
3. 빌드 및 배포 진행 상황 모니터링

### 6.2 배포 로그 확인

- **Logs** 탭에서 실시간 로그 확인
- 각 서비스별 로그 확인 가능:
  - `postgres` - PostgreSQL 로그
  - `redis` - Redis 로그
  - `neo4j` - Neo4j 로그
  - `backend` - FastAPI 백엔드 로그
  - `frontend` - Next.js 프론트엔드 로그
  - `celery-worker` - Celery Worker 로그

---

## ✅ 7단계: 배포 확인

### 7.1 서비스 상태 확인

**Dashboard** → **Services**에서 모든 서비스가 **Running** 상태인지 확인:

- ✅ postgres (healthy)
- ✅ redis (healthy)
- ✅ neo4j (healthy)
- ✅ backend (healthy)
- ✅ frontend (running)
- ✅ celery-worker (running)

### 7.2 헬스체크

#### 통합 도메인 URL로 접속:

1. **Frontend**:
   ```
   https://InsureGraphPro.34.64.191.91/
   ```
   - 메인 페이지가 로드되는지 확인

2. **Backend API**:
   ```
   https://InsureGraphPro.34.64.191.91/api/health
   ```
   - Response: `{"status": "ok"}` 확인

3. **API Docs**:
   ```
   https://InsureGraphPro.34.64.191.91/api/docs
   ```
   - Swagger UI가 표시되는지 확인

4. **Neo4j Browser**:
   ```
   https://InsureGraphPro.34.64.191.91/neo4j
   ```
   - Username: `neo4j`
   - Password: `<your-neo4j-password>`
   - 로그인 및 연결 확인

#### 포트 직접 접속 (대체):

1. **Frontend**: http://34.64.191.91:18000
2. **Backend**: http://34.64.191.91:18001/health
3. **API Docs**: http://34.64.191.91:18001/docs
4. **Neo4j Browser**: http://34.64.191.91:17474

---

## 🔄 8단계: 데이터베이스 마이그레이션

### 8.1 Alembic 마이그레이션 실행

1. **Services** → **backend** 선택
2. **Terminal** 탭 클릭
3. 다음 명령어 실행:
   ```bash
   alembic upgrade head
   ```

### 8.2 Neo4j 인덱스 생성 (옵션)

Neo4j Browser에서 실행:
```cypher
// 텍스트 검색 최적화
CREATE INDEX article_text IF NOT EXISTS FOR (n:Article) ON (n.text);
CREATE INDEX paragraph_text IF NOT EXISTS FOR (n:Paragraph) ON (n.text);

// 소스 추적
CREATE INDEX article_source IF NOT EXISTS FOR (n:Article) ON (n.source);
```

---

## 🔧 9단계: 트러블슈팅

### 9.1 빌드 실패 시

**원인**: AMD64 플랫폼 미설정
**해결**: Settings → Build → Platform을 `linux/amd64`로 변경

### 9.2 환경변수 문제

**원인**: API 키 미설정 또는 잘못된 값
**해결**: Settings → Environment Variables에서 모든 키 재확인

### 9.3 서비스 연결 실패

**원인**: 서비스 시작 순서 문제
**해결**:
1. **Services**에서 모든 서비스 중지
2. 데이터베이스부터 순서대로 재시작:
   - postgres, redis, neo4j
   - backend
   - frontend, celery-worker

### 9.4 CORS 에러

**원인**: CORS_ORIGINS 설정 오류
**해결**: 환경변수에서 다음 확인:
```bash
CORS_ORIGINS=https://InsureGraphPro.34.64.191.91,http://InsureGraphPro.34.64.191.91,http://localhost:3000
```

### 9.5 Neo4j 연결 실패

**원인**: Neo4j 비밀번호 불일치
**해결**:
1. 환경변수의 `NEO4J_PASSWORD` 확인
2. Neo4j 서비스 재시작
3. 데이터 초기화가 필요한 경우 볼륨 삭제 후 재생성

---

## 📊 10단계: 모니터링 설정

### 10.1 로그 모니터링

**Dashboard** → **Logs**에서:
- 실시간 로그 확인
- 에러 필터링
- 특정 서비스 로그 선택

### 10.2 리소스 사용량 확인

**Dashboard** → **Metrics**에서:
- CPU 사용량
- 메모리 사용량
- 네트워크 트래픽
- 디스크 사용량

---

## 🔄 업데이트 및 재배포

### 코드 변경 후 재배포:

1. GitHub에 코드 푸시
2. Coolify 대시보드에서 **"Redeploy"** 클릭
3. 또는 **Auto Deploy** 설정:
   - Settings → **Git** → **Auto Deploy** 활성화
   - GitHub Webhook 자동 설정됨

---

## 📞 지원

### GitHub Issues
https://github.com/myaji35/12_InsureGraph-Pro/issues

### Coolify 문서
https://coolify.io/docs

---

## 🎉 완료!

축하합니다! InsureGraph Pro가 성공적으로 배포되었습니다.

**접속 URL**:
- 🌐 **메인**: https://InsureGraphPro.34.64.191.91
- 📱 **Frontend**: https://InsureGraphPro.34.64.191.91/
- 🔧 **Backend API**: https://InsureGraphPro.34.64.191.91/api
- 📖 **API Docs**: https://InsureGraphPro.34.64.191.91/api/docs
- 🗄️ **Neo4j**: https://InsureGraphPro.34.64.191.91/neo4j

**대체 포트 접속**:
- Frontend: http://34.64.191.91:18000
- Backend: http://34.64.191.91:18001
- Neo4j: http://34.64.191.91:17474
