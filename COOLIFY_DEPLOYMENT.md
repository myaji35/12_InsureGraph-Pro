# InsureGraph Pro - Coolify CLI 배포 가이드

## 🎯 서버 환경 정보
- **Coolify URL**: http://34.64.191.91
- **서버 IP**: 34.64.191.91
- **OS/Architecture**: Linux AMD64
- **배포 방식**: CLI 기반 자동 배포
- **프로젝트 도메인**: https://InsureGraphPro.34.64.191.91 (통합 도메인)

## 📋 빠른 배포 명령어

**"Coolify에 배포"**라고만 말하면 다음 절차가 자동으로 실행됩니다:

1. ✅ Linux AMD64 환경 확인
2. ✅ 서버 IP를 34.64.191.91로 설정
3. ✅ Docker 이미지를 AMD64 플랫폼으로 빌드
4. ✅ 환경변수 자동 주입
5. ✅ 포트 매핑 (18000, 18001, 17474, 17687)
6. ✅ 배포 및 헬스체크

---

## 🚀 CLI 기반 1-Step 배포

### 전체 스택 배포 (한 번에)

```bash
#!/bin/bash
# Coolify 서버에 전체 스택 배포

COOLIFY_SERVER="34.64.191.91"
PLATFORM="linux/amd64"

# 1. 서버 접속 및 프로젝트 디렉토리 생성
ssh root@$COOLIFY_SERVER << 'EOF'
  mkdir -p /opt/insuregraph
  cd /opt/insuregraph
EOF

# 2. 소스코드 전송
rsync -avz --exclude 'node_modules' --exclude 'venv' --exclude '.next' \
  ./ root@$COOLIFY_SERVER:/opt/insuregraph/

# 3. 환경변수 파일 전송
scp .coolify.env root@$COOLIFY_SERVER:/opt/insuregraph/.env

# 4. Docker Compose로 배포 (AMD64 플랫폼 지정)
ssh root@$COOLIFY_SERVER << 'EOF'
  cd /opt/insuregraph

  # AMD64 플랫폼으로 빌드 및 실행
  DOCKER_DEFAULT_PLATFORM=linux/amd64 docker-compose -f docker-compose.coolify.yml up -d --build

  # 헬스체크
  sleep 10
  curl -f http://localhost:18001/health || echo "Backend not ready yet"
  curl -f http://localhost:18000 || echo "Frontend not ready yet"
EOF

echo "✅ 배포 완료!"
echo "🌐 Frontend: http://34.64.191.91:18000"
echo "🌐 Backend: http://34.64.191.91:18001/docs"
```

---

## 🔧 서비스별 개별 배포

### Backend API 배포

```bash
ssh root@34.64.191.91 << 'EOF'
  cd /opt/insuregraph
  DOCKER_DEFAULT_PLATFORM=linux/amd64 \
    docker-compose -f docker-compose.coolify.yml up -d --build backend

  # 로그 확인
  docker-compose -f docker-compose.coolify.yml logs -f backend
EOF
```

### Frontend 배포

```bash
ssh root@34.64.191.91 << 'EOF'
  cd /opt/insuregraph
  DOCKER_DEFAULT_PLATFORM=linux/amd64 \
    docker-compose -f docker-compose.coolify.yml up -d --build frontend

  # 로그 확인
  docker-compose -f docker-compose.coolify.yml logs -f frontend
EOF
```

### Database 초기화

```bash
ssh root@34.64.191.91 << 'EOF'
  cd /opt/insuregraph

  # PostgreSQL, Redis, Neo4j 시작
  DOCKER_DEFAULT_PLATFORM=linux/amd64 \
    docker-compose -f docker-compose.coolify.yml up -d postgres redis neo4j

  # 데이터베이스 마이그레이션 (PostgreSQL 준비 대기)
  sleep 15
  docker-compose -f docker-compose.coolify.yml exec backend alembic upgrade head
EOF
```

---

## 📝 환경변수 설정 (.coolify.env)

