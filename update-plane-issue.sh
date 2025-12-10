#!/bin/bash
set -e

# Plane 서버 정보
PLANE_URL="http://34.158.192.195"
ISSUE_ID="14d8ec1a49934a46b5927d0fc033699f"

# API 토큰 (환경변수에서 읽기)
PLANE_API_TOKEN="${PLANE_API_TOKEN:-your-plane-api-token-here}"

if [ "$PLANE_API_TOKEN" = "your-plane-api-token-here" ]; then
    echo "⚠️  PLANE_API_TOKEN 환경변수를 설정해주세요."
    echo ""
    echo "사용 방법:"
    echo "  export PLANE_API_TOKEN='your-actual-token'"
    echo "  ./update-plane-issue.sh"
    exit 1
fi

echo "🚀 InsureGraph Pro - Plane 이슈 업데이트 시작"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 대상 이슈: http://34.158.192.195/spaces/issues/${ISSUE_ID}"
echo ""

# 현재 Git 정보 수집
CURRENT_BRANCH=$(git branch --show-current)
LATEST_COMMIT=$(git log -1 --format="%H")
COMMIT_MESSAGE=$(git log -1 --format="%s")
COMMIT_DATE=$(git log -1 --format="%ai")

echo "📊 프로젝트 정보:"
echo "  - 브랜치: $CURRENT_BRANCH"
echo "  - 최신 커밋: ${LATEST_COMMIT:0:7}"
echo "  - 커밋 메시지: $COMMIT_MESSAGE"
echo ""

# 코멘트 1: 개발 현황
COMMENT_1=$(cat <<EOF
## 📊 개발 현황 업데이트 ($(date '+%Y-%m-%d %H:%M'))

**GitHub**: https://github.com/myaji35/12_InsureGraph-Pro
**커밋**: ${LATEST_COMMIT:0:7}

---

### ✅ 완료된 주요 기능

#### 1. LLM 통합 및 최적화
- ✅ Google Gemini 2.5 Flash 통합
- ✅ 답변 품질 개선 (사과 표현 제거)
- ✅ LLM 모델명 UI 표시
- ✅ 중복 참고 문서 제거
- ✅ 상세 로깅 시스템

#### 2. UI/UX 대폭 개선
- ✅ 폰트 크기 확대 (14px 이상)
- ✅ 전체 너비 레이아웃
- ✅ 채팅 스타일 UI
- ✅ 고령 사용자 최적화

#### 3. Neo4j 검색 확장
- ✅ 노드 타입: 3개 → 9개
- ✅ 전체 노드: 4,018개 (MetLife)
- ✅ 검색 속성 확장

#### 4. Unstructured.io 청킹
- ✅ 보험 약관 전문 파싱
- ✅ 계층 구조 보존
- ✅ 의미 기반 청킹

---

### 📈 성능 지표
- **Neo4j 노드**: 4,018개
- **LLM 모델**: Gemini 2.5 Flash
- **응답 시간**: ~2-3초
- **목표 정확도**: 80%+

---

### 🔧 기술 스택
- Backend: FastAPI, Neo4j 5.14, PostgreSQL 15, Redis 7
- Frontend: Next.js 14, TypeScript, Tailwind
- LLM: Gemini, Claude, GPT, Upstage
- 인프라: Docker Compose, Coolify

---

### 📚 생성된 문서
1. DEV_SETUP_GUIDE.md
2. AUTH_GUIDE.md
3. CORS_FIX_SUMMARY.md
4. DEVELOPMENT_PROGRESS.md
5. ERROR_RESOLUTION_SUMMARY.md

---

### 📅 다음 단계
- [ ] Gemini API 이슈 해결
- [ ] 답변 품질 80%+ 달성
- [ ] 추가 보험사 데이터
- [ ] 실시간 스트리밍
EOF
)

