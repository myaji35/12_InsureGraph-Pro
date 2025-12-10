# Plane 동기화 가이드

InsureGraph Pro의 개발현황과 배포현황을 Plane 프로젝트에 자동으로 동기화하는 가이드입니다.

---

## 📋 사전 준비

### 1. Plane API 토큰 발급

1. **Plane 대시보드 접속**
   ```
   http://34.158.192.195
   ```

2. **로그인 후 Settings 이동**
   - 우측 상단 프로필 클릭
   - Settings 선택

3. **API Tokens 페이지**
   - 좌측 메뉴에서 "API Tokens" 선택
   - **"Create New Token"** 버튼 클릭

4. **토큰 생성**
   - Token Name: `insuregraph-sync`
   - Description: `InsureGraph Pro 개발/배포 현황 자동 동기화`
   - Permissions: **Write** (이슈 생성/수정 권한)
   - **Create** 버튼 클릭

5. **토큰 복사**
   - 생성된 토큰을 안전한 곳에 복사
   - ⚠️ 한 번만 표시되므로 반드시 복사!

### 2. 프로젝트 정보 확인

현재 설정된 정보:
- **Plane URL**: http://34.158.192.195
- **워크스페이스**: testgraph
- **프로젝트 ID**: INSUR
- **프로젝트 UUID**: a53c6c7c-7e21-4e59-a870-b4a12f6a54f1

---

## 🚀 사용 방법

### 방법 1: 환경변수 설정 (권장)

```bash
# 1. API 토큰 환경변수로 설정
export PLANE_API_TOKEN='your-actual-plane-api-token'

# 2. 스크립트 실행
cd "/Users/gangseungsig/Documents/02_GitHub/12_InsureGraph Pro"
./sync-to-plane.sh
```

### 방법 2: 인라인 실행

```bash
# 토큰을 직접 지정하여 실행
PLANE_API_TOKEN='your-actual-plane-api-token' ./sync-to-plane.sh
```

### 방법 3: .env 파일 사용

```bash
# 1. .env 파일 생성
cat > .env.plane << 'EOF'
export PLANE_API_TOKEN='your-actual-plane-api-token'
EOF

# 2. .env 파일 로드 후 실행
source .env.plane
./sync-to-plane.sh
```

---

## 📊 생성되는 이슈

### 이슈 1: [개발현황] InsureGraph Pro 주요 기능 구현 완료

**내용**:
- ✅ LLM 통합 및 최적화 (Gemini 2.5 Flash)
- ✅ UI/UX 대폭 개선 (고령 사용자 최적화)
- ✅ Neo4j 검색 확장 (9개 노드 타입)
- ✅ Unstructured.io 청킹 시스템
- 📈 성능 지표 (4,018 노드)
- 🔧 기술 스택 정보
- 🐛 알려진 이슈
- 📚 생성된 문서
- 📅 다음 계획

**라벨**: `development`, `feature`, `llm`, `ui-ux`
**우선순위**: High
**상태**: Started

### 이슈 2: [배포현황] Coolify CLI 배포 인프라 구축 완료

**내용**:
- ✅ Coolify CLI 설정 완료
- ✅ 서버 추가 (coolify-insuregraph)
- ✅ 프로젝트 생성 (InsureGraphPro)
- ✅ 애플리케이션 구성 (6개 서비스)
- 🐳 Docker Compose 서비스 상세
- 🌐 배포 URL 설정 (통합 도메인)
- 🔧 환경변수 설정 가이드
- 📚 배포 문서 목록
- ⏳ 다음 단계

**라벨**: `deployment`, `infrastructure`, `coolify`, `docker`
**우선순위**: High
**상태**: Started

---

## 🔄 자동화 설정 (선택)

### GitHub Actions로 자동 동기화

`.github/workflows/plane-sync.yml` 생성:

```yaml
name: Sync to Plane

on:
  push:
    branches: [main]
    paths:
      - 'DEVELOPMENT_PROGRESS.md'
      - 'COOLIFY_DEPLOYMENT_STATUS.md'

jobs:
  sync-to-plane:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Sync to Plane
        env:
          PLANE_API_TOKEN: ${{ secrets.PLANE_API_TOKEN }}
        run: |
          chmod +x ./sync-to-plane.sh
          ./sync-to-plane.sh
```

**GitHub Secrets 설정**:
1. GitHub 저장소 → Settings → Secrets and variables → Actions
2. **New repository secret** 클릭
3. Name: `PLANE_API_TOKEN`
4. Value: [발급받은 Plane API 토큰]
5. **Add secret** 클릭

---

## 📝 실행 결과 예시

```
🚀 InsureGraph Pro - Plane 동기화 시작
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 프로젝트 정보:
  - 브랜치: main
  - 최신 커밋: 9862b20
  - 커밋 메시지: docs: Add Plane collaboration platform integration guide
  - 커밋 시간: 2025-12-10 22:55:30 +0900

📝 이슈 1: 개발 현황
📝 이슈 2: 배포 현황

🔄 Plane API로 이슈 생성 중...

Creating Issue 1: 개발현황...
✅ 개발현황 이슈 생성 완료
   {"id":"abc123","name":"[개발현황] InsureGraph Pro 주요 기능 구현 완료"}

Creating Issue 2: 배포현황...
✅ 배포현황 이슈 생성 완료
   {"id":"def456","name":"[배포현황] Coolify CLI 배포 인프라 구축 완료"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 Plane 동기화 완료!

📊 생성된 이슈:
  1. [개발현황] 주요 기능 구현 완료
  2. [배포현황] Coolify CLI 인프라 구축

🔗 Plane 프로젝트:
  http://34.158.192.195/testgraph/projects/a53c6c7c-7e21-4e59-a870-b4a12f6a54f1/issues
```

---

## 🔧 트러블슈팅

### 에러: "PLANE_API_TOKEN 환경변수를 설정해주세요"

**원인**: API 토큰이 설정되지 않음

**해결**:
```bash
export PLANE_API_TOKEN='your-actual-token'
```

### 에러: HTTP 401 Unauthorized

**원인**: API 토큰이 잘못되었거나 만료됨

**해결**:
1. Plane 대시보드에서 새 토큰 발급
2. 환경변수 업데이트

### 에러: HTTP 404 Not Found

**원인**: 프로젝트 UUID가 잘못됨

**해결**:
1. Plane 프로젝트 URL 확인
2. `sync-to-plane.sh`에서 `PROJECT_ID` 수정

### 에러: Permission Denied

**원인**: 스크립트 실행 권한 없음

**해결**:
```bash
chmod +x sync-to-plane.sh
```

---

## 🔐 보안 주의사항

### API 토큰 관리

1. **절대 Git에 커밋하지 마세요**
   ```bash
   # .gitignore에 추가
   .env.plane
   *.token
   ```

2. **환경변수로만 관리**
   ```bash
   # ~/.bashrc 또는 ~/.zshrc에 추가 (선택)
   export PLANE_API_TOKEN='your-token'
   ```

3. **토큰 순환**
   - 정기적으로 토큰 재발급
   - 의심스러운 활동 시 즉시 재발급

---

## 📞 지원

### Plane 관련
- **Plane 대시보드**: http://34.158.192.195
- **프로젝트 URL**: http://34.158.192.195/testgraph/projects/a53c6c7c-7e21-4e59-a870-b4a12f6a54f1

### InsureGraph Pro
- **GitHub**: https://github.com/myaji35/12_InsureGraph-Pro
- **Issues**: https://github.com/myaji35/12_InsureGraph-Pro/issues

---

**Plane과 GitHub를 연동하여 효율적인 프로젝트 관리를 시작하세요!** 🚀