서버에 배포하기 전에 환경변수를 설정하세요:

```bash
# .coolify.env 파일
# Linux AMD64 서버 (34.64.191.91) 전용 설정

# Application
APP_NAME=InsureGraph Pro
ENVIRONMENT=production
DEBUG=false

# Database - PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=insuregraph
POSTGRES_USER=insuregraph_user
POSTGRES_PASSWORD=InsureGraph2024!Prod!Secure

# Database - Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=Neo4j2024!Graph!Secure

# Cache - Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Security
SECRET_KEY=7K8mNpQ3rT9vX2bC5dF6gH8jK0lM4nP7qR9sT2uV5wX8yZ
JWT_SECRET_KEY=3aB5cD7eF9gH2iJ4kL6mN8oP0qR2sT4uV6wX8yZ1aB3cD5

# LLM API Keys
ANTHROPIC_API_KEY=your-anthropic-api-key-here
GOOGLE_API_KEY=your-google-api-key-here
OPENAI_API_KEY=your-openai-api-key
UPSTAGE_API_KEY=your-upstage-api-key

# CORS - Unified domain format
CORS_ORIGINS=https://InsureGraphPro.34.64.191.91,http://InsureGraphPro.34.64.191.91,http://localhost:3000

# Frontend API URL - Path-based routing
NEXT_PUBLIC_API_URL=https://InsureGraphPro.34.64.191.91/api
```

---

## 🌐 배포된 서비스 접속 정보

배포 완료 후 접속 URL (통합 도메인 형식):

### 통합 도메인 (권장)
- **메인 URL**: https://InsureGraphPro.34.64.191.91
  - Frontend: https://InsureGraphPro.34.64.191.91/
  - Backend API: https://InsureGraphPro.34.64.191.91/api
  - API Docs: https://InsureGraphPro.34.64.191.91/api/docs
  - Neo4j Browser: https://InsureGraphPro.34.64.191.91/neo4j

### 포트 직접 접속 (대체 방법)
- **Frontend**: http://34.64.191.91:18000
- **Backend API**: http://34.64.191.91:18001
- **API Docs**: http://34.64.191.91:18001/docs
- **Neo4j Browser**: http://34.64.191.91:17474
  - Username: `neo4j`
  - Password: `Neo4j2024!Graph!Secure`

### 포트 매핑
- Frontend: `18000` → `3000` (컨테이너 내부)
- Backend: `18001` → `8080` (컨테이너 내부)
- Neo4j Browser: `17474` → `7474` (컨테이너 내부)
- Neo4j Bolt: `17687` → `7687` (컨테이너 내부)

---

## 🔄 업데이트 및 재배포

코드 변경 후 재배포:

```bash
#!/bin/bash
# 업데이트 및 재배포 스크립트

COOLIFY_SERVER="34.64.191.91"

# 1. 변경사항 전송
rsync -avz --exclude 'node_modules' --exclude 'venv' --exclude '.next' \
  ./ root@$COOLIFY_SERVER:/opt/insuregraph/

# 2. 재배포 (AMD64)
ssh root@$COOLIFY_SERVER << 'EOF'
  cd /opt/insuregraph

  # 기존 컨테이너 중지
  docker-compose -f docker-compose.coolify.yml down

  # AMD64 플랫폼으로 재빌드 및 시작
  DOCKER_DEFAULT_PLATFORM=linux/amd64 \
    docker-compose -f docker-compose.coolify.yml up -d --build

  # 헬스체크
  sleep 10
  docker-compose -f docker-compose.coolify.yml ps
EOF

echo "✅ 재배포 완료!"
```

---

## 📊 모니터링 및 로그

### 실시간 로그 확인

```bash
# 모든 서비스 로그
ssh root@34.64.191.91 "cd /opt/insuregraph && docker-compose -f docker-compose.coolify.yml logs -f"

# Backend만
ssh root@34.64.191.91 "cd /opt/insuregraph && docker-compose -f docker-compose.coolify.yml logs -f backend"

# Frontend만
ssh root@34.64.191.91 "cd /opt/insuregraph && docker-compose -f docker-compose.coolify.yml logs -f frontend"
```

