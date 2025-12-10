# InsureGraph Pro - Plane 협업 솔루션 연동 가이드

**Plane 서버**: http://34.158.192.195
**프로젝트 ID**: a53c6c7c-7e21-4e59-a870-b4a12f6a54f1
**워크스페이스**: testgraph

---

## 📋 Plane이란?

Plane은 오픈소스 프로젝트 관리 및 이슈 추적 도구입니다. Jira, Linear와 유사한 기능을 제공하며, 다음과 같은 특징이 있습니다:

- 이슈 추적 및 관리
- 스프린트 계획
- 칸반 보드
- 로드맵 시각화
- GitHub 연동
- API 기반 자동화

---

## 🔗 InsureGraph Pro 프로젝트 정보

### GitHub 저장소
- **URL**: https://github.com/myaji35/12_InsureGraph-Pro.git
- **브랜치**: main
- **최신 커밋**: 7391bcf

### Plane 프로젝트
- **URL**: http://34.158.192.195/testgraph/projects/a53c6c7c-7e21-4e59-a870-b4a12f6a54f1
- **Issues**: http://34.158.192.195/testgraph/projects/a53c6c7c-7e21-4e59-a870-b4a12f6a54f1/issues
- **프로젝트 ID**: a53c6c7c-7e21-4e59-a870-b4a12f6a54f1

---

## 🚀 Plane 연동 방법

### 1. Plane API 토큰 발급

1. Plane 웹 UI 접속: http://34.158.192.195
2. 로그인
3. Settings → API Tokens
4. **Create New Token** 클릭
5. 토큰 이름: `insuregraph-deployment`
6. 권한 설정: `Write` (이슈 생성 권한)
7. 토큰 복사 및 안전하게 보관

### 2. GitHub와 Plane 연동

Plane은 GitHub 이슈와 자동 동기화를 지원합니다:

1. Plane 프로젝트 설정
2. Integrations → GitHub
3. GitHub 저장소 연결: `myaji35/12_InsureGraph-Pro`
4. 동기화 설정:
   - GitHub Issue → Plane Issue
   - GitHub PR → Plane Issue
   - Commit 자동 연결

---

## 📝 배포 현황 이슈 자동 생성 스크립트

### Plane API를 사용한 이슈 생성

```bash
#!/bin/bash

# Plane 서버 및 프로젝트 정보
PLANE_URL="http://34.158.192.195"
WORKSPACE_SLUG="testgraph"
PROJECT_ID="a53c6c7c-7e21-4e59-a870-b4a12f6a54f1"
PLANE_API_TOKEN="your-plane-api-token-here"

# 이슈 데이터
ISSUE_TITLE="[Deployment] InsureGraph Pro Coolify 배포 완료"
ISSUE_DESCRIPTION=$(cat <<'EOF'
# InsureGraph Pro - Coolify 배포 현황

## ✅ 완료된 작업

### Coolify CLI 설정
- Coolify CLI 1.3.0 사용
- 서버: coolify-insuregraph (34.64.191.91)
- 프로젝트: InsureGraphPro (UUID: rsskss4gcwsgwo8w040gs4ks4)
- 애플리케이션: insuregraph-pro (UUID: e04ggk4k4www8kkg44ks0sk4)

### 배포 정보
- **Deployment UUID**: fk4cg804w8o444kggco0gsc4
- **커밋**: 7391bcf
- **GitHub**: https://github.com/myaji35/12_InsureGraph-Pro
- **Docker Compose**: 6개 서비스 구성

### 서비스 구성
1. PostgreSQL 15
2. Redis 7
3. Neo4j 5.14 (APOC)
4. FastAPI Backend
5. Next.js Frontend
6. Celery Worker

## ⏳ 진행 중

### 환경변수 설정 필요
Coolify Web UI에서 설정 필요:
- LLM API Keys (Anthropic, Google, OpenAI, Upstage)
- Database Passwords
- Security Keys
- CORS Settings

## 🔗 관련 링크

- **Coolify 대시보드**: http://34.64.191.91
- **GitHub 저장소**: https://github.com/myaji35/12_InsureGraph-Pro
- **최신 커밋**: https://github.com/myaji35/12_InsureGraph-Pro/commit/7391bcf

## 📚 배포 문서

1. COOLIFY_DEPLOYMENT_STATUS.md - 배포 현황
2. COOLIFY_QUICK_DEPLOY.md - 빠른 배포 가이드
3. COOLIFY_UI_DEPLOYMENT.md - UI 배포 상세
4. DEPLOYMENT_COMPLETE.md - 배포 완료 보고서

## 다음 단계

- [ ] Coolify Web UI에서 환경변수 설정
- [ ] 배포 재시작
- [ ] 헬스체크 확인
- [ ] 도메인 설정 (https://InsureGraphPro.34.64.191.91)
- [ ] 데이터베이스 마이그레이션
- [ ] Neo4j 인덱스 생성
EOF
)

# Plane API로 이슈 생성
curl -X POST "${PLANE_URL}/api/v1/workspaces/${WORKSPACE_SLUG}/projects/${PROJECT_ID}/issues/" \
  -H "Authorization: Bearer ${PLANE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"${ISSUE_TITLE}\",
    \"description_html\": \"${ISSUE_DESCRIPTION}\",
    \"state\": \"in_progress\",
    \"priority\": \"high\",
    \"labels\": [\"deployment\", \"coolify\", \"infrastructure\"]
  }"
```