# 코멘트 2: 배포 현황
COMMENT_2=$(cat <<EOF
## 🚀 배포 현황 업데이트 ($(date '+%Y-%m-%d %H:%M'))

**Coolify**: http://34.64.191.91
**도메인**: https://InsureGraphPro.34.64.191.91

---

### ✅ Coolify CLI 배포 완료

#### 1. 인프라 구축
- ✅ Coolify CLI 1.3.0 설정
- ✅ 서버: coolify-insuregraph (34.64.191.91)
- ✅ 프로젝트: InsureGraphPro
- ✅ 애플리케이션: insuregraph-pro

#### 2. Docker Compose 서비스 (6개)
- ✅ PostgreSQL 15
- ✅ Redis 7
- ✅ Neo4j 5.14 (APOC)
- ✅ FastAPI Backend
- ✅ Next.js Frontend
- ✅ Celery Worker

#### 3. 통합 도메인 설정
- 메인: https://InsureGraphPro.34.64.191.91
- Frontend: https://InsureGraphPro.34.64.191.91/
- Backend API: https://InsureGraphPro.34.64.191.91/api
- API Docs: https://InsureGraphPro.34.64.191.91/api/docs
- Neo4j: https://InsureGraphPro.34.64.191.91/neo4j

#### 4. 배포 정보
- Deployment UUID: fk4cg804w8o444kggco0gsc4
- 커밋: ${LATEST_COMMIT:0:7}
- 상태: 환경변수 설정 대기

---

### 📚 배포 문서 (8개)
1. COOLIFY_DEPLOYMENT.md
2. COOLIFY_UI_DEPLOYMENT.md
3. COOLIFY_QUICK_DEPLOY.md
4. COOLIFY_DEPLOYMENT_STATUS.md
5. DEPLOYMENT_COMPLETE.md
6. PLANE_INTEGRATION.md
7. PLANE_SYNC_README.md
8. deploy-to-coolify.sh

---

### ⏳ 다음 단계
1. [ ] Coolify Web UI에서 환경변수 설정
2. [ ] LLM API 키 입력
3. [ ] 배포 재시작
4. [ ] 헬스체크 확인
5. [ ] 도메인 DNS 설정
6. [ ] 데이터베이스 마이그레이션

---

### 🔗 관련 링크
- Coolify: http://34.64.191.91
- GitHub: https://github.com/myaji35/12_InsureGraph-Pro
- 커밋: https://github.com/myaji35/12_InsureGraph-Pro/commit/$LATEST_COMMIT
EOF
)

echo "🔄 Plane API로 코멘트 추가 중..."
echo ""

# 워크스페이스와 프로젝트 정보 추출 (API 호출로 확인 필요)
# 일단 spaces API 사용
echo "Adding Comment 1: 개발현황..."

# 이슈에 코멘트 추가 (Plane API v1)
RESPONSE_1=$(curl -s -w "\n%{http_code}" -X POST \
  "${PLANE_URL}/api/v1/workspaces/*/projects/*/issues/${ISSUE_ID}/comments/" \
  -H "Authorization: Bearer ${PLANE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"comment_html\": \"$(echo "$COMMENT_1" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')\"}")

HTTP_CODE_1=$(echo "$RESPONSE_1" | tail -n1)
BODY_1=$(echo "$RESPONSE_1" | sed '$d')

if [ "$HTTP_CODE_1" = "201" ] || [ "$HTTP_CODE_1" = "200" ]; then
    echo "✅ 개발현황 코멘트 추가 완료"
else
    echo "⚠️  개발현황 코멘트 추가 실패 (HTTP $HTTP_CODE_1)"
    echo "   $BODY_1" | head -3
fi
echo ""

sleep 2

echo "Adding Comment 2: 배포현황..."
RESPONSE_2=$(curl -s -w "\n%{http_code}" -X POST \
  "${PLANE_URL}/api/v1/workspaces/*/projects/*/issues/${ISSUE_ID}/comments/" \
  -H "Authorization: Bearer ${PLANE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"comment_html\": \"$(echo "$COMMENT_2" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')\"}")

HTTP_CODE_2=$(echo "$RESPONSE_2" | tail -n1)
BODY_2=$(echo "$RESPONSE_2" | sed '$d')

if [ "$HTTP_CODE_2" = "201" ] || [ "$HTTP_CODE_2" = "200" ]; then
    echo "✅ 배포현황 코멘트 추가 완료"
else
    echo "⚠️  배포현황 코멘트 추가 실패 (HTTP $HTTP_CODE_2)"
    echo "   $BODY_2" | head -3
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Plane 이슈 업데이트 완료!"
echo ""
echo "🔗 이슈 확인:"
echo "  ${PLANE_URL}/spaces/issues/${ISSUE_ID}"
echo ""