### 서비스 상태 확인

```bash
ssh root@34.64.191.91 << 'EOF'
  cd /opt/insuregraph
  docker-compose -f docker-compose.coolify.yml ps

  # 리소스 사용량
  docker stats --no-stream
EOF
```

### 헬스체크

```bash
# Backend API
curl -f http://34.64.191.91:18001/health

# Frontend
curl -f http://34.64.191.91:18000

# Neo4j
curl -f http://34.64.191.91:17474
```

---

## 🛠️ 트러블슈팅

### 문제 1: 플랫폼 아키텍처 불일치

**증상**: `exec format error` 또는 `no matching manifest`

**해결**:
```bash
# AMD64 플랫폼 명시적으로 지정
ssh root@34.64.191.91 << 'EOF'
  cd /opt/insuregraph

  # buildx 사용하여 AMD64로 빌드
  docker buildx build --platform linux/amd64 -t insuregraph-backend ./backend
  docker buildx build --platform linux/amd64 -t insuregraph-frontend ./frontend

  # 또는 환경변수로 지정
  export DOCKER_DEFAULT_PLATFORM=linux/amd64
  docker-compose -f docker-compose.coolify.yml up -d --build
EOF
```

### 문제 2: 포트 충돌

**증상**: `port is already allocated`

**해결**:
```bash
ssh root@34.64.191.91 << 'EOF'
  # 사용 중인 포트 확인
  netstat -tulpn | grep -E "18000|18001|17474|17687"

  # 충돌하는 프로세스 종료
  docker-compose -f docker-compose.coolify.yml down

  # 재시작
  docker-compose -f docker-compose.coolify.yml up -d
EOF
```

### 문제 3: 데이터베이스 연결 실패

**증상**: `could not connect to server`

**해결**:
```bash
ssh root@34.64.191.91 << 'EOF'
  cd /opt/insuregraph

  # 데이터베이스 상태 확인
  docker-compose -f docker-compose.coolify.yml ps postgres redis neo4j

  # 로그 확인
  docker-compose -f docker-compose.coolify.yml logs postgres

  # 재시작
  docker-compose -f docker-compose.coolify.yml restart postgres

  # Backend 재시작 (DB 준비 후)
  sleep 10
  docker-compose -f docker-compose.coolify.yml restart backend
EOF
```

---

## 🔐 보안 체크리스트

배포 전 확인사항:

- [ ] `.coolify.env` 파일에 실제 API 키 설정
- [ ] Secret 키들을 강력한 랜덤 값으로 변경
- [ ] PostgreSQL 비밀번호 변경
- [ ] Neo4j 비밀번호 변경
- [ ] CORS_ORIGINS에 실제 도메인만 추가
- [ ] DEBUG=false 설정
- [ ] 방화벽 규칙 설정 (필요한 포트만 개방)

---

## 💾 백업 및 복구

### 데이터베이스 백업

```bash
ssh root@34.64.191.91 << 'EOF'
  cd /opt/insuregraph

  # PostgreSQL 백업
  docker-compose -f docker-compose.coolify.yml exec -T postgres \
    pg_dump -U insuregraph_user insuregraph > backup_$(date +%Y%m%d).sql

  # Neo4j 백업
  docker-compose -f docker-compose.coolify.yml exec neo4j \
    neo4j-admin database dump neo4j --to-path=/backups
EOF
```

### 복구

```bash
ssh root@34.64.191.91 << 'EOF'
  cd /opt/insuregraph

  # PostgreSQL 복구
  cat backup_20251210.sql | \
    docker-compose -f docker-compose.coolify.yml exec -T postgres \
    psql -U insuregraph_user insuregraph
EOF
```

---

## 📝 자동화 스크립트

전체 배포 자동화 스크립트 생성:

