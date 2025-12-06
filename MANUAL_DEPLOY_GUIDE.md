# InsureGraph Pro - 수동 배포 가이드

## 서버 정보
- **IP**: 58.225.113.125
- **사용자**: root
- **비밀번호**: gmldnjs!00

---

## 📋 배포 단계

### Step 1: 로컬에서 파일 압축

로컬 Mac에서 실행:

```bash
cd "/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro"

# 배포용 파일 압축
tar -czf /tmp/insuregraph-deploy.tar.gz \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='backend/venv' \
    --exclude='backend/__pycache__' \
    --exclude='backend/.pytest_cache' \
    --exclude='backend/logs' \
    --exclude='frontend/.next' \
    --exclude='frontend/out' \
    --exclude='.turbo' \
    --exclude='*.pyc' \
    backend/ frontend/ docker-compose.prod.yml .env.production

echo "✅ 파일 압축 완료: /tmp/insuregraph-deploy.tar.gz"
ls -lh /tmp/insuregraph-deploy.tar.gz
```

### Step 2: 서버로 파일 전송

```bash
# SCP로 파일 전송 (비밀번호 입력 필요)
scp /tmp/insuregraph-deploy.tar.gz root@58.225.113.125:/tmp/

# 또는 sshpass 사용 (설치되어 있는 경우)
# brew install hudochenkov/sshpass/sshpass
# sshpass -p 'gmldnjs!00' scp /tmp/insuregraph-deploy.tar.gz root@58.225.113.125:/tmp/
```

### Step 3: 서버 접속 및 설정

**새 터미널 열기**:

```bash
# 서버 접속
ssh root@58.225.113.125
# 비밀번호: gmldnjs!00
```

### Step 4: 서버에서 Docker 설치

서버에 접속한 상태에서:

```bash
# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo "Docker 설치 시작..."

    # Docker 설치
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh

    # Docker Compose 플러그인 설치
    apt-get update
    apt-get install -y docker-compose-plugin

    # 설치 확인
    docker --version
    docker compose version

    echo "✅ Docker 설치 완료"
else
    echo "✅ Docker가 이미 설치되어 있습니다."
    docker --version
fi
```

### Step 5: 프로젝트 파일 설정

```bash
# 프로젝트 디렉토리 생성
mkdir -p ~/InsureGraph-Pro
cd ~/InsureGraph-Pro

# 기존 파일 백업 (있는 경우)
if [ -f docker-compose.prod.yml ]; then
    timestamp=$(date +%Y%m%d_%H%M%S)
    mkdir -p backups
    tar -czf backups/backup_${timestamp}.tar.gz . 2>/dev/null || true
    echo "✅ 기존 파일 백업 완료"
fi

# 새 파일 압축 해제
tar -xzf /tmp/insuregraph-deploy.tar.gz
echo "✅ 파일 압축 해제 완료"

# 파일 확인
ls -la
```

### Step 6: 방화벽 설정

```bash
# UFW 방화벽 설정 (Ubuntu)
if command -v ufw &> /dev/null; then
    # SSH 포트 먼저 허용 (중요!)
    ufw allow 22/tcp

    # 애플리케이션 포트 허용
    ufw allow 3000/tcp  # Frontend
    ufw allow 8000/tcp  # Backend API
    ufw allow 7474/tcp  # Neo4j Browser
    ufw allow 7687/tcp  # Neo4j Bolt

    # 방화벽 활성화
    ufw --force enable

    # 상태 확인
    ufw status

    echo "✅ 방화벽 설정 완료"
fi
```

### Step 7: Docker Compose 실행

```bash
cd ~/InsureGraph-Pro

# 환경변수 파일 확인
cat .env.production

# Docker Compose 빌드 및 실행
docker compose -f docker-compose.prod.yml up -d --build

# 진행 상황 확인 (5-10분 소요)
docker compose -f docker-compose.prod.yml logs -f
# Ctrl+C로 로그 보기 종료
```

### Step 8: 서비스 상태 확인

```bash
# 컨테이너 상태 확인
docker compose -f docker-compose.prod.yml ps

# 예상 출력:
# NAME                    COMMAND                  SERVICE     STATUS      PORTS
# insuregraph-backend     "uvicorn app.main:ap…"   backend     running     0.0.0.0:8000->8080/tcp
# insuregraph-celery      "celery -A app.celer…"   celery      running
# insuregraph-frontend    "node server.js"         frontend    running     0.0.0.0:3000->3000/tcp
# insuregraph-neo4j       "tini -g -- /startup…"   neo4j       running     0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp
# insuregraph-postgres    "docker-entrypoint.s…"   postgres    running     0.0.0.0:5432->5432/tcp
# insuregraph-redis       "redis-server --appe…"   redis       running     0.0.0.0:6379->6379/tcp
```

### Step 9: 데이터베이스 마이그레이션

```bash
# Alembic 마이그레이션 실행
docker exec insuregraph-backend alembic upgrade head

# 성공 메시지 확인
echo "✅ 데이터베이스 마이그레이션 완료"
```

### Step 10: 헬스 체크

