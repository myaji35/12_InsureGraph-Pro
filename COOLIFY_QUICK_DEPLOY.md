# InsureGraph Pro - Coolify 빠른 배포 가이드

## 🎯 준비 완료 사항

✅ **GitHub 저장소**: https://github.com/myaji35/12_InsureGraph-Pro.git
✅ **Coolify 서버**: http://34.64.191.91
✅ **프로젝트**: InsureGraphPro (UUID: rsskss4gcwsgwo8w040gs4ks)
✅ **서버**: coolify-insuregraph (UUID: rc0s0w80gcksc00kkso0kwos)
✅ **배포 도메인**: https://InsureGraphPro.34.64.191.91

---

## 🚀 5단계로 빠른 배포

### 1단계: Coolify 대시보드 접속 (1분)

```bash
# 브라우저에서 접속
open http://34.64.191.91
```

또는 직접 브라우저에서:
```
http://34.64.191.91
```

### 2단계: 프로젝트 및 리소스 생성 (2분)

1. 로그인 후 **"InsureGraphPro"** 프로젝트 선택 (또는 생성)
2. **"+ New"** → **"Resource"** 클릭
3. **"Public Repository"** 선택
4. 다음 정보 입력:
   - Repository URL: `https://github.com/myaji35/12_InsureGraph-Pro`
   - Branch: `main`
   - Build Pack: `Docker Compose`
   - Docker Compose File: `docker-compose.coolify.yml`
5. **"Continue"** 클릭

### 3단계: 환경변수 설정 (3분)

**Environment** 탭에서 다음 필수 환경변수 추가:

```bash
# PostgreSQL
POSTGRES_PASSWORD=InsureGraph2024!Prod!Secure

# Neo4j
NEO4J_PASSWORD=Neo4j2024!Graph!Secure

# Security Keys
SECRET_KEY=7K8mNpQ3rT9vX2bC5dF6gH8jK0lM4nP7qR9sT2uV5wX8yZ
JWT_SECRET_KEY=3aB5cD7eF9gH2iJ4kL6mN8oP0qR2sT4uV6wX8yZ1aB3cD5

# LLM API Keys (실제 키로 교체 필요!)
ANTHROPIC_API_KEY=<your-real-key>
GOOGLE_API_KEY=<your-real-key>
OPENAI_API_KEY=<your-real-key>
UPSTAGE_API_KEY=<your-real-key>

# CORS
CORS_ORIGINS=https://InsureGraphPro.34.64.191.91,http://InsureGraphPro.34.64.191.91,http://localhost:3000

# Frontend API URL
NEXT_PUBLIC_API_URL=https://InsureGraphPro.34.64.191.91/api
```

**"Save"** 클릭

### 4단계: 도메인 설정 (1분)

**Domains** 탭에서:
1. **"Add Domain"** 클릭
2. 도메인 입력: `InsureGraphPro.34.64.191.91`
3. **HTTPS**: 필요시 체크
4. **"Save"** 클릭

### 5단계: 배포 실행 (5-10분)

1. **"Deploy"** 버튼 클릭
2. **Logs** 탭에서 빌드 진행 상황 모니터링
3. 모든 서비스가 **Running** 상태가 될 때까지 대기

---

## ✅ 배포 확인

### 서비스 접속 테스트

```bash
# Frontend
curl -I https://InsureGraphPro.34.64.191.91/

# Backend API
curl https://InsureGraphPro.34.64.191.91/api/health

# API Docs
open https://InsureGraphPro.34.64.191.91/api/docs
```

### 포트 직접 접속 (대체)

- Frontend: http://34.64.191.91:18000
- Backend: http://34.64.191.91:18001
- Neo4j: http://34.64.191.91:17474

---

## 🔧 Coolify CLI로 모니터링

### 배포 상태 확인

```bash
# 애플리케이션 목록
coolify app list

# 배포 로그 확인 (UUID는 app list에서 확인)
coolify app logs <app-uuid>

# 배포 재시작
coolify deploy name InsureGraphPro
```

---

## 📊 배포 후 작업

### 1. 데이터베이스 마이그레이션

Coolify UI에서 Backend 서비스의 Terminal을 열고:

```bash
alembic upgrade head
```

### 2. Neo4j 인덱스 생성

Neo4j Browser (http://34.64.191.91:17474)에서:

```cypher
CREATE INDEX article_text IF NOT EXISTS FOR (n:Article) ON (n.text);
CREATE INDEX paragraph_text IF NOT EXISTS FOR (n:Paragraph) ON (n.text);
CREATE INDEX article_source IF NOT EXISTS FOR (n:Article) ON (n.source);
```

### 3. 헬스체크

```bash
# Backend 헬스체크
curl https://InsureGraphPro.34.64.191.91/api/health

# Frontend 접속
open https://InsureGraphPro.34.64.191.91/
```

---

## 🆘 트러블슈팅

### 빌드 실패 시

1. **Logs** 탭에서 에러 메시지 확인
2. 환경변수가 모두 설정되었는지 확인
3. Docker Compose 파일 경로 확인 (`docker-compose.coolify.yml`)
4. 서버 디스크 용량 확인

### 서비스 연결 실패

1. 모든 서비스가 **Running** 상태인지 확인
2. 서비스 재시작: **Restart** 버튼
3. 네트워크 설정 확인
4. 방화벽 규칙 확인 (포트 18000, 18001, 17474 오픈)

### CORS 에러

`CORS_ORIGINS` 환경변수가 올바르게 설정되었는지 확인:
```
https://InsureGraphPro.34.64.191.91,http://InsureGraphPro.34.64.191.91
```

---

## 🎉 완료!

축하합니다! InsureGraph Pro가 Coolify에 성공적으로 배포되었습니다.

**접속 URL**:
- 🌐 **메인**: https://InsureGraphPro.34.64.191.91
- 📱 **Frontend**: https://InsureGraphPro.34.64.191.91/
- 🔧 **API**: https://InsureGraphPro.34.64.191.91/api
- 📖 **API Docs**: https://InsureGraphPro.34.64.191.91/api/docs
- 🗄️ **Neo4j**: https://InsureGraphPro.34.64.191.91/neo4j

**CLI 모니터링**:
```bash
# 배포 상태 확인
coolify deploy list

# 실시간 로그
coolify app logs <app-uuid> -f
```

---

## 📚 추가 문서

- 상세 배포 가이드: `COOLIFY_UI_DEPLOYMENT.md`
- CLI 배포 가이드: `COOLIFY_DEPLOYMENT.md`
- 배포 완료 보고서: `DEPLOYMENT_COMPLETE.md`
- 개발 진행 상황: `DEVELOPMENT_PROGRESS.md`