```bash
# deploy-to-coolify.sh 파일 생성
cat > deploy-to-coolify.sh << 'SCRIPT'
#!/bin/bash
set -e

COOLIFY_SERVER="34.64.191.91"
PLATFORM="linux/amd64"
PROJECT_DIR="/opt/insuregraph"

echo "🚀 InsureGraph Pro 배포 시작..."
echo "📍 서버: $COOLIFY_SERVER (Linux AMD64)"

# 1. 소스코드 전송
echo "📦 소스코드 전송 중..."
rsync -avz --progress \
  --exclude 'node_modules' \
  --exclude 'venv' \
  --exclude '.next' \
  --exclude '__pycache__' \
  --exclude '.git' \
  ./ root@$COOLIFY_SERVER:$PROJECT_DIR/

# 2. 환경변수 전송
echo "🔧 환경변수 설정 중..."
scp .coolify.env root@$COOLIFY_SERVER:$PROJECT_DIR/.env

# 3. 배포 실행
echo "🐳 Docker 컨테이너 빌드 및 시작 중..."
ssh root@$COOLIFY_SERVER << EOF
  cd $PROJECT_DIR

  # 기존 컨테이너 중지 (첫 배포시는 무시)
  docker-compose -f docker-compose.coolify.yml down 2>/dev/null || true

  # AMD64 플랫폼으로 빌드 및 실행
  DOCKER_DEFAULT_PLATFORM=$PLATFORM \
    docker-compose -f docker-compose.coolify.yml up -d --build

  echo "⏳ 서비스 시작 대기 중..."
  sleep 15

  # 데이터베이스 마이그레이션
  echo "🗄️  데이터베이스 마이그레이션 실행 중..."
  docker-compose -f docker-compose.coolify.yml exec -T backend alembic upgrade head

  # 상태 확인
  echo "📊 서비스 상태:"
  docker-compose -f docker-compose.coolify.yml ps
EOF

# 4. 헬스체크
echo "🏥 헬스체크 실행 중..."
sleep 5

if curl -f http://$COOLIFY_SERVER:18001/health > /dev/null 2>&1; then
  echo "✅ Backend: http://$COOLIFY_SERVER:18001 (정상)"
else
  echo "❌ Backend: 응답 없음"
fi

if curl -f http://$COOLIFY_SERVER:18000 > /dev/null 2>&1; then
  echo "✅ Frontend: http://$COOLIFY_SERVER:18000 (정상)"
else
  echo "❌ Frontend: 응답 없음"
fi

echo ""
echo "🎉 배포 완료!"
echo "🌐 접속 URL:"
echo "   Frontend:  http://$COOLIFY_SERVER:18000"
echo "   Backend:   http://$COOLIFY_SERVER:18001"
echo "   API Docs:  http://$COOLIFY_SERVER:18001/docs"
echo "   Neo4j:     http://$COOLIFY_SERVER:17474"
SCRIPT

chmod +x deploy-to-coolify.sh
```

사용법:
```bash
./deploy-to-coolify.sh
```

---

## 🎯 "Coolify에 배포" 명령어 실행 시 자동 수행 항목

1. ✅ **서버 정보 확인**
   - IP: 34.64.191.91
   - 플랫폼: Linux AMD64

2. ✅ **환경 설정**
   - 환경변수 파일 (.coolify.env) 확인
   - API 키 검증
   - 포트 매핑 확인 (18000, 18001, 17474, 17687)

3. ✅ **Docker 빌드**
   - `DOCKER_DEFAULT_PLATFORM=linux/amd64` 설정
   - Backend 이미지 빌드
   - Frontend 이미지 빌드

4. ✅ **배포 실행**
   - PostgreSQL, Redis, Neo4j 시작
   - Backend API 시작
   - Frontend 시작
   - 데이터베이스 마이그레이션

5. ✅ **검증**
   - 헬스체크 수행
   - 로그 확인
   - 접속 URL 출력

---

**작성일**: 2025-12-10
**서버**: 34.64.191.91 (Linux AMD64)
**배포 방식**: CLI 기반 자동 배포