---

## 🔄 자동화된 배포 상태 동기화

### GitHub Actions로 Plane 업데이트

`.github/workflows/plane-sync.yml`:

```yaml
name: Sync to Plane

on:
  push:
    branches: [main]
  issues:
    types: [opened, edited, closed]

jobs:
  sync-to-plane:
    runs-on: ubuntu-latest
    steps:
      - name: Sync Issue to Plane
        uses: makeplane/plane-github-action@v1
        with:
          plane-url: ${{ secrets.PLANE_URL }}
          plane-api-token: ${{ secrets.PLANE_API_TOKEN }}
          workspace-slug: testgraph
          project-id: a53c6c7c-7e21-4e59-a870-b4a12f6a54f1
```

---

## 📊 Plane에서 추적할 이슈 카테고리

### 1. 배포 관련
- [x] Coolify 서버 설정
- [x] 프로젝트 생성
- [x] 애플리케이션 구성
- [ ] 환경변수 설정
- [ ] 배포 완료
- [ ] 도메인 설정

### 2. 개발 진행
- [x] LLM 통합 (Gemini 2.5 Flash)
- [x] UI/UX 개선
- [x] Neo4j 검색 확장
- [x] Unstructured.io 청킹
- [ ] 답변 품질 개선
- [ ] 모바일 최적화

### 3. 인프라
- [x] GitHub 저장소 설정
- [x] Docker Compose 구성
- [ ] Coolify 배포
- [ ] 모니터링 설정
- [ ] 백업 전략

### 4. 문서화
- [x] 배포 가이드 작성
- [x] API 문서화
- [ ] 사용자 매뉴얼
- [ ] 운영 가이드

---

## 🛠️ Plane CLI 도구

Plane은 CLI 도구도 제공합니다:

```bash
# Plane CLI 설치
npm install -g @plane/cli

# Plane 설정
plane config set url http://34.158.192.195
plane config set token YOUR_API_TOKEN

# 이슈 생성
plane issue create \
  --workspace testgraph \
  --project a53c6c7c-7e21-4e59-a870-b4a12f6a54f1 \
  --title "[Deployment] Coolify 배포 완료" \
  --state "in_progress" \
  --priority "high"

# 이슈 목록 조회
plane issue list \
  --workspace testgraph \
  --project a53c6c7c-7e21-4e59-a870-b4a12f6a54f1

# 이슈 업데이트
plane issue update <issue-id> \
  --state "completed" \
  --comment "배포 완료 및 헬스체크 통과"
```

---

## 📈 Plane 대시보드 활용

### 칸반 보드 설정

**컬럼 구성**:
1. **Backlog**: 계획 단계
2. **Todo**: 작업 대기
3. **In Progress**: 진행 중 (현재 배포 작업)
4. **Review**: 검토 중
5. **Done**: 완료

### 스프린트 계획

**Sprint 1: 배포 및 안정화** (1주)
- Coolify 배포 완료
- 환경변수 설정
- 헬스체크 통과
- 도메인 설정

**Sprint 2: 품질 개선** (2주)
- Gemini API 최적화
- 답변 품질 개선 (80%+ 정확도)
- 성능 튜닝

**Sprint 3: 기능 확장** (3주)
- 추가 보험사 데이터
- 실시간 스트리밍
- 모바일 UI

---

## 🔐 보안 설정

### Plane API 토큰 관리

1. **환경변수로 관리**:
   ```bash
   export PLANE_API_TOKEN="your-token-here"
   ```

2. **GitHub Secrets에 저장**:
   - Repository Settings → Secrets
   - `PLANE_URL`: http://34.158.192.195
   - `PLANE_API_TOKEN`: [발급받은 토큰]
   - `PLANE_WORKSPACE`: testgraph
   - `PLANE_PROJECT_ID`: a53c6c7c-7e21-4e59-a870-b4a12f6a54f1

3. **로컬 개발**:
   ```bash
   # .env.local
   PLANE_URL=http://34.158.192.195
   PLANE_API_TOKEN=your-token-here
   PLANE_WORKSPACE=testgraph
   PLANE_PROJECT_ID=a53c6c7c-7e21-4e59-a870-b4a12f6a54f1
   ```

---

## 📞 지원

### Plane 문서
- **공식 문서**: https://docs.plane.so
- **API 문서**: https://docs.plane.so/api-reference
- **GitHub**: https://github.com/makeplane/plane

### InsureGraph Pro
- **GitHub**: https://github.com/myaji35/12_InsureGraph-Pro
- **Issues**: https://github.com/myaji35/12_InsureGraph-Pro/issues
- **Plane**: http://34.158.192.195/testgraph/projects/a53c6c7c-7e21-4e59-a870-b4a12f6a54f1

---

## 🎯 다음 단계

1. **Plane 접속 확인**
   - http://34.158.192.195 접속
   - 로그인 및 프로젝트 확인

2. **API 토큰 발급**
   - Settings → API Tokens
   - insuregraph-deployment 토큰 생성

3. **배포 이슈 생성**
   - 위 스크립트 사용
   - 배포 현황 동기화

4. **GitHub 연동**
   - Plane-GitHub 통합 설정
   - 이슈 자동 동기화

5. **협업 시작**
   - 팀원 초대
   - 칸반 보드 활용
   - 스프린트 계획

---

**Plane을 활용하여 InsureGraph Pro 개발 및 배포를 효율적으로 관리하세요!** 🚀
