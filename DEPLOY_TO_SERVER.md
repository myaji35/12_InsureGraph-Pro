# InsureGraph Pro - 서버 직접 배포 가이드

## 목차
1. [서버 환경 준비](#1-서버-환경-준비)
2. [Docker 배포](#2-docker-배포)
3. [환경변수 설정](#3-환경변수-설정)
4. [서비스 시작](#4-서비스-시작)
5. [모니터링 및 관리](#5-모니터링-및-관리)

---

## 1. 서버 환경 준비

### 1.1 서버 접속

```bash
# SSH로 서버 접속
ssh your-username@58.225.113.125

# 또는 키 파일 사용
ssh -i /path/to/key.pem your-username@58.225.113.125
```

### 1.2 필수 소프트웨어 설치

```bash
# Docker 설치 (Ubuntu/Debian 기준)
sudo apt-get update
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Docker GPG 키 추가
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Docker 리포지토리 추가
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker 설치
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# 현재 사용자를 docker 그룹에 추가 (sudo 없이 docker 사용)
sudo usermod -aG docker $USER
newgrp docker

# 설치 확인
docker --version
docker compose version
```

### 1.3 Git 설치 및 프로젝트 클론

```bash
# Git 설치
sudo apt-get install -y git

# 프로젝트 디렉토리 생성
mkdir -p ~/projects
cd ~/projects

# 프로젝트 클론
git clone https://github.com/YOUR_USERNAME/InsureGraph-Pro.git
cd InsureGraph-Pro
```

---

## 2. Docker 배포

### 2.1 Docker Compose 파일 생성

**docker-compose.prod.yml** 파일 생성:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15
    container_name: insuregraph-postgres
    environment:
      POSTGRES_DB: insuregraph
      POSTGRES_USER: insuregraph_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - insuregraph-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U insuregraph_user -d insuregraph"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: insuregraph-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - insuregraph-network
    restart: unless-stopped
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Neo4j Graph Database
  neo4j:
    image: neo4j:5.14
    container_name: insuregraph-neo4j
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc"]'
      NEO4J_dbms_security_procedures_unrestricted: apoc.*
      NEO4J_dbms_memory_heap_max__size: 2G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    networks:
      - insuregraph-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "${NEO4J_PASSWORD}", "RETURN 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: insuregraph-backend
    environment:
      # Database
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: insuregraph
      POSTGRES_USER: insuregraph_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}

      # Redis
      REDIS_HOST: redis
      REDIS_PORT: 6379

      # Neo4j
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: ${NEO4J_PASSWORD}

      # Security
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}

      # API Keys
      UPSTAGE_API_KEY: ${UPSTAGE_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}

      # Environment
      ENVIRONMENT: production
      DEBUG: false
      LOG_LEVEL: INFO

      # CORS
      CORS_ORIGINS: http://58.225.113.125:3000,https://your-domain.com
    volumes:
      - ./backend/logs:/app/logs
      - ./backend/data:/app/data
    ports:
      - "8000:8080"
    networks:
      - insuregraph-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      neo4j:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: insuregraph-frontend
    environment:
      NEXT_PUBLIC_API_URL: http://58.225.113.125:8000
      NODE_ENV: production
    ports:
      - "3000:3000"
    networks:
      - insuregraph-network
    depends_on:
      - backend
    restart: unless-stopped

  # Celery Worker (백그라운드 작업)
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: insuregraph-celery
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      # 백엔드와 동일한 환경변수 사용
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: insuregraph
      POSTGRES_USER: insuregraph_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: ${NEO4J_PASSWORD}
      SECRET_KEY: ${SECRET_KEY}
      UPSTAGE_API_KEY: ${UPSTAGE_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    volumes:
      - ./backend/logs:/app/logs
      - ./backend/data:/app/data
    networks:
      - insuregraph-network
    depends_on:
      - postgres
      - redis
      - neo4j
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  neo4j_data:
  neo4j_logs:

networks:
  insuregraph-network:
    driver: bridge
```

### 2.2 환경변수 파일 생성

**.env.production** 파일 생성:

```bash
# Database
POSTGRES_PASSWORD=your_secure_postgres_password

# Neo4j
NEO4J_PASSWORD=your_secure_neo4j_password

# Security Keys (강력한 랜덤 문자열 생성)
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here

# API Keys
UPSTAGE_API_KEY=your_upstage_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

**안전한 비밀번호 생성**:
```bash
# 비밀번호 자동 생성
openssl rand -base64 32

# 여러 개 생성
for i in {1..5}; do openssl rand -base64 32; done
```

### 2.3 Frontend Dockerfile 생성

**frontend/Dockerfile** 생성:

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# 종속성 설치
COPY package*.json ./
RUN npm ci

# 소스 복사 및 빌드
COPY . .
RUN npm run build

# Production 이미지
FROM node:18-alpine

WORKDIR /app

# 빌드 결과만 복사
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/next.config.js ./

# Production 종속성만 설치
RUN npm ci --only=production

EXPOSE 3000

CMD ["npm", "start"]
```

---

## 3. 서비스 시작

### 3.1 환경변수 설정

```bash
# .env.production 파일 권한 설정
chmod 600 .env.production

# 환경변수 로드
export $(cat .env.production | xargs)
```

### 3.2 Docker Compose 실행

```bash
# 서비스 빌드 및 시작
docker compose -f docker-compose.prod.yml up -d --build

# 로그 확인
docker compose -f docker-compose.prod.yml logs -f

# 특정 서비스 로그만 확인
docker compose -f docker-compose.prod.yml logs -f backend
```

### 3.3 데이터베이스 마이그레이션

```bash
# 백엔드 컨테이너 접속
docker exec -it insuregraph-backend bash

# Alembic 마이그레이션 실행
alembic upgrade head

# 컨테이너 종료
exit
```

### 3.4 서비스 상태 확인

```bash
# 모든 컨테이너 상태 확인
docker compose -f docker-compose.prod.yml ps

# 헬스 체크
curl http://58.225.113.125:8000/api/v1/health
curl http://58.225.113.125:3000

# Neo4j 브라우저 접속
# http://58.225.113.125:7474
```

---

## 4. 방화벽 설정

### 4.1 UFW (Ubuntu Firewall) 설정

```bash
# UFW 활성화
sudo ufw enable

# SSH 포트 허용 (중요!)
sudo ufw allow 22/tcp

# 애플리케이션 포트 허용
sudo ufw allow 3000/tcp  # Frontend
sudo ufw allow 8000/tcp  # Backend API
sudo ufw allow 7474/tcp  # Neo4j Browser (선택사항)
sudo ufw allow 7687/tcp  # Neo4j Bolt (선택사항)

# 방화벽 상태 확인
sudo ufw status verbose
```

### 4.2 클라우드 방화벽 설정

**GCP, AWS, Azure 등 클라우드 사용 시**:
- 인바운드 규칙 추가:
  - 포트 3000 (Frontend) - TCP
  - 포트 8000 (Backend) - TCP
  - 포트 7474, 7687 (Neo4j) - TCP (필요 시)

---

## 5. 모니터링 및 관리

### 5.1 로그 확인

```bash
# 실시간 로그 확인
docker compose -f docker-compose.prod.yml logs -f

# 최근 100줄 로그
docker compose -f docker-compose.prod.yml logs --tail=100

# 특정 서비스 로그
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f celery-worker
```

### 5.2 서비스 재시작

```bash
# 전체 서비스 재시작
docker compose -f docker-compose.prod.yml restart

# 특정 서비스만 재시작
docker compose -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.prod.yml restart frontend
```

### 5.3 서비스 중지 및 삭제

```bash
# 서비스 중지
docker compose -f docker-compose.prod.yml stop

# 서비스 중지 및 컨테이너 삭제
docker compose -f docker-compose.prod.yml down

# 볼륨까지 모두 삭제 (⚠️ 데이터 손실 주의!)
docker compose -f docker-compose.prod.yml down -v
```

### 5.4 백업

```bash
# PostgreSQL 백업
docker exec insuregraph-postgres pg_dump -U insuregraph_user insuregraph > backup_$(date +%Y%m%d).sql

# Neo4j 백업
docker exec insuregraph-neo4j neo4j-admin database dump neo4j --to-path=/backups

# 백업 파일 다운로드
scp your-username@58.225.113.125:~/projects/InsureGraph-Pro/backup_*.sql ./
```

### 5.5 업데이트 배포

```bash
# 최신 코드 가져오기
cd ~/projects/InsureGraph-Pro
git pull origin main

# 서비스 재빌드 및 재시작
docker compose -f docker-compose.prod.yml up -d --build

# 데이터베이스 마이그레이션 (필요 시)
docker exec -it insuregraph-backend alembic upgrade head
```

---

## 6. 성능 최적화

### 6.1 리소스 제한 설정

**docker-compose.prod.yml**에 추가:

```yaml
services:
  backend:
    # ... 기존 설정 ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### 6.2 Nginx 리버스 프록시 설정 (선택사항)

```bash
# Nginx 설치
sudo apt-get install -y nginx

# 설정 파일 생성
sudo nano /etc/nginx/sites-available/insuregraph
```

**Nginx 설정**:
```nginx
server {
    listen 80;
    server_name 58.225.113.125;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
    }
}
```

```bash
# 설정 활성화
sudo ln -s /etc/nginx/sites-available/insuregraph /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 7. SSL/TLS 설정 (HTTPS)

### 7.1 Let's Encrypt 인증서 발급

```bash
# Certbot 설치
sudo apt-get install -y certbot python3-certbot-nginx

# 도메인이 있는 경우
sudo certbot --nginx -d your-domain.com

# IP만 있는 경우 (자체 서명 인증서)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/nginx-selfsigned.key \
  -out /etc/ssl/certs/nginx-selfsigned.crt
```

---

## 8. 트러블슈팅

### 문제 1: 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker compose -f docker-compose.prod.yml logs backend

# 컨테이너 상태 확인
docker ps -a

# 컨테이너 재시작
docker compose -f docker-compose.prod.yml restart backend
```

### 문제 2: 데이터베이스 연결 실패

```bash
# PostgreSQL 상태 확인
docker exec insuregraph-postgres pg_isready -U insuregraph_user

# 네트워크 확인
docker network inspect insuregraph-pro_insuregraph-network
```

### 문제 3: 포트가 이미 사용 중

```bash
# 포트 사용 확인
sudo netstat -tulpn | grep :8000

# 프로세스 종료
sudo kill -9 <PID>
```

---

## 9. 보안 권장사항

1. **방화벽 설정**: 필요한 포트만 개방
2. **강력한 비밀번호**: 최소 32자 이상의 랜덤 문자열
3. **환경변수 보안**: .env 파일 권한을 600으로 설정
4. **정기 업데이트**: Docker 이미지 및 시스템 패키지 업데이트
5. **로그 모니터링**: 이상 활동 감지
6. **백업 자동화**: Cron job으로 정기 백업 설정

```bash
# Cron 백업 설정
crontab -e

# 매일 새벽 3시에 백업
0 3 * * * cd ~/projects/InsureGraph-Pro && docker exec insuregraph-postgres pg_dump -U insuregraph_user insuregraph > backup_$(date +\%Y\%m\%d).sql
```

---

## 10. 배포 체크리스트

- [ ] 서버 접속 확인
- [ ] Docker 및 Docker Compose 설치
- [ ] 프로젝트 클론
- [ ] .env.production 파일 생성 및 설정
- [ ] docker-compose.prod.yml 검토
- [ ] 방화벽 설정
- [ ] Docker Compose 빌드 및 실행
- [ ] 데이터베이스 마이그레이션
- [ ] 헬스 체크 확인
- [ ] 로그 확인
- [ ] 백업 설정
- [ ] 모니터링 설정

---

**작성일**: 2025-12-05
**버전**: 1.0
**작성자**: Claude Code
