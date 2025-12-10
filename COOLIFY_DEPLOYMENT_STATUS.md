# InsureGraph Pro - Coolify 배포 현황 보고서

**작성일**: 2025-12-10 22:52 KST
**프로젝트**: InsureGraphPro
**GitHub**: https://github.com/myaji35/12_InsureGraph-Pro.git

---

## ✅ 완료된 작업

### 1. Coolify CLI 설정 완료
- **CLI 버전**: 1.3.0
- **Context**: production (http://34.64.191.91:8000)
- **API 토큰**: 설정 완료
- **Private Key**: localhost's key 사용

### 2. Coolify 서버 추가 완료
- **서버명**: coolify-insuregraph
- **UUID**: rc0s0w80gcksc00kkso0kwos
- **IP**: 34.64.191.91
- **상태**: is_reachable: true, is_usable: true ✅
- **포트**: 22 (SSH)
- **사용자**: root

### 3. InsureGraphPro 프로젝트 생성 완료
- **프로젝트명**: InsureGraphPro
- **UUID**: rsskss4gcwsgwo8w040gs4ks
- **설명**: Insurance Knowledge Graph with GraphRAG
- **생성 방법**: Coolify API 직접 호출

### 4. 애플리케이션 자동 생성 완료
- **애플리케이션명**: insuregraph-pro
- **UUID**: e04ggk4k4www8kkg44ks0sk4
- **타입**: Docker Compose (public repository)
- **GitHub 저장소**: https://github.com/myaji35/12_InsureGraph-Pro
- **브랜치**: main
- **Docker Compose 파일**: /docker-compose.coolify.yml
- **서버**: localhost (Coolify host)

### 5. 배포 시작 완료
- **Deployment UUID**: fk4cg804w8o444kggco0gsc4
- **커밋**: 8b6d5f703ce9a1ee920a8ea9607d970dfb8e1de8
- **상태**: in_progress → exited:unhealthy
- **배포 방법**: Coolify API POST /deploy

---

## 📋 현재 상태

### 애플리케이션 상태
```
Name: insuregraph-pro
UUID: e04ggk4k4www8kkg44ks0sk4
Status: exited:unhealthy
Branch: main
Server: localhost
Description: AI-powered Insurance Graph RAG Platform
```

### 배포 상태
```
Deployment UUID: fk4cg804w8o444kggco0gsc4
Status: in_progress
Commit: 8b6d5f703ce9a1ee920a8ea9607d970dfb8e1de8
Application: insuregraph-pro
Server: localhost
```

### 서비스 구성 (Docker Compose)
Coolify가 자동으로 파싱한 서비스:
1. **postgres** (PostgreSQL 15)
   - Container: postgres-e04ggk4k4www8kkg44ks0sk4-124348780929
   - Volume: e04ggk4k4www8kkg44ks0sk4_postgres-data
   - Network: insuregraph-network, e04ggk4k4www8kkg44ks0sk4
   - Healthcheck: pg_isready

2. **redis** (Redis 7 Alpine)
   - Container: redis-e04ggk4k4www8kkg44ks0sk4-124348822609
   - Volume: e04ggk4k4www8kkg44ks0sk4_redis-data
   - Healthcheck: redis-cli ping

3. **neo4j** (Neo4j 5.14)
   - Container: neo4j-e04ggk4k4www8kkg44ks0sk4-124348829757
   - Volumes: neo4j-data, neo4j-logs
   - Plugins: APOC
   - Healthcheck: cypher-shell

4. **backend** (FastAPI)
   - Container: backend-e04ggk4k4www8kkg44ks0sk4-124348841567
   - Build: ./backend/Dockerfile
   - Port: 8080
   - Healthcheck: curl /api/v1/health
   - Depends on: postgres, redis, neo4j (healthy)

5. **frontend** (Next.js)
   - Container: frontend-e04ggk4k4www8kkg44ks0sk4-124348880822
   - Build: ./frontend/Dockerfile.prod
   - Port: 3000
   - Depends on: backend

6. **celery-worker**
   - Container: celery-worker-e04ggk4k4www8kkg44ks0sk4-124348883463
   - Build: ./backend/Dockerfile
   - Command: celery worker
   - Depends on: postgres, redis, neo4j

---

## ⚠️ 현재 이슈

### Issue #1: 애플리케이션 상태 unhealthy
**상태**: `exited:unhealthy`
**원인 분석**:
1. 환경변수 미설정 가능성
2. Docker 빌드 실패
3. 서비스 의존성 문제

**해결 방법**:
1. Coolify Web UI에서 환경변수 확인 및 설정
2. 배포 로그 확인
3. 수동 재배포

### Issue #2: 배포 로그 접근 제한
**상태**: CLI로 상세 로그 확인 제한적
**해결 방법**: Web UI에서 로그 확인 필요

---

## 🔧 필요한 환경변수 (Web UI에서 설정)

### 필수 환경변수
```bash
# PostgreSQL
POSTGRES_PASSWORD=InsureGraph2024!Prod!Secure

# Neo4j
NEO4J_PASSWORD=Neo4j2024!Graph!Secure

# Security Keys
SECRET_KEY=7K8mNpQ3rT9vX2bC5dF6gH8jK0lM4nP7qR9sT2uV5wX8yZ
JWT_SECRET_KEY=3aB5cD7eF9gH2iJ4kL6mN8oP0qR2sT4uV6wX8yZ1aB3cD5

# LLM API Keys (실제 키 필요!)
ANTHROPIC_API_KEY=<your-real-key>
GOOGLE_API_KEY=<your-real-key>
OPENAI_API_KEY=<your-real-key>
UPSTAGE_API_KEY=<your-real-key>

# CORS
CORS_ORIGINS=https://InsureGraphPro.34.64.191.91,http://InsureGraphPro.34.64.191.91,http://localhost:3000

# Frontend API URL
NEXT_PUBLIC_API_URL=https://InsureGraphPro.34.64.191.91/api
```

---

## 🚀 다음 단계

### 단기 (즉시)
1. **Coolify Web UI 접속**: http://34.64.191.91
2. **환경변수 설정**:
   - Applications → insuregraph-pro → Environment
   - 위 환경변수 모두 추가
   - Save 클릭
3. **재배포**:
   - Deploy 버튼 클릭
   - 로그 모니터링
4. **헬스체크**:
   - 모든 서비스 Running 확인
   - Frontend, Backend API 접속 테스트

### 중기 (배포 성공 후)
1. **데이터베이스 마이그레이션**:
   ```bash
   # Backend 컨테이너에서
   alembic upgrade head
   ```

2. **Neo4j 인덱스 생성**:
   ```cypher
   CREATE INDEX article_text IF NOT EXISTS FOR (n:Article) ON (n.text);
   CREATE INDEX paragraph_text IF NOT EXISTS FOR (n:Paragraph) ON (n.text);
   ```

3. **도메인 설정**:
   - Coolify에서 도메인 추가
   - https://InsureGraphPro.34.64.191.91

4. **모니터링 설정**:
   - 로그 확인
   - 리소스 사용량 체크

---

## 📊 배포 정보 요약

| 항목 | 값 |
|------|-----|
| **Coolify 서버** | http://34.64.191.91 |
| **프로젝트 UUID** | rsskss4gcwsgwo8w040gs4ks4 |
| **애플리케이션 UUID** | e04ggk4k4www8kkg44ks0sk4 |
| **Deployment UUID** | fk4cg804w8o444kggco0gsc4 |
| **GitHub 저장소** | https://github.com/myaji35/12_InsureGraph-Pro.git |
| **커밋** | 8b6d5f7 |
| **Docker Compose** | docker-compose.coolify.yml |
| **서비스 수** | 6 (postgres, redis, neo4j, backend, frontend, celery-worker) |

---

## 🔗 유용한 링크

### Coolify
- **대시보드**: http://34.64.191.91
- **프로젝트**: http://34.64.191.91/project/rsskss4gcwsgwo8w040gs4ks4
- **애플리케이션**: http://34.64.191.91/project/rsskss4gcwsgwo8w040gs4ks4/application/e04ggk4k4www8kkg44ks0sk4

### GitHub
- **저장소**: https://github.com/myaji35/12_InsureGraph-Pro
- **최신 커밋**: https://github.com/myaji35/12_InsureGraph-Pro/commit/8b6d5f7

### GitLab (선택)
- **프로젝트**: http://34.158.192.195/testgraph/projects/a53c6c7c-7e21-4e59-a870-b4a12f6a54f1
- **Issues**: http://34.158.192.195/testgraph/projects/a53c6c7c-7e21-4e59-a870-b4a12f6a54f1/issues
- **상태**: 접근 확인 필요

---

## 📚 관련 문서

1. **COOLIFY_QUICK_DEPLOY.md** - 5단계 빠른 배포 가이드
2. **COOLIFY_UI_DEPLOYMENT.md** - 상세 UI 배포 가이드
3. **COOLIFY_DEPLOYMENT.md** - CLI 배포 가이드
4. **DEPLOYMENT_COMPLETE.md** - 배포 완료 보고서
5. **DEVELOPMENT_PROGRESS.md** - 개발 진행 상황

---

## ✅ CLI로 완료한 작업

1. ✅ Coolify CLI 설치 및 설정
2. ✅ Coolify 서버 추가 (coolify-insuregraph)
3. ✅ InsureGraphPro 프로젝트 생성 (API)
4. ✅ GitHub 저장소 연결 (insuregraph-pro 애플리케이션)
5. ✅ Docker Compose 파싱 및 서비스 구성
6. ✅ 배포 큐 등록 (Deployment UUID: fk4cg804w8o444kggco0gsc4)
7. ✅ 배포 상태 모니터링 시작

## ⏳ Web UI로 완료 필요한 작업

1. ⏳ 환경변수 설정 (LLM API 키 등)
2. ⏳ 배포 재시작
3. ⏳ 로그 확인 및 디버깅
4. ⏳ 헬스체크 및 서비스 확인
5. ⏳ 도메인 설정
6. ⏳ 데이터베이스 마이그레이션

---

**최종 상태**: Coolify CLI로 프로젝트 및 애플리케이션 생성 완료, 환경변수 설정 및 재배포는 Web UI에서 진행 필요

🎯 다음 작업: http://34.64.191.91 접속 → insuregraph-pro 애플리케이션 → Environment 탭 → 환경변수 설정 → Deploy