```bash
# Backend API 확인
curl http://localhost:8000/api/v1/health

# 예상 응답:
# {"status":"healthy","database":"connected",...}

# Frontend 확인
curl -I http://localhost:3000

# 예상 응답:
# HTTP/1.1 200 OK
```

---

## 🌐 접속 URL 확인

배포가 완료되면 다음 URL로 접속할 수 있습니다:

### 로컬에서 테스트 (Mac)

```bash
# Backend API
curl http://58.225.113.125:8000/api/v1/health

# Frontend
open http://58.225.113.125:3000

# API 문서
open http://58.225.113.125:8000/docs

# Neo4j 브라우저
open http://58.225.113.125:7474
# Username: neo4j
# Password: Neo4j2024!Graph!Secure
```

---

## 🔧 관리 명령어

### 로그 확인

```bash
# 전체 로그 실시간 보기
docker compose -f docker-compose.prod.yml logs -f

# 특정 서비스 로그
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f celery-worker

# 최근 100줄만 보기
docker compose -f docker-compose.prod.yml logs --tail=100
```

### 서비스 재시작

```bash
# 전체 재시작
docker compose -f docker-compose.prod.yml restart

# 특정 서비스만 재시작
docker compose -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.prod.yml restart frontend
```

### 서비스 중지

```bash
# 서비스 중지
docker compose -f docker-compose.prod.yml stop

# 서비스 중지 및 컨테이너 삭제
docker compose -f docker-compose.prod.yml down

# 볼륨까지 모두 삭제 (⚠️ 데이터 손실 주의!)
docker compose -f docker-compose.prod.yml down -v
```

### 업데이트 배포

```bash
# 1. 새 파일을 서버로 전송 (로컬 Mac에서)
cd "/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro"
tar -czf /tmp/insuregraph-update.tar.gz backend/ frontend/ docker-compose.prod.yml
scp /tmp/insuregraph-update.tar.gz root@58.225.113.125:/tmp/

# 2. 서버에서 업데이트 (서버에서)
ssh root@58.225.113.125
cd ~/InsureGraph-Pro
tar -xzf /tmp/insuregraph-update.tar.gz
docker compose -f docker-compose.prod.yml up -d --build
docker exec insuregraph-backend alembic upgrade head
```

---

## 🔍 트러블슈팅

### 문제 1: 컨테이너가 시작되지 않음

```bash
# 컨테이너 상태 확인
docker compose -f docker-compose.prod.yml ps

# 로그 확인
docker compose -f docker-compose.prod.yml logs backend

# 컨테이너 재시작
docker compose -f docker-compose.prod.yml restart backend
```

### 문제 2: 포트가 이미 사용 중

```bash
# 포트 사용 확인
netstat -tulpn | grep :8000

# 프로세스 종료
kill -9 <PID>

# 또는 Docker Compose 재시작
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### 문제 3: 데이터베이스 연결 실패

```bash
# PostgreSQL 상태 확인
docker exec insuregraph-postgres pg_isready -U insuregraph_user

# PostgreSQL 재시작
docker compose -f docker-compose.prod.yml restart postgres

# 로그 확인
docker compose -f docker-compose.prod.yml logs postgres
```

### 문제 4: Frontend가 API에 연결 안 됨

```bash
# Backend 상태 확인
curl http://localhost:8000/api/v1/health

# Frontend 환경변수 확인
docker exec insuregraph-frontend env | grep API

# Frontend 재빌드
docker compose -f docker-compose.prod.yml up -d --build frontend
```

---

## 📊 백업

### PostgreSQL 백업

```bash
# 백업 생성
docker exec insuregraph-postgres pg_dump -U insuregraph_user insuregraph > backup_$(date +%Y%m%d).sql

# 백업 복원
docker exec -i insuregraph-postgres psql -U insuregraph_user insuregraph < backup_20251205.sql
```

### Neo4j 백업

```bash
# 백업 디렉토리 생성
mkdir -p ~/backups/neo4j

# 백업 생성
docker exec insuregraph-neo4j neo4j-admin database dump neo4j --to-path=/backups

# 백업 파일 복사
docker cp insuregraph-neo4j:/backups ~/backups/neo4j/
```

---

## 📈 모니터링

### 리소스 사용량

```bash
# Docker 컨테이너 리소스 확인
docker stats

# 디스크 사용량
df -h

# 메모리 사용량
free -h
```

### 로그 정리

```bash
# 오래된 로그 삭제
docker system prune -f

# 사용하지 않는 이미지 삭제
docker image prune -a -f

# 전체 정리 (⚠️ 주의)
docker system prune -a --volumes -f
```

---

## 🎯 배포 완료 체크리스트

- [ ] Docker 설치 확인
- [ ] 파일 압축 해제 완료
- [ ] 방화벽 설정 완료
- [ ] Docker Compose 실행 완료
- [ ] 모든 컨테이너 정상 실행 중
- [ ] 데이터베이스 마이그레이션 완료
- [ ] Backend API 헬스 체크 성공
- [ ] Frontend 접속 확인
- [ ] Neo4j 브라우저 접속 확인

---

**배포 일시**: 2025-12-05
**서버**: 58.225.113.125
**환경**: Production
